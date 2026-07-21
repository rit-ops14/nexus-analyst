# 🧠 Nexus Analyst

**A multi-agent AI system for conversational data analysis.**

**Built with:** Python 3.10+ · LangGraph · Streamlit · MCP · Groq (Llama 3.3 70B) · ChromaDB · MIT License

*Built by Team BrainBots — SIP 2026 Capstone, Department of Information Technology, Indira Gandhi Delhi Technical University for Women.*

Upload a CSV, ask "what's the average revenue by region?", and watch a
Supervisor Agent delegate to a Data Analyst Agent and a Visualization
Agent in real time — with the full reasoning trail visible, not hidden
behind a black box.

🔗 **[Live demo](https://nexus-analyst-m3b3ksgokgfckjeiv4jm8u.streamlit.app)**

---

## ✨ Why this project stands out

- 🤖 **Real multi-agent collaboration** — not one AI doing everything, but a Supervisor delegating to specialist agents, LangGraph-style
- 🔌 **MCP-based tools** — the agents' tools (data analysis, charts, email) live in a standard Model Context Protocol server, decoupled from the reasoning logic
- 📚 **RAG-computed retrieval layer** — a ChromaDB vector store computes the most relevant columns for every question; schema grounding for code generation currently happens through a direct `describe_dataframe` tool call, with full integration of the RAG-retrieved subset into agent prompts planned as future work
- 📈 **Interactive dashboard** — real pandas + Plotly analysis runs the moment you upload data, no question needed
- 📧 **Agents that take real action** — the Communicator Agent can actually send an email report via Brevo's SMTP relay, not just display text
- 🧑‍🤝‍🧑 **Full transparency** — every response shows exactly which agents ran and what code they executed

---

## 🧠 How it works (architecture)

This project uses a **multi-agent supervisor architecture** — instead of
one AI trying to do everything, a small TEAM of specialist agents
collaborates, coordinated by a Supervisor Agent.

```
User types a question
        │
        ▼
┌───────────────────────────┐
│      Streamlit UI         │
│        (app.py)           │
└─────────────┬──────────────┘
              │
              ▼
┌───────────────────────────┐
│      RAG Retrieval        │
│   (rag/retrieve.py)       │
│   finds relevant columns  │
└─────────────┬──────────────┘
              ▼
┌───────────────────────────┐
│      Supervisor Agent     │   "What does this
│    (agent/graph.py)       │    question need?"
└──────┬─────────┬───────────┘
       │         │
 needs_data   needs_chart
       │         │
       ▼         ▼
┌─────────────────┐   ┌──────────────────┐
│  Data Analyst    │   │  Visualization    │
│     Agent        │   │      Agent        │
│ (runs pandas via  │   │ (draws charts via │
│    MCP tool)      │   │    MCP tool)      │
└────────┬─────────┘   └─────────┬─────────┘
         └─────────┬─────────────┘
                    ▼
        ┌───────────────────────────┐
        │    Communicator Agent     │
        │  writes final answer,     │
        │   emails if requested     │
        └───────────────────────────┘
```

### The four concepts, and exactly where they live

| Concept | Where | What it actually does here |
|---|---|---|
| **LLM** | Every agent in `agent/graph.py` (via `ChatGroq`, Llama 3.3 70B on Groq) | Each specialist agent uses the LLM for its own narrow job — planning, analysis, chart code, or communication |
| **RAG** | `rag/ingest.py`, `rag/retrieve.py` | Stores column names/types/samples in a ChromaDB vector store; retrieves the most relevant columns for a given question on every request. Schema grounding for code generation currently happens via a direct `describe_dataframe` MCP tool call rather than this retrieved subset |
| **MCP** | `mcp_server/server.py` | Exposes shared tools (`describe_dataframe`, `run_pandas_code`, `generate_chart`, `send_email_report`) that ANY agent can call — the tools are decoupled from any one agent |
| **Multi-Agent Collaboration** | `agent/graph.py` | A **Supervisor Agent** plans and delegates to a **Data Analyst Agent** and a **Visualization Agent**, then a **Communicator Agent** finalizes the response — four distinct specialists, each with one job |
| **LangGraph** | `agent/graph.py` | Implements the whole team as an explicit state graph with conditional routing — `route_from_supervisor()` is the delegation logic |

Each folder = one concept, and each **agent function** in `agent/graph.py`
— `supervisor_node`, `data_analyst_node`, `visualization_node`,
`communicator_node` — is one team member's job, visible and readable,
not a black box.

---

## 📁 Folder structure

```
nexus-analyst/
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── app.py
├── test_debug.py
├── test_agent.py
├── test_email.py
├── agent/
│   └── graph.py
├── mcp_server/
│   └── server.py
├── rag/
│   ├── ingest.py
│   └── retrieve.py
└── sample_data/
    └── sample_sales.csv
```

---

## 🚀 Setup (local)

**1. Clone and enter the project**
```bash
git clone https://github.com/rit-ops14/nexus-analyst.git
cd nexus-analyst
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
```
Then edit `.env` and paste your free Groq API key (get one at https://console.groq.com/keys).

**5. Run the app**
```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`),
upload `sample_data/sample_sales.csv`, and:
- Check the **Auto Dashboard** tab immediately — it's already showing real stats and charts
- Switch to **Ask the Agent** and try:
  - "What's the average revenue by region?"
  - "Show me a bar chart of profit by category"
  - "Which region sold the most units?"
  - "Email the average revenue by region to your.email@example.com" (needs email setup below)

**Optional: enable the email feature**

The email tool sends via Brevo's free SMTP relay (no Gmail App Password needed):
1. Create a free account at https://www.brevo.com
2. Go to SMTP & API settings and generate an SMTP key
3. Add these three values to `.env`: `EMAIL_ADDRESS`, `BREVO_SMTP_LOGIN`, `BREVO_SMTP_KEY`

If you skip this, everything else still works — the email tool will just report the missing credentials instead of crashing.

---

## ☁️ Deployment

### Streamlit Community Cloud (used for the live demo)

1. Push this repo to GitHub (`.env` is already in `.gitignore` — never commit real API keys).
2. Go to https://share.streamlit.io, sign in with GitHub.
3. Click "New app", select this repo, set the main file to `app.py`.
4. Under "Advanced settings → Secrets", add:
```
GROQ_API_KEY = "your_real_key_here"
EMAIL_ADDRESS = "your_sender_email"
BREVO_SMTP_LOGIN = "your_brevo_login"
BREVO_SMTP_KEY = "your_brevo_smtp_key"
```
5. Deploy. Streamlit Cloud installs `requirements.txt` automatically.
6. The MCP server launches automatically as a subprocess of the agent — no separate manual step is needed.

---

## 🛠️ Known limitations & future work

- The Data Analyst and Visualization agents execute LLM-generated code with Python's `exec()` — fine for this project, but not a production-safe sandbox
- Only a single CSV per session is supported — no multi-file joins yet
- The RAG layer's retrieved column subset is computed on every question but not yet wired into the Data Analyst/Visualization prompts — schema grounding currently relies on a direct `describe_dataframe` call instead
- No memory of past questions within or across sessions
- Planned next: sandboxed code execution, multi-file support (Excel/JSON), authentication for multi-user deployment, and a dedicated Data Quality/Validation agent

---

## 👥 Team BrainBots

| Member | Focus area |
|---|---|
| Ritika Tiwari | Multi-agent orchestration (`agent/graph.py`), LangGraph state design, final documentation |
| Samarpita Das | RAG layer (`rag/ingest.py`, `rag/retrieve.py`), ChromaDB integration |
| Rishika Asthana | MCP tool server (`mcp_server/server.py`), email integration and debugging |
| Ritu Popli | Streamlit frontend (`app.py`), deployment, README and repository polish |

---

## 📄 License

MIT License — free to use, modify, and learn from. See `LICENSE` for details.

---

## 📚 Key libraries used

- [LangGraph](https://langchain-ai.github.io/langgraph/) — agent orchestration as a state graph
- [langchain-mcp-adapters](https://github.com/langchain-ai/langchain-mcp-adapters) — bridges MCP tools into LangChain/LangGraph
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — defines the tool server
- [ChromaDB](https://www.trychroma.com/) + [sentence-transformers](https://www.sbert.net/) — RAG vector store and embeddings
- [Groq](https://groq.com/) — fast, free LLM inference (Llama 3.3 70B)
- [Streamlit](https://streamlit.io/) — the interactive UI
