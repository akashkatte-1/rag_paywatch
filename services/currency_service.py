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
        # NOTE: Ensure your CURRENCY_API_URL is set to something like:
        # https://v6.exchangerate-api.com/v6/YOUR_API_KEY
        currency_api_url = os.getenv("CURRENCY_API_URL")

        # <-- CHANGED: Use the /pair endpoint for direct conversion
        response = requests.get(f"{currency_api_url}/pair/{from_currency}/{to_currency}")
        
        response.raise_for_status()
        data = response.json()
        
        # <-- CHANGED: Extract the rate from 'conversion_rate' key
        conversion_rate = data["conversion_rate"]
        
        return conversion_rate
    except requests.exceptions.RequestException as e:
        print(f"Error getting exchange rate: {e}")
        return None
    except KeyError:
        print(f"Error: 'conversion_rate' key not found in API response. Response was: {data}")
        return None