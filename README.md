# 🌌 NOVA-CactusTech: EchoMinder

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Agentuity](https://img.shields.io/badge/Framework-Agentuity.ai-brightgreen.svg)](https://agentuity.ai)
[![Model](https://img.shields.io/badge/Model-GPT--4o--mini-purple.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Team](https://img.shields.io/badge/Team-CactusTech-orange.svg)](#team-cactustech)

---

> 🧠 **EchoMinder** — A next-generation AI memory system that helps chatbots *remember and think like humans*.  
> Developed by **Team CactusTech** under the project **NOVA-CactusTech**.

---

## 🚀 Overview

Most chatbots forget everything after each message.  
**EchoMinder** changes that by introducing a **three-layer AI memory architecture** that continuously learns and remembers user context.

EchoMinder acts as a *memory layer* for LLM-based assistants — automatically summarizing, merging, and retrieving information from past conversations to create more human-like, personalized dialogue.

---

## 🧩 Key Features

- 🧠 **Three-Layer Memory System**
  - **Short-Term Memory** — Stores recent summaries (latest ~10 messages).  
  - **Mid-Term Memory** — Merges multiple short-term memories into abstract insights.  
  - **Long-Term Memory** — Persists meaningful information in local storage.

- 🤖 **Automatic Memory Summarization**
  - Each user and assistant message is summarized using GPT-4o-mini.
  - The summaries are stored and periodically merged into long-term memory.

- 🔍 **Intelligent Retrieval**
  - Fetches relevant memories based on keywords and semantic similarity.
  - Expands user queries via synonym mapping (e.g., “fav” → “favorite”, “language” → “code”).

- 🧱 **Enhanced Prompt Construction**
  - Builds a structured **enhanced_prompt** that includes memory context.
  - Ensures the main chatbot responds based on user history and preferences.

---

## 🏗️ System Architecture

```
User ↔ Chat UI (HTML/JS)
          │
          ▼
   EchoMinder_New Agent (Python + Agentuity)
   ├─ Summarize user messages
   ├─ Update 3-layer memory (short/mid/long)
   ├─ Retrieve related context
   └─ Build enhanced prompt
          │
          ▼
   OpenRouter API (GPT-4o-mini)
          │
          ▼
   Personalized & Context-Aware Reply
```

---

## ⚙️ Technology Stack

| Layer | Technology | Description |
|--------|-------------|-------------|
| **Backend Core** | Python 3.11 + AsyncIO | Implements the agent and memory system |
| **Agent Framework** | [Agentuity.ai](https://agentuity.ai) | Handles runtime, dev mode, and cloud hooks |
| **Language Model** | GPT-4o-mini (OpenRouter) | Summarization + reasoning |
| **Persistence** | Local JSON storage (`long_term_new.json`) | Long-term memory |
| **Frontend** | HTML + Vanilla JS | Minimal chat interface |
| **Deployment** | AWS EC2 / Render / Vercel | Optional hosting solutions |

---

## 💻 Quick Start

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/CactusTech/NOVA-CactusTech.git
cd NOVA-CactusTech
```

### 2️⃣ Install Dependencies
```bash
pip install openai agentuity
```

### 3️⃣ Run Locally (no webhook needed)
```bash
agentuity dev
```

Or directly:
```bash
python agents/EchoMinder_New/main.py
```

### 4️⃣ Test Locally
Send a sample request:
```bash
curl -X POST http://127.0.0.1:49764   -H "Content-Type: application/json"   -d '{"user_message": "Remember that my favorite language is Python"}'
```

---

## 🧠 Example Output

```json
{
  "mode": "auto",
  "enhanced_prompt": "You are a helpful AI assistant. Below is important context about the user that you MUST remember and use...",
  "memory_context": "User prefers Python for programming projects.",
  "original_message": "What should I build next?",
  "memory_stats": {
    "short_term_count": 5,
    "mid_term_count": 2,
    "long_term_count": 1
  },
  "hint": "Use the 'enhanced_prompt' field as the chatbot input."
}
```

---


## 🌱 Future Roadmap

- [ ] Integrate **vector-based memory** (FAISS / Chroma)
- [ ] Enable **semantic search and ranking**
- [ ] Build a **web dashboard** for visualizing user memories
- [ ] Replace JSON with **PostgreSQL / SQLite** backend
- [ ] Launch **EchoMinder API** for third-party chatbots

---

## 🧭 Vision

> “Real intelligence isn’t about knowing everything.  
> It’s about remembering what matters.”  
>
> — Team **CactusTech**

---

## 🪪 License

MIT License © 2025 **CactusTech**

---
