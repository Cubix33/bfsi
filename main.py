import os
from typing import Dict, List, Any
from groq import Groq
from agents.sales import SalesAgent
from agents.verification import VerificationAgent
from agents.underwriting import UnderwritingAgent
from agents.document import DocumentAgent
from agents.credit import CreditAgent
from agents.upload import UploadAgent
from utils.mock_data import get_customer_data, get_offer_data
import json
from dotenv import load_dotenv
import platform
import subprocess


def open_pdf(filepath):
    """Open PDF file with default PDF viewer"""
    
    # Make sure the file exists
    if not os.path.exists(filepath):
        print(f"⚠️  PDF file not found: {filepath}")
        print(f"   Please check the sanction_letters folder")
        return
    
    try:
        # Get absolute path
        abs_path = os.path.abspath(filepath)
        
        if platform.system() == 'Windows':
            os.startfile(abs_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', abs_path])
        else:  # Linux
            subprocess.call(['xdg-open', abs_path])
            
        print(f"✅ PDF opened: {abs_path}")
    except Exception as e:
        print(f"Could not open PDF automatically: {e}")
        print(f"Please open manually: {os.path.abspath(filepath)}")


class MasterAgent:
    """
    Master Agent - Main Orchestrator
    Manages conversation flow and coordinates all worker agents
    """
    
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.state = {
            "stage": "initial",
            "customer_data": None,
            "loan_request": {},
            "verification_status": False,
            "credit_score": None,
            "underwriting_result": None,
            "documents_uploaded": False,
            "final_decision": None,
            "waiting_for_manual_upload": False
        }
        
        # Initialize worker agents
        self.sales_agent = SalesAgent(api_key)
        self.verification_agent = VerificationAgent()
        self.credit_agent = CreditAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.document_agent = DocumentAgent()
        self.upload_agent = UploadAgent()
        
    def start_conversation(self, customer_phone: str = None):
        """Initialize conversation with customer"""
        print("=" * 80)
        print("🏦 TATA CAPITAL - Personal Loan Assistant")
        print("=" * 80)
        
        welcome_msg = """Hello! 👋 Welcome to Tata Capital.

I'm your personal loan assistant, and I'm here to help you get the best loan offer tailored to your needs.

May I have your phone number to get started?"""
        
        print(f"\n🤖 Assistant: {welcome_msg}\n")
        self.conversation_history.append({
            "role": "assistant",
            "content": welcome_msg
        })
        
        return welcome_msg
    
    def process_message(self, user_message: str) -> str:
        """Main orchestration logic - routes to appropriate agent based on state"""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Route based on current stage
        if self.state["stage"] == "initial":
            return self._handle_initial_stage(user_message)
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
        elif self.state["stage"] == "approval":
            return self._handle_approval(user_message)
        elif self.state["stage"] == "rejection":
            return self._handle_rejection(user_message)
        else:
            return "I'm sorry, something went wrong. Let me restart our conversation."
    
    def _handle_initial_stage(self, user_message: str) -> str:
        """Handle initial customer identification"""
        phone = ''.join(filter(str.isdigit, user_message))
        
        if len(phone) >= 10:
            customer_data = get_customer_data(phone[-10:])
            
            if customer_data:
                self.state["customer_data"] = customer_data
                self.state["stage"] = "needs_assessment"
                
                response = f"""Great! I found your profile, {customer_data['name']}.

I see you're based in {customer_data['city']}. Good news - you have a pre-approved personal loan offer of ₹{customer_data['pre_approved_limit']:,}!

Before we proceed, could you tell me:
1. What would you like to use this loan for?
2. How much loan amount are you looking for?
3. What repayment tenure would be comfortable for you?"""
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response
            else:
                response = """I couldn't find your profile in our system. Let me take your details:

Could you please provide:
1. Your full name
2. Your city
3. Your monthly income"""
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response
        else:
            response = "I didn't catch a valid phone number. Could you please provide your 10-digit mobile number?"
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _handle_needs_assessment(self, user_message: str) -> str:
        """Delegate to Sales Agent for needs assessment and negotiation"""
        sales_response = self.sales_agent.negotiate_loan(
            user_message,
            self.state["customer_data"],
            self.conversation_history
        )
        
        if sales_response.get("ready_for_next_stage"):
            self.state["loan_request"] = sales_response["loan_details"]
            self.state["stage"] = "verification"
            
            verification_msg = f"""Perfect! Let me summarize:
- Loan Amount: ₹{sales_response['loan_details']['amount']:,}
- Purpose: {sales_response['loan_details']['purpose'].replace('_', ' ').title()}
- Tenure: {sales_response['loan_details']['tenure']} months ({sales_response['loan_details']['tenure']//12} years)
- Interest Rate: {sales_response['loan_details']['interest_rate']}% p.a.
- Monthly EMI: ₹{sales_response['loan_details']['emi']:,}

Now, for security purposes, I need to verify your details. Let me confirm:
- Name: {self.state['customer_data']['name']}
- Phone: {self.state['customer_data']['phone']}
- Address: {self.state['customer_data']['address']}

Is this information correct? (Yes/No)"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": verification_msg
            })
            return verification_msg
        else:
            response = sales_response["message"]
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _handle_verification(self, user_message: str) -> str:
        """Delegate to Verification Agent for KYC check"""
        if "yes" in user_message.lower():
            verification_result = self.verification_agent.verify_customer(
                self.state["customer_data"]
            )
            
            if verification_result["verified"]:
                self.state["verification_status"] = True
                self.state["stage"] = "credit_check"
                
                response = """✅ Verification successful!

Now let me check your credit score and eligibility. This will just take a moment..."""
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                
                return response + "\n\n" + self._handle_credit_check("")
            else:
                response = "❌ I couldn't verify your details. Please contact our customer service."
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                self.state["stage"] = "rejection"
                return response
        else:
            response = "Please confirm if the details are correct by typing 'Yes' or 'No'."
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _handle_credit_check(self, user_message: str) -> str:
        """Delegate to Credit Agent to fetch credit score"""
        credit_result = self.credit_agent.get_credit_score(
            self.state["customer_data"]["phone"]
        )
        
        self.state["credit_score"] = credit_result["score"]
        
        if credit_result["score"] < 700:
            self.state["stage"] = "rejection"
            
            # Empathetic rejection message
            response = f"""I've reviewed your credit profile carefully.

{self.state["customer_data"]["name"]}, your credit score is currently {credit_result['score']}/900. Unfortunately, our minimum requirement is 700 for instant approval.

But here's the good news - you're only {700 - credit_result['score']} points away! 

**Quick Options:**
1. ✅ Take your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,} (say "yes" or "option 1")
2. 💬 Free credit counseling (say "counseling" or "option 2")
3. 🔒 Secured loan options (say "secured loan" or "option 3")

What would you like to do?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        else:
            self.state["stage"] = "underwriting"
            response = f"""Excellent news! Your credit score of {credit_result['score']}/900 is strong! ✅

Let me now evaluate your loan eligibility..."""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response + "\n\n" + self._handle_underwriting("")
    
    def _handle_underwriting(self, user_message: str) -> str:
        """Delegate to Underwriting Agent for eligibility check"""
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
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            return response + "\n\n" + self._generate_sanction_letter()
        
        elif underwriting_result["decision"] == "REQUIRES_SALARY_SLIP":
            self.state["stage"] = "document_upload"
            response = f"""Your loan amount (₹{self.state['loan_request']['amount']:,}) is {underwriting_result['ratio']:.1f}x your pre-approved limit.

We need to verify your income for approval.

📄 **Please upload your latest salary slip.**

Type 'upload' to auto-fetch from database, or type 'manual upload' to upload your own file."""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        else:  # REJECTED
            self.state["stage"] = "rejection"
            response = f"""I've carefully reviewed your application.

The requested amount (₹{self.state['loan_request']['amount']:,}) exceeds our maximum approval limit.

However, you're pre-approved for ₹{self.state['customer_data']['pre_approved_limit']:,}. 

Would you like to proceed with this amount? (Yes/No)"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _handle_document_upload(self, user_message: str) -> str:
        """Handle salary slip upload with manual upload option"""
        
        user_lower = user_message.lower()
        
        # Check if in manual upload waiting state
        if self.state.get("waiting_for_manual_upload"):
            if "done" in user_lower:
                # User completed manual upload
                self.state["waiting_for_manual_upload"] = False
                
                # Try to process the uploaded file
                upload_result = self.upload_agent.process_upload(
                    self.state["customer_data"]["name"]
                )
                
                if upload_result["success"]:
                    return self._process_salary_verification(upload_result["file_path"])
                else:
                    response = f"""I still can't find the file. Please make sure:

1. File is named: SalarySlip_{self.state['customer_data']['name'].replace(' ', '_')}.pdf
2. File is in the 'salary_slips' folder
3. File is a valid PDF

Type 'done' once ready, or 'skip' to see other options."""
                    
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    return response
            
            elif "skip" in user_lower:
                self.state["waiting_for_manual_upload"] = False
                return self._show_skip_options()
            
            else:
                response = """Please type 'done' once you've uploaded the file, or 'skip' to see other options."""
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response
        
        # Manual upload request
        if "manual" in user_lower and "upload" in user_lower:
            response = f"""📤 **Manual Upload Process:**

To upload your salary slip:

1. **Save your salary slip** as a PDF file
2. **Name it**: SalarySlip_{self.state['customer_data']['name'].replace(' ', '_')}.pdf
3. **Place it** in the 'salary_slips' folder in the project directory
4. **Type 'done'** once uploaded

Alternatively, type 'auto' to let me check our database for your salary slip."""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Set a flag to wait for manual upload confirmation
            self.state["waiting_for_manual_upload"] = True
            
            return response
        
        # Auto upload OR just "upload"
        elif "upload" in user_lower or "auto" in user_lower:
            # Try auto-fetch from database
            upload_result = self.upload_agent.process_upload(
                self.state["customer_data"]["name"]
            )
            
            if upload_result["success"]:
                return self._process_salary_verification(upload_result["file_path"])
            else:
                # File not found - offer manual upload
                response = f"""I couldn't find your salary slip in our database.

Would you like to:
1. **Upload manually** (type 'manual upload')
2. **Skip** and see other options (type 'skip')

What would you prefer?"""
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
                return response
        
        # Skip option
        elif "skip" in user_lower:
            return self._show_skip_options()
        
        # User is confused
        else:
            response = """I need your salary slip to proceed. Please choose:

- Type **'upload'** → I'll check our database
- Type **'manual upload'** → Upload your own file
- Type **'skip'** → See other options

What would you like to do?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _process_salary_verification(self, file_path: str) -> str:
        """Process salary slip and make approval decision"""
        doc_result = self.document_agent.extract_salary_info(file_path)
        
        monthly_emi = self.state["loan_request"]["emi"]
        monthly_salary = doc_result["basic_salary"] + doc_result["hra"] + doc_result["other_allowances"]
        emi_ratio = (monthly_emi / monthly_salary) * 100
        
        if emi_ratio <= 50:
            self.state["stage"] = "approval"
            response = f"""✅ Salary slip verified successfully!

Your monthly income: ₹{monthly_salary:,}
EMI-to-Income ratio: {emi_ratio:.1f}% (Well within our 50% limit)

🎉 Your loan of ₹{self.state['loan_request']['amount']:,} is APPROVED!

Generating your sanction letter..."""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response + "\n\n" + self._generate_sanction_letter()
        else:
            self.state["stage"] = "rejection"
            response = f"""Thank you for uploading your salary slip.

After review, your EMI (₹{monthly_emi:,}) would be {emi_ratio:.1f}% of your income (₹{monthly_salary:,}/month).

Our policy requires EMI ≤ 50% of income.

Would you like to accept your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _show_skip_options(self) -> str:
        """Show options when user skips document upload"""
        self.state["stage"] = "rejection"
        self.state["waiting_for_manual_upload"] = False
        
        response = f"""No problem! Let's look at alternatives:

1. **Accept ₹{self.state['customer_data']['pre_approved_limit']:,}** (instant approval - say "yes")
2. **Credit counseling** (free advice - say "counseling")
3. **Secured loan** (higher amounts - say "secured loan")

What would you prefer?"""
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        return response
    
    def _generate_sanction_letter(self) -> str:
        """Generate PDF sanction letter"""
        from utils.pdf_generator import generate_sanction_letter
        
        pdf_path = generate_sanction_letter(
            customer_data=self.state["customer_data"],
            loan_details=self.state["loan_request"]
        )
        
        response = f"""✅ Sanction Letter Generated Successfully!

📄 Your sanction letter: {pdf_path}

Opening PDF now...

Next Steps:
1. Review the sanction letter
2. Our team will contact you within 24 hours
3. Loan disbursement in 2-3 business days

Thank you for choosing Tata Capital!"""
        
        # Try to open PDF automatically
        try:
            open_pdf(pdf_path)
        except:
            pass
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        self.state["final_decision"] = "APPROVED"
        return response
    
    def _handle_approval(self, user_message: str) -> str:
        """Handle post-approval queries with LLM-powered natural responses"""
        
        # Don't process empty messages
        if not user_message or user_message.isspace():
            response = "Thank you for choosing Tata Capital! Have a great day! 👋"
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        try:
            # Use LLM for natural post-approval conversation
            system_prompt = f"""You are a friendly loan advisor at Tata Capital. 

The customer {self.state['customer_data']['name']} has been APPROVED for their loan! 🎉

APPROVED LOAN DETAILS:
- Amount: ₹{self.state['loan_request']['amount']:,}
- EMI: ₹{self.state['loan_request']['emi']:,}/month
- Tenure: {self.state['loan_request']['tenure']} months
- Purpose: {self.state['loan_request']['purpose']}

YOUR ROLE:
- Answer ANY questions they have naturally and helpfully
- Be warm, friendly, and conversational
- If they ask about timeline, documents, EMI, or process - provide clear answers
- If they just chat casually, respond warmly and bring conversation back to helpful info
- Keep responses concise (2-4 sentences)

COMMON QUESTIONS & ANSWERS:
- Timeline: "Disbursement in 2-3 business days after documentation"
- Documents: "Our team will send you a list within 24 hours. Typically: PAN, Aadhaar, bank statements"
- EMI payments: "You'll receive payment schedule via email. Auto-debit available"
- Contact: "Call 1800-123-4567 or email support@tatacapital.com"
- Prepayment: "Allowed after 6 months with no charges"
- Next steps: "Our team will call you within 24 hours to complete documentation"

If they say casual things like "how are you", "bro", "thanks", "cool":
- Respond warmly: "I'm doing great! So happy your loan got approved!"
- Then ask: "Do you have any questions about the loan or the next steps?"

Be HUMAN, be HELPFUL, be FRIENDLY!"""

            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent context (last 6 messages)
            for msg in self.conversation_history[-6:]:
                if msg["role"] in ["user", "assistant"]:
                    messages.append(msg)
            
            # Call LLM for natural response
            response = self.client.chat.completions.create(
                model=self.sales_agent.model,
                messages=messages,
                temperature=0.9,
                max_tokens=250
            )
            
            helpful_response = response.choices[0].message.content.strip()
            
            self.conversation_history.append({
                "role": "assistant",
                "content": helpful_response
            })
            
            return helpful_response
            
        except Exception as e:
            print(f"Error in approval handler: {e}")
            
            # Fallback to context-aware canned responses
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ["when", "timeline", "how long", "disburse"]):
                response = """Your loan will be disbursed within 2-3 business days after final documentation.

You'll receive confirmation email, payment schedule, and SMS alerts.

Anything else I can help with?"""
            
            elif any(word in user_lower for word in ["document", "paper", "upload", "need"]):
                response = """Our team will contact you within 24 hours with the document list.

Typically needed: PAN card, Aadhaar, bank statements (last 3 months).

Any other questions?"""
            
            elif any(word in user_lower for word in ["thank", "great", "perfect", "awesome", "cool"]):
                response = f"""You're very welcome, {self.state['customer_data']['name']}! 🎉

We're excited to have you as a Tata Capital customer. 

Is there anything else you'd like to know about your loan?"""
            
            elif any(word in user_lower for word in ["how are you", "what's up", "bro", "dude"]):
                response = f"""I'm doing great, thanks for asking! 😊

More importantly, congratulations on your loan approval! 

Do you have any questions about the next steps or your loan details?"""
            
            else:
                response = f"""Your loan of ₹{self.state['loan_request']['amount']:,} is approved! 

If you have any specific questions:
- Call: 1800-123-4567
- Email: support@tatacapital.com

What would you like to know?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _handle_rejection(self, user_message: str) -> str:
        """Handle post-rejection queries with empathy and alternatives"""
        
        user_lower = user_message.lower()
        
        # Check if customer wants pre-approved amount
        # More flexible detection
        if any(word in user_lower for word in ["yes", "option 1", "pre-approved", "pre approved", "accept", "take it", "i'll take"]):
            # Customer wants pre-approved amount
            self.state["loan_request"]["amount"] = self.state["customer_data"]["pre_approved_limit"]
            self.state["loan_request"]["purpose"] = self.state["loan_request"].get("purpose", "personal")
            
            # Recalculate EMI
            interest_rate = 12.5
            tenure = self.state["loan_request"].get("tenure", 24)  # Default to 24 if not set
            monthly_rate = interest_rate / (12 * 100)
            self.state["loan_request"]["interest_rate"] = interest_rate
            self.state["loan_request"]["emi"] = int(
                (self.state["loan_request"]["amount"] * monthly_rate * (1 + monthly_rate)**tenure) /
                ((1 + monthly_rate)**tenure - 1)
            )
            
            self.state["stage"] = "approval"
            self.state["final_decision"] = "APPROVED"
            
            response = f"""Perfect! Let me process your pre-approved loan of ₹{self.state['customer_data']['pre_approved_limit']:,}.

Generating your sanction letter..."""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Generate sanction letter immediately
            return response + "\n\n" + self._generate_sanction_letter()
        
        # Check if they want counseling
        elif any(word in user_lower for word in ["option 2", "counsel", "credit improvement", "improve", "counseling"]):
            response = f"""Great choice! Let me connect you with our credit counselor.

📞 **Free Credit Counseling Session**

Our expert will help you:
1. Review your credit report for errors
2. Create a 6-month improvement plan
3. Understand factors affecting your score
4. Get personalized advice for your situation

You'll receive a call within 24 hours at {self.state['customer_data']['phone']}.

In the meantime, would you like to:
- Accept your pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")
- Learn more about secured loans? (Say "secured loan")"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        # Check if they want secured loan info
        elif any(word in user_lower for word in ["option 3", "secured", "collateral", "property", "vehicle"]):
            response = f"""Excellent! Let me explain our secured loan options.

🏠 **Secured Loan Against Property**
- Loan Amount: Up to ₹50 lakhs
- Interest Rate: 8.5% - 10.5% (lower than personal loans!)
- Tenure: Up to 15 years
- Requirement: Property documents

🚗 **Secured Loan Against Vehicle**
- Loan Amount: Up to 80% of vehicle value
- Interest Rate: 9.5% - 11.5%
- Tenure: Up to 5 years
- Requirement: Vehicle RC

Would you like to:
1. Apply for secured loan? (Our team will call you)
2. Accept pre-approved ₹{self.state['customer_data']['pre_approved_limit']:,}? (Say "yes")

What works better for you?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        # Check for keywords indicating they want alternatives
        elif any(keyword in user_lower for keyword in ["alternative", "what can", "help", "anything", "other", "explore"]):
            # Provide concise alternatives
            response = f"""I understand, {self.state['customer_data']['name']}. Here are your options:

**Option 1: Pre-Approved Amount ✅**
- Amount: ₹{self.state['customer_data']['pre_approved_limit']:,}
- Instant approval, no extra documents
- **Say "yes" or "option 1" to proceed**

**Option 2: Credit Improvement 📈**
- Your score: {self.state.get('credit_score', 'N/A')}/900
- Free counseling available
- **Say "option 2" or "counseling"**

**Option 3: Secured Loan 🏠**
- Use property/vehicle as collateral
- Higher amounts with lower rates
- **Say "option 3" or "secured loan"**

Which interests you?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        # Frustrated customer - be empathetic
        elif any(word in user_lower for word in ["fuck", "shit", "wtf", "stupid", "useless", "bro"]):
            response = f"""I'm really sorry for the frustration, {self.state['customer_data']['name']}. I want to help.

Let me make this simple:

Type **"yes"** - I'll instantly approve your ₹{self.state['customer_data']['pre_approved_limit']:,} loan right now.

That's it. One word, and you're done.

What do you say?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
        
        # Default empathetic response
        else:
            response = f"""I understand this is disappointing, {self.state['customer_data']['name']}.

Let me make it simple. Just type:
- **"yes"** → Get ₹{self.state['customer_data']['pre_approved_limit']:,} approved instantly
- **"counseling"** → Free credit advice
- **"secured loan"** → Learn about higher loan amounts

What would you like?"""
            
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            return response
    
    def _get_rejection_reason(self) -> str:
        """Get human-readable rejection reason"""
        if self.state["credit_score"] and self.state["credit_score"] < 700:
            return f"Credit score ({self.state['credit_score']}) below minimum (700)"
        elif self.state["underwriting_result"]:
            return self.state["underwriting_result"].get("reason", "Loan amount exceeds limits")
        else:
            return "Unable to approve at this time"


def main():
    """Main execution function"""
    
    # Load environment variables
    load_dotenv() 
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    
    # Validate API key
    if not api_key:
        print("\n" + "="*80)
        print("❌ ERROR: Groq API Key Not Found!")
        print("="*80)
        print("\nPlease follow these steps:")
        print("1. Get FREE API key from: https://console.groq.com")
        print("2. Add to .env file:")
        print("   GROQ_API_KEY=gsk_your-groq-key-here")
        print("3. Run the program again")
        print("\n" + "="*80 + "\n")
        return
    
    print(f"\n✅ Groq API Key loaded: {api_key[:7]}...{api_key[-4:]}\n")
    
    # Initialize Master Agent
    try:
        master = MasterAgent(api_key)
        
        # Start conversation
        master.start_conversation()
        
        # Conversation loop
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\n🤖 Assistant: Thank you for visiting Tata Capital. Have a great day! 👋\n")
                    break
                
                if not user_input:
                    continue
                
                response = master.process_message(user_input)
                print(f"\n🤖 Assistant: {response}\n")
                
                # Check if conversation has ended
                if master.state["stage"] in ["approval", "rejection"] and master.state["final_decision"]:
                    print("\n" + "=" * 80)
                    print("✅ Conversation completed.")
                    print("=" * 80)
                    
                    # Ask if they want to continue
                    continue_chat = input("\nWould you like to ask anything else? (yes/no): ").strip().lower()
                    if continue_chat not in ['yes', 'y']:
                        print("\n🤖 Assistant: Thank you for choosing Tata Capital! Have a great day! 👋\n")
                        break
                    else:
                        # Keep in approval/rejection handler but allow LLM to respond
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
