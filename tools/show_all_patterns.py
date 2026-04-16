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
bullet_point = []
one_p_three_c = []
one_p_four_c = []
one_p_five_c = []
one_p_six_plus_c = []
two_p_one_c = []
two_p_two_c = []
two_p_three_c = []
two_p_four_c = []
two_p_five_c = []
two_p_six_plus_c = []

for i, ability in enumerate(data['unique_abilities'], 1):
    costless_text = ability['costless_text']
    period_count = costless_text.count('。')
    comma_count = costless_text.count('、')
    
    # Check for bullet point patterns first (must have both bullet points and choice marker)
    if '・' in costless_text and '以下から1つを選ぶ' in costless_text:
        bullet_point.append({
            'index': i,
            'card_count': ability['card_count'],
            'triggers': ability['triggers'],
            'costless_text': costless_text,
            'effect': ability['effect']
        })
        continue  # Skip other categorization if it has bullet points
    
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
    # 1 period patterns with various comma counts
    elif period_count == 1:
        if comma_count == 0:
            one_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 1:
            one_p_one_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 2:
            one_p_two_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 3:
            one_p_three_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 4:
            one_p_four_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 5:
            one_p_five_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count >= 6:
            one_p_six_plus_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
    # 2 period patterns with various comma counts
    elif period_count == 2:
        if comma_count == 0:
            two_p_zero_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 1:
            two_p_one_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 2:
            two_p_two_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 3:
            two_p_three_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 4:
            two_p_four_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count == 5:
            two_p_five_c.append({
                'index': i,
                'card_count': ability['card_count'],
                'triggers': ability['triggers'],
                'costless_text': costless_text,
                'effect': ability['effect']
            })
        elif comma_count >= 6:
            two_p_six_plus_c.append({
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
    
    # Bullet point patterns
    f.write("BULLET POINT (・) PATTERNS\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(bullet_point)}\n\n")
    
    raw_count_bullet = 0
    for item in bullet_point:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_bullet += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_bullet}\n\n")
    
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
    f.write("1P_3C (One period, three comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_three_c)}\n\n")
    
    raw_count_3c = 0
    for item in one_p_three_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_3c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_3c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_4C (One period, four comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_four_c)}\n\n")
    
    raw_count_4c = 0
    for item in one_p_four_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_4c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_4c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_5C (One period, five comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_five_c)}\n\n")
    
    raw_count_5c = 0
    for item in one_p_five_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_5c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_5c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("1P_6+C (One period, six+ comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(one_p_six_plus_c)}\n\n")
    
    raw_count_6plus_c = 0
    for item in one_p_six_plus_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_6plus_c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_6plus_c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_1C (Two period, one comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_one_c)}\n\n")
    
    raw_count_2p1c = 0
    for item in two_p_one_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p1c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p1c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_2C (Two period, two comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_two_c)}\n\n")
    
    raw_count_2p2c = 0
    for item in two_p_two_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p2c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p2c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_3C (Two period, three comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_three_c)}\n\n")
    
    raw_count_2p3c = 0
    for item in two_p_three_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p3c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p3c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_4C (Two period, four comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_four_c)}\n\n")
    
    raw_count_2p4c = 0
    for item in two_p_four_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p4c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p4c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_5C (Two period, five comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_five_c)}\n\n")
    
    raw_count_2p5c = 0
    for item in two_p_five_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p5c += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p5c}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("2P_6+C (Two period, six+ comma)\n")
    f.write("=" * 80 + "\n")
    f.write(f"Total: {len(two_p_six_plus_c)}\n\n")
    
    raw_count_2p6plusc = 0
    for item in two_p_six_plus_c:
        f.write(f"[{item['index']}] Card count: {item['card_count']}\n")
        f.write(f"    Triggers: {item['triggers']}\n")
        f.write(f"    Costless text: {item['costless_text']}\n")
        f.write(f"    Effect: {json.dumps(item['effect'], indent=2, ensure_ascii=False)}\n")
        
        # Check for raw_text
        effect_str = json.dumps(item['effect'], ensure_ascii=False)
        if 'raw_text' in effect_str:
            f.write(f"    RAW TEXT FOUND\n")
            raw_count_2p6plusc += 1
        
        f.write("\n")
    
    f.write(f"Raw text count: {raw_count_2p6plusc}\n\n")
    
    f.write("=" * 80 + "\n")
    f.write("SUMMARY\n")
    f.write("=" * 80 + "\n")
    f.write(f"BULLET POINT: {len(bullet_point)} total, {raw_count_bullet} raw_text\n")
    f.write(f"0P_0C: {len(zero_p_two_c)} total, {raw_count_0p0c} raw_text\n")
    f.write(f"1P_0C: {len(one_p_zero_c)} total, {raw_count_1p0c} raw_text\n")
    f.write(f"2P_0C: {len(two_p_zero_c)} total, {raw_count_2p0c} raw_text\n")
    f.write(f"3P_0C: {len(three_p_zero_c)} total, {raw_count_3p0c} raw_text\n")
    f.write(f"4P_0C: {len(four_p_zero_c)} total, {raw_count_4p0c} raw_text\n")
    f.write(f"5P_0C: {len(five_p_zero_c)} total, {raw_count_5p0c} raw_text\n")
    f.write(f"6+P_0C: {len(six_plus_p_zero_c)} total, {raw_count_6plus} raw_text\n")
    f.write(f"1P_1C: {len(one_p_one_c)} total, {raw_count_1c} raw_text\n")
    f.write(f"1P_2C: {len(one_p_two_c)} total, {raw_count_2c} raw_text\n")
    f.write(f"1P_3C: {len(one_p_three_c)} total, {raw_count_3c} raw_text\n")
    f.write(f"1P_4C: {len(one_p_four_c)} total, {raw_count_4c} raw_text\n")
    f.write(f"1P_5C: {len(one_p_five_c)} total, {raw_count_5c} raw_text\n")
    f.write(f"1P_6+C: {len(one_p_six_plus_c)} total, {raw_count_6plus_c} raw_text\n")
    f.write(f"2P_1C: {len(two_p_one_c)} total, {raw_count_2p1c} raw_text\n")
    f.write(f"2P_2C: {len(two_p_two_c)} total, {raw_count_2p2c} raw_text\n")
    f.write(f"2P_3C: {len(two_p_three_c)} total, {raw_count_2p3c} raw_text\n")
    f.write(f"2P_4C: {len(two_p_four_c)} total, {raw_count_2p4c} raw_text\n")
    f.write(f"2P_5C: {len(two_p_five_c)} total, {raw_count_2p5c} raw_text\n")
    f.write(f"2P_6+C: {len(two_p_six_plus_c)} total, {raw_count_2p6plusc} raw_text\n")
    f.write(f"Total: {len(bullet_point) + len(zero_p_two_c) + len(one_p_zero_c) + len(two_p_zero_c) + len(three_p_zero_c) + len(four_p_zero_c) + len(five_p_zero_c) + len(six_plus_p_zero_c) + len(one_p_one_c) + len(one_p_two_c) + len(one_p_three_c) + len(one_p_four_c) + len(one_p_five_c) + len(one_p_six_plus_c) + len(two_p_one_c) + len(two_p_two_c) + len(two_p_three_c) + len(two_p_four_c) + len(two_p_five_c) + len(two_p_six_plus_c)}, {raw_count_bullet + raw_count_0p0c + raw_count_1p0c + raw_count_2p0c + raw_count_3p0c + raw_count_4p0c + raw_count_5p0c + raw_count_6plus + raw_count_1c + raw_count_2c + raw_count_3c + raw_count_4c + raw_count_5c + raw_count_6plus_c + raw_count_2p1c + raw_count_2p2c + raw_count_2p3c + raw_count_2p4c + raw_count_2p5c + raw_count_2p6plusc} raw_text\n")

print(f"Report complete. See data/all_patterns_report.txt")
print(f"BULLET POINT: {len(bullet_point)}, 0P_0C: {len(zero_p_two_c)}, 1P_0C: {len(one_p_zero_c)}, 2P_0C: {len(two_p_zero_c)}, 3P_0C: {len(three_p_zero_c)}, 4P_0C: {len(four_p_zero_c)}, 5P_0C: {len(five_p_zero_c)}, 6+P_0C: {len(six_plus_p_zero_c)}, 1P_1C: {len(one_p_one_c)}, 1P_2C: {len(one_p_two_c)}, 1P_3C: {len(one_p_three_c)}, 1P_4C: {len(one_p_four_c)}, 1P_5C: {len(one_p_five_c)}, 1P_6+C: {len(one_p_six_plus_c)}, 2P_1C: {len(two_p_one_c)}, 2P_2C: {len(two_p_two_c)}, 2P_3C: {len(two_p_three_c)}, 2P_4C: {len(two_p_four_c)}, 2P_5C: {len(two_p_five_c)}, 2P_6+C: {len(two_p_six_plus_c)}")
