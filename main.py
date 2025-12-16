# main.py

from fastapi import FastAPI, Request
import requests, os
from dotenv import load_dotenv
from logic import analyze_input

load_dotenv()

app = FastAPI()
user_sessions = {}

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = os.getenv("PHONE_NUMBER_ID")

# Verification endpoint for WhatsApp
@app.get("/webhook")
def verify(mode: str, challenge: str, token: str):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge
    return "Verification failed"

# Endpoint for incoming WhatsApp messages
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        text = msg["text"]["body"]
        sender = msg["from"]
    except:
        return {"status": "ignored"}

    if sender not in user_sessions:
        user_sessions[sender] = {}

    reply = analyze_input(user_sessions[sender], text)
    send_message(sender, reply)
    return {"status": "ok"}

# Function to send message back to WhatsApp
def send_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)
