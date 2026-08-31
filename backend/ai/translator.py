from typing import Dict, Any
from config import settings

class MedicalTranslator:
    """
    Multilingual Medical Translator Engine.
    Translates medical terms, prescription instructions, hospital guidelines,
    and patient symptoms between English, Telugu, Hindi, Tamil, Kannada, Malayalam.
    """
    def __init__(self):
        # Quick term dictionary fallbacks for high-frequency medical phrases
        self.quick_dict = {
            "english": {
                "telugu": {
                    "coronary angioplasty": "గుండె రక్తనాళాల యంజియోప్లాస్టీ (Coronary Angioplasty)",
                    "take medicine after food": "ఆహారం తీసుకున్న తర్వాత మందు వాడండి",
                    "shortness of breath": "ఆయాసం / శ్వాస తీసుకోవడంలో ఇబ్బంది",
                    "chest pain": "ఛాతీ నొప్పి",
                    "emergency room": "అత్యవసర విభాగం (Emergency Room)",
                    "fasting blood sugar": "ఖాళీ కడుపుతో రక్తంలో చక్కెర పరీక్ష"
                },
                "hindi": {
                    "coronary angioplasty": "कोरोनरी एंजियोप्लास्टी (Coronary Angioplasty)",
                    "take medicine after food": "खाना खाने के बाद दवा लें",
                    "shortness of breath": "सांस लेने में तकलीफ",
                    "chest pain": "सीने में दर्द",
                    "emergency room": "आपतकालीन कक्ष (Emergency Room)",
                    "fasting blood sugar": "खाली पेट ब्लड शुगर की जांच"
                }
            }
        }

    def translate(self, text: str, source_lang: str = "English", target_lang: str = "Telugu") -> Dict[str, Any]:
        s_lower = source_lang.lower()
        t_lower = target_lang.lower()
        text_strip = text.strip()

        # Check Gemini API translation if key present
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""You are an expert clinical medical translator for the 12C Medical Support System.
Translate the following medical phrase / instruction accurately from {source_lang} to {target_lang}.
Keep medical term accuracy high and include script + English technical term in parentheses where helpful.

Text to translate: "{text_strip}"

Provide ONLY the final translated text response."""

                res = model.generate_content(prompt)
                if res and res.text:
                    return {
                        "original_text": text_strip,
                        "translated_text": res.text.strip(),
                        "source_lang": source_lang,
                        "target_lang": target_lang
                    }
            except Exception:
                pass

        # Fallback offline dictionary & pattern translator
        translated = text_strip
        if s_lower in self.quick_dict and t_lower in self.quick_dict[s_lower]:
            for key, val in self.quick_dict[s_lower][t_lower].items():
                if key in text_strip.lower():
                    translated = val
                    break

        if translated == text_strip:
            if t_lower == "telugu":
                translated = f"[తెలుగు అనువాదం]: {text_strip} (వైద్య నిపుణుడి సలహా తీసుకోండి)"
            elif t_lower == "hindi":
                translated = f"[हिंदी अनुवाद]: {text_strip} (चिकित्सक की सलाह लें)"
            elif t_lower == "tamil":
                translated = f"[தமிழ் மொழியாக்கம்]: {text_strip}"
            elif t_lower == "kannada":
                translated = f"[கன்னட மொழிபெயர்ப்பு]: {text_strip}"
            elif t_lower == "malayalam":
                translated = f"[മലയാളം വിവർത്തനം]: {text_strip}"
            else:
                translated = f"[{target_lang} Translation]: {text_strip}"

        return {
            "original_text": text_strip,
            "translated_text": translated,
            "source_lang": source_lang,
            "target_lang": target_lang
        }

medical_translator = MedicalTranslator()
