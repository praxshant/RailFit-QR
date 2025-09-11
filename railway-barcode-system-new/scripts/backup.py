import shutil, os, datetime

def backup_database(db_path='railway_barcode.db', backup_dir='backups'):
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(backup_dir, f'{os.path.basename(db_path)}.{ts}.bak')
    if os.path.exists(db_path):
        shutil.copy2(db_path, dst)
        print('Backup created:', dst)
    else:
        print('Database not found:', db_path)

if __name__ == '__main__':
    backup_database()
