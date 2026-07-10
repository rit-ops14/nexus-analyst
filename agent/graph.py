"""
AGENT GRAPH — MULTI-AGENT SUPERVISOR DESIGN
============================================
DESIGN NOTE: instead of relying on the LLM to reliably chain multiple
"tool calls" together, each specialist agent follows a fixed sequence:
  1. WE always fetch the schema first (describe_dataframe) — not optional
  2. WE ask the LLM to write plain-text pandas/matplotlib code
  3. WE always execute that code via the tool
"""
print("🟢🟢🟢 GRAPH.PY VERSION 3 LOADED 🟢🟢🟢")

import asyncio
import json
import re
import sys
import os
from typing import TypedDict, Annotated
import operator

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from rag.retrieve import retrieve_context as rag_retrieve


class AgentState(TypedDict):
    question: str
    context: str
    needs_data: bool
    needs_chart: bool
    email_address: str | None
    data_result: str
    chart_base64: str | None
    tool_calls_made: int
    steps_log: Annotated[list[str], operator.add]
    final_answer: str


llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Compute the MCP server's exact absolute path, and use the SAME Python
# interpreter that's currently running this file (sys.executable) instead
# of guessing "python" as a command name. This matters because different
# environments (your laptop vs. Streamlit Cloud) may only expose "python3"
# or a specific virtualenv path — sys.executable is always correct,
# everywhere, since it's literally "whichever interpreter is running me."
_AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_AGENT_DIR)
_MCP_SERVER_PATH = os.path.join(_PROJECT_ROOT, "mcp_server", "server.py")

MCP_SERVER_CONFIG = {
    "data_tools": {
        "command": sys.executable,
        "args": [_MCP_SERVER_PATH],
        "transport": "stdio",
    }
}


def _extract_code(llm_text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", llm_text, re.DOTALL)
    return match.group(1).strip() if match else llm_text.strip()


def retrieve_node(state: AgentState) -> dict:
    context = rag_retrieve(state["question"])
    return {
        "context": context,
        "steps_log": ["🔍 Retrieved relevant column info from the knowledge base."],
    }


def supervisor_node(state: AgentState) -> dict:
    prompt = f"""
    You are a supervisor agent managing a small team: a Data Analyst Agent
    and a Visualization Agent. Read the user's question and decide what's
    needed. Respond with ONLY a JSON object, nothing else, like this:

    {{"needs_data": true, "needs_chart": false, "email_address": null}}

    - needs_data: true if the question asks for a number, comparison, or fact from the data
    - needs_chart: true if the user explicitly asks to see/show/plot/visualize something
    - email_address: the email address if the user asks to email/send the result somewhere, else null

    User question: {state['question']}
    """
    response = llm.invoke(prompt)

    try:
        decision = json.loads(response.content.strip().strip("`"))
    except (json.JSONDecodeError, AttributeError):
        decision = {"needs_data": True, "needs_chart": False, "email_address": None}

    return {
        "needs_data": decision.get("needs_data", True),
        "needs_chart": decision.get("needs_chart", False),
        "email_address": decision.get("email_address"),
        "steps_log": [
            f"🧭 Supervisor Agent plan: data={decision.get('needs_data')}, "
            f"chart={decision.get('needs_chart')}, email={decision.get('email_address')}"
        ],
    }


async def data_analyst_node(state: AgentState) -> dict:
    client = MultiServerMCPClient(MCP_SERVER_CONFIG)
    tools = await client.get_tools()
    describe_tool = next(t for t in tools if t.name == "describe_dataframe")
    run_tool = next(t for t in tools if t.name == "run_pandas_code")

    schema_info = await describe_tool.ainvoke({})

    code_prompt = f"""
    You are a data analyst. Here is the exact schema of the dataset:
    {schema_info}

    User question: {state['question']}

    Write ONLY pandas code, nothing else — no explanation, no markdown
    fences, no comments. The dataframe is called `df`. Assign your final
    answer to a variable called `result`. Example format:
    result = df.groupby("region")["revenue"].mean()
    """
    code_response = llm.invoke(code_prompt)
    code = _extract_code(code_response.content)

    output = await run_tool.ainvoke({"code": code})

    return {
        "data_result": str(output),
        "tool_calls_made": state.get("tool_calls_made", 0) + 1,
        "steps_log": [f"📊 Data Analyst Agent ran: `{code}`"],
    }


async def visualization_node(state: AgentState) -> dict:
    client = MultiServerMCPClient(MCP_SERVER_CONFIG)
    tools = await client.get_tools()
    describe_tool = next(t for t in tools if t.name == "describe_dataframe")
    chart_tool = next(t for t in tools if t.name == "generate_chart")

    schema_info = await describe_tool.ainvoke({})

    code_prompt = f"""
    Here is the exact schema of the dataset:
    {schema_info}

    User question: {state['question']}

    Write ONLY matplotlib code, nothing else — no explanation, no markdown
    fences, no comments. The dataframe is called `df`, matplotlib.pyplot
    is called `plt`. Just write the plotting code directly.
    """
    code_response = llm.invoke(code_prompt)
    code = _extract_code(code_response.content)

    chart = await chart_tool.ainvoke({"code": code})

    return {
        "chart_base64": chart,
        "steps_log": [f"📈 Visualization Agent ran: `{code}`"],
    }


async def communicator_node(state: AgentState) -> dict:
    prompt = (
        f"User asked: {state['question']}\n"
        f"Data Analyst Agent's result: {state.get('data_result', 'N/A')}\n\n"
        "State the actual result/number clearly first, then explain it in "
        "1-2 friendly sentences for someone who isn't a data expert. "
        "Don't mention code or tools."
    )
    response = llm.invoke(prompt)
    final_answer = response.content
    steps = ["💬 Communicator Agent wrote the final plain-English answer."]

    if state.get("email_address"):
        client = MultiServerMCPClient(MCP_SERVER_CONFIG)
        tools = await client.get_tools()
        email_tool = next(t for t in tools if t.name == "send_email_report")
        result = await email_tool.ainvoke({
            "recipient_email": state["email_address"],
            "subject": "Your Data Analyst Agent Report",
            "body": final_answer,
        })
        steps.append(f"📧 Communicator Agent sent the email: {result}")

    return {"final_answer": final_answer, "steps_log": steps}


def route_from_supervisor(state: AgentState) -> str:
    if state.get("needs_data"):
        return "data_analyst"
    if state.get("needs_chart"):
        return "visualization"
    return "communicator"


def route_from_data_analyst(state: AgentState) -> str:
    if state.get("needs_chart"):
        return "visualization"
    return "communicator"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve", retrieve_node)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("data_analyst", data_analyst_node)
    graph.add_node("visualization", visualization_node)
    graph.add_node("communicator", communicator_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "supervisor")

    graph.add_conditional_edges(
        "supervisor", route_from_supervisor,
        {"data_analyst": "data_analyst", "visualization": "visualization", "communicator": "communicator"},
    )
    graph.add_conditional_edges(
        "data_analyst", route_from_data_analyst,
        {"visualization": "visualization", "communicator": "communicator"},
    )
    graph.add_edge("visualization", "communicator")
    graph.add_edge("communicator", END)

    return graph.compile()


def run_agent(question: str) -> AgentState:
    app = build_graph()
    initial_state: AgentState = {
        "question": question,
        "context": "",
        "needs_data": True,
        "needs_chart": False,
        "email_address": None,
        "data_result": "",
        "chart_base64": None,
        "tool_calls_made": 0,
        "steps_log": [],
        "final_answer": "",
    }
    return asyncio.run(app.ainvoke(initial_state))