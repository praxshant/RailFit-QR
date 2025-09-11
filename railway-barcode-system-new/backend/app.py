from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import base64
import io
import os
from dotenv import load_dotenv
from services.qr_generator import RailwayQRGenerator
from services.ai_analyzer import RailwayAIAnalyzer
from services.udm_tms_integration import UDMTMSIntegrator
from services.database_service import DatabaseService
from utils.database import init_db
import json
from werkzeug.utils import secure_filename
from datetime import datetime
from services.advanced_qr_scanner import StateOfTheArtQRScanner
from services.auth_service import AuthService, role_required
from services.railway_parts_data import railway_parts_db

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'railway-secret-key')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['QR_CODE_FOLDER'] = os.getenv('QR_CODE_FOLDER', 'generated_qr_codes')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['QR_CODE_FOLDER'], exist_ok=True)

# Initialize services
auth_service = AuthService(app.config['JWT_SECRET_KEY'])
qr_generator = RailwayQRGenerator()
ai_analyzer = RailwayAIAnalyzer()
integrator = UDMTMSIntegrator()
db_service = DatabaseService()
qr_scanner = StateOfTheArtQRScanner()

# Initialize database
init_db()

ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'bmp', 'tiff' }
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE', str(16 * 1024 * 1024)))

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Friendly index routes so opening http://localhost:5000 doesn't 404
@app.route('/', methods=['GET'])
def root_index():
    frontend_url = os.getenv('FRONTEND_URL', '/web')
    return (
        f"""
        <html>
          <head><title>Indian Railways QR System</title></head>
          <body style='font-family: Arial, sans-serif; padding: 24px;'>
            <h1>Indian Railways – Track Fittings QR System</h1>
            <p>Backend is running.</p>
            <ul>
              <li>Open Frontend: <a href="{frontend_url}">{frontend_url}</a></li>
              <li>Health: <a href="/api/health">/api/health</a></li>
              <li>Items: <a href="/api/items">/api/items</a></li>
            </ul>
          </body>
        </html>
        """,
        200,
        {"Content-Type": "text/html; charset=utf-8"}
    )

@app.route('/api', methods=['GET'])
def api_index():
    return jsonify({
        'service': 'Indian Railways QR System',
        'version': '2.0.0',
        'docs': 'See README.md in repo root',
        'endpoints': [
            'POST /api/login',
            'GET  /api/verify-token',
            'POST /api/manufacturer/generate-qr',
            'POST /api/vendor/search-parts',
            'POST /api/vendor/parts-summary',
            'POST /api/official/scan-qr',
            'GET  /api/items',
            'GET  /api/download/qr/<qr_ref>',
            'GET  /api/health'
        ]
    })

# ----------------- Frontend Static Hosting (optional) -----------------
# Serve the frontend/public directory at /web to avoid needing Node serve
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FRONTEND_PUBLIC = os.path.join(PROJECT_ROOT, 'frontend', 'public')
FRONTEND_SRC = os.path.join(PROJECT_ROOT, 'frontend', 'src')

@app.route('/web/')
def web_index():
    if os.path.exists(os.path.join(FRONTEND_PUBLIC, 'index.html')):
        return send_from_directory(FRONTEND_PUBLIC, 'index.html')
    return jsonify({'error': 'frontend/public/index.html not found'}), 404

@app.route('/web/<path:path>')
def web_static(path):
    if os.path.exists(os.path.join(FRONTEND_PUBLIC, path)):
        return send_from_directory(FRONTEND_PUBLIC, path)
    # fallback to index for client-side routing if needed
    if os.path.exists(os.path.join(FRONTEND_PUBLIC, 'index.html')):
        return send_from_directory(FRONTEND_PUBLIC, 'index.html')
    return jsonify({'error': 'file not found'}), 404

@app.route('/web/src/<path:path>')
def web_src(path):
    if os.path.exists(os.path.join(FRONTEND_SRC, path)):
        return send_from_directory(FRONTEND_SRC, path)
    return jsonify({'error': 'file not found'}), 404

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not all([username, password, role]):
        return jsonify({'success': False, 'message': 'All fields required'}), 400
    result = auth_service.authenticate_user(username, password, role)
    return (jsonify(result), 200) if result.get('success') else (jsonify(result), 401)

@app.route('/api/verify-token', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'success': False, 'message': 'Token missing'}), 401
    token = token.split(' ')[1] if ' ' in token else token
    result = auth_service.verify_token(token)
    return jsonify(result)


@app.route('/api/manufacturer/generate-qr', methods=['POST'])
@role_required('manufacturer')
def manufacturer_generate_qr():
    try:
        item_data = request.get_json() or {}
        item_data['manufacturer'] = getattr(request, 'user', {}).get('name')

        # Attach comprehensive part specifications if available
        part_specs = railway_parts_db.get_part_specifications(item_data.get('item_type', ''))
        if part_specs:
            item_data['specifications'] = {
                'material': part_specs.material,
                'material_grade': part_specs.material_grade,
                'service_life_years': part_specs.service_life_years,
                'load_capacity_kn': part_specs.load_capacity_kn,
                'rdso_specification': part_specs.rdso_specification,
                'testing_requirements': part_specs.testing_requirements,
                'maintenance_interval_months': part_specs.maintenance_interval_months,
            }

        # Generate QR with manufacturer styling
        qr_image, qr_ref = qr_generator.generate_railway_qr(item_data, 'manufacturer')

        # Save to DB
        try:
            db_service.save_item(item_data, qr_ref)
        except Exception as e:
            print(f"DB save error: {e}")

        # Convert to base64
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

        # Save file
        filename = f"railway_qr_mfg_{qr_ref}.png"
        filepath = os.path.join(app.config['QR_CODE_FOLDER'], filename)
        qr_image.save(filepath)

        return jsonify({
            'success': True,
            'qr_ref': qr_ref,
            'qr_image': img_base64,
            'filename': filename,
            'specifications': item_data.get('specifications', {})
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/official/scan-qr', methods=['POST'])
@role_required('railway_official')
def official_scan_qr():
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_name = f"{ts}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            file.save(file_path)
            try:
                best = qr_scanner.scan_qr(file_path)
                if best and best.get('success'):
                    qr_data = best.get('data', '')
                    if 'INDIAN_RAILWAYS:' in qr_data:
                        qr_ref = qr_data.replace('INDIAN_RAILWAYS:', '')
                        item = db_service.get_item_by_qr_ref(qr_ref)
                        if item:
                            item_data = item.to_dict()
                            ai_insights = ai_analyzer.analyze_item_performance(item_data)
                            item_data['ai_insights'] = ai_insights
                            return jsonify({
                                'success': True,
                                'scan_result': best,
                                'item_data': item_data,
                                'scanned_by': getattr(request, 'user', {}).get('name'),
                                'scan_timestamp': datetime.now().isoformat()
                            })
                        else:
                            return jsonify({'success': False, 'error': 'QR not found in database'}), 404
                    else:
                        return jsonify({'success': False, 'error': 'Not an Indian Railways QR code'}), 400
                else:
                    return jsonify({'success': False, 'error': 'No QR detected in image'}), 404
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        return jsonify({'success': False, 'error': 'Invalid file format'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/vendor/search-parts', methods=['POST'])
@role_required('vendor')
def vendor_search_parts():
    try:
        search_data = request.get_json() or {}
        items = db_service.search_items({
            'item_type': search_data.get('part_type'),
            'vendor_lot': search_data.get('supplier'),
            'date_range': (search_data.get('date_from'), search_data.get('date_to'))
        })
        udm_links = [{'item_id': i.item_id, 'link': f"https://ireps.gov.in/udm/item/{i.item_id}", 'status': 'Active'} for i in items]
        tms_links = [{'item_id': i.item_id, 'link': f"https://www.irecept.gov.in/tms/item/{i.item_id}", 'status': 'Tracked'} for i in items]
        return jsonify({'success': True, 'total_items': len(items), 'items': [i.to_dict() for i in items], 'udm_links': udm_links, 'tms_links': tms_links})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vendor/parts-summary', methods=['POST'])
@role_required('vendor')
def vendor_parts_summary():
    try:
        summary_data = request.get_json() or {}
        parts_list = summary_data.get('parts_list', [])
        processed_summary = {
            'vendor_name': getattr(request, 'user', {}).get('name'),
            'parts_list': parts_list,
            'total_parts': len(parts_list),
            'generated_at': datetime.now().isoformat(),
            'database_sync': True,
            'udm_sync': True,
            'tms_sync': True
        }
        # Placeholder integrations
        udm_result = {'success': True}
        tms_result = {'success': True}
        return jsonify({'success': True, 'summary': processed_summary, 'udm_sync_result': udm_result, 'tms_sync_result': tms_result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Indian Railways QR System', 'version': '2.0.0'})

# Backwards compatibility routes (optional)
@app.route('/api/download/qr/<qr_ref>', methods=['GET'])
def download_qr(qr_ref):
    try:
        filename = os.path.join(app.config['QR_CODE_FOLDER'], f'railway_qr_mfg_{qr_ref}.png')
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/udm', methods=['POST'])
@role_required('vendor')
def sync_with_udm():
    try:
        data = request.get_json() or {}
        result = integrator.sync_to_udm(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/tms', methods=['POST'])
@role_required('vendor')
def sync_with_tms():
    try:
        data = request.get_json() or {}
        result = integrator.sync_to_tms(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/items', methods=['GET'])
def get_all_items():
    try:
        items = db_service.list_items()
        return jsonify([i.to_dict() for i in items])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --------- Parts Specification APIs ---------
@app.route('/api/parts/specifications/<part_type>', methods=['GET'])
def get_part_specifications(part_type):
    try:
        specs = railway_parts_db.get_part_specifications(part_type)
        if specs:
            return jsonify({'success': True, 'part_type': part_type, 'specifications': specs.__dict__})
        return jsonify({'success': False, 'error': f'Specifications not found for part type: {part_type}'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parts/search', methods=['POST'])
def search_parts_specifications():
    try:
        criteria = request.get_json() or {}
        results = []
        for ptype, spec in railway_parts_db.get_all_parts().items():
            match = True
            if 'material' in criteria and criteria['material']:
                if criteria['material'].lower() not in spec.material.lower():
                    match = False
            if 'rdso_spec' in criteria and criteria['rdso_spec']:
                if criteria['rdso_spec'] not in spec.rdso_specification:
                    match = False
            if 'min_service_life' in criteria and criteria['min_service_life']:
                if spec.service_life_years < int(criteria['min_service_life']):
                    match = False
            if match:
                results.append({'part_type': ptype, 'specifications': spec.__dict__})
        return jsonify({'success': True, 'total_results': len(results), 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Lookup by QR ref for webcam scanning flow
@app.route('/api/lookup/<qr_ref>', methods=['GET'])
def lookup_qr_ref(qr_ref):
    try:
        item = db_service.get_item_by_qr_ref(qr_ref)
        if not item:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return jsonify(item.to_dict())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
