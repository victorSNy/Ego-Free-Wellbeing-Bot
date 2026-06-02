import nest_asyncio
nest_asyncio.apply()  

import pandas as pd
import random
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# Load CSV 
try:
    data = pd.read_csv(r"knowledge_base.csv", encoding='utf-8-sig').fillna("")
    print("✅ CSV loaded.")
except FileNotFoundError:
    print("❌ CSV not found.")
    exit(1)

data["priority"] = pd.to_numeric(data["priority"], errors="coerce").fillna(99).astype(int)

required_cols = ["emotion", "keywords", "priority", "tool_name", "tool_description",
                 "citation", "ego_explanation", "youtube_query", "patristic_explanation", "source_type"]
missing = [c for c in required_cols if c not in data.columns]
if missing:
    print(f"Missing columns: {missing}")
    exit(1)

user_state = {}

emotions_list = """
Choose your current emotional state:

1. Anxiety (e.g. persistent worry about future events)
2. Sadness (e.g. feeling of loss, heaviness, low energy)
3. Anger (e.g. frustration, perceived injustice, irritation)
4. Existential frustration (e.g. lack of meaning, feeling that nothing truly matters)
5. Loneliness (e.g. emotional isolation, even when not physically alone)
6. Shame (e.g. negative self evaluation, feeling defective)
7. Overwhelm (e.g. too many demands, mental paralysis)
8. Spiritual dryness (e.g. feeling disconnected from transcendence or inner self)

Of course you can feel different, mixed, more depper feelings, but try to stick to the strongest emotion present.
"""

def normalize_emotion(text):
    text = text.lower().strip()
    m = {
        "1":"anxiety","anxiety":"anxiety","anxious":"anxiety",
        "2":"sadness","sad":"sadness","depressed":"sadness",
        "3":"anger","angry":"anger","rage":"anger",
        "4":"existential_frustration","existential":"existential_frustration",
        "5":"loneliness","lonely":"loneliness",
        "6":"shame","ashamed":"shame",
        "7":"overwhelm","overwhelmed":"overwhelm",
        "8":"spiritual_dryness","spiritual dryness":"spiritual_dryness","dryness":"spiritual_dryness"
    }
    for k,v in m.items():
        if k in text:
            return v
    return None

def find_best_tools(emotion, user_text):
    matches = data[data["emotion"] == emotion]
    if matches.empty:
        return "No tools found.", []
    results = []
    for _, row in matches.iterrows():
        kw = str(row["keywords"]).lower().split()
        score = sum(1 for k in kw if k in user_text.lower())
        results.append((score, row["priority"], row))
    results.sort(key=lambda x: (-x[0], x[1], random.random()))
    top = [r[2] for r in results[:2]]
    text = ""
    for r in top:
        text += f"\n✅ {r['tool_name']}\n{r['tool_description']}\nSource: {r['citation']}\n"
    return text, top
def workflow(user_id, text):
    if text.lower() == "/start":
        user_state[user_id] = {"step": 1}
        return "🔄 Conversation reset.\n\n" + emotions_list

    state = user_state.get(user_id, {"step": 1})
    step = state["step"]

    if step == 1:
        state["step"] = 2
        user_state[user_id] = state
        return "🌱 Emotional State Selection\n\n" + emotions_list

    elif step == 2:
        emotion = normalize_emotion(text)
        if not emotion:
            return "Please choose an emotion from the list (number)."
        state["emotion"] = emotion
        state["step"] = 3
        user_state[user_id] = state
        return "In 1–2 sentences, describe why you feel this way (or why you think you do)."

    # STEP 3 – empathetic reaction + immediately ask tool preference
    elif step == 3:
        state["reason"] = text
        emotion = state["emotion"]
        templates = {
            "anger": "That sounds really difficult. It makes sense you'd feel angry in that situation.",
            "sadness": "I hear how heavy that feels. It's natural to feel sadness when something matters to you.",
            "anxiety": "It's understandable to feel worried when things are uncertain.",
            "loneliness": "Feeling alone can be painful. Your feelings are valid.",
            "shame": "That takes courage to share. Shame often hides in silence.",
            "overwhelm": "When everything piles up, it's normal to feel paralyzed.",
            "existential_frustration": "Questions of meaning can be deeply unsettling.",
            "spiritual_dryness": "That sense of emptiness can be confusing."
        }
        empathy = templates.get(emotion, f"It makes sense you'd feel {emotion} in that situation. But I am going to help you with some insights from recent academic psychological studies combined with spiritual insights.")
        question = f"\n\nWould you like to receive a psychological tool, a spiritual tool, or both to cope with {emotion}? (type 'psychological', 'spiritual', or 'both')"
        state["step"] = 5   # skip old step 4
        user_state[user_id] = state
        return empathy + question

    # STEP 5 – present tools (receives preference directly)
    elif step == 5:
        pref = text.lower()
        if pref not in ["psychological", "spiritual", "both"]:
            pref = "both"
        emotion = state["emotion"]
        tool_text, all_rows = find_best_tools(emotion, state["reason"])
        if pref == "psychological":
            rows = [r for r in all_rows if r["source_type"] == "psychology"]
        elif pref == "spiritual":
            rows = [r for r in all_rows if r["source_type"] == "spiritual"]
        else:
            rows = all_rows
        if not rows:
            rows = all_rows[:2]
            tool_text = "\nNo exact match – showing general tools:\n"
        else:
            tool_text = ""
        for r in rows[:2]:
            tool_text += f"\n✅ {r['tool_name']}\n{r['tool_description']}\nSource: {r['citation']}\n"
        state["selected_tools"] = rows
        state["tools_text"] = tool_text
        state["step"] = 6
        user_state[user_id] = state
        return tool_text + "\n\n Do you want to know how our ego is connected to that? (yes/no)"

    elif step == 6:
        if text.lower() in ["yes", "y"]:
            response = "You know that our attachment to the ego – seen by some brands of psychology and spirituality – is a main cause of inner discomfort. Briefly: the ego is the sense of a separate self that wants control, approval, and certainty. When we cling to that, we suffer.\n\n"
        else:
            response = "Ok, we'll skip the detailed ego explanation for now.\n\n"
        response += "Would you like to watch some videos on this topic? (e.g., Eckhart Tolle, monastic wisdom) (yes/no)"
        state["step"] = 7
        user_state[user_id] = state
        return response

    elif step == 7:
        if text.lower() in ["yes", "y"]:
            emotion = state["emotion"]
            base = "https://www.youtube.com/results?search_query="
            queries = [
                f"{emotion} coping skills",
                f"{emotion} psychology",
                f"{emotion} spiritual guidance",
                "ego attachment Eckhart Tolle",
                "patristic Orthodox monks passions"
            ]
            links = "\n".join([f"• {base}{q.replace(' ', '+')}" for q in queries[:5]])
            response = f"Here are some video resources:\n{links}\n\n"
        else:
            response = "Ok, moving on.\n\n"
        response += "From the patristic (Church Fathers) point of view, these emotional states are called 'passions' – they are interconnected. Would you like to know more? (yes/no)"
        state["step"] = 8
        user_state[user_id] = state
        return response

    elif step == 8:
        if text.lower() in ["yes", "y"]:
            emotion = state["emotion"]
            matches = data[data["emotion"] == emotion]
            patristic = matches.iloc[0]["patristic_explanation"] if not matches.empty else "The passions are thoughts and emotions that disturb the soul's natural state of peace."
            response = f"🕊 Patristic view:\n{patristic}\n\n"
        else:
            response = "Ok, skipping patristic explanation.\n\n"
        response += "Would you like me to create a summary of what we discussed for your future use? (yes/no)"
        state["step"] = 9
        user_state[user_id] = state
        return response
   
    elif step == 9:
        if text.lower() in ["yes", "y"]:
            try:
                ai_summary = generate_ai_summary(
                state.get("emotion"),
                state.get("reason"),
                state.get("tools_text", "")
            )

            except:
                ai_summary = None

        # ✅ fallback summary if AI fails
        if not ai_summary or "failed" in ai_summary.lower():

            fallback = f"""
You described feeling {state.get("emotion")} in response to {state.get("reason")}. 
This reaction is understandable given the situation.

From a psychological perspective, emotions like this are often influenced by thought patterns and behavioral responses. Techniques such as the ones you explored can help regulate the intensity of this state.

From a deeper perspective, this experience may also be connected to patterns of attachment, expectations, or meaning-making. Reflecting on these can help you respond more consciously rather than react automatically.

A helpful next step is to apply the tools you explored in small, practical ways and observe how your experience changes over time.
"""
            ai_summary = fallback
        summary = f"\n🌱 SUMMARY\n\n{ai_summary}"
    else:
        summary = "Ok, no summary saved."
    user_state[user_id] = {"step": 1}
    return summary + "\n\nType /start to begin a new conversation."

async def handle_message(update, context):
    user_id = update.message.chat_id
    user_text = update.message.text
    response = workflow(user_id, user_text)
    await update.message.reply_text(response)

if __name__ == "__main__":
    TOKEN = ""   
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("✅ Bot is running. Watch console for debug output...")
    app.run_polling()
