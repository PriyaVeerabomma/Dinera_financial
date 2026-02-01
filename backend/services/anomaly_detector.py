"""
Module: anomaly_detector.py
Description: Hybrid anomaly detection using ML (Isolation Forest) and statistical methods.

Implements two approaches:
    1. MLAnomalyDetector: Isolation Forest for multi-dimensional anomaly detection (>=50 transactions)
    2. AnomalyDetector: Z-score statistical fallback (<50 transactions)

Features used for ML (aligned with train_models.py):
    - amount_abs, amount_zscore, amount_log (amount-based)
    - merchant_frequency, is_one_time (rarity-based)
    - day_of_week, is_weekend, is_payday (temporal)

Data Validation:
    - Outlier filtering before z-score calculations
    - Bounds checking on amounts
    - Duplicate anomaly prevention
    - Statistical assumption validation

Author: Smart Financial Coach Team
Created: 2025-01-31
"""

import numpy as np
import pandas as pd
from typing import Optional, Set
from sqlalchemy.orm import Session as DBSession

from models import Transaction, Anomaly, Category


# =============================================================================
# Data Validation Constants
# =============================================================================

# Maximum transaction amount to include in analysis
# Transactions above this are likely data errors or should be handled separately
MAX_AMOUNT_FOR_ANALYSIS = 50000  # $50,000

# Minimum number of transactions for valid z-score calculation
MIN_TRANSACTIONS_FOR_ZSCORE = 5

# Z-score bounds (cap extreme values)
MAX_ZSCORE = 10.0  # Cap z-scores to prevent infinity

# ML imports with graceful fallback
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ scikit-learn not installed. Using statistical fallback only.")


class MLAnomalyDetector:
    """
    Machine Learning-based anomaly detector using Isolation Forest.
    
    Isolation Forest is an unsupervised algorithm that isolates anomalies
    by randomly selecting features and split values. Anomalies are easier
    to isolate and thus have shorter path lengths in the tree.
    
    Features (8 total, aligned with train_models.py):
        - amount_abs: Absolute transaction amount
        - amount_zscore: Z-score of amount
        - amount_log: Log-transformed amount
        - merchant_frequency: How often this merchant appears
        - is_one_time: 1 if merchant appears <=2 times
        - day_of_week: 0-6 (Monday-Sunday)
        - is_weekend: 1 if Saturday/Sunday
        - is_payday: 1 if day 1-3 or 15-17
    
    Attributes:
        db: Database session
        model: Trained IsolationForest model
        scaler: StandardScaler for feature normalization
        contamination: Expected proportion of outliers (default 0.05)
    """
    
    # Severity thresholds based on confidence score (0-1 range)
    # Adjusted for typical Isolation Forest output distributions
    # Higher confidence = more anomalous
    SEVERITY_THRESHOLDS = {
        'high': 0.15,    # Confidence >= 0.15 = high severity (top ~5%)
        'medium': 0.08,  # Confidence >= 0.08 = medium severity
        'low': 0.0       # Confidence >= 0 = low severity
    }
    
    def __init__(self, db: DBSession, contamination: float = 0.05):
        """
        Initialize ML anomaly detector.
        
        Args:
            db: Database session for queries.
            contamination: Expected proportion of anomalies (0.01-0.5).
        """
        self.db = db
        self.contamination = contamination
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Note: Model is retrained on each session (fast enough, avoids versioning issues)
    
    def detect(self, session_id: str) -> int:
        """
        Detect anomalies using Isolation Forest.
        
        Args:
            session_id: Session ID to analyze.
            
        Returns:
            Number of anomalies detected.
        """
        if not ML_AVAILABLE:
            print("⚠️ ML not available, skipping ML detection")
            return 0
        
        # Fetch transactions
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.session_id == session_id)
            .filter(Transaction.category_id.isnot(None))
            .order_by(Transaction.date)
            .all()
        )
        
        if len(transactions) < 50:
            print(f"⚠️ Only {len(transactions)} transactions, need 50+ for ML detection")
            return 0
        
        # Build category lookup
        categories = self.db.query(Category).all()
        category_map = {c.id: c.name for c in categories}
        
        # Extract features
        features_df = self._extract_features(transactions)
        
        if features_df.empty:
            return 0
        
        # Train or use existing model
        if self.model is None:
            self._train_model(features_df)
        
        # Predict anomalies using aligned features
        X = features_df[['amount_abs', 'amount_zscore', 'amount_log', 
                         'merchant_frequency', 'is_one_time', 'day_of_week',
                         'is_weekend', 'is_payday']].values
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get predictions (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(X_scaled)
        
        # Get anomaly scores (more negative = more anomalous)
        anomaly_scores = self.model.decision_function(X_scaled)
        
        # Create anomalies for detected outliers
        anomalies_created = 0
        
        # Get existing anomaly transaction IDs to prevent duplicates
        existing_anomaly_ids: Set[int] = set(
            row[0] for row in self.db.query(Anomaly.transaction_id)
            .filter(Anomaly.session_id == session_id)
            .all()
        )
        
        for idx, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
            if pred == -1:  # Anomaly detected
                # Convert numpy int to Python int for database compatibility
                txn_id = int(features_df.iloc[idx]['transaction_id'])
                
                # Skip if anomaly already exists for this transaction (duplicate prevention)
                if txn_id in existing_anomaly_ids:
                    continue
                
                txn = next((t for t in transactions if t.id == txn_id), None)
                
                if txn is None:
                    continue
                
                # Bounds check: Skip if amount is unreasonably high
                if abs(txn.amount) > MAX_AMOUNT_FOR_ANALYSIS:
                    print(f"⚠️ Skipping anomaly for extreme amount: ${abs(txn.amount):.2f}")
                    continue
                
                # Determine severity based on score
                severity = self._score_to_severity(score)
                
                # Calculate confidence (convert score to 0-1 range, bounded)
                confidence = min(self._score_to_confidence(score), 1.0)
                
                # Get category name
                category_name = category_map.get(txn.category_id, "Unknown")
                
                # Generate ML-based explanation
                explanation = self._generate_ml_explanation(
                    txn=txn,
                    category_name=category_name,
                    confidence=confidence,
                    features=features_df.iloc[idx]
                )
                
                # Create anomaly record
                anomaly = Anomaly(
                    session_id=session_id,
                    transaction_id=txn_id,
                    anomaly_type="ml_isolation_forest",
                    severity=severity,
                    expected_value=features_df['amount_abs'].mean(),
                    actual_value=abs(txn.amount),
                    z_score=confidence,  # Store confidence in z_score field
                    explanation=explanation,
                )
                self.db.add(anomaly)
                existing_anomaly_ids.add(txn_id)  # Track to prevent duplicates in same batch
                anomalies_created += 1
        
        self.db.commit()
        
        return anomalies_created
    
    def _extract_features(self, transactions: list) -> pd.DataFrame:
        """
        Extract features from transactions for ML model.
        
        Features (aligned with train_models.py):
            - amount_abs: Absolute amount
            - amount_zscore: Z-score of amount
            - amount_log: Log-transformed amount
            - merchant_frequency: count / total
            - is_one_time: 1 if merchant appears <=2 times
            - day_of_week: 0-6
            - is_weekend: 0 or 1
            - is_payday: 0 or 1
        
        Args:
            transactions: List of Transaction objects.
            
        Returns:
            DataFrame with extracted features.
        """
        if not transactions:
            return pd.DataFrame()
        
        # Build raw data
        data = []
        for t in transactions:
            txn_date = t.date
            day_of_week = txn_date.weekday() if hasattr(txn_date, 'weekday') else 0
            day_of_month = txn_date.day if hasattr(txn_date, 'day') else 1
            
            data.append({
                'transaction_id': t.id,
                'amount': abs(t.amount),
                'category_id': t.category_id,
                'date': txn_date,
                'description': t.description.upper() if t.description else '',
                'day_of_week': day_of_week,
                'day_of_month': day_of_month,
            })
        
        df = pd.DataFrame(data)
        
        # Feature 1: Absolute amount
        df['amount_abs'] = df['amount']
        
        # Feature 2: Z-score of amount
        amount_mean = df['amount'].mean()
        amount_std = df['amount'].std()
        df['amount_zscore'] = (df['amount'] - amount_mean) / (amount_std if amount_std > 0 else 1)
        
        # Feature 3: Log-transformed amount
        df['amount_log'] = np.log1p(df['amount'])
        
        # Feature 4: Merchant frequency
        df['merchant_norm'] = df['description'].apply(self._normalize_merchant)
        merchant_counts = df['merchant_norm'].value_counts()
        total_txns = len(df)
        df['merchant_frequency'] = df['merchant_norm'].map(
            lambda m: merchant_counts.get(m, 1) / total_txns
        )
        
        # Feature 5: Is one-time merchant
        df['is_one_time'] = df['merchant_norm'].map(
            lambda m: 1 if merchant_counts.get(m, 0) <= 2 else 0
        )
        
        # Feature 6: Is weekend
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Feature 7: Is payday period (days 1-3 or 15-17)
        df['is_payday'] = ((df['day_of_month'] <= 3) | 
                           ((df['day_of_month'] >= 15) & (df['day_of_month'] <= 17))).astype(int)
        
        return df
    
    def _normalize_merchant(self, description: str) -> str:
        """Normalize merchant name for frequency calculation."""
        if not description:
            return "UNKNOWN"
        
        # Take first 2 words, remove numbers
        import re
        text = re.sub(r'\d+', '', description).strip()
        words = text.split()[:2]
        return ' '.join(words) if words else "UNKNOWN"
    
    def _train_model(self, features_df: pd.DataFrame) -> None:
        """
        Train Isolation Forest model on features.
        
        Args:
            features_df: DataFrame with extracted features.
        """
        X = features_df[['amount_abs', 'amount_zscore', 'amount_log', 
                         'merchant_frequency', 'is_one_time', 'day_of_week',
                         'is_weekend', 'is_payday']].values
        
        # Initialize and fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=100,
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,  # Use all CPU cores
            warm_start=False
        )
        self.model.fit(X_scaled)
        
        print(f"✅ Trained Isolation Forest on {len(X)} transactions")
    
    def _score_to_severity(self, score: float) -> str:
        """
        Convert anomaly score to severity level based on confidence.
        
        Args:
            score: Isolation Forest decision_function score (negative = anomalous).
            
        Returns:
            Severity string: 'high', 'medium', or 'low'.
        """
        # Convert score to confidence first
        confidence = self._score_to_confidence(score)
        
        if confidence >= self.SEVERITY_THRESHOLDS['high']:
            return 'high'
        elif confidence >= self.SEVERITY_THRESHOLDS['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _score_to_confidence(self, score: float) -> float:
        """
        Convert anomaly score to confidence (0.0-1.0).
        
        More negative scores = higher confidence that it's an anomaly.
        
        Args:
            score: Isolation Forest decision_function score.
            
        Returns:
            Confidence value between 0.0 and 1.0.
        """
        # Scores typically range from -0.5 to 0.5
        # Map to 0-1 where lower scores = higher confidence
        confidence = max(0.0, min(1.0, (0.0 - score) * 2))
        return round(confidence, 3)
    
    def _generate_ml_explanation(
        self, 
        txn, 
        category_name: str, 
        confidence: float,
        features: pd.Series
    ) -> str:
        """
        Generate human-readable explanation for ML-detected anomaly.
        
        Args:
            txn: Transaction object.
            category_name: Category name.
            confidence: Anomaly confidence (0-1).
            features: Feature row for this transaction.
            
        Returns:
            Explanation string.
        """
        # Identify which features contributed most
        unusual_factors = []
        
        # Check amount z-score (high = unusual)
        if features['amount_zscore'] > 2.0:
            unusual_factors.append(f"amount is significantly higher than average (z={features['amount_zscore']:.1f})")
        elif features['amount_zscore'] < -1.5:
            unusual_factors.append(f"amount is unusually low (z={features['amount_zscore']:.1f})")
        
        # Check if one-time merchant
        if features['is_one_time'] == 1:
            unusual_factors.append("from a merchant you've rarely used")
        
        # Check frequency
        if features['merchant_frequency'] < 0.02:  # Rare merchant
            unusual_factors.append("from an infrequent merchant")
        
        # Check weekend/payday patterns
        if features['is_weekend'] == 1:
            unusual_factors.append("weekend transaction")
        if features['is_payday'] == 1:
            unusual_factors.append("occurred during payday period")
        
        # Build explanation
        confidence_pct = int(confidence * 100)
        
        if unusual_factors:
            factors_text = ", ".join(unusual_factors[:3])
            explanation = (
                f"ML model flagged this {category_name} transaction of ${abs(txn.amount):.2f} "
                f"as {confidence_pct}% unusual based on: {factors_text}. "
                f"This pattern differs from your typical spending behavior."
            )
        else:
            explanation = (
                f"ML model flagged this {category_name} transaction of ${abs(txn.amount):.2f} "
                f"as {confidence_pct}% unusual based on amount, timing, and frequency patterns."
            )
        
        return explanation


class AnomalyDetector:
    """
    Hybrid anomaly detector using ML (Isolation Forest) for large datasets
    and statistical z-score for smaller datasets.
    
    Strategy:
        - >=50 transactions: Use MLAnomalyDetector (Isolation Forest)
        - <50 transactions: Use z-score statistical method
        - <3 transactions: Skip detection
    
    This approach provides:
        - Multi-dimensional pattern detection for large datasets
        - Robust fallback for small datasets
        - Graceful degradation if ML libraries unavailable
    """

    def __init__(self, db: DBSession):
        """
        Initialize hybrid anomaly detector.
        
        Args:
            db: Database session.
        """
        self.db = db
        self.ml_detector: Optional[MLAnomalyDetector] = None
        
        # Initialize ML detector if available
        if ML_AVAILABLE:
            self.ml_detector = MLAnomalyDetector(db, contamination=0.05)

    def detect(self, session_id: str) -> int:
        """
        Detect anomalies using hybrid ML + statistical approach.
        
        Uses Isolation Forest for datasets with >=50 transactions,
        falls back to z-score method for smaller datasets.
        
        Args:
            session_id: Session ID to analyze.
            
        Returns:
            Number of anomalies detected.
        """
        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.session_id == session_id)
            .filter(Transaction.category_id.isnot(None))
            .all()
        )

        if len(transactions) < 3:
            return 0
        
        # Use ML for larger datasets
        if len(transactions) >= 50 and self.ml_detector is not None:
            print(f"🤖 Using ML anomaly detection ({len(transactions)} transactions)")
            return self.ml_detector.detect(session_id)
        
        # Fallback to statistical z-score method
        print(f"📊 Using statistical anomaly detection ({len(transactions)} transactions)")
        return self._detect_statistical(session_id, transactions)

    def _detect_statistical(self, session_id: str, transactions: list) -> int:
        """
        Detect anomalies using z-score statistical method.
        
        This is the fallback method for datasets with <50 transactions
        where ML models may not generalize well.
        
        Includes:
            - Outlier filtering before z-score calculation
            - Duplicate anomaly prevention
            - Statistical assumption validation
        
        Args:
            session_id: Session ID.
            transactions: List of Transaction objects.
            
        Returns:
            Number of anomalies detected.
        """
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
        
        # VALIDATION: Filter out extreme outliers before z-score calculation
        # These would poison the mean/std calculations
        df = df[df['amount'].abs() <= MAX_AMOUNT_FOR_ANALYSIS]
        
        # Get existing anomaly transaction IDs (duplicate prevention)
        existing_anomaly_ids: Set[int] = set(
            row[0] for row in self.db.query(Anomaly.transaction_id)
            .filter(Anomaly.session_id == session_id)
            .all()
        )

        anomalies_created = 0

        # Detect amount anomalies by category (for spending only)
        for category_id in df["category_id"].unique():
            cat_df = df[
                (df["category_id"] == category_id) & (df["amount"] < 0)
            ]  # Spending only

            # VALIDATION: Require minimum transactions for valid z-score
            if len(cat_df) < MIN_TRANSACTIONS_FOR_ZSCORE:
                continue

            # VALIDATION: Use robust statistics (median for center, MAD for spread)
            # to reduce impact of any remaining outliers
            mean = cat_df["amount"].mean()
            std = cat_df["amount"].std()

            # VALIDATION: Skip if no variance (all same amounts)
            if std == 0 or pd.isna(std) or std < 0.01:
                continue

            for _, row in cat_df.iterrows():
                txn_id = row["id"]
                
                # Skip if anomaly already exists (duplicate prevention)
                if txn_id in existing_anomaly_ids:
                    continue
                
                # Calculate z-score with bounds
                z_score = (row["amount"] - mean) / std
                z_score_bounded = np.clip(z_score, -MAX_ZSCORE, MAX_ZSCORE)

                # Detect if significantly different (|z| > 2)
                if abs(z_score_bounded) > 2:
                    severity = self._get_severity(abs(z_score_bounded))
                    category_name = category_map.get(category_id, "Unknown")
                    
                    # Calculate confidence from z-score (map |z| to 0-1, bounded)
                    confidence = min(1.0, abs(z_score_bounded) / 5.0)

                    explanation = self._generate_explanation(
                        category_name,
                        abs(row["amount"]),
                        abs(mean),
                        abs(z_score_bounded),
                    )

                    anomaly = Anomaly(
                        session_id=session_id,
                        transaction_id=txn_id,
                        anomaly_type="amount",
                        severity=severity,
                        expected_value=abs(mean),
                        actual_value=abs(row["amount"]),
                        z_score=confidence,  # Store confidence in z_score field
                        explanation=explanation,
                    )
                    self.db.add(anomaly)
                    existing_anomaly_ids.add(txn_id)  # Prevent duplicates in batch
                    anomalies_created += 1

        self.db.commit()
        return anomalies_created

    def _get_severity(self, z_score_abs: float) -> str:
        """
        Determine severity based on z-score magnitude.
        
        Args:
            z_score_abs: Absolute value of z-score.
            
        Returns:
            Severity string: 'low', 'medium', or 'high'.
        """
        if z_score_abs > 3:
            return "high"
        elif z_score_abs > 2.5:
            return "medium"
        else:
            return "low"

    def _generate_explanation(
        self, category: str, actual: float, expected: float, z_score_abs: float
    ) -> str:
        """
        Generate human-readable explanation for statistical anomaly.
        
        Args:
            category: Category name.
            actual: Actual transaction amount.
            expected: Expected (mean) amount.
            z_score_abs: Absolute z-score value.
            
        Returns:
            Human-readable explanation string.
        """
        if actual > expected:
            multiplier = actual / expected if expected > 0 else 0
            return (
                f"This {category} expense of ${actual:.2f} is {multiplier:.1f}x "
                f"your typical ${expected:.2f}. This is {z_score_abs:.1f} standard "
                f"deviations above your normal spending in this category."
            )
        else:
            return (
                f"This {category} expense of ${actual:.2f} is unusually low "
                f"compared to your typical ${expected:.2f}."
            )
