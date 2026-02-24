# Oracle改善計画

## 現在のパス率と失敗原因分析

### パス率: 87.1%（710/815能力）

**失敗: 105能力**

### 失敗原因カテゴリ

| カテゴリ | 件数 | 割合 | 原因詳細 |
|:---|:---:|:---:|:---|
| 条件未充足 | ~50 | 48% | Oracleが生成した合成環境が条件を満たしていない |
| スコアデルタゼロ | ~30 | 29% | Liveフェーズ未設定、Constant能力の条件不一致 |
| 無限ループ検出 | ~6 | 6% | インタープリータが1000ステップで停止 |
| オプショナル未解決 | ~10 | 10% | 自動選択が正しく処理されない |
| その他 | ~9 | 7% | Oracleパースミス、未知のバグ |

### 失敗例

#### 1. 条件未充足（最も多い）
```
カードテキスト: "エネルギーが7枚以上ある場合、カードを1枚引く"
Oracle期待値: HAND_DELTA = 1
実際の結果: HAND_DELTA = 0（条件を満たしていないため発動しない）

原因: setup_oracle_environment()がエネルギーを7枚用意していない
```

#### 2. スコアデルタゼロ
```
カードテキスト: "ライブ成功時、スコア+3"
Oracle期待値: SCORE_DELTA = 3
実際の結果: SCORE_DELTA = 0

原因: ライブ成功時トリガーだが、Liveフェーズ/LiveResultフェーズが設定されていない
```

#### 3. 無限ループ検出
```
カード: O_LOOK_AND_CHOOSE系の複雑な能力
実際の結果: 1000ステップで停止

原因: インタラクション解決ループ、または条件分岐の無限ループ
```

#### 4. Oracleパースミス
```
カードテキスト: "エネルギーが7枚以上ある場合、カードを1枚引く"
Oracle期待値: HAND_DELTA = 7（誤り）
正解: HAND_DELTA = 1

原因: 正規表現が条件値（7）を効果値として抽出
```

---

## アーキテクチャ変更

### 現在のフロー（問題あり）
```
日本語テキスト → Oracle (正規表現) → semantic_truth_v3.json → Assertions
```
- 正規表現で日本語を解析
- 条件値と効果値の混同
- パス率87.1%

### あるべきフロー
```
擬似コード (manual_pseudocode.json) → Oracle → semantic_truth_v3.json → Assertions
```
- 構造化された擬似コードから期待値生成
- 正確な効果量の抽出
- パス率95%+目標

---

## 擬似コードフォーマット

`data/manual_pseudocode.json`の例：
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: TAP_OPPONENT(2) {FILTER="COST_LE=4"}

TRIGGER: ON_LIVE_START
EFFECT: SELECT_MODE(1)
  OPTION: DRAW | EFFECT: DRAW(1); DISCARD_HAND(1)
  OPTION: WAIT | EFFECT: TAP_OPPONENT(99) {FILTER="COST_LE_2"}
```

---

## 改善案

### アプローチA: 擬似コードパーサー（推奨）

**変更内容:**
擬似コードから期待値を生成するパーサーを実装

```python
class PseudocodeOracle:
    """擬似コードから期待値を生成"""
    
    EFFECT_PATTERNS = {
        "DRAW": r"DRAW\((\d+)\)",
        "DISCARD_HAND": r"DISCARD_HAND\((\d+)\)",
        "TAP_OPPONENT": r"TAP_OPPONENT\((\d+)\)",
        "ADD_BLADES": r"ADD_BLADES\((\d+)\)",
        "BOOST_SCORE": r"BOOST_SCORE\((\d+)\)",
        "RECOVER_MEMBER": r"RECOVER_MEMBER\((\d+)\)",
        "RECOVER_LIVE": r"RECOVER_LIVE\((\d+)\)",
        "ACTIVATE_ENERGY": r"ACTIVATE_ENERGY\((\d+)\)",
    }
    
    def parse_pseudocode(self, pseudocode: str) -> List[SemanticAbility]:
        abilities = []
        
        # TRIGGERで分割
        trigger_blocks = re.split(r'TRIGGER:\s*', pseudocode)
        
        for block in trigger_blocks:
            if not block.strip():
                continue
                
            # トリガータイプ抽出
            trigger_match = re.match(r'(\w+)', block)
            trigger_type = trigger_match.group(1) if trigger_match else "NONE"
            
            # 効果抽出
            effects = self.extract_effects(block)
            
            abilities.append({
                "trigger": trigger_type,
                "sequence": effects
            })
        
        return abilities
    
    def extract_effects(self, block: str) -> List[dict]:
        effects = []
        
        for effect_name, pattern in self.EFFECT_PATTERNS.items():
            matches = re.finditer(pattern, block)
            for match in matches:
                value = int(match.group(1))
                effects.append(self.map_effect_to_delta(effect_name, value))
        
        return effects
    
    def map_effect_to_delta(self, effect_name: str, value: int) -> dict:
        mapping = {
            "DRAW": {"tag": "HAND_DELTA", "value": value},
            "DISCARD_HAND": {"tag": "HAND_DISCARD", "value": value},
            "TAP_OPPONENT": {"tag": "MEMBER_TAP_DELTA", "value": value},
            "ADD_BLADES": {"tag": "BLADE_DELTA", "value": value},
            "BOOST_SCORE": {"tag": "SCORE_DELTA", "value": value},
            "RECOVER_MEMBER": {"tag": "HAND_DELTA", "value": value},
            "RECOVER_LIVE": {"tag": "LIVE_RECOVER", "value": value},
            "ACTIVATE_ENERGY": {"tag": "ENERGY_ACTIVATE", "value": value},
        }
        return mapping.get(effect_name, {"tag": effect_name, "value": value})
```

**効果:**
- 構造化データから正確な期待値生成
- 条件値と効果値の混同を回避
- パス率95%+見込み

### アプローチB: ルールベース強化（現在）

**変更内容:**
1. 条件検出パターンの追加
2. 条件値と効果値の区別
3. セグメント分割の改善

```python
# 改善例
CONDITION_PATTERNS = {
    "IF_ENERGY_GE": r'エネルギーが([0-9]+)枚以上ある場合',
    "IF_LIVE_SUCCESS": r'ライブに成功した場合',
    "IF_OPPONENT_HAS": r'相手の.*?がある場合',
}

def map_expectations(self, segment_text):
    # まず条件を検出
    conditions = self.extract_conditions(segment_text)
    
    # 条件がある場合、期待値に条件フラグを追加
    if conditions:
        return {
            "conditions": conditions,
            "effects": self.extract_effects(segment_text),
            "conditional": True
        }
    
    return self.extract_effects(segment_text)
```

**効果:**
- 条件付き能力の誤検出削減
- パス率5-10%向上見込み

### アプローチB: コンパイラ連携

**変更内容:**
Oracleではなく、コンパイラが生成したバイトコードから期待値を逆算

```python
# コンパイラの能力定義を使用
def interpret_from_bytecode(ability):
    expectations = []
    for opcode in ability.bytecode:
        if opcode == O_DRAW:
            expectations.append({"tag": "HAND_DELTA", "value": opcode.v})
        elif opcode == O_ADD_HEARTS:
            expectations.append({"tag": "HEART_DELTA", "value": opcode.v})
    return expectations
```

**効果:**
- 100%正確な期待値（コンパイラと同一ロジック）
- テキスト解析の複雑さを回避

**欠点:**
- コンパイラのバグも正解として扱う
- テキストとバイトコードの不一致を検出できない

### アプローチC: LLM活用

**変更内容:**
GPT-4等のLLMで日本語テキストを解析

```python
def map_expectations_llm(self, segment_text):
    prompt = f"""
    以下のカードテキストから期待される効果を抽出してください。
    出力形式: JSON
    
    テキスト: {segment_text}
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content)
```

**効果:**
- 複雑な構文も正確に解析
- 条件、選択肢、ネストに対応

**欠点:**
- APIコスト
- 実行速度
- 確実性の問題

---

## 推奨アプローチ

### 段階的改善

1. **フェーズ1: ルールベース強化**（即時）
   - 条件検出パターン追加
   - 条件値と効果値の区別
   - パス率87%→92%目標

2. **フェーズ2: コンパイラ連携**（中期）
   - バイトコードからの期待値生成
   - テキスト解析とのクロスチェック
   - パス率95%目標

3. **フェーズ3: ハイブリッド**（長期）
   - ルールベース + LLM
   - 疑わしいケースのみLLM確認
   - パス率98%目標

---

## 具体的な改善項目

### 優先度1: 条件検出

```python
# 追加するパターン
CONDITION_MARKERS = [
    r'場合',      # if
    r'時',        # when
    r'なら',      # if
    r'とき',      # when
    r'以上',      # >= (condition)
    r'以下',      # <= (condition)
    r'含む',      # contains
]

def is_condition_clause(text):
    """条件文かどうかを判定"""
    return any(re.search(p, text) for p in CONDITION_MARKERS)
```

### 優先度2: 数値抽出の改善

```python
def extract_effect_value(text, effect_type):
    """効果量を抽出（条件値と区別）"""
    # 効果パターンの後に来る数値を優先
    effect_patterns = {
        "DRAW": r'(引く|加える).*?([0-9]+)枚',
        "DISCARD": r'控え室に置く.*?([0-9]+)枚',
    }
    
    match = re.search(effect_patterns.get(effect_type, ''), text)
    if match:
        return int(match.group(1))
    return 1  # デフォルト
```

### 優先度3: セグメント分割

```python
def extract_segments(self, text):
    """より正確なセグメント分割"""
    # コストと効果の境界
    text = re.sub(r'：', '|COST|', text)
    # 接続詞
    text = re.sub(r'その後', '|THEN|', text)
    text = re.sub(r'さらに', '|AND|', text)
    
    segments = text.split('|')
    return [s.strip() for s in segments if s.strip() and s not in ['COST', 'THEN', 'AND']]
```

---

## 期待される効果

| 改善 | パス率向上 | 実装難易度 |
|:---|:---:|:---:|
| 条件検出 | +3% | 低 |
| 数値抽出改善 | +2% | 低 |
| セグメント分割 | +2% | 中 |
| コンパイラ連携 | +5% | 高 |
| LLM活用 | +5% | 高 |

**現在: 87.1% → 目標: 95%+**
