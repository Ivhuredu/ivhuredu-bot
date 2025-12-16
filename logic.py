# logic.py

def analyze_input(user_state, message):
    msg = message.lower().strip()

    # Start
    if msg in ["tanga", "start"]:
        return "Tinokugamuchirai ku IvhuRedu 🌱\nTanga here?\nPindura: EHE kana KWETE"

    if msg == "ehe":
        return "Uri kupi? Nyora zita renzvimbo (semuenzaniso: Mataga)"

    if user_state.get("location") is None:
        user_state["location"] = message
        return (
            "Wakamboongorora here pH yeivhu rako?\n1️⃣ Ehe, ndinoziva pH\n2️⃣ Kwete, handina kumboongorora"
        )

    if msg == "1":
        return "Nyora pH yawakaona (semuenzaniso: 5.8, 7.8)"

    if msg == "2":
        user_state["symptom_step"] = 1
        return "Mashizha echibage ari kuita yero here? (EHE / KWETE)"

    # pH input
    try:
        ph = float(msg)
        if ph < 5.5:
            return "📊 Mhedziso: Ivhu rine acid yakawanda\n✅ Dota shoma-shoma\n📏 1 kapu pa 10 m²"
        elif 5.5 <= ph <= 7.0:
            return "📊 Mhedziso: Ivhu rakanaka\n✅ Manyowa emombe akaorera\n📏 2–3 mabara pa 100 m²"
        elif ph <= 7.8:
            return "📊 Mhedziso: Alkaline zvishoma\n❌ Usaise dota\n✅ Manyowa akaorera\n📏 2–3 mabara pa 100 m²"
        else:
            return "📊 Mhedziso: Alkaline yakanyanya\n❌ Dota harikurudzirwi\n✅ Manyowa + compost"
    except ValueError:
        pass

    # Symptom-based flow
    if user_state.get("symptom_step") == 1:
        user_state["yellow"] = msg == "ehe"
        user_state["symptom_step"] = 2
        return "Ivhu rinoita here sekunge rine munyu? (EHE / KWETE)"

    if user_state.get("symptom_step") == 2:
        user_state["salty"] = msg == "ehe"
        user_state["symptom_step"] = 3
        return "Uswa hunomera ipapo hudiki here? (EHE / KWETE)"

    if user_state.get("symptom_step") == 3:
        weak_grass = msg == "ehe"
        risk = sum([
            user_state.get("yellow"),
            user_state.get("salty"),
            weak_grass
        ])

        if risk >= 2:
            return "📊 Mhedziso: Ivhu rine alkaline / munyu\n❌ Usaise dota\n✅ Manyowa akaorera\n📏 2–3 mabara pa 100 m²"
        else:
            return "📊 Mhedziso: Ivhu rakanaka asi rine nzara\n✅ Wedzera manyowa\n🌱 Siya marara ezvirimwa"

    return "Ndapota pindura neEHE, KWETE, 1, 2 kana pH."
