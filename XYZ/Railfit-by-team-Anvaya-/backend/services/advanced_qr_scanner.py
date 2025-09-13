# backend/services/advanced_qr_scanner.py
import cv2
import numpy as np
from typing import List, Dict
try:
    from pyzbar import pyzbar  # Optional: requires zbar DLL on Windows
    _HAS_PYZBAR = True
except Exception:
    pyzbar = None
    _HAS_PYZBAR = False

class StateOfTheArtQRScanner:
    """Advanced QR scanner optimized for railway track fittings"""
    def __init__(self, model_path: str = None):
        self.preprocessor = MetalSurfacePreprocessor()
        self.min_confidence = 0.8

    def scan_qr(self, image_path: str) -> Dict:
        """Main QR scanning method returning best result dict or {'success': False}"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Cannot load image: {image_path}")

            results: List[Dict] = []

            # Method 1: Direct scan
            results.extend(self._direct_qr_scan(image))

            # Method 2: Enhanced preprocessing fallback
            if not results or max(r.get('confidence', 0) for r in results) < 0.9:
                results.extend(self._enhanced_qr_scan(image))

            # Method 3: Recovery
            if not results:
                results.extend(self._damaged_qr_recovery(image))

            if not results:
                return {'success': False}

            best = max(results, key=lambda r: r.get('confidence', 0))
            best['success'] = True
            return best
        except Exception as e:
            return {'error': str(e), 'success': False}

    def _direct_qr_scan(self, image: np.ndarray) -> List[Dict]:
        results: List[Dict] = []
        try:
            # First try OpenCV's native detector (no external DLL needed)
            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(image)
            if data:
                conf = 0.9
                bbox = None
                if points is not None:
                    pts = points.squeeze().astype(int)
                    xs, ys = pts[:, 0], pts[:, 1]
                    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                results.append({
                    'method': 'opencv_qr_detector',
                    'data': data,
                    'confidence': conf,
                    'bbox': bbox,
                    'quality_score': conf,
                })

            # Also attempt pyzbar if available (may improve robustness)
            if _HAS_PYZBAR:
                variants = [
                    ('bgr', image),
                    ('gray', cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)),
                    ('value', cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 2]),
                ]
                for name, img in variants:
                    for code in pyzbar.decode(img):
                        if code.type == 'QRCODE':
                            conf = self._calculate_qr_confidence(code, img)
                            results.append({
                                'method': f'direct_{name}',
                                'data': code.data.decode('utf-8'),
                                'confidence': conf,
                                'bbox': [code.rect.left, code.rect.top,
                                         code.rect.left + code.rect.width,
                                         code.rect.top + code.rect.height],
                                'quality_score': conf,
                            })
        except Exception:
            pass
        return results

    def _enhanced_qr_scan(self, image: np.ndarray) -> List[Dict]:
        results: List[Dict] = []
        variants = self.preprocessor.generate_qr_variants(image)
        for name, img in variants.items():
            # Try OpenCV on each enhanced image
            detector = cv2.QRCodeDetector()
            data, points, _ = detector.detectAndDecode(img)
            if data:
                conf = 0.9
                bbox = None
                if points is not None:
                    pts = points.squeeze().astype(int)
                    xs, ys = pts[:, 0], pts[:, 1]
                    bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                results.append({
                    'method': f'enhanced_opencv_{name}',
                    'data': data,
                    'confidence': conf,
                    'bbox': bbox,
                    'quality_score': conf * 0.95,
                })

            # Then pyzbar on enhanced images if available
            if _HAS_PYZBAR:
                try:
                    for code in pyzbar.decode(img):
                        if code.type == 'QRCODE':
                            conf = self._calculate_qr_confidence(code, img)
                            if conf >= self.min_confidence:
                                results.append({
                                    'method': f'enhanced_{name}',
                                    'data': code.data.decode('utf-8'),
                                    'confidence': conf,
                                    'bbox': [code.rect.left, code.rect.top,
                                             code.rect.left + code.rect.width,
                                             code.rect.top + code.rect.height],
                                    'quality_score': conf * 0.95,
                                })
                except Exception:
                    continue
        return results

    def _damaged_qr_recovery(self, image: np.ndarray) -> List[Dict]:
        results: List[Dict] = []
        try:
            enhanced = self.preprocessor.damage_recovery_qr(image)
            for attempt in range(3):
                params = self.preprocessor.get_recovery_params(attempt)
                processed = self.preprocessor.apply_recovery_params(enhanced, params)
                # Try OpenCV recovery first
                detector = cv2.QRCodeDetector()
                data, points, _ = detector.detectAndDecode(processed)
                if data:
                    conf = 0.75
                    results.append({
                        'method': f'recovery_opencv_{attempt}',
                        'data': data,
                        'confidence': conf,
                        'quality_score': conf,
                    })
                    return results

                # Then pyzbar if available
                if _HAS_PYZBAR:
                    for code in pyzbar.decode(processed):
                        if code.type == 'QRCODE':
                            conf = self._calculate_qr_confidence(code, processed) * 0.8
                            if conf >= 0.6:
                                results.append({
                                    'method': f'recovery_{attempt}',
                                    'data': code.data.decode('utf-8'),
                                    'confidence': conf,
                                    'quality_score': conf,
                                })
                                return results
        except Exception:
            pass
        return results

    def _calculate_qr_confidence(self, qr_code, image) -> float:
        # Area based heuristic
        area = qr_code.rect.width * qr_code.rect.height
        h, w = (image.shape[:2] if len(image.shape) >= 2 else (1, 1))
        image_area = float(h * w) if (h and w) else 1.0
        area_ratio = min(max(area / image_area, 0.0), 1.0)

        # Data quality
        try:
            data = qr_code.data.decode('utf-8')
            if 'INDIAN_RAILWAYS:' in data:
                data_quality = 1.0
            elif len(data) > 10:
                data_quality = 0.9
            else:
                data_quality = 0.7
        except Exception:
            data_quality = 0.5

        confidence = (area_ratio * 0.4) + (data_quality * 0.6)
        return min(max(confidence, 0.0), 1.0)


class MetalSurfacePreprocessor:
    """QR-specific preprocessing for metal surfaces"""
    def generate_qr_variants(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        variants: Dict[str, np.ndarray] = {}
        variants['original'] = image
        variants['high_contrast'] = self._enhance_qr_contrast(image)
        variants['denoised'] = self._denoise_qr(image)
        variants['sharpened'] = self._sharpen_qr(image)
        variants['threshold'] = self._adaptive_threshold_qr(image)
        return variants

    def _enhance_qr_contrast(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def _denoise_qr(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return cv2.bilateralFilter(gray, 9, 75, 75)

    def _sharpen_qr(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        kernel = np.array([[-1,-1,-1],[-1, 9,-1],[-1,-1,-1]])
        return cv2.filter2D(gray, -1, kernel)

    def _adaptive_threshold_qr(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    def damage_recovery_qr(self, image):
        # Aggressive preprocessing chain
        img = self._enhance_qr_contrast(image)
        img = self._denoise_qr(img)
        img = self._sharpen_qr(img)
        return img

    def get_recovery_params(self, attempt: int):
        return {'blur': (attempt + 1) * 3, 'thresh_block': 11 + attempt * 2}

    def apply_recovery_params(self, image, params):
        blur_k = params.get('blur', 3)
        img = cv2.GaussianBlur(image, (blur_k, blur_k), 0)
        return self._adaptive_threshold_qr(img)
