import requests
import os
from langchain.agents import tool

@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """
    This tool gets the current exchange rate between two currencies.
    Use this to get real-time currency conversion rates.
    """
    try:
        # Using a free and reliable API (e.g., from exchangerate-api.com)
        # You must have a free API key from a provider like CurrencyApi or Open Exchange Rates.
        currency_api_url = os.getenv("CURRENCY_API_URL")
        response = requests.get(f"{currency_api_url}/latest?from={from_currency}&to={to_currency}")
        response.raise_for_status()
        data = response.json()
        usd_rate = data["rates"][to_currency]
        return usd_rate
    except requests.exceptions.RequestException as e:
        print(f"Error getting exchange rate: {e}")
        return None