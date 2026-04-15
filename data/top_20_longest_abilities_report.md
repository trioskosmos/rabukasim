# Top 20 Longest Abilities - Manual Analysis Report

## Approach Descriptions

### 1. Manual Opcode Mapping
Direct mapping of ability text to specific opcodes based on verb/action analysis

### 2. Template-First Approach
Using existing combined_templates as the primary structure and mapping to opcodes

### 3. State Transformation Approach
Based on ability_concrete_format_documentation.md framework - treating abilities as state transformations over zones, resources, and state flags

---

## 1. Ability (Length: 303 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。

**Combined Template:**  ： [player]の[zone]に『[group_name]』の[object]がいる場合、この[card]を成功させるための必要[card]は、[heart][heart][heart]か、[heart][heart][heart]か、[heart][heart][heart]のうち、選んだ[number]つにしてもよい。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone]に『[group_name]』の[object]がいる場合、この[card]を成功させるための必要[card]は、[heart][heart][heart]か、[heart][heart][heart]か、[heart][heart][heart]のうち、選んだ[number]つにしてもよい。

**Card Examples:** PL!HS-bp2-019-L | Bloom the smile, Bloom the dream! (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 2. Ability (Length: 297 characters)

**Full Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが2枚以上あるか、自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_06.png|heart06}}のうち合計5種類以上あるか、このターンに自分のステージにいるメンバーがエリアを移動している場合、このカードのスコアを+１する。

**Combined Template:**  ： エールにより公開された[player]の[card]の中に[card]が[number]枚以上あるか、[player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]のうち合計[number]種類以上あるか、このターンに[player]の[zone_condition][object]が[zone]を移動している場合、この[card]の[value_type:score]を+[number]する。

**Card Count:** 1

**Triggers:** ['ライブ成功時']

**Cost Template:** 

**Effect Template:** エールにより公開された[player]の[card]の中に[card]が[number]枚以上あるか、[player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]のうち合計[number]種類以上あるか、このターンに[player]の[zone_condition][object]が[zone]を移動している場合、この[card]の[value_type:score]を+[number]する。

**Card Examples:** LL-bp5-001-L | Live with a smile! (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 3. Ability (Length: 269 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が3の『虹ヶ咲』のライブカードがある場合、ライブ終了時まで、自分のステージにいる{{heart_06.png|heart06}}を持つ『虹ヶ咲』のメンバー1人は{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。

**Combined Template:**  ： [player]の[card]置き場かライブ中の[card]の中に、必要[card]に含まれる[heart]が[number]の[card]がある場合、ライブ終了時まで、[player]の[zone_condition][heart]を持つ『[group_name]』の[object][number]人は[heart][heart][heart][icon_gain]。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[card]置き場かライブ中の[card]の中に、必要[card]に含まれる[heart]が[number]の[card]がある場合、ライブ終了時まで、[player]の[zone_condition][heart]を持つ『[group_name]』の[object][number]人は[heart][heart][heart][icon_gain]。

**Card Examples:** PL!N-pb1-039-L | Stellar Stream (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 4. Ability (Length: 265 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がすべてある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Combined Template:**  ： [player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がすべてある場合、ライブ終了時まで、{{icon_blade.png|[card]}}[icon_gain]。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がすべてある場合、ライブ終了時まで、{{icon_blade.png|[card]}}[icon_gain]。

**Card Examples:** PL!N-bp5-015-N | 桜坂しずく (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 5. Ability (Length: 261 characters)

**Full Text:** {{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、エールにより公開された自分のカードが持つブレードハートの中に[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}のうち、3種類以上ある場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。6種類以上ある場合、さらにライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。

**Combined Template:**  ： {{turn[number].png|ターン[number]回}}[player]がエールしたとき、エールにより公開された[player]の[card]が持つ[card][card]の中に[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、{{icon_b_all.png|ALL[card]}}のうち、[number]種類以上ある場合、ライブ終了時まで、[icon_gain]。[number]種類以上ある場合、さらにライブ終了時まで、[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。

**Card Count:** 4

**Triggers:** ['自動']

**Cost Template:** 

**Effect Template:** {{turn[number].png|ターン[number]回}}[player]がエールしたとき、エールにより公開された[player]の[card]が持つ[card][card]の中に[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、[[colored_blade]]、{{icon_b_all.png|ALL[card]}}のうち、[number]種類以上ある場合、ライブ終了時まで、[icon_gain]。[number]種類以上ある場合、さらにライブ終了時まで、[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。

**Card Examples:** PL!N-bp5-001-P | 上原歩夢 (ab#0), PL!N-bp5-001-R+ | 上原歩夢 (ab#0), PL!N-bp5-001-AR | 上原歩夢 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 6. Ability (Length: 250 characters)

**Full Text:** {{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このメンバーをステージから控え室に置く：自分の手札からコスト13以下の「優木せつ菜」のメンバーカードを1枚、このメンバーがいたエリアに登場させる。その後、自分のエネルギー置き場にあるエネルギー1枚をそのメンバーの下に置く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）

**Combined Template:** [icon_count:1][card]を[zone_placement] ： [player]の[zone]から[value_type:cost][number]以下の[character_name]の[card]を[number]枚、[card]がいた[zone]に登場させる。その後、[player]の[zone_condition][card][number]枚をその[object]の下に置く。([object]の下に置かれている[card]では[value_type:cost]を支払えない。[object]が[zone]から離れたとき、下に置かれている[card]は[card]に置く。)

**Card Count:** 2

**Triggers:** ['起動']

**Cost Template:** [icon_count:1][card]を[zone_placement]

**Effect Template:** [player]の[zone]から[value_type:cost][number]以下の[character_name]の[card]を[number]枚、[card]がいた[zone]に登場させる。その後、[player]の[zone_condition][card][number]枚をその[object]の下に置く。([object]の下に置かれている[card]では[value_type:cost]を支払えない。[object]が[zone]から離れたとき、下に置かれている[card]は[card]に置く。)

**Card Examples:** PL!N-bp3-007-R | 優木せつ菜 (ab#0), PL!N-bp3-007-P | 優木せつ菜 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 7. Ability (Length: 241 characters)

**Full Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Combined Template:** [icon_count:1]支払ってもよい ： ライブ終了時まで、{{icon_blade.png|[card]}}{{icon_blade.png|[card]}}[icon_gain]。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** [icon_count:1]支払ってもよい

**Effect Template:** ライブ終了時まで、{{icon_blade.png|[card]}}{{icon_blade.png|[card]}}[icon_gain]。

**Card Examples:** LL-bp3-001-R+ | 園田海未&津島善子&天王寺璃奈 (ab#1)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 8. Ability (Length: 234 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）

**Combined Template:**  ： [player]の[zone_condition][card][number]枚を[card]の下に置いてもよい。そうした場合、[draw_effect]、ライブ終了時まで、[player]の[zone_condition][object]は{{icon_blade.png|[card]}}[icon_gain]。([object]の下に置かれている[card]では[value_type:cost]を支払えない。[object]が[zone]から離れたとき、下に置かれている[card]は[card]に置く。)

**Card Count:** 4

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone_condition][card][number]枚を[card]の下に置いてもよい。そうした場合、[draw_effect]、ライブ終了時まで、[player]の[zone_condition][object]は{{icon_blade.png|[card]}}[icon_gain]。([object]の下に置かれている[card]では[value_type:cost]を支払えない。[object]が[zone]から離れたとき、下に置かれている[card]は[card]に置く。)

**Card Examples:** PL!N-bp3-001-R+ | 上原歩夢 (ab#0), PL!N-bp3-001-P | 上原歩夢 (ab#0), PL!N-bp3-001-P+ | 上原歩夢 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 9. Ability (Length: 233 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}になる。

**Combined Template:**  ： [player]の、[zone]と[zone]にいる名前の異なる『[group_name]』の[object]が[number]人以上いる場合、この[card]を使用するための[value_type:cost]は[heart][heart][heart][heart][heart][heart]になる。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の、[zone]と[zone]にいる名前の異なる『[group_name]』の[object]が[number]人以上いる場合、この[card]を使用するための[value_type:cost]は[heart][heart][heart][heart][heart][heart]になる。

**Card Examples:** PL!SP-bp1-026-L | 未来予報ハレルヤ！ (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 10. Ability (Length: 233 characters)

**Full Text:** {{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がある場合、このカードのスコアを+１する。

**Combined Template:**  ： エールにより公開された[player]の[card]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がある場合、この[card]の[value_type:score]を+[number]する。

**Card Count:** 1

**Triggers:** ['ライブ成功時']

**Cost Template:** 

**Effect Template:** エールにより公開された[player]の[card]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がある場合、この[card]の[value_type:score]を+[number]する。

**Card Examples:** PL!N-bp4-025-L | VIVID WORLD (ab#1)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 11. Ability (Length: 232 characters)

**Full Text:** {{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）

**Combined Template:** {{center.png|[position]}}{{turn[number].png|ターン[number]回}}[card]を[zone]にし、[zone]を[number]枚[zone]に置く ： [card]以外の『[group_name]』の[object][number]人を[player]の[zone_placement]。そうした場合、[player]の[zone]から、その[object]の[value_type:cost]に[number]を足した数に等しい[value_type:cost]の[card]を[number]枚、その[object]がいた[zone]に登場させる。(この能力は[position][zone]に登場している場合のみ起動できる。)

**Card Count:** 4

**Triggers:** ['起動']

**Cost Template:** {{center.png|[position]}}{{turn[number].png|ターン[number]回}}[card]を[zone]にし、[zone]を[number]枚[zone]に置く

**Effect Template:** [card]以外の『[group_name]』の[object][number]人を[player]の[zone_placement]。そうした場合、[player]の[zone]から、その[object]の[value_type:cost]に[number]を足した数に等しい[value_type:cost]の[card]を[number]枚、その[object]がいた[zone]に登場させる。(この能力は[position][zone]に登場している場合のみ起動できる。)

**Card Examples:** PL!S-bp3-006-R+ | 津島善子 (ab#0), PL!S-bp3-006-P | 津島善子 (ab#0), PL!S-bp3-006-P+ | 津島善子 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 12. Ability (Length: 229 characters)

**Full Text:** {{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。

**Combined Template:**  ： [player]のライブ中の[card]の必要[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がそれぞれ[number]以上含まれるかぎり、[icon_gain]。

**Card Count:** 2

**Triggers:** ['常時']

**Cost Template:** 

**Effect Template:** [player]のライブ中の[card]の必要[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がそれぞれ[number]以上含まれるかぎり、[icon_gain]。

**Card Examples:** PL!N-pb1-007-R | 優木せつ菜 (ab#0), PL!N-pb1-007-P+ | 優木せつ菜 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 13. Ability (Length: 221 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバーが持つ{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_06.png|heart06}}のうち1色につき、このカードのスコアを+１する。

**Combined Template:**  ： [player]の[zone_condition]『[group_name]』の[object]が持つ[heart]、[heart]、[heart]、[heart]、[heart]、[heart]のうち[number]色につき、この[card]の[value_type:score]を+[number]する。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone_condition]『[group_name]』の[object]が持つ[heart]、[heart]、[heart]、[heart]、[heart]、[heart]のうち[number]色につき、この[card]の[value_type:score]を+[number]する。

**Card Examples:** PL!N-bp1-027-L | Solitude Rain (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 14. Ability (Length: 221 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がすべてある場合、このカードのスコアを+１する。

**Combined Template:**  ： [player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がすべてある場合、この[card]の[value_type:score]を+[number]する。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone_condition][object]が持つ[card]の中に[heart]、[heart]、[heart]、[heart]、[heart]、[heart]がすべてある場合、この[card]の[value_type:score]を+[number]する。

**Card Examples:** PL!N-bp5-026-L | TOKIMEKI Runners (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 15. Ability (Length: 220 characters)

**Full Text:** {{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを+２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）

**Combined Template:**  ： {{center.png|[position]}}[player]の[card]置き場に{{icon_score.png|[value_type:score]}}を持つ[card]が[number]枚ある場合、ライブ終了時まで、[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。[number]枚以上ある場合、代わりに[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。(この能力は[position][zone]に登場した場合のみ発動する。)

**Card Count:** 2

**Triggers:** ['登場']

**Cost Template:** 

**Effect Template:** {{center.png|[position]}}[player]の[card]置き場に{{icon_score.png|[value_type:score]}}を持つ[card]が[number]枚ある場合、ライブ終了時まで、[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。[number]枚以上ある場合、代わりに[icon_count:1]ライブの合計[value_type:score]を+[number]する。を得る。(この能力は[position][zone]に登場した場合のみ発動する。)

**Card Examples:** PL!-pb1-004-R | 園田海未 (ab#0), PL!-pb1-004-P+ | 園田海未 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 16. Ability (Length: 220 characters)

**Full Text:** {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージにコスト9以上の『EdelNote』のメンバーがいる場合、以下から1つを選ぶ。
・自分の控え室からコスト4以下の『EdelNote』のメンバーカードを1枚、メンバーのいないエリアに登場させる。
・このカードの必要ハートを{{heart_06.png|heart06}}減らす。

**Combined Template:** [icon_count:1]支払ってもよい ： [player]の[zone]に[value_type:cost][number]以上の『[group_name]』の[object]がいる場合、以下から[number]つを選ぶ。・[player]の[zone]から[value_type:cost][number]以下の[card]を[number]枚、[object]のいない[zone]に登場させる。・この[card]の必要[card]を[heart]減らす。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** [icon_count:1]支払ってもよい

**Effect Template:** [player]の[zone]に[value_type:cost][number]以上の『[group_name]』の[object]がいる場合、以下から[number]つを選ぶ。・[player]の[zone]から[value_type:cost][number]以下の[card]を[number]枚、[object]のいない[zone]に登場させる。・この[card]の必要[card]を[heart]減らす。

**Card Examples:** PL!HS-bp5-022-L | Retrofuture (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 17. Ability (Length: 218 characters)

**Full Text:** {{live_start.png|ライブ開始時}}自分のステージに{{heart_02.png|heart02}}を4つ以上持つメンバーがいる場合、このカードのスコアを+２し、必要ハートは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}になる。

**Combined Template:**  ： [player]の[zone]に[heart]を[number]つ以上持つ[object]がいる場合、この[card]の[value_type:score]を+[number]し、必要[card]は[heart][heart][heart][heart][heart]になる。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** 

**Effect Template:** [player]の[zone]に[heart]を[number]つ以上持つ[object]がいる場合、この[card]の[value_type:score]を+[number]し、必要[card]は[heart][heart][heart][heart][heart]になる。

**Card Examples:** PL!N-bp5-028-L | CHASE! (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 18. Ability (Length: 216 characters)

**Full Text:** {{toujyou.png|登場}}以下から1つを選ぶ。
・自分のステージにいるこのメンバー以外の『Aqours』のメンバー1人は、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)

**Combined Template:**  ： 以下から[number]つを選ぶ。・[player]の[zone_condition][card]以外の『[group_name]』の[object][number]人は、ライブ終了時まで、[icon_gain]。・[player]の[zone_condition]『[group_name]』の[object][number]人をポジションチェンジさせる。([card]を今いる[zone]以外の[zone]に移動させる。その[zone]に[object]がいる場合、その[object]は[card]がいた[zone]に移動させる。)

**Card Count:** 3

**Triggers:** ['登場']

**Cost Template:** 

**Effect Template:** 以下から[number]つを選ぶ。・[player]の[zone_condition][card]以外の『[group_name]』の[object][number]人は、ライブ終了時まで、[icon_gain]。・[player]の[zone_condition]『[group_name]』の[object][number]人をポジションチェンジさせる。([card]を今いる[zone]以外の[zone]に移動させる。その[zone]に[object]がいる場合、その[object]は[card]がいた[zone]に移動させる。)

**Card Examples:** PL!S-bp5-004-P | 黒澤ダイヤ (ab#0), PL!S-bp5-004-R | 黒澤ダイヤ (ab#0), PL!S-bp5-004-AR | 黒澤ダイヤ (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 19. Ability (Length: 214 characters)

**Full Text:** {{live_start.png|ライブ開始時}}手札の『蓮ノ空』のカードを2枚控え室に置いてもよい：{{heart_01.png|heart01}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいるこのメンバー以外の『蓮ノ空』のメンバー1人は、選んだハートを2つ得る。

**Combined Template:** [zone]の[card]を[number]枚[zone]に置いてもよい ： [heart]か[heart]か[heart]か[heart]のうち、[number]つを選ぶ。ライブ終了時まで、[player]の[zone_condition][card]以外の『[group_name]』の[object][number]人は、選んだ[card]を[number]つ得る。

**Card Count:** 1

**Triggers:** ['ライブ開始時']

**Cost Template:** [zone]の[card]を[number]枚[zone]に置いてもよい

**Effect Template:** [heart]か[heart]か[heart]か[heart]のうち、[number]つを選ぶ。ライブ終了時まで、[player]の[zone_condition][card]以外の『[group_name]』の[object][number]人は、選んだ[card]を[number]つ得る。

**Card Examples:** PL!HS-sd1-008-SD | 桂城 泉 (ab#1)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

## 20. Ability (Length: 211 characters)

**Full Text:** {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Combined Template:** [zone]を[number]枚[zone]に置いてもよい ： [player]の[zone]の上から[card_look]。その中から[number]枚を[zone_placement]。[icon_count:1]支払ってもよい：ライブ終了時まで、{{icon_blade.png|[card]}}[icon_gain]。

**Card Count:** 2

**Triggers:** ['登場']

**Cost Template:** [zone]を[number]枚[zone]に置いてもよい

**Effect Template:** [player]の[zone]の上から[card_look]。その中から[number]枚を[zone_placement]。[icon_count:1]支払ってもよい：ライブ終了時まで、{{icon_blade.png|[card]}}[icon_gain]。

**Card Examples:** PL!S-PR-013-PR | 高海千歌 (ab#0), PL!S-PR-019-PR | 国木田花丸 (ab#0)

---

### Manual Opcode Mapping

[TO BE FILLED]

---

### Template-First Approach

[TO BE FILLED]

---

### State Transformation Approach

[TO BE FILLED]

---

