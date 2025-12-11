import os
from typing import Dict, List, Any
from groq import Groq
from agents.sales import SalesAgent
from agents.verification import VerificationAgent
from agents.underwriting import UnderwritingAgent
from agents.document import DocumentAgent
from agents.credit import CreditAgent
from agents.upload import UploadAgent
from agents.risk import RiskAgent
from utils.mock_data import get_customer_data
import json
from dotenv import load_dotenv
import platform
import subprocess
import re
from user_store import add_application
from uuid import uuid4
from datetime import datetime

# Load environment variables
load_dotenv()

def open_pdf(filepath):
    """Open PDF file with default PDF viewer"""
    if not os.path.exists(filepath):
        print(f"PDF file not found: {filepath}")
        print(f"Please check the sanction_letters folder")
        return
    
    try:
        abs_path = os.path.abspath(filepath)
        if platform.system() == 'Windows':
            os.startfile(abs_path)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', abs_path])
        else:
            subprocess.call(['xdg-open', abs_path])
            
        print(f"PDF opened: {abs_path}")
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")
        print(f"Please open manually: {os.path.abspath(filepath)}")


# --- SECURED LOAN AGENT ---
class SecuredLoanAgent:
    """
    Secured Loan Agent - Handles collateral-based loan offers
    """
    def __init__(self):
        # LTV Ratios
        self.collateral_ltv = {
            "property": 0.65, "vehicle": 0.75, "gold": 0.75,
            "fd": 0.90, "mutual_funds": 0.70, "stocks": 0.60, "land": 0.60
        }
        
        # Interest Rates
        self.interest_rates = {
            "property": 9.5, "vehicle": 10.5, "gold": 9.0,
            "fd": 8.0, "mutual_funds": 11.0, "stocks": 12.0, "land": 10.0
        }
    
    def parse_collateral(self, collateral_str: str) -> Dict[str, Any]:
        """Parse collateral string to extract type and value - ROBUST"""
        if not collateral_str or collateral_str.lower() in ["none", "no", "nil", "na", "nothing"]:
            return None
        
        value = None
        clean_str = collateral_str.replace('â', '').replace('¹', '').strip()
        
        # Logic to handle 'lacks', 'lakhs', 'k' in description
        patterns = [
            r'₹\s*([\d,]+)',             
            r'value[:\s]+([\d,]+)',      
            r'\b([\d,]{4,})\b',          
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, clean_str, re.IGNORECASE)
            for match in matches:
                try:
                    clean_val = int(match.replace(',', '').replace(' ', ''))
                    if clean_val > 1000: 
                        value = clean_val
                        break
                except: continue
            if value: break

        if not value:
            lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)', clean_str, re.IGNORECASE)
            if lakh_match:
                value = int(float(lakh_match.group(1)) * 100000)
            elif re.search(r'(\d+(?:\.\d+)?)\s*k', clean_str, re.IGNORECASE):
                k_match = re.search(r'(\d+(?:\.\d+)?)\s*k', clean_str, re.IGNORECASE)
                value = int(float(k_match.group(1)) * 1000)

        if not value:
            return None
        
        collateral_lower = clean_str.lower()
        
        if any(x in collateral_lower for x in ["fixed deposit", " fd", "deposit"]):
            collateral_type = "fd"
        elif any(x in collateral_lower for x in ["property", "flat", "house", "villa", "apartment", "shop", "bhk", "residential"]):
            collateral_type = "property"
        elif any(x in collateral_lower for x in ["vehicle", "car", "bike", "scooter"]):
            collateral_type = "vehicle"
        elif any(x in collateral_lower for x in ["gold", "jewelry"]):
            collateral_type = "gold"
        elif any(x in collateral_lower for x in ["mutual fund", "mf", "stock", "share"]):
            collateral_type = "stocks"
        else:
            collateral_type = "property"
        
        ltv = self.collateral_ltv.get(collateral_type, 0.60)
        max_loan = int(value * ltv)
        
        return {
            "type": collateral_type,
            "description": collateral_str,
            "value": value,
            "max_loan": max_loan,
            "interest_rate": self.interest_rates.get(collateral_type, 10.0),
            "ltv_ratio": ltv * 100
        }
    
    def get_secured_loan_offer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        collateral_info = self.parse_collateral(customer_data.get("collateral", "None"))
        
        if not collateral_info:
            return {"eligible": False, "reason": "No collateral available"}
        
        return {
            "eligible": True,
            "collateral": collateral_info,
            "max_amount": collateral_info["max_loan"],
            "interest_rate": collateral_info["interest_rate"],
            "min_tenure": 12,
            "max_tenure": 120,
            "processing_fee": "1% of loan amount"
        }

# --- MASTER AGENT ---
class MasterAgent:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.state = {
            "stage": "initial",
            "customer_data": None,
            "temp_customer_data": None,
            "awaiting_profile_permission": False,
            "awaiting_secured_loan_decision": False,
            "awaiting_detail_correction": False,
            "awaiting_secured_loan_application": False,
            "awaiting_manual_data_entry": False,
            "manual_data_step": 0,
            "secured_loan_offer": None,
            "loan_request": {},
            "verification_status": False,
            "credit_score": None,
            "underwriting_result": None,
            "documents_uploaded": False,
            "final_decision": None,
            "waiting_for_manual_upload": False,
            "user_personality": "friendly"
        }
        
        self.sales_agent = SalesAgent(api_key)
        self.verification_agent = VerificationAgent()
        self.credit_agent = CreditAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.document_agent = DocumentAgent()
        self.upload_agent = UploadAgent()
        self.secured_loan_agent = SecuredLoanAgent()
        self.risk_agent = RiskAgent()
        
    def _is_affirmative(self, text: str) -> bool:
        return any(word in text.lower() for word in ["yes", "yep", "ya", "y", "sure", "ok", "okay", "proceed", "accept", "correct"])

    def _is_negative(self, text: str) -> bool:
        return any(word in text.lower() for word in ["no", "n", "nope", "nah", "cancel", "stop"])
    
    def _detect_personality(self, user_message: str) -> str:
        return "friendly"

    def _get_personality_prompt(self, personality: str) -> str:
        return """
- Your Vibe: You are a helpful, professional, and human bank agent.
- Formatting: DO NOT use asterisks (*), bolding (**), or emojis. Use simple text formatting.
- Style: Speak naturally, like a bank officer talking to a customer in person.
- Negotiation: If the EMI is too high, suggest extending the tenure or lowering the amount.
"""

    def start_conversation(self):
        print("=" * 80)
        print("TATA CAPITAL - Personal Loan Assistant")
        print("=" * 80)
        
        welcome_msg = """Hello! Welcome to Tata Capital.
I am your personal loan assistant, and I am here to help you get the best loan offer tailored to your needs.
May I have your phone number to get started?"""
        
        self.conversation_history.append({"role": "assistant", "content": welcome_msg})
        return welcome_msg
    
    def process_message(self, user_message: str) -> str:
        self.conversation_history.append({"role": "user", "content": user_message})
        
        if self.state["stage"] == "initial":
            return self._handle_initial_stage(user_message)
        elif self.state["stage"] == "new_customer_onboarding":
            return self._handle_new_customer_onboarding(user_message)
        elif self.state["stage"] == "needs_assessment":
            return self._handle_needs_assessment(user_message)
        elif self.state["stage"] == "verification":
            return self._handle_verification(user_message)
        elif self.state["stage"] == "credit_check":
            return self._handle_credit_check(user_message)
        elif self.state["stage"] == "underwriting":
            return self._handle_underwriting(user_message)
        elif self.state["stage"] == "document_upload":
            return self._handle_document_upload(user_message)
        elif self.state["stage"] == "secured_loan":
            return self._handle_secured_loan_flow(user_message)
        elif self.state["stage"] == "approval":
            return self._handle_approval(user_message)
        elif self.state["stage"] == "rejection":
            return self._handle_rejection(user_message)
        elif self.state["stage"] == "completed":
            return self._handle_post_completion_qa(user_message)
        else:
            return "I am sorry, something went wrong. Let me restart our conversation."

    def _handle_initial_stage(self, user_message: str) -> str:
        phone = ''.join(filter(str.isdigit, user_message))
        
        if len(phone) >= 10:
            customer_data = get_customer_data(phone[-10:])
            
            if customer_data:
                self.state["temp_customer_data"] = customer_data
                self.state["awaiting_profile_permission"] = True
                self.state["stage"] = "verification"
                response = "Thank you. I found an existing profile linked to this number.\n\nMay I access your profile information to provide you with personalized loan offers?\n\nPlease reply with Yes or No."
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                self.state["awaiting_manual_data_entry"] = True
                self.state["manual_data_step"] = 1
                self.state["temp_customer_data"] = {"phone": phone[-10:]}
                self.state["stage"] = "new_customer_onboarding"
                
                response = "I couldn't find your profile in our system. No worries, let me collect your details.\n\nWhat is your full name?"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        else:
            response = "I didn't catch a valid phone number. Could you please provide your 10-digit mobile number?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def _handle_new_customer_onboarding(self, user_message: str) -> str:
        step = self.state["manual_data_step"]
        
        if step == 1:
            self.state["temp_customer_data"]["name"] = user_message.strip()
            self.state["manual_data_step"] = 2
            response = "Great. What is your city?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        elif step == 2:
            self.state["temp_customer_data"]["city"] = user_message.strip()
            self.state["manual_data_step"] = 3
            response = "Perfect. What is your complete address?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        elif step == 3:
            self.state["temp_customer_data"]["address"] = user_message.strip()
            self.state["manual_data_step"] = 4
            response = "Thank you. What is your email address?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        elif step == 4:
            self.state["temp_customer_data"]["email"] = user_message.strip()
            self.state["manual_data_step"] = 5
            response = "Thanks. What is your monthly income (in rupees)?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

        elif step == 5:
            raw_text = user_message.lower().replace(',', '').strip()
            multiplier = 1
            if 'k' in raw_text: multiplier = 1000
            elif 'l' in raw_text: multiplier = 100000
            elif 'c' in raw_text: multiplier = 10000000
            
            income_match = re.search(r'(\d+(\.\d+)?)', raw_text)
            
            if income_match:
                monthly_income = int(float(income_match.group(1)) * multiplier)
                self.state["temp_customer_data"]["monthly_income"] = monthly_income
                self.state["temp_customer_data"]["pre_approved_limit"] = min(monthly_income * 10, 500000)
                
                self.state["manual_data_step"] = 6
                response = """Great. One last question:

Do you have any collateral that you would like to use for a secured loan? This could be Property, Vehicle, Gold, or Fixed Deposits.

Please provide details like '3BHK worth 30 lakhs' or 'Honda City Car'.
(Or simply type 'none' if you don't have collateral)"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                response = "I didn't catch a valid amount. Please type your monthly income (e.g., 50000)."
                self.conversation_history.append({"role": "assistant", "content": response})
                return response

        elif step == 6:
            user_lower = user_message.lower().strip()
            if user_lower in ["none", "no", "nothing", "don't have", "nahi", "nil"]:
                collateral_value = "None"
            else:
                collateral_value = user_message.strip()
            
            self.state["temp_customer_data"].update({
                "credit_score": 700,
                "employment": "Salaried",
                "collateral": collateral_value,
                "id": f"C{100 + hash(self.state['temp_customer_data']['phone']) % 100:02d}",
                "age": 30
            })
            
            risk_result = self.risk_agent.get_safety_score(self.state["temp_customer_data"])
            self.state["temp_customer_data"]["internal_safety_score"] = risk_result["safety_score"]
            self.state["customer_data"] = self.state["temp_customer_data"]
            self.state["awaiting_manual_data_entry"] = False
            self.state["stage"] = "needs_assessment"
            
            pre_approved_limit = self.state['customer_data']['pre_approved_limit']
            collateral_info = self.secured_loan_agent.parse_collateral(collateral_value)
            
            summary = f"Perfect! Thank you for providing your details, {self.state['customer_data']['name']}.\n\n"
            summary += f"Profile Summary:\n"
            summary += f"- Monthly Income: Rs. {self.state['temp_customer_data']['monthly_income']:,}\n"
            
            if collateral_info:
                summary += f"- Collateral: {collateral_info['description']} (Value: Rs. {collateral_info['value']:,})\n"
                summary += f"\nBased on this, you have two options:\n"
                summary += f"1. Unsecured Loan: Up to Rs. {pre_approved_limit:,}\n"
                summary += f"2. Secured Loan: Up to Rs. {collateral_info['max_loan']:,} at {collateral_info['interest_rate']}% interest.\n"
            else:
                summary += f"You are eligible for a pre-approved unsecured loan of up to Rs. {pre_approved_limit:,}.\n"
                
            summary += "\nNow, let's discuss your loan needs:\n"
            summary += "1. What is the purpose of the loan?\n"
            summary += "2. How much amount do you need?\n"
            summary += "3. What tenure (years or months) works for you?"
            
            self.conversation_history.append({"role": "assistant", "content": summary})
            return summary

    def _handle_needs_assessment(self, user_message: str) -> str:
        personality_instructions = self._get_personality_prompt(self.state["user_personality"])
        sales_response = self.sales_agent.negotiate_loan(
            user_message, self.state["customer_data"], self.conversation_history,
            self.state["loan_request"], personality_instructions
        )
        self.state["loan_request"] = sales_response.get("loan_details", self.state["loan_request"])
        
        if sales_response.get("ready_for_next_stage"):
            self.state["stage"] = "verification"
            msg = self._get_verification_summary()
            self.conversation_history.append({"role": "assistant", "content": msg})
            return msg
        else:
            response = sales_response["message"]
            self.conversation_history.append({"role": "assistant", "content": response})
            return response

    def _get_verification_summary(self) -> str:
        return f"""Perfect. Let me summarize your request:
- Amount: Rs. {self.state['loan_request']['amount']:,}
- Purpose: {self.state['loan_request']['purpose']}
- Tenure: {self.state['loan_request']['tenure']} months
- EMI: Rs. {self.state['loan_request']['emi']:,}

For security, I need to verify your details:
- Name: {self.state['customer_data']['name']}
- Phone: {self.state['customer_data']['phone']}
- Address: {self.state['customer_data']['address']}
- Email: {self.state['customer_data'].get('email', 'Not provided')}

Is this correct? (Yes/No)"""

    def _handle_verification(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        # 1. Check for LOAN updates (Amount, Tenure, Purpose) -> Handled by Sales Agent
        if any(word in user_lower for word in ["purpose", "amount", "tenure", "year", "month", "lacs", "lakh"]) and \
           any(word in user_lower for word in ["change", "update", "modify", "wrong"]):
             self.state["stage"] = "needs_assessment"
             return "Understood. Let's update your loan details.\n" + self._handle_needs_assessment(user_message)

        # 2. Check for PERSONAL updates (Smart Capture) -> Update directly
        personal_updates = {}
        
        # Address
        if "address" in user_lower:
            # Matches: "change address to Delhi", "Address is Delhi", "update address: Delhi"
            addr_match = re.search(r'address\s*(?:is|to|:|->)\s*(.+)', user_message, re.IGNORECASE)
            if addr_match:
                personal_updates["address"] = addr_match.group(1).strip()
        
        # Name
        if "name" in user_lower:
            name_match = re.search(r'name\s*(?:is|to|:|->)\s*([a-zA-Z\s\.]+)', user_message, re.IGNORECASE)
            if name_match:
                name_val = name_match.group(1).strip()
                if len(name_val) > 2: personal_updates["name"] = name_val

        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', user_message)
        if email_match:
             if "email" in user_lower or "@" in user_message:
                 personal_updates["email"] = email_match.group(0)

        # Apply updates
        if personal_updates:
            self.state["customer_data"].update(personal_updates)
            self.state["awaiting_detail_correction"] = False
            return f"✅ Updated: {', '.join(personal_updates.keys())}. Let me re-verify:\n\n" + self._get_verification_summary()

        # 3. Handle Fallback Correction Loop (if Smart Capture failed or just "No" was said)
        if self.state.get("awaiting_detail_correction"):
            updated_data = {}
            if not updated_data and len(user_message) > 3:
                # Naive assumption fallback
                if "@" in user_message: updated_data["email"] = user_message.strip()
                else: updated_data["address"] = user_message.strip() 
            
            if updated_data:
                self.state["customer_data"].update(updated_data)
                self.state["awaiting_detail_correction"] = False
                return "Details updated. Let me re-verify...\n\n" + self._get_verification_summary()

        # 4. Profile Permission Loop
        if self.state.get("awaiting_profile_permission"):
            if self._is_affirmative(user_lower):
                customer_data = self.state["temp_customer_data"]
                self.state["customer_data"] = customer_data
                self.state["stage"] = "needs_assessment"
                self.state["awaiting_profile_permission"] = False
                response = f"Great. I found your profile, {customer_data['name']}. You have a pre-approved limit of Rs. {customer_data['pre_approved_limit']:,}.\n\nCould you tell me how much loan amount you are looking for and for what purpose?"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            elif self._is_negative(user_lower):
                self.state["awaiting_profile_permission"] = False
                self.state["awaiting_manual_data_entry"] = True
                self.state["manual_data_step"] = 1
                self.state["stage"] = "new_customer_onboarding"
                response = "No problem. Let's enter your details manually. What is your full name?"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        # 5. Standard Yes/No Verification
        if self._is_affirmative(user_lower):
            self.state["verification_status"] = True
            self.state["stage"] = "credit_check"
            return "Thank you. Checking your credit profile now..." + "\n\n" + self._handle_credit_check("")
        
        elif self._is_negative(user_lower):
            self.state["awaiting_detail_correction"] = True
            return "Oh, I see. Which personal detail is incorrect? (Name, Phone, Address, or Email)"
        
        return "Please confirm if your details are correct (Yes/No). Or say 'change amount' if you want to modify the loan."

    def _handle_credit_check(self, user_message: str) -> str:
        credit_result = self.credit_agent.get_credit_score(self.state["customer_data"]["phone"])
        self.state["credit_score"] = credit_result["score"]
        
        if credit_result["score"] < 700:
            self.state["stage"] = "rejection"
            response = f"I have reviewed your profile. Your credit score is {credit_result['score']}, which is below our minimum for unsecured loans."
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n" + self._send_rejection_options()
        else:
            self.state["stage"] = "underwriting"
            response = f"Your credit score of {credit_result['score']} is strong. Evaluating eligibility..."
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n\n" + self._handle_underwriting("")

    def _handle_underwriting(self, user_message: str) -> str:
        underwriting_result = self.underwriting_agent.evaluate_loan(
            customer_data=self.state["customer_data"],
            loan_request=self.state["loan_request"],
            credit_score=self.state["credit_score"]
        )
        self.state["underwriting_result"] = underwriting_result
        
        if underwriting_result["decision"] == "APPROVED":
            self.state["stage"] = "approval"
            return "Congratulations! Your loan is APPROVED.\n" + self._generate_sanction_letter()
        elif underwriting_result["decision"] == "REQUIRES_SALARY_SLIP":
            self.state["stage"] = "document_upload"
            return "We need to verify your income. Please upload your latest salary slip (type 'upload' or 'manual upload')."
        else:
            self.state["stage"] = "rejection"
            response = f"I have reviewed your application. The requested amount of Rs. {self.state['loan_request']['amount']:,} exceeds our unsecured limits based on your profile."
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n" + self._send_rejection_options()

    def _handle_document_upload(self, user_message: str) -> str:
        if "skip" in user_message.lower():
            self.state["stage"] = "rejection"
            return self._send_rejection_options()
        return "Please upload your salary slip to proceed."

    def _send_rejection_options(self) -> str:
        collateral_info = self.secured_loan_agent.parse_collateral(self.state["customer_data"].get("collateral", "None"))
        
        req_amount = self.state["loan_request"].get("amount", 0)
        pre_approved = self.state["customer_data"]["pre_approved_limit"]
        suggested = max(pre_approved, int(req_amount * 0.85 / 10000) * 10000)
        
        response = "Here are your options:\n"
        response += f"1. Try a lower amount: Rs. {suggested:,} (Reply 'Option 1')\n"
        if collateral_info:
            response += f"2. Secured Loan: Get up to Rs. {collateral_info['max_loan']:,} using your {collateral_info['type']} (Reply 'Option 2')\n"
            response += f"3. Accept Pre-approved: Rs. {pre_approved:,} (Reply 'Option 3')\n"
        else:
            response += f"2. Accept Pre-approved: Rs. {pre_approved:,} (Reply 'Option 2')\n"
            
        return response

    def _handle_rejection(self, user_message: str) -> str:
        user_lower = user_message.lower()
        collateral_info = self.secured_loan_agent.parse_collateral(self.state["customer_data"].get("collateral", "None"))
        
        is_option_1 = "option 1" in user_lower or "lower amount" in user_lower
        is_option_2 = "option 2" in user_lower
        is_option_3 = "option 3" in user_lower
        
        if is_option_1:
            req_amount = self.state["loan_request"].get("amount", 0)
            suggested = max(self.state["customer_data"]["pre_approved_limit"], int(req_amount * 0.85 / 10000) * 10000)
            self.state["loan_request"]["amount"] = suggested
            self.state["stage"] = "underwriting"
            return f"Okay, let's try for Rs. {suggested:,}. Re-evaluating..." + "\n\n" + self._handle_underwriting("")

        elif is_option_2 and collateral_info:
            secured_offer = self.secured_loan_agent.get_secured_loan_offer(self.state["customer_data"])
            self.state["secured_loan_offer"] = secured_offer
            self.state["awaiting_secured_loan_application"] = True
            self.state["stage"] = "secured_loan"
            
            msg = f"""Perfect choice. Let me explain your Secured Loan option.

Collateral: {secured_offer['collateral']['description']} (Value: Rs. {secured_offer['collateral']['value']:,})

Loan Offer:
- Maximum Amount: Rs. {secured_offer['max_amount']:,}
- Interest Rate: {secured_offer['interest_rate']}% p.a.
- Tenure: Up to 10 years

How much would you like to borrow? (Max: Rs. {secured_offer['max_amount']:,})"""
            self.conversation_history.append({"role": "assistant", "content": msg})
            return msg
        
        elif (is_option_3) or (is_option_2 and not collateral_info) or "yes" in user_lower:
            self.state["loan_request"]["amount"] = self.state["customer_data"]["pre_approved_limit"]
            self.state["stage"] = "approval"
            self.state["final_decision"] = "APPROVED"
            return f"Great. Processing your pre-approved loan of Rs. {self.state['loan_request']['amount']:,}." + "\n" + self._generate_sanction_letter()

        else:
             return self._send_rejection_options()

    def _handle_secured_loan_flow(self, user_message: str) -> str:
        if not self.state.get("awaiting_secured_loan_application"):
            return "Session expired. Type 'restart'."
            
        user_lower = user_message.lower()
        secured_offer = self.state["secured_loan_offer"]
        
        if any(w in user_lower for w in ["max", "maximum", "full", "all"]):
            requested_amount = secured_offer["max_amount"]
        else:
            nums = re.findall(r'[\d,]+', user_message)
            if nums:
                val = int(nums[0].replace(',', ''))
                if val < 1000 and "l" in user_lower: val *= 100000
                elif val < 100: val *= 100000 
                requested_amount = val
            else:
                return f"Please specify an amount up to Rs. {secured_offer['max_amount']:,}."

        if requested_amount > secured_offer["max_amount"]:
            return f"That exceeds the limit. Maximum allowed is Rs. {secured_offer['max_amount']:,}. Would you like the maximum?"
        
        self.state["loan_request"]["amount"] = requested_amount
        self.state["loan_request"]["interest_rate"] = secured_offer["interest_rate"]
        self.state["loan_request"]["loan_type"] = "secured"
        
        tenure = 120 
        if "year" in user_lower:
            y_match = re.search(r'(\d+)\s*y', user_lower)
            if y_match: tenure = int(y_match.group(1)) * 12
            
        self.state["loan_request"]["tenure"] = tenure
        r = secured_offer["interest_rate"] / (12 * 100)
        emi = int(requested_amount * r * (1+r)**tenure / ((1+r)**tenure - 1))
        self.state["loan_request"]["emi"] = emi
        
        self.state["stage"] = "approval"
        self.state["final_decision"] = "APPROVED_SECURED"
        self.state["awaiting_secured_loan_application"] = False
        
        return f"Excellent. Your Secured Loan of Rs. {requested_amount:,} is APPROVED.\n\nLoan Details:\n- Tenure: {tenure} months\n- Interest: {secured_offer['interest_rate']}%\n- EMI: Rs. {emi:,}\n\n" + self._generate_sanction_letter()

    def _generate_sanction_letter(self) -> str:
        from utils.pdf_generator import generate_sanction_letter
        
        pdf_path = generate_sanction_letter(
            customer_data=self.state["customer_data"],
            loan_details=self.state["loan_request"]
        )
        
        self.state["stage"] = "completed" 
        
        try:
            open_pdf(pdf_path)
        except: pass
        
        return f"Sanction Letter Generated: {pdf_path}\n\nOur team will contact you shortly. Is there anything else you would like to know about your loan?"

    def _handle_approval(self, user_message: str):
        return self._handle_post_completion_qa(user_message)

    def _handle_post_completion_qa(self, user_message: str) -> str:
        system_prompt = """You are a helpful bank agent. The user has just completed their loan application.
Answer their questions simply and clearly. 
DO NOT use Markdown tables. Use bullet points or simple paragraphs.
DO NOT use asterisks or emojis.
Keep answers short and human-like."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history[-4:])
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b", 
                messages=messages,
                max_tokens=200
            )
            ans = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": ans})
            return ans
        except:
            return "I can answer any questions about your loan terms or the difference between secured and unsecured loans."

# --- MAIN LOOP ---
def main():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        return

    while True:
        master = MasterAgent(api_key)
        welcome_message = master.start_conversation()
        print(f"\nAssistant: {welcome_message}\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == "restart":
                    print("\n" + "="*40 + "\nRestarting...\n" + "="*40)
                    break 
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("\nAssistant: Goodbye! Have a nice day.")
                    return 
                
                if not user_input: continue
                
                response = master.process_message(user_input)
                print(f"\nAssistant: {response}\n")
                
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    main()