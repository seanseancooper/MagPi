from app.server import mcp


#   curl -X POST http://127.0.0.1:8000/mcp/get_worker_metadata -H "Content-Type: application/json" -d '{"worker_id": "12345"}'
@mcp.tool()
def get_worker_metadata(worker_id: str) -> dict:
    """Retrieve worker metadata by ID."""
    return {
        "worker_id": worker_id,
        "status": "active",
        "location": {
            "lat": 0.0,
            "lon": 0.0
        }
    }
