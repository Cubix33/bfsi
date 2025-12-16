import os
from flask import Flask, request, send_from_directory
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
from main import MasterAgent
import json
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv

# Force load the .env from current directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
print("Loading .env from:", env_path)
load_dotenv(dotenv_path=env_path)

# Debug print values
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))
print("TWILIO_ACCOUNT_SID:", os.getenv("TWILIO_ACCOUNT_SID"))
print("TWILIO_AUTH_TOKEN:", os.getenv("TWILIO_AUTH_TOKEN"))
print("TWILIO_WHATSAPP_NUMBER:", os.getenv("TWILIO_WHATSAPP_NUMBER"))

# Check if loaded
if not all([
    os.getenv("GROQ_API_KEY"),
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN"),
    os.getenv("TWILIO_WHATSAPP_NUMBER")
]):
    print("❌ ERROR: Missing credentials! Please check your .env file.")
    exit()
else:
    print("✅ All credentials loaded successfully.")


app = Flask(__name__)

# Directory where sanction letters are stored (same as web API)
SANCTION_DIR = os.path.join(os.path.dirname(__file__), "sanction_letters")

# Twilio credentials
# Twilio credentials (loaded from .env)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

if not all([GROQ_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
    print("❌ ERROR: Missing credentials! Please check your .env file.")
    exit()
else:
    print("✅ All credentials loaded successfully.")

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


@app.route("/sanction_letters/<path:filename>", methods=["GET"])
def download_sanction_letter(filename):
    """
    Serve generated sanction letters so Twilio can fetch them as media.
    """
    return send_from_directory(SANCTION_DIR, filename, as_attachment=True)


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    WhatsApp webhook endpoint - receives incoming messages
    """
    try:
        # Get incoming message details
        incoming_msg = request.values.get("Body", "").strip()
        from_number = request.values.get("From", "")  # Format: whatsapp:+1234567890
        num_media = int(request.values.get("NumMedia", "0") or "0")

        print(f"📱 Received from {from_number}: {incoming_msg} (media count: {num_media})")
        
        # Get or create agent for this user
        agent = get_or_create_session(from_number)

        # If user has sent a media file (e.g., salary slip PDF), acknowledge it.
        # Note: The core loan logic currently simulates uploads; here we at least
        # mirror that behaviour for WhatsApp by confirming receipt.
        if num_media > 0:
            media_content_type = request.values.get("MediaContentType0", "")
            media_url = request.values.get("MediaUrl0", "")
            print(f"📎 Incoming media: {media_url} ({media_content_type})")

            if media_content_type == "application/pdf":
                incoming_msg = f"I have uploaded my salary slip via WhatsApp: {media_url}"
            else:
                incoming_msg = f"I have uploaded a document via WhatsApp: {media_url}"

        # Handle first message
        if not agent.conversation_history:
            reply_text = agent.start_conversation()
        else:
            reply_text = agent.process_message(incoming_msg)

        print(f"🤖 Replying with: {reply_text}")

        # --- ✅ IMPORTANT PART ---
        # Return TwiML so Twilio shows message immediately
        resp = MessagingResponse()

        # If a sanction letter has just been generated, try to attach it as media.
        # MasterAgent returns text like: "Sanction Letter Generated: path/to/file.pdf ..."
        media_url = None
        marker = "Sanction Letter Generated:"
        if marker in reply_text:
            try:
                after = reply_text.split(marker, 1)[1].strip()
                first_line = after.splitlines()[0].strip()
                pdf_path = first_line
                filename = os.path.basename(pdf_path)
                base_url = request.url_root.rstrip("/")
                media_url = f"{base_url}/sanction_letters/{filename}"
                print(f"📄 Attaching sanction letter for WhatsApp: {media_url}")
            except Exception as parse_err:
                print(f"⚠️ Could not parse sanction letter path from reply: {parse_err}")

        msg = resp.message(reply_text)
        if media_url:
            msg.media(media_url)

        return str(resp)

    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        resp = MessagingResponse()
        resp.message("Sorry! Something went wrong. Please try again later.")
        return str(resp)




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
