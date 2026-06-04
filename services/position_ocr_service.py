"""OCR service for extracting position coordinates from Star Citizen screenshots.

Reads the 'CamPos Planet Zone: X Y Z' and 'Current player location' lines
from the top-right debug overlay (F3 overlay in Star Citizen).
"""

from __future__ import annotations

import re
import os
import cv2
import numpy as np
import pytesseract


def _ensure_tesseract_ready() -> None:
    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd:
        pytesseract.pytesseract.tesseract_cmd = env_cmd

    if os.name == "nt":
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Programs\Tesseract-OCR\tesseract.exe"),
        ]
        if not os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")):
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break

    try:
        pytesseract.get_tesseract_version()
    except Exception as exc:
        raise RuntimeError(
            "Tesseract OCR introuvable. Installez Tesseract et/ou définissez TESSERACT_CMD."
        ) from exc


def _preprocess(gray: np.ndarray) -> list[np.ndarray]:
    """Returns multiple preprocessed variants of the image."""
    variants = []
    _, thresh1 = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY)
    variants.append(thresh1)
    _, thresh2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants.append(thresh2)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 15, 4)
    variants.append(adaptive)
    scaled = []
    for v in variants:
        scaled.append(cv2.resize(v, (v.shape[1] * 2, v.shape[0] * 2), interpolation=cv2.INTER_CUBIC))
    return scaled


def read_position_from_screenshot(image_path: str) -> dict:
    """Extracts X, Y, Z coordinates and location name from a Star Citizen screenshot.

    Reads:
    - 'CamPos Planet Zone: X Y Z' for coordinates
    - 'Current player location : <name>' for location name

    Returns:
        dict with keys 'x', 'y', 'z' (floats), 'location_name' (str|None), 'ok' (bool), 'message' (str).
    """
    _ensure_tesseract_ready()

    img = cv2.imread(image_path)
    if img is None:
        return {"ok": False, "message": f"Cannot open image: {image_path}",
                "x": None, "y": None, "z": None, "location_name": None}

    h, w = img.shape[:2]

    # The debug overlay is on the right half, top 60% of the screen
    crop_defs = [
        (0, int(w * 0.50), int(h * 0.45), w),   # right 50%, top 45%
        (0, int(w * 0.45), int(h * 0.55), w),   # right 55%, top 55%
        (0, int(w * 0.40), int(h * 0.65), w),   # right 60%, top 65%
        (0, 0,             int(h * 0.65), w),    # full width, top 65%
    ]

    config = "--psm 6"
    all_raw_texts = []

    coords_result = {"ok": False, "x": None, "y": None, "z": None}
    location_name = None

    for y1, x1, y2, x2 in crop_defs:
        crop = img[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        for variant in _preprocess(gray):
            raw = pytesseract.image_to_string(variant, config=config)
            all_raw_texts.append(raw)

            if not coords_result["ok"]:
                r = _parse_campos_line(raw)
                if r["ok"]:
                    coords_result = r

            if location_name is None:
                location_name = _parse_location_name(raw)

            if coords_result["ok"] and location_name is not None:
                break
        if coords_result["ok"] and location_name is not None:
            break

    if coords_result["ok"]:
        msg_parts = ["Coordinates extracted successfully."]
        if location_name:
            msg_parts.append(f"Location: {location_name}")
        return {
            "ok": True,
            "message": " ".join(msg_parts),
            "x": coords_result["x"],
            "y": coords_result["y"],
            "z": coords_result["z"],
            "location_name": location_name,
        }

    # Failed — show raw OCR output for diagnosis
    raw_preview = all_raw_texts[0][:500] if all_raw_texts else ""
    return {
        "ok": False,
        "message": (
            "No 'CamPos Planet Zone' coordinates found in image.\n\n"
            "Make sure the F3 debug overlay is visible in the top-right corner "
            "of the screenshot.\n\nOCR raw (first crop):\n" + raw_preview
        ),
        "x": None,
        "y": None,
        "z": None,
        "location_name": None,
    }


def _parse_campos_line(text: str) -> dict:
    """Parses the 'CamPos Planet Zone: X Y Z' line."""
    float_pat = r"([-+]?\d[\d\s]*\.[\d\s]*)"

    patterns = [
        r"[Cc]am[Pp]os\s+[Pp]lanet\s+[Zz]one\s*:?\s*" + float_pat + r"\s+" + float_pat + r"\s+" + float_pat,
        r"[Pp]lanet\s+[Zz]one\s*:?\s*" + float_pat + r"\s+" + float_pat + r"\s+" + float_pat,
        r"[Zz]one\s*:?\s*([-+]?\d{5,}\.[\d]+)\s+([-+]?\d{4,}\.[\d]+)\s+([-+]?\d+\.[\d]+)",
        r"([-+]?\d{7,}\.\d+)\s+([-+]?\d{7,}\.\d+)\s+([-+]?\d+\.\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                x = float(match.group(1).replace(" ", ""))
                y = float(match.group(2).replace(" ", ""))
                z = float(match.group(3).replace(" ", ""))
                return {"ok": True, "x": x, "y": y, "z": z}
            except (ValueError, IndexError):
                continue

    return {"ok": False, "x": None, "y": None, "z": None}


def _parse_location_name(text: str) -> str | None:
    """Parses the 'Current player location : <name>' line."""
    patterns = [
        r"[Cc]urrent\s+player\s+location\s*:?\s*(.+)",
        r"player\s+location\s*:?\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up common OCR artifacts
            name = re.sub(r"[^A-Za-z0-9 _\-]", "", name).strip()
            # Normalize spaces and uppercase
            name = re.sub(r"\s+", " ", name).strip().upper()
            if len(name) >= 3:
                return name
    return None
