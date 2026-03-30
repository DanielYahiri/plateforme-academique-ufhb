import httpx
from config import SUPABASE_URL, SUPABASE_HEADERS

def _headers(schema: str) -> dict:
    h = SUPABASE_HEADERS.copy()
    if schema != "public":
        h["Accept-Profile"] = schema
    return h

def _rpc_headers(schema: str) -> dict:
    h = SUPABASE_HEADERS.copy()
    if schema != "public":
        h["Content-Profile"] = schema
    return h

async def fetch_view(view: str, schema: str, limit: int = 1000) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{view}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            url,
            headers=_headers(schema),
            params={"select": "*", "limit": str(limit)},
        )
    r.raise_for_status()
    return r.json()

async def call_rpc(func: str, schema: str, params: dict) -> list:
    url = f"{SUPABASE_URL}/rest/v1/rpc/{func}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            url,
            headers=_rpc_headers(schema),
            json=params
        )
    r.raise_for_status()
    return r.json()
async def fetch_recent(table: str, schema: str, order_col: str, limit: int = 5) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            url,
            headers=_headers(schema),
            params={
                "select": "*",
                "order": f"{order_col}.desc",
                "limit": str(limit)
            },
        )
    r.raise_for_status()
    return r.json()

async def fetch_filtered(table: str, schema: str, filters: dict, limit: int = 50) -> list:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"select": "*", "limit": str(limit)}
    for key, value in filters.items():
        params[key] = f"eq.{value}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            url,
            headers=_headers(schema),
            params=params,
        )
    r.raise_for_status()
    return r.json()