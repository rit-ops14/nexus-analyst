# 🧠 Nexus Analyst

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-multi--agent-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-tool%20server-teal)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**A multi-agent AI system for conversational data analysis.**
*Built by Team BrainBots.*

Upload a CSV, ask "what's the average revenue by region?", and watch a
Supervisor Agent delegate to a Data Analyst Agent and a Visualization
Agent in real time — with the full reasoning trail visible, not hidden
behind a black box.

🔗 **[Live demo](https://nexus-analyst-m3b3ksgokgfckjeiv4jm8u.streamlit.app)** &nbsp;·&nbsp; 📺 **[Architecture](#-how-it-works-architecture)** &nbsp;·&nbsp; 🚀 **[Quick start](#-setup-local)**

> ⭐ If this project is useful or interesting to you, consider starring the repo — it helps others find it too.

---

## ✨ Why this project stands out

- 🤖 **Real multi-agent collaboration** — not one AI doing everything, but a Supervisor delegating to specialist agents, LangGraph-style
- 🔌 **MCP-based tools** — the agents' tools (data analysis, charts, email) live in a standard Model Context Protocol server, decoupled from the reasoning logic
- 📚 **RAG-grounded** — retrieves the actual dataset schema before writing any analysis code, instead of guessing column names
- 📈 **Interactive dashboard** — real pandas + Plotly analysis runs the moment you upload data, no question needed
- 📧 **Agents that take real action** — the Communicator Agent can actually send an email report, not just display text
- 🧑‍🤝‍🧑 **Full transparency** — every response shows exactly which agents ran and what code they executed

---

## 🧠 How it works (architecture)

This project uses a **multi-agent supervisor architecture** — instead of
one AI trying to do everything, a small TEAM of specialist agents
collaborates, coordinated by a Supervisor Agent. This mirrors how your
own team splits work between people.

```
                          ┌───────────────────────────┐
   User types a question  │        Streamlit UI        │
   ────────────────────▶  │  (app.py)                  │
                          └─────────────┬──────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │      RAG Retrieval         │
                          │   (rag/retrieve.py)        │
                          │  finds relevant columns    │
                          └─────────────┬──────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │     Supervisor Agent       │  "What does this
                          │   (agent/graph.py)         │   question need?"
                          └──────┬─────────┬───────────┘
                                 │         │
                  needs_data     │         │  needs_chart
                                 ▼         ▼
                   ┌─────────────────┐ ┌──────────────────┐
                   │ Data Analyst     │ │ Visualization     │
                   │ Agent            │ │ Agent             │
                   │ (runs pandas via │ │ (draws charts via │
                   │  MCP tool)       │ │  MCP tool)        │
                   └────────┬─────────┘ └─────────┬─────────┘
                            └─────────┬─────────────┘
                                      ▼
                          ┌───────────────────────────┐
                          │    Communicator Agent      │
                          │  writes final answer,      │
                          │  emails if requested        │
                          └───────────────────────────┘
```

### The four concepts, and exactly where they live

| Concept | Where | What it actually does here |
|---|---|---|
| **LLM** | Every agent in `agent/graph.py` (via `ChatGroq`) | Each specialist agent uses the LLM for its own narrow job — planning, analysis, chart code, or communication |
| **RAG** | `rag/ingest.py`, `rag/retrieve.py` | Stores column names/types/samples in a ChromaDB vector store; retrieves only the relevant columns so agents don't guess column names |
| **MCP** | `mcp_server/server.py` | Exposes shared tools (`describe_dataframe`, `run_pandas_code`, `generate_chart`, `send_email_report`) that ANY agent can call — the tools are decoupled from any one agent |
| **Multi-Agent Collaboration** | `agent/graph.py` | A **Supervisor Agent** plans and delegates to a **Data Analyst Agent** and a **Visualization Agent**, then a **Communicator Agent** finalizes the response — four distinct specialists, each with one job |
| **LangGraph** | `agent/graph.py` | Implements the whole team as an explicit state graph with conditional routing — you can point to `route_from_supervisor()` and explain exactly how work gets delegated |

### Why this design is easy to explain in a viva

Each folder = one concept, and each **agent function** = one team
member's job. If an evaluator asks "where's the multi-agent part?" you
point at the four functions in `agent/graph.py`: `supervisor_node`,
`data_analyst_node`, `visualization_node`, `communicator_node` — and
explain that the Supervisor's `route_from_supervisor()` function is
literally the delegation logic, visible and readable, not a black box.

---

## 📁 Folder structure

```
agentic-data-analyst/
├── mcp_server/
│   └── server.py        # MCP tools: describe_dataframe, run_pandas_code, generate_chart
├── rag/
│   ├── ingest.py         # builds the vector DB from the uploaded CSV's schema
│   └── retrieve.py       # fetches relevant column info for a given question
├── agent/
│   └── graph.py          # LangGraph state graph (the agent's reasoning loop)
├── app.py                # Streamlit UI (chat interface + charts)
├── sample_data/
│   └── sample_sales.csv  # sample dataset to test with immediately
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Setup (local)

**1. Clone and enter the project**
```bash
git clone <your-repo-url>
cd agentic-data-analyst
```

**2. Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API key**
```bash
cp .env.example .env
# then edit .env and paste your free Groq API key
# get one at https://console.groq.com/keys
```

**5. Run the app**
```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`),
upload `sample_data/sample_sales.csv`, and:
- Check the **Auto Dashboard tab** immediately — it's already showing real stats and charts
- Switch to **Ask the Agent** and try:
  - "What's the average revenue by region?"
  - "Show me a bar chart of profit by category"
  - "Which region sold the most units?"
  - "Email the average revenue by region to your.email@example.com" (needs email setup below)

**Optional: enable the email feature**
The email tool needs a Gmail account with an "App Password" (not your normal password):
1. Turn on 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords and generate a 16-character app password
3. Put your Gmail address and that app password into `.env` as `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD`
If you skip this, everything else still works — the email button/tool will just tell you it's not configured instead of crashing.

---

## ☁️ Deployment

### Option A: Streamlit Community Cloud (easiest, free)
1. Push this repo to GitHub (make sure `.env` is in `.gitignore` — never commit real API keys).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Click "New app", select your repo, set the main file to `app.py`.
4. Under "Advanced settings → Secrets", add:
   ```
   GROQ_API_KEY = "your_real_key_here"
   ```
5. Deploy. Streamlit Cloud installs `requirements.txt` automatically.

> Note: the MCP server is launched as a local subprocess by the agent, so it works out of the box on Streamlit Cloud with no extra setup.

### Option B: Hugging Face Spaces
1. Create a new Space, choose the **Streamlit** SDK.
2. Upload the repo files (or connect via GitHub).
3. Add `GROQ_API_KEY` under Space **Settings → Repository secrets**.
4. The Space builds and deploys automatically.

### Option C: Render / Railway (more control)
1. Create a new **Web Service** from your GitHub repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
4. Add `GROQ_API_KEY` as an environment variable in the dashboard.

**After deploying:** open the live link in an incognito window to confirm it works for a fresh user, then add the live link to this README.

---

## 🛠️ Suggested improvements (good "future work" talking points)

- Add a real data dictionary UI so users can describe their own columns for better RAG context
- Support multiple file formats (Excel, JSON)
- Persist chat history and past Q&A into the vector store so the agent "remembers" earlier questions in the session
- Add authentication if deploying for multiple users
- Swap the `exec()`-based sandbox for a properly isolated code execution service for production use

---

## 🖼️ Screenshots

<!-- Replace these with real screenshots before submitting/sharing.
     Take screenshots of your running app, save them in a `screenshots/`
     folder in the repo, and update the paths below. -->

| Auto Dashboard | Multi-Agent Chat |
|---|---|
| ![Dashboard](screenshots/dashboard.png) | ![Chat](screenshots/chat.png) |

---

## 👥 (BrainBots)

Built by a 4-person team as part of a college agentic AI project:

| Member | Focus area |
|---|---|
| [Name] | RAG layer (`rag/`) |
| [Name] | MCP tool server (`mcp_server/`) |
| [Name] | Multi-agent orchestration (`agent/graph.py`) |
| [Name] | Frontend + deployment (`app.py`, README) |

---

## 📄 License

MIT License — free to use, modify, and learn from. See `LICENSE` for details.

---

## 📚 Key libraries used

- [LangGraph](https://langchain-ai.github.io/langgraph/) — agent orchestration as a state graph
- [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) — bridges MCP tools into LangChain/LangGraph
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — defines the tool server
- [ChromaDB](https://www.trychroma.com/) + [sentence-transformers](https://www.sbert.net/) — RAG vector store and embeddings
- [Groq](https://groq.com/) — fast, free LLM inference (Llama 3.3)
- [Streamlit](https://streamlit.io/) — the interactive UI
