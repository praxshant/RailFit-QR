from PIL import Image
import io

class ImageProcessing:
    @staticmethod
    def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
        return Image.open(io.BytesIO(image_bytes))

    @staticmethod
    def convert_to_png(image: Image.Image) -> bytes:
        buf = io.BytesIO()
        image.save(buf, format='PNG')
        return buf.getvalue()
