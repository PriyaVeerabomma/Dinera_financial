"""Statistical anomaly detection with rich metadata."""

from sqlalchemy.orm import Session as DBSession
import pandas as pd

from models import Transaction, Anomaly, Category


class AnomalyDetector:
    """Detect anomalous transactions using statistical methods."""

    def __init__(self, db: DBSession):
        self.db = db

    def detect(self, session_id: str) -> int:
        """Detect anomalies in transactions for a session."""
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.session_id == session_id)
            .filter(Transaction.category_id.isnot(None))
            .all()
        )

        if len(transactions) < 3:
            return 0

        # Build category lookup
        categories = self.db.query(Category).all()
        category_map = {c.id: c.name for c in categories}

        # Convert to DataFrame for analysis
        data = [
            {
                "id": t.id,
                "amount": t.amount,
                "category_id": t.category_id,
                "date": t.date,
                "description": t.description,
            }
            for t in transactions
        ]
        df = pd.DataFrame(data)

        anomalies_created = 0

        # Detect amount anomalies by category (for spending only)
        for category_id in df["category_id"].unique():
            cat_df = df[
                (df["category_id"] == category_id) & (df["amount"] < 0)
            ]  # Spending only

            if len(cat_df) < 3:
                continue

            # Calculate statistics
            mean = cat_df["amount"].mean()
            std = cat_df["amount"].std()

            if std == 0 or pd.isna(std):
                continue

            for _, row in cat_df.iterrows():
                z_score = (row["amount"] - mean) / std

                # Detect if significantly different (|z| > 2)
                if abs(z_score) > 2:
                    severity = self._get_severity(abs(z_score))
                    category_name = category_map.get(category_id, "Unknown")

                    explanation = self._generate_explanation(
                        category_name,
                        abs(row["amount"]),
                        abs(mean),
                        abs(z_score),
                    )

                    anomaly = Anomaly(
                        session_id=session_id,
                        transaction_id=row["id"],
                        anomaly_type="amount",
                        severity=severity,
                        expected_value=abs(mean),
                        actual_value=abs(row["amount"]),
                        z_score=z_score,
                        explanation=explanation,
                    )
                    self.db.add(anomaly)
                    anomalies_created += 1

        self.db.commit()
        return anomalies_created

    def _get_severity(self, z_score_abs: float) -> str:
        """Determine severity based on z-score magnitude."""
        if z_score_abs > 3:
            return "high"
        elif z_score_abs > 2.5:
            return "medium"
        else:
            return "low"

    def _generate_explanation(
        self, category: str, actual: float, expected: float, z_score_abs: float
    ) -> str:
        """Generate human-readable explanation for anomaly."""
        if actual > expected:
            direction = "higher"
            multiplier = actual / expected if expected > 0 else 0
            return (
                f"This {category} expense of ${actual:.2f} is {multiplier:.1f}x "
                f"your typical ${expected:.2f}. This is {z_score_abs:.1f} standard "
                f"deviations above your normal spending in this category."
            )
        else:
            direction = "lower"
            return (
                f"This {category} expense of ${actual:.2f} is unusually low "
                f"compared to your typical ${expected:.2f}."
            )
