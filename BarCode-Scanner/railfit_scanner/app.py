from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import os
import base64
import io
import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate')
def generate_page():
    return render_template('generate_barcode.html')

@app.route('/decode_barcode', methods=['POST'])
def decode_barcode():
    """Fixed decode endpoint with proper error handling"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        image_data = data['image']

        # Handle base64 image data
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]

        # Decode base64 to image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))

        # Convert PIL to numpy array
        img_array = np.array(image)

        # Decode barcode
        result = decode_custom_barcode(img_array)

        if isinstance(result, str) and result.startswith('Error:'):
            return jsonify({'success': False, 'error': result})
        else:
            return jsonify({'success': True, 'decoded': result})

    except Exception as e:
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'}), 500

@app.route('/generate_barcode', methods=['POST'])
def generate_barcode():
    """Fixed generator endpoint"""
    try:
        data = request.get_json()
        digit_string = (data or {}).get('digits', '')
        
        # Validate input
        if len(digit_string) != 23:
            return jsonify({'success': False, 'error': 'Must be exactly 23 digits'})
        
        if not all(c.isdigit() for c in digit_string):
            return jsonify({'success': False, 'error': 'All characters must be digits 0-9'})
        
        if digit_string[0] != '1' or digit_string[22] != '1' or digit_string[11] != '9':
            return jsonify({'success': False, 'error': 'Reference bars must be: 1st=1, 23rd=1, 12th=9'})
        
        # Generate barcode
        img = generate_barcode_image(digit_string)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True, 
            'image': f'data:image/png;base64,{img_base64}',
            'digits': digit_string
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Generation error: {str(e)}'}), 500

def decode_custom_barcode(image_array):
    """
    Decode 23-bar custom barcode from image array
    Reference bars: 1st=1, 23rd=1, 12th=9
    Height mapping: 0->1unit, 1->2units, ..., 9->10units
    """
    # Convert image to OpenCV format if needed
    if len(image_array.shape) == 3:
        # Handle RGB or RGBA inputs robustly
        if image_array.shape[2] == 4:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGRA2GRAY)
        else:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_array
    
    height, width = gray.shape

    # Step 1: Convert to clean binary matching generator (black bars on white)
    # Use fixed threshold and invert so bars become 255 (foreground) for contour detection
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    
    # Morphological open to remove small noise
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # Step 2: Middle line consistent with generator
    middle_y = height // 2

    # Step 3: Find 23 bar contours
    def find_bar_rects(bin_img):
        h_img, w_img = bin_img.shape
        contours, _ = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rects = []
        min_bar_height = max(8, int(h_img * 0.05))  # be permissive
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if h < min_bar_height:
                continue
            rects.append((x, y, w, h))
        rects.sort(key=lambda b: b[0])
        return rects

    bars = find_bar_rects(binary)

    # Fallback A: crop to content and retry if not 23
    if len(bars) != 23 and len(bars) > 0:
        x0 = min(b[0] for b in bars)
        x1 = max(b[0] + b[2] for b in bars)
        y0 = min(b[1] for b in bars)
        y1 = max(b[1] + b[3] for b in bars)
        pad = 6
        x0 = max(0, x0 - pad)
        x1 = min(width, x1 + pad)
        y0 = max(0, y0 - pad)
        y1 = min(height, y1 + pad)
        cropped = binary[y0:y1, x0:x1]
        bars_crop = find_bar_rects(cropped)
        if len(bars_crop) == 23:
            # Translate back to full image coords
            bars = [(x + x0, y + y0, w, h) for (x, y, w, h) in bars_crop]

    # Fallback B: peak detection with enforced 23 peaks
    if len(bars) != 23:
        col_counts = (binary > 0).astype(np.uint8).sum(axis=0).astype(np.float32)
        smooth = gaussian_filter1d(col_counts, sigma=2)
        # Try generous parameters
        from scipy.signal import find_peaks as _find_peaks
        distance = max(1, width // 40)
        peaks, _ = _find_peaks(smooth, distance=distance)
        xs = list(map(int, peaks.tolist()))
        xs.sort()
        if len(xs) == 0:
            return 'Error: No bars detected'
        # Force exactly 23 positions
        def merge_nearest(arr):
            if len(arr) <= 23:
                return arr
            # merge closest pair
            diffs = [arr[i+1]-arr[i] for i in range(len(arr)-1)]
            k = int(np.argmin(diffs))
            merged = arr[:k] + [int((arr[k]+arr[k+1])//2)] + arr[k+2:]
            return merged
        def split_widest(arr):
            if len(arr) >= 23:
                return arr
            # insert midpoint in widest gap
            diffs = [arr[i+1]-arr[i] for i in range(len(arr)-1)]
            k = int(np.argmax(diffs))
            mid = int((arr[k]+arr[k+1])//2)
            return arr[:k+1] + [mid] + arr[k+1:]
        # Adjust count to 23
        while len(xs) > 23:
            xs = merge_nearest(xs)
        while len(xs) < 23 and len(xs) > 1:
            xs = split_widest(xs)
        if len(xs) != 23:
            return f'Error: Detected {len(bars)} bars instead of 23'
        # Build synthetic bars from columns around each x
        bars = []
        for x in xs:
            x = max(0, min(width-1, x))
            col = binary[:, x]
            ys = np.where(col > 0)[0]
            if len(ys) == 0:
                # expand search +/-1
                found = False
                for dx in (-1, 1, -2, 2):
                    xx = x + dx
                    if 0 <= xx < width:
                        ys2 = np.where(binary[:, xx] > 0)[0]
                        if len(ys2) > 0:
                            ys = ys2
                            found = True
                            break
                if not found:
                    continue
            y_top = int(ys[0])
            y_bot = int(ys[-1])
            # approximate bar width by local run length
            left = x
            while left-1 >= 0 and (binary[middle_y, left-1] > 0):
                left -= 1
            right = x
            while right+1 < width and (binary[middle_y, right+1] > 0):
                right += 1
            bars.append((left, y_top, max(1, right-left+1), y_bot - y_top + 1))

    # Final check
    if len(bars) != 23:
        return f'Error: Detected {len(bars)} bars instead of 23'

    # Step 4: Measure half-heights for each bar from middle line
    pixel_heights = []
    for (x, y, w, h) in bars:
        top = y
        bottom = y + h - 1
        height_up = max(0, middle_y - top)
        height_down = max(0, bottom - middle_y)
        half_height = min(height_up, height_down)
        pixel_heights.append(int(half_height))

    # Step 5: Calibrate using reference bars (1st=1, 12th=9, 23rd=1)
    h1_first = pixel_heights[0]
    h1_last = pixel_heights[22]
    h9_middle = pixel_heights[11]

    h1_avg = (h1_first + h1_last) / 2.0

    # Digit mapping: height = (digit + 1) * step
    step_from_1 = h1_avg / 2.0
    step_from_9 = h9_middle / 10.0
    step = (step_from_1 + step_from_9) / 2.0

    if step <= 0:
        return 'Error: Calibration failed - invalid step'

    # Validate step consistency (30% tolerance)
    if abs(step_from_1 - step_from_9) > step * 0.3:
        return 'Error: Calibration failed - reference bars inconsistent'

    # Step 6: Map each height to digit 0-9
    decoded = []
    for h in pixel_heights:
        digit = int(round(h / step - 1))
        digit = max(0, min(9, digit))
        decoded.append(digit)

    # Step 7: Validate reference bars
    if decoded[0] != 1 or decoded[22] != 1 or decoded[11] != 9:
        return f'Error: Reference bars validation failed. Got {decoded[0]}, {decoded[22]}, {decoded[11]}, expected 1, 1, 9'

    return ''.join(map(str, decoded))

def generate_barcode_image(digit_string, width=800, height=200):
    """
    Generate barcode image matching detection algorithm parameters
    Height mapping: 0->1unit, 1->2units, ..., 9->10units (symmetric around middle)
    Reference bars must be 1 (first and last) and 9 at index 11
    """
    if len(digit_string) != 23:
        raise ValueError("Digit string must be exactly 23 characters")

    if digit_string[0] != '1' or digit_string[22] != '1' or digit_string[11] != '9':
        raise ValueError("Reference bars must be: 1st=1, 23rd=1, 12th=9")

    if not all(c.isdigit() for c in digit_string):
        raise ValueError("All characters must be digits 0-9")

    # Create image
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Bar layout
    margin = 50
    bar_area_width = width - 2 * margin
    bar_spacing = bar_area_width / 23.0
    bar_width = int(bar_spacing * 0.8)  # 80% width for bar, 20% spacing

    # Height parameters
    base_y = height // 2  # Middle line
    max_bar_total_height = height - 40  # leave margins
    unit_height = max(1, max_bar_total_height // 20)  # 10 units above and below = 20 units total

    for i, ch in enumerate(digit_string):
        d = int(ch)
        bar_units = d + 1  # digit 0 -> 1 unit ... digit 9 -> 10 units
        half_height = bar_units * unit_height

        bar_x_center = int(margin + i * bar_spacing + bar_spacing / 2)
        left = max(0, bar_x_center - bar_width // 2)
        right = min(width - 1, bar_x_center + bar_width // 2)
        top = max(10, base_y - half_height)
        bottom = min(height - 10, base_y + half_height)

        draw.rectangle([left, top, right, bottom], fill='black')

    return img

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
