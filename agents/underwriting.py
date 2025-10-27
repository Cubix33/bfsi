from typing import Dict, Any

class UnderwritingAgent:
    """
    Underwriting Agent - Worker Agent
    Evaluates loan eligibility based on credit score and pre-approved limit
    """
    
    def __init__(self):
        self.min_credit_score = 700
        self.max_emi_ratio = 50  # EMI should be <= 50% of salary
    
    def evaluate_loan(
        self,
        customer_data: Dict[str, Any],
        loan_request: Dict[str, Any],
        credit_score: int
    ) -> Dict[str, Any]:
        """
        Underwriting logic:
        1. If amount <= pre-approved limit: INSTANT APPROVAL
        2. If amount <= 2x pre-approved limit: REQUEST SALARY SLIP
        3. If amount > 2x pre-approved limit: REJECT
        4. Credit score must be >= 700
        """
        
        requested_amount = loan_request["amount"]
        pre_approved_limit = customer_data["pre_approved_limit"]
        
        # Credit score check
        if credit_score < self.min_credit_score:
            return {
                "decision": "REJECTED",
                "reason": f"Credit score ({credit_score}) below minimum requirement (700)",
                "alternative": None
            }
        
        # Amount-based decision
        ratio = requested_amount / pre_approved_limit
        
        if ratio <= 1.0:
            # Instant approval
            return {
                "decision": "APPROVED",
                "reason": "Within pre-approved limit",
                "ratio": ratio,
                "requires_documents": False
            }
        
        elif ratio <= 2.0:
            # Requires salary slip verification
            return {
                "decision": "REQUIRES_SALARY_SLIP",
                "reason": "Amount exceeds pre-approved limit but within 2x range",
                "ratio": ratio,
                "requires_documents": True
            }
        
        else:
            # Rejected - too high
            return {
                "decision": "REJECTED",
                "reason": f"Requested amount (₹{requested_amount:,}) exceeds maximum limit",
                "ratio": ratio,
                "alternative": f"Maximum approved amount: ₹{int(pre_approved_limit * 2):,}"
            }
    
    def evaluate_with_salary(
        self,
        monthly_salary: int,
        monthly_emi: int
    ) -> Dict[str, Any]:
        """
        Evaluate loan after salary slip verification
        EMI should be <= 50% of monthly salary
        """
        
        emi_ratio = (monthly_emi / monthly_salary) * 100
        
        if emi_ratio <= self.max_emi_ratio:
            return {
                "decision": "APPROVED",
                "emi_ratio": emi_ratio,
                "reason": f"EMI-to-Income ratio ({emi_ratio:.1f}%) within acceptable range"
            }
        else:
            return {
                "decision": "REJECTED",
                "emi_ratio": emi_ratio,
                "reason": f"EMI-to-Income ratio ({emi_ratio:.1f}%) exceeds maximum (50%)"
            }
