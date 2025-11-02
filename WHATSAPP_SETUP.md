# 📱 WhatsApp Integration Setup Guide

## Overview
This guide will help you add WhatsApp as a chat channel to your BFSI loan chatbot. Users can interact with your bot directly through WhatsApp while your existing backend (MasterAgent) handles all the logic.

---



✅ **WhatsApp webhook server** (`whatsapp_bot.py`)
- Flask server to receive/send WhatsApp messages
- Session management for multiple concurrent users
- Integration with your existing `MasterAgent`

✅ **Multi-user support**
- Each WhatsApp user gets their own conversation session
- Sessions auto-expire after 30 minutes of inactivity

✅ **Seamless backend integration**
- Your existing agents (Sales, Verification, Credit, etc.) work as-is
- No changes needed to your core logic

---



### 1. Twilio Account (Free Trial Available)
- Sign up at: https://www.twilio.com/try-twilio
- You'll get $15 free credit
- Free trial limitations:
  - Can only send messages to verified phone numbers
  - Messages include "Sent from your Twilio trial account" footer

### 2. Python Packages
Already added to `requirements.txt`:
```
flask
twilio
```

---

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
pip install flask twilio
```

Or reinstall from requirements:
```bash
pip install -r requirements.txt
```

---

### Step 2: Get Twilio Credentials

1. **Sign up for Twilio**: https://www.twilio.com/try-twilio

2. **Get your credentials** from the Twilio Console:
   - **Account SID**: Found on your dashboard
   - **Auth Token**: Found on your dashboard (click to reveal)

3. **Enable WhatsApp Sandbox**:
   - Go to: Console → Messaging → Try it out → Send a WhatsApp message
   - You'll see a sandbox number like: `+1 415 523 8886`
   - Send a WhatsApp message to that number with the code shown (e.g., "join ABC-123")
   - This connects your phone to the sandbox

4. **Get the WhatsApp number**:
   - Format: `whatsapp:+14155238886` (example)
   - Copy this from the Twilio Sandbox settings

---

### Step 3: Configure Environment Variables

Update your `.env` file:

```env
# Add your Groq API key here
GROQ_API_KEY=your_groq_api_key_here

# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

Replace the placeholder values with your actual credentials.

---

### Step 4: Expose Your Server to the Internet (ngrok)

Twilio needs to send webhooks to your server, so you need a public URL.

#### Option A: Using ngrok (Recommended for Testing)

1. **Download ngrok**: https://ngrok.com/download

2. **Install and authenticate**:
   ```bash
   ngrok authtoken YOUR_NGROK_AUTH_TOKEN
   ```

3. **Start your Flask server** (in one terminal):
   ```bash
   python whatsapp_bot.py
   ```

4. **Expose it with ngrok** (in another terminal):
   ```bash
   ngrok http 5000
   ```

5. **Copy the ngrok URL**:
   - You'll see something like: `https://abc123.ngrok.io`
   - This is your public webhook URL

#### Option B: Deploy to Cloud (Production)
- Deploy to Heroku, Railway, Render, or AWS
- Use the deployed URL as your webhook

---

### Step 5: Configure Twilio Webhook

1. Go to **Twilio Console → Messaging → Settings → WhatsApp sandbox settings**

2. Set the **"When a message comes in"** webhook:
   ```
   https://abc123.ngrok.io/webhook
   ```
   - Replace `abc123.ngrok.io` with your actual ngrok URL
   - Make sure to append `/webhook` at the end

3. Set HTTP method to **POST**

4. Click **Save**

---

### Step 6: Test Your WhatsApp Bot! 🎉

1. Send a WhatsApp message to your Twilio sandbox number
2. The bot should respond with the welcome message
3. Start a loan application conversation!

#### Test Flow Example:
```
You: Hi
Bot: Hello! 👋 Welcome to Tata Capital...

You: 9876543210
Bot: Thank you! I found an existing profile...

You: Yes
Bot: Great! I found your profile, Rajesh Kumar...
```

---

## 🏗️ Architecture

```
WhatsApp User
    ↓
Twilio WhatsApp API
    ↓
Flask Webhook (whatsapp_bot.py)
    ↓
MasterAgent (main.py)
    ↓
Specialized Agents (Sales, Credit, etc.)
    ↓
Response back through same path
```

---

## 🔥 Features

### ✅ What Works
- ✅ Multi-user concurrent conversations
- ✅ Session management (30-min timeout)
- ✅ Full loan application flow
- ✅ All agent functionalities (Sales, Verification, Credit, etc.)
- ✅ Restart command (`restart`, `reset`, `start over`)

### 🚧 Limitations & Future Enhancements

1. **PDF Sanction Letters**
   - Currently: Text notification only
   - Future: Upload PDF to cloud storage (S3/Azure Blob) and send via WhatsApp
   - Code placeholder already added in `whatsapp_bot.py`

2. **Session Storage**
   - Currently: In-memory (lost on server restart)
   - Production: Use Redis or database

3. **Document Upload**
   - Your bot asks users to upload salary slips
   - WhatsApp can receive media - extend the webhook to handle it!

---

## 📱 Available Commands

Users can send these commands anytime:

| Command | Action |
|---------|--------|
| `restart` | Start a new conversation |
| `reset` | Same as restart |
| `start over` | Same as restart |

---

## 🛠️ Troubleshooting

### Bot not responding?
1. Check if Flask server is running
2. Check if ngrok is running and URL is correct
3. Verify webhook URL in Twilio Console
4. Check server logs for errors

### "Missing credentials" error?
- Make sure all values in `.env` are set correctly
- Restart the Flask server after updating `.env`

### Messages delayed?
- Free Twilio sandbox can have delays
- Upgrade to a production WhatsApp number for faster delivery

### Can't send to friends?
- Twilio trial: Only verified numbers work
- Add their numbers in Twilio Console → Phone Numbers → Verified Caller IDs
- Or upgrade to paid account

---

## 🚀 Going to Production

### 1. Get WhatsApp Business API Access
- Not the sandbox - real WhatsApp API
- Options:
  - Twilio WhatsApp Business API (Paid)
  - Meta Cloud API (Free tier available)
  - 360dialog, Infobip, etc.

### 2. Deploy Your Server
- Use a cloud platform (Heroku, Railway, AWS, Azure)
- Set up environment variables on the platform
- Update Twilio webhook to production URL

### 3. Add PDF Sending
- Upload PDFs to AWS S3 / Azure Blob Storage
- Generate public URLs
- Send via Twilio media_url parameter

Example code (already in `whatsapp_bot.py`):
```python
# TODO: Upload to S3
s3_url = upload_to_s3(pdf_path)
send_whatsapp_message(phone, "Your sanction letter:", media_url=s3_url)
```

### 4. Use Redis for Sessions
- Install Redis: `pip install redis`
- Replace in-memory `sessions` dict with Redis storage

---

## 📊 Monitoring Active Sessions

Visit `http://localhost:5000/status` to see:
- Number of active sessions
- Connected phone numbers

---

## 🎉 You're All Set!

Your BFSI chatbot now works on **both** channels:
1. **CLI** (original) - Run `python main.py`
2. **WhatsApp** (new) - Message your Twilio number

Both use the same backend logic! 🚀

---

## 📞 Support

If you run into issues:
1. Check Flask server logs
2. Check Twilio debugger: Console → Monitor → Logs → Errors
3. Test webhook manually: `curl -X POST http://localhost:5000/webhook`

---

**Happy Building! 🏦💬**
