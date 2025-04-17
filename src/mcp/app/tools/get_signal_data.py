import os

from app.server import mcp


# curl -X POST http://127.0.0.1:8000/mcp/get_signal_data -H "Content-Type: application/json" -d {}
@mcp.tool(name="get_signal_data", description="Return a dict")
def get_signal_data():
    return {"signal": "example_signal_data"}


# curl -X POST http://127.0.0.1:8000/mcp/get_file_data -H "Content-Type: application/json" -d '{"filename":"scanlist_out.json"}'
@mcp.tool(name="get_file_data", description="Read log data")
def get_file_data(filename: str) -> list:
    import pandas as pd
    df = pd.read_json(f"app/data/{filename}")
    return df.to_dict(orient="records")


#  curl -X POST http://127.0.0.1:8000/mcp/scan -H "Content-Type: application/json" -d '{"freq_range":"1000"}'
@mcp.tool(name="scan", description="Scan frequencies")
def exec_scan(freq_range: str) -> dict:
    from mcp-flask.fauxtrx.FAKETRXUSBRetriever import FAKETRXUSBRetriever
    scanner = FAKETRXUSBRetriever()
    scanner.set_freq(freq_range)
    scanned = scanner.scan()
    return scanned
