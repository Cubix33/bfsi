from typing import Dict, List, Any, Optional
import json
import re
import os
from dotenv import load_dotenv
from groq import Groq

class SalesAgent:
    """
    Sales Agent - Worker Agent
    Handles customer needs assessment, loan negotiation, and persuasion
    Uses LLM for natural, human-like conversation
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        # Using Llama 3 70B for better instruction following regarding formatting
        self.model = "openai/gpt-oss-20b" 
        self.conversation_context = []
        
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
        
        all_history = conversation_history + [{"role": "user", "content": user_message}]
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
                temperature=0.6, # Slightly lower temperature for more stable formatting
                max_tokens=600, 
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            # CRITICAL: Force remove asterisks and emojis if LLM leaks them
            assistant_message = assistant_message.replace('*', '').replace('✨', '').replace('🎉', '')
            
            extraction_match = re.search(r'\[EXTRACTION:amount=(\d+),tenure=(\d+),purpose=([^\]]+)\]', assistant_message)
            if extraction_match:
                final_loan = {
                    "amount": int(extraction_match.group(1)),
                    "tenure": int(extraction_match.group(2)),
                    "purpose": extraction_match.group(3).strip()
                }
                final_loan = self._finalize_loan_details(final_loan, customer_data)
                clean_message = self._clean_message(assistant_message)
                
                return {
                    "message": clean_message,
                    "ready_for_next_stage": True,
                    "loan_details": final_loan 
                }

            return {
                "message": self._clean_message(assistant_message),
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
- Calculated Interest Rate: {current_loan_details.get('interest_rate', 'Not specified')}
- Calculated EMI: {current_loan_details.get('emi', 'Not specified')}
"""

        base_prompt = f"""You are Arjun, a personal loan advisor at Tata Capital. You are talking to {customer_data['name']}.

CUSTOMER PROFILE:
- Name: {customer_data['name']}
- Pre-approved Limit: {customer_data['pre_approved_limit']}
- Monthly Income: {customer_data['monthly_income']}

STRICT FORMATTING RULES:
1. Do NOT use asterisks (*).
2. Do NOT use bolding (**text**).
3. Do NOT use emojis.
4. Keep the tone natural, human, and conversational.

YOUR GOAL:
Gather the Loan Amount, Tenure, and Purpose.

WHAT YOU HAVE SO FAR:
{what_you_have_so_far}
"""

        if mode == "gather_info":
            return base_prompt + f"""
INSTRUCTIONS:
You are missing one or more pieces of information (Amount, Tenure, or Purpose). 
Ask for what is missing in a polite, human way.
Do not mention the EMI yet.
"""

        elif mode == "present_emi":
            return base_prompt + f"""
INSTRUCTIONS:
1. Present the Calculated EMI to the user clearly.
   Example: "For 5 lakhs over 3 years, your EMI comes to about 16,310 at 10.75% interest. Does that fit your budget?"

2. If the user hesitates (says it is too high), suggest extending the tenure.

3. If the user AGREES to the unsecured loan terms, append the extraction tag at the very end of your message:
   [EXTRACTION:amount={current_loan_details.get('amount')},tenure={current_loan_details.get('tenure')},purpose={current_loan_details.get('purpose')}]

4. If the user asks for a SECURED LOAN (collateral), finalize the current request so we can switch departments. Append the extraction tag.
"""
        
        return base_prompt

    
    def _extract_loan_details(self, conversation_history: List[Dict]) -> Optional[Dict]:
        """
        Extract loan details from entire conversation using NLP and pattern matching.
        Iterates backwards to find the MOST RECENT user-provided details.
        """
        
        details = {}
        
        # Check if LLM already extracted it in the last turn
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
                purpose = self._extract_purpose(msg)
                if purpose:
                    details["purpose"] = purpose
                    purpose_found = True
            
            if amount_found and tenure_found and purpose_found:
                break
        
        # Fallback purpose extraction from combined text
        if "purpose" not in details and user_messages_reversed:
            all_user_text = " ".join(user_messages_reversed)
            purpose = self._extract_purpose(all_user_text)
            if purpose:
                details["purpose"] = purpose
        
        return details if details else None
    
    def _extract_amount(self, text: str) -> Optional[int]:
        """Extract loan amount from text"""
        # 1. Lakhs/Lacs
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)', text, re.IGNORECASE)
        if lakh_match:
            return int(float(lakh_match.group(1)) * 100000)
        
        # 2. Crores
        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:crore|cr)', text, re.IGNORECASE)
        if crore_match:
            return int(float(crore_match.group(1)) * 10000000)

        # 3. Thousands (k)
        k_match = re.search(r'(\d+(?:\.\d+)?)\s*k', text, re.IGNORECASE)
        if k_match:
            return int(float(k_match.group(1)) * 1000)

        # 4. Explicit numbers with commas
        # Remove commas and look for large numbers
        clean_text = text.replace(',', '')
        number_match = re.search(r'\b(\d{4,9})\b', clean_text)
        if number_match:
            # Simple filter to avoid confusing phone numbers/years if they appear in isolation
            # (In a real app, this would be more context-aware)
            val = int(number_match.group(1))
            if 1000 < val < 100000000: 
                return val
        
        return None
    
    def _extract_tenure(self, text: str) -> Optional[int]:
        """Extract loan tenure from text"""
        # Years
        year_match = re.search(r'(\d+)\s*(?:years?|yrs?|y)', text, re.IGNORECASE)
        if year_match:
            return int(year_match.group(1)) * 12
        
        # Months
        month_match = re.search(r'(\d+)\s*(?:months?|mon|m)', text, re.IGNORECASE)
        if month_match:
            return int(month_match.group(1))
        
        return None
    
    def _extract_purpose(self, text: str) -> Optional[str]:
        """Extract loan purpose from text"""
        purpose_keywords = {
            "business": ["business", "startup", "venture", "shop", "expansion"],
            "wedding": ["wedding", "marriage", "shaadi", "function"],
            "medical": ["medical", "health", "hospital", "surgery", "treatment"],
            "education": ["education", "study", "college", "fees", "school"],
            "travel": ["travel", "vacation", "holiday", "trip"],
            "renovation": ["renovate", "renovation", "repair", "construction", "interior"],
            "debt": ["debt", "loan", "card", "pay off"],
            "vehicle": ["car", "bike", "vehicle", "scooter"],
            "personal": ["personal", "urgent", "need"]
        }
        for purpose, keywords in purpose_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return purpose
        return None
    
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