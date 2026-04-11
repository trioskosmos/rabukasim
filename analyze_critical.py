#!/usr/bin/env python3
import json
import sys
import traceback

def main():
    try:
        with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find abilities by card number
        target_cards = ['PL!S-bp2-001-P', 'PL!S-pb1-009-P+']
        
        with open('manual_analysis.txt', 'w', encoding='utf-8') as out:
            for idx, ability in enumerate(data['abilities']):
                for ref in ability.get('card_refs', []):
                    if ref.get('card_no') in target_cards:
                        out.write(f"\n{'='*70}\n")
                        out.write(f"ABILITY #{idx} - {ref.get('card_no')}\n")
                        out.write(f"Name: {ref.get('name', 'N/A')}\n")
                        out.write(f"{'='*70}\n")
                        out.write(f"\nJapanese Text:\n")
                        out.write(ability.get('primary_text_jp', 'N/A') + '\n')
                        out.write(f"\nTrigger: {ability.get('trigger', 'N/A')}\n")
                        out.write(f"\nFrames ({len(ability.get('frames', []))} total):\n")
                        for i, frame in enumerate(ability.get('frames', [])):
                            out.write(f"\n  [{i}] {frame.get('op', 'UNKNOWN')}\n")
                            if 'value' in frame:
                                out.write(f"      value: {frame['value']}\n")
                            if 'attr' in frame:
                                out.write(f"      attr: {frame['attr']}\n")
                            if 'slot' in frame:
                                out.write(f"      slot: {frame['slot']}\n")
                        out.write('\n')
            
            out.write("\n\n" + "="*70 + "\n")
            out.write("MANUAL ANALYSIS:\n")
            out.write("="*70 + "\n\n")
            
            # Now analyze each
            for idx, ability in enumerate(data['abilities']):
                for ref in ability.get('card_refs', []):
                    card_no = ref.get('card_no', '')
                    if card_no == 'PL!S-bp2-001-P':
                        analyze_plsb2001(idx, ability, out)
                    elif card_no == 'PL!S-pb1-009-P+':
                        analyze_plspb1009(idx, ability, out)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_plsb2001(idx, ability, out):
    text = ability.get('primary_text_jp', '')
    frames = ability.get('frames', [])
    
    out.write(f"\n## ABILITY #{idx}: PL!S-bp2-001-P (Mia Taylor)\n\n")
    out.write("**Japanese Text:**\n")
    out.write(text + "\n\n")
    out.write("**Translation:**\n")
    out.write("\"{{jyouji.png|Always}} When your successful live card pile has 0 cards,")
    out.write(" and the opponent's successful live card pile has 1 or more cards,")
    out.write(" gain 3 blades ({{icon_blade.png|Blade}}x3).\"\n\n")
    
    out.write("**Frame Analysis:**\n")
    frame_ops = [f.get('op', 'UNKNOWN') for f in frames]
    out.write(f"Current frames: {frame_ops}\n\n")
    
    out.write("**Does this match the text?**\n")
    out.write("- Text says: Count success pile (0 for self, >=1 for opponent) -> gain 3 blades\n")
    out.write("- Frames show: BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE\n")
    out.write("- Issue: BATON and COUNT_ENERGY/ENERGY_CHARGE are for ENERGY, not BLADES\n")
    out.write("- Should use: COUNT_SUCCESS to check both players' success piles\n")
    out.write("- Then: ADD_BLADES with value=3\n\n")
    
    out.write("**VERDICT: FRAMES ARE WRONG**\n")
    out.write("The frames are checking ENERGY instead of SUCCESS PILE COUNT,\n")
    out.write("and using ENERGY_CHARGE instead of ADD_BLADES.\n\n")

def analyze_plspb1009(idx, ability, out):
    text = ability.get('primary_text_jp', '')
    frames = ability.get('frames', [])
    
    out.write(f"\n## ABILITY #{idx}: PL!S-pb1-009-P+ (Mia Taylor - Promo)\n\n")
    out.write("**Japanese Text:**\n")
    out.write(text + "\n\n")
    out.write("**Translation:**\n")
    out.write("\"{{jyouji.png|Always}} When your and opponent's successful live card piles")
    out.write(" have a total of 3 or more cards combined, gain 3 blades")
    out.write(" ({{icon_blade.png|Blade}}x3).\"\n\n")
    
    out.write("**Frame Analysis:**\n")
    frame_ops = [f.get('op', 'UNKNOWN') for f in frames]
    out.write(f"Current frames: {frame_ops}\n\n")
    
    out.write("**Does this match the text?**\n")
    out.write("- Text says: Total success cards (self + opponent) >= 3 -> gain 3 blades\n")
    out.write("- Frames show: BATON, JUMP_IF_FALSE, COUNT_ENERGY, JUMP_IF_FALSE, ENERGY_CHARGE\n")
    out.write("- Issue: BATON and COUNT_ENERGY are for ENERGY, not SUCCESS PILES\n")
    out.write("- Should use: COUNT_SUCCESS with target_player=BOTH and value=3\n")
    out.write("- Then: ADD_BLADES with value=3\n\n")
    
    out.write("**VERDICT: FRAMES ARE WRONG**\n")
    out.write("Same issue as #454 - checking energy instead of success pile count.\n\n")

if __name__ == '__main__':
    main()
