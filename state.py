from typing import Dict, Any, List
from enum import Enum

class ConversationStage(Enum):
    INITIAL = "initial"
    NEEDS_ASSESSMENT = "needs_assessment"
    VERIFICATION = "verification"
    CREDIT_CHECK = "credit_check"
    UNDERWRITING = "underwriting"
    DOCUMENT_UPLOAD = "document_upload"
    APPROVAL = "approval"
    REJECTION = "rejection"
    COMPLETED = "completed"

class ConversationState:
    """Manages conversation state across the multi-agent workflow"""
    
    def __init__(self):
        self.stage = ConversationStage.INITIAL
        self.customer_data: Dict[str, Any] = {}
        self.loan_request: Dict[str, Any] = {}
        self.verification_status = False
        self.credit_score: int = 0
        self.underwriting_result: Dict[str, Any] = {}
        self.documents_uploaded = False
        self.final_decision: str = None
        self.conversation_history: List[Dict[str, str]] = []
    
    def transition_to(self, new_stage: ConversationStage):
        """Transition to new conversation stage"""
        print(f"[STATE] Transitioning from {self.stage.value} to {new_stage.value}")
        self.stage = new_stage
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current state summary"""
        return {
            "stage": self.stage.value,
            "has_customer_data": bool(self.customer_data),
            "has_loan_request": bool(self.loan_request),
            "verification_status": self.verification_status,
            "credit_score": self.credit_score,
            "documents_uploaded": self.documents_uploaded,
            "final_decision": self.final_decision
        }
