import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
input_path = root / 'data' / 'ability_frame_source.json'
output_json_path = root / 'data' / 'frame_jp_mismatches.json'
output_md_path = root / 'data' / 'frame_jp_mismatch_report.md'

# mapping of opcode -> list of Japanese keywords expected in jp text
opcode_jp_map = {
    'DRAW': ['引く','カードを引く','カードを1枚引く','カードを2枚引く','手札が'],
    'MOVE_TO_DISCARD': ['控え室','控え室に置','手札を1枚控え室に置','残りを控え室に置く'],
    'MOVE_MEMBER': ['移動','登場させる','登場','ポジションチェンジ','ウェイトにする','ウェイト'],
    'PLAY_MEMBER_FROM_HAND': ['登場させる','登場','ステージに登場','ステージに登場させる'],
    'ADD_BLADES': ['ブレード','ブレードハート','ブレードを得'],
    'ADD_HEARTS': ['ハート','ハートを得','ブレードハートを失い'],
    'ENERGY_CHARGE': ['エネルギー','ウェイト状態','ウェイト','エネルギーデッキ','エネルギーカードを'],
    'ACTIVATE_ENERGY': ['エネルギーを','エネルギーを2枚アクティブ','エネルギーを1枚アクティブ'],
    'RECOVER_LIVE': ['手札に加え','手札に加える','控え室からライブカードを1枚手札に加える','手札に加える。'],
    'RECOVER_MEMBER': ['手札に加える','控え室から','控え室からコスト2以下のメンバーカードを1枚手札に加える'],
    'LOOK_AND_CHOOSE': ['見る','公開して','公開し','公開して手札に加え','見る。その中から','見る。その中から好きな'],
    'LOOK_DECK': ['見る','デッキの上からカードを','デッキの上からカードを3枚見る','デッキの上からカードを5枚見る'],
    'LOOK_REORDER_DISCARD': ['見る','順番でデッキの上に置','並べる','再配置'],
    'PLAY_MEMBER_FROM_DISCARD': ['ステージに登場','控え室から','控え室からメンバーを登場させる','プレイ'],
    'SELECT_CARDS': ['選ぶ','選択','選ぶ。','公開して手札に加えて'],
    'SET_TAPPED': ['ウェイト','ウェイトにする','ウェイト状態'],
    'TAP_OPPONENT': ['ウェイトにする','ウェイト','相手のステージにいる'],
    'DRAW_UNTIL': ['手札が','手札が5枚になるまで','手札が5枚になるまで'],
    'ADD_TO_HAND': ['手札に加える','手札に加え'],
    'DISCARDED_CARDS': ['控え室に置く','控え室','控え室に'],
    'MOVE_TO_DECK': ['デッキの一番下','デッキの一番上','デッキの上に置く'],
    'SELECT_MEMBER': ['選ぶ','選択する','選ぶ：','相手のステージにいる','自分のステージにいる'],
    'SET_SCORE': ['スコア','スコアの合計'],
    'SCORE_TOTAL_CHECK': ['スコアの合計','スコアの合計が'],
    'BATON': ['バトンタッチ','バトンタッチして','バトンタッチして登場'],
    'SUM_VALUE': ['合計','合計が'],
}


def contains_any(text, keywords):
    if not text:
        return False
    for k in keywords:
        if k in text:
            return True
    return False


def main():
    data = json.loads(input_path.read_text(encoding='utf-8'))
    abilities = data.get('abilities', [])
    issues = []

    for idx, ab in enumerate(abilities):
        ops = {f['op'] for f in ab.get('frames', [])}
        jp_texts = []
        if ab.get('primary_text_jp'):
            jp_texts.append(ab.get('primary_text_jp'))
        for s in ab.get('source_ability_texts', []):
            if s.get('jp'):
                jp_texts.append(s.get('jp'))
        combined_jp = '\n'.join(jp_texts)

        for op in sorted(ops):
            if op in opcode_jp_map:
                keywords = opcode_jp_map[op]
                if not contains_any(combined_jp, keywords):
                    issues.append({
                        'ability_index': idx,
                        'signature': ab.get('signature'),
                        'op': op,
                        'expected_keywords': keywords,
                        'primary_text_jp': ab.get('primary_text_jp',''),
                        'source_texts_jp': [s.get('jp','') for s in ab.get('source_ability_texts',[])][:3],
                        'cards_sample': ab.get('cards',[])[:3]
                    })

    output_path.write_text(json.dumps({'generated_at': __import__('datetime').datetime.utcnow().isoformat(), 'issues': issues}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Checked {len(abilities)} abilities, found {len(issues)} potential mismatches. Report: {output_path}")

if __name__ == '__main__':
    main()
