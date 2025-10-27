from typing import Dict, Any
import os
import re
from utils.mock_data import get_customer_data

class DocumentAgent:
    """
    Document Agent - Worker Agent
    Processes uploaded salary slips and extracts salary information
    """
    
    def __init__(self):
        self.salary_slips_folder = "salary_slips"
    
    def extract_salary_info(self, file_path: str) -> Dict[str, Any]:
        """
        Extract salary information from uploaded PDF
        In production: use OCR (PyPDF2, pdfplumber, or AWS Textract)
        """
        
        # Extract name from filename (e.g., "SalarySlip_Kabir_Rao.pdf")
        filename = os.path.basename(file_path)
        name_match = re.search(r'SalarySlip_(.+)\.pdf', filename)
        
        if name_match:
            name = name_match.group(1).replace('_', ' ')
            
            # Get salary data from customer database
            salary_data = self._get_salary_from_database(name)
            
            return {
                "success": True,
                "basic_salary": salary_data["basic_salary"],
                "hra": salary_data["hra"],
                "other_allowances": salary_data["other_allowances"],
                "gross_salary": salary_data["gross_salary"],
                "deductions": salary_data["deductions"],
                "net_salary": salary_data["net_salary"],
                "company": salary_data.get("company", "N/A"),
                "month": salary_data.get("month", "August 2025")
            }
        else:
            # Fallback
            return {
                "success": True,
                "basic_salary": 36400,
                "hra": 10400,
                "other_allowances": 5200,
                "gross_salary": 52000,
                "deductions": 2600,
                "net_salary": 49400,
                "company": "N/A",
                "month": "August 2025"
            }
    
    def _get_salary_from_database(self, name: str) -> Dict[str, int]:
        """Get salary breakdown from customer database"""
        from utils.mock_data import get_all_customers
        
        # Find customer by name
        all_customers = get_all_customers()
        
        for phone, customer in all_customers.items():
            if customer['name'].lower() == name.lower():
                monthly_salary = customer['monthly_income']
                
                # Calculate salary breakdown (typical Indian salary structure)
                basic_salary = int(monthly_salary * 0.70)  # 70% basic
                hra = int(monthly_salary * 0.20)  # 20% HRA
                other_allowances = int(monthly_salary * 0.10)  # 10% other
                gross_salary = basic_salary + hra + other_allowances
                deductions = int(gross_salary * 0.05)  # 5% deductions (PF, tax)
                net_salary = gross_salary - deductions
                
                return {
                    "basic_salary": basic_salary,
                    "hra": hra,
                    "other_allowances": other_allowances,
                    "gross_salary": gross_salary,
                    "deductions": deductions,
                    "net_salary": net_salary,
                    "company": customer.get('company', 'N/A'),
                    "month": "August 2025"
                }
        
        # Fallback if customer not found
        return {
            "basic_salary": 36400,
            "hra": 10400,
            "other_allowances": 5200,
            "gross_salary": 52000,
            "deductions": 2600,
            "net_salary": 49400,
            "company": "N/A"
        }
