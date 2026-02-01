"""
Module: synthetic_data.py
Description: Synthetic Transaction Data Generator for demo and testing purposes.

Generates realistic 3-month transaction data with:
    - Regular patterns (rent, subscriptions, utilities)
    - Anomalies (unusual large purchases)
    - Gray charges (small unknown recurring charges)

Author: Smart Financial Coach Team
Created: 2025-01-31

Usage:
    from synthetic_data import generate_synthetic_transactions
    transactions = generate_synthetic_transactions()
"""

import random
import csv
from datetime import datetime, timedelta, date
from typing import List, Dict


class SyntheticDataGenerator:
    """Generate realistic financial transactions for demo purposes."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the synthetic data generator.
        
        Args:
            seed: Random seed for reproducibility.
        """
        random.seed(seed)
        # Dynamic date range: 3 months ending yesterday
        today = datetime.now()
        self.end_date = today - timedelta(days=1)
        self.start_date = self.end_date - timedelta(days=90)  # ~3 months
    
    def generate(self, months: int = 3, txns_per_month: int = 50) -> List[Dict]:
        """
        Generate synthetic transactions.
        
        Args:
            months: Number of months of data to generate.
            txns_per_month: Approximate transactions per month.
        
        Returns:
            List of transaction dictionaries with date (date object), description, amount.
        """
        transactions = []
        current_date = self.start_date
        
        # Regular patterns (recurring charges, fixed expenses)
        patterns = self._get_recurring_patterns()
        
        for month in range(months):
            month_start = current_date + timedelta(days=30 * month)
            month_end = month_start + timedelta(days=30)
            
            # Add recurring transactions for this month
            for pattern in patterns:
                txn_date = month_start + timedelta(days=pattern['day'] - 1)
                if month_start <= txn_date < month_end:
                    variance = pattern.get('variance', 0)
                    amount = pattern['amount']
                    if variance > 0:
                        amount += random.uniform(-variance, variance)
                    
                    transactions.append({
                        'date': txn_date.date(),  # Return date object for DB compatibility
                        'description': pattern['name'],
                        'amount': round(amount, 2)
                    })
            
            # Add random transactions for variety
            random_txns = self._generate_random_transactions(
                month_start, month_end, txns_per_month - len(patterns)
            )
            transactions.extend(random_txns)
            
            # Add anomalies in months 2 and 3
            if month > 0:
                anomalies = self._generate_anomalies(month_start, month_end)
                transactions.extend(anomalies)
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        return transactions
    
    def _get_recurring_patterns(self) -> List[Dict]:
        """Return fixed recurring transaction patterns."""
        return [
            # Fixed monthly expenses
            {'name': 'LANDLORD PAYMENT - RENT', 'amount': -1500, 'day': 1, 'category': 'Housing'},
            {'name': 'NETFLIX SUBSCRIPTION', 'amount': -15.99, 'day': 5, 'category': 'Subscriptions'},
            {'name': 'SPOTIFY PREMIUM', 'amount': -9.99, 'day': 5, 'category': 'Subscriptions'},
            {'name': 'GYM MEMBERSHIP', 'amount': -49.99, 'day': 7, 'category': 'Entertainment'},
            {'name': 'ELECTRIC COMPANY - MONTHLY', 'amount': -120, 'day': 15, 'variance': 30, 'category': 'Utilities'},
            {'name': 'INTERNET SERVICE PROVIDER', 'amount': -79.99, 'day': 15, 'category': 'Utilities'},
            
            # Gray charges (small, unknown recurring)
            {'name': 'UNKNOWN APP PURCHASE', 'amount': -2.99, 'day': 12, 'category': 'Unknown'},
            {'name': 'APP STORE CHARGE', 'amount': -4.99, 'day': 20, 'category': 'Unknown'},
            {'name': 'MYSTERY SUBSCRIPTION', 'amount': -1.99, 'day': 25, 'category': 'Unknown'},
            
            # Income (twice per month - typical bi-weekly paycheck)
            {'name': 'PAYCHECK - DIRECT DEPOSIT', 'amount': 3200, 'day': 1, 'category': 'Income'},
            {'name': 'PAYCHECK - DIRECT DEPOSIT', 'amount': 3200, 'day': 15, 'category': 'Income'},
        ]
    
    def _generate_random_transactions(self, start_date: datetime, end_date: datetime, count: int) -> List[Dict]:
        """Generate random varied transactions."""
        categories = {
            'Groceries': [
                'WHOLE FOODS', 'TRADER JOES', 'SAFEWAY', 'KROGER', 'WHOLE FOODS',
                'SPROUTS', 'ALPHA BETA', 'RALPHS'
            ],
            'Dining': [
                'STARBUCKS COFFEE', 'MCDONALD', 'CHIPOTLE', 'PANERA', 'TACO BELL',
                'BURGER KING', 'SUBWAY', 'OLIVE GARDEN', 'APPLEBEES', 'CHILI'
            ],
            'Delivery': [
                'DOORDASH', 'UBER EATS', 'GRUBHUB', 'INSTACART'
            ],
            'Transportation': [
                'UBER', 'LYFT', 'SHELL GAS', 'CHEVRON', 'EXXON', 'BP FUEL',
                'PARKING - STREET', 'PARKING - GARAGE', 'METRO TRANSIT'
            ],
            'Shopping': [
                'AMAZON', 'TARGET', 'WALMART', 'COSTCO', 'BEST BUY',
                'HOME DEPOT', 'LOWES', 'IKEA', 'MALL STORE'
            ],
            'Entertainment': [
                'MOVIE THEATER', 'CONCERT TICKETS', 'BOWLING ALLEY',
                'AMUSEMENT PARK', 'ZOO ADMISSION'
            ],
            'Healthcare': [
                'CVS PHARMACY', 'WALGREENS', 'RITE AID', 'DR CLINIC', 'HOSPITAL',
                'URGENT CARE'
            ],
        }
        
        amount_ranges = {
            'Groceries': (40, 120),
            'Dining': (8, 45),
            'Delivery': (15, 35),
            'Transportation': (12, 50),
            'Shopping': (25, 150),
            'Entertainment': (20, 80),
            'Healthcare': (30, 200),
        }
        
        transactions = []
        for _ in range(count):
            category = random.choice(list(categories.keys()))
            merchant = random.choice(categories[category])
            min_amt, max_amt = amount_ranges[category]
            amount = round(random.uniform(min_amt, max_amt), 2)
            
            # Negative for expenses
            amount = -amount
            
            # Random day in range
            days_diff = (end_date - start_date).days
            random_date = start_date + timedelta(days=random.randint(0, days_diff))
            
            transactions.append({
                'date': random_date.date(),  # Return date object for DB compatibility
                'description': merchant,
                'amount': amount
            })
        
        return transactions
    
    def _generate_anomalies(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Generate unusual transaction anomalies.
        
        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
        
        Returns:
            List of anomaly transactions.
        """
        anomalies = [
            {
                'date': (start_date + timedelta(days=random.randint(5, 25))).date(),
                'description': 'ELECTRONICS STORE - LAPTOP',
                'amount': -1487.99,
                'reason': 'Large unusual purchase'
            },
            {
                'date': (start_date + timedelta(days=random.randint(5, 25))).date(),
                'description': 'RESTAURANT CATERING SERVICE',
                'amount': -523.45,
                'reason': 'Very high dining expense (possible event)'
            },
        ]
        
        return [{'date': a['date'], 'description': a['description'], 'amount': a['amount']} for a in anomalies]
    
    def to_csv(self, transactions: List[Dict], filename: str = 'sample_transactions.csv') -> str:
        """
        Export transactions to CSV file.
        
        Args:
            transactions: List of transaction dictionaries.
            filename: Output filename.
        
        Returns:
            The filename written.
        """
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'description', 'amount'])
            writer.writeheader()
            # Convert date objects to strings for CSV
            for txn in transactions:
                row = {
                    'date': txn['date'].isoformat() if hasattr(txn['date'], 'isoformat') else txn['date'],
                    'description': txn['description'],
                    'amount': txn['amount']
                }
                writer.writerow(row)
        print(f"✅ Generated {len(transactions)} transactions → {filename}")
        return filename
    
    def to_dict_list(self, transactions: List[Dict]) -> List[Dict]:
        """Return transactions as list of dicts (unchanged)."""
        return transactions


# =============================================================================
# Module-level function for main.py integration
# =============================================================================

def generate_synthetic_transactions(months: int = 3, txns_per_month: int = 50) -> List[Dict]:
    """
    Generate synthetic transaction data for demo purposes.
    
    This is the main entry point used by main.py for the /sample endpoint.
    
    Args:
        months: Number of months of data to generate (default: 3).
        txns_per_month: Approximate transactions per month (default: 50).
    
    Returns:
        List of transaction dictionaries with keys: date, description, amount.
        Date is a date object, amount is float (negative for expenses).
    
    Example:
        >>> transactions = generate_synthetic_transactions()
        >>> len(transactions)
        150  # approximately
    """
    generator = SyntheticDataGenerator(seed=42)
    return generator.generate(months=months, txns_per_month=txns_per_month)


def generate_and_save():
    """Main function to generate and save synthetic data."""
    print("🚀 Generating synthetic transaction data...")
    print("=" * 60)
    
    generator = SyntheticDataGenerator(seed=42)
    transactions = generator.generate(months=3, txns_per_month=50)
    
    # Save to CSV
    generator.to_csv(transactions, 'sample_transactions.csv')
    
    # Print summary
    print("\n📊 Dataset Summary:")
    print(f"   Total transactions: {len(transactions)}")
    first_date = transactions[0]['date']
    last_date = transactions[-1]['date']
    # Handle both date objects and strings
    first_str = first_date.isoformat() if hasattr(first_date, 'isoformat') else first_date
    last_str = last_date.isoformat() if hasattr(last_date, 'isoformat') else last_date
    print(f"   Date range: {first_str} to {last_str}")
    
    # Calculate totals
    total_income = sum(t['amount'] for t in transactions if t['amount'] > 0)
    total_expenses = sum(t['amount'] for t in transactions if t['amount'] < 0)
    net = total_income + total_expenses
    
    print(f"   Total income: ${total_income:,.2f}")
    print(f"   Total expenses: ${abs(total_expenses):,.2f}")
    print(f"   Net: ${net:,.2f}")
    
    # Show some sample transactions
    print("\n📝 Sample Transactions:")
    print("-" * 60)
    for txn in transactions[:10]:
        txn_date = txn['date']
        date_str = txn_date.isoformat() if hasattr(txn_date, 'isoformat') else txn_date
        print(f"   {date_str} | {txn['description']:30} | ${txn['amount']:>8.2f}")
    print("   ...")
    
    # Show recurring charges
    print("\n🔄 Recurring Charges Detected:")
    print("-" * 60)
    recurring = [
        ('NETFLIX SUBSCRIPTION', -15.99),
        ('SPOTIFY PREMIUM', -9.99),
        ('GYM MEMBERSHIP', -49.99),
        ('UNKNOWN APP PURCHASE', -2.99),
        ('APP STORE CHARGE', -4.99),
        ('MYSTERY SUBSCRIPTION', -1.99),
    ]
    for name, amount in recurring:
        annual = amount * 12
        print(f"   {name:30} | ${amount:>6.2f}/mo | ${annual:>7.2f}/yr")
    
    # Show anomalies
    print("\n⚠️  Anomalies in Data:")
    print("-" * 60)
    anomalies = [
        ('ELECTRONICS STORE - LAPTOP', -1487.99),
        ('RESTAURANT CATERING SERVICE', -523.45),
    ]
    for name, amount in anomalies:
        print(f"   {name:30} | ${amount:>8.2f} (unusual)")
    
    print("\n" + "=" * 60)
    print("✅ Synthetic data ready for import!")
    print("   Use 'sample_transactions.csv' in the application")
    
    return transactions


if __name__ == '__main__':
    generate_and_save()