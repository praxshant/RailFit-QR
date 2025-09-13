import requests, os

UDM_URL = os.getenv('UDM_PORTAL_URL', '')
TMS_URL = os.getenv('TMS_PORTAL_URL', '')

def sync_udm(payload):
    print('Simulated sync to UDM with payload:', payload)

def sync_tms(payload):
    print('Simulated sync to TMS with payload:', payload)

if __name__ == '__main__':
    sample = { 'item_id': 'EC-2025-001234' }
    sync_udm(sample)
    sync_tms(sample)
