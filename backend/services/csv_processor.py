"""CSV parsing, validation, and normalization."""

import uuid
import re
from datetime import datetime
from io import StringIO
from typing import Optional
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session as DBSession

from models import Session, Transaction


class CSVProcessor:
    """Parse, validate, and normalize transaction CSVs."""

    REQUIRED_COLUMNS = ["date", "description", "amount"]
    DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]

    def __init__(self, db: DBSession):
        self.db = db

    async def process(self, file: UploadFile) -> tuple[str, int]:
        """Process uploaded CSV and create session with transactions."""
        # Read file content
        content = await file.read()
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

        df = pd.read_csv(StringIO(text))

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        # Validate required columns
        self._validate_columns(df)

        # Normalize data
        df = self._normalize_dates(df)
        df = self._normalize_amounts(df)
        df = self._clean_descriptions(df)

        # Create session
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            filename=file.filename,
            row_count=len(df),
            status="processing",
        )
        self.db.add(session)

        # Create transactions
        for _, row in df.iterrows():
            transaction = Transaction(
                session_id=session_id,
                date=row["date"],
                description=row["description"],
                amount=row["amount"],
                raw_description=row.get("raw_description", row["description"]),
            )
            self.db.add(transaction)

        self.db.commit()
        return session_id, len(df)

    def process_synthetic(self, transactions: list[dict]) -> tuple[str, int]:
        """Process synthetic transaction data."""
        session_id = str(uuid.uuid4())
        session = Session(
            id=session_id,
            filename="sample_transactions.csv",
            row_count=len(transactions),
            status="processing",
        )
        self.db.add(session)

        for txn in transactions:
            transaction = Transaction(
                session_id=session_id,
                date=txn["date"],
                description=txn["description"],
                amount=txn["amount"],
                raw_description=txn["description"],
            )
            self.db.add(transaction)

        self.db.commit()
        return session_id, len(transactions)

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist."""
        missing = []
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                # Check for common alternatives
                alternatives = {
                    "date": ["transaction_date", "trans_date", "txn_date"],
                    "description": ["merchant", "name", "memo", "payee"],
                    "amount": ["value", "sum", "total"],
                }
                found = False
                for alt in alternatives.get(col, []):
                    if alt in df.columns:
                        df.rename(columns={alt: col}, inplace=True)
                        found = True
                        break
                if not found:
                    missing.append(col)

        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    def _normalize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert dates to consistent format."""

        def parse_date(val):
            if pd.isna(val):
                return None
            if isinstance(val, datetime):
                return val.date()
            val_str = str(val).strip()
            for fmt in self.DATE_FORMATS:
                try:
                    return datetime.strptime(val_str, fmt).date()
                except ValueError:
                    continue
            # Try pandas parser as fallback
            try:
                return pd.to_datetime(val_str).date()
            except Exception:
                raise ValueError(f"Cannot parse date: {val_str}")

        df["date"] = df["date"].apply(parse_date)
        df = df.dropna(subset=["date"])
        return df

    def _normalize_amounts(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize amount values."""

        def parse_amount(val):
            if pd.isna(val):
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val).strip()
            # Remove currency symbols and commas
            val_str = re.sub(r"[$,]", "", val_str)
            # Handle parentheses as negative
            if val_str.startswith("(") and val_str.endswith(")"):
                val_str = "-" + val_str[1:-1]
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        df["amount"] = df["amount"].apply(parse_amount)
        return df

    def _clean_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize descriptions."""

        def clean_desc(val):
            if pd.isna(val):
                return "Unknown"
            desc = str(val).strip()
            # Remove extra whitespace
            desc = re.sub(r"\s+", " ", desc)
            # Remove common prefixes
            desc = re.sub(r"^(POS |CHECKCARD |DEBIT |CREDIT )", "", desc, flags=re.I)
            return desc if desc else "Unknown"

        df["raw_description"] = df["description"]
        df["description"] = df["description"].apply(clean_desc)
        return df
