# Ability DSL Analysis
## Domain-Specific Language for Card Game Abilities

### Information Theory Perspective

Card game ability text is not random prose - it's a **domain-specific language (DSL)** for expressing game mechanics. Like a programming language, it has:
- **Syntax**: Grammatical structures that combine tokens
- **Semantics**: Game mechanics meaning behind the structures
- **Vocabulary**: Tokens representing game elements

By identifying these language structures, we can compress abilities like compiling source code to an AST:
- **Before**: N unique text strings (high entropy)
- **After**: 1 AST structure + M variable parameters (low entropy)

### Language Vocabulary (Tokens)

#### Structural Operators (Low Entropy - Keep as Template)
- **Actions**: 引く, 置く, 得る, 見る, 選ぶ, 公開, 加える, 登場, 移動, アクティブ, ウェイト
- **Conditions**: 場合, とき, たび, まで, から, に
- **Comparisons**: 以上, 以下, より多い, より少ない, 合計が
- **Connectors**: その中から, 残りを, それらが, そうした場合

#### Variables (High Entropy - Replace with Placeholders)
- **Numbers**: 1, 2, 3, etc.
- **Card Types**: カード, メンバーカード, ライブカード, エネルギーカード
- **Zones**: 手札, 控え室, デッキ, ステージ, ライブカード置き場, 成功ライブカード置き場
- **Resources**: ブレード, ハート, エール, スコア, エネルギー
- **Groups**: μ's, Aqours, 虹ヶ咲, Liella!, 蓮ノ空, etc.
- **Characters**: Names in 「」 brackets

### Language Syntax (Grammatical Structures)

#### 1. Basic Action Pattern
```
[Source]から[Count]枚[Target]を[Action]
```
Example: "自分のデッキの上からカードを5枚見る"
Template: "自分のデッキの上からカードを⟦X⟧枚見る"

#### 2. Conditional Pattern
```
[Condition]場合、[Effect]
```
Example: "自分のエネルギーが7枚以上ある場合、カードを1枚引く"
Template: "自分のエネルギーが⟦X⟧枚以上ある場合、カードを⟦Y⟧枚引く"

#### 3. Cost-Effect Pattern
```
[Cost]を[Count]枚控え室に置いてもよい：[Effect]
```
Example: "手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る"
Template: "⟦COST⟧を⟦X⟧枚控え室に置いてもよい：⟦EFFECT⟧"

#### 4. Look-Select-Add Pattern
```
[Source]から[Count]枚見る。その中から[Filter]を[SelectCount]枚[Destination]に加える。残りを[DiscardDest]に置く
```
Example: "自分のデッキの上からカードを5枚見る。その中から1枚を手札に加え、残りを控え室に置く"
Template: "自分のデッキの上からカードを⟦X⟧枚見る。その中から⟦Y⟧枚を手札に加え、残りを控え室に置く"

#### 5. Per-Unit Pattern
```
[Source]の[Unit][Count]につき、[Effect]
```
Example: "自分のステージにいるメンバー1人につき、カードを1枚引く"
Template: "自分のステージにいるメンバー⟦X⟧人につき、カードを⟦Y⟧枚引く"

#### 6. Duration Pattern
```
[Duration]、[Effect]
```
Example: "ライブ終了時まで、ブレードを得る"
Template: "ライブ終了時まで、⟦RESOURCE⟧を得る"

#### 7. State Change Pattern
```
[Target]を[State]にする
```
Example: "エネルギーを2枚アクティブにする"
Template: "エネルギーを⟦X⟧枚アクティブにする"

### Semantic Categories (Game Mechanics)

#### Card Movement
- Draw: デッキから手札に引く
- Discard: 手札/ステージから控え室に置く
- Add: 控え室から手札に加える
- Place: 任意のゾーンに置く

#### Resource Manipulation
- Gain: ブレード、ハート、エール、スコアを得る
- Pay: エネルギー、ハートを支払う
- Modify: スコア、コストを増減する

#### State Changes
- Activate: ウェイト→アクティブ
- Wait: アクティブ→ウェイト
- Move: エリア間移動
- Enter Stage: 控え室→ステージ

#### Conditional Effects
- Threshold: X枚以上/以下の場合
- Comparison: 相手より多い/少ない場合
- Presence: 特定カード/メンバーがいる場合
- Total: 合計がX以上の場合

### Compression Strategy

1. **Identify Language Structures**: Parse abilities to identify grammatical patterns
2. **Extract Variables**: Replace numbers, card types, groups, zones with placeholders
3. **Build Templates**: Create templates for each grammatical structure
4. **Count Coverage**: Measure how many clauses match each template
5. **Iterate**: Refine templates based on unmatched clauses

### Example Compression

**Original (171 unique clauses):**
- "自分の控え室からライブカードを1枚手札に加える"
- "自分の控え室からメンバーカードを1枚手札に加える"
- "自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える"

**Template:**
- "自分の控え室から⟦FILTER⟧カードを⟦X⟧枚手札に加える"

**Variables (27 unique combinations):**
- (ライブ, 1), (メンバー, 1), (『虹ヶ咲』のライブ, 1), etc.

**Compression**: 171 clauses → 1 template + 27 variable combinations
