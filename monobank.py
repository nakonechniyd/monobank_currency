import requests


def get_currency() -> list[dict]:
    resp = requests.get('https://api.monobank.ua/bank/currency')
    if not resp.ok:
        print('Not 200 from monobank')
        return []
    return resp.json()
