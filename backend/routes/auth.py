from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, PatientProfile
from schemas import UserCreate, UserLogin, UserResponse, PatientProfileSchema

router = APIRouter(prefix="/auth", tags=["Authentication & User Profile"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already registered.")

    new_user = User(
        email=user_data.email,
        hashed_password=f"hashed_{user_data.password}", # Simplified hashing
        full_name=user_data.full_name,
        role="patient"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize default patient profile
    profile = PatientProfile(
        user_id=new_user.id,
        current_city="Hyderabad",
        preferred_currency="INR"
    )
    db.add(profile)
    db.commit()

    return new_user

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        # Fallback quick demo login
        if login_data.email == "patient@example.com":
            user = db.query(User).first()
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

    return {
        "access_token": f"token_user_{user.id}",
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@router.get("/profile", response_model=PatientProfileSchema)
def get_profile(user_id: int = 1, db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        profile = PatientProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/profile", response_model=PatientProfileSchema)
def update_profile(profile_data: PatientProfileSchema, user_id: int = 1, db: Session = Depends(get_db)):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == user_id).first()
    if not profile:
        profile = PatientProfile(user_id=user_id)
        db.add(profile)

    for field, val in profile_data.dict(exclude_unset=True).items():
        if field not in ["id", "user_id"]:
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile
