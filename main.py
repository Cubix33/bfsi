import os
from typing import Dict, List, Any
from groq import Groq
from agents.sales import SalesAgent
from agents.verification import VerificationAgent
from agents.underwriting import UnderwritingAgent
from agents.document import DocumentAgent
from agents.credit import CreditAgent
from agents.upload import UploadAgent
from agents.risk import RiskAgent  # <-- 1. IMPORT XGBOOST/RISK AGENT
from utils.mock_data import get_customer_data, get_offer_data
import json
from dotenv import load_dotenv
import platform
import subprocess
import re
from user_store import add_application
from uuid import uuid4
from datetime import datetime
from deep_translator import GoogleTranslator


def open_pdf(filepath):
    """Open PDF file with default PDF viewer"""
    
    if not os.path.exists(filepath):
        print(f"⚠️  PDF file not found: {filepath}")
        print(f"   Please check the sanction_letters folder")
        return
    
    try:
        abs_path = os.path.abspath(filepath)
        
        if platform.system() == 'Windows':
            os.startfile(abs_path)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', abs_path])
        else:
            subprocess.call(['xdg-open', abs_path])
            
        print(f"✅ PDF opened: {abs_path}")
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")
        print(f"Please open manually: {os.path.abspath(filepath)}")


# --- NEW SECURED LOAN AGENT (Added to main.py for simplicity) ---
class SecuredLoanAgent:
    """
    Secured Loan Agent - Handles collateral-based loan offers
    """
    
    def __init__(self):
        # LTV Ratios
        self.collateral_ltv = {
            "property": 0.65,      # 65% for Property
            "vehicle": 0.75,       # 75% for Vehicle
            "gold": 0.75,          # 75% for Gold
            "fd": 0.90,            # 90% for Fixed Deposits
            "mutual_funds": 0.70,  # 70% for Mutual Funds
            "stocks": 0.60,        # 60% for Stocks
            "land": 0.60           # 60% for Land
        }
        
        # Interest Rates
        self.interest_rates = {
            "property": 9.5,
            "vehicle": 10.5,
            "gold": 9.0,
            "fd": 8.0,
            "mutual_funds": 11.0,
            "stocks": 12.0,
            "land": 10.0
        }
    
    def parse_collateral(self, collateral_str: str) -> Dict[str, Any]:
        """Parse collateral string to extract type and value - ROBUST"""
        if not collateral_str or collateral_str.lower() == "none":
            return None
        
        # print(f"🔍 DEBUG: Parsing collateral: {collateral_str}") # Removed debug
        
        value = None
        
        # Clean string from potential OCR/encoding errors
        clean_str = collateral_str.replace('â', '').replace('¹', '').strip()
        
        # Regex patterns to find the value
        patterns = [
            r'₹\s*([\d,]+)',             # Finds "₹ 45,00,000"
            r'\(.*?₹\s*([\d,]+)\)',     # Finds "(Value: ₹45,00,000)"
            r'value[:\s]+([\d,]+)',    # Finds "Value: 45,00,000"
            r':\s*₹?\s*([\d,]{6,})',    # Finds ": 45,00,000"
            r'\b([\d,]{6,})\b',        # Finds any number > 6 digits
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, clean_str, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        clean_value = match.replace(',', '').replace(' ', '').strip()
                        test_value = int(clean_value)
                        if test_value >= 50000: # Min collateral value
                            value = test_value
                            break
                    except (ValueError, AttributeError):
                        continue
                if value:
                    break
        
        if not value: # Try lakh/crore
            lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac)', clean_str, re.IGNORECASE)
            if lakh_match:
                try: value = int(float(lakh_match.group(1)) * 100000)
                except ValueError: pass
        
        if not value: # Give up
            return None
        
        collateral_lower = clean_str.lower()
        
        # Determine collateral type
        if "fixed deposit" in collateral_lower or " fd" in collateral_lower or "deposit" in collateral_lower:
            collateral_type = "fd"
        elif any(word in collateral_lower for word in ["property", "flat", "house", "villa", "apartment", "shop", "residential", "commercial", "2bhk", "3bhk", "1bhk"]):
            collateral_type = "property"
        elif any(word in collateral_lower for word in ["vehicle", "car", "bike", "city", "swift", "creta", "enfield", "honda", "maruti", "hyundai"]):
            collateral_type = "vehicle"
        elif "gold" in collateral_lower or "jewelry" in collateral_lower or "jewellery" in collateral_lower:
            collateral_type = "gold"
        elif "mutual fund" in collateral_lower or "mf" in collateral_lower:
            collateral_type = "mutual_funds"
        elif "stock" in collateral_lower or "share" in collateral_lower or "equity" in collateral_lower:
            collateral_type = "stocks"
        elif "land" in collateral_lower or "agricultural" in collateral_lower or "plot" in collateral_lower:
            collateral_type = "land"
        else:
            collateral_type = "property" # Default
        
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
        """Generate secured loan offer based on customer's collateral"""
        collateral_info = self.parse_collateral(customer_data.get("collateral", "None"))
        
        if not collateral_info:
            return {
                "eligible": False,
                "reason": "No collateral available"
            }
        
        return {
            "eligible": True,
            "collateral": collateral_info,
            "max_amount": collateral_info["max_loan"],
            "interest_rate": collateral_info["interest_rate"],
            "min_tenure": 12,
            "max_tenure": 120, # Up to 10 years
            "processing_fee": "1% of loan amount"
        }
# --- END OF NEW AGENT ---


class MasterAgent:
    """
    Master Agent - Main Orchestrator
    Manages conversation flow and coordinates all worker agents
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.user_language = "en"
        self.state = {
            "stage": "initial",
            "customer_data": None,
            "temp_customer_data": None,
            "awaiting_profile_permission": False,
            "awaiting_secured_loan_decision": False,
            "awaiting_detail_correction": False,
            "awaiting_secured_loan_application": False, # New flag
            "awaiting_manual_data_entry": False, # New flag
            "manual_data_step": 0, # New flag
            "secured_loan_offer": None, # New state
            "loan_request": {},
            "verification_status": False,
            "credit_score": None,
            "underwriting_result": None,
            "documents_uploaded": False,
            "final_decision": None,
            "waiting_for_manual_upload": False,
            "user_personality": "friendly",
        }
        
        self.sales_agent = SalesAgent(api_key)
        self.verification_agent = VerificationAgent()
        self.credit_agent = CreditAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.document_agent = DocumentAgent()
        self.upload_agent = UploadAgent()
        self.secured_loan_agent = SecuredLoanAgent() # Initialize new agent
        self.risk_agent = RiskAgent()
        
    def _translate_like_user(self, text: str, example_user_message: str) -> str:
            """
        Use Groq to translate `text` into the same language that
        `example_user_message` is written in.
        """
            if not text.strip():
                return text

            try:
                response = self.client.chat.completions.create(
                    model="openai/gpt-oss-120b",  # or whatever Groq model you're using
                    messages=[
                        {
                        "role": "system",
                        "content": (
                            "You are a translator.\n"
                            "Detect the language of TEXT_B and translate TEXT_A "
                            "into exactly that language.\n"
                            "Return ONLY the translated TEXT_A, nothing else."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"TEXT_A:\n{text}\n\nTEXT_B:\n{example_user_message}",
                    },
                ],
                temperature=0.0,
                max_tokens=800,
            )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[WARN] Translation failed: {e}")
            # Fallback to English if translation fails
                return text

    def _is_affirmative(self, text: str) -> bool:
        return any(word in text for word in ["yes", "yep", "ya", "y", "ys", "yeah", "ok", "okay", "sure", "correct", "proceed", "accept"])

    def _is_negative(self, text: str) -> bool:
        return any(word in text for word in ["no", "n", "nope", "nah", "negative", "cancel", "stop"])
    
    def _detect_personality(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        if any(word in user_lower for word in ["bro", "dude", "yo", "wtf", "shit"]):
            return "casual"
        elif any(word in user_lower for word in ["kindly", "please", "inquire", "regards", "formal"]):
            return "formal"
        elif any(word in user_lower for word in ["help", "sad", "disappointed", "frustrated", "sorry", "confused"]):
            return "empathetic"
        
        return self.state["user_personality"]

    def _get_personality_prompt(self, personality: str) -> str:
        """Get system prompt instructions for a given personality, including negotiation and collateral logic."""
        
        base_prompts = {
            "casual": """
- **Your Vibe:** Be super casual, friendly, and use simple language (like 'bro', 'cool', 'no problem', 'let's figure this out').
- **Negotiation:** You're a persuasive negotiator. If the user hesitates on EMI, suggest a longer tenure (e.g., "we can stretch it to 6 years") or a slightly smaller loan to fit their budget. Your goal is to find a "yes".
- **Collateral (Value-Add):** {COLLATERAL_ADVICE}
            """,
            "formal": """
- **Your Vibe:** Be professional, polite, and use formal language. Avoid slang.
- **Negotiation:** You are a skilled advisor. Your goal is to secure the customer's business. If they express concern about the EMI, proactively offer to model alternative scenarios. "We could explore extending the tenure to 72 months to reduce the monthly obligation, or alternatively, we could assess a slightly revised principal amount."
- **Collateral (Value-Add):** {COLLATERAL_ADVICE}
            """,
            "empathetic": """
- **Your Vibe:** Be very understanding, patient, and reassuring ("I understand this is a big decision", "Don't worry, we can find a solution that works for you").
- **Negotiation:** Be a problem-solver. If the user is worried ("That EMI is high"), be reassuring. "I completely understand that concern. The good news is we have flexibility. We could look at a longer 6-year term to lower the payment, or maybe a slightly smaller loan of (Loan Amount * 0.9) would feel more comfortable. What works best for you?"
- **Collateral (Value-Add):** {COLLATERAL_ADVICE}
            """,
            "friendly": """
- **Your Vibe:** Be warm, friendly, conversational, and enthusiastic (💰 🎉 👍).
- **Negotiation:** Be a helpful partner. Your goal is to get them a loan they're happy with. If they hesitate, jump in. "No problem! If that EMI feels a bit high, we can absolutely adjust. We could either extend the tenure to 6 or 7 years to lower the monthly payment, or we could look at a smaller amount. What do you think?"
- **Collateral (Value-Add):** {COLLATERAL_ADVICE}
            """
        }
        
        base_prompt = base_prompts.get(personality, base_prompts["friendly"])
        
        # --- Collateral Math Logic ---
        collateral_advice = ""
        collateral_info = None
        if self.state.get("customer_data"):
             collateral_str = self.state["customer_data"].get("collateral", "None")
             collateral_info = self.secured_loan_agent.parse_collateral(collateral_str)

        if collateral_info and collateral_info.get("value", 0) > 0 and collateral_info.get("type") == "property":
            # Use 3.5% annual rental yield, divided by 12 for monthly
            monthly_rent = (collateral_info["value"] * 0.035) / 12
            collateral_advice = f"Just a pro-tip! I noticed you have a property listed. You could be earning **₹{monthly_rent:,.0f} a month** just by renting it out! That's a fantastic extra income stream. Something to think about!"
        
        return base_prompt.replace("{COLLATERAL_ADVICE}", collateral_advice)
    
    def start_conversation(self, customer_phone: str = None):
        print("=" * 80)
        print("🏦 TATA CAPITAL - Personal Loan Assistant")
        print("=" * 80)
        
        welcome_msg = """Hello! 👋 Welcome to Tata Capital.
I'm your personal loan assistant, and I'm here to help you get the best loan offer tailored to your needs.
May I have your phone number to get started?"""
        
        print(f"\n🤖 Assistant: {welcome_msg}\n")
        self.conversation_history.append({"role": "assistant", "content": welcome_msg})
        return welcome_msg
    
    def process_message(self, user_message: str) -> str:
        """
    1. If needed, translate user's message -> English (for rules & heuristics).
    2. Run state machine.
    3. Translate our English reply -> user's selected language.
    """

    # 1) Normalize incoming to English for internal logic
        if self.user_language != "en":
            try:
                normalized_message = GoogleTranslator(
                    source=self.user_language,
                target="en"
            ).translate(user_message)
            except Exception:
                normalized_message = user_message
        else:
            normalized_message = user_message

    # Store ENGLISH version in history so LLM context is clean
        self.conversation_history.append({
        "role": "user",
        "content": normalized_message,
    })

    # Personality detection on normalized English text
        self.state["user_personality"] = self._detect_personality(
        normalized_message.lower()
    )

    # 🔹 SPECIAL CASE: Needs Assessment uses SalesAgent, which already
    # does its own translation in/out. So we let it handle language and
    # just return its reply directly.
        if self.state["stage"] == "needs_assessment":
            return self._handle_needs_assessment(user_message)

    # 2) All other stages use our ENGLISH normalized text
        if self.state["stage"] == "initial":
            response = self._handle_initial_stage(normalized_message)
        elif self.state["stage"] == "new_customer_onboarding":
            response = self._handle_new_customer_onboarding(normalized_message)
        elif self.state["stage"] == "verification":
            response = self._handle_verification(normalized_message)
        elif self.state["stage"] == "credit_check":
            response = self._handle_credit_check(normalized_message)
        elif self.state["stage"] == "underwriting":
            response = self._handle_underwriting(normalized_message)
        elif self.state["stage"] == "document_upload":
            response = self._handle_document_upload(normalized_message)
        elif self.state["stage"] == "secured_loan":
            response = self._handle_secured_loan_flow(normalized_message)
        elif self.state["stage"] == "approval":
            response = self._handle_approval(normalized_message)
        elif self.state["stage"] == "rejection":
            response = self._handle_rejection(normalized_message)
        elif self.state["stage"] == "completed":
            response = "Our conversation has ended. If you'd like to start over, please type 'restart'."
        else:
            response = "I'm sorry, something went wrong. Let me restart our conversation."

    # 3) Translate response back to user's language (except English)
        if self.user_language != "en":
            try:
                translated_response = GoogleTranslator(
                source="en",
                target=self.user_language
            ).translate(response)
                return translated_response
            except Exception:
            # if translation fails, at least return English
                return response

    # English case
        return response


    
    def _handle_initial_stage(self, user_message: str) -> str:
        phone = ''.join(filter(str.isdigit, user_message))
        
        if len(phone) >= 10:
            customer_data = get_customer_data(phone[-10:])
            
            if customer_data:
                self.state["temp_customer_data"] = customer_data
                self.state["awaiting_profile_permission"] = True
                self.state["stage"] = "verification"
                
                response = f"""Thank you! I found an existing profile linked to this number.\n\nMay I access your profile information to provide you with personalized loan offers?\n\nPlease reply with 'Yes' or 'No'."""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                # --- NEW USER FLOW ---
                self.state["awaiting_manual_data_entry"] = True
                self.state["manual_data_step"] = 1
                self.state["temp_customer_data"] = {"phone": phone[-10:]} # Save the phone
                self.state["stage"] = "new_customer_onboarding"
                
                response = """I couldn't find your profile in our system. No worries! Let me collect your details.

What is your full name?"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        else:
            response = "I didn't catch a valid phone number. Could you please provide your 10-digit mobile number?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    # --- NEW FUNCTION FOR NEW USERS ---
    def _handle_new_customer_onboarding(self, user_message: str) -> str:
        """Complete manual data entry flow WITH COLLATERAL COLLECTION"""
        if not self.state.get("awaiting_manual_data_entry"):
            response = "Thank you for providing your details. Currently, our automated system is optimized for existing customers. Please contact our support team to continue your application."
            self.state["stage"] = "completed"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        step = self.state["manual_data_step"]
        
        if step == 1: # Was asking for name
            self.state["temp_customer_data"]["name"] = user_message.strip()
            self.state["manual_data_step"] = 2
            response = "Great! What is your city?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        elif step == 2: # Was asking for city
            self.state["temp_customer_data"]["city"] = user_message.strip()
            self.state["manual_data_step"] = 3
            response = "Perfect! What is your complete address?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        elif step == 3: # Was asking for address
            self.state["temp_customer_data"]["address"] = user_message.strip()
            self.state["manual_data_step"] = 4
            response = "Thank you! What is your monthly income (in rupees)?"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        elif step == 4: # Was asking for income
            income_match = re.search(r'(\d+)', user_message.replace(',', ''))
            if income_match:
                monthly_income = int(income_match.group(1))
                self.state["temp_customer_data"]["monthly_income"] = monthly_income
                # Give a default pre-approved limit based on income
                self.state["temp_customer_data"]["pre_approved_limit"] = min(monthly_income * 10, 500000)
                
                self.state["manual_data_step"] = 5
                response = """Great! One last question:

Do you have any collateral that you'd like to use for a secured loan? This could be:
🏠 Property (house, flat, shop)
🚗 Vehicle (car, bike)
🪙 Gold/Jewelry
💰 Fixed Deposits
📈 Stocks/Mutual Funds

Please provide details like:
"Residential Property - 2BHK (Estimated Value: ₹45,00,000)"
or
"Vehicle - Honda City 2019 (Value: ₹6,50,000)"

(Or simply type "none" if you don't have collateral)"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                response = "I didn't catch a valid income amount. Please provide your monthly income in rupees (e.g., 50000):"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        elif step == 5: # Was asking for collateral
            user_lower = user_message.lower().strip()
            
            if user_lower in ["none", "no", "nothing", "don't have", "nope", "nahi", "nil"]:
                collateral_value = "None"
            else:
                collateral_value = user_message.strip()
            
            # Create the full customer profile
            self.state["temp_customer_data"].update({
                "email": f"{self.state['temp_customer_data']['name'].lower().replace(' ', '.')}@email.com",
                "credit_score": 750,  # Assign a default score for new users
                "employment": "Salaried",
                "company": "N/A",
                "current_loans": "None",
                "collateral": collateral_value,
                "id": f"C{100 + hash(self.state['temp_customer_data']['phone']) % 100:02d}", # Create a temp ID
                "age": 30 # Assign a default age
            })
            
            # --- RUN XGBOOST MODEL FOR NEW USER ---
            risk_result = self.risk_agent.get_safety_score(self.state["temp_customer_data"])
            self.state["temp_customer_data"]["internal_safety_score"] = risk_result["safety_score"]
            # ---
            
            self.state["customer_data"] = self.state["temp_customer_data"]
            self.state["awaiting_manual_data_entry"] = False
            self.state["stage"] = "needs_assessment"
            
            pre_approved_limit = self.state['customer_data']['pre_approved_limit']
            
            if collateral_value != "None":
                collateral_info = self.secured_loan_agent.parse_collateral(collateral_value)
                
                if collateral_info:
                    response = f"""Perfect! Thank you for providing your details, {self.state['customer_data']['name']}! ✨

📊 **Your Profile Summary:**
- Monthly Income: ₹{self.state['temp_customer_data']['monthly_income']:,}
- Unsecured Limit: ₹{pre_approved_limit:,}
- Collateral: {collateral_info['description']} (Value: ₹{collateral_info['value']:,})
- Internal Safety Score: {self.state['customer_data']['internal_safety_score']:.0%}

🎉 **Great news!** With your collateral, you have two options:
- Unsecured Loan: Up to ₹{pre_approved_limit:,}
- **Secured Loan: Up to ₹{collateral_info['max_loan']:,}** at just {collateral_info['interest_rate']}% interest! 🔥

Now, let's discuss your loan needs:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
                else:
                    response = f"""Perfect! Thank you, {self.state['customer_data']['name']}!

Based on your income (₹{self.state['temp_customer_data']['monthly_income']:,}) and an internal safety score of {self.state['customer_data']['internal_safety_score']:.0%}, you're eligible for a pre-approved loan of up to ₹{pre_approved_limit:,}! 🎉

Before we proceed, could you tell me:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
            else:
                response = f"""Perfect! Thank you, {self.state['customer_data']['name']}!

Based on your income (₹{self.state['temp_customer_data']['monthly_income']:,}) and an internal safety score of {self.state['customer_data']['internal_safety_score']:.0%}, you're eligible for a pre-approved loan of up to ₹{pre_approved_limit:,}! 🎉

Before we proceed, could you tell me:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        return "Something went wrong. Please type 'restart' to begin again."
    
    def _handle_needs_assessment(self, user_message: str) -> str:
        # Get the full personality prompt with math/negotiation logic
        personality_instructions = self._get_personality_prompt(self.state["user_personality"])
        
        sales_response = self.sales_agent.negotiate_loan(
            user_message,
            self.state["customer_data"],
            self.conversation_history,
            self.state["loan_request"],
            personality_instructions  # Pass the full prompt, not just the name
        )
        
        self.state["loan_request"] = sales_response.get("loan_details", self.state["loan_request"])
        
        if sales_response.get("ready_for_next_stage"):
            self.state["stage"] = "verification"
            
            verification_msg = f"""Perfect! Let me summarize:
- Loan Amount: ₹{self.state['loan_request']['amount']:,}
- Purpose: {self.state['loan_request']['purpose'].replace('_', ' ').title()}
- Tenure: {self.state['loan_request']['tenure']} months ({self.state['loan_request']['tenure']//12} years)
- Interest Rate: {self.state['loan_request']['interest_rate']}% p.a.
- Monthly EMI: ₹{self.state['loan_request']['emi']:,}

Now, for security purposes, I need to verify your details. Let me confirm:
- Name: {self.state['customer_data']['name']}
- Phone: {self.state['customer_data']['phone']}
- Address: {self.state['customer_data']['address']}

Is this information correct? (Yes/No)"""
            
            localized_msg = self._translate_like_user(verification_msg, user_message)

            self.conversation_history.append({
                "role": "assistant",
                "content": localized_msg,
            })
            return localized_msg

        else:
            response = sales_response["message"]
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _handle_verification(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        # --- NEW: Handle detail correction flow ---
        if self.state.get("awaiting_detail_correction"):
            updated_data = {}
            
            # Simple parser for "key: value"
            if "name" in user_lower:
                name_match = re.search(r'name[:\s]+([a-zA-Z\s]+)', user_message, re.IGNORECASE)
                if name_match:
                    updated_data["name"] = name_match.group(1).strip()
            
            phone_match = re.search(r'(\d{10})', user_message)
            if phone_match:
                updated_data["phone"] = phone_match.group(1)
            
            if "address" in user_lower:
                address_match = re.search(r'address[:\s]+(.+)', user_message, re.IGNORECASE | re.DOTALL)
                if address_match:
                    updated_data["address"] = address_match.group(1).strip()
            
            # If no keys, assume they just sent the address
            if not updated_data and len(user_message) > 10:
                updated_data["address"] = user_message.strip()
            
            self.state["customer_data"].update(updated_data)
            
            self.state["awaiting_detail_correction"] = False
            self.state["stage"] = "needs_assessment" # Go back to needs assessment
            
            response = f"""✅ Thank you! Your details have been updated:
- Name: {self.state['customer_data']['name']}
- Phone: {self.state['customer_data']['phone']}
- Address: {self.state['customer_data']['address']}

Now, let's continue with your loan application. Could you tell me:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        if self.state.get("awaiting_profile_permission"):
            
            if self._is_affirmative(user_lower):
                customer_data = self.state["temp_customer_data"]
                
                # --- RUN XGBOOST/RISK AGENT ---
                risk_result = self.risk_agent.get_safety_score(customer_data)
                customer_data["internal_safety_score"] = risk_result["safety_score"]
                # ---
                
                self.state["customer_data"] = customer_data
                self.state["stage"] = "needs_assessment"
                self.state["awaiting_profile_permission"] = False
                del self.state["temp_customer_data"]
                
                response = f"""Great! I found your profile, {customer_data['name']}.
I see you're based in {customer_data['city']}. Good news - you have a pre-approved personal loan offer of ₹{customer_data['pre_approved_limit']:,}!
(Our internal safety model also gives you a score of {customer_data['internal_safety_score']:.0%})

Before we proceed, could you tell me:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            
            elif self._is_negative(user_lower):
                # --- UPDATED: Divert to manual entry flow ---
                self.state["awaiting_profile_permission"] = False
                self.state["awaiting_manual_data_entry"] = True
                self.state["manual_data_step"] = 1
                self.state["stage"] = "new_customer_onboarding"
                
                phone = self.state["temp_customer_data"]["phone"]
                self.state["temp_customer_data"] = {"phone": phone} # Keep phone, clear rest

                response = """No problem! I understand you'd prefer to provide your details manually.

Let's start fresh. What is your full name?"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                response = "Please respond with 'Yes' to allow me to access your profile, or 'No' to provide details manually."
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        if any(word in user_lower for word in ["change", "update", "lacs", "thousand", "amount", "tenure", "go back", "revert"]):
            self.state["stage"] = "needs_assessment"
            response = "Okay, let's update your loan details. "
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + self._handle_needs_assessment(user_message)
        
        if self._is_affirmative(user_lower):
            self.state["verification_status"] = True
            self.state["stage"] = "credit_check"
            kyc_result = self.verification_agent.verify_customer(self.state["customer_data"])
            
            if kyc_result["verified"]:
                response = "Thank you for confirming. Now, let me quickly check your credit profile..."
                self.conversation_history.append({"role": "assistant", "content": response})
                return response + "\n\n" + self._handle_credit_check("")
            else:
                self.state["stage"] = "rejection"
                response = "I'm sorry, I couldn't verify your KYC details at this time. Please contact our support team."
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
                
        elif self._is_negative(user_lower):
            # --- NEW: Set flag to wait for correction ---
            self.state["awaiting_detail_correction"] = True
            response = """No problem! Let's update your details. Please provide your correct information in this format:

Name: Your Full Name
Phone: 1234567890
Address: Your Complete Address

(Or just tell me what needs to be corrected)"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        else:
            response = "Please confirm if your details are correct by typing 'Yes' or 'No'. (Or say 'change loan amount' to go back)."
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _handle_credit_check(self, user_message: str) -> str:
        credit_result = self.credit_agent.get_credit_score(
            self.state["customer_data"]["phone"]
        )
        self.state["credit_score"] = credit_result["score"]
        
        if credit_result["score"] < 700:
            self.state["stage"] = "rejection"
            
            # --- UPDATED: Check for collateral BEFORE sending response ---
            collateral_info = self.secured_loan_agent.parse_collateral(
                self.state["customer_data"].get("collateral", "None")
            )
            
            if collateral_info:
                response = f"""I've reviewed your credit profile carefully.
{self.state["customer_data"]["name"]}, your credit score is currently {credit_result['score']}/900. Our minimum requirement is 700 for instant unsecured loan approval.

But here's the good news - you have collateral! 🎉

**Your Collateral:** {collateral_info['description']}
**Collateral Value:** ₹{collateral_info['value']:,}
**Maximum Loan Available:** ₹{collateral_info['max_loan']:,} at {collateral_info['interest_rate']}% p.a.

**Quick Options:**
1. 🏠 **Secured Loan** - Up to ₹{collateral_info['max_loan']:,} (say "secured loan" or "option 1")
2. ✅ **Pre-approved Amount** - ₹{self.state['customer_data']['pre_approved_limit']:,} (say "yes" or "option 2")
3. 💬 **Credit counseling** - Free advice (say "counseling" or "option 3")

What would you like to explore?"""
            else:
                response = f"""I've reviewed your credit profile carefully.
{self.state["customer_data"]["name"]}, your credit score is currently {credit_result['score']}/900. Unfortunately, our minimum requirement is 700 for instant approval.
But here's the good news - you're only {700 - credit_result['score']} points away! 
**Quick Options:**
1. ✅ Take your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,} (say "yes" or "option 1")
2. 💬 Free credit counseling (say "counseling" or "option 2")
What would you like to do?"""
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        else:
            self.state["stage"] = "underwriting"
            response = f"""Excellent news! Your credit score of {credit_result['score']}/900 is strong! ✅
Let me now evaluate your loan eligibility..."""
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
            response = f"""🎉 Congratulations! Your loan has been APPROVED!
Loan Details:
- Amount: ₹{self.state['loan_request']['amount']:,}
- Tenure: {self.state['loan_request']['tenure']} months
- Interest Rate: {self.state['loan_request']['interest_rate']}% p.a.
- Monthly EMI: ₹{self.state['loan_request']['emi']:,}
Let me generate your sanction letter right away..."""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n\n" + self._generate_sanction_letter()
        
        elif underwriting_result["decision"] == "REQUIRES_SALARY_SLIP":
            self.state["stage"] = "document_upload"
            response = f"""Your loan amount (₹{self.state['loan_request']['amount']:,}) is {underwriting_result['ratio']:.1f}x your pre-approved limit.
We need to verify your income for approval.
📄 **Please upload your latest salary slip.**
Type 'upload' to auto-fetch from database, or type 'manual upload' to upload your own file."""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        else:  # REJECTED
            self.state["stage"] = "rejection"
            
            # --- UPDATED: Check for collateral BEFORE sending response ---
            collateral_info = self.secured_loan_agent.parse_collateral(
                self.state["customer_data"].get("collateral", "None")
            )
            
            if collateral_info and collateral_info['max_loan'] >= self.state['loan_request']['amount']:
                response = f"""I've carefully reviewed your application.
The requested amount (₹{self.state['loan_request']['amount']:,}) exceeds our unsecured loan limit.

**But great news!** You have eligible collateral that can get you this amount! 🎉

**Your Collateral:** {collateral_info['description']}
**Collateral Value:** ₹{collateral_info['value']:,}
**Maximum Secured Loan:** ₹{collateral_info['max_loan']:,} at {collateral_info['interest_rate']}% p.a.

**Options:**
1. 🏠 **Apply for secured loan** - Get ₹{self.state['loan_request']['amount']:,} (say "secured loan" or "option 1")
2. ✅ **Take pre-approved amount** - ₹{self.state['customer_data']['pre_approved_limit']:,} (say "yes" or "option 2")

What would you prefer?"""
            else:
                response = f"""I've carefully reviewed your application.
The requested amount (₹{self.state['loan_request']['amount']:,}) exceeds our maximum approval limit.
However, you're pre-approved for ₹{self.state['customer_data']['pre_approved_limit']:,}. 
Would you like to proceed with this amount? (Yes/No)"""
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _handle_document_upload(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        # --- NEW: Allow user to switch to secured loan ---
        if any(word in user_lower for word in ["secured", "collateral", "option"]):
            return self._handle_rejection(user_message)
        
        if self.state.get("waiting_for_manual_upload"):
            if "done" in user_lower:
                self.state["waiting_for_manual_upload"] = False
                upload_result = self.upload_agent.process_upload(self.state["customer_data"]["name"])
                
                if upload_result["success"]:
                    return self._process_salary_verification(upload_result["file_path"])
                else:
                    response = f"""I still can't find the file. Please make sure:
1. File is named: SalarySlip_{self.state['customer_data']['name'].replace(' ', '_')}.pdf
2. File is in the 'salary_slips' folder
Type 'done' once ready, or 'skip' to see other options."""
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response
            
            elif "skip" in user_lower:
                self.state["waiting_for_manual_upload"] = False
                return self._show_skip_options()
            
            else:
                response = """Please type 'done' once you've uploaded the file, or 'skip' to see other options."""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        if "manual" in user_lower and "upload" in user_lower:
            response = f"""📤 **Manual Upload Process:**
1. **Save your salary slip** as a PDF file
2. **Name it**: SalarySlip_{self.state['customer_data']['name'].replace(' ', '_')}.pdf
3. **Place it** in the 'salary_slips' folder in the project directory
4. **Type 'done'** once uploaded"""
            self.conversation_history.append({"role": "assistant", "content": response})
            self.state["waiting_for_manual_upload"] = True
            return response
        
        elif "upload" in user_lower or "auto" in user_lower:
            upload_result = self.upload_agent.process_upload(self.state["customer_data"]["name"])
            
            if upload_result["success"]:
                return self._process_salary_verification(upload_result["file_path"])
            else:
                response = f"""I couldn't find your salary slip in our database.
Would you like to:
1. **Upload manually** (type 'manual upload')
2. **Skip** and see other options (type 'skip')"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        elif "skip" in user_lower:
            return self._show_skip_options()
        
        else:
            response = """I need your salary slip to proceed. Please choose:
- Type **'upload'** → I'll check our database
- Type **'manual upload'** → Upload your own file
- Type **'skip'** → See other options"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _process_salary_verification(self, file_path: str) -> str:
        doc_result = self.document_agent.extract_salary_info(file_path)
        
        monthly_emi = self.state["loan_request"]["emi"]
        monthly_salary = doc_result["basic_salary"] + doc_result["hra"] + doc_result["other_allowances"]
        
        if monthly_salary == 0:
             self.state["stage"] = "rejection"
             response = "I'm sorry, I was unable to read the salary from the document. Please contact support."
             self.conversation_history.append({"role": "assistant", "content": response})
             return response
        
        emi_ratio = (monthly_emi / monthly_salary) * 100
        
        if emi_ratio <= 50:
            self.state["stage"] = "approval"
            response = f"""✅ Salary slip verified successfully!
Your monthly income: ₹{monthly_salary:,}
EMI-to-Income ratio: {emi_ratio:.1f}% (Well within our 50% limit)
🎉 Your loan of ₹{self.state['loan_request']['amount']:,} is APPROVED!
Generating your sanction letter..."""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n\n" + self._generate_sanction_letter()
        else:
            self.state["stage"] = "rejection"
            response = f"""Thank you for uploading your salary slip.
After review, your EMI (₹{monthly_emi:,}) would be {emi_ratio:.1f}% of your income (₹{monthly_salary:,}/month).
Our policy requires EMI ≤ 50% of income.
Would you like to accept your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _show_skip_options(self) -> str:
        self.state["stage"] = "rejection"
        self.state["waiting_for_manual_upload"] = False
        
        collateral_info = self.secured_loan_agent.parse_collateral(
            self.state["customer_data"].get("collateral", "None")
        )
        
        if collateral_info:
            response = f"""No problem! Let's look at alternatives:
1. 🏠 **Secured Loan** (using your {collateral_info['type'].title()}) - Up to ₹{collateral_info['max_loan']:,} at {collateral_info['interest_rate']}% (say "secured loan")
2. ✅ **Accept ₹{self.state['customer_data']['pre_approved_limit']:,}** (instant approval - say "yes")
3. 💬 **Credit counseling** (free advice - say "counseling")
What would you prefer?"""
        else:
            response = f"""No problem! Let's look at alternatives:
1. **Accept ₹{self.state['customer_data']['pre_approved_limit']:,}** (instant approval - say "yes")
2. **Credit counseling** (free advice - say "counseling")
What would you prefer?"""
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    # --- NEW FUNCTION TO HANDLE SECURED LOAN FLOW ---
    def _handle_secured_loan_flow(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        if self.state.get("awaiting_secured_loan_application"):
            
            # Allow user to go back
            if self._is_negative(user_lower) or "back" in user_lower or "cancel" in user_lower:
                self.state["awaiting_secured_loan_application"] = False
                self.state["stage"] = "rejection"
                response = "Okay, cancelling the secured loan application. What would you like to do instead?"
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            
            # Check for affirmative to max amount
            if self._is_affirmative(user_lower):
                 requested_amount = self.state["secured_loan_offer"]["max_amount"]
            else:
                # Try to parse a new amount
                amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)', user_lower)
                if amount_match:
                    requested_amount = int(float(amount_match.group(1)) * 100000)
                else:
                    numbers = re.findall(r'\d+', user_message.replace(',', ''))
                    if numbers:
                        num = int(numbers[0])
                        if num < 1000: # e.g., user types "5" for 5 lakh
                            requested_amount = num * 100000
                        else:
                            requested_amount = num
                    else:
                        requested_amount = None
            
            if requested_amount:
                secured_offer = self.state["secured_loan_offer"]
                
                if requested_amount <= secured_offer["max_amount"]:
                    tenure = self.state["loan_request"].get("tenure", 60) # Default to 5 years
                    interest_rate = secured_offer["interest_rate"]
                    monthly_rate = interest_rate / (12 * 100)
                    
                    if (1 + monthly_rate)**tenure - 1 == 0:
                        emi = int(requested_amount / tenure)
                    else:
                        emi = int(
                            (requested_amount * monthly_rate * (1 + monthly_rate)**tenure) /
                            ((1 + monthly_rate)**tenure - 1)
                        )
                    
                    self.state["loan_request"]["amount"] = requested_amount
                    self.state["loan_request"]["interest_rate"] = interest_rate
                    self.state["loan_request"]["emi"] = emi
                    self.state["loan_request"]["loan_type"] = "secured" # Mark as secured
                    self.state["loan_request"]["collateral"] = secured_offer["collateral"]["description"]
                    
                    self.state["stage"] = "approval"
                    self.state["final_decision"] = "APPROVED_SECURED"
                    self.state["awaiting_secured_loan_application"] = False
                    
                    response = f"""🎉 Excellent! Your **Secured Loan** has been APPROVED!

**Loan Details:**
- Amount: ₹{requested_amount:,}
- Collateral: {secured_offer['collateral']['description']}
- LTV: {secured_offer['collateral']['ltv_ratio']:.0f}%
- Interest Rate: {interest_rate}% p.a.
- Tenure: {tenure} months ({tenure//12} years)
- Monthly EMI: ₹{emi:,}
- Processing Fee: {secured_offer['processing_fee']}

Generating your sanction letter..."""
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response + "\n\n" + self._generate_sanction_letter()
                else:
                    response = f"""The amount you requested (₹{requested_amount:,}) exceeds your maximum eligible secured loan (₹{secured_offer['max_amount']:,}).

Would you like to take the maximum amount of ₹{secured_offer['max_amount']:,}? (Yes/No)"""
                    self.conversation_history.append({"role": "assistant", "content": response})
                    return response
            else:
                response = f"""I didn't catch the amount. How much would you like to borrow?
(Maximum: ₹{self.state['secured_loan_offer']['max_amount']:,})"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        response = "I didn't catch that. Could you clarify your request?"
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def _generate_sanction_letter(self) -> str:
        from utils.pdf_generator import generate_sanction_letter
        
        pdf_path = generate_sanction_letter(
            customer_data=self.state["customer_data"],
            loan_details=self.state["loan_request"]
        )
        user_id = self.state["customer_data"].get("email") or self.state["customer_data"].get("phone")
        if user_id:
            app_record = {
            "id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "status": "APPROVED",
            "amount": self.state["loan_request"]["amount"],
            "tenure": self.state["loan_request"]["tenure"],
            "emi": self.state["loan_request"]["emi"],
            "purpose": self.state["loan_request"].get("purpose"),
            "sanction_letter_path": pdf_path,
        }
            add_application(user_id, app_record)
        response = f"""✅ Sanction Letter Generated Successfully!
📄 Your sanction letter: {pdf_path}
Opening PDF now...
Next Steps:
1. Review the sanction letter
2. Our team will contact you within 24 hours
3. Loan disbursement in 2-3 business days
Thank you for choosing Tata Capital!"""
        
        try:
            open_pdf(pdf_path)
        except:
            pass
        
        self.conversation_history.append({"role": "assistant", "content": response})
        self.state["final_decision"] = "APPROVED"
        return response
    
    def _handle_approval(self, user_message: str) -> str:
        
        # --- FIX: Check for new loan request ---
        user_lower = user_message.lower()
        if any(word in user_lower for word in ["new loan", "one more", "another loan", "i need", "borrow", "lacs", "startup"]):
            response = f"""I'm happy to help with a new loan! 
            
To start a fresh application, please type **'restart'**.

This chat is for your just-approved loan of ₹{self.state['loan_request']['amount']:,}. Do you have any questions about *this* loan?"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        # --- END FIX ---
            
        if not user_message or user_message.isspace():
            response = "Thank you for choosing Tata Capital! Have a great day! 👋"
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        try:
            personality_prompt = self._get_personality_prompt(self.state["user_personality"])
            
            system_prompt = f"""You are a friendly loan advisor at Tata Capital. 
            
YOUR PERSONALITY:
{personality_prompt}

The customer {self.state['customer_data']['name']} has been APPROVED for their loan! 🎉

APPROVED LOAN DETAILS:
- Amount: ₹{self.state['loan_request']['amount']:,}
- EMI: ₹{self.state['loan_request']['emi']:,}/month
- Tenure: {self.state['loan_request']['tenure']} months
- Purpose: {self.state['loan_request']['purpose']}

YOUR ROLE:
- Answer ANY questions they have naturally and helpfully, matching YOUR PERSONALITY.
- **CRITICAL: This conversation is ONLY about the loan that was just approved.**
- **DO NOT, under any circumstances, discuss a new loan, new amounts, or new applications.**
- If the user asks for a new loan (e.g., "I need one more loan", "I need 4 lacs"), you MUST respond *only* with: "I'm happy to help with a new loan! To start a fresh application, please type **'restart'**."

COMMON QUESTIONS & ANSWERS:
- Timeline: "Disbursement in 2-3 business days after documentation"
- Documents: "Our team will send you a list within 24 hours. Typically: PAN, Aadhaar, bank statements"
- EMI payments: "You'll receive payment schedule via email. Auto-debit available"
"""

            messages = [{"role": "system", "content": system_prompt}]
            for msg in self.conversation_history[-6:]:
                if msg["role"] in ["user", "assistant"]:
                    messages.append(msg)
            
            response = self.client.chat.completions.create(
                model=self.sales_agent.model,
                messages=messages,
                temperature=0.9,
                max_tokens=250
            )
            helpful_response = response.choices[0].message.content.strip()
            self.conversation_history.append({"role": "assistant", "content": helpful_response})
            return helpful_response
            
        except Exception as e:
            print(f"Error in approval handler: {e}")
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ["when", "timeline", "how long", "disburse"]):
                response = """Your loan will be disbursed within 2-3 business days after final documentation.
You'll receive confirmation email, payment schedule, and SMS alerts.
Anything else I can help with?"""
            elif any(word in user_lower for word in ["thank", "great", "perfect", "awesome", "cool"]):
                response = f"""You're very welcome, {self.state['customer_data']['name']}! 🎉
We're excited to have you as a Tata Capital customer. 
Is there anything else you'd like to know about your loan?"""
            else:
                response = f"""Your loan of ₹{self.state['loan_request']['amount']:,} is approved! 
If you have any specific questions, feel free to ask."""
            
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
    
    def _handle_rejection(self, user_message: str) -> str:
        user_lower = user_message.lower()
        
        # --- NEGOTIATION LOOP: Check for "try that" ---
        # This now also checks that there isn't collateral, or that the user said "option 1"
        if "try that" in user_lower or ("option 1" in user_lower and not self.secured_loan_agent.parse_collateral(self.state["customer_data"].get("collateral", "None"))):
            requested_amount = self.state["loan_request"].get("amount", 0)
            pre_approved_limit = self.state["customer_data"]["pre_approved_limit"]
            
            # Suggest 85% of the requested amount, rounded to nearest 10k, but not less than pre-approved
            suggested_amount = max(pre_approved_limit, int(requested_amount * 0.85 / 10000) * 10000)
            
            if suggested_amount >= requested_amount: # Don't suggest more than they asked
                 suggested_amount = pre_approved_limit

            self.state["loan_request"]["amount"] = suggested_amount
            
            # Rerun underwriting
            self.state["stage"] = "underwriting"
            response = f"Great! Let's try again with ₹{suggested_amount:,}. Re-evaluating your eligibility..."
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + "\n\n" + self._handle_underwriting("")
        
        # --- SECURED LOAN PATH ---
        if any(word in user_lower for word in ["secured", "collateral"]) or ("option 1" in user_lower and self.secured_loan_agent.parse_collateral(self.state["customer_data"].get("collateral", "None"))):
            secured_offer = self.secured_loan_agent.get_secured_loan_offer(self.state["customer_data"])
            
            if secured_offer["eligible"]:
                self.state["secured_loan_offer"] = secured_offer
                self.state["awaiting_secured_loan_application"] = True
                self.state["stage"] = "secured_loan"
                
                collateral = secured_offer["collateral"]
                response = f"""Perfect choice! Let me explain your **Secured Loan** option in detail.

📋 **Your Collateral Details:**
- Type: {collateral['type'].upper()}
- Description: {collateral['description']}
- Value: ₹{collateral['value']:,}

💰 **Loan Offer:**
- Maximum Amount: ₹{secured_offer['max_amount']:,}
- Loan-to-Value (LTV): {collateral['ltv_ratio']:.0f}%
- Interest Rate: {secured_offer['interest_rate']}% p.a. (Lower than unsecured!)
- Tenure: {secured_offer['min_tenure']}-{secured_offer['max_tenure']} months
- Processing Fee: {secured_offer['processing_fee']}

✅ **Benefits:**
- Higher loan amount
- Lower interest rate
- Flexible repayment

How much would you like to borrow? (Maximum: ₹{secured_offer['max_amount']:,})"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
            else:
                response = f"""I'm sorry, but you don't have eligible collateral for a secured loan at this time.

Would you like to accept your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")"""
                self.conversation_history.append({"role": "assistant", "content": response})
                return response
        
        # --- REVERT/CHANGE AMOUNT PATH ---
        if any(word in user_lower for word in ["change", "update", "lacs", "thousand", "amount", "tenure", "go back", "revert"]):
            self.state["stage"] = "needs_assessment"
            response = "Okay, let's review your loan request again. "
            self.conversation_history.append({"role": "assistant", "content": response})
            return response + self._handle_needs_assessment(user_message)

        # --- PRE-APPROVED LOAN PATH ---
        if self._is_affirmative(user_lower) or "option 2" in user_lower or "option 3" in user_lower: # "yes" or "option 2/3" (if no collateral)
            return self._process_pre_approved_loan()
        
        # --- COUNSELING PATH ---
        elif any(word in user_lower for word in ["counsel", "credit improvement", "improve", "counseling"]) or ("option 3" in user_lower) or ("option 4" in user_lower):
            response = f"""Great choice! Let me connect you with our credit counselor.
📞 **Free Credit Counseling Session**
Our expert will help you:
1. Review your credit report for errors
2. Create a 6-month improvement plan
You'll receive a call within 24 hours at {self.state['customer_data']['phone']}.
In the meantime, would you like to:
- Accept your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")
- Learn more about secured loans? (Say "secured loan")"""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        # --- OTHER/HELP PATH ---
        elif any(keyword in user_lower for keyword in ["alternative", "what can", "help", "anything", "other", "explore"]):
            return self._send_rejection_options()
        
        elif any(word in user_lower for word in ["fuck", "shit", "wtf", "stupid", "useless", "bro"]):
            response = f"""I'm really sorry for the frustration, {self.state['customer_data']['name']}. I want to help.
Let me make this simple:
Type **"yes"** - I'll instantly approve your ₹{self.state['customer_data']['pre_approved_limit']:,} loan right now."""
            self.conversation_history.append({"role": "assistant", "content": response})
            return response
        
        # --- DEFAULT: RE-PROMPT WITH ALL OPTIONS ---
        else:
            return self._send_rejection_options()
            
    def _process_pre_approved_loan(self) -> str:
        """Helper to process the pre-approved amount"""
        self.state["loan_request"]["amount"] = self.state["customer_data"]["pre_approved_limit"]
        self.state["loan_request"]["purpose"] = self.state["loan_request"].get("purpose", "personal")
        
        interest_rate = 12.5
        tenure = self.state["loan_request"].get("tenure", 24)
        monthly_rate = interest_rate / (12 * 100)
        self.state["loan_request"]["interest_rate"] = interest_rate
        if (1 + monthly_rate)**tenure - 1 == 0:
            emi = int(self.state["loan_request"]["amount"] / tenure)
        else:
            emi = int(
                (self.state["loan_request"]["amount"] * monthly_rate * (1 + monthly_rate)**tenure) /
                ((1 + monthly_rate)**tenure - 1)
            )
        self.state["loan_request"]["emi"] = emi
        
        self.state["stage"] = "approval"
        self.state["final_decision"] = "APPROVED"
        response = f"""Perfect! Let me process your pre-approved loan of ₹{self.state['customer_data']['pre_approved_limit']:,}.
Generating your sanction letter..."""
        self.conversation_history.append({"role": "assistant", "content": response})
        return response + "\n\n" + self._generate_sanction_letter()

    def _send_rejection_options(self) -> str:
        """Helper to send the list of rejection options"""
        collateral_info = self.secured_loan_agent.parse_collateral(
            self.state["customer_data"].get("collateral", "None")
        )
        
        # Propose a new amount
        requested_amount = self.state["loan_request"].get("amount", 0)
        pre_approved_limit = self.state["customer_data"]["pre_approved_limit"]
        
        # Suggest 85% of the requested amount, rounded to nearest 10k, but not less than pre-approved
        suggested_amount = max(pre_approved_limit, int(requested_amount * 0.85 / 10000) * 10000)
        
        if suggested_amount >= requested_amount: # Don't suggest more than they asked
                 suggested_amount = pre_approved_limit
        
        if collateral_info:
            response = f"""I understand this is disappointing, {self.state['customer_data']['name']}.
The amount of ₹{requested_amount:,} couldn't be approved as an unsecured loan.

However, we can try a few other options:
1. **Try a lower amount:** How about we try for **₹{suggested_amount:,}**? (Say "try that" or "option 1")
2. **Secured Loan:** Get up to **₹{collateral_info['max_loan']:,}** using your collateral (Say "secured loan" or "option 2")
3. **Accept Pre-approved:** Get **₹{pre_approved_limit:,}** instantly (Say "yes" or "option 3")
4. **Credit Counseling:** Free advice (Say "counseling" or "option 4")

(Or say "change amount" to enter a different number)"""
        else:
            response = f"""I understand this is disappointing, {self.state['customer_data']['name']}.
The amount of ₹{requested_amount:,} couldn't be approved.

However, we can try a few other options:
1. **Try a lower amount:** How about we try for **₹{suggested_amount:,}**? (Say "try that" or "option 1")
2. **Accept Pre-approved:** Get **₹{pre_approved_limit:,}** instantly (Say "yes" or "option 2")
3. **Credit Counseling:** Free advice (Say "counseling" or "option 3")

(Or say "change amount" to enter a different number)"""
        
        self.conversation_history.append({"role": "assistant", "content": response})
        return response
    
    def _get_rejection_reason(self) -> str:
        if self.state["credit_score"] and self.state["credit_score"] < 700:
            return f"Credit score ({self.state['credit_score']}) below minimum (700)"
        elif self.state["underwriting_result"]:
            return self.state["underwriting_result"].get("reason", "Loan amount exceeds limits")
        else:
            return "Unable to approve at this time"


def main():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("\n" + "="*80 + "\n❌ ERROR: Groq API Key Not Found!\n" + "="*80)
        print("\nPlease add GROQ_API_KEY=gsk_your-key-here to your .env file\n")
        return
    
    print(f"\n✅ Groq API Key loaded: {api_key[:7]}...{api_key[-4:]}\n")
    
    final_prompt_shown = False
    
    try:
        master = MasterAgent(api_key)
        master.start_conversation()
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\n🤖 Assistant: Thank you for visiting Tata Capital. Have a great day! 👋\n")
                    break
                
                if user_input.lower() == 'restart':
                    print("\n" + "=" * 80 + "\n🔄 Restarting conversation...\n" + "=" * 80)
                    master = MasterAgent(api_key)
                    master.start_conversation()
                    final_prompt_shown = False
                    continue
                
                if not user_input:
                    continue
                
                response = master.process_message(user_input)
                print(f"\n🤖 Assistant: {response}\n")
                
                if master.state["stage"] == "completed":
                    print("\n" + "=" * 80 + "\n✅ Conversation completed. Type 'restart' to begin.\n" + "=" * 80)
                    final_prompt_shown = True
                    continue
                
                if master.state["stage"] in ["approval", "rejection"] and master.state["final_decision"] and not final_prompt_shown:
                    final_prompt_shown = True
                    
                    print("\n" + "=" * 80 + "\n✅ Conversation completed.\n" + "=" * 80)
                    
                    continue_chat = input("\nWould you like to ask anything else? (yes/no): ").strip().lower()
                    if not (continue_chat.startswith('y') or continue_chat.startswith('ok')):
                        print("\n🤖 Assistant: Thank you for choosing Tata Capital! Have a great day! 👋\n")
                        break
                    else:
                        print("\n🤖 Assistant: Of course! What would you like to know?\n")
                        continue
                    
            except KeyboardInterrupt:
                print("\n\n🤖 Assistant: Thank you for visiting Tata Capital. Have a great day! 👋\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Let me try to help you again.\n")
                continue
                
    except Exception as e:
        print(f"\n❌ Error initializing chatbot: {e}")
        print("Please check your API key and try again.\n")


if __name__ == "__main__":
    main()