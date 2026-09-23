import os
import io
import re
import shutil
import numpy as np
from PIL import Image

# Setup Tesseract binary executable path
try:
    import pytesseract
    tesseract_candidates = [
        shutil.which("tesseract"),
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for cand in tesseract_candidates:
        if cand and os.path.exists(cand):
            pytesseract.pytesseract.tesseract_cmd = cand
            break
except Exception:
    pytesseract = None


class OCREngine:
    """
    Robust Optical Character Recognition (OCR) Engine for Medical Documents.
    Supports:
    - Text-based digital PDFs (direct native text extraction)
    - Scanned/rasterized PDFs (page-by-page rendering + OpenCV preprocessing + Tesseract OCR)
    - Image formats: PNG, JPG, JPEG, WEBP, TIFF, BMP (OpenCV preprocessing + Tesseract OCR)
    - Plain text files (UTF-8 decode)

    Image Preprocessing Pipeline:
    1. Grayscale conversion
    2. Resolution normalization / scaling (for optimal 300 DPI text recognition)
    3. CLAHE (Contrast Limited Adaptive Histogram Equalization) for lighting normalization
    4. Bilateral filtering for denoising without blurring text edges
    5. Deskewing via minimum bounding box angle detection
    6. Adaptive/Otsu binarization
    """

    def __init__(self):
        self.tesseract_available = pytesseract is not None and bool(shutil.which("tesseract") or os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")))

    def preprocess_image(self, pil_img: Image.Image) -> np.ndarray:
        """
        Applies OpenCV image preprocessing to significantly enhance OCR accuracy on
        clinical scans, photos, and faxed reports.
        """
        import cv2

        # Convert PIL image to OpenCV numpy array (BGR format)
        img_arr = np.array(pil_img)
        if len(img_arr.shape) == 3:
            if img_arr.shape[2] == 4:
                bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGBA2BGR)
            else:
                bgr = cv2.cvtColor(img_arr, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_arr

        # 1. Resolution Normalization / Resizing
        h, w = gray.shape[:2]
        if w < 1100 or h < 1100:
            scale = max(1100 / max(w, 1), 1100 / max(h, 1))
            scale = min(scale, 3.0)
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
        elif w > 3500 or h > 3500:
            scale = min(3500 / w, 3500 / h)
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        # 2. Contrast Enhancement via CLAHE (equalizes phone shadows / dark scan corners)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 3. Bilateral Filter Denoising (removes scanner grain & paper texture while preserving sharp text borders)
        denoised = cv2.bilateralFilter(enhanced, d=7, sigmaColor=50, sigmaSpace=50)

        # 4. Deskewing
        try:
            # Detect text pixels (typically dark text on light background)
            coords = np.column_stack(np.where(denoised < 200))
            if len(coords) > 200:
                rect = cv2.minAreaRect(coords)
                angle = rect[-1]
                if angle < -45:
                    angle = -(90 + angle)
                elif angle > 45:
                    angle = 90 - angle
                else:
                    angle = -angle

                # Only rotate if the skew is noticeable and within realistic rotation range
                if 0.5 < abs(angle) < 40.0:
                    (dh, dw) = denoised.shape[:2]
                    center = (dw // 2, dh // 2)
                    m = cv2.getRotationMatrix2D(center, angle, 1.0)
                    denoised = cv2.warpAffine(
                        denoised, m, (dw, dh),
                        flags=cv2.INTER_CUBIC,
                        borderMode=cv2.BORDER_REPLICATE
                    )
        except Exception:
            pass

        return denoised

    def _ocr_image_array(self, cv_img: np.ndarray) -> str:
        """Runs Tesseract OCR on a preprocessed OpenCV image array with layout & table support."""
        if not self.tesseract_available or pytesseract is None:
            return ""

        import cv2

        candidates = []

        # Pass 1: Standard layout analysis (psm 3)
        try:
            t1 = pytesseract.image_to_string(cv_img, config="--oem 3 --psm 3")
            if t1 and len(t1.strip()) > 20:
                candidates.append(t1.strip())
        except Exception:
            pass

        # Pass 2: Tabular / single uniform block analysis (psm 6) on Otsu threshold
        try:
            _, thresh = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            t2 = pytesseract.image_to_string(thresh, config="--oem 3 --psm 6")
            if t2 and len(t2.strip()) > 20:
                candidates.append(t2.strip())
        except Exception:
            pass

        # Pass 3: Column / variable text block (psm 4)
        if not candidates:
            try:
                t3 = pytesseract.image_to_string(cv_img, config="--oem 3 --psm 4")
                if t3 and len(t3.strip()) > 20:
                    candidates.append(t3.strip())
            except Exception:
                pass

        if not candidates:
            return ""

        # Select the candidate with highest alphanumeric density and length
        best = max(candidates, key=lambda s: (sum(1 for c in s if c.isalnum()), len(s)))
        return best

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """
        Intelligently extracts text from a PDF document:
        1. First attempts digital text extraction via pypdf with layout mode for table column alignment.
        2. If extracted text is empty or insufficient (< 50 chars), classifies as scanned PDF,
           rasterizes each page via pypdfium2 at high DPI, and runs OCR with OpenCV preprocessing.
        """
        # Step 1: Digital text extraction with layout awareness
        extracted_pages = []
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                try:
                    page_text = page.extract_text(extraction_mode="layout") or ""
                except Exception:
                    page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_pages.append(page_text.strip())

            full_text = "\n\n".join(extracted_pages).strip()
            # Verify if digital text is genuine readable content
            alpha_chars = sum(1 for c in full_text if c.isalnum())
            if len(full_text) >= 50 and alpha_chars >= 30:
                return full_text
        except Exception:
            pass


        # Step 2: Scanned / rasterized PDF extraction
        try:
            import pypdfium2 as pdfium
            doc = pdfium.PdfDocument(file_bytes)
            ocr_pages = []
            max_pages = min(len(doc), 10)  # Safeguard processing budget

            for i in range(max_pages):
                page = doc[i]
                # Render at 2.0x scale (equivalent to ~150-300 DPI)
                pil_page = page.render(scale=2.0).to_pil()
                preprocessed = self.preprocess_image(pil_page)
                page_text = self._ocr_image_array(preprocessed)
                if page_text:
                    ocr_pages.append(f"--- Page {i + 1} ---\n{page_text}")

            if ocr_pages:
                return "\n\n".join(ocr_pages).strip()
        except Exception:
            pass

        return ""

    def extract_text_from_image(self, file_bytes: bytes) -> str:
        """Loads an image file, preprocesses it with OpenCV, and runs Tesseract OCR."""
        try:
            pil_img = Image.open(io.BytesIO(file_bytes))
            preprocessed = self.preprocess_image(pil_img)
            return self._ocr_image_array(preprocessed)
        except Exception:
            return ""

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """
        Main entry point for document intelligence extraction.
        Routes to PDF or Image parser based on file format.
        Does NOT use any hardcoded filename or mock data fallbacks.
        """
        if not file_bytes:
            return ""

        ext = os.path.splitext(filename)[1].lower()

        # 1. PDF documents
        if ext == ".pdf":
            text = self.extract_text_from_pdf(file_bytes)
            if text:
                return text

        # 2. Standard image formats
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"]:
            text = self.extract_text_from_image(file_bytes)
            if text:
                return text

        # 3. Plain text / fallback decoding
        elif ext in [".txt", ".log", ".csv"]:
            try:
                return file_bytes.decode("utf-8", errors="replace").strip()
            except Exception:
                pass

        # 4. If extension is missing or unusual, attempt image decode then PDF decode
        text = self.extract_text_from_image(file_bytes)
        if text:
            return text

        return self.extract_text_from_pdf(file_bytes)

    def validate_extracted_text(self, text: str) -> tuple[bool, str]:
        """
        Validates whether extracted OCR text contains genuine, readable document content
        rather than noise, corruption, or an empty page.

        Returns:
            (is_valid: bool, validation_message: str)
        """
        if not text or not text.strip():
            return False, "Document contains no readable text or is completely blank."

        cleaned = text.strip()
        if len(cleaned) < 20:
            return False, f"Extracted text is too short ({len(cleaned)} chars) to constitute a valid medical report."

        # Check alphanumeric content ratio (avoids scanner noise like '###!@&^')
        alpha_count = sum(1 for c in cleaned if c.isalnum())
        ratio = alpha_count / max(len(cleaned), 1)
        if ratio < 0.30:
            return False, f"Document has low text density ({ratio:.1%}). May be an unreadable image or high-noise scan."

        # Check for meaningful word tokens
        words = re.findall(r'[a-zA-Z0-9]{2,}', cleaned)
        if len(words) < 3:
            return False, "Extracted content does not contain recognizable clinical or linguistic words."

        return True, "Valid document content successfully extracted."


ocr_engine = OCREngine()
