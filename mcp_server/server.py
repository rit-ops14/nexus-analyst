"""
MCP SERVER
==========
Exposes the AI agent's tools: describe_dataframe, run_pandas_code,
generate_chart, send_email_report.

IMPORTANT DESIGN NOTE: this server runs as a SEPARATE process from the
Streamlit app. A normal Python variable set in app.py is NOT visible here
— each process has its own separate memory. To share which CSV is
currently active, we write its path to a small file ON DISK, using a
location calculated from server.py's own fixed file position (not the
"current working directory", which can differ between processes and was
the actual bug before this).
"""

from mcp.server.fastmcp import FastMCP
import pandas as pd
import io
import os
import base64
import smtplib
from email.mime.text import MIMEText
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Calculate an absolute, unambiguous location for the "which file is active"
# marker, based on where THIS server.py file physically sits on disk.
_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))       # .../agentic-data-analyst/mcp_server
_PROJECT_ROOT = os.path.dirname(_SERVER_DIR)                    # .../agentic-data-analyst
CURRENT_PATH_FILE = os.path.join(_PROJECT_ROOT, "sample_data", "_current_dataset.txt")

mcp = FastMCP("data-analyst-tools")


def load_dataframe(csv_path: str) -> None:
    """Called by the Streamlit app whenever the user uploads a new CSV.
    Saves the ABSOLUTE path so it can be found regardless of which
    process (Streamlit or the MCP subprocess) reads it later."""
    abs_path = os.path.abspath(csv_path)
    os.makedirs(os.path.dirname(CURRENT_PATH_FILE), exist_ok=True)
    with open(CURRENT_PATH_FILE, "w") as f:
        f.write(abs_path)


def _load_current_df() -> pd.DataFrame | None:
    """Every tool below calls this to get the current dataset."""
    if not os.path.exists(CURRENT_PATH_FILE):
        return None
    with open(CURRENT_PATH_FILE) as f:
        path = f.read().strip()
    if not path or not os.path.exists(path):
        return None
    return pd.read_csv(path)


@mcp.tool()
def describe_dataframe() -> str:
    """Returns shape, column names/types, and sample rows of the dataset."""
    df = _load_current_df()
    if df is None:
        return "No dataset has been uploaded yet."

    return (
        f"Shape: {df.shape[0]} rows, {df.shape[1]} columns\n"
        f"Columns and types:\n{df.dtypes.to_string()}\n\n"
        f"First 3 rows:\n{df.head(3).to_string()}"
    )


@mcp.tool()
def run_pandas_code(code: str) -> str:
    """Executes pandas code (uses `df`), must set a variable called `result`."""
    df = _load_current_df()
    if df is None:
        return "No dataset has been uploaded yet."

    safe_globals = {"pd": pd, "df": df}
    try:
        exec(code, safe_globals)
        result = safe_globals.get("result", "Code ran, but no `result` variable was set.")
        return str(result)
    except Exception as e:
        return f"Error while running code: {e}"


@mcp.tool()
def generate_chart(code: str) -> str:
    """Executes matplotlib code (uses `df`, `plt`), returns base64 PNG."""
    df = _load_current_df()
    if df is None:
        return "No dataset has been uploaded yet."

    safe_globals = {"pd": pd, "df": df, "plt": plt}
    plt.figure(figsize=(7, 4))

    try:
        exec(code, safe_globals)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except Exception as e:
        plt.close()
        return f"Error while generating chart: {e}"


@mcp.tool()
def send_email_report(recipient_email: str, subject: str, body: str) -> str:
    """
    Emails a text summary via Brevo's SMTP relay (free tier, no Gmail
    App Password required).
    """
    sender = os.environ.get("EMAIL_ADDRESS")
    smtp_login = os.environ.get("BREVO_SMTP_LOGIN")
    smtp_key = os.environ.get("BREVO_SMTP_KEY")

    if not sender or not smtp_login or not smtp_key:
        return (
            "Email not sent: EMAIL_ADDRESS / BREVO_SMTP_LOGIN / BREVO_SMTP_KEY "
            "are missing from your .env file."
        )

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient_email

        with smtplib.SMTP("smtp-relay.brevo.com", 587) as server:
            server.starttls()
            server.login(smtp_login, smtp_key)
            server.sendmail(sender, [recipient_email], msg.as_string())

        return f"Email sent successfully to {recipient_email}."
    except Exception as e:
        return f"Error while sending email: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")