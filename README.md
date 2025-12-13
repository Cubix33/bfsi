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

## 1. Start the WhatsApp Flask Server

Open a terminal in the backend folder and run:

python whatsapp_bot.py

The server will start on:

http://localhost:5000

Keep this terminal running.

---

## 2. Expose the Server Using Ngrok

Open a new terminal and run:

ngrok http 5000

Ngrok will generate a public HTTPS URL like:

https://xxxx.ngrok-free.dev

Copy this URL.

---

## 3. Configure Twilio WhatsApp Webhook

1. Open **Twilio Console**
2. Go to:
   - Messaging  
   - Try it out  
   - WhatsApp Sandbox
3. Find **WHEN A MESSAGE COMES IN**
4. Paste the webhook URL:

https://<ngrok-url>/webhook

Example:

https://xxxx.ngrok-free.dev/webhook

5. Save the changes

---

## 4. Join the WhatsApp Sandbox

Send this message to the Twilio sandbox WhatsApp number:

join <sandbox-code>

Example:

join cave-pool

You will receive a confirmation message.

---

## 5. Using the WhatsApp Bot (User Flow)

- User sends **Hi** on WhatsApp  
- Bot creates a new session  
- Bot asks for phone number and validates it  
- Bot collects:
  - Loan amount  
  - Loan purpose  
  - Monthly income  
- Bot requests KYC documents  
- Documents are verified  
- Credit score is fetched  
- Risk model (XGBoost) is executed  
- Loan is approved or rejected  

If approved:
- Sanction letter PDF is generated  
- PDF is sent via WhatsApp or provided as a website download link  

---
Loan approved or rejected
Sanction letter PDF generated
PDF delivered via WhatsApp or website
