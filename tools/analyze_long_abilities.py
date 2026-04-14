import json
import sys
from pathlib import Path
from typing import Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    with open(cards_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_ability(ability_text: str) -> dict[str, Any]:
    """Analyze a single ability and break it down into components."""
    analysis = {
        "original": ability_text,
        "sentences": [],
        "components": []
    }
    
    # Split by newlines to get separate sentences
    sentences = ability_text.split('\n')
    
    for sentence in sentences:
        if not sentence.strip():
            continue
            
        sentence_analysis = {
            "original": sentence,
            "triggers": [],
            "conditions": [],
            "effects": [],
            "costs": [],
            "game_terms": [],
            "particles": []
        }
        
        # Identify triggers (icons with {{...}})
        import re
        triggers = re.findall(r'\{\{[^}]+\}\}', sentence)
        sentence_analysis["triggers"] = triggers
        
        # Remove triggers for further analysis
        text_without_triggers = sentence
        for trigger in triggers:
            text_without_triggers = text_without_triggers.replace(trigger, "【TRIGGER】")
        
        # Identify common game terms
        game_terms = [
            "自分", "相手", "手札", "ステージ", "控え室", "デッキ", 
            "成功ライブカード置き場", "エネルギー", "ブレード", "ハート",
            "スコア", "コスト", "メンバー", "ライブカード", "メンバーカード",
            "エネルギーカード", "ライブ終了時", "登場", "起動", "常時",
            "アクティブ", "ウェイト", "公開", "見る", "置く", "加える",
            "得る", "支払う", "選ぶ"
        ]
        
        found_terms = []
        for term in game_terms:
            if term in text_without_triggers:
                found_terms.append(term)
        sentence_analysis["game_terms"] = found_terms
        
        # Identify particles (Japanese grammatical particles)
        particles = ["の", "を", "に", "が", "から", "で", "と", "へ"]
        found_particles = []
        for particle in particles:
            if particle in text_without_triggers:
                found_particles.append(particle)
        sentence_analysis["particles"] = found_particles
        
        # Identify numbers
        numbers = re.findall(r'\d+', text_without_triggers)
        sentence_analysis["numbers"] = numbers
        
        # Identify card groups (『...』)
        groups = re.findall(r'『([^』]+)』', text_without_triggers)
        sentence_analysis["groups"] = groups
        
        # Identify card names (「...」)
        card_names = re.findall(r'「([^」]+)」', text_without_triggers)
        sentence_analysis["card_names"] = card_names
        
        analysis["sentences"].append(sentence_analysis)
    
    return analysis

def main():
    cards_file = Path("data/cards.json")
    cards = load_cards(cards_file)
    
    # Find long abilities (> 100 characters)
    long_abilities = []
    for card_id, card in cards.items():
        ability = card.get("ability", "")
        if ability and len(ability) > 100:
            long_abilities.append({
                "card_id": card_id,
                "card_name": card.get("name", ""),
                "ability": ability
            })
    
    # Sort by length (longest first)
    long_abilities.sort(key=lambda x: len(x["ability"]), reverse=True)
    
    print("=" * 80)
    print("LONG ABILITY ANALYSIS")
    print("=" * 80)
    
    for i, item in enumerate(long_abilities[:10]):  # Show top 10
        print(f"\n{'=' * 80}")
        print(f"Ability {i+1}")
        print(f"{'=' * 80}")
        print(f"Card: {item['card_name']} ({item['card_id']})")
        print(f"Length: {len(item['ability'])} characters")
        print(f"\nOriginal ability:")
        print(item['ability'])
        print(f"\n{'-' * 80}")
        print("Analysis:")
        print(f"{'-' * 80}")
        
        analysis = analyze_ability(item['ability'])
        
        for j, sentence in enumerate(analysis['sentences']):
            print(f"\nSentence {j+1}:")
            print(f"  Original: {sentence['original']}")
            print(f"  Triggers: {sentence['triggers']}")
            print(f"  Game terms: {sentence['game_terms']}")
            print(f"  Particles: {sentence['particles']}")
            print(f"  Numbers: {sentence['numbers']}")
            print(f"  Groups: {sentence['groups']}")
            print(f"  Card names: {sentence['card_names']}")
        
        print(f"\n{'-' * 80}")
        print("Potential sentence patterns:")
        print(f"{'-' * 80}")
        
        # Suggest patterns based on analysis
        for sentence in analysis['sentences']:
            text = sentence['original']
            
            # Trigger + effect pattern
            if sentence['triggers']:
                print(f"  - Trigger pattern: {sentence['triggers'][0]} + [effect]")
            
            # Zone movement pattern
            if any(term in sentence['game_terms'] for term in ["手札", "ステージ", "控え室", "デッキ"]):
                if "から" in sentence['particles'] and "に" in sentence['particles']:
                    print(f"  - Zone movement pattern: [source]から[target]に[action]")
            
            # Conditional pattern
            if "場合" in text or "とき" in text:
                print(f"  - Conditional pattern: [condition]場合/とき、[effect]")
            
            # Cost-effect pattern
            if "：" in text:
                print(f"  - Cost-effect pattern: [cost]：[effect]")
            
            # Per-unit pattern
            if "につき" in text:
                print(f"  - Per-unit pattern: [source][number]枚につき、[effect]")
            
            # Selection pattern
            if "選ぶ" in text:
                print(f"  - Selection pattern: [options]から[number]つ選ぶ")
            
            # Optional pattern
            if "してもよい" in text:
                print(f"  - Optional pattern: [action]してもよい")

if __name__ == "__main__":
    main()
