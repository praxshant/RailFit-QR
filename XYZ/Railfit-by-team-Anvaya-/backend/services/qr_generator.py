# backend/services/qr_generator.py
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import hashlib
from datetime import datetime
import uuid
from PIL import Image, ImageDraw, ImageFont

class RailwayQRGenerator:
    def __init__(self):
        self.lookup_table = {}

    def generate_railway_qr(self, item_data, style: str = 'default'):
        """Generate QR code for railway items with enhanced styling"""
        qr_ref = self._create_qr_reference(item_data)

        # Store in in-memory lookup (optional; DB is source of truth)
        self.lookup_table[qr_ref] = {
            'item_id': item_data.get('item_id'),
            'vendor_lot': item_data.get('vendor_lot'),
            'supply_date': item_data.get('supply_date'),
            'warranty_period': item_data.get('warranty_period'),
            'inspection_dates': item_data.get('inspection_dates', []),
            'item_type': item_data.get('item_type'),
            'manufacturer': item_data.get('manufacturer', ''),
            'created_at': datetime.now().isoformat()
        }

        qr_data = f"INDIAN_RAILWAYS:{qr_ref}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        if style == 'manufacturer':
            img = self._create_manufacturer_qr(qr)
        elif style == 'vendor':
            img = self._create_vendor_qr(qr)
        elif style == 'official':
            img = self._create_official_qr(qr)
        else:
            img = qr.make_image(fill_color="black", back_color="white")

        return img, qr_ref

    def _create_manufacturer_qr(self, qr):
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(0, 51, 102))
        )
        return self._add_railway_header_footer(img, "MANUFACTURER")

    def _create_vendor_qr(self, qr):
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=SquareModuleDrawer(),
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(0, 102, 51))
        )
        return self._add_railway_header_footer(img, "VENDOR")

    def _create_official_qr(self, qr):
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=SolidFillColorMask(back_color=(255, 255, 255), front_color=(255, 103, 31))
        )
        return self._add_railway_header_footer(img, "RAILWAY")

    def _add_railway_header_footer(self, qr_img, role: str):
        width, height = qr_img.size
        new_height = height + 80
        new_img = Image.new('RGB', (width, new_height), 'white')
        new_img.paste(qr_img, (0, 40))

        draw = ImageDraw.Draw(new_img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font = ImageFont.load_default()

        header_text = f"INDIAN RAILWAYS - {role}"
        bbox = draw.textbbox((0, 0), header_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (width - text_width) // 2
        draw.text((text_x, 10), header_text, fill='black', font=font)

        footer = "भारतीय रेल"
        bbox_f = draw.textbbox((0, 0), footer, font=font)
        footer_width = bbox_f[2] - bbox_f[0]
        footer_x = (width - footer_width) // 2
        draw.text((footer_x, height + 50), footer, fill='black', font=font)

        return new_img

    def _create_qr_reference(self, item_data):
        unique_string = f"{item_data.get('item_id')}{datetime.now().isoformat()}{uuid.uuid4()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
