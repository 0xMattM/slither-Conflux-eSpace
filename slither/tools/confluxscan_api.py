import requests

class ConfluxScanAPI:
    def __init__(self, api_key=None):
        self.api_url = "https://api.confluxscan.org"  # Core Space API
        self.api_key = api_key  # No se necesita para getsourcecode

    def get_source_code(self, contract_address):
        url = f"{self.api_url}/contract/getsourcecode"
        params = {
            "address": contract_address
        }

        response = requests.get(url, params=params)

        try:
            data = response.json()
        except Exception as e:
            raise Exception(f"Invalid JSON response: {e}")

        # Aquí depende de cómo responda la API de ConfluxScan
        if data.get('code') != 0:
            raise Exception(f"Error from ConfluxScan API: {data.get('message')}")

        return data.get('data', {})
