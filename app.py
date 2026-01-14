from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os, re, base64, requests
from openai import OpenAI

# ==========================
# OPENAI CONFIG
# ==========================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
# MAIN MENU
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

# ==========================
# DOSAGE & PH FUNCTIONS
# ==========================
def calculate_dosage(ph, plot_size=10):
    """Return recommended handfuls per fertilizer type based on ~10m²"""
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
    msg = "📊 *Dosage Yakakurudzirwa (~10m²):*\n"
    for k, v in dosage.items():
        msg += f"• {k.replace('_',' ').title()}: {v} handfuls\n"
    return msg

def analyze_ph(message, user):
    match = re.search(r'ph\s*([0-9]+(\.[0-9]+)?)', message)
    if not match:
        return "⚠️ Ndapota nyora pH nenzira yakadai: pH 5.5"
    ph = float(match.group(1))
    user_data.setdefault(user, {})['ph'] = ph
    user_states[user] = "main_menu"

    # Give full explanation + advice per 10m²
    advice = ""
    if ph < 5.5:
        advice = "Ivhu rako rine acidity yakanyanya (acidic). Zvichaita kuti zvirimwa zvikure zvishoma. Isa dota, anthill soil, uye mufudze zvishoma."
    elif 5.5 <= ph <= 6.5:
        advice = "Ivhu rako rakanaka kune zvirimwa zvakawanda. Chengetedza nemufudze wemombe uye organic matter."
    elif 6.6 <= ph <= 7.0:
        advice = "Ivhu rako rakanaka uye rakaringana. Hapana zvinokosha zvekushandisa panguva ino."
    elif 7.1 <= ph <= 8.0:
        advice = "Ivhu rako rine alkaline yakati wandei. Shandisa mufudze wemombe uye zvishoma zve manyowa ehuku."
    else:
        advice = "Ivhu rako rine alkaline yakanyanya. Rubatsiro rwenyanzvi runokurudzirwa."

    dosage = calculate_dosage(ph)
    return f"📊 pH = {ph}\n{advice}\n\n{format_dosage_message(dosage)}"

# ==========================
# OPTION 6: 7 GUIDED QUESTIONS (Shona)
# ==========================
OPTION6_QUESTIONS = [
    {"field":"soil_texture","question":"📝 Q1: Ndeipi mhando yevhu riri mumunda wako?\n• jecha\n• musanganiswa\n• ivhu rakaonda/rakakora"},
    {"field":"soil_color","question":"📝 Q2: Ivhu rako rine ruvara rwakadii kana raitaoma?\n• tsvuku\n• dema\n• yero\n• chena/pale"},
    {"field":"drainage","question":"📝 Q3: Mvura inonyura sei mumunda pashure pemvura?\n• inonyura nekukurumidza\n• inogara kwechinguva\n• inogara kwenguva refu"},
    {"field":"leaf_yellowing","question":"📝 Q4: Mashizha ezvirimwa ari yero here?\n• hongu, ekare\n• hongu, matsva\n• kwete"},
    {"field":"crop_growth","question":"📝 Q5: Zvirimwa zviri kukura sei zvichienzaniswa nenguva yapfuura?\n• zviri nani\n• zvakafanana\n• zvashata"},
    {"field":"fertilizer_history","question":"📝 Q6: Wakamboshandisa fertilizer kana manyowa here?\n• hapana\n• manyowa emombe\n• manyowa ehuku\n• fertilizer yemakemikari"},
    {"field":"years_cultivated","question":"📝 Q7: Wakadyara mumunda uyu kwemakore mangani uchiramba uchidyara?\n• < 3 makore\n• 3–10 makore\n• > 10 makore"}
]

# ==========================
# AI PHOTO ANALYSIS
# ==========================
def ai_photo_analysis(photo_url, plot_size=10):
    try:
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        img_response = requests.get(photo_url, auth=(twilio_sid, twilio_token), timeout=10)
        if img_response.status_code != 200:
            return "❌ Mufananidzo haukwanisi kuverengwa. Edza zvakare."

        image_base64 = base64.b64encode(img_response.content).decode("utf-8")
        prompt = (
            "Uri nyanzvi yezvekurima muZimbabwe.\n"
            "Tarisa mufananidzo wemunda wechibage.\n"
            "Tsanangura:\n"
            "• Hutano hwezvirimwa\n"
            "• Zviratidzo zvekushaikwa kwemanyowa\n"
            "• Fungidzira soil pH\n"
            "• Zano rinoshanda uchishandisa dota, mufudze, ivhu rechuru\n"
            "Pindura muShona yakareruka."
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user","content":[{"type":"text","text":prompt},
                       {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{image_base64}"}}]}],
            max_tokens=400
        )

        text = completion.choices[0].message.content
        ph_match = re.search(r'([5-8]\.[0-9])', text)
        estimated_ph = float(ph_match.group(1)) if ph_match else 6.0
        dosage = calculate_dosage(estimated_ph, plot_size)

        return f"📸 *AI Ongororo Yemufananidzo*\n\n{text}\n\n📊 Estimated pH: {estimated_ph}\n\n{format_dosage_message(dosage)}"

    except:
        return "⚠️ Handikwanisi kuongorora mufananidzo izvozvi. Shandisa Option 6."

# ==========================
# WEBHOOK
# ==========================
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    user = request.values.get("From")
    incoming = request.values.get("Body", "").strip().lower()
    num_media = int(request.values.get("NumMedia", 0))

    resp = MessagingResponse()
    msg = resp.message()
    state = user_states.get(user, "main_menu")

    # --------------------------
    # MAIN MENU OPTIONS
    # --------------------------
    if incoming in ["hi","hello","menu","start","makadini"]:
        user_states[user] = "main_menu"
        msg.body(main_menu())

    elif incoming == "1":
        user_states[user] = "option1_ph"
        msg.body("📊 Nyora pH yeivhu rako (semuenzaniso: pH 5.5) kana tumira mufananidzo wemunda wako.")

    elif incoming == "2":
        user_states[user] = "option2_fix"
        msg.body(
            "🥤 Kugadzirisa ivhu rako.\n"
            "Kana uchiziva pH, nyora pH (semuenzaniso: pH 5.5).\n"
            "Kana usingazivi pH, tumira mufananidzo wemunda wako kana nyora 6 kuti tibatsire."
        )

    elif incoming == "3":
        user_states[user] = "option3_help"
        msg.body("💰 Rubatsiro: EcoCash 0773 208904, Zita: Beloved Nkomo\nTibate kana uine mibvunzo.")

    elif incoming == "4":
        user_states[user] = "option4_l












