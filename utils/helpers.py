from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import base64
from uuid import UUID
import pandas as pd
import numpy as np


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def parse_datetime_string(date_string: str) -> datetime:
    """Parse datetime string with multiple format support"""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse datetime string: {date_string}")


def calculate_date_range(days: int = 180) -> tuple[datetime, datetime]:
    """Calculate date range for transaction analysis"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format amount as currency string"""
    return f"{currency}{amount:,.2f}"


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return ((new_value - old_value) / old_value) * 100


def categorize_transaction_amount(amount: float) -> str:
    """Categorize transaction by amount range"""
    if amount < 100:
        return "micro"
    elif amount < 1000:
        return "small"
    elif amount < 10000:
        return "medium"
    elif amount < 50000:
        return "large"
    else:
        return "very_large"


def detect_spending_anomalies(amounts: List[float], threshold: float = 2.0) -> List[int]:
    """Detect anomalous spending using z-score"""
    if len(amounts) < 3:
        return []
    
    mean_amount = np.mean(amounts)
    std_amount = np.std(amounts)
    
    if std_amount == 0:
        return []
    
    anomalies = []
    for i, amount in enumerate(amounts):
        z_score = abs((amount - mean_amount) / std_amount)
        if z_score > threshold:
            anomalies.append(i)
    
    return anomalies


def calculate_financial_health_score(
    savings_rate: float,
    income_volatility: float,
    spending_volatility: float,
    essential_spending_ratio: float
) -> float:
    """Calculate overall financial health score (0-100)"""
    
    # Savings rate component (0-30 points)
    savings_score = min(30, max(0, savings_rate * 100))
    
    # Stability component (0-30 points)
    volatility_penalty = (income_volatility + spending_volatility) * 15
    stability_score = max(0, 30 - volatility_penalty)
    
    # Essential spending component (0-25 points)
    essential_score = min(25, essential_spending_ratio * 30)
    
    # Base score (15 points for having any financial activity)
    base_score = 15
    
    total_score = savings_score + stability_score + essential_score + base_score
    return min(100, max(0, total_score))


def generate_spending_insights(spending_data: Dict[str, float]) -> List[str]:
    """Generate textual insights from spending data"""
    insights = []
    
    if not spending_data:
        return ["No spending data available for analysis"]
    
    total_spending = sum(spending_data.values())
    sorted_categories = sorted(spending_data.items(), key=lambda x: x[1], reverse=True)
    
    # Top spending category
    if sorted_categories:
        top_category, top_amount = sorted_categories[0]
        percentage = (top_amount / total_spending) * 100
        insights.append(f"Highest spending category is {top_category} ({percentage:.1f}% of total)")
    
    # Essential vs non-essential spending
    essential_categories = {'groceries', 'utilities', 'rent', 'healthcare', 'transport', 'bills'}
    essential_spending = sum(amount for category, amount in spending_data.items() 
                           if category.lower() in essential_categories)
    
    if total_spending > 0:
        essential_percentage = (essential_spending / total_spending) * 100
        if essential_percentage > 70:
            insights.append("Very high focus on essential spending indicates good financial discipline")
        elif essential_percentage > 50:
            insights.append("Balanced spending between essential and discretionary items")
        else:
            insights.append("High discretionary spending - consider reviewing non-essential expenses")
    
    # Spending diversity
    num_categories = len(spending_data)
    if num_categories > 8:
        insights.append("Diverse spending across multiple categories")
    elif num_categories < 4:
        insights.append("Limited spending categories - may indicate focused spending habits")
    
    return insights


def create_monthly_trend_data(monthly_data: Dict[str, Dict[str, float]]) -> Dict[str, List]:
    """Create trend data for frontend charts"""
    months = sorted(monthly_data.keys())
    
    trend_data = {
        "months": months,
        "income": [],
        "spending": [],
        "savings": [],
        "savings_rate": []
    }
    
    for month in months:
        data = monthly_data.get(month, {})
        income = data.get('income', 0)
        spending = data.get('spending', 0)
        savings = income - spending
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        trend_data["income"].append(income)
        trend_data["spending"].append(spending)
        trend_data["savings"].append(savings)
        trend_data["savings_rate"].append(round(savings_rate, 1))
    
    return trend_data


def validate_account_number(account_no: str) -> bool:
    """Validate Indian bank account number format"""
    # Remove spaces and convert to uppercase
    account_no = account_no.replace(" ", "").upper()
    
    # Basic validation: 9-18 digits
    if not account_no.isdigit():
        return False
    
    if len(account_no) < 9 or len(account_no) > 18:
        return False
    
    return True


def validate_ifsc_code(ifsc_code: str) -> bool:
    """Validate Indian IFSC code format"""
    # Remove spaces and convert to uppercase
    ifsc_code = ifsc_code.replace(" ", "").upper()
    
    # IFSC format: 4 letters + 7 characters (letters/digits)
    if len(ifsc_code) != 11:
        return False
    
    # First 4 characters should be letters
    if not ifsc_code[:4].isalpha():
        return False
    
    # 5th character should be 0
    if ifsc_code[4] != '0':
        return False
    
    # Last 6 characters should be alphanumeric
    if not ifsc_code[5:].isalnum():
        return False
    
    return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    return numerator / denominator if denominator != 0 else default


def round_to_precision(value: float, precision: int = 2) -> float:
    """Round value to specified precision"""
    return round(value, precision)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)
