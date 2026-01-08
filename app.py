from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import re

# ==========================
# GLOBALS
# ==========================
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
    # Match pH numbers like "ph 5.5", "ph6.8", "PH 7.2"
    match = re.search(r'ph\s*([0-9]+(\.[0-9]+)?)', message, re.IGNORECASE)
    if not match:
        return None

    ph = float(match.group(1))

    if ph < 5.5:
        return (
            f"📉 *pH = {ph} (Acidic)*\n\n"
            "Ivhu rako rine acid yakawandisa.\n\n"
            "Zvinokurudzirwa:\n"
            "• Isa *dota* zvishoma nezvishoma\n"
            "• Ivhu rechuru (anthill soil)\n"
            "• Regedza manyowa ehuku akawandisa\n\n"
            "Izvi zviite mwedzi mishoma usati wasima."
        )
    elif 5.5 <= ph <= 7.0:
        return (
            f"✅ *pH = {ph} (Yakanakira Chibage)*\n\n"
            "Ivhu rako rakanaka kuchibage.\n\n"
            "Kurudziro:\n"
            "• Chengetedza nemufudze wemombe wakaorera\n"
            "• Wedzera organic matter nguva nenguva\n"
            "• Dzivisa dota rakawandisa"
        )
    elif 7.0 < ph <= 8.0:
        return (
            f"📈 *pH = {ph} (Alkaline)*\n\n"
            "Ivhu rako rine alkaline yakati wandei.\n\n"
            "Zvinokurudzirwa:\n"
            "• Mufudze wemombe wakawanda\n"
            "• Manyowa ehuku (zvishoma)\n"
            "• Regedza dota"
        )
    else:
        return (
            f"⚠️ *pH = {ph} (Alkaline Yakanyanya)*\n\n"
            "Ivhu rako rine alkaline yakanyanyisa.\n"
            "Tinokurudzira rubatsiro rwenyanzwi.\n\n"
            "Nyora *3* kana uchida kubatsirwa."
        )

# ==========================
# ROUTES
# ==========================
@app.route("/", methods=["GET"])
def home():
    return "IvhuRedu is running"

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # --------------------------
    # MAIN MENU TRIGGERS
    # --------------------------
    if incoming_msg in ["hi", "hello", "menu", "start", "makadini"]:
        msg.body(main_menu())

    # --------------------------
    # OPTION 1: Kuongorora pH
    # --------------------------
    elif incoming_msg == "1":
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

    # --------------------------
    # OPTION 2: Kugadzirisa ivhu
    # --------------------------
    elif incoming_msg == "2":
        msg.body(
            "🥤 *KUGADZIRISA IVHU*\n\n"
            "Kana uchiziva pH nyora pH yacho (semuenzaniso: pH 5.5)\n"
            "Kana usingaizivi nyora *1*"
        )

    # --------------------------
    # OPTION 3: Rubatsiro
    # --------------------------
    elif incoming_msg == "3":
        msg.body(
            "💰 *NDINODA RUBATSIRO*\n\n"
            "Nyanzwi dzedu dzinokubatsira kugadzirisa ivhu rako.\n\n"
            "Nzira dzekubhadhara:\n"
            "• EcoCash\n"
            "• OneMoney\n"
            "• Mukuru\n"
            "• Bank\n\n"
            "Nyora *PAY* kuti uwane quotation"
        )

    # --------------------------
    # OPTION 4: Lessons
    # --------------------------
    elif incoming_msg == "4":
        msg.body(
            "🎁 *ZVIDZIDZO PAMUSORO PEIVHU*\n\n"
            "Ivhu rinofanira kuva ne pH yakakodzera kuti chibage chikure zvakanaka.\n"
            "Kana pH yakakwira kana kudzika zvakanyanya, zvirimwa hazvikuri.\n\n"
            "Nyora *1* kutanga kuongorora kana *2* kana uchiziva pH.\n"
            "Nyora *MENU* kudzokera pekutanga."
        )

    # --------------------------
    # ONGORA FLOW
    # --------------------------
    elif incoming_msg == "ongorora":
        msg.body(
            "✅ *ONGORORA IVHU RAKO*\n\n"
            "1️⃣ Chera ivhu 15–20cm\n"
            "2️⃣ Sanganisa 1L ivhu + 2.5L mvura\n"
            "3️⃣ Siya 15–20 min\n"
            "4️⃣ Pima pH ne pH paper\n\n"
            "Nyora pH yawawana (semuenzaniso: pH 5.5)"
        )

    # --------------------------
    # OPTION 6: No-pH examine
    # --------------------------
    elif incoming_msg == "6":
        msg.body("Kana usingazivi pH, nyora *EXAMINE*")

    elif incoming_msg in ["examine", "kwete"]:
        msg.body(
            "Rudzii rwemasora ruri mumunda wako? (yero, tsvukuruka, hazvikuri)"
        )

    elif incoming_msg in ["grass type", "photo of grass"]:
        msg.body(
            "Ivhu rakaita sei? (jecha, chinhare, rukangarabwe)\n"
            "Tumira mufananidzo kana tsananguro."
        )

    elif incoming_msg in ["soil type", "photo of ground"]:
        msg.body(
            "Zvirimwa zvine utano here kana zviri zveyero?\n"
            "Tumira mufananidzo."
        )

    elif incoming_msg in ["tsvukuruka", "yero", "hazvikuri", "photo of yellow grass"]:
        msg.body(
            "Ndatenda. Tiri kuongorora ivhu rako.\n\n"
            "Tapota tumira:\n"
            "• Zita\n"
            "• Kwaunogara\n"
            "• Phone number\n\n"
            "Mhinduro dzichadzoka mumaawa asingapfuuri 48."
        )

    # --------------------------
    # PAYMENT
    # --------------------------
    elif incoming_msg == "pay":
        msg.body(
            "💳 *PAYMENT DETAILS*\n\n"
            "EcoCash: 0773 208904\n"
            "Zita: Beloved Nkomo\n\n"
            "Tumira proof mushure mekubhadhara."
        )

    # --------------------------
    # pH INTELLIGENCE
    # --------------------------
    elif "ph" in incoming_msg:
        result = analyze_ph(incoming_msg)
        if result:
            msg.body(result)
        else:
            msg.body(
                "Ndakundikana kunzwisisa pH yawatumira.\n"
                "Nyora seizvi: pH 5.5 kana ph6.8"
            )

    # --------------------------
    # DEFAULT: main menu
    # --------------------------
    else:
        msg.body(main_menu())

    return str(resp)

# ==========================
# RUN APP
# ==========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
