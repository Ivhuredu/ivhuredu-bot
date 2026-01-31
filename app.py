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

        # Download private Twilio image
        img_response = requests.get(
            photo_url,
            auth=(twilio_sid, twilio_token),
            timeout=15
        )

        if img_response.status_code != 200:
            return "❌ Handina kukwanisa kuwana mufananidzo."

        image_base64 = base64.b64encode(img_response.content).decode("utf-8")

        prompt = (
             "Uri nyanzvi yezvekurima muZimbabwe.\n"
             "Taura muShona chaiyo inoshandiswa nevarimi vemumaruwa.\n"
             "Tarisa mufananidzo wemunda wechibage.\n\n"
             "Tsanangura zvakajeka:\n"
             "• Hutano hwezvirimwa\n"
             "• Zvinoratidza kushomeka kwemanyowa\n"
             "• Fungidzira pH yeivhu\n"
             "• Zano rinoshanda uchishandisa dota, mufudze, ivhu rechuru\n"
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_base64}"
                    }
                ]
            }],
            max_output_tokens=400
        )

        text = response.output_text

        ph_match = re.search(r'([5-8]\.[0-9])', text)
        estimated_ph = float(ph_match.group(1)) if ph_match else 6.0

        dosage = calculate_dosage(estimated_ph)

        return (
            "📸 *AI Ongororo Yemufananidzo*\n\n"
            f"{text}\n\n"
            f"📊 Estimated pH: {estimated_ph}\n\n"
            f"{format_dosage_message(dosage)}"
        )

    except Exception as e:
        return f"⚠️ AI analysis failed: {str(e)}"

def ai_answer_question(user_question):
    try:
        prompt = (
            "Uri nyanzvi yezvekurima muZimbabwe ine ruzivo rwevarimi vemumaruwa.\n"
            "Pindura mubvunzo wemurimi muShona chaiyo yakachena uye iri nyore kunzwisisa.\n"
            "Shandisa mashoko anoshandiswa nevarimi veZimbabwe.\n"
            "Dzivisa Shona yekushandura zvakananga kubva kuEnglish.\n\n"
            f"Mubvunzo wemurimi: {user_question}"
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=300
        )

        return response.output_text

    except Exception as e:
        return f"⚠️ AI failed to answer: {str(e)}"


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
        user_states[user] = "option4_lessons"
        msg.body(
            "🎁 Zvidzidzo pamusoro peivhu.\n"
            "1️⃣ Soil basics\n"
            "2️⃣ Fertilizer usage\n"
            "3️⃣ Crop rotation tips\n"
            "Nyora nhamba yesarudzo yaunoda."
        )

    elif incoming == "5":
        user_states[user] = "option5_consult"
        msg.body("📝 Bvunza Mudhumeni Wedu. Nyora mubvunzo wako pano:")
        

    elif incoming == "6":
        user_states[user] = "q1"
        user_data[user] = {"answers": {}}
        msg.body(OPTION6_QUESTIONS[0]['question'])

    # --------------------------
    # PH INPUT OR PHOTO (Option 1 & 2)
    # --------------------------
    elif state in ["option1_ph", "option2_fix"]:
        if "ph" in incoming:
            msg.body(analyze_ph(incoming, user))
            user_states[user] = "main_menu"
        elif num_media > 0:
            photo_url = request.values.get("MediaUrl0")
            result = ai_photo_analysis(photo_url)
            user_states[user] = "main_menu"
            msg.body(result + "\n\nNyora *MENU* kudzokera kumenyu huru.")
        else:
            msg.body("⚠️ Ndapota nyora pH (semuenzaniso: pH 5.5) kana tumira mufananidzo wemunda wako.")

    # --------------------------
    # OPTION 4 LESSONS
    # --------------------------
    elif state == "option4_lessons":
        if incoming == "1":
            msg.body("📘 Soil Basics: Ivhu rakanaka rinofanira kuva nemanyowa, humus, uye drainage yakanaka.")
        elif incoming == "2":
            msg.body("📗 Fertilizer Usage: Shandisa mufudze wemombe kana manyowa zvichienderana nepH.")
        elif incoming == "3":
            msg.body("📙 Crop Rotation: Shandura zvirimwa kuti udzivise kushaikwa kwemanyowa.")
        else:
            msg.body("⚠️ Nyora 1, 2, kana 3 kuti usarudze chidzidzo.")
        user_states[user] = "main_menu"
        msg.body("Chidzidzo chapera.\n\nNyora *MENU* kudzokera kumenyu huru.")


    # --------------------------
    # OPTION 5 USER QUESTIONS
    # --------------------------
    
    elif state == "option5_consult":
        answer = ai_answer_question(incoming)   # ask OpenAI
        user_states[user] = "main_menu"

        msg.body(
            "🤖 *Mhinduro yeIvhuRedu AI*\n\n"
            f"{answer}\n\n"
            "Nyora *MENU* kudzokera kumenyu huru."
        )

    # --------------------------
    # OPTION 6 GUIDED QUESTIONS
    # --------------------------
    elif state.startswith("q"):
        answers = user_data[user].get("answers", {})
        q_index = int(state[1:]) - 1
        field_name = OPTION6_QUESTIONS[q_index]['field']
        answers[field_name] = incoming
        user_data[user]['answers'] = answers

        if q_index + 1 < len(OPTION6_QUESTIONS):
            user_states[user] = f"q{q_index+2}"
            msg.body(OPTION6_QUESTIONS[q_index+1]['question'])
        else:
            user_states[user] = "main_menu"
            # Estimate pH from simple rules
            est_ph = 6.0
            if answers.get("soil_color","")=="yero" or answers.get("leaf_yellowing","")=="hongu":
                est_ph = 5.5
            elif answers.get("soil_color","")=="tsvuku":
                est_ph = 6.8
            dosage = calculate_dosage(est_ph)
            msg.body(f"🤖 Estimated pH: {est_ph}\n{format_dosage_message(dosage)}\n\nNyora *MENU* kudzokera kumenyu huru.")

    # --------------------------
    # PHOTO UPLOAD OUTSIDE MENU
    # --------------------------
    elif num_media > 0:
        photo_url = request.values.get("MediaUrl0")
        result = ai_photo_analysis(photo_url)
        user_states[user] = "main_menu"
        msg.body(result + "\n\nNyora *MENU* kudzokera kumenyu huru.")

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























