#!/usr/bin/env python
"""Add missing columns to scan_history table"""
from database import engine, Base
from models import ScanHistory

print("🔄 Dropping old scan_history table...")
Base.metadata.drop_all(bind=engine, tables=[ScanHistory.__table__])

print("✅ Recreating scan_history table with new columns...")
Base.metadata.create_all(bind=engine)

print("✅ Database migration complete!")
print("✅ Table now has: image_paths, raw_text_front, raw_text_back")
