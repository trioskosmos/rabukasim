"""Generate a human-readable mapping from source text to parsed variables.

This report is intentionally practical: it shows the original Japanese text,
the parsed action or condition, and the concrete variables that were inferred.
It is meant to make parser behavior auditable without reading the full JSON.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path


INPUT_PATH = Path('data/abilities_extracted_from_cards.json')
OUTPUT_PATH = Path('data/opcode_variable_map_report.md')


def _flatten_nodes(value, path='root'):
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from _flatten_nodes(item, f'{path}.{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _flatten_nodes(item, f'{path}[{index}]')


def _interesting_fields(node):
    fields = []
    for key in sorted(node.keys()):
        if key in {'text', 'action', 'trigger', 'raw_text'}:
            continue
        value = node[key]
        if isinstance(value, (dict, list)):
            continue
        fields.append(f'{key}={value!r}')
    return ', '.join(fields) if fields else '(no extra variables)'


def _split_text(text):
    parts = []
    for sentence in text.replace('（', ' (').replace('）', ') ').split('。'):
        sentence = sentence.strip()
        if not sentence:
            continue
        parts.extend([part.strip() for part in sentence.split('、') if part.strip()])
    return parts


def _variable_evidence(node, text):
    evidence = []
    fields = {key: value for key, value in node.items() if key not in {'text', 'action', 'trigger', 'raw_text'} and not isinstance(value, (dict, list))}

    if 'count' in fields:
        count = fields['count']
        if isinstance(count, int):
            match = next((part for part in _split_text(text) if str(count) in part), None)
            evidence.append(f'count <- {match or count}')
        else:
            evidence.append(f'count <- {count}')

    if 'card_type' in fields:
        card_type = fields['card_type']
        lookup = {
            'member_card': 'メンバーカード',
            'live_card': 'ライブカード',
            'energy_card': 'エネルギーカード',
            'card': 'カード',
        }.get(card_type, card_type)
        evidence.append(f'card_type <- {lookup}')

    if 'source' in fields:
        source_lookup = {
            'deck_top': 'デッキの上',
            'deck_bottom': 'デッキの一番下',
            'hand': '手札',
            'waitroom': '控え室',
            'stage': 'ステージ',
            'energy_deck': 'エネルギーデッキ',
            'energy_zone': 'エネルギー置き場',
            'looked_at_cards': 'その中から',
            'opponent_selected_card': '選ばれたカード',
        }
        evidence.append(f"source <- {source_lookup.get(fields['source'], fields['source'])}")

    if 'target' in fields:
        target_lookup = {
            'self': '自分',
            'opponent': '相手',
            'selected_player': 'そのプレイヤー',
            'selected_member': 'そのメンバー',
        }
        evidence.append(f"target <- {target_lookup.get(fields['target'], fields['target'])}")

    if 'resource' in fields:
        resource_lookup = {'blade': 'ブレード', 'heart': 'ハート', 'energy': 'エネルギー'}
        evidence.append(f"resource <- {resource_lookup.get(fields['resource'], fields['resource'])}")

    if 'heart_types' in fields:
        evidence.append(f"heart_types <- {fields['heart_types']}")

    if 'selection' in node and isinstance(node['selection'], dict):
        selection = node['selection']
        if 'heart_types' in selection:
            evidence.append(f"selection.heart_types <- {selection['heart_types']}")
        if 'cost_min' in selection:
            evidence.append(f"selection.cost_min <- {selection['cost_min']}")

    if 'condition' in node and isinstance(node['condition'], dict):
        cond = node['condition']
        if cond.get('type'):
            evidence.append(f"condition.type <- {cond['type']}")
        if 'value' in cond:
            evidence.append(f"condition.value <- {cond['value']}")

    return evidence


def _variable_rows(node, text):
    rows = []
    parts = _split_text(text)

    def pick_part(*needles):
        for part in parts:
            if all(needle in part for needle in needles):
                return part
        for part in parts:
            if any(needle in part for needle in needles):
                return part
        return text

    scalar_fields = {key: value for key, value in node.items() if key not in {'text', 'action', 'trigger', 'raw_text', 'selection', 'condition'} and not isinstance(value, (dict, list))}
    for key, value in scalar_fields.items():
        if key == 'count':
            evidence = pick_part(str(value))
        elif key == 'card_type':
            evidence = pick_part('メンバーカード', 'ライブカード', 'カード')
        elif key == 'source':
            evidence = pick_part('デッキ', '手札', '控え室', 'エール', 'エネルギー', 'ステージ', '公開')
        elif key == 'target':
            evidence = pick_part('自分', '相手', 'その', '選んだ', '選択')
        elif key == 'resource':
            evidence = pick_part('ブレード', 'ハート', 'エネルギー')
        elif key == 'location':
            evidence = pick_part('控え室', 'ライブカード置き場', '成功ライブカード置き場', 'エールにより公開')
        elif key == 'destination':
            evidence = pick_part('デッキの上', '控え室', '手札', 'ステージ')
        elif key == 'order':
            evidence = pick_part('好きな順番', '任意の順番')
        elif key == 'may':
            evidence = pick_part('もよい', 'できる')
        elif key == 'reveal':
            evidence = pick_part('公開')
        else:
            evidence = text
        rows.append((key, value, evidence))

    if 'selection' in node and isinstance(node['selection'], dict):
        selection = node['selection']
        for key, value in selection.items():
            if isinstance(value, (dict, list)):
                continue
            if key == 'up_to':
                evidence = pick_part('好きな枚数', 'まで')
            elif key == 'order':
                evidence = pick_part('好きな順番', '順番')
            elif key == 'heart_types':
                evidence = pick_part('heart')
            elif key == 'cost_min':
                evidence = pick_part('コスト')
            else:
                evidence = text
            rows.append((f'selection.{key}', value, evidence))

    if 'condition' in node and isinstance(node['condition'], dict):
        cond = node['condition']
        for key, value in cond.items():
            if key in {'text', 'trigger', 'use_limit'} or isinstance(value, (dict, list)):
                continue
            evidence = cond.get('text', text)
            rows.append((f'condition.{key}', value, evidence))

    return rows


def _label(node):
    if 'action' in node and isinstance(node['action'], str):
        return node['action']
    if 'type' in node and isinstance(node['type'], str):
        return node['type']
    return '(unlabelled)'


def _collect_examples(data):
    by_label = defaultdict(list)
    issues = []
    for idx, ability in enumerate(data['unique_abilities']):
        full_text = ability.get('full_text', '')
        effect = ability.get('effect')
        if not effect:
            continue
        for path, node in _flatten_nodes(effect):
            if not isinstance(node, dict):
                continue
            label = _label(node)
            text = node.get('text')
            if not text and 'raw_text' in node:
                text = node['raw_text']
            if text:
                by_label[label].append((idx, path, text, _interesting_fields(node), dict(node)))
            if label in {'draw_cards', 'add_to_hand', 'place_card', 'member_to_wait', 'deploy_to_stage', 'look_at_cards', 'gain_resource'}:
                missing = []
                for field in {
                    'draw_cards': ['count'],
                    'add_to_hand': ['count', 'card_type'],
                    'place_card': ['card_type'],
                    'member_to_wait': ['source', 'target'],
                    'deploy_to_stage': ['target'],
                    'look_at_cards': ['count', 'source'],
                    'gain_resource': ['resource'],
                }.get(label, []):
                    if field not in node:
                        missing.append(field)
                if missing:
                    issues.append((idx, path, label, missing, text or full_text[:120]))
    return by_label, issues


def main():
    with INPUT_PATH.open('r', encoding='utf-8') as handle:
        data = json.load(handle)

    by_label, issues = _collect_examples(data)

    lines = []
    lines.append('# Opcode Variable Map')
    lines.append('')
    lines.append(f'- Unique abilities: {len(data["unique_abilities"])}')
    lines.append(f'- Labels observed: {len(by_label)}')
    lines.append(f'- Potential variable issues: {len(issues)}')
    lines.append('')

    if issues:
        lines.append('## Potential Issues')
        for idx, path, label, missing, text in issues[:50]:
            lines.append(f'- #{idx} `{label}` missing {", ".join(missing)} at `{path}`')
            lines.append(f'  - Text: {text}')
        lines.append('')

    lines.append('## Common Mappings')
    for label, items in sorted(by_label.items(), key=lambda item: (-len(item[1]), item[0])):
        lines.append(f'### {label}')
        lines.append(f'- Examples: {len(items)}')
        for idx, path, text, vars_text, node in items[:5]:
            lines.append(f'- `#{idx}` `{path}`')
            lines.append(f'  - Text: {text}')
            split_parts = _split_text(text)
            if split_parts:
                lines.append('  - Segments:')
                for part in split_parts[:6]:
                    lines.append(f'    - {part}')
            rows = _variable_rows(node, text)
            if rows:
                lines.append('  - Variable split:')
                for key, value, evidence in rows:
                    lines.append(f'    - {key} = {value!r}')
                    lines.append(f'      - From: {evidence}')
            evidence = _variable_evidence(node, text)
            if evidence:
                lines.append('  - Evidence:')
                for item in evidence:
                    lines.append(f'    - {item}')
            lines.append(f'  - Vars: {vars_text}')
        lines.append('')

    OUTPUT_PATH.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {OUTPUT_PATH}')
    print(f'Potential issues: {len(issues)}')


if __name__ == '__main__':
    main()
