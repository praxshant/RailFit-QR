from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import JSON
from datetime import datetime
import json

Base = declarative_base()

class RailwayItem(Base):
    __tablename__ = 'railway_items'

    id = Column(Integer, primary_key=True)
    item_id = Column(String(50), unique=True, nullable=False, index=True)
    qr_ref = Column(String(12), unique=True, nullable=False, index=True)
    vendor_lot = Column(String(50), nullable=False)
    supply_date = Column(DateTime, nullable=False)
    warranty_period = Column(String(20))
    item_type = Column(String(30), nullable=False)
    manufacturer = Column(String(100))
    inspection_dates = Column(JSON)
    ai_insights = Column(JSON)
    quality_score = Column(Float)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'item_id': self.item_id,
            'qr_ref': self.qr_ref,
            'vendor_lot': self.vendor_lot,
            'supply_date': self.supply_date.isoformat() if self.supply_date else None,
            'warranty_period': self.warranty_period,
            'item_type': self.item_type,
            'manufacturer': self.manufacturer,
            'inspection_dates': self.inspection_dates or [],
            'ai_insights': self.ai_insights or {},
            'quality_score': self.quality_score,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
