import os
import shutil
import re
from typing import Dict, Any, Optional

try:
    # Lightweight PDF text extraction
    import PyPDF2  # type: ignore
except Exception:
    PyPDF2 = None


class UploadAgent:
    """
    Upload Agent - Worker Agent
    Handles salary slip uploads
    """
    
    def __init__(self):
        self.salary_slips_folder = "salary_slips"
        self.uploaded_folder = "uploaded_documents"
        
        # Create folders if they don't exist
        os.makedirs(self.salary_slips_folder, exist_ok=True)
        os.makedirs(self.uploaded_folder, exist_ok=True)

    def _extract_text_from_pdf(self, file_path: str) -> str:
        if not PyPDF2:
            return ""
        try:
            text = []
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text() or ""
                    if t:
                        text.append(t)
            return "\n".join(text)
        except Exception:
            return ""

    def _extract_salary_amount(self, text: str) -> Optional[int]:
        """
        Heuristics to locate monthly salary/net pay in the slip text.
        - Looks for lines with keywords and a currency/number nearby.
        - Falls back to the largest currency-like number if keywords not found.
        """
        if not text:
            return None

        # Normalize text
        norm = text.lower()

        patterns = [
            r"net\s*(pay|salary)[^\d]*(₹|rs\.?|inr)?\s*([\d,]+)",
            r"gross\s*(salary|pay)[^\d]*(₹|rs\.?|inr)?\s*([\d,]+)",
            r"monthly\s*(salary|income)[^\d]*(₹|rs\.?|inr)?\s*([\d,]+)",
        ]

        for pat in patterns:
            m = re.search(pat, norm, re.IGNORECASE)
            if m:
                amt = m.group(3)
                try:
                    return int(amt.replace(",", ""))
                except Exception:
                    pass

        # Fallback: pick the largest currency-like number in the document
        numbers = [int(n.replace(",", "")) for n in re.findall(r"(₹|rs\.?|inr)?\s*([\d,]{4,})", norm)
                   if n[1].strip()]
        if numbers:
            # Heuristic: monthly salary is usually among the larger values but < 500000
            plausible = [x for x in numbers if 5000 <= x <= 500000]
            if plausible:
                return sorted(plausible)[-1]
            return sorted(numbers)[-1]
        return None

    def analyze_uploaded_file(self, file_path: str) -> Dict[str, Any]:
        """Attempt to extract monthly salary from the uploaded salary slip.
        Returns a dict with keys: success, monthly_salary (optional), message.
        """
        text = self._extract_text_from_pdf(file_path)
        salary = self._extract_salary_amount(text)
        if salary:
            return {
                "success": True,
                "monthly_salary": salary,
                "message": f"Detected monthly salary: ₹{salary:,}"
            }
        return {
            "success": False,
            "message": "Could not auto-read salary from the document"
        }
    
    def process_upload(self, customer_name: str) -> Dict[str, Any]:
        """
        Simulate salary slip upload
        In production: handles actual file upload from web interface
        """
        
        # Format filename
        filename = f"SalarySlip_{customer_name.replace(' ', '_')}.pdf"
        source_path = os.path.join(self.salary_slips_folder, filename)
        dest_path = os.path.join(self.uploaded_folder, filename)
        
        # Check if salary slip exists in database
        if os.path.exists(source_path):
            # Copy to uploaded folder
            shutil.copy(source_path, dest_path)
            
            analysis = self.analyze_uploaded_file(dest_path)
            result = {
                "success": True,
                "file_path": dest_path,
                "message": f"Salary slip uploaded successfully: {filename}"
            }
            result.update(analysis)
            return result
        else:
            # Salary slip not found - create a placeholder
            # In production, this would prompt user to upload
            print(f"\n⚠️  Salary slip not found: {source_path}")
            print(f"   For demo: Creating placeholder file...")
            
            # Create placeholder
            with open(dest_path, 'w') as f:
                f.write("PLACEHOLDER SALARY SLIP\n")
                f.write(f"Employee: {customer_name}\n")
            
            return {
                "success": True,
                "file_path": dest_path,
                "message": f"Placeholder created for demo: {filename}"
            }
