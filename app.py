from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import re
import openai

# ==========================
# OPENAI CONFIG
# ==========================
openai.api_key = os.getenv("OPENAI_API_KEY")

# ==========================
# GLOBALS
# ==========================
user_states = {}
user_data = {}

# ==========================
# FLASK APP
# ==========================
app = Flask(__name__)

# ==========================
# HELPER FUNCTIONS
# ==========================
def main_menu():
    return (
        "👋 Hevoi! Tinokugamuchirai ku *IvhuRedu* 🇿🇼\n\n"
        "Sarudza nhamba 👇🏽\n\n"
        "1️⃣ Kutanga Kuongorora Ivhu\n"
        "2️⃣ Kugadzirisa Ivhu Randakaongorora\n"
        "3️⃣ Ndinoda Rubatsiro\n"
        "4️⃣ Zvidzidzo Pamusoro PeIvhu\n"
        "5️⃣ Bvunza Mudhumeni Wedu\n"
        "6️⃣ Ongorora Ivhu Pasina pH"
    )

def calculate_dosage(ph, plot_size):
    if ph < 5.5:
        return {"dota": 2*plot_size, "anthill_soil": 2*plot_size, "mufudze": 1*plot_size}
    elif 5.5 <= ph <= 6.5:
        return {"mufudze": 1*plot_size}
    elif 6.6 <= ph <= 7.0:
        return {}
    elif 7.1 <= ph <= 8.0:
        return {"mufudze": 2*plot_size, "chicken_manure": 1*plot_size}
    elif 8.1 <= ph <= 9.0:
        return {"mufudze": 3*plot_size, "chicken_manure": 1*plot_size}
    return {}

def format_dosage_message(dosage):
    if not dosage:
        return "✅ Ivhu rako rakanaka parizvino."
    msg = "📊 *Dosage Yakakurudzirwa:*\n"
    for k, v in dosage.items():
        msg += f"• {k.replace('_',' ').title()}: {v} handfuls\n"
    return msg

def analyze_ph(message, user):
    match = re.search(r'ph\s*([0-9]+(\.[0-9]+)?)', message)
    if not match:
        return None
    ph = float(match.group(1))
    user_data.setdefault(user, {})['ph'] = ph
    user_states[user] = "awaiting_plot_size"
    return f"📊 pH = {ph}\nNyora saizi yemunda wako (m²)"

# ==========================
# 🔥 REAL AI PHOTO ANALYSIS
# ==========================
def ai_photo_analysis(photo_url, plot_size=10):
    try:
        prompt = (
            "Uri nyanzvi yezvekurima muZimbabwe.\n"
            "Tarisa mufananidzo weivhu kana chirimwa ichi.\n"
            "Tsanangura:\n"
            "1. Mamiriro evhu\n"
            "2. Hutano hwezvirimwa\n"
            "3. Fungidzira soil pH (ipa nhamba)\n"
            "4. Zano rekushandisa dota, mufudze, kana ivhu rechuru\n"
            "Pindura muShona."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": photo_url}}
                ]
            }],
            temperature=0.6
        )

        text = response["choices"][0]["message"]["content"]
        ph_match = re.search(r'([0-9]\.[0-9])', text)
        estimated_ph = float(ph_match.group(1)) if ph_match else 6.0
        dosage = calculate_dosage(estimated_ph, plot_size)

        return (
            "📸 *AI Yakaongorora Mufananidzo*\n\n"
            f"{text}\n\n"
            f"📊 Estimated pH: {estimated_ph}\n\n"
            f"{format_dosage_message(dosage)}"
        )

    except Exception:
        return "⚠️ Handina kukwanisa kuongorora mufananidzo. Edza zvakare nemufananidzo wakajeka."

# ==========================
# ROUTES
# ==========================
@app.route("/", methods=["GET"])
def home():
    return "IvhuRedu is running"

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    user = request.values.get("From")
    incoming = request.values.get("Body", "").strip().lower()
    num_media = int(request.values.get("NumMedia", 0))

    resp = MessagingResponse()
    msg = resp.message()
    state = user_states.get(user, "main_menu")

    if incoming in ["hi", "hello", "menu", "start", "makadini"]:
        user_states[user] = "main_menu"
        msg.body(main_menu())

    elif incoming == "6":
        user_states[user] = "q1"
        user_data[user] = {}
        msg.body("📝 Ruvara rweivhu?\n• yero\n• tsvukuruka\n• jecha")

    elif state == "q1":
        user_data[user]['soil_color'] = incoming
        user_states[user] = "q2"
        msg.body("🌱 Zvirimwa zviri kukura zvakanaka here?\n• hongu\n• kwete")

    elif state == "q2":
        user_data[user]['health'] = incoming
        user_states[user] = "q3"
        msg.body("📐 Nyora saizi yemunda wako (m²)")

    elif state == "q3" and incoming.isdigit():
        plot = int(incoming)
        estimated_ph = 5.5 if user_data[user]['health']=="kwete" else 6.8
        dosage = calculate_dosage(estimated_ph, plot)
        user_states[user] = "main_menu"
        msg.body(f"🤖 Estimated pH: {estimated_ph}\n{format_dosage_message(dosage)}")

    elif num_media > 0:
        photo_url = request.values.get("MediaUrl0")
        plot = user_data.get(user, {}).get("plot_size", 10)
        result = ai_photo_analysis(photo_url, plot)
        user_states[user] = "main_menu"
        msg.body(result + "\n\nNyora *MENU* kudzokera.")

    elif state == "awaiting_ph" and "ph" in incoming:
        msg.body(analyze_ph(incoming, user))

    elif state == "awaiting_plot_size" and incoming.isdigit():
        plot = int(incoming)
        ph = user_data[user]['ph']
        user_states[user] = "main_menu"
        msg.body(format_dosage_message(calculate_dosage(ph, plot)))

    else:
        msg.body(main_menu())

    return str(resp)

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)








