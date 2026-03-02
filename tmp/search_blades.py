
import json

def search():
    try:
        with open('data/cards.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return

    results = []
    if isinstance(data, dict):
        for card_no, card_data in data.items():
            ability = card_data.get('ability', '')
            if 'ブレード' in ability:
                results.append(f"{card_no}: {ability}")
    
    for r in results:
        print(r)

if __name__ == "__main__":
    search()
