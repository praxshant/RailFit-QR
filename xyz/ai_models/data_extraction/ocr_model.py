import pytesseract
import cv2
import numpy as np
import re
from typing import Dict


class OCRExtractor:
    def __init__(self, tesseract_cmd: str = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def extract_text_from_image(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {}
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(processed, config='--psm 6')
        return self.parse_railway_text(text)

    def parse_railway_text(self, text: str) -> Dict:
        patterns = {
            'item_id': r'[A-Z]{2}-\d{4}-\d{6}',
            'vendor_lot': r'VL\d{7}',
            'date': r'\d{4}-\d{2}-\d{2}',
            'serial_number': r'SN\d{8}'
        }
        extracted = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, text)
            if m:
                extracted[key] = m.group()
        return extracted
