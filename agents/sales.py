from openai import OpenAI
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
    Uses GPT-4 for natural, human-like conversation
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.model = "openai/gpt-oss-20b"  # Latest GPT-4 model
        self.conversation_context = []
        
    def negotiate_loan(
        self, 
        user_message: str, 
        customer_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Negotiate loan terms with customer using GPT-4
        This is the main conversational agent
        """
        
        # Create comprehensive system prompt
        system_prompt = self._create_system_prompt(customer_data)
        
        # Prepare messages for GPT-4
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages for context)
        for msg in conversation_history[-10:]:
            if msg["role"] in ["user", "assistant"]:
                messages.append(msg)
        
        # Add current user message if not already in history
        if not conversation_history or conversation_history[-1]["content"] != user_message:
            messages.append({"role": "user", "content": user_message})
        
        try:
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.8,  # More natural and varied responses
                max_tokens=600,
                presence_penalty=0.6,  # Encourage diverse responses
                frequency_penalty=0.3   # Reduce repetition
            )
            
            assistant_message = response.choices[0].message.content.strip()
            
            # Check if we have enough information to proceed
            loan_details = self._extract_loan_details(conversation_history + [{"role": "assistant", "content": assistant_message}])
            
            if loan_details and self._has_complete_info(loan_details):
                # Calculate EMI and finalize
                loan_details = self._finalize_loan_details(loan_details, customer_data)
                
                # Remove extraction markers from message
                clean_message = self._clean_message(assistant_message)
                
                return {
                    "message": clean_message,
                    "ready_for_next_stage": True,
                    "loan_details": loan_details
                }
            else:
                return {
                    "message": assistant_message,
                    "ready_for_next_stage": False,
                    "loan_details": {}
                }
                
        except Exception as e:
            print(f"Error calling GPT-4: {e}")
            # Provide a helpful fallback
            return {
                "message": "I'd love to help you with your loan! Could you tell me more about what you're looking for?",
                "ready_for_next_stage": False,
                "loan_details": {}
            }
    
    def _create_system_prompt(self, customer_data: Dict[str, Any]) -> str:
        """Create a detailed system prompt for the sales agent"""
        
        return f"""You are Arjun, a friendly and professional personal loan advisor at Tata Capital. You're talking to {customer_data['name']}, a valued customer.

CUSTOMER PROFILE:
- Name: {customer_data['name']}
- Age: {customer_data['age']}
- Location: {customer_data['city']}
- Pre-approved Limit: ₹{customer_data['pre_approved_limit']:,}
- Credit Score: {customer_data['credit_score']}/900 (Excellent!)
- Monthly Income: ₹{customer_data['monthly_income']:,}
- Current Loans: {customer_data.get('current_loans', 'None')}
- Company: {customer_data.get('company', 'N/A')}

YOUR PERSONALITY:
- Warm, friendly, and conversational (like talking to a friend)
- Enthusiastic but not pushy
- Use emojis occasionally (💰 🎉 ✨ 👍 📊)
- Address customer by first name
- Empathetic and understanding
- Professional yet approachable

YOUR GOAL:
Help {customer_data['name']} get the perfect personal loan by understanding their needs and offering the best solution.

WHAT YOU NEED TO FIND OUT (naturally through conversation):
1. Loan Purpose - Why do they need the loan? (business, wedding, travel, home renovation, medical, education, debt consolidation, etc.)
2. Loan Amount - How much do they need? (be flexible, suggest if needed)
3. Repayment Period - How long do they want to repay? (12-60 months)

CONVERSATION GUIDELINES:

1. BE CONVERSATIONAL:
   - Don't ask questions like a form
   - React to what they say naturally
   - Show understanding: "That sounds exciting!", "I completely understand", "Great choice!"
   - Share relevant insights: "Many of our customers take loans for business expansion"

2. BE HELPFUL & SUGGESTIVE:
   - If they mention amount > pre-approved: "₹10 lakh is a significant amount! Your pre-approved limit is ₹{customer_data['pre_approved_limit']:,}. We can definitely work with amounts up to ₹{customer_data['pre_approved_limit'] * 2:,} with additional verification."
   - If they're unsure: Suggest typical amounts based on their income
   - Mention benefits: "Interest rates as low as 10.5%", "Zero processing fee this month!"

3. EXTRACT INFORMATION SMARTLY:
   - Listen for amounts: "10 lakh", "5 lakhs", "two hundred thousand", "₹300000"
   - Listen for tenure: "5 years", "2 years", "24 months", "60 months"
   - Listen for purpose: "business", "wedding", "medical emergency", "vacation"
   - Don't ask for info they already gave!

4. BE PERSUASIVE (but ethical):
   - Highlight quick approval: "We can process this in 24 hours!"
   - Mention flexibility: "Prepayment allowed with no charges after 6 months"
   - Build trust: "Tata Capital has helped 5 million+ customers"
   - Create urgency: "This pre-approved offer is valid till month-end"

5. WHEN YOU HAVE ALL INFO:
   Once you know the amount, tenure, and purpose, summarize enthusiastically:
   "Perfect! So you're looking for ₹[amount] for [purpose] over [tenure] months. Let me calculate the best EMI for you!"
   
   Then include this EXACT line at the end:
   [EXTRACTION:amount=[rupees],tenure=[months],purpose=[purpose]]

EXAMPLES OF GOOD RESPONSES:

User: "I need a loan for my business"
You: "That's fantastic! 🚀 Business expansion is a great reason for a loan. Many entrepreneurs like you choose Tata Capital for business funding. 

How much capital are you looking to invest in your business? And do you have a timeline in mind for repayment?"

User: "Around 10 lakhs, can pay back in 5 years"
You: "₹10 lakhs over 5 years - that's a solid plan! 💼

I see your pre-approved limit is ₹{customer_data['pre_approved_limit']:,}. For ₹10 lakhs, we can definitely make it work - we'll just need to verify your salary slip since it's a bit higher than your pre-approved amount.

The good news? Your excellent credit score of {customer_data['credit_score']} makes you a prime candidate! 

With our special rates, your EMI would be approximately ₹21,200/month. Does that work for your budget?"

IMPORTANT RULES:
- NEVER repeat the same question twice
- NEVER use robotic language like "Please provide the following information:"
- ALWAYS acknowledge what they just said before asking more
- Keep responses concise (2-4 sentences usually)
- Be human, be helpful, be friendly!

Now, respond to {customer_data['name']}'s message naturally and helpfully."""

    def _extract_loan_details(self, conversation_history: List[Dict]) -> Optional[Dict]:
        """
        Extract loan details from entire conversation using NLP and pattern matching
        """
        
        # Combine all user messages
        all_text = " ".join([msg["content"].lower() for msg in conversation_history if msg["role"] == "user"])
        
        details = {}
        
        # Extract AMOUNT
        amount = self._extract_amount(all_text)
        if amount:
            details["amount"] = amount
        
        # Extract TENURE
        tenure = self._extract_tenure(all_text)
        if tenure:
            details["tenure"] = tenure
        
        # Extract PURPOSE
        purpose = self._extract_purpose(all_text)
        if purpose:
            details["purpose"] = purpose
        
        # Also check for extraction marker in assistant's last message
        if conversation_history and conversation_history[-1]["role"] == "assistant":
            last_msg = conversation_history[-1]["content"]
            extraction_match = re.search(r'\[EXTRACTION:amount=(\d+),tenure=(\d+),purpose=([^\]]+)\]', last_msg)
            if extraction_match:
                details["amount"] = int(extraction_match.group(1))
                details["tenure"] = int(extraction_match.group(2))
                details["purpose"] = extraction_match.group(3)
        
        return details if details else None
    
    def _extract_amount(self, text: str) -> Optional[int]:
        """Extract loan amount from text"""
        
        # Pattern 1: "10 lakh", "5 lakhs"
        lakh_pattern = r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|lakhs|lacs)'
        lakh_match = re.search(lakh_pattern, text, re.IGNORECASE)
        if lakh_match:
            return int(float(lakh_match.group(1)) * 100000)
        
        # Pattern 2: "₹500000", "Rs 500000", "500000 rupees"
        rupee_pattern = r'(?:₹|rs\.?|rupees?)\s*(\d+(?:,\d+)*)'
        rupee_match = re.search(rupee_pattern, text, re.IGNORECASE)
        if rupee_match:
            amount_str = rupee_match.group(1).replace(',', '')
            return int(amount_str)
        
        # Pattern 3: Just large numbers (likely amounts)
        number_pattern = r'\b(\d{5,})\b'
        number_match = re.search(number_pattern, text)
        if number_match:
            return int(number_match.group(1))
        
        # Pattern 4: "1 crore", "2 crores"
        crore_pattern = r'(\d+(?:\.\d+)?)\s*(?:crore|crores)'
        crore_match = re.search(crore_pattern, text, re.IGNORECASE)
        if crore_match:
            return int(float(crore_match.group(1)) * 10000000)
        
        # Pattern 5: "thousand"
        thousand_pattern = r'(\d+(?:\.\d+)?)\s*(?:thousand|k)'
        thousand_match = re.search(thousand_pattern, text, re.IGNORECASE)
        if thousand_match:
            return int(float(thousand_match.group(1)) * 1000)
        
        return None
    
    def _extract_tenure(self, text: str) -> Optional[int]:
        """Extract loan tenure from text"""
        
        # Pattern 1: "5 years", "2 year"
        year_pattern = r'(\d+)\s*(?:years?|yrs?)'
        year_match = re.search(year_pattern, text, re.IGNORECASE)
        if year_match:
            return int(year_match.group(1)) * 12
        
        # Pattern 2: "24 months", "36 month"
        month_pattern = r'(\d+)\s*(?:months?|mon)'
        month_match = re.search(month_pattern, text, re.IGNORECASE)
        if month_match:
            return int(month_match.group(1))
        
        return None
    
    def _extract_purpose(self, text: str) -> Optional[str]:
        """Extract loan purpose from text"""
        
        purpose_keywords = {
            "business": ["business", "startup", "venture", "company", "expand", "expansion"],
            "wedding": ["wedding", "marriage", "shaadi"],
            "medical": ["medical", "health", "hospital", "surgery", "treatment"],
            "education": ["education", "study", "course", "college", "university"],
            "travel": ["travel", "vacation", "holiday", "trip"],
            "home_renovation": ["renovation", "repair", "remodel", "home improvement"],
            "debt_consolidation": ["debt", "consolidate", "pay off", "credit card"],
            "emergency": ["emergency", "urgent", "immediate"],
            "vehicle": ["car", "bike", "vehicle", "automobile"],
            "personal": ["personal", "general"]
        }
        
        for purpose, keywords in purpose_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return purpose
        
        return "personal"
    
    def _has_complete_info(self, loan_details: Dict) -> bool:
        """Check if we have all required information"""
        return all(key in loan_details for key in ["amount", "tenure", "purpose"])
    
    def _finalize_loan_details(self, loan_details: Dict, customer_data: Dict) -> Dict:
        """Calculate EMI and finalize loan details"""
        
        amount = loan_details["amount"]
        tenure = loan_details["tenure"]
        
        # Calculate interest rate based on amount
        interest_rate = self._calculate_interest_rate(amount, tenure, customer_data)
        
        # Calculate EMI
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
        
        # Base rate
        base_rate = 11.5
        
        # Credit score adjustment
        credit_score = customer_data.get("credit_score", 700)
        if credit_score >= 800:
            base_rate -= 1.0
        elif credit_score >= 750:
            base_rate -= 0.5
        elif credit_score < 700:
            base_rate += 1.0
        
        # Amount adjustment
        if amount <= 200000:
            base_rate -= 0.5
        elif amount >= 1000000:
            base_rate += 0.5
        
        # Tenure adjustment
        if tenure <= 12:
            base_rate -= 0.5
        elif tenure >= 48:
            base_rate += 0.5
        
        return round(base_rate, 2)
    
    def _calculate_emi(self, principal: int, annual_rate: float, tenure_months: int) -> int:
        """Calculate EMI using reducing balance method"""
        monthly_rate = annual_rate / (12 * 100)
        
        if monthly_rate == 0:
            return principal // tenure_months
        
        emi = principal * monthly_rate * (1 + monthly_rate)**tenure_months / \
              ((1 + monthly_rate)**tenure_months - 1)
        
        return int(emi)
    
    def _clean_message(self, message: str) -> str:
        """Remove extraction markers from message"""
        # Remove [EXTRACTION:...] markers
        cleaned = re.sub(r'\[EXTRACTION:.*?\]', '', message)
        return cleaned.strip()


# Test the sales agent
if __name__ == "__main__":
    import os
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    agent = SalesAgent(api_key)
    
    test_customer = {
        "name": "Kabir",
        "age": 31,
        "city": "Mumbai",
        "credit_score": 698,
        "pre_approved_limit": 200000,
        "monthly_income": 52000,
        "current_loans": "Car Loan: ₹3,50,000",
        "company": "Finance Corp"
    }
    
    conversation = []
    
    test_messages = [
        "I need a loan for my business",
        "Around 10 lakh, can pay back in 5 years"
    ]
    
    for msg in test_messages:
        conversation.append({"role": "user", "content": msg})
        result = agent.negotiate_loan(msg, test_customer, conversation)
        
        print(f"\n👤 User: {msg}")
        print(f"🤖 Agent: {result['message']}")
        print(f"Ready: {result['ready_for_next_stage']}")
        
        conversation.append({"role": "assistant", "content": result['message']})
        
        if result['ready_for_next_stage']:
            print(f"\n✅ Loan Details: {result['loan_details']}")
