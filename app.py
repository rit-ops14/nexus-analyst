"""
STREAMLIT APP
=============
The user-facing interface for the agent. Upload a CSV, ask a question in
plain English, and watch the agent think and answer.
"""

import base64
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from rag.ingest import build_knowledge_base
from mcp_server.server import load_dataframe, send_email_report
from agent.graph import run_agent

load_dotenv()

st.set_page_config(page_title="Nexus Analyst", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
    .main-title   { font-size: 2.6rem; font-weight: 800; margin-bottom: 0;
                background: linear-gradient(90deg, #6c63ff, #00c9a7);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text; letter-spacing: -0.5px; }
.subtitle     { color: #9a9a9a; margin-top: 0.3rem; font-size: 1.1rem; }
</parameter>
    .step-box     { background-color: #f6f5ff; border-left: 4px solid #6c63ff;
                    padding: 0.55rem 1rem; border-radius: 8px; margin-bottom: 0.4rem;
                    font-size: 0.92rem; color: #2b2b2b; }
    .answer-box   { background-color: #eefcf3; border: 1px solid #b7e4c7;
                    padding: 1rem 1.2rem; border-radius: 12px; font-size: 1.05rem;
                    color: #1a3d2b; }
    .metric-card  { background-color: #fafafa; border: 1px solid #eee;
                    border-radius: 10px; padding: 0.8rem; text-align: center;
                    color: #2b2b2b; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-title">🧠 NEXUS ANALYST</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">A multi-agent AI system for conversational data analysis — '
    'built by Team BrainBots.</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("1️⃣ Upload your data")
    uploaded_file = st.file_uploader("CSV file", type=["csv"])

    if uploaded_file:
        csv_path = f"sample_data/{uploaded_file.name}"
        with open(csv_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df_preview = pd.read_csv(csv_path)

        col1, col2 = st.columns(2)
        col1.markdown(f'<div class="metric-card"><b>{df_preview.shape[0]}</b><br>rows</div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="metric-card"><b>{df_preview.shape[1]}</b><br>columns</div>', unsafe_allow_html=True)

        st.markdown("**Preview**")
        st.dataframe(df_preview.head(5), use_container_width=True)

        with st.spinner("Indexing dataset for the agent..."):
            load_dataframe(csv_path)
            build_knowledge_base(csv_path)
        st.session_state["data_ready"] = True
        st.session_state["csv_path"] = csv_path
        st.success("Dataset ready — check the Dashboard tab or ask a question!")

    st.divider()
    st.caption(
        "💡 Try questions like:\n"
        "- What's the average sales by region?\n"
        "- Show me a bar chart of revenue by month\n"
        "- Which category has the highest profit?\n"
        "- Email the average revenue by region to me@example.com"
    )

    st.divider()
    st.header("2️⃣ Email a quick summary")
    st.caption("Sends the auto-generated dashboard summary below, straight from this button.")
    recipient = st.text_input("Recipient email", placeholder="you@example.com")
    if st.button("📧 Send summary email"):
        if not st.session_state.get("data_ready"):
            st.warning("Upload a CSV first.")
        elif not recipient:
            st.warning("Enter a recipient email first.")
        else:
            summary_text = st.session_state.get("summary_text", "No summary available yet.")
            with st.spinner("Sending..."):
                result = send_email_report(
                    recipient_email=recipient,
                    subject="Your Data Analyst Agent Report",
                    body=summary_text,
                )
            st.info(result)

tab_dashboard, tab_chat = st.tabs(["📈 Auto Dashboard", "💬 Ask the Agent"])

with tab_dashboard:
    if not st.session_state.get("data_ready"):
        st.info("⬅️ Upload a CSV from the sidebar to see your dashboard here.")
    else:
        df = pd.read_csv(st.session_state["csv_path"])
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

        st.subheader("Summary statistics")
        st.dataframe(df.describe(), use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            if numeric_cols:
                chosen_num = st.selectbox("Numeric column to explore", numeric_cols)
                fig = px.histogram(df, x=chosen_num, title=f"Distribution of {chosen_num}")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if numeric_cols and categorical_cols:
                chosen_cat = st.selectbox("Group by (categorical column)", categorical_cols)
                grouped = df.groupby(chosen_cat)[numeric_cols[0]].mean().reset_index()
                fig2 = px.bar(
                    grouped, x=chosen_cat, y=numeric_cols[0],
                    title=f"Average {numeric_cols[0]} by {chosen_cat}"
                )
                st.plotly_chart(fig2, use_container_width=True)

        if len(numeric_cols) > 1:
            st.subheader("Correlation between numeric columns")
            corr = df[numeric_cols].corr()
            fig3 = px.imshow(corr, text_auto=True, title="Correlation heatmap")
            st.plotly_chart(fig3, use_container_width=True)

        st.session_state["summary_text"] = (
            f"Dataset summary ({df.shape[0]} rows, {df.shape[1]} columns)\n\n"
            f"{df.describe().to_string()}"
        )

with tab_chat:
    if "history" not in st.session_state:
        st.session_state["history"] = []

    question = st.chat_input("e.g. What's the average sales by region?")

    if question:
        if not st.session_state.get("data_ready"):
            st.warning("Please upload a CSV first.")
        else:
            with st.spinner("🤖 Agent is thinking..."):
                result = run_agent(question)
            st.session_state["history"].append((question, result))

    for q, result in reversed(st.session_state["history"]):
        with st.chat_message("user"):
            st.write(q)

        with st.chat_message("assistant"):
            with st.expander("🧑‍🤝‍🧑 See which agents worked on this"):
                for step in result["steps_log"]:
                    st.markdown(f'<div class="step-box">{step}</div>', unsafe_allow_html=True)

            st.markdown(f'<div class="answer-box">{result["final_answer"]}</div>', unsafe_allow_html=True)

            chart = result.get("chart_base64")
            if chart and "Error" not in chart:
                st.image(base64.b64decode(chart), caption="Generated chart", use_container_width=True)