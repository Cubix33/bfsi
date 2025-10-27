"""
Test script to verify all 20 customers work correctly
"""
from utils.mock_data import get_customer_data, get_all_customers
from agents.credit import CreditAgent

def test_all_customers():
    """Test data for all 20 customers"""
    
    print("=" * 80)
    print("TESTING ALL 20 CUSTOMERS")
    print("=" * 80)
    
    all_customers = get_all_customers()
    credit_agent = CreditAgent()
    
    print(f"\nTotal customers loaded: {len(all_customers)}\n")
    
    for phone, customer in all_customers.items():
        print(f"Customer ID: {customer['id']}")
        print(f"Name: {customer['name']}")
        print(f"Phone: {customer['phone']}")
        print(f"City: {customer['city']}")
        print(f"Age: {customer['age']}")
        print(f"Credit Score: {customer['credit_score']}")
        print(f"Pre-approved Limit: ₹{customer['pre_approved_limit']:,}")
        print(f"Monthly Salary: ₹{customer['monthly_income']:,}")
        print(f"Current Loans: {customer['current_loans']}")
        print(f"Company: {customer['company']}")
        
        # Test credit score fetch
        credit_result = credit_agent.get_credit_score(phone)
        print(f"Credit Bureau Score: {credit_result['score']}")
        
        # Determine eligibility
        if credit_result['score'] >= 700:
            print("✅ ELIGIBLE for loan")
        else:
            print("❌ NOT ELIGIBLE (score < 700)")
        
        print("-" * 80)
    
    print("\n✅ All customer data loaded successfully!")


def test_specific_customers():
    """Test specific customer scenarios"""
    
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC SCENARIOS")
    print("=" * 80)
    
    # Test Case 1: High credit score, high limit (Rohan Mehta)
    print("\n1. Testing Rohan Mehta (High score, high limit)")
    customer = get_customer_data("9988776655")
    if customer:
        print(f"Name: {customer['name']}")
        print(f"Score: {customer['credit_score']} (Expected: 780)")
        print(f"Pre-approved: ₹{customer['pre_approved_limit']:,} (Expected: ₹6,00,000)")
        print(f"Salary: ₹{customer['monthly_income']:,}")
        print("✅ Should get instant approval for amounts up to ₹6,00,000")
    
    # Test Case 2: Low credit score (Megha Singh)
    print("\n2. Testing Megha Singh (Low credit score)")
    customer = get_customer_data("9512345678")
    if customer:
        print(f"Name: {customer['name']}")
        print(f"Score: {customer['credit_score']} (Expected: 660)")
        print(f"Pre-approved: ₹{customer['pre_approved_limit']:,}")
        print("❌ Should be REJECTED (score < 700)")
    
    # Test Case 3: Borderline case (Kabir Rao)
    print("\n3. Testing Kabir Rao (Borderline score)")
    customer = get_customer_data("8667765432")
    if customer:
        print(f"Name: {customer['name']}")
        print(f"Score: {customer['credit_score']} (Expected: 698)")
        print(f"Pre-approved: ₹{customer['pre_approved_limit']:,}")
        print("❌ Should be REJECTED (score < 700)")
    
    # Test Case 4: Good candidate (Riya Sharma)
    print("\n4. Testing Riya Sharma (Excellent candidate)")
    customer = get_customer_data("7303201137")
    if customer:
        print(f"Name: {customer['name']}")
        print(f"Score: {customer['credit_score']} (Expected: 782)")
        print(f"Pre-approved: ₹{customer['pre_approved_limit']:,} (Expected: ₹5,00,000)")
        print(f"Salary: ₹{customer['monthly_income']:,}")
        print("✅ Excellent candidate for instant approval")
    
    # Test Case 5: Moderate limit (Siddharth Taneja)
    print("\n5. Testing Siddharth Taneja (Below 700 score)")
    customer = get_customer_data("9778899001")
    if customer:
        print(f"Name: {customer['name']}")
        print(f"Score: {customer['credit_score']} (Expected: 688)")
        print(f"Pre-approved: ₹{customer['pre_approved_limit']:,}")
        print("❌ Should be REJECTED (score < 700)")


def test_phone_number_variations():
    """Test different phone number formats"""
    
    print("\n" + "=" * 80)
    print("TESTING PHONE NUMBER VARIATIONS")
    print("=" * 80)
    
    test_numbers = [
        "7303201137",  # Standard
        "+917303201137",  # With country code
        "91 7303201137",  # With space
        "730-320-1137",  # With dashes
    ]
    
    for number in test_numbers:
        customer = get_customer_data(number)
        if customer:
            print(f"✅ '{number}' -> Found: {customer['name']}")
        else:
            print(f"❌ '{number}' -> Not found")


if __name__ == "__main__":
    test_all_customers()
    test_specific_customers()
    test_phone_number_variations()
    
    print("\n" + "=" * 80)
    print("SUMMARY: Credit Score Distribution")
    print("=" * 80)
    
    all_customers = get_all_customers()
    
    eligible = sum(1 for c in all_customers.values() if c['credit_score'] >= 700)
    not_eligible = sum(1 for c in all_customers.values() if c['credit_score'] < 700)
    
    print(f"Total Customers: {len(all_customers)}")
    print(f"Eligible (≥700): {eligible} ({eligible/len(all_customers)*100:.1f}%)")
    print(f"Not Eligible (<700): {not_eligible} ({not_eligible/len(all_customers)*100:.1f}%)")
    
    avg_score = sum(c['credit_score'] for c in all_customers.values()) / len(all_customers)
    print(f"Average Credit Score: {avg_score:.1f}")
