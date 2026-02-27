import json
from collections import defaultdict, Counter

with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Extract QA references from each card
qa_counter = Counter()
qa_cards = defaultdict(list)

for card_id, card_data in cards.items():
    faq = card_data.get('faq', [])
    for faq_item in faq:
        title = faq_item.get('title', '')
        if title.startswith('Q'):
            # Extract Q number like Q79
            q_num = title.split('（')[0]
            qa_counter[q_num] += 1
            qa_cards[q_num].append(card_id)

# Sort by count (most to least)
sorted_qa = sorted(qa_counter.items(), key=lambda x: -x[1])

# Print to console
print('QA Usage Statistics (Most to Least Used):')
print('=' * 50)
for q_num, count in sorted_qa[:60]:
    print(f'{q_num}: {count} cards')

print()
print(f'Total unique QAs with card references: {len(sorted_qa)}')

# Write to file for later reference
with open('qa_usage.txt', 'w', encoding='utf-8') as f:
    f.write('QA Usage Statistics (Most to Least Used):\n')
    f.write('=' * 50 + '\n')
    for q_num, count in sorted_qa[:60]:
        f.write(f'{q_num}: {count} cards\n')
    f.write('\n')
    f.write(f'Total unique QAs with card references: {len(sorted_qa)}\n')
    # Also show cards for top QAs
    f.write('\n\nTop 10 QAs with card examples:\n')
    for q_num, count in sorted_qa[:10]:
        f.write(f'\n{q_num} ({count} cards):\n')
        for card in qa_cards[q_num][:5]:
            f.write(f'  - {card}\n')
