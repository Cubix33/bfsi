import os
import shutil
from typing import Dict, Any


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
            
            return {
                "success": True,
                "file_path": dest_path,
                "message": f"Salary slip uploaded successfully: {filename}"
            }
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
