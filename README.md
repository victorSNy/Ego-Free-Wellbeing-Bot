# Ego-Free-Wellbeing-Bot
Diploma for DS course

Phyton code
!pip install nest_asyncio
import nest_asyncio
nest_asyncio.apply()
import pandas as pd
import os
import random
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# 1. Load and prepare CSV
try:
  data = pd.read_csv(r"C:\Victor\DS\ego_free_bot\knowledge_base.csv", encoding='utf-8').fillna("")
  print("CSV loaded successfully. Shape:", data.shape)
except FileNotFoundError:
    print("knowledge_base.csv not found!")
    exit(1)

# Clege an priority column
data["priority"] = pd.to_numeric(data["priority"], errors="coerce").fillna(99).astype(int)

# Required columns check
required_cols = ["emotion", "keywords", "priority", "tool_name", "tool_description",
                 "citation", "ego_explanation", "youtube_query", "patristic_explanation"]
missing = [col for col in required_cols if col not in data.columns]
if missing:
    print(f"Missing columns in CSV: {missing}")
    exit(1)

# Debug: show unique emotions found
unique_emotions = data["emotion"].unique()
print("Loaded emotions:", unique_emotions)

# 2. User state stora-------
user_state = {}

# 3. Emotion list and normalisation
emotions_list = """
Choose your emotional state:

1. Anxiety  
2. Sadness  
3. Anger  
4. Existential frustration  
5. Loneliness  
6. Shame  
7. Overwhelm  
8. Spiritual dryness  

Please type the name or number.
"""

def normalize_emotion(text):
    text = text.lower().strip()
    mapping = {
        "1": "anxiety", "anxiety": "anxiety", "anxious": "anxiety", "stress": "anxiety",
        "2": "sadness", "sad": "sadness", "depressed": "sadness",
        "3": "anger", "angry": "anger", "rage": "anger",
        "4": "existential_frustration", "existential": "existential_frustration",
        "5": "loneliness", "lonely": "loneliness",
        "6": "shame", "ashamed": "shame",
        "7": "overwhelm", "overwhelmed": "overwhelm",
        "8": "spiritual_dryness", "spiritual dryness": "spiritual_dryness", "dryness": "spiritual_dryness"
    }
    for key, value in mapping.items():
        if key in text:
            print(f"   → Normalised '{text}' to '{value}'")
            return value
    print(f"   → No match for '{text}'")
    return None

# 4. Tool selection with keyword scoring + tie‑breaker
def find_best_tools(emotion, user_text):
    print(f"\n🔍 find_best_tools(emotion='{emotion}', user_text='{user_text}')")
    matches = data[data["emotion"] == emotion]
    print(f"   → Found {len(matches)} matching rows in CSV")
    if matches.empty:
        return "No tools found.", []

    results = []
    for idx, row in matches.iterrows():
        keywords = str(row["keywords"]).lower().split()
        score = sum(1 for kw in keywords if kw in user_text.lower())
        results.append((score, int(row["priority"]), row))
        print(f"   → Row {idx}: keywords={keywords}, score={score}, priority={row['priority']}")

    results.sort(key=lambda x: (-x[0], x[1], random.random()))
    top_rows = [r[2] for r in results[:2]]
    print(f"   → Selected top {len(top_rows)} rows")

    tool_text = ""
    for row in top_rows:
        tool_text += f"""
✅ {row['tool_name']}
{row['tool_description']}
Source: {row['citation']}
"""
    return tool_text, top_rows

# 5. Main workflow
def workflow(user_id, text):
    # Reset on /start command
    if text.lower() == "/start":
        user_state[user_id] = {"step": 1}
        return "🔄 Conversation reset.\n\n" + emotions_list

    state = user_state.get(user_id, {"step": 1})
    step = state["step"]
    print(f"\n📌 User {user_id} | Step {step} | Text: {text}")

    # Step 1: choose emotion
    if step == 1:
        state["step"] = 2
        user_state[user_id] = state
        return "🌱 Emotional State Selection\n\n" + emotions_list

    # Step 2: recognise emotion
    elif step == 2:
        emotion = normalize_emotion(text)
        if not emotion:
            return "Please choose an emotion from the list (name or number)."
        state["emotion"] = emotion
        state["step"] = 3
        user_state[user_id] = state
        return "In 1–2 sentences, describe why you feel this way."

    # Step 3: get description and empathise
    elif step == 3:
        state["reason"] = text
        emotion = state["emotion"]
        state["step"] = 4
        user_state[user_id] = state
        return f"It makes sense you'd feel {emotion} in that situation."

    # Step 4: ask tool preference
    elif step == 4:
        state["preference"] = text.lower()
        state["step"] = 5
        user_state[user_id] = state
        return "Would you like psychological tools, spiritual tools, or both?"

    # Step 5: present tools (with preference filter)
    elif step == 5:
        emotion = state["emotion"]
        pref = state.get("preference", "both")
        print(f"   → Using preference: {pref}")
        tool_text, all_rows = find_best_tools(emotion, state["reason"])

        # Filter by source_type if user gave a preference
        if pref == "psychological":
            rows = [r for r in all_rows if r["source_type"] == "psychology"]
        elif pref == "spiritual":
            rows = [r for r in all_rows if r["source_type"] == "spiritual"]
        else:
            rows = all_rows

        # Rebuild tool text from filtered rows
        tool_text = ""
        for row in rows[:2]:
            tool_text += f"""
✅ {row['tool_name']}
{row['tool_description']}
Source: {row['citation']}
"""

        if not tool_text:
            tool_text = "\nNo tools match your preference. Showing general tools instead.\n"
            rows = all_rows[:2]  # fallback

        # Ego explanation and YouTube link (from first tool)
        ego_text = ""
        youtube_link = ""
        if rows:
            ego_text = f"\n🧠 Insight: {rows[0]['ego_explanation']}"
            query = rows[0]["youtube_query"]
            if query:
                youtube_link = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            ego_text = "\n🧠 Insight: Reflect on how this emotion connects to your sense of self."

        state["step"] = 6
        user_state[user_id] = state
        return f"{tool_text}{ego_text}\n🎥 Video: {youtube_link if youtube_link else 'Not available'}\n\nExplore ego/attachment more? (yes/no)"

    # Step 6: handle ego exploration
    elif step == 6:
        if text.lower() in ["yes", "y"]:
            response = "Great! We'll go deeper next time."
        else:
            response = "Ok, moving on."
        state["step"] = 7
        user_state[user_id] = state
        return response + "\n\nWould you like more explanation from the patristic perspective? (yes/no)"

    # Step 7: patristic explanation
    elif step == 7:
        if text.lower() in ["yes", "y"]:
            emotion = state["emotion"]
            matches = data[data["emotion"] == emotion]
            patristic = matches.iloc[0]["patristic_explanation"] if not matches.empty else "No patristic explanation available."
            response = f"🕊 Patristic view:\n{patristic}"
        else:
            response = "Ok, skipping patristic explanation."
        state["step"] = 8
        user_state[user_id] = state
        return response

    # Step 8: summary and reset
    elif step == 8:
        summary = f"""
🌱 Summary

Emotion: {state.get('emotion')}
Reason: {state.get('reason')}

You explored tools and insights to regulate this state.
"""
        user_state[user_id] = {"step": 1}
        return summary + "\nWould you like to start again? (type /start)"

    else:
        user_state[user_id] = {"step": 1}
        return "Let's start over.\n" + emotions_list
        
# 6. Telegram handler
async def handle_message(update, context):
    user_id = update.message.chat_id
    user_text = update.message.text
    response = workflow(user_id, user_text)
    await update.message.reply_text(response)

# 7. Main entry point
if __name__ == "__main__":
    TOKEN = "8918816834:AAHM9mf6QKkhWB6RgFMkT_nWZfnoBLrEjys"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    print("✅ Bot is running. Watch console for debug output...")
    app.run_polling()
