"""OCR utilities for extracting ship stats from Star Citizen screenshots."""

from __future__ import annotations

from difflib import SequenceMatcher
import os
import re

import cv2
import numpy as np
import pytesseract


def _ensure_tesseract_ready() -> None:
    """Configure Tesseract path on Windows when possible."""
    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd:
        pytesseract.pytesseract.tesseract_cmd = env_cmd

    if os.name == "nt":
        common_paths = [
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
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


def _normalize_label(text: str) -> str:
    text = text.upper().replace("_", " ")
    text = re.sub(r"[^A-Z0-9/ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_key(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", (text or "").upper())


def _clean_value(value: str) -> str:
    value = value.replace("|", "/")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _first_number(value: str) -> float | None:
    val = value.replace(" ", "")
    match = re.search(r"(\d+(?:[\.,]\d+)?)", val)
    if not match:
        return None
    return float(match.group(1).replace(",", "."))


def _has_digits(value: str) -> bool:
    return bool(re.search(r"\d", value or ""))


def _is_triplet_like(value: str) -> bool:
    return len(re.findall(r"\d+", value or "")) >= 3


def _is_time_like(value: str) -> bool:
    return bool(re.search(r"\d{1,2}:\d{2}:\d{2}", value or ""))


def _is_plain_text_like(value: str) -> bool:
    txt = _normalize_label(value)
    if not txt:
        return False
    if _has_digits(txt):
        return False
    # Exclude obvious units/noise captured by OCR.
    if any(k in txt for k in ("M/S", "DEG/S", "SCU", "AUEC", "KG", "HP")):
        return False
    return True


def _first_int(value: str) -> int | None:
    numbers = re.findall(r"\d+", value.replace(" ", ""))
    if not numbers:
        return None
    return int("".join(numbers))


def _triplet(value: str) -> tuple[int, int, int] | None:
    parts = re.findall(r"\d+", value)
    if len(parts) < 3:
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])


def _time_to_minutes(value: str) -> float | None:
    m = re.search(r"(\d{1,2}):(\d{2}):(\d{2})", value)
    if not m:
        return None
    hours = int(m.group(1))
    minutes = int(m.group(2))
    seconds = int(m.group(3))
    return round(hours * 60 + minutes + (seconds / 60.0), 2)


def _extract_field(lines: list[str], patterns: list[str]) -> str:
    for idx, line in enumerate(lines):
        normalized = _normalize_label(line)
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if not match:
                continue
            tail = normalized[match.end():].strip()
            if not tail:
                # Some OCR runs place the value on the next line.
                if idx + 1 < len(lines):
                    next_line = _normalize_label(lines[idx + 1])
                    if re.search(r"\d|:|/", next_line):
                        return _clean_value(next_line)
                continue
            return _clean_value(tail)
    return ""


def _preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)

    # Enhances contrast on dark UI backgrounds.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(enlarged)

    thr = cv2.adaptiveThreshold(
        contrast,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9,
    )
    return thr


def _preprocess_variants(img):
    base = _preprocess(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enlarged_gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    inv = cv2.bitwise_not(base)
    return [base, inv, enlarged_gray]

def _crop_by_ratio(img, x1: float, y1: float, x2: float, y2: float):
    height, width = img.shape[:2]
    xa = max(0, min(width, int(width * x1)))
    xb = max(0, min(width, int(width * x2)))
    ya = max(0, min(height, int(height * y1)))
    yb = max(0, min(height, int(height * y2)))
    if xb <= xa or yb <= ya:
        return None
    return img[ya:yb, xa:xb]

def _ocr_text_candidates(crop, psm: int, whitelist: str | None = None) -> list[str]:
    if crop is None or crop.size == 0:
        return []

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if len(crop.shape) == 3 else crop
    enlarged = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    thr = cv2.adaptiveThreshold(
        enlarged,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        8,
    )
    variants = [enlarged, thr, cv2.bitwise_not(thr)]

    extra = ""
    if whitelist:
        safe_whitelist = "".join(ch for ch in whitelist if ch.isalnum() or ch in " ./:")
        if safe_whitelist:
            extra = f" -c tessedit_char_whitelist={safe_whitelist}"

    results: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        text = pytesseract.image_to_string(variant, config=f"--oem 3 --psm {psm}{extra}")
        for raw in text.splitlines():
            cleaned = _clean_value(raw)
            if not cleaned:
                continue
            norm = _normalize_label(cleaned)
            if norm in seen:
                continue
            seen.add(norm)
            results.append(cleaned)
    return results


def _collect_ocr_candidates(crop, psms: list[int], whitelist: str | None = None) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for psm in psms:
        for candidate in _ocr_text_candidates(crop, psm=psm, whitelist=whitelist):
            norm = _normalize_label(candidate)
            if not norm or norm in seen:
                continue
            seen.add(norm)
            merged.append(candidate)
    return merged

def _pick_first_valid(candidates: list[str], validator) -> str:
    for candidate in candidates:
        if validator(candidate):
            return candidate
    return ""


def _token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(_normalize_label(left).split())
    right_tokens = set(_normalize_label(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(right_tokens), 1)


def _pick_reference_candidate(candidates: list[str], references: list[str], min_ratio: float = 0.45) -> str:
    refs = [_normalize_label(ref) for ref in references if _normalize_label(ref)]
    if not candidates or not refs:
        return ""

    best_value = ""
    best_ratio = 0.0
    for candidate in candidates:
        cand_norm = _normalize_label(candidate)
        if not cand_norm:
            continue
        cand_key = _normalize_key(cand_norm)
        for ref in refs:
            ref_key = _normalize_key(ref)
            seq_ratio = SequenceMatcher(None, cand_key, ref_key).ratio()
            overlap_ratio = _token_overlap_ratio(cand_norm, ref)
            ratio = max(seq_ratio, overlap_ratio)
            if ratio > best_ratio:
                best_ratio = ratio
                best_value = ref

    return best_value if best_value and best_ratio >= min_ratio else ""

def _extract_layout_fixed_stats(image_path: str, reference_data: dict | None = None) -> dict:
    img = _load_image(image_path)
    refs = reference_data or {}

    fixed: dict[str, object] = {}

    # Use a reference-aware header extraction for title fields.
    title_name, title_brand = _extract_title_fields(image_path, reference_data=reference_data)
    if title_name:
        fixed["name"] = title_name
    if title_brand:
        fixed["brand"] = title_brand

    # Role/career/size/crew sit on the same top row in the game card.
    role_crop = _crop_by_ratio(img, 0.60, 0.085, 0.98, 0.145)
    career_crop = _crop_by_ratio(img, 0.60, 0.125, 0.98, 0.185)
    size_crop = _crop_by_ratio(img, 0.74, 0.085, 0.88, 0.145)
    crew_crop = _crop_by_ratio(img, 0.88, 0.085, 0.99, 0.145)

    role_candidates = _collect_ocr_candidates(
        role_crop,
        psms=[7, 6, 8],
        whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
    )
    role_text = _pick_reference_candidate(role_candidates, refs.get("roles", []), min_ratio=0.34)

    career_candidates = _collect_ocr_candidates(
        career_crop,
        psms=[7, 6, 8],
        whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
    )
    career_text = _pick_reference_candidate(career_candidates, refs.get("careers", []), min_ratio=0.34)

    size_candidates = _collect_ocr_candidates(
        size_crop,
        psms=[7, 8],
        whitelist="Ss0123456789",
    )
    size_text = _pick_first_valid(size_candidates, lambda text: bool(re.search(r"\bS\s*\d\b", text.upper().replace(" ", ""))))

    crew_candidates = _collect_ocr_candidates(
        crew_crop,
        psms=[7, 8],
        whitelist="0123456789",
    )
    crew_text = _pick_first_valid(crew_candidates, lambda text: (_first_int(text) or 0) in range(1, 65))

    if role_text:
        fixed["role"] = _normalize_label(role_text)
    if career_text:
        fixed["career"] = _normalize_label(career_text)
    if size_text:
        m = re.search(r"S\s*(\d)", size_text.upper())
        if m:
            fixed["size"] = f"S{m.group(1)}"
    if crew_text:
        crew = _first_int(crew_text)
        if crew is not None and 1 <= crew <= 64:
            fixed["crew_size"] = crew

    return fixed


def _extract_title_fields(image_path: str, reference_data: dict | None = None) -> tuple[str, str]:
    img = _load_image(image_path)
    height, width = img.shape[:2]
    refs = reference_data or {}

    top_crop = img[0 : max(40, int(height * 0.14)), int(width * 0.05) : int(width * 0.95)]
    if top_crop.size == 0:
        return "", ""

    gray = cv2.cvtColor(top_crop, cv2.COLOR_BGR2GRAY)
    enlarged = cv2.resize(gray, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    thr = cv2.adaptiveThreshold(
        enlarged,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        8,
    )

    candidates: list[str] = []
    seen: set[str] = set()
    for proc in (enlarged, thr, cv2.bitwise_not(thr)):
        data = pytesseract.image_to_data(proc, config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)
        rows: dict[tuple[int, int, int], list[tuple[int, str]]] = {}
        total = len(data.get("text", []))
        for i in range(total):
            txt = str(data["text"][i] or "").strip()
            if not txt:
                continue
            try:
                conf = float(str(data.get("conf", ["-1"] * total)[i]).strip())
            except Exception:
                conf = -1.0
            if conf < 20:
                continue
            key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
            rows.setdefault(key, []).append((int(data["left"][i]), txt))

        ordered_lines = []
        for words in rows.values():
            words.sort(key=lambda item: item[0])
            line = " ".join(word for _, word in words).strip()
            norm = _normalize_label(line)
            if not norm or norm in seen:
                continue
            if len(norm.split()) > 6:
                continue
            seen.add(norm)
            ordered_lines.append(norm)

        candidates.extend(ordered_lines)

    deduped = []
    seen2 = set()
    for item in candidates:
        if item in seen2:
            continue
        seen2.add(item)
        deduped.append(item)

    brand = _pick_reference_candidate(deduped, refs.get("brands", []), min_ratio=0.55)

    # Name is safer as raw OCR header text than force-snapping to known ship names,
    # which can incorrectly map noisy text to short names like "ARROW".
    skip_tokens = {
        "PLAYERS", "ORGANIZATIONS", "SHIPS", "INTEL", "ARCHIVE", "SYSTEM",
        "ROLE", "CAREER", "SIZE", "CREW", "SCM", "SPEED", "BOOST", "NAV",
        "PITCH", "YAW", "ROLL", "POWER", "CONSUMPTION", "DECOY", "NOISE",
        "HP", "CARGO", "DIMENSIONS", "MASS", "HYDROGEN", "QT", "FUEL",
        "EXPEDITION", "CLAIM", "EXPEDITE", "TIME",
    }
    name = ""
    best_score = -1
    for candidate in deduped:
        cand_norm = _normalize_label(candidate)
        if not cand_norm:
            continue
        if brand and _normalize_key(cand_norm) == _normalize_key(brand):
            continue
        tokens = [t for t in cand_norm.split() if t]
        if not tokens:
            continue
        # Ignore header/menu and any line that contains stat labels.
        if any(token in skip_tokens for token in tokens):
            continue
        if all(token in skip_tokens for token in tokens):
            continue
        score = len(_normalize_key(cand_norm)) + (4 if len(tokens) >= 2 else 0)
        if any(ch.isdigit() for ch in cand_norm):
            score += 1
        if score > best_score:
            best_score = score
            name = cand_norm

    if not brand and len(deduped) > 1:
        for candidate in deduped:
            if candidate != name and (len(candidate) >= 5 or " " in candidate):
                brand = candidate
                break
    if name and brand and _normalize_key(name) == _normalize_key(brand):
        name = ""

    return name, brand


def _load_image(image_path: str):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image introuvable: {image_path}")

    _ensure_tesseract_ready()

    # cv2.imread can fail on Windows when path contains special unicode chars.
    img = None
    normalized_path = os.path.normpath(image_path)
    try:
        data = np.fromfile(normalized_path, dtype=np.uint8)
        if data.size > 0:
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        img = None

    if img is None:
        img = cv2.imread(normalized_path)

    if img is None:
        raise ValueError(
            "Impossible de charger l'image fournie (chemin/fichier invalide ou format non supporte)."
        )

    return img


def _best_alias_score(label_key: str, alias_keys: list[str]) -> float:
    best = 0.0
    for alias in alias_keys:
        if not alias:
            continue
        # For very short aliases like HP, avoid permissive substring matches.
        if len(alias) > 3 and (alias in label_key or label_key in alias):
            best = max(best, 1.0)
            continue
        if len(alias) <= 3 and label_key == alias:
            best = max(best, 1.0)
            continue
        best = max(best, SequenceMatcher(None, label_key, alias).ratio())
    return best


def _snap_to_reference(
    value: str,
    candidates: list[str],
    min_ratio: float = 0.74,
    strict: bool = False,
) -> str:
    """Return closest candidate if OCR value is similar enough.

    If strict=True and no candidate matches enough, return empty string.
    """
    raw = _normalize_label(value)
    if not raw:
        return ""

    options = [
        _normalize_label(c)
        for c in (candidates or [])
        if _normalize_label(c)
    ]
    if not options:
        return "" if strict else raw

    raw_key = _normalize_key(raw)
    best = ""
    best_ratio = 0.0
    for opt in options:
        opt_key = _normalize_key(opt)
        ratio = SequenceMatcher(None, raw_key, opt_key).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best = opt

    if best and best_ratio >= min_ratio:
        return best
    return "" if strict else raw


def _aliases_to_patterns(aliases: list[str]) -> list[str]:
    patterns = []
    for alias in aliases:
        tokens = re.findall(r"[A-Z0-9]+", alias.upper())
        if not tokens:
            continue
        patterns.append(r"\\b" + r"\\s*".join(tokens) + r"\\b")
    return patterns


def _ocr_artifacts(image_path: str) -> tuple[list[str], list[tuple[str, str]]]:
    img = _load_image(image_path)
    variants = _preprocess_variants(img)
    width = variants[0].shape[1]
    split_x = int(width * 0.50)

    merged_lines: list[str] = []
    merged_pairs: list[tuple[str, str]] = []
    seen_lines: set[str] = set()
    seen_pairs: set[str] = set()
    row_lines: list[tuple[int, str]] = []

    for proc in variants:
        for psm in ("4", "6", "11", "12"):
            config = f"--oem 3 --psm {psm}"

            text = pytesseract.image_to_string(proc, config=config)
            for raw in text.splitlines():
                line = raw.strip()
                if len(line) < 2:
                    continue
                norm = _normalize_label(line)
                if not norm or norm in seen_lines:
                    continue
                seen_lines.add(norm)
                merged_lines.append(line)

            data = pytesseract.image_to_data(
                proc,
                config=config,
                output_type=pytesseract.Output.DICT,
            )

            rows: dict[tuple[int, int, int], list[tuple[int, int, int, int, str]]] = {}
            total = len(data.get("text", []))
            for i in range(total):
                txt = str(data["text"][i] or "").strip()
                if not txt:
                    continue

                conf_raw = str(data.get("conf", ["-1"] * total)[i]).strip()
                try:
                    conf = float(conf_raw)
                except Exception:
                    conf = -1.0
                if conf < 0:
                    continue

                x = int(data["left"][i])
                y = int(data["top"][i])
                w = int(data["width"][i])
                h = int(data["height"][i])
                key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
                rows.setdefault(key, []).append((x, y, w, h, txt))

            for words in rows.values():
                words.sort(key=lambda it: it[0])
                full_line = " ".join(w[4] for w in words).strip()
                if not full_line:
                    continue

                row_y = min(w[1] for w in words)
                row_lines.append((row_y, full_line))

                line_norm = _normalize_label(full_line)
                if line_norm and line_norm not in seen_lines:
                    seen_lines.add(line_norm)
                    merged_lines.append(full_line)

                left_words = [w[4] for w in words if (w[0] + (w[2] // 2)) <= split_x]
                right_words = [w[4] for w in words if (w[0] + (w[2] // 2)) > split_x]

                label = _clean_value(" ".join(left_words))
                value = _clean_value(" ".join(right_words))

                if not label and full_line:
                    m = re.search(r"\d", full_line)
                    if m:
                        label = _clean_value(full_line[: m.start()])
                        value = _clean_value(full_line[m.start() :])

                if label and not value:
                    label_norm = _normalize_label(label)
                    full_norm = _normalize_label(full_line)
                    if full_norm.startswith(label_norm):
                        tail = _clean_value(full_norm[len(label_norm) :])
                        if tail:
                            value = tail

                if not label or not value:
                    continue

                pair_key = f"{_normalize_key(label)}=>{_normalize_key(value)}"
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                merged_pairs.append((label, value))

    # Keep a top-to-bottom ordered set of OCR lines for title detection and regex fallback.
    for _y, full_line in sorted(row_lines, key=lambda r: r[0]):
        norm = _normalize_label(full_line)
        if not norm or norm in seen_lines:
            continue
        seen_lines.add(norm)
        merged_lines.insert(0, full_line)

    return merged_lines, merged_pairs


def _extract_from_pairs_or_lines(
    lines: list[str],
    pairs: list[tuple[str, str]],
    aliases: list[str],
    min_score: float = 0.62,
    validator=None,
) -> str:
    alias_keys = [_normalize_key(a) for a in aliases]

    best_value = ""
    best_score = 0.0
    for label, value in pairs:
        score = _best_alias_score(_normalize_key(label), alias_keys)
        val = _clean_value(value)
        if validator is not None and not validator(val):
            continue
        if score >= min_score and score > best_score:
            best_value = val
            best_score = score

    if best_value:
        return best_value

    raw = _extract_field(lines, _aliases_to_patterns(aliases))
    if validator is not None and raw and not validator(raw):
        return ""
    return raw


def _infer_name_from_reference_context(stats: dict, reference_data: dict | None = None) -> str:
    refs = reference_data or {}
    records = refs.get("ship_records", []) or []
    if not records:
        return ""

    brand = _normalize_label(str(stats.get("brand", "")))
    role = _normalize_label(str(stats.get("role", "")))
    career = _normalize_label(str(stats.get("career", "")))

    if not brand and not role and not career:
        return ""

    filtered = records
    if brand:
        filtered = [r for r in filtered if _normalize_label(str(r.get("brand", ""))) == brand]
    if role:
        filtered = [r for r in filtered if _normalize_label(str(r.get("role", ""))) == role]
    if career:
        filtered = [r for r in filtered if _normalize_label(str(r.get("career", ""))) == career]

    candidate_names = sorted(
        {
            _normalize_label(str(r.get("name", "")))
            for r in filtered
            if _normalize_label(str(r.get("name", "")))
        }
    )
    if len(candidate_names) == 1:
        return candidate_names[0]
    return ""


def extract_ship_stats(image_path: str, reference_data: dict | None = None) -> dict:
    """Extract ship stats from a screenshot and return keys matching ships columns."""
    lines, pairs = _ocr_artifacts(image_path)
    title_name, title_brand = _extract_title_fields(image_path, reference_data=reference_data)
    fixed_stats = _extract_layout_fixed_stats(image_path, reference_data=reference_data)

    stats: dict[str, object] = {}

    # The title block is usually NAME then BRAND on the first lines.
    title_candidates = [l.strip() for l in lines[:8] if l.strip()]
    labels = {
        "ROLE", "CAREER", "SIZE", "CREW SIZE", "SCM SPEED", "NAV MAX SPEED", "BOOSTED", "HP",
        "SCM BOOST SPEED FORWARD", "SCM BOOST SPEED BACKWARD", "PITCH/YAW/ROLL"
    }
    plain_titles = [
        t for t in title_candidates
        if _normalize_label(t) not in labels
        and len(t.split()) <= 4
        and not _has_digits(t)
    ]
    if title_name:
        stats["name"] = title_name.upper().strip()
    elif plain_titles:
        name_val = plain_titles[0].upper().strip()
        if len(name_val) >= 2:
            stats["name"] = name_val
    if title_brand:
        stats["brand"] = title_brand.upper().strip()
    elif len(plain_titles) > 1:
        brand_val = plain_titles[1].upper().strip()
        if len(brand_val) >= 5 or " " in brand_val:
            stats["brand"] = brand_val

    raw_role = _extract_from_pairs_or_lines(lines, pairs, ["ROLE"], min_score=0.8, validator=_is_plain_text_like)
    if raw_role:
        stats["role"] = raw_role.upper()

    raw_career = _extract_from_pairs_or_lines(lines, pairs, ["CAREER"], min_score=0.8, validator=_is_plain_text_like)
    if raw_career:
        stats["career"] = raw_career.upper()

    raw_size = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["SIZE"],
        min_score=0.8,
        validator=lambda v: bool(re.search(r"\bS\d\b", v.upper().replace(" ", ""))),
    )
    if raw_size:
        m_size = re.search(r"S\s*(\d)", raw_size.upper())
        if m_size:
            stats["size"] = f"S{m_size.group(1)}"

    raw_crew = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["CREW SIZE", "CREWSIZE", "CREW"],
        min_score=0.78,
        validator=lambda v: _first_int(v) is not None,
    )
    crew = _first_int(raw_crew)
    if crew is not None:
        stats["crew_size"] = crew

    raw_scm = _extract_from_pairs_or_lines(lines, pairs, ["SCM SPEED", "SCMSPEED"])
    scm = _first_int(raw_scm)
    if scm is not None:
        stats["scm_speed"] = scm

    raw_boost_fw = _extract_from_pairs_or_lines(
        lines,
        pairs,
        [
            "SCM BOOST SPEED FORWARD",
            "SCM BOOST FORWARD",
            "SCMBOOSTSPEEDFORWARD",
            "BOOST FORWARD",
        ],
        min_score=0.78,
        validator=lambda v: _first_int(v) is not None,
    )
    boost_fw = _first_int(raw_boost_fw)
    if boost_fw is not None:
        stats["scm_boost_forward"] = boost_fw

    raw_boost_bw = _extract_from_pairs_or_lines(
        lines,
        pairs,
        [
            "SCM BOOST SPEED BACKWARD",
            "SCM BOOST BACKWARD",
            "SCMBOOSTSPEEDBACKWARD",
            "BOOST BACKWARD",
        ],
        min_score=0.78,
        validator=lambda v: _first_int(v) is not None,
    )
    boost_bw = _first_int(raw_boost_bw)
    if boost_bw is not None:
        stats["scm_boost_backward"] = boost_bw

    raw_nav = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["NAV MAX SPEED", "NAV SPEED", "NAVMAXSPEED"],
        min_score=0.78,
        validator=lambda v: _first_int(v) is not None,
    )
    nav = _first_int(raw_nav)
    if nav is not None:
        stats["nav_max_speed"] = nav

    raw_pyr = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["PITCH/YAW/ROLL", "PITCH YAW ROLL"],
        min_score=0.78,
        validator=_is_triplet_like,
    )
    pyr = _triplet(raw_pyr)
    if pyr:
        stats["pitch"], stats["yaw"], stats["roll"] = pyr

    raw_boosted = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["BOOSTED", "BOOST"],
        min_score=0.78,
        validator=_is_triplet_like,
    )
    boosted = _triplet(raw_boosted)
    if boosted:
        stats["boosted_pitch"], stats["boosted_yaw"], stats["boosted_roll"] = boosted

    raw_power = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["POWER CONSUMPTION", "POWERCONSUMPTION"],
        min_score=0.78,
        validator=lambda v: _first_int(v) is not None,
    )
    power = _first_int(raw_power)
    if power is not None:
        stats["power_consumption"] = str(power)

    raw_cm = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["CM DECOY/NOISE", "CM DECOY NOISE", "CMDECOYNOISE"],
        min_score=0.76,
        validator=lambda v: len(re.findall(r"\d+", v)) >= 2,
    )
    if raw_cm:
        cm_vals = re.findall(r"\d+", raw_cm)
        if len(cm_vals) >= 2:
            stats["cm_decoy_noise"] = f"{cm_vals[0]}/{cm_vals[1]}"

    raw_hp = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["HP"],
        min_score=0.8,
        validator=lambda v: _first_int(v) is not None,
    )
    hp = _first_int(raw_hp)
    if hp is not None:
        stats["hp"] = hp

    raw_cargo = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["CARGO", "CARGO CAPACITY"],
        min_score=0.8,
        validator=lambda v: _first_int(v) is not None,
    )
    cargo = _first_int(raw_cargo)
    if cargo is not None:
        stats["cargo"] = cargo

    raw_dimensions = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["DIMENSIONS", "DIMENTIONS", "DIMENSION"],
        min_score=0.76,
        validator=lambda v: bool(re.search(r"\d", v)),
    )
    if raw_dimensions:
        stats["dimensions"] = raw_dimensions.upper()

    raw_mass = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["MASS"],
        min_score=0.8,
        validator=lambda v: _first_int(v) is not None,
    )
    if raw_mass:
        stats["mass"] = raw_mass.upper()

    raw_h2 = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["HYDROGEN CAPACITY", "HYDROGENCAPACITY", "HYDROGEN"],
        min_score=0.76,
        validator=lambda v: _first_number(v) is not None,
    )
    h2 = _first_number(raw_h2)
    if h2 is not None:
        stats["hydrogen_capacity"] = h2

    raw_qt = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["QT FUEL CAPACITY", "QTFUELCAPACITY", "QTFUEL", "QT FUEL"],
        min_score=0.76,
        validator=lambda v: _first_number(v) is not None,
    )
    qt = _first_number(raw_qt)
    if qt is not None:
        stats["qt_fuel_capacity"] = qt

    raw_fee = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["EXPEDITION FEE", "EXPEDITIONFEE"],
        min_score=0.76,
        validator=lambda v: (_first_int(v) is not None)
        and ("M/S" not in v.upper())
        and ("DEG" not in v.upper())
        and (_first_int(v) or 0) >= 500,
    )
    if raw_fee:
        stats["expedition_fee"] = raw_fee.upper()

    raw_claim = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["CLAIM TIME", "CLAIMTIME"],
        min_score=0.76,
        validator=_is_time_like,
    )
    claim_minutes = _time_to_minutes(raw_claim)
    if claim_minutes is not None:
        stats["claim_time"] = claim_minutes

    raw_expedite = _extract_from_pairs_or_lines(
        lines,
        pairs,
        ["EXPEDITE TIME", "EXPEDITETIME"],
        min_score=0.76,
        validator=_is_time_like,
    )
    expedite_minutes = _time_to_minutes(raw_expedite)
    if expedite_minutes is not None:
        stats["expedite_time"] = expedite_minutes

    # Sanity rules: avoid obvious cross-field contamination.
    scm = stats.get("scm_speed")
    nav = stats.get("nav_max_speed")
    hp = stats.get("hp")
    if isinstance(scm, int) and isinstance(nav, int) and nav <= scm:
        stats.pop("nav_max_speed", None)
    if isinstance(scm, int) and isinstance(hp, int) and abs(hp - scm) <= 1:
        stats.pop("hp", None)

    # Layout-fixed extraction has priority when available for the standardized SC ship stat screen.
    stats.update(fixed_stats)

    # Optional dictionary-assisted correction to reduce OCR false positives.
    refs = reference_data or {}
    if isinstance(stats.get("name"), str):
        stats["name"] = _normalize_label(stats["name"])
        if len(stats["name"]) < 3:
            stats.pop("name", None)
        elif isinstance(stats.get("brand"), str):
            if _normalize_key(stats["name"]) == _normalize_key(stats["brand"]):
                stats.pop("name", None)
    if isinstance(stats.get("brand"), str):
        stats["brand"] = _snap_to_reference(
            stats["brand"],
            refs.get("brands", []),
            min_ratio=0.70,
            strict=True,
        )
    if isinstance(stats.get("role"), str):
        stats["role"] = _snap_to_reference(
            stats["role"],
            refs.get("roles", []),
            min_ratio=0.52,
            strict=True,
        )
    if isinstance(stats.get("career"), str):
        stats["career"] = _snap_to_reference(
            stats["career"],
            refs.get("careers", []),
            min_ratio=0.52,
            strict=True,
        )

    # If OCR name is noisy, infer from unique brand+role+career match in DB.
    inferred_name = _infer_name_from_reference_context(stats, reference_data=reference_data)
    if inferred_name:
        current_name = _normalize_label(str(stats.get("name", "")))
        strong_name = _snap_to_reference(current_name, refs.get("names", []), min_ratio=0.90, strict=True)
        if not strong_name:
            stats["name"] = inferred_name

    # Reject obvious cross-field contamination values.
    crew = stats.get("crew_size")
    if isinstance(crew, int) and not (1 <= crew <= 64):
        stats.pop("crew_size", None)

    scm_speed = stats.get("scm_speed")
    if isinstance(scm_speed, int) and not (50 <= scm_speed <= 700):
        stats.pop("scm_speed", None)

    nav_speed = stats.get("nav_max_speed")
    if isinstance(nav_speed, int) and not (300 <= nav_speed <= 2500):
        stats.pop("nav_max_speed", None)

    power_text = str(stats.get("power_consumption", "")).strip()
    power_num = _first_int(power_text)
    if power_num is not None and not (1 <= power_num <= 200):
        stats.pop("power_consumption", None)

    h2_cap = stats.get("hydrogen_capacity")
    if isinstance(h2_cap, (float, int)) and not (0.1 <= float(h2_cap) <= 300.0):
        stats.pop("hydrogen_capacity", None)

    qt_cap = stats.get("qt_fuel_capacity")
    if isinstance(qt_cap, (float, int)) and not (0.1 <= float(qt_cap) <= 50.0):
        stats.pop("qt_fuel_capacity", None)

    dims = str(stats.get("dimensions", "")).upper()
    if dims and "X" not in dims:
        stats.pop("dimensions", None)

    mass_text = str(stats.get("mass", "")).upper().strip()
    if mass_text and ("MVS" in mass_text or "M/S" in mass_text):
        stats.pop("mass", None)

    fee_text = str(stats.get("expedition_fee", "")).upper().strip()
    if fee_text and ("MS" in fee_text or "M/S" in fee_text):
        stats.pop("expedition_fee", None)

    if stats.get("name") and stats.get("brand"):
        if _normalize_key(str(stats["name"])) == _normalize_key(str(stats["brand"])):
            stats.pop("name", None)

    return stats
