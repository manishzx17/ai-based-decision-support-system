from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    Conversation, ChatMessage, MedicalReport,
    User, PatientProfile, Hospital
)
from schemas import (
    ChatRequest, ChatResponse,
    RAGQueryRequest, RAGQueryResponse,
    RAGProfileGroundingRequest, RAGProfileGroundingResponse
)
from ai.healthcare_assistant import healthcare_assistant
from ai.rag_engine import rag_engine
from routes.auth import get_shared_clinical_context
from security import get_current_user
from config import settings

router = APIRouter(prefix="/services", tags=["Contextual AI Healthcare Assistant & RAG"])


@router.post("/chat", response_model=ChatResponse)
def ai_assistant_chat(
    req: ChatRequest,
    user_id: Optional[int] = None,
    report_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    RAG-grounded conversational healthcare decision support endpoint.
    Operates with single-user/demo session persistence.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's chat."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)

    # 1. Conversation Isolation / Session Persistence
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
        if not conv:
            conv = Conversation(id=req.conversation_id, user_id=target_user_id, title=req.message[:40])
            db.add(conv)
            db.commit()
            db.refresh(conv)
        elif conv.user_id != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have authorization to access this patient's conversation."
            )
        conv_id = conv.id
    else:
        conv = Conversation(user_id=target_user_id, title=req.message[:40])
        db.add(conv)
        db.commit()
        db.refresh(conv)
        conv_id = conv.id

    # 2. Retrieve Conversation History for Multi-Turn Context
    prior_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conv_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history_list = [{"sender": m.sender, "text": m.text} for m in prior_messages]

    # 3. Save User Message
    u_msg = ChatMessage(conversation_id=conv_id, sender="user", text=req.message)
    db.add(u_msg)
    db.commit()

    # 4. Active Patient Context (Shared Clinical Profile for active demo patient)
    profile_dict = get_shared_clinical_context(target_user_id, db)

    # 5. Medical Report Context (Resolution: URL/Req report_id -> Session/Query report_id -> Latest report)
    target_report_id = req.report_id if req.report_id is not None else report_id
    rep = None
    if target_report_id is not None and target_report_id <= 0:
        # Explicit request for NO active medical report context
        rep = None
    elif target_report_id:
        rep_obj = db.query(MedicalReport).filter(MedicalReport.id == target_report_id).first()
        if rep_obj:
            if rep_obj.user_id != target_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not have authorization to access this patient's medical report."
                )
            rep = rep_obj
    else:
        # No explicit report_id requested; resolve to latest patient report if one exists
        rep = (
            db.query(MedicalReport)
            .filter(MedicalReport.user_id == target_user_id)
            .order_by(MedicalReport.id.desc())
            .first()
        )

    report_dict = None
    if rep:
        report_dict = {
            "id": rep.id,
            "summary": rep.summary,
            "recommended_specialty": rep.recommended_specialty,
            "entities": [e.entity_name for e in rep.entities] if rep.entities else []
        }

    # 6. Hospital Context
    hospital_dict = None
    if req.hospital_id:
        h = db.query(Hospital).filter(Hospital.id == req.hospital_id).first()
        if h:
            hospital_dict = {"name": h.name, "city": h.city}

    # 7. Process through Grounded AI Healthcare Assistant Engine
    result = healthcare_assistant.process_chat_query(
        user_query=req.message,
        conversation_history=history_list,
        patient_profile=profile_dict,
        medical_report=report_dict,
        hospital_context=hospital_dict
    )

    # 8. Persist Assistant Response
    a_msg = ChatMessage(conversation_id=conv_id, sender="assistant", text=result["reply"])
    db.add(a_msg)
    db.commit()

    return {
        "reply": result["reply"],
        "conversation_id": conv_id,
        "citations": result["citations"],
        "grounding_status": result["grounding_status"],
        "retrieved_evidence": result["retrieved_evidence"],
        "is_emergency": result.get("is_emergency", False),
        "emergency_alert": result.get("emergency_alert"),
        "patient_context_applied": result.get("patient_context_applied"),
        "suggested_followups": result.get("suggested_followups", []),
        "safety_guardrails_triggered": result.get("safety_guardrails_triggered", []),
        "disclaimer": result.get("disclaimer", healthcare_assistant.MANDATORY_SAFETY_DISCLAIMER),
        "llm_provider": result.get("llm_provider", "deterministic_fallback"),
        "model_used": result.get("model_used", "none")
    }


# =====================================================================
# PHASE 4: MEDICAL KNOWLEDGE + RAG DEDICATED ENDPOINTS
# =====================================================================

@router.post("/rag/query", response_model=RAGQueryResponse)
def rag_semantic_query(
    req: RAGQueryRequest,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evidence-grounded medical knowledge RAG query endpoint.
    Retrieves authoritative clinical guideline evidence and synthesizes responses
    via Ollama local LLM runtime, fusing Phase 3 Clinical Profile context.
    """
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's data."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)
    clinical_profile = None

    if req.use_clinical_profile:
        clinical_profile = get_shared_clinical_context(target_user_id, db)
        result = rag_engine.query_with_clinical_profile(
            user_query=req.query,
            clinical_profile=clinical_profile,
            top_k=req.top_k or 3,
            threshold=req.threshold
        )
    else:
        retrieved = rag_engine.retrieve_documents(
            query=req.query,
            top_k=req.top_k or 3,
            threshold=req.threshold
        )
        result = rag_engine.generate_response(
            user_query=req.query,
            retrieved_docs=retrieved
        )

    return {
        "reply": result["reply"],
        "citations": result.get("citations", []),
        "grounding_status": result.get("grounding_status", "GROUNDED"),
        "retrieved_evidence": result.get("retrieved_evidence", []),
        "llm_provider": result.get("llm_provider", "none"),
        "model_used": result.get("model_used", "none"),
        "clinical_profile_used": clinical_profile if req.use_clinical_profile else None
    }


@router.post("/rag/profile-grounding", response_model=RAGProfileGroundingResponse)
def rag_profile_grounding(
    req: RAGProfileGroundingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Directly grounds the patient's Phase 3 Shared Clinical Profile against
    verified authoritative clinical practice guidelines.
    """
    if req.user_id is not None and req.user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access another patient's data."
        )
    target_user_id = current_user.id if current_user else (req.user_id or 1)
    clinical_profile = get_shared_clinical_context(target_user_id, db)

    grounding_result = rag_engine.ground_clinical_profile(
        clinical_profile=clinical_profile,
        top_k=req.top_k or 2
    )

    return {
        "grounding_status": grounding_result["grounding_status"],
        "matched_guidelines": grounding_result["matched_guidelines"],
        "citations": grounding_result["citations"],
        "patient_conditions_evaluated": grounding_result["patient_conditions_evaluated"],
        "patient_procedures_evaluated": grounding_result["patient_procedures_evaluated"]
    }



@router.get("/chat/history")
def get_chat_history(
    conversation_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves conversation history for demo session persistence."""
    if user_id is not None and user_id != current_user.id and getattr(current_user, "role", "") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have authorization to access this patient's conversation."
        )
    target_user_id = current_user.id if current_user else (user_id or 1)

    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if not conv:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found."
            )
        if conv.user_id != current_user.id and getattr(current_user, "role", "") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have authorization to access this patient's conversation."
            )
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.conversation_id == conv.id)
            .order_by(ChatMessage.id.asc())
            .all()
        )
        return {
            "conversation_id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "messages": [
                {"id": m.id, "sender": m.sender, "text": m.text, "created_at": m.created_at}
                for m in messages
            ]
        }

    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == target_user_id)
        .order_by(Conversation.id.desc())
        .all()
    )
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at,
            "message_count": len(c.messages)
        }
        for c in conversations
    ]

