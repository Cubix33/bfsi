# AI Loan Assistant – WhatsApp & Website Chatbot

This project is an AI-powered loan origination system that allows users to apply for loans via **Website Chat** or **WhatsApp**.  
Both channels connect to a **single Master Agent** that orchestrates verification, risk assessment, underwriting, and document generation.

---

## Features

- Website chat and WhatsApp chat support  
- AI-driven conversation using Groq LLM  
- KYC and document verification  
- Credit & risk assessment using XGBoost  
- Automated loan approval or rejection  
- Sanction letter PDF generation  
- PDF delivery via WhatsApp or website download  

---

## Tech Stack

- **Backend:** Flask (Python)
- **AI:** Groq LLM
- **Risk Model:** XGBoost
- **Messaging:** Twilio WhatsApp API
- **Tunneling:** Ngrok
- **PDF Generation:** ReportLab
- **Document Parsing:** OCR / NLP
- **Frontend:** React + TypeScript (Vite)

---

## Project Architecture (High Level)

- Website Chat → Flask API  
- WhatsApp → Twilio → Flask Webhook  
- Flask → Master Agent  
- Master Agent → Specialized Agents  
- Agents → Backend Systems  
- Output → Website / WhatsApp  

---

## Environment Setup

Create a `.env` file in the backend directory:

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
GROQ_API_KEY=your_groq_api_key
```

## Running the WhatsApp Bot
Step 1: Start the Flask WhatsApp Server
``` python whatsapp_bot.py
```

Server runs on:
http://localhost:5000

Step 2: Expose Server Using Ngrok
ngrok http 5000
Copy the generated HTTPS ngrok URL.

Step 3: Configure Twilio Webhook
Twilio Console → Messaging → WhatsApp Sandbox
Set WHEN A MESSAGE COMES IN to:
https://<ngrok-url>/webhook
Save changes.

Step 4: Join WhatsApp Sandbox
Send this message to the Twilio sandbox number:
join <sandbox-code>
eg : join cave-pool
You will receive a confirmation message.

Using the WhatsApp Bot (User Flow)
User sends Hi
Bot asks for phone number
Loan amount, purpose, income collected
KYC documents requested and validated
Credit score fetched and risk model executed
Loan approved or rejected
Sanction letter PDF generated
PDF delivered via WhatsApp or website
