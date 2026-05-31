"""
Product data model and SQLite database manager
"""

import sqlite3
import json
import os
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class Category(Enum):
    FOOD = "식품"
    COSMETIC = "화장품"
    MEDICINE = "의약품"
    OTHER = "기타"


class ExpiryStatus(Enum):
    SAFE = "safe"        # 초록 - 2/3 이상 남음
    WARNING = "warning"  # 노랑 - 1/3 이상 남음
    DANGER = "danger"    # 빨강 - 1/3 미만 남음
    EXPIRED = "expired"  # 만료됨


STATUS_COLORS = {
    ExpiryStatus.SAFE: "#22C55E",
    ExpiryStatus.WARNING: "#EAB308",
    ExpiryStatus.DANGER: "#EF4444",
    ExpiryStatus.EXPIRED: "#6B7280",
}

STATUS_LABELS = {
    ExpiryStatus.SAFE: "널널",
    ExpiryStatus.WARNING: "애매",
    ExpiryStatus.DANGER: "임박",
    ExpiryStatus.EXPIRED: "만료",
}

CATEGORY_ICONS = {
    Category.FOOD: "🍱",
    Category.COSMETIC: "💄",
    Category.MEDICINE: "💊",
    Category.OTHER: "📦",
}


@dataclass
class Product:
    id: Optional[int]
    name: str
    category: Category
    registered_date: date
    expiry_date: date
    image_path: Optional[str] = None
    notes: str = ""

    @property
    def status(self) -> ExpiryStatus:
        today = date.today()
        if today > self.expiry_date:
            return ExpiryStatus.EXPIRED
        remaining_days = (self.expiry_date - today).days
        if remaining_days <= 7:
            return ExpiryStatus.DANGER
        elif remaining_days <= 30:
            return ExpiryStatus.WARNING
        else:
            return ExpiryStatus.SAFE

    @property
    def days_remaining(self) -> int:
        return (self.expiry_date - date.today()).days

    @property
    def status_color(self) -> str:
        return STATUS_COLORS[self.status]

    @property
    def status_label(self) -> str:
        return STATUS_LABELS[self.status]

    @property
    def category_icon(self) -> str:
        return CATEGORY_ICONS.get(self.category, "📦")


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "products.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    registered_date TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    image_path TEXT,
                    notes TEXT DEFAULT ''
                )
            """)
            conn.commit()

    def _row_to_product(self, row) -> Product:
        return Product(
            id=row[0],
            name=row[1],
            category=Category(row[2]),
            registered_date=date.fromisoformat(row[3]),
            expiry_date=date.fromisoformat(row[4]),
            image_path=row[5],
            notes=row[6] or "",
        )

    def add_product(self, product: Product) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO products (name, category, registered_date, expiry_date, image_path, notes) VALUES (?,?,?,?,?,?)",
                (product.name, product.category.value,
                 product.registered_date.isoformat(), product.expiry_date.isoformat(),
                 product.image_path, product.notes)
            )
            conn.commit()
            return cursor.lastrowid

    def get_all_products(self) -> List[Product]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY expiry_date ASC").fetchall()
        return [self._row_to_product(r) for r in rows]

    def delete_product(self, product_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()

    def update_product(self, product: Product):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE products SET name=?, category=?, registered_date=?, expiry_date=?, image_path=?, notes=? WHERE id=?",
                (product.name, product.category.value,
                 product.registered_date.isoformat(), product.expiry_date.isoformat(),
                 product.image_path, product.notes, product.id)
            )
            conn.commit()
