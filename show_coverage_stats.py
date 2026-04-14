import json

data = json.load(open('data/abilities_extracted_simple.json', 'r', encoding='utf-8'))

# Calculate coverage stats
coverages = [a['coverage'] for a in data['abilities']]
avg_coverage = sum(coverages) / len(coverages)
below_50 = sum(1 for c in coverages if c < 0.5)
below_60 = sum(1 for c in coverages if c < 0.6)
below_70 = sum(1 for c in coverages if c < 0.7)
below_80 = sum(1 for c in coverages if c < 0.8)
below_90 = sum(1 for c in coverages if c < 0.9)

print(f"Total abilities: {len(coverages)}")
print(f"Average coverage: {avg_coverage:.1%}")
print(f"Below 50%: {below_50} ({below_50/len(coverages):.1%})")
print(f"Below 60%: {below_60} ({below_60/len(coverages):.1%})")
print(f"Below 70%: {below_70} ({below_70/len(coverages):.1%})")
print(f"Below 80%: {below_80} ({below_80/len(coverages):.1%})")
print(f"Below 90%: {below_90} ({below_90/len(coverages):.1%})")
