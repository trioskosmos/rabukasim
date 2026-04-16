#!/usr/bin/env python3
"""
Show all three pattern types with 1P_2C at the top.
"""
import json

# Read the abilities file
with open('data/abilities_extracted_from_cards.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Categorize by pattern
zero_p_two_c = []
one_p_two_c = []
one_p_one_c = []
one_p_zero_c = []
two_p_zero_c = []
three_p_zero_c = []
four_p_zero_c = []
five_p_zero_c = []
six_plus_p_zero_c = []

for i, ability in enumerate(data['unique_abilities'], 1):
    costless_text = ability['costless_text']
    period_count = costless_text.count('。')
    comma_count = costless_text.count('、')
    
    # 0 comma patterns with various periods
    if comma_count == 0:
        if period_count == 0:
            zero_p_two_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count == 1:
            one_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count == 2:
            two_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count == 3:
            three_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count == 4:
            four_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count == 5:
            five_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif period_count >= 6:
            six_plus_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
    # 1 comma patterns
    elif comma_count == 1 and period_count == 1:
        one_p_one_c.append({
            'index': i,
            'card_count': ability['card_count'],
            'triggers': ability['triggers'],
            'costless_text': costless_text,
            'effect': ability['effect']
        })
    # 2 comma patterns
    elif comma_count == 2 and period_count == 1:
        one_p_two_c.append({
            'index': i,
            'card_count': ability['card_count'],
            'triggers': ability['triggers'],
            'costless_text': costless_text,
            'effect': ability['effect']
        })

# Write combined report
with open('data/all_patterns_report.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ALL PATTERNS REPORT\n")
    f.write("=" * 80 + "\n\n")
    
    # 0 comma patterns
    f.write("0P_0C (Zero period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(zero_p_two_c)}\n\n")
    
    raw_count_0p0c = 0
    for item in zero_p_two_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_0p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_0p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_0C (One period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_zero_c)}\n\n")
    
    raw_count_1p0c = 0
    for item in one_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_1p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_1p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_0C (Two period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_zero_c)}\n\n")
    
    raw_count_2p0c = 0
    for item in two_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("3P_0C (Three period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(three_p_zero_c)}\n\n")
    
    raw_count_3p0c = 0
    for item in three_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_3p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_3p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("4P_0C (Four period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(four_p_zero_c)}\n\n")
    
    raw_count_4p0c = 0
    for item in four_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_4p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_4p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("5P_0C (Five period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(five_p_zero_c)}\n\n")
    
    raw_count_5p0c = 0
    for item in five_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_5p0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_5p0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("6+P_0C (Six+ period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(six_plus_p_zero_c)}\n\n")
    
    raw_count_6plus = 0
    for item in six_plus_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_6plus += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_6plus}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_2C (One period, two comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_two_c)}\n\n")
    
    raw_count_2c = 0
    for item in one_p_two_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_1C (One period, one comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_one_c)}\n\n")
    
    raw_count_1c = 0
    for item in one_p_one_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_1c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_1c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_0C (One period, zero comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_zero_c)}\n\n")
    
    raw_count_0c = 0
    for item in one_p_zero_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_0c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_0c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("SUMMARY\n")
    f.write("=" * 80 + "\n")
    f.write(f"0P_0C: {len(zero_p_two_c)} total, {raw_count_0p0c} raw_text\n")
    f.write(f"1P_0C: {len(one_p_zero_c)} total, {raw_count_1p0c} raw_text\n")
    f.write(f"2P_0C: {len(two_p_zero_c)} total, {raw_count_2p0c} raw_text\n")
    f.write(f"3P_0C: {len(three_p_zero_c)} total, {raw_count_3p0c} raw_text\n")
    f.write(f"4P_0C: {len(four_p_zero_c)} total, {raw_count_4p0c} raw_text\n")
    f.write(f"5P_0C: {len(five_p_zero_c)} total, {raw_count_5p0c} raw_text\n")
    f.write(f"6+P_0C: {len(six_plus_p_zero_c)} total, {raw_count_6plus} raw_text\n")
    f.write(f"1P_2C: {len(one_p_two_c)} total, {raw_count_2c} raw_text\n")
    f.write(f"1P_1C: {len(one_p_one_c)} total, {raw_count_1c} raw_text\n")
    f.write(f"Total: {len(zero_p_two_c) + len(one_p_zero_c) + len(two_p_zero_c) + len(three_p_zero_c) + len(four_p_zero_c) + len(five_p_zero_c) + len(six_plus_p_zero_c) + len(one_p_two_c) + len(one_p_one_c)}, {raw_count_0p0c + raw_count_1p0c + raw_count_2p0c + raw_count_3p0c + raw_count_4p0c + raw_count_5p0c + raw_count_6plus + raw_count_2c + raw_count_1c} raw_text\n")

print(f"Report complete. See data/all_patterns_report.txt")
print(f"0P_0C: {len(zero_p_two_c)}, 1P_0C: {len(one_p_zero_c)}, 2P_0C: {len(two_p_zero_c)}, 3P_0C: {len(three_p_zero_c)}, 4P_0C: {len(four_p_zero_c)}, 5P_0C: {len(five_p_zero_c)}, 6+P_0C: {len(six_plus_p_zero_c)}, 1P_2C: {len(one_p_two_c)}, 1P_1C: {len(one_p_one_c)}")
