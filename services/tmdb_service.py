import requests
from config import TMDB_API_KEY, TMDB_BASE_URL

def safe_request(endpoint, params=None):
    try:
        if params is None: params = {}
        params["api_key"] = TMDB_API_KEY
        response = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=10)
        return response.json()
    except:
        return {}

def search_multi(query): return safe_request("/search/multi", {"query": query})
def get_details(m_type, m_id): return safe_request(f"/{m_type}/{m_id}")
def get_credits(m_type, m_id): return safe_request(f"/{m_type}/{m_id}/credits")
def get_recommendations(m_type, m_id): return safe_request(f"/{m_type}/{m_id}/recommendations")