from typing import Dict, Any, Optional
import json
import os

# Load customer database from JSON
def load_customer_database() -> Dict[str, Dict[str, Any]]:
    """Load customer data from customer_data.json"""
    try:
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'customer_data.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Create phone-indexed dictionary
        customer_db = {}
        for customer in data['customers']:
            # Standardize the customer data structure
            customer_db[customer['phone']] = {
                "id": customer['id'],
                "name": customer['name'],
                "age": customer['age'],
                "city": customer['city'],
                "phone": customer['phone'],
                "address": customer.get('address', f"{customer['city']}, India"),
                "email": customer.get('email', f"{customer['name'].lower().replace(' ', '.')}@email.com"),
                "current_loans": customer.get('current_loans', 'None'),
                "pre_approved_limit": customer['preapproved_limit'],
                "credit_score": customer['score'],
                "employment": customer.get('employment', 'Salaried'),
                "company": customer.get('company', 'N/A'),
                "monthly_income": customer['salary'],
                "collateral": customer.get('collateral', 'None')  # Added .get() for safety
            }
        return customer_db
    except FileNotFoundError:
        print("Warning: customer_data.json not found. Using fallback data.")
        return FALLBACK_CUSTOMER_DATABASE
    except Exception as e:
        print(f"Error loading customer data: {e}. Using fallback data.")
        return FALLBACK_CUSTOMER_DATABASE

# Fallback database in case JSON file is not found
FALLBACK_CUSTOMER_DATABASE = {
    "7303201137": {
        "id": "C01",
        "name": "Riya Sharma",
        "age": 28,
        "city": "Delhi",
        "phone": "7303201137",
        "address": "Block A, Sector 15, Rohini, Delhi - 110085",
        "email": "riya.sharma@email.com",
        "current_loans": "None",
        "pre_approved_limit": 500000,
        "credit_score": 782,
        "employment": "Salaried",
        "company": "Tech Innovations Pvt Ltd",
        "monthly_income": 60000,
        "collateral": "Residential Property - 2BHK Apartment (Estimated Value: ₹45,00,000)"  # ADDED
    },
    "8667765432": {
        "id": "C02",
        "name": "Kabir Rao",
        "age": 31,
        "city": "Mumbai",
        "phone": "8667765432",
        "address": "78, Andheri West, Mumbai - 400053",
        "email": "kabir.rao@email.com",
        "current_loans": "Car Loan: ₹3,50,000",
        "pre_approved_limit": 200000,
        "credit_score": 698,
        "employment": "Salaried",
        "company": "Finance Corp",
        "monthly_income": 52000,
        "collateral": "Vehicle - Honda City 2019 (Estimated Value: ₹6,50,000)"  # ADDED
    }
}

# Load the database on module import
CUSTOMER_DATABASE = load_customer_database()

def get_customer_data(phone: str) -> Optional[Dict[str, Any]]:
    """Fetch customer data from database by phone number"""
    # Clean phone number (remove spaces, dashes, etc.)
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Try direct match first
    if clean_phone in CUSTOMER_DATABASE:
        return CUSTOMER_DATABASE[clean_phone]
    
    # Try last 10 digits
    if len(clean_phone) >= 10:
        last_10 = clean_phone[-10:]
        if last_10 in CUSTOMER_DATABASE:
            return CUSTOMER_DATABASE[last_10]
    
    return None

def get_all_customers() -> Dict[str, Dict[str, Any]]:
    """Get all customer data"""
    return CUSTOMER_DATABASE

def get_offer_data(phone: str) -> Optional[Dict[str, Any]]:
    """Get pre-approved offer for customer"""
    customer = get_customer_data(phone)
    if customer:
        return {
            "customer_id": customer['id'],
            "offer_type": "Pre-Approved Personal Loan",
            "max_amount": customer["pre_approved_limit"],
            "min_interest_rate": 10.5,
            "max_tenure": 60,
            "special_offer": "0% processing fee for this month",
            "valid_until": "2025-11-30"
        }
    return None

def get_customer_by_id(customer_id: str) -> Optional[Dict[str, Any]]:
    """Get customer by ID (C01, C02, etc.)"""
    for phone, data in CUSTOMER_DATABASE.items():
        if data['id'] == customer_id:
            return data
    return None

# Test function
if __name__ == "__main__":
    print("Testing customer database...")
    print(f"Total customers loaded: {len(CUSTOMER_DATABASE)}")
    
    # Test fetching customer
    test_phone = "7303201137"
    customer = get_customer_data(test_phone)
    if customer:
        print(f"\nTest customer found:")
        print(f"Name: {customer['name']}")
        print(f"City: {customer['city']}")
        print(f"Pre-approved limit: ₹{customer['pre_approved_limit']:,}")
        print(f"Credit Score: {customer['credit_score']}")
        print(f"Collateral: {customer.get('collateral', 'None')}")  # ADDED
    
    # List all customers
    print("\nAll customers:")
    for phone, data in CUSTOMER_DATABASE.items():
        print(f"{data['id']}: {data['name']} - {data['city']} - ₹{data['pre_approved_limit']:,} - Collateral: {data.get('collateral', 'None')}")  # ADDED
