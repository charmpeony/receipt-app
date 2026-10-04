"""Local receipt crop, perspective correction and OCR preparation."""
import cv2
import numpy as np
from PIL import Image


def crop_receipt(image):
    """Detect a bright paper quadrilateral; keep original on uncertain detection."""
    rgb = np.array(image.convert('RGB'))
    h, w = rgb.shape[:2]
    scale = min(1.0, 1400 / max(h, w))
    small = cv2.resize(rgb, None, fx=scale, fy=scale)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    edges = cv2.Canny(blur, 40, 120)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    candidates = []
    total = small.shape[0] * small.shape[1]
    for source in (mask, edges):
        contours, _ = cv2.findContours(source, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if not 0.10 * total < area < 0.97 * total:
                continue
            approx = cv2.approxPolyDP(contour, 0.025 * cv2.arcLength(contour, True), True)
            if len(approx) != 4 or not cv2.isContourConvex(approx):
                continue
            x, y, cw, ch = cv2.boundingRect(approx)
            if min(cw, ch) < 80:
                continue
            inside = np.zeros_like(gray)
            cv2.drawContours(inside, [approx], -1, 255, -1)
            if cv2.mean(gray, mask=inside)[0] < 135:
                continue
            candidates.append((area, approx.reshape(4, 2).astype(np.float32) / scale))
    if not candidates:
        return image.copy(), False
    pts = max(candidates, key=lambda item: item[0])[1]
    # Sort cyclically, then start with top-left. Works for skewed quadrilaterals.
    center = pts.mean(axis=0)
    pts = pts[np.argsort(np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0]))]
    pts = np.roll(pts, -np.argmin(pts.sum(axis=1)), axis=0)
    tl, tr, br, bl = pts
    width = int(max(np.linalg.norm(tr-tl), np.linalg.norm(br-bl)))
    height = int(max(np.linalg.norm(bl-tl), np.linalg.norm(br-tr)))
    if min(width, height) < 50:
        return image.copy(), False
    target = np.float32([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    transform = cv2.getPerspectiveTransform(pts, target)
    warped = cv2.warpPerspective(rgb, transform, (width, height), borderValue=(255, 255, 255))
    return Image.fromarray(warped), True


def prepare_receipt(image):
    gray = cv2.cvtColor(np.array(image.convert('RGB')), cv2.COLOR_RGB2GRAY)
    # Bound RAM and enlarge small print; never grow a long receipt without limit.
    h, w = gray.shape
    scale = min(3.0, max(1.0, 1600 / w), 4500 / max(h, w), (10_000_000 / (h*w))**0.5)
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    # Divide out uneven illumination before contrast adjustment.
    background = cv2.GaussianBlur(gray, (0, 0), 21)
    corrected = cv2.divide(gray, np.maximum(background, 1), scale=255)
    corrected = cv2.normalize(corrected, None, 0, 255, cv2.NORM_MINMAX)
    binary = cv2.adaptiveThreshold(corrected, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 41, 15)
    def padded(arr):
        return Image.fromarray(cv2.copyMakeBorder(arr, 24, 24, 24, 24,
                                                  cv2.BORDER_CONSTANT, value=255))
    return padded(corrected), padded(binary)


def recognize(image, pytesseract):
    """Compare grayscale and binary results using Tesseract word confidence."""
    gray, binary = prepare_receipt(image)
    results = []
    for variant in (gray, binary):
        data = pytesseract.image_to_data(variant, lang='jpn+eng',
            config='--psm 6', timeout=40, output_type=pytesseract.Output.DICT)
        lines = {}
        scores = []
        for i, word in enumerate(data['text']):
            word = word.strip()
            if not word:
                continue
            key = (data['page_num'][i], data['block_num'][i], data['par_num'][i], data['line_num'][i])
            lines.setdefault(key, []).append(word)
            confidence = float(data['conf'][i])
            if confidence >= 0:
                scores.append(confidence)
        text = '\n'.join(' '.join(words) for words in lines.values())
        score = sum(scores) / len(scores) if scores else -1
        results.append((score, text, variant))
    _, text, selected = max(results, key=lambda result: result[0])
    return text, selected
