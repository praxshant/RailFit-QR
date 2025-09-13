import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

try:
    from backend.models.railway_item import Base, RailwayItem
except Exception:
    from models.railway_item import Base, RailwayItem

class DatabaseService:
    def __init__(self):
        db_url = os.getenv('DATABASE_URL', 'sqlite:///railway_qr.db')
        self.engine = create_engine(db_url, future=True)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.session = Session()
    
    def _parse_date(self, s: str):
        if not s:
            return None
        # Try ISO first
        try:
            return datetime.fromisoformat(s)
        except Exception:
            pass
        # Try DD-MM-YYYY
        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
        # As a last resort, return None (caller should handle)
        return None

    def save_item(self, item_data, qr_ref):
        item = RailwayItem(
            item_id=item_data['item_id'],
            qr_ref=qr_ref,
            vendor_lot=item_data['vendor_lot'],
            supply_date=self._parse_date(item_data.get('supply_date')) or datetime.utcnow(),
            warranty_period=item_data.get('warranty_period'),
            item_type=item_data['item_type'],
            manufacturer=item_data.get('manufacturer'),
            inspection_dates=item_data.get('inspection_dates', [])
        )
        self.session.add(item)
        self.session.commit()
        return item
    
    def get_item_by_qr_ref(self, qr_ref):
        return self.session.query(RailwayItem).filter_by(qr_ref=qr_ref).first()
    
    def update_item_insights(self, qr_ref, ai_insights, quality_score=None):
        item = self.get_item_by_qr_ref(qr_ref)
        if not item:
            return None
        item.ai_insights = ai_insights
        if quality_score is not None:
            item.quality_score = quality_score
        item.updated_at = datetime.utcnow()
        self.session.commit()
        return item
    
    def list_items(self):
        return self.session.query(RailwayItem).all()

    def search_items(self, filters: dict):
        q = self.session.query(RailwayItem)
        if filters.get('item_type'):
            q = q.filter(RailwayItem.item_type == filters['item_type'])
        if filters.get('vendor_lot'):
            q = q.filter(RailwayItem.vendor_lot == filters['vendor_lot'])
        date_range = filters.get('date_range')
        if date_range and all(date_range):
            try:
                df = datetime.fromisoformat(date_range[0])
                dt = datetime.fromisoformat(date_range[1])
                q = q.filter(RailwayItem.supply_date.between(df, dt))
            except Exception:
                pass
        return q.all()
