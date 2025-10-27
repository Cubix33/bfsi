from typing import Dict, Any
import random

class VerificationAgent:
    """
    Verification Agent - Worker Agent
    Verifies customer KYC details from mock CRM
    """
    
    def __init__(self):
        self.crm_database = {}  # Mock CRM
    
    def verify_customer(self, customer_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Verify customer details against CRM database
        In production: calls actual CRM API
        """
        
        # Mock verification logic
        # In real scenario: check phone, address, PAN, Aadhaar
        
        verification_checks = {
            "phone_verified": True,
            "address_verified": True,
            "identity_verified": True,
            "overall_verified": True
        }
        
        # Simulate 95% success rate
        if random.random() < 0.95:
            verification_checks["overall_verified"] = True
        else:
            verification_checks["overall_verified"] = False
            verification_checks["phone_verified"] = False
        
        return {
            "verified": verification_checks["overall_verified"],
            "checks": verification_checks,
            "message": "Verification successful" if verification_checks["overall_verified"] else "Verification failed"
        }
    
    def verify_phone_otp(self, phone: str, otp: str) -> bool:
        """Verify OTP (mock implementation)"""
        # In production: verify against sent OTP
        return otp == "123456"
    
    def verify_address(self, address: str) -> bool:
        """Verify address with utility bill/Aadhaar"""
        # Mock implementation
        return len(address) > 10
