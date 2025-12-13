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
###1. Start the WhatsApp Flask Server

Open a terminal in the backend folder and run:
```bash
python whatsapp_bot.py
```
The server will start on:
http://localhost:5000
Keep this terminal running.
