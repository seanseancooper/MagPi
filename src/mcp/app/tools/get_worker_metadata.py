from app.server import mcp

from src.mcp.xrx.XRXSignalGenerator import XRXSignalGenerator


#   curl -X POST http://127.0.0.1:8000/mcp/get_worker_metadata -H "Content-Type: application/json" -d '{"worker_id": "12345"}'
@mcp.tool()
def get_worker_metadata(worker_id: str) -> dict:
    """Retrieve worker metadata by ID."""
    scanner = XRXSignalGenerator()
    scanner.set_freq(1000)
    scanned = scanner.scan()
    return {"scan": scanned} if scanned else {}

    # while scanned:
    #     worker = scanned[random.randint(1, len(scanned))]
    #     return {
    #         "worker_id": worker.get("worker_id"),
    #         "is_tracked": worker.get("is_tracked"),
    #         "location": {
    #             "lat": worker.get("lat"),
    #             "lon": worker.get("lon")
    #         }
    #     }
