import json


def create_embedded_html():
    # 1. Load deck data
    deck_data = {
        "PL!-bp3-026-L": 1,
        "PL!-pb1-008-R": 4,
        "PL!-pb1-015-R": 2,
        "PL!-sd1-002-SD": 2,
        "PL!HS-bp2-012-N": 4,
        "PL!N-bp1-026-L": 3,
        "PL!N-bp1-034-PE": 1,
        "PL!N-bp1-035-PE": 1,
        "PL!N-bp1-036-PE": 1,
        "PL!N-bp1-037-PE": 1,
        "PL!N-bp1-038-PE": 1,
        "PL!N-bp3-004-R": 2,
        "PL!N-bp3-016-N": 2,
        "PL!N-bp3-022-N": 4,
        "PL!N-bp3-027-L": 4,
        "PL!N-bp3-031-L": 4,
        "PL!N-bp3-037-PE": 1,
        "PL!N-bp3-038-PE": 1,
        "PL!N-bp3-039-PE": 1,
        "PL!N-bp4-020-N": 4,
        "PL!N-bp4-038-PE": 1,
        "PL!N-bp4-039-PE": 1,
        "PL!N-bp4-040-PE": 1,
        "PL!N-bp4-041-PE": 1,
        "PL!N-pb1-004-R": 1,
        "PL!N-pb1-008-R": 2,
        "PL!N-pb1-034-N": 4,
        "PL!N-sd1-011-SD": 3,
        "PL!S-pb1-004-R": 3,
        "PL!SP-bp1-020-N": 4,
        "PL!SP-bp2-009-R＋": 4,
    }

    # 2. Load all cards
    with open("data/cards.json", "r", encoding="utf-8") as f:
        all_cards = json.load(f)

    # 3. Extract subset
    subset_cards = {}
    for cid in deck_data.keys():
        if cid in all_cards:
            subset_cards[cid] = all_cards[cid]
        else:
            print(f"Warning: Card {cid} not found in DB")
            subset_cards[cid] = {"name": "Unknown", "img": "", "type": "Unknown"}

    # 4. Generate HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deck Viewer (Embedded)</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-size: 2rem;
            background: linear-gradient(90deg, #ff6b9d, #c44dff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{ text-align: center; margin-bottom: 30px; color: #aaa; }}
        .deck-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .card-item {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 10px;
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(196, 77, 255, 0.3);
        }}
        .card-item img {{
            width: 100%;
            border-radius: 8px;
            margin-bottom: 8px;
            aspect-ratio: 219/306;
            object-fit: contain;
            background: #000;
        }}
        .card-name {{
            font-size: 0.85rem;
            color: #fff;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .card-type {{
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 10px;
            display: inline-block;
            margin-bottom: 4px;
        }}
        .card-type.member {{ background: #4CAF50; }}
        .card-type.live {{ background: #2196F3; }}
        .card-type.energy {{ background: #FF9800; }}
        .card-count {{ font-size: 1.2rem; font-weight: bold; color: #ff6b9d; }}
        .card-id {{ font-size: 0.65rem; color: #666; margin-top: 4px; }}
    </style>
</head>
<body>
    <h1>Deck Viewer</h1>
    <div class="stats" id="stats">Loading...</div>
    <div class="deck-grid" id="deck-grid"></div>

    <script>
        const deckData = {json.dumps(deck_data)};
        const cardsDb = {json.dumps(subset_cards, ensure_ascii=False)};

        const grid = document.getElementById('deck-grid');
        let totalCards = 0;
        let memberCount = 0;
        let liveCount = 0;
        let energyCount = 0;

        for (const [cardId, count] of Object.entries(deckData)) {{
            totalCards += count;
            const card = cardsDb[cardId];

            const item = document.createElement('div');
            item.className = 'card-item';

            const type = card.type || 'Unknown';
            const typeClass = type.includes('メンバー') ? 'member' :
                             type.includes('ライブ') ? 'live' :
                             type.includes('エネルギー') ? 'energy' : '';

            if (typeClass === 'member') memberCount += count;
            else if (typeClass === 'live') liveCount += count;
            else if (typeClass === 'energy') energyCount += count;

            // Use local image path (_img) if available, otherwise remote (img)
            const imgSrc = card._img || card.img || '';

            item.innerHTML = `
                <img src="${{imgSrc}}" alt="${{card.name}}" loading="lazy" onerror="this.src='https://via.placeholder.com/150x210?text=No+Image'">
                <div class="card-name">${{card.name}}</div>
                <span class="card-type ${{typeClass}}">${{type}}</span>
                <div class="card-count">×${{count}}</div>
                <div class="card-id">${{cardId}}</div>
            `;
            grid.appendChild(item);
        }}

        document.getElementById('stats').textContent =
            `Total: ${{totalCards}} cards | Members: ${{memberCount}} | Live: ${{liveCount}} | Energy: ${{energyCount}} | Unique: ${{Object.keys(deckData).length}}`;
    </script>
</body>
</html>
"""

    with open("deck_viewer_embedded.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("Created deck_viewer_embedded.html")


if __name__ == "__main__":
    create_embedded_html()
