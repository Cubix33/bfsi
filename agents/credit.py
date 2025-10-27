from typing import Dict, Any
from utils.mock_data import get_customer_data

class CreditAgent:
    """
    Credit Agent - Worker Agent
    Fetches credit score from mock credit bureau API
    """
    
    def __init__(self):
        self.credit_bureau_name = "CIBIL"
    
    def get_credit_score(self, phone: str) -> Dict[str, Any]:
        """
        Fetch credit score from customer database
        In production: calls CIBIL/Experian/Equifax API
        """
        
        # Fetch customer data
        customer = get_customer_data(phone)
        
        if customer and 'credit_score' in customer:
            credit_score = customer['credit_score']
        else:
            # Fallback to a default score
            credit_score = 700
        
        return {
            "score": credit_score,
            "bureau": self.credit_bureau_name,
            "max_score": 900,
            "report_date": "2025-10-27",
            "factors": self._get_credit_factors(credit_score)
        }
    
    def _get_credit_factors(self, score: int) -> Dict[str, str]:
        """Get factors affecting credit score"""
        if score >= 800:
            return {
                "payment_history": "Excellent",
                "credit_utilization": "Low",
                "credit_age": "Good",
                "credit_mix": "Diverse"
            }
        elif score >= 750:
            return {
                "payment_history": "Very Good",
                "credit_utilization": "Low",
                "credit_age": "Good",
                "credit_mix": "Good"
            }
        elif score >= 700:
            return {
                "payment_history": "Good",
                "credit_utilization": "Moderate",
                "credit_age": "Fair",
                "credit_mix": "Adequate"
            }
        else:
            return {
                "payment_history": "Needs Improvement",
                "credit_utilization": "High",
                "credit_age": "Limited",
                "credit_mix": "Limited"
            }
