# Helper functions (e.g. extract video ID)

from typing import Any

def paginate_request(request: Any, limit: int = 300) -> list:
    results = []
    response = request.execute()
    results.extend(response.get("items", []))

    while "nextPageToken" in response and len(results) < limit:
        request = request.list_next(request, response)
        response = request.execute()
        results.extend(response.get("items", []))

    return results[:limit]
