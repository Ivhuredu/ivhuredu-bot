
   from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import re

# ==========================
# GLOBALS
# ==========================
user_states = {}  # Stores current step for each user
user_data = {}    # Stores pH, plot size, photo URLs per user

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

def calculate_dosage(ph, plot_size):
    """Return recommended handfuls per fertilizer type based on plot size (m²)"""
    dosage = {}
    if ph < 5.5:
        dosage = {
            "dota": 2 * plot_size,  # 2 handfuls/m²
            "anthill_soil": 2 * plot_size,
            "mufudze": 1 * plot_size
        }
    elif 5.5 <= ph <= 6.5:
        dosage = {"mufudze": 1 * plot_size}
    elif 6.6 <= ph <= 7.0:
        dosage = {}  # Ideal, no extra
    elif 7.1 <= ph <= 8.0:
        dosage = {"mufudze": 2 * plot_size, "chicken_manure": 1 * plot_size}
    elif 8.1 <= ph <= 9.0:
        dosage = {"mufudze": 3 * plot_size, "chicken_manure": 1 * plot_size}
    else:
        dosage = {}
    return dosage

def format_dosage_message(dosage):
    if not dosage:
        return "Ivhu rako rakanaka, hapana zvekuchinja zvakakosha panguva ino."
    msg = "📊 *Recommended Dosage for Your Plot:*\n"
    for key, value in dosage.items():
        msg += f"• {key.replace('_', ' ').title()}: {value} handfuls\n"
    return msg

def analyze_ph(message, user):
    match = re.search(r'ph\s*([0-9]+(\.[0-9]+)?)', message, re.IGNORECASE)
    if not match:
        return None

    ph = float(match.group(1))
    user_data[user] = user_data.get(user, {})
    user_data[user]['ph'] = ph

    # Ask for plot size next
    user_states[user] = "awaiting_plot_size"
    return (
        f"📊 Ivhu rako rine pH = {ph}\n"
        "Nyora saizi yemunda wako (m²) kuti ndikupe dosage chaiyo. "
        "Semuyenzaniso: 50"
    )

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
    num_media = int(request.values.get("NumMedia", 0))
    resp = MessagingResponse()
    msg = resp.message()

    state = user_states.get(user, "main_menu")

    # --------------------------
    # MAIN MENU
    # --------------------------
    if incoming_msg in ["hi", "hello", "menu", "start", "makadini"]:
        user_states[user] = "main_menu"
        msg.body(main_menu())

    # --------------------------
    # OPTION 1: Kuongorora pH
    # --------------------------
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

    # START EXAMINE
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

    # --------------------------
    # OPTION 2: Kugadzirisa ivhu
    # --------------------------
    elif incoming_msg == "2":
        user_states[user] = "awaiting_ph"
        msg.body(
            "🥤 *KUGADZIRISA IVHU*\n\n"
            "Kana uchiziva pH nyora pH yacho (semuenzaniso: pH 5.5)\n"
            "Kana usingaizivi nyora *1* kuti tibatsire"
        )

    # --------------------------
    # OPTION 3: Rubatsiro
    # --------------------------
    elif incoming_msg == "3":
        user_states[user] = "awaiting_support"
        msg.body(
            "💰 *NDINODA RUBATSIRO*\n\n"
            "Nyanzwi dzedu dzinokubatsira kugadzirisa ivhu rako.\n\n"
            "Nzira dzekubhadhara:\n"
            "• EcoCash\n• OneMoney\n• Mukuru\n• Bank\n\n"
            "Nyora *PAY* kuti uwane quotation"
        )

    # --------------------------
    # LESSONS
    # --------------------------
    elif incoming_msg == "4":
        msg.body(
            "🎁 *ZVIDZIDZO PAMUSORO PEIVHU*\n\n"
            "Ivhu rinofanira kuva ne pH yakakodzera kuti chibage chikure zvakanaka.\n"
            "Nyora *1* kutanga kuongorora kana *2* kana uchiziva pH.\n"
            "Nyora *MENU* kudzokera pekutanga."
        )

    # --------------------------
    # OPTION 6: No-pH examine
    # --------------------------
    elif incoming_msg == "6":
        user_states[user] = "examining"
        msg.body("Kana usingazivi pH, nyora *EXAMINE*")

    # EXAMINE FLOW
    elif state == "examining" and incoming_msg in ["examine", "kwete"]:
        msg.body("Rudzii rwemasora ruri mumunda wako? (yero, tsvukuruka, hazvikuri)")

    # --------------------------
    # PHOTO UPLOAD HANDLING
    # --------------------------
    elif num_media > 0:
        media_urls = [request.values.get(f"MediaUrl{i}") for i in range(num_media)]
        user_data[user] = user_data.get(user, {})
        user_data[user]['photos'] = user_data[user].get('photos', []) + media_urls
        msg.body(
            f"Ndatenda! Mufananidzo wako watambirwa. "
            "Nyanzwi wedu achaongorora mumazuva 2 uye achakupa mhinduro."
        )

    # --------------------------
    # PH INPUT
    # --------------------------
    elif state == "awaiting_ph" and "ph" in incoming_msg:
        response = analyze_ph(incoming_msg, user)
        msg.body(response)

    # --------------------------
    # PLOT SIZE INPUT
    # --------------------------
    elif state == "awaiting_plot_size" and incoming_msg.isdigit():
        plot_size = int(incoming_msg)
        user_data[user]['plot_size'] = plot_size
        ph = user_data[user].get('ph', None)
        if ph:
            dosage = calculate_dosage(ph, plot_size)
            user_states[user] = "main_menu"
            msg.body(format_dosage_message(dosage))
        else:
            msg.body("Ndatadza kuwana pH yako. Nyora pH zvakare (semuenzaniso: pH 5.5)")

    # --------------------------
    # PAYMENT
    # --------------------------
    elif incoming_msg == "pay":
        user_states[user] = "awaiting_payment"
        msg.body(
            "💳 *PAYMENT DETAILS*\n\n"
            "EcoCash: 0773 208904\n"
            "Zita: Beloved Nkomo\n\n"
            "Tumira proof mushure mekubhadhara."
        )

    # --------------------------
    # DEFAULT
    # --------------------------
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




