Ego-Free-Wellbeing-Bot

A Telegram bot designed to provide emotional support by guiding users through a structured 8-step workflow. 
It offers evidence-based psychological coping tools and traditional spiritual practices based on a curated knowledge base.

Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.env` file with `BOT_TOKEN=your_token`
4. Run: `python bot.py`
Prerequisites

*   Python 3.11 or higher installed.
*   A Telegram account and a bot token from [@BotFather](https://t.me/botfather).

Installation

 Clone the repository (or download the files):
    ```bash
    git clone <your-github-repo-url>
    cd <your-project-folder>

How it works
User Layer (Telegram)
        ↓
Application Layer (Bot Logic / Workflow Engine)
        ↓
Decision Layer (Emotion Detection + Keyword Matching)
        ↓
Knowledge Layer (CSV Dataset)
        ↓
Interpretation Layer (AI / Rule-based synthesis)
        ↓
Response Layer (tools + explanations)
