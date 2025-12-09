from openai import OpenAI
from typing import Dict, List, Any, Optional
import json
import re
import os
from dotenv import load_dotenv
from groq import Groq
from deep_translator import GoogleTranslator

class SalesAgent:
    """
    Sales Agent - Worker Agent
    Handles customer needs assessment, loan negotiation, and persuasion
    Uses LLM for natural, human-like conversation
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"
        self.conversation_context = []
        self.user_language = "en"
    
    # Multilingual greetings
        self.greetings = {
        "en": "Hello 👋 I'm Arjun, your personal loan advisor at Tata Capital.\n\nTo get started, could you please share your registered phone number?",
        "hi": "नमस्ते 👋 मैं अर्जुन हूं, टाटा कैपिटल में आपका व्यक्तिगत ऋण सलाहकार।\n\nशुरू करने के लिए, क्या आप कृपया अपना पंजीकृत फोन नंबर साझा कर सकते हैं?",
        "ta": "வணக்கம் 👋 நான் அர்ஜுன், டாடா கேபிடலில் உங்கள் தனிப்பட்ட கடன் ஆலோசகர்.\n\nதொடங்க, உங்கள் பதிவு செய்யப்பட்ட தொலைபேசி எண்ணைப் பகிரவும்?",
        "te": "నమస్కారం 👋 నేను అర్జున్, టాటా క్యాపిటల్‌లో మీ వ్యక్తిగత లోన్ సలహాదారుడు.\n\nప్రారంభించడానికి, దయచేసి మీ నమోదు చేసుకున్న ఫోన్ నంబర్‌ను షేర్ చేయగలరా?",
        "bn": "নমস্কার 👋 আমি অর্জুন, টাটা ক্যাপিটালে আপনার ব্যক্তিগত ঋণ পরামর্শদাতা।\n\nশুরু করতে, আপনি কি আপনার নিবন্ধিত ফোন নম্বর শেয়ার করতে পারেন?",
        "mr": "नमस्कार 👋 मी अर्जुन, टाटा कॅपिटलमधील तुमचा वैयक्तिक कर्ज सल्लागार.\n\nसुरुवात करण्यासाठी, कृपया तुमचा नोंदणीकृत फोन नंबर शेअर करू शकता का?",
        "gu": "નમસ્તે 👋 હું અર્જુન છું, ટાટા કેપિટલમાં તમારો વ્યક્તિગત લોન સલાહકાર.\n\nશરૂ કરવા માટે, શું તમે તમારો નોંધાયેલ ફોન નંબર શેર કરી શકો છો?"
    }

    def set_language(self, language: str):
        """Set the conversation language"""
        self.user_language = language

    def get_initial_greeting(self) -> str:
        """Get greeting in user's language"""
        return self.greetings.get(self.user_language, self.greetings["en"])

    def negotiate_loan(
        self, 
        user_message: str, 
        customer_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        current_loan_details: Dict[str, Any],
        personality_instructions: str
    ) -> Dict[str, Any]:
        """
        Negotiate loan terms with customer using LLM
        """
        if self.user_language != "en":
            try:
                translated_input = GoogleTranslator(source=self.user_language, target='en').translate(user_message)
            except:
                translated_input = user_message
        else:
            translated_input = user_message
    
        all_history = conversation_history + [{"role": "user", "content": translated_input}]
        extracted_details = self._extract_loan_details(all_history)
        
        final_details = current_loan_details.copy()
        final_details.update(extracted_details) 
        
        has_all_info = self._has_complete_info(final_details)
        
        if has_all_info:
            final_details = self._finalize_loan_details(final_details, customer_data)
            mode = "present_emi"
        else:
            mode = "gather_info"

        system_prompt = self._create_system_prompt(
            customer_data, 
            final_details, 
            personality_instructions,
            mode 
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-10:]:
            if msg["role"] in ["user", "assistant"]:
                messages.append(msg)
        
        if not conversation_history or conversation_history[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=800, 
            )
            
            assistant_message = response.choices[0].message.content.strip()
            if self.user_language != "en":
                try:
                    translated_response = GoogleTranslator(source='en', target=self.user_language).translate(assistant_message)
                except:
                    translated_response = assistant_message
            else:
                translated_response = assistant_message
            extraction_match = re.search(r'\[EXTRACTION:amount=(\d+),tenure=(\d+),purpose=([^\]]+)\]', assistant_message)
            if extraction_match:
                final_loan = {
                    "amount": int(extraction_match.group(1)),
                    "tenure": int(extraction_match.group(2)),
                    "purpose": extraction_match.group(3).strip()
                }
                final_loan = self._finalize_loan_details(final_loan, customer_data)
                clean_message = self._clean_message(translated_response)
                
                return {
                    "message": clean_message,
                    "ready_for_next_stage": True,
                    "loan_details": final_loan 
                }

            return {
                "message": self._clean_message(translated_response),
                "ready_for_next_stage": False, 
                "loan_details": final_details
            }
                
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {
                "message": "I'd love to help you with your loan! Could you tell me more about what you're looking for?",
                "ready_for_next_stage": False,
                "loan_details": current_loan_details 
            }
    
    def _create_system_prompt(self, customer_data: Dict[str, Any], current_loan_details: Dict[str, Any], personality_instructions: str, mode: str) -> str:
        """Create a detailed system prompt for the sales agent"""
        
        what_you_have_so_far = f"""
- Loan Amount: {current_loan_details.get('amount', 'Not specified')}
- Loan Tenure: {current_loan_details.get('tenure', 'Not specified')}
- Loan Purpose: {current_loan_details.get('purpose', 'Not specified')}
- **Calculated Interest Rate:** {current_loan_details.get('interest_rate', 'Not specified')}
- **Calculated EMI:** {current_loan_details.get('emi', 'Not specified')}
"""

        base_prompt = f"""You are Arjun, a personal loan advisor at Tata Capital. You're talking to {customer_data['name']}.

CUSTOMER PROFILE:
- Name: {customer_data['name']}
- Pre-approved Limit: ₹{customer_data['pre_approved_limit']:,}
- CIBIL Score: {customer_data['credit_score']}/900
- Internal Safety Score: {customer_data.get('internal_safety_score', 0.5):.0%}
- Monthly Income: ₹{customer_data['monthly_income']:,}
- Collateral: {customer_data.get('collateral', 'None')}

YOUR PERSONALITY & MISSION (Follow these rules!):
{personality_instructions}

WHAT YOU HAVE SO_FAR:
{what_you_have_so_far}
"""

        if mode == "gather_info":
            return base_prompt + f"""
YOUR GOAL:
You are missing one or more pieces of information (Amount, Tenure, or Purpose). Your *only* job is to ask for what's missing.

- If 'Loan Amount' is 'Not specified', ask for it.
- If 'Loan Tenure' is 'Not specified', ask for it.
- If 'Loan Purpose' is 'Not specified', ask for it.

DO NOT mention the EMI. DO NOT use the [EXTRACTION] tag. Just ask for the info.

Now, respond to {customer_data['name']}'s message.
"""

        elif mode == "present_emi":
            # --- THIS IS THE UPDATED PROMPT WITH THE FIX ---
            return base_prompt + f"""
***CRITICAL RULE: THE CONVERSATION FLOW***
You have one job: get the user to agree to an UNSECURED loan EMI.

1.  **PRESENT THE CALCULATED EMI:**
    -   Your system has calculated the EMI. It is in "WHAT YOU HAVE SO_FAR".
    -   Your job is to PRESENT this EMI to the user.
    -   **DO NOT DO THE MATH YOURSELF.** Just present the EMI you were given.
    -   **Example (static):** "Great! For ₹5,00,000 over 3 years, our system calculates an EMI of about **₹16,310** at **10.75%**. How does that sound for your budget?"

2.  **NEGOTIATE (Your Most Important Job!):**
    -   **If the user hesitates** (e.g., "that's too high," "omg", "noooo"):
    -   Your job is to negotiate a *new unsecured term*.
    -   **DO** suggest extending the tenure (e.g., "We can stretch it to 5 years...") or lowering the amount (e.g., "What about we try for 12 lakhs?").
    -   If the user agrees to a *new* unsecured term (e.g., "ok let's try 5 years"), acknowledge it. The system will loop, and you will get a new 'Calculated EMI' to present.
    
    -   **--- NEW RULE (THE FIX) ---**
    -   **If the user asks for a SECURED LOAN** (e.g., "use my bhk apartment," "what about collateral?"):
    -   Your *only* response is to finalize the *current rejected* loan so the next agent can take over.
    -   **Example Response:** "That's a great idea. Using your collateral is definitely the best way to lower your EMI. Let me just finalize this request, and I'll pass you over to our secured loan department.
    [EXTRACTION:amount={current_loan_details.get('amount')},tenure={current_loan_details.get('tenure')},purpose={current_loan_details.get('purpose')}]"
    -   **--- END NEW RULE ---**

3.  **CONFIRM & EXTRACT (Success):**
    -   Only *after* the user has clearly agreed to the *unsecured* terms (e.g., "Yes, that works"), your *next* response is to confirm and *then* use the [EXTRACTION] tag.
    -   **Example (static):** "Perfect! You're all set for the ₹500,000 over 36 months. Let's move to the next step!
    [EXTRACTION:amount=500000,tenure=36,purpose=wedding]"

4.  **CONFIRM & EXTRACT (Failure):**
    -   If the user rejects all your *unsecured* offers (e.g., "no, that's still too high"):
    -   Your *only* response is to finalize the *rejected* loan so the next agent can take over.
    -   **Example (use the real numbers):** "I understand. It looks like we can't get this unsecured amount to work right now. Let me finalize this, and we can look at other options.
    [EXTRACTION:amount={current_loan_details.get('amount')},tenure={current_loan_details.get('tenure')},purpose={current_loan_details.get('purpose')}]"
---

IMPORTANT RULES:
- ALWAYS follow the **CRITICAL RULE** above.
- **NEVER** try to process a secured loan yourself. Your job is to hand it off.
- NEVER use the [EXTRACTION:...] tag until the user has *either* agreed to a final unsecured EMI or *rejected* all your offers.

Now, respond to {customer_data['name']}'s message."""
        
        # Fallback just in case
        return base_prompt + "\n\nHow can I help you today?"

    
    def _extract_loan_details(self, conversation_history: List[Dict]) -> Optional[Dict]:
        """
        Extract loan details from entire conversation using NLP and pattern matching.
        Iterates backwards to find the MOST RECENT user-provided details.
        """
        
        details = {}
        
        if conversation_history and conversation_history[-1]["role"] == "assistant":
            last_msg = conversation_history[-1]["content"]
            extraction_match = re.search(r'\[EXTRACTION:amount=(\d+),tenure=(\d+),purpose=([^\]]+)\]', last_msg)
            if extraction_match:
                details["amount"] = int(extraction_match.group(1))
                details["tenure"] = int(extraction_match.group(2))
                details["purpose"] = extraction_match.group(3).strip()
                return details 

        user_messages_reversed = [msg["content"].lower() for msg in reversed(conversation_history) if msg["role"] == "user"]
        
        amount_found = False
        tenure_found = False
        purpose_found = False
        
        for msg in user_messages_reversed:
            if not amount_found:
                amount = self._extract_amount(msg)
                if amount:
                    details["amount"] = amount
                    amount_found = True
            
            if not tenure_found:
                tenure = self._extract_tenure(msg)
                if tenure:
                    details["tenure"] = tenure
                    tenure_found = True
            
            if not purpose_found:
                purpose = self._extract_purpose(msg) # Check one message at a time
                if purpose:
                    details["purpose"] = purpose
                    purpose_found = True
            
            if amount_found and tenure_found and purpose_found:
                break
        
        if "purpose" not in details:
            all_user_text = " ".join(user_messages_reversed)
            purpose = self._extract_purpose(all_user_text)
            if purpose:
                details["purpose"] = purpose
        
        return details if details else None
    
    def _extract_amount(self, text: str) -> Optional[int]:
        """Extract loan amount from text"""
        lakh_pattern = r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs|lacs|lacksm)'
        lakh_match = re.search(lakh_pattern, text, re.IGNORECASE)
        if lakh_match:
            return int(float(lakh_match.group(1)) * 100000)
        
        crore_pattern = r'(\d+(?:\.\d+)?)\s*(?:crore|crores)'
        crore_match = re.search(crore_pattern, text, re.IGNORECASE)
        if crore_match:
            return int(float(crore_match.group(1)) * 10000000)

        rupee_pattern = r'(?:₹|rs\.?|rupees?)\s*([\d,]+)'
        rupee_match = re.search(rupee_pattern, text, re.IGNORECASE)
        if rupee_match:
            return int(rupee_match.group(1).replace(',', ''))
        
        thousand_pattern = r'(\d+(?:\.\d+)?)\s*(?:thousand|k)'
        thousand_match = re.search(thousand_pattern, text, re.IGNORECASE)
        if thousand_match:
            return int(float(thousand_match.group(1)) * 1000)
        
        number_pattern = r'\b(\d{5,9})\b'
        number_match = re.search(number_pattern, text)
        if number_match:
            if "phone" not in text and "pin" not in text and "code" not in text:
                 return int(number_match.group(1))
        
        return None
    
    def _extract_tenure(self, text: str) -> Optional[int]:
        """Extract loan tenure from text"""
        year_pattern = r'(\d+)\s*(?:years?|yrs?|yearrs)'
        year_match = re.search(year_pattern, text, re.IGNORECASE)
        if year_match:
            return int(year_match.group(1)) * 12
        
        month_pattern = r'(\d+)\s*(?:months?|mon)'
        month_match = re.search(month_pattern, text, re.IGNORECASE)
        if month_match:
            return int(month_match.group(1))
        
        return None
    
    def _extract_purpose(self, text: str) -> Optional[str]:
        """Extract loan purpose from text"""
        # --- FIX: Added "renovate" ---
        purpose_keywords = {
            "business": ["business", "startup", "venture", "company", "expand", "expansion"],
            "wedding": ["wedding", "marriage", "shaadi", "sisterw wedding", "fathere wedding"],
            "medical": ["medical", "health", "hospital", "surgery", "treatment"],
            "education": ["education", "study", "course", "college", "university"],
            "travel": ["travel", "vacation", "holiday", "trip", "recreation"],
            "home_renovation": ["renovate", "renovating", "renovation", "repair", "remodel", "home improvement", "painting"],
            "debt_consolidation": ["debt", "consolidate", "pay off", "credit card"],
            "emergency": ["emergency", "urgent", "immediate"],
            "vehicle": ["car", "bike", "vehicle", "automobile"],
            "personal": ["personal", "general", "use"]
        }
        for purpose, keywords in purpose_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return purpose
        return None # Return None if nothing found
    
    def _has_complete_info(self, loan_details: Dict) -> bool:
        """Check if we have all required information"""
        return all(key in loan_details and loan_details[key] for key in ["amount", "tenure", "purpose"])
    
    def _finalize_loan_details(self, loan_details: Dict, customer_data: Dict) -> Dict:
        """Calculate EMI and finalize loan details"""
        amount = loan_details.get("amount", 0)
        tenure = loan_details.get("tenure", 12) # Default to 12 months if missing
        interest_rate = self._calculate_interest_rate(amount, tenure, customer_data)
        emi = self._calculate_emi(amount, interest_rate, tenure)
        
        return {
            "amount": amount,
            "tenure": tenure,
            "purpose": loan_details.get("purpose", "personal"),
            "interest_rate": interest_rate,
            "emi": emi
        }
    
    def _calculate_interest_rate(self, amount: int, tenure: int, customer_data: Dict) -> float:
        """Calculate interest rate based on multiple factors"""
        base_rate = 11.5
        credit_score = customer_data.get("credit_score", 700)
        
        if credit_score >= 800: base_rate -= 1.0
        elif credit_score >= 750: base_rate -= 0.5
        elif credit_score < 700: base_rate += 1.0
        
        internal_score = customer_data.get('internal_safety_score', 0.5)
        if internal_score >= 0.9: base_rate -= 0.25
        elif internal_score <= 0.3: base_rate += 0.25
            
        if amount <= 200000: base_rate -= 0.5
        elif amount >= 1000000: base_rate += 0.5
        
        # Add penalty for very large unsecured amounts
        if amount > 2000000: base_rate += 1.0
        if amount > 5000000: base_rate += 1.5 # Extra penalty for 99L
        
        if tenure <= 12: base_rate -= 0.5
        elif tenure >= 48: base_rate += 0.5
        
        return round(base_rate, 2)
    
    def _calculate_emi(self, principal: int, annual_rate: float, tenure_months: int) -> int:
        """Calculate EMI using reducing balance method"""
        if tenure_months <= 0: return principal
        monthly_rate = annual_rate / (12 * 100)
        if monthly_rate == 0: return int(principal / tenure_months)
        
        emi = principal * monthly_rate * (1 + monthly_rate)**tenure_months / \
              ((1 + monthly_rate)**tenure_months - 1)
        return int(emi)
    
    def _clean_message(self, message: str) -> str:
        """Remove extraction markers from message"""
        cleaned = re.sub(r'\[EXTRACTION:.*?\]', '', message)
        return cleaned.strip()