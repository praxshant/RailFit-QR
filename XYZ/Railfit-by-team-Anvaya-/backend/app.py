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
from utils.database import init_db, get_db_session
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

# Add seed data if database is empty
def add_seed_data():
    try:
        from utils.database import get_db_session
        from models.railway_item import RailwayItem
        from datetime import datetime
        
        session = get_db_session()
        # Check if database is empty
        item_count = session.query(RailwayItem).count()
        if item_count == 0:
            print("Adding seed data to database...")
            # Add sample data
            sample_items = [
                {
                    'item_id': 'EC-2025-001234',
                    'qr_ref': 'demoabcd1234',
                    'vendor_lot': 'VL2025001',
                    'supply_date': datetime(2025, 1, 15),
                    'warranty_period': '5 years',
                    'item_type': 'elastic_rail_clip',
                    'manufacturer': 'Railway Parts Manufacturer',
                    'inspection_dates': ['2025-01-16', '2025-02-15'],
                    'ai_insights': {'quality': 'excellent', 'maintenance_required': False},
                    'quality_score': 85.0,
                    'status': 'active'
                },
                {
                    'item_id': 'RP-2025-002345',
                    'qr_ref': 'demorfgh5678',
                    'vendor_lot': 'VL2025002',
                    'supply_date': datetime(2025, 1, 20),
                    'warranty_period': '3 years',
                    'item_type': 'rail_pad',
                    'manufacturer': 'Track Components Ltd',
                    'inspection_dates': ['2025-01-21'],
                    'ai_insights': {'quality': 'good', 'maintenance_required': False},
                    'quality_score': 78.0,
                    'status': 'active'
                },
                {
                    'item_id': 'LN-2025-003456',
                    'qr_ref': 'demijkli9012',
                    'vendor_lot': 'VL2025003',
                    'supply_date': datetime(2025, 1, 25),
                    'warranty_period': '4 years',
                    'item_type': 'liner',
                    'manufacturer': 'Railway Solutions Inc',
                    'inspection_dates': [],
                    'ai_insights': {'quality': 'excellent', 'maintenance_required': False},
                    'quality_score': 92.0,
                    'status': 'active'
                }
            ]
            
            for item_data in sample_items:
                item = RailwayItem(**item_data)
                session.add(item)
            
            session.commit()
            print(f"Added {len(sample_items)} sample items to database")
        else:
            print(f"Database already contains {item_count} items")
        
        session.close()
    except Exception as e:
        print(f"Error adding seed data: {e}")

# Add seed data
add_seed_data()

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
        print(f"Vendor search request: {search_data}")
        
        # Get all items first to debug
        all_items = db_service.list_items()
        print(f"Total items in database: {len(all_items)}")
        
        items = db_service.search_items({
            'item_type': search_data.get('part_type'),
            'vendor_lot': search_data.get('supplier'),
            'date_range': (search_data.get('date_from'), search_data.get('date_to'))
        })
        print(f"Search results: {len(items)} items found")
        
        udm_links = [{'item_id': i.item_id, 'link': f"https://ireps.gov.in/udm/item/{i.item_id}", 'status': 'Active'} for i in items]
        tms_links = [{'item_id': i.item_id, 'link': f"https://www.irecept.gov.in/tms/item/{i.item_id}", 'status': 'Tracked'} for i in items]
        return jsonify({'success': True, 'total_items': len(items), 'items': [i.to_dict() for i in items], 'udm_links': udm_links, 'tms_links': tms_links})
    except Exception as e:
        print(f"Vendor search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/vendor/parts-summary', methods=['POST'])
@role_required('vendor')
def vendor_parts_summary():
    try:
        data = request.get_json() or {}
        print(f"Parts summary request: {data}")
        part_type = data.get('part_type')
        try:
            quantity = int(data.get('quantity', 0))
        except Exception:
            quantity = 0

        print(f"Parsed: part_type={part_type}, quantity={quantity}")
        
        if not part_type or quantity <= 0:
            print(f"Validation failed: part_type={part_type}, quantity={quantity}")
            return jsonify({'success': False, 'message': 'Please provide valid part type and quantity'}), 400

        session = get_db_session()
        try:
            try:
                from backend.models.railway_item import RailwayItem
            except Exception:
                from models.railway_item import RailwayItem

            existing_parts = (
                session.query(RailwayItem)
                .filter(RailwayItem.item_type == part_type, RailwayItem.status == 'active')
                .limit(quantity)
                .all()
            )
            print(f"Found {len(existing_parts)} parts of type {part_type}")

            if not existing_parts:
                return jsonify({
                    'success': False,
                    'message': f'No {part_type.replace("_", " ").title()} parts found in database',
                    'part_type': part_type,
                    'requested_quantity': quantity,
                    'found_quantity': 0
                })

            found_quantity = len(existing_parts)
            if found_quantity < quantity:
                return jsonify({
                    'success': False,
                    'message': f'Only {found_quantity} {part_type.replace("_", " ").title()} parts available (requested: {quantity})',
                    'part_type': part_type,
                    'requested_quantity': quantity,
                    'found_quantity': found_quantity,
                    'available_parts': [
                        {
                            'item_id': part.item_id,
                            'vendor_lot': part.vendor_lot,
                            'supply_date': part.supply_date.isoformat() if part.supply_date else None
                        } for part in existing_parts
                    ]
                })

            parts_data = []
            for part in existing_parts:
                parts_data.append({
                    'item_id': part.item_id,
                    'item_type': part.item_type,
                    'vendor_lot': part.vendor_lot,
                    'supply_date': part.supply_date.isoformat() if part.supply_date else None,
                    'manufacturer': part.manufacturer,
                    'quality_score': part.quality_score
                })

            udm_sync_result = integrator.sync_to_udm(parts_data)
            tms_sync_result = integrator.sync_to_tms(parts_data)

            return jsonify({
                'success': True,
                'message': f'Summary generated for {found_quantity} {part_type.replace("_", " ").title()} parts',
                'summary': {
                    'part_type': part_type,
                    'total_parts': found_quantity,
                    'generated_at': datetime.now().isoformat(),
                    'database_sync': True,
                    'udm_sync': bool(udm_sync_result.get('success')),
                    'tms_sync': bool(tms_sync_result.get('success'))
                },
                'parts_data': parts_data,
                'udm_sync_result': udm_sync_result,
                'tms_sync_result': tms_sync_result
            })
        finally:
            try:
                session.close()
            except Exception:
                pass
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating parts summary: {str(e)}'}), 500

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
        print(f"Looking up QR ref: {qr_ref}")
        
        # Debug: List all items
        all_items = db_service.list_items()
        print(f"Total items in database: {len(all_items)}")
        for item in all_items:
            print(f"Item: {item.item_id}, QR: {item.qr_ref}")
        
        item = db_service.get_item_by_qr_ref(qr_ref)
        if not item:
            print(f"QR ref {qr_ref} not found in database")
            return jsonify({'success': False, 'error': 'Not found'}), 404
        
        print(f"Found item: {item.item_id}")
        return jsonify(item.to_dict())
    except Exception as e:
        print(f"Lookup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
