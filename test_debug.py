import os
from mcp_server.server import load_dataframe, CURRENT_PATH_FILE, _load_current_df

print("Looking for the marker file at:", CURRENT_PATH_FILE)

load_dataframe("sample_data/sample_sales.csv")

print("Marker file exists after calling load_dataframe():", os.path.exists(CURRENT_PATH_FILE))

if os.path.exists(CURRENT_PATH_FILE):
    with open(CURRENT_PATH_FILE) as f:
        print("Marker file contents:", f.read())

df = _load_current_df()
print("Dataframe successfully loaded:", df is not None)
if df is not None:
    print(df.head())