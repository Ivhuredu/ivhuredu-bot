from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

user_lessons = {}
user_drink_lessons = {}

app = Flask(__name__)

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

@app.route("/", methods=["GET"])
def home():
    return "IvhuRedu is running"

@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # MAIN MENU
    if incoming_msg in ["hi", "hello", "menu", "start", "makadini"]:
        msg.body(main_menu())

    # OPTION 1
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

    # OPTION 2
    elif incoming_msg == "2":
        msg.body(
            "🥤 *KUGADZIRISA IVHU*\n\n"
            "Kana uchiziva pH nyora pH yacho (semuenzaniso: pH 5.5)\n"
            "Kana usingaizivi nyora *1*"
        )

    # OPTION 3
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

    # OPTION 4
    elif incoming_msg == "4":
        msg.body(
            "🎁 *ZVIDZIDZO PAMUSORO PEIVHU*\n\n"
            "Ivhu rinofanira kuva ne pH yakakodzera kuti chibage chikure zvakanaka.\n"
            "Kana pH yakakwira kana kudzika zvakanyanya, zvirimwa hazvikuri.\n\n"
            "Nyora *1* kutanga kuongorora kana *2* kana uchiziva pH.\n"
            "Nyora *MENU* kudzokera pekutanga."
        )

    # ONGORA STEPS
    elif incoming_msg == "ongorora":
        msg.body(
            "✅ *ONGORORA IVHU RAKO*\n\n"
            "1️⃣ Chera ivhu 15–20cm\n"
            "2️⃣ Sanganisa 1L ivhu + 2.5L mvura\n"
            "3️⃣ Siya 15–20 min\n"
            "4️⃣ Pima pH ne pH paper\n\n"
            "Nyora pH yawawana (pH 5.5)"
        )

    # OPTION 6
    elif incoming_msg == "6":
        msg.body(
            "Kana usingazivi pH, nyora *EXAMINE*"
        )

    # EXAMINE FLOW
    elif incoming_msg == "examine" or incoming_msg == "kwete":
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

    # PAYMENT
    elif incoming_msg == "pay":
        msg.body(
            "💳 *PAYMENT DETAILS*\n\n"
            "EcoCash: 0773 208904\n"
            "Zita: Beloved Nkomo\n\n"
            "Tumira proof mushure mekubhadhara."
        )

    else:
        msg.body(main_menu())

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


