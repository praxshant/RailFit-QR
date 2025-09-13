import os
import requests

class UDMTMSIntegrator:
    def __init__(self):
        self.udm_base_url = os.getenv('UDM_API_BASE_URL') or os.getenv('UDM_PORTAL_URL', '')
        self.tms_base_url = os.getenv('TMS_API_BASE_URL') or os.getenv('TMS_PORTAL_URL', '')
        self.api_key = os.getenv('IREPS_API_KEY') or os.getenv('UDM_API_KEY')

    def sync_to_udm(self, item_data):
        headers = {
            'Authorization': f"Bearer {self.api_key}" if self.api_key else '',
            'Content-Type': 'application/json'
        }
        if isinstance(item_data, list):
            payload = { 'items': item_data }
        else:
            payload = {
                'item_id': item_data.get('item_id'),
                'vendor_lot_number': item_data.get('vendor_lot'),
                'supply_date': item_data.get('supply_date'),
                'item_type': item_data.get('item_type'),
                'qr_ref': item_data.get('qr_ref') or item_data.get('item_ref')
            }
        try:
            url = f"{self.udm_base_url}/api/track-fittings/register"
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            return {'success': resp.ok, 'status': resp.status_code, 'data': resp.json() if resp.content else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def sync_to_tms(self, item_data):
        headers = {
            'Authorization': f"Bearer {self.api_key}" if self.api_key else '',
            'Content-Type': 'application/json'
        }
        if isinstance(item_data, list):
            payload = { 'items': item_data }
        else:
            payload = {
                'track_fitting_id': item_data.get('item_id'),
                'installation_data': {
                    'vendor_lot': item_data.get('vendor_lot'),
                    'supply_date': item_data.get('supply_date'),
                    'warranty_info': item_data.get('warranty_period'),
                    'qr_reference': item_data.get('qr_ref') or item_data.get('item_ref')
                }
            }
        try:
            url = f"{self.tms_base_url}/api/installations/register"
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            return {'success': resp.ok, 'status': resp.status_code, 'data': resp.json() if resp.content else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}
