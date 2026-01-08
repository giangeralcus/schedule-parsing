"""
Image preprocessing for OCR
"""
import os

# Optional dependencies
HAS_CV2 = False
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    pass

try:
    from PIL import Image, ImageEnhance
except ImportError:
    Image = None


class ImageProcessor:
    """Image preprocessing for better OCR results"""

    def __init__(self, min_width: int = 2500):
        self.min_width = min_width
        self.has_cv2 = HAS_CV2

    def preprocess(self, image_path: str):
        """
        Preprocess image for OCR

        Returns:
            PIL Image ready for OCR
        """
        if not os.path.exists(image_path):
            return None

        if self.has_cv2:
            return self._preprocess_cv2(image_path)
        else:
            return self._preprocess_pil(image_path)

    def _preprocess_cv2(self, image_path: str):
        """Advanced preprocessing with OpenCV - optimized for shipping schedules"""
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Get dimensions
        h, w = gray.shape

        # Upscale if too small (300 DPI equivalent)
        if w < self.min_width:
            scale = self.min_width / w
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                            interpolation=cv2.INTER_CUBIC)
            h, w = gray.shape

        # Deskew image if rotated
        gray = self._deskew(gray)

        # Apply CLAHE for better contrast (handles varying lighting)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise while preserving edges
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

        # Adaptive threshold (handles uneven illumination)
        binary = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Remove horizontal/vertical lines (table borders)
        binary = self._remove_lines(binary)

        # Morphological cleaning - close gaps in text
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Remove small noise
        kernel_noise = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel_noise)

        # Convert to PIL Image
        return Image.fromarray(cleaned)

    def _deskew(self, img):
        """Deskew image using Hough transform to detect rotation angle"""
        try:
            # Detect edges
            edges = cv2.Canny(img, 50, 150, apertureSize=3)

            # Detect lines using Hough transform
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100,
                                    minLineLength=100, maxLineGap=10)

            if lines is None or len(lines) < 5:
                return img

            # Calculate angles from detected lines
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    # Only consider near-horizontal lines (within 15 degrees)
                    if abs(angle) < 15:
                        angles.append(angle)

            if not angles:
                return img

            # Use median angle for robustness
            median_angle = np.median(angles)

            # Only deskew if angle is significant (> 0.5 degrees)
            if abs(median_angle) < 0.5:
                return img

            # Rotate image to correct skew
            h, w = img.shape
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(img, M, (w, h),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception:
            return img

    def _remove_lines(self, binary_img):
        """Remove horizontal and vertical lines (table borders) from image"""
        try:
            result = binary_img.copy()
            h, w = binary_img.shape

            # Invert image for line detection (lines become white on black)
            inverted = cv2.bitwise_not(binary_img)

            # Calculate kernel sizes with minimum guard (prevent division by zero)
            h_kernel_width = max(w // 30, 10)  # Minimum 10 pixels
            v_kernel_height = max(h // 30, 10)  # Minimum 10 pixels

            # Detect and remove horizontal lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_width, 1))
            horizontal_lines = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            # Fill detected line areas with white (remove black lines)
            result = cv2.bitwise_or(result, horizontal_lines)

            # Detect and remove vertical lines
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_height))
            vertical_lines = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            result = cv2.bitwise_or(result, vertical_lines)

            return result
        except Exception:
            return binary_img

    def _preprocess_pil(self, image_path: str):
        """Basic preprocessing with PIL only"""
        if Image is None:
            return None

        img = Image.open(image_path)

        # Convert to grayscale
        if img.mode != 'L':
            img = img.convert('L')

        # Resize if too small
        w, h = img.size
        if w < self.min_width:
            scale = self.min_width / w
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)

        return img

    def get_image_info(self, image_path: str) -> dict:
        """Get image information"""
        if Image is None:
            return {}

        try:
            img = Image.open(image_path)
            return {
                'width': img.size[0],
                'height': img.size[1],
                'mode': img.mode,
                'format': img.format,
            }
        except Exception:
            return {}
