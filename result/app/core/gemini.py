"""
EasyOCR 기반 제품명 및 유통기한 인식 모듈
Gemini API 없이 로컬에서 동작
"""

import os
import re
from datetime import datetime
from typing import Optional, Tuple

import cv2
import easyocr
import numpy as np


# ── 전역 reader (한 번만 로드) ─────────────────────────────────
_reader: Optional[easyocr.Reader] = None

def _get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["ko", "en"], gpu=False)
    return _reader


# ── 날짜 패턴 ─────────────────────────────────────────────────
# 구분자 있음: 월·일은 앞자리 0 없이도 허용 (3·12월 등). 숫자만 붙은 8자리는 애매하므로 0패딩만 허용.
_M = r"(1[0-2]|0[1-9]|[1-9])"
_D = r"(3[01]|[12]\d|0[1-9]|[1-9])"
DATE_PATTERNS = [
    re.compile(rf"(20\d{{2}})\s*년\s*{_M}\s*월\s*{_D}\s*일"),
    re.compile(rf"(20\d{{2}})년({_M})월({_D})일"),
    re.compile(rf"(20\d{{2}})[.\-/]\s*{_M}[.\-/]\s*{_D}"),
    re.compile(rf"(20\d{{2}})\s+{_M}\s+{_D}"),
    re.compile(rf"(\d{{2}})[.\-/]\s*{_M}[.\-/]\s*{_D}"),
    re.compile(r"(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])"),
]

NOISE_PATTERN = re.compile(r"^[\d\s.\-/:]+$")
EXPIRY_KEYWORDS = ["유통기한", "소비기한", "exp", "best before", "use by", "유통", "소비", "까지"]


def imread_unicode(path: str) -> Optional[np.ndarray]:
    """Windows 한글 경로에서도 동작하는 이미지 읽기 (cv2.imread 한계 우회)"""
    image = cv2.imread(path)
    if image is not None:
        return image
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_unicode(path: str, image: np.ndarray) -> bool:
    """Windows 한글 경로에서도 동작하는 이미지 저장"""
    ext = os.path.splitext(path)[1] or ".jpg"
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        return False
    buf.tofile(path)
    return True


def _preprocess(image_path: str) -> Tuple[object, object]:
    image = imread_unicode(image_path)
    if image is None:
        raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.bilateralFilter(gray, 7, 60, 60)
    thresholded = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 2,
    )
    return image, thresholded


def _normalize_date(raw: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = pattern.search(raw)
        if match:
            groups = match.groups()
            y, m, d = groups[0], groups[1], groups[2]
            if len(y) == 2:
                y = "20" + y
            try:
                parsed = datetime(int(y), int(m), int(d))
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _bbox_from_result(result_item, img_w: int, img_h: int) -> Optional[dict]:
    try:
        box = result_item[0]
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        x = min(xs) / img_w
        y = min(ys) / img_h
        w = (max(xs) - min(xs)) / img_w
        h = (max(ys) - min(ys)) / img_h
        return {"x": x, "y": y, "w": w, "h": h}
    except Exception:
        return None


def recognize_product_name(image_path: str) -> Tuple[Optional[str], Optional[dict]]:
    try:
        image, processed = _preprocess(image_path)
        img_h, img_w = image.shape[:2]
        reader = _get_reader()

        results = reader.readtext(image)
        alt = reader.readtext(processed)
        if not results:
            results = alt
        elif alt:
            seen = {item[1].strip() for item in results}
            results = list(results) + [x for x in alt if x[1].strip() not in seen]

        candidates = []
        for item in results:
            text = item[1].strip()
            conf = item[2]
            if NOISE_PATTERN.match(text):
                continue
            if len(text) < 2:
                continue
            if any(kw in text.lower() for kw in EXPIRY_KEYWORDS):
                continue
            candidates.append((text, conf, item))

        if not candidates:
            return None, None

        candidates.sort(key=lambda x: x[1] * len(x[0]), reverse=True)
        best_text, best_conf, best_item = candidates[0]
        bbox = _bbox_from_result(best_item, img_w, img_h)
        return best_text, bbox

    except Exception as e:
        raise RuntimeError(f"제품명 인식 실패: {e}")


def recognize_expiry_date(image_path: str) -> Tuple[Optional[str], Optional[dict]]:
    try:
        image, processed = _preprocess(image_path)
        img_h, img_w = image.shape[:2]
        reader = _get_reader()

        # 컬러 원본이 이진화보다 날짜 OCR에 유리한 경우가 많음
        results = reader.readtext(image, detail=1)
        alt = reader.readtext(processed, detail=1)

        def _scan(items):
            for item in items:
                text = item[1].strip()
                date_str = _normalize_date(text)
                if date_str:
                    bbox = _bbox_from_result(item, img_w, img_h)
                    return date_str, bbox
            merged = " ".join(item[1] for item in items)
            date_str = _normalize_date(merged)
            if date_str:
                return date_str, None
            return None, None

        found = _scan(results) if results else (None, None)
        if found[0]:
            return found
        found = _scan(alt) if alt else (None, None)
        if found[0]:
            return found
        return None, None

    except Exception as e:
        raise RuntimeError(f"유통기한 인식 실패: {e}")
