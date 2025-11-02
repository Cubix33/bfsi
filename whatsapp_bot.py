import os
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from main import MasterAgent
import json
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g., whatsapp:+14155238886
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# In-memory session storage (use Redis in production)
# Structure: {phone_number: {"agent": MasterAgent, "last_activity": datetime}}
sessions = {}

# Session timeout (30 minutes)
SESSION_TIMEOUT = timedelta(minutes=30)


def get_or_create_session(phone_number: str) -> MasterAgent:
    """
    Get existing session or create a new one for the phone number
    """
    # Clean expired sessions
    clean_expired_sessions()
    
    if phone_number in sessions:
        # Update last activity
        sessions[phone_number]["last_activity"] = datetime.now()
        return sessions[phone_number]["agent"]
    else:
        # Create new session
        agent = MasterAgent(GROQ_API_KEY)
        sessions[phone_number] = {
            "agent": agent,
            "last_activity": datetime.now()
        }
        return agent


def clean_expired_sessions():
    """
    Remove sessions that have been inactive for more than SESSION_TIMEOUT
    """
    now = datetime.now()
    expired = [
        phone for phone, data in sessions.items()
        if now - data["last_activity"] > SESSION_TIMEOUT
    ]
    for phone in expired:
        del sessions[phone]
        print(f"🗑️ Cleaned expired session for {phone}")


def send_whatsapp_message(to_number: str, message: str, media_url: str = None):
    """
    Send a WhatsApp message (optionally with media attachment)
    """
    try:
        if media_url:
            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=to_number,
                media_url=[media_url]
            )
        else:
            client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=message,
                to=to_number
            )
        print(f"✅ Message sent to {to_number}")
    except Exception as e:
        print(f"❌ Error sending message: {e}")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    WhatsApp webhook endpoint - receives incoming messages
    """
    try:
        # Get incoming message details
        incoming_msg = request.values.get("Body", "").strip()
        from_number = request.values.get("From", "")  # Format: whatsapp:+1234567890
        
        print(f"📱 Received from {from_number}: {incoming_msg}")
        
        # Handle special commands
        if incoming_msg.lower() in ['restart', 'reset', 'start over']:
            # Delete existing session
            if from_number in sessions:
                del sessions[from_number]
                print(f"🔄 Restarted session for {from_number}")
            
            # Create new session and send welcome message
            agent = get_or_create_session(from_number)
            welcome_msg = agent.start_conversation()
            send_whatsapp_message(from_number, welcome_msg)
            return str(MessagingResponse())
        
        # Get or create agent for this user
        agent = get_or_create_session(from_number)
        
        # Check if this is the first message (agent hasn't started)
        if not agent.conversation_history:
            # Start conversation
            welcome_msg = agent.start_conversation()
            send_whatsapp_message(from_number, welcome_msg)
            return str(MessagingResponse())
        
        # Process the message through the MasterAgent
        response = agent.process_message(incoming_msg)
        
        # Check if a sanction letter was generated
        if agent.state.get("stage") == "approval" and agent.state.get("final_decision"):
            # Extract PDF path from conversation if sanction letter was generated
            if "sanction_letters/" in response:
                # Try to find the PDF path in the response
                import re
                pdf_match = re.search(r'(sanction_letters/[^\s]+\.pdf)', response)
                if pdf_match:
                    pdf_path = pdf_match.group(1)
                    
                    # For Twilio, you need to host the PDF publicly
                    # For now, we'll just send the text response
                    # TODO: Upload PDF to cloud storage (AWS S3, Azure Blob, etc.) and get public URL
                    send_whatsapp_message(from_number, response)
                    send_whatsapp_message(
                        from_number, 
                        f"📄 Your sanction letter has been generated! Please visit our office or we'll email it to you."
                    )
                else:
                    send_whatsapp_message(from_number, response)
            else:
                send_whatsapp_message(from_number, response)
        else:
            # Send normal response
            send_whatsapp_message(from_number, response)
        
        return str(MessagingResponse())
        
    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        error_msg = "I'm sorry, something went wrong. Please try again or type 'restart' to start over."
        send_whatsapp_message(from_number, error_msg)
        return str(MessagingResponse())


@app.route("/status", methods=["GET"])
def status():
    """
    Health check endpoint
    """
    return {
        "status": "running",
        "active_sessions": len(sessions),
        "sessions": list(sessions.keys())
    }


@app.route("/", methods=["GET"])
def home():
    """
    Home page
    """
    return """
    <h1>🏦 TATA Capital WhatsApp Bot</h1>
    <p>WhatsApp webhook is running!</p>
    <p><a href="/status">Check Status</a></p>
    """


if __name__ == "__main__":
    # Check if all credentials are set
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, GROQ_API_KEY]):
        print("\n" + "="*80)
        print("❌ ERROR: Missing credentials!")
        print("="*80)
        print("\nPlease add the following to your .env file:")
        print("TWILIO_ACCOUNT_SID=your_account_sid")
        print("TWILIO_AUTH_TOKEN=your_auth_token")
        print("TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886")
        print("GROQ_API_KEY=your_groq_key")
        print("\n")
    else:
        print("\n" + "="*80)
        print("✅ WhatsApp Bot Server Starting...")
        print("="*80)
        print(f"\nTwilio WhatsApp Number: {TWILIO_WHATSAPP_NUMBER}")
        print(f"Webhook URL: http://localhost:5000/webhook")
        print("\nNote: Use ngrok to expose this to the internet:")
        print("  ngrok http 5000")
        print("\nThen configure the ngrok URL in Twilio Console\n")
        
        # Run Flask app
        app.run(host="0.0.0.0", port=5000, debug=True)
