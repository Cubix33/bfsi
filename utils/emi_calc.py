def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Calculate EMI using reducing balance method
    Formula: EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
    Where:
        P = Principal loan amount
        r = Monthly interest rate (annual rate / 12 / 100)
        n = Tenure in months
    """
    
    if annual_rate == 0:
        return principal / tenure_months
    
    monthly_rate = annual_rate / (12 * 100)
    
    emi = principal * monthly_rate * (1 + monthly_rate)**tenure_months / \
          ((1 + monthly_rate)**tenure_months - 1)
    
    return round(emi, 2)


def calculate_total_interest(principal: float, emi: float, tenure_months: int) -> float:
    """Calculate total interest payable"""
    total_payment = emi * tenure_months
    total_interest = total_payment - principal
    return round(total_interest, 2)


def generate_amortization_schedule(principal: float, annual_rate: float, tenure_months: int):
    """Generate month-by-month amortization schedule"""
    monthly_rate = annual_rate / (12 * 100)
    emi = calculate_emi(principal, annual_rate, tenure_months)
    
    balance = principal
    schedule = []
    
    for month in range(1, tenure_months + 1):
        interest_payment = balance * monthly_rate
        principal_payment = emi - interest_payment
        balance -= principal_payment
        
        schedule.append({
            "month": month,
            "emi": round(emi, 2),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "balance": round(max(0, balance), 2)
        })
    
    return schedule


# Test
if __name__ == "__main__":
    principal = 300000
    rate = 11.5
    tenure = 24
    
    emi = calculate_emi(principal, rate, tenure)
    print(f"EMI: ₹{emi:,.2f}")
    
    total_interest = calculate_total_interest(principal, emi, tenure)
    print(f"Total Interest: ₹{total_interest:,.2f}")
    
    schedule = generate_amortization_schedule(principal, rate, tenure)
    print("\nFirst 3 months:")
    for entry in schedule[:3]:
        print(entry)
