-- QR-based schema (optional; SQLAlchemy creates tables programmatically)
CREATE TABLE IF NOT EXISTS railway_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT UNIQUE NOT NULL,
  qr_ref TEXT UNIQUE NOT NULL,
  vendor_lot TEXT NOT NULL,
  supply_date TEXT NOT NULL,
  warranty_period TEXT,
  item_type TEXT NOT NULL,
  manufacturer TEXT,
  inspection_dates TEXT,
  ai_insights TEXT,
  quality_score REAL,
  status TEXT DEFAULT 'active',
  created_at TEXT,
  updated_at TEXT
);
