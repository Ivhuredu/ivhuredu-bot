from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import re

# ==========================
# GLOBALS
# ==========================
user_states = {}  # Stores current step for each user
user_lessons = {}
user_drink_lessons = {}

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
        "Tinokubatsira kuongorora uye kugadzirisa ivhu remunda wako.\n\n"
        "Sarudza nhamba 👇🏽\n\n"
        "1️⃣ Kutanga Kuongorora Ivhu\n"
        "2️⃣ Kugadzirisa Ivhu Randakaongorora\n"
        "3️⃣ Ndinoda Rubatsiro\n"
        "4️⃣ Zvidzidzo Pamusoro PeIvhu\n"
        "5️⃣ Bvunza Mudhumeni Wedu\n"
        "6️⃣ Ongorora Ivhu Pasina pH"
    )

def analyze_ph(message):
    match = re.search(r'ph\s*([0-9]+(\.[0-9]+)?)', message, re.IGNORECASE)
    if not match:
        return None

    ph = float(match.group(1))
    advice = ""

    # Dosage recommendations
    if ph < 5.5:
        advice = (
            f"📉 *Acidic Soil* (pH = {ph})\n\n"
            "Ivhu rako rine acid yakawandisa.\n"
            "Kurudzira:\n"
            "• Dota: 2–3 handfuls/m²\n"
            "• Anthill soil: 2 handfuls/m²\n"
            "• Mufudze wemombe wakaorera: 1–2 handfuls/m²\n"
            "Shandisa mwedzi mishoma usati wasima."
        )
    elif 5.5 <= ph <= 6.5:
        advice = (
            f"✅ *Good Soil* (pH = {ph})\n\n"
            "Ivhu rako rakanaka kuchibage.\n"
            "Kurudzira:\n"
            "• Mufudze: 1 handful/m² nguva nenguva\n"
        )
    elif 6.6 <= ph <= 7.0:
        advice = (
            f"🌿 *Ideal Soil* (pH = {ph})\n\n"
            "Ivhu rako rakanaka. Ramba uchichengetedza organic matter."
        )
    elif 7.1 <= ph <= 8.0:
        advice = (
            f"📈 *Slightly Alkaline Soil* (pH = {ph})\n\n"
            "Kurudzira:\n"
            "• Mufudze: 2 handfuls/m²\n"
            "• Chicken manure: 1 handful/m²\n"
            "Dzivisa ash yakawandisa."
        )
    elif 8.1 <= ph <= 9.0:
        advice = (
            f"⚠️ *Alkaline Soil* (pH = {ph})\n\n"
            "Ivhu rako rine alkaline yakati wandei.\n"
            "• Mufudze: 3 handfuls/m²\n"
            "• Chicken manure: 1 handful/m²\n"
            "Dzivisa ash nemvura yakawanda."
        )
    else:
        advice = (
            f"❗ *Very Alkaline Soil* (pH = {ph})\n\n"
            "Ivhu rako rine alkaline yakanyanya.\n"
            "Tinokurudzira kutsvaga rubatsiro rwe nyanzwi dzezvekurima.\n"
            "Nyora *3* kuti uwane rubatsiro."
        )

    return advice

# ==========================
# ROUTES
# ==========================
@app.route("/", methods=["GET"])
def home():
    return "IvhuRedu is running"

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    user = request.values.get("From")
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Get user state
    state = user_states.get(user, "main_menu")

    # ==========================
    # MAIN MENU TRIGGERS
    # ==========================
    if incoming_msg in ["hi", "hello", "menu", "start", "makadini"]:
        user_states[user] = "main_menu"
        msg.body(main_menu())

    # ==========================
    # OPTION 1: Kuongorora pH
    # ==========================
    elif incoming_msg == "1":
        user_states[user] = "awaiting_examine_start"
        msg.body(
            "🧼 *KUONGORORA pH YEIVHU RAKO*\n\n"
            "Zvinodiwa:\n"
            "✔ 2.5L mvura yakavidzwa yopora\n"
            "✔ 5L container\n"
            "✔ Mugoti\n"
            "✔ Badza\n"
            "✔ pH Testing Paper\n\n"
            "Nyora *ONGORORA* kuti ndikuudze ma steps"
        )

    # ==========================
    # START EXAMINE
    # ==========================
    elif state == "awaiting_examine_start" and incoming_msg == "ongorora":
        user_states[user] = "awaiting_ph"
        msg.body(
            "✅ *ONGORORA IVHU RAKO*\n\n"
            "1️⃣ Chera ivhu 15–20cm\n"
            "2️⃣ Sanganisa 1L ivhu + 2.5L mvura\n"
            "3️⃣ Siya 15–20 min\n"
            "4️⃣ Pima pH ne pH paper\n\n"
            "Nyora pH yawawana (semuenzaniso: pH 5.5)"
        )

    # ==========================
    # OPTION 2: Kugadzirisa ivhu
    # ==========================
    elif incoming_msg == "2":
        user_states[user] = "awaiting_ph"
        msg.body(
            "🥤 *KUGADZIRISA IVHU*\n\n"
            "Kana uchiziva pH nyora pH yacho (semuenzaniso: pH 5.5)\n"
            "Kana usingaizivi nyora *1* kuti tibatsire"
        )

    # ==========================
    # OPTION 3: Rubatsiro
    # ==========================
    elif incoming_msg == "3":
        user_states[user] = "awaiting_support"
        msg.body(
            "💰 *NDINODA RUBATSIRO*\n\n"
            "Nyanzwi dzedu dzinokubatsira kugadzirisa ivhu rako.\n\n"
            "Nzira dzekubhadhara:\n"
            "• EcoCash\n• OneMoney\n• Mukuru\n• Bank\n\n"
            "Nyora *PAY* kuti uwane quotation"
        )

    # ==========================
    # OPTION 4: Lessons
    # ==========================
    elif incoming_msg == "4":
        msg.body(
            "🎁 *ZVIDZIDZO PAMUSORO PEIVHU*\n\n"
            "Ivhu rinofanira kuva ne pH yakakodzera kuti chibage chikure zvakanaka.\n"
            "Kana pH yakakwira kana kudzika zvakanyanya, zvirimwa hazvikuri.\n\n"
            "Nyora *1* kutanga kuongorora kana *2* kana uchiziva pH.\n"
            "Nyora *MENU* kudzokera pekutanga."
        )

    # ==========================
    # OPTION 6: No-pH examine
    # ==========================
    elif incoming_msg == "6":
        user_states[user] = "examining"
        msg.body("Kana usingazivi pH, nyora *EXAMINE*")

    elif state == "examining" and incoming_msg in ["examine", "kwete"]:
        msg.body("Rudzii rwemasora ruri mumunda wako? (yero, tsvukuruka, hazvikuri)")

    elif state == "examining" and incoming_msg in ["grass type", "photo of grass"]:
        msg.body(
            "Ivhu rakaita sei? (jecha, chinhare, rukangarabwe)\n"
            "Tumira mufananidzo kana tsananguro."
        )

    elif state == "examining" and incoming_msg in ["soil type", "photo of ground"]:
        msg.body(
            "Zvirimwa zvine utano here kana zviri zveyero?\n"
            "Tumira mufananidzo."
        )

    elif state == "examining" and incoming_msg in ["tsvukuruka", "yero", "hazvikuri", "photo of yellow grass"]:
        user_states[user] = "main_menu"
        msg.body(
            "Ndatenda. Tiri kuongorora ivhu rako.\n\n"
            "Tapota tumira:\n"
            "• Zita\n• Kwaunogara\n• Phone number\n\n"
            "Mhinduro dzichadzoka mumaawa asingapfuuri 48."
        )

    # ==========================
    # PAYMENT
    # ==========================
    elif incoming_msg == "pay":
        user_states[user] = "awaiting_payment"
        msg.body(
            "💳 *PAYMENT DETAILS*\n\n"
            "EcoCash: 0773 208904\n"
            "Zita: Beloved Nkomo\n\n"
            "Tumira proof mushure mekubhadhara."
        )

    # ==========================
    # PH INTELLIGENCE
    # ==========================
    elif state == "awaiting_ph" and "ph" in incoming_msg:
        result = analyze_ph(incoming_msg)
        user_states[user] = "main_menu"
        if result:
            msg.body(result)
        else:
            msg.body(
                "Ndakundikana kunzwisisa pH yawatumira.\n"
                "Nyora seizvi: pH 5.5 kana ph6.8"
            )

    # ==========================
    # DEFAULT
    # ==========================
    else:
        user_states[user] = "main_menu"
        msg.body(main_menu())

    return str(resp)

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


