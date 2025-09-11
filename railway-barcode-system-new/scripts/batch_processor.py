import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from backend.services.barcode_generator import RailwayBarcodeGenerator

class BatchQRProcessor:
    def __init__(self, max_workers=10):
        self.generator = RailwayBarcodeGenerator()
        self.max_workers = max_workers
    
    def process_csv_file(self, csv_path, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        df = pd.read_csv(csv_path)
        required_cols = ['item_id', 'vendor_lot', 'supply_date', 'item_type']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        batch_size = 1000
        total_batches = len(df) // batch_size + (1 if len(df) % batch_size else 0)
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            self.process_batch(batch_df, output_dir, i)
            print(f"Processed batch {i+1}/{total_batches}")
    
    def process_batch(self, batch_df, output_dir, batch_num):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for _, row in batch_df.iterrows():
                item_data = row.to_dict()
                futures.append(executor.submit(self.process_single_item, item_data, output_dir))
            for f in futures:
                result = f.result()
                if result['success']:
                    print(f"Generated BARCODE for {result['item_id']}")
                else:
                    print(f"Failed for {result['item_id']}: {result['error']}")
    
    def process_single_item(self, item_data, output_dir):
        try:
            barcode_obj, barcode_ref = self.generator.generate_railway_barcode(item_data)
            img = barcode_obj.render()
            filename = os.path.join(output_dir, f"barcode_{item_data['item_id']}_{barcode_ref}.png")
            img.save(filename)
            return {'success': True, 'item_id': item_data['item_id'], 'barcode_ref': barcode_ref, 'filename': filename}
        except Exception as e:
            return {'success': False, 'item_id': item_data.get('item_id', 'unknown'), 'error': str(e)}

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Bulk BARCODE generation for railway items')
    parser.add_argument('--csv', required=True, help='Path to CSV file with items')
    parser.add_argument('--out', required=True, help='Output directory to save barcode images')
    args = parser.parse_args()
    BatchQRProcessor().process_csv_file(args.csv, args.out)
