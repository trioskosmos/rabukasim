# Parsing Issues Documentation

## Cards Mentioned by User

### LL-PR-004-PR | 愛♡スクリ～ム！
- **Issue**: Ability splitting bug - was split into 4 abilities instead of 1
- **Status**: FIXED - Modified extract_card_abilities.py to handle conditional outcomes (lines starting with "回答が" or containing "の場合")
- **Fix**: Added logic to append conditional continuation lines to previous ability

### PL!SP-bp5-001-SEC | 澁谷かのん
- **Issue**: Ability splitting bug - was split into 4 abilities instead of 2
- **Status**: FIXED - Same fix as LL-PR-004-PR
- **Fix**: Conditional continuation lines now correctly appended

### PL!HS-bp2-019-L | Bloom the smile, Bloom the dream!
- **Issue**: Heart cost modification with missing condition
- **Full text**: "{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。"
- **Parsed effect**: Only has "choose_heart_cost" action with options
- **Missing**: 
  - Condition "自分のステージに『蓮ノ空』のメンバーがいる場合"
  - Trigger information (live_start.png)
  - Optional flag "してもよい"
- **Status**: NOT FIXED
- **Required fix**: Add condition parsing for group presence, capture trigger context, add optional flag

## Parsing Issues Found by Index

### Ability #5
- **Full text**: "{{toujyou.png|登場}}自分のデッキの上からカードを3枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。"
- **Parsed effect**: look_at_cards + discard_to_waitroom
- **Missing**: "その中から好きな枚数を好きな順番でデッキの上に置き" (place cards back on deck in chosen order)
- **Status**: NOT FIXED
- **Required fix**: Add "place_on_deck" action with order specification

### Ability #16
- **Full text**: "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）"
- **Parsed effect**: look_at_cards + discard_to_waitroom + note
- **Missing**: "その中から好きな枚数を好きな順番でデッキの上に置き"
- **Status**: NOT FIXED
- **Required fix**: Same as #5

### Ability #17
- **Full text**: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：このカードを控え室からステージに登場させる。この能力は、このカードが控え室にある場合のみ起動できる。"
- **Parsed effect**: Condition as raw text, action as activation_restriction
- **Issue**: Activation restriction treated as action, deploy action treated as condition
- **Status**: NOT FIXED
- **Required fix**: Parse "この能力は、このカードが控え室にある場合のみ起動できる" as activation_restriction, parse "このカードを控え室からステージに登場させる" as deploy_to_stage action

### Ability #40
- **Full text**: "{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。"
- **Parsed effect**: Generic "reduce" action
- **Issue**: Should be specific cheer reveal count reduction, not generic reduce
- **Status**: NOT FIXED
- **Required fix**: Create specific action type for cheer_reveal_count_reduction

### Ability #50
- **Full text**: "{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。"
- **Parsed cost**: member_to_wait with optional=false
- **Issue**: "ウェイトにしてもよい" should be optional=true
- **Status**: NOT FIXED
- **Required fix**: Fix cost parser to correctly handle "してもよい" as optional

### Ability #70
- **Full text**: "{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。"
- **Parsed effect**: timing as separate action
- **Issue**: "timing" should be part of main action structure, not separate
- **Status**: NOT FIXED
- **Required fix**: Integrate timing into action structure

### Ability #80
- **Full text**: "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：相手のステージにいるコスト10以下のメンバー1人をウェイトにする。この能力を起動するためのコストは自分のステージにいるメンバーの中のグループ名1種類につき、{{icon_energy.png|E}}減る。"
- **Parsed effect**: Condition with per_unit and reduce action
- **Issue**: Cost reduction based on group variety should be in cost field, not effect
- **Status**: NOT FIXED
- **Required fix**: Parse cost reduction as cost modifier, not effect

### Ability #180
- **Full text**: "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべてメンバーカードの場合、カードを1枚引く。"
- **Parsed effect**: Condition as raw text including discard action
- **Issue**: Entire discard treated as condition, should be: discard_to_waitroom + condition + draw_cards
- **Status**: NOT FIXED
- **Required fix**: Parse as sequence: discard 3 cards → condition (all member cards) → draw 1 card

### Ability #200
- **Full text**: "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、ライブ終了時まで、［緑ハート］を得る。"
- **Parsed effect**: gain_resource without heart type
- **Issue**: Should specify heart_type: green
- **Status**: NOT FIXED
- **Required fix**: Add heart_type extraction for bracket notation like ［緑ハート］

### Ability #250
- **Full text**: "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
- **Parsed effect**: Condition as raw text
- **Issue**: Should be member_deploy_count >= 2
- **Status**: NOT FIXED
- **Required fix**: Parse member deployment count condition

### Ability #350
- **Full text**: "{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。"
- **Parsed effect**: Condition includes add_to_hand action, action is just place_card
- **Issue**: Should be: optional reveal + add_to_hand + conditional place_card
- **Status**: NOT FIXED
- **Required fix**: Parse as optional cost + main action + conditional follow-up action

### Ability #550
- **Full text**: "{{toujyou.png|登場}}このターン、自分のステージにいるほかのメンバーがエリアを移動している場合、カードを1枚引く。"
- **Parsed effect**: Condition as raw text
- **Issue**: Should be member_area_move condition
- **Status**: NOT FIXED
- **Required fix**: Parse member area movement condition

### Ability #580
- **Full text**: "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバー1人につき、カードを1枚引く。その後、これにより引いた枚数と同じ枚数を手札から控え室に置く。"
- **Parsed effect**: Only draw_cards with per_unit condition
- **Issue**: Missing "その後" discard action based on drawn cards
- **Status**: NOT FIXED
- **Required fix**: Parse sequential actions with "その後" marker

## Summary

**Total Issues**: 14 (13 parsing issues + 1 card-specific issue)
**Fixed**: 2 (ability splitting for LL-PR-004-PR and PL!SP-bp5-001-SEC)
**Not Fixed**: 12

**Priority Fixes**:
1. Cost optional flag (ability #50) - simple fix in cost_parser.py
2. Missing deck placement action (abilities #5, #16) - add action type
3. Sequential action parsing (ability #580) - handle "その後"
4. Condition parsing improvements (abilities #250, #350, #550) - add new condition types
5. Heart cost modification (PL!HS-bp2-019-L) - new action type or cost modifier
