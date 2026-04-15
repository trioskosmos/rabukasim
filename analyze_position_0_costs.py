import json

# Load the coverage log which has template data
with open('data/ability_coverage_log.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract cost patterns from templates (everything before colon)
cost_patterns = {}

for template_data in data.get('templates', []):
    template = template_data.get('template', '')
    if '：' in template:
        # Split by colon and take the first part (cost)
        parts = template.split('：', 1)
        cost = parts[0].strip()
        if cost:
            cost_patterns[cost] = cost_patterns.get(cost, 0) + template_data.get('usage_count', 1)

# Sort by frequency
sorted_costs = sorted(cost_patterns.items(), key=lambda x: -x[1])

print(f"Total unique cost patterns: {len(cost_patterns)}")
print(f"\nTop 20 most common cost patterns:")
for i, (cost, count) in enumerate(sorted_costs[:20], 1):
    print(f"{i}. '{cost}' (appears in {count} templates)")

print(f"\nAll unique cost patterns:")
for i, (cost, count) in enumerate(sorted_costs, 1):
    print(f"{i}. '{cost}' (appears in {count} templates)")
