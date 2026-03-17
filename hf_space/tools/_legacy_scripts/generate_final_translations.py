import json
import re

# Final batch of translations
translations_map = {
    # [2] PL!SP-bp1-002-R＋
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。": "[On Play] You may pay (E)(E): If this member is on the Left Side Area, draw 2 cards.",
    # [2] PL!SP-bp1-003-R＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札にあるメンバーカードを好きな枚数公開する：公開したカードのコストの合計が、10、20、30、40、50のいずれかの場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[Activate] [Turn 1] Reveal any number of Member cards from your hand: If the total Cost of the revealed cards is 10, 20, 30, 40, or 50, this member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [2] PL!SP-bp1-007-R＋
    "{{toujyou.png|登場}}自分のエネルギーが11枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。": "[On Play] If you have 11 or more Energy, add 1 Live card from your waiting room to your hand.",
    # [2] PL!HS-bp1-003-R＋
    "{{jyouji.png|常時}}自分のステージのエリアすべてに『蓮ノ空』のメンバーが登場しており、かつ名前が異なる場合、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": "[Continuous] If you have 'Hasunosora' members with different names in all areas of your stage, this member gets \"[Continuous] Live Score +1\".",
    # [2] PL!HS-bp1-004-R＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}：自分の控え室から4コスト以下の『蓮ノ空』のメンバーカードを1枚手札に加える。": "[Activate] [Turn 1] (E): Add 1 'Hasunosora' Member card with Cost 4 or less from your waiting room to your hand.",
    # [2] PL!HS-bp1-004-R＋ (Second ability)
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。": "[Activate] [Turn 1] (E)(E)(E): Add 1 'Hasunosora' Live card from your waiting room to your hand.",
    # [2] PL!HS-bp1-004-R＋ (Third ability)
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のライブ中のカード1枚につき、{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay (E): This member gets +1 Blade for each of your Live cards in progress until the end of the live phase.",
    # [2] PL!HS-bp1-006-R＋
    "{{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。": "[On Play] Draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [2] PL!HS-bp1-006-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。": "[Live Start] You may put 1 card from your hand into the waiting room: If you have other members on your stage, declare 1 Heart color. This member gets that Heart until the end of the live phase.",
    # [2] PL!SP-pb1-003-R
    "{{toujyou.png|登場}}自分のステージにいるメンバーが『5yncri5e!』のみの場合、自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる。": "[On Play] If you have only '5yncri5e!' members on your stage, both you and your opponent move the member in the Center Area to the Left Side Area, the member in the Left Side Area to the Right Side Area, and the member in the Right Side Area to the Center Area.",
    # [2] PL!SP-pb1-004-R
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Start] You may pay (E)(E): Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [2] PL!SP-pb1-004-R (Second ability)
    "{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：カードを1枚引く。": "[Live Success] You may pay (E)(E)(E): Draw 1 card.",
    # [2] PL!S-bp2-005-R＋
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを7枚見る。その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 7 cards of your deck. You may reveal up to 3 Member cards with [Heart 02], [Heart 04], or [Heart 05] from among them and add them to your hand. Put the rest into the waiting room.",
    # [2] PL!S-bp2-007-R＋
    "{{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分の手札が7枚以下の場合、カードを1枚引く。": "[Auto] [Turn 1] When you reveal 1 or more Live cards via Yell, if you have 7 or fewer cards in your hand, draw 1 card.",
    # [2] PL!S-bp2-007-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札のライブカードを1枚公開し、デッキの一番下に置いてもよい：自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。": "[Live Start] You may reveal 1 Live card from your hand and put it on the bottom of your deck: Look at the top 2 cards of your deck. Put any number of them back on top of your deck in any order, and put the rest into the waiting room.",
    # [2] PL!S-bp2-008-R＋
    "{{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。": "[On Play] Put up to 1 Live card from your waiting room on the bottom of your deck.",
    # [2] PL!S-bp2-008-R＋ (Second ability)
    "{{jyouji.png|常時}}自分のステージのエリアすべてに『Aqours』のメンバーが登場しており、かつ名前が異なる場合、「{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上ある場合、ライブの合計スコアを＋１する。ライブカードが3枚以上ある場合、代わりに合計スコアを＋２する。」を得る。": "[Continuous] If you have 'Aqours' members with different names in all areas of your stage, this member gets \"[Live Success] If you revealed 1 or more Live cards via Yell, Live Score +1. If you revealed 3 or more Live cards, Live Score +2 instead.\".",
    # [2] PL!SP-bp2-001-R＋
    "{{toujyou.png|登場}}自分のステージにいる『Liella!』のメンバー1人のすべての{{live_start.png|ライブ開始時}}能力を、ライブ終了時まで、無効にしてもよい。これにより無効にした場合、自分の控え室から『Liella!』のカードを1枚手札に加える。": "[On Play] You may negate all [Live Start] abilities of 1 'Liella!' member on your stage until the end of the live phase. If you do, add 1 'Liella!' card from your waiting room to your hand.",
    # [2] PL!SP-bp2-006-R＋
    "{{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。": "[On Play] If this member entered via Baton Touch, add 1 'Liella!' Member card put into the waiting room by this Baton Touch to your hand.",
    # [2] PL!SP-bp2-006-R＋ (Second ability)
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のコスト4以下の『Liella!』のメンバーカードを1枚控え室に置く：これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる。": "[Activate] [Turn 1] Put 1 'Liella!' Member card with Cost 4 or less from your hand into the waiting room: Activate 1 [On Play] ability of the member card put into the waiting room.",
    # [2] PL!SP-bp2-006-R＋ (Note)
    "({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)": "(If the [On Play] ability has a cost, you must pay it to activate.)",
    # [2] PL!SP-bp2-009-R＋
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分の手札2枚につき、{{icon_blade.png|ブレード}}を得る。": "[Live Start] This member gets +1 Blade for every 2 cards in your hand until the end of the live phase.",
    # [2] PL!SP-bp2-009-R＋ (Second ability)
    "{{live_success.png|ライブ成功時}}カードを2枚引き、手札を1枚控え室に置く。": "[Live Success] Draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [2] PL!SP-bp2-010-R＋
    "{{jyouji.png|常時}}相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる。": "[Continuous] All Live cards in your opponent's Live Area require +1 Heart to succeed.",
    # [2] PL!SP-bp2-010-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}自分のステージにこのメンバー以外のメンバーが1人以上いる場合、ライブ終了時まで、エールによって公開される自分のカードの枚数が8枚減る。": "[Live Start] If you have 1 or more other members on your stage, the number of cards revealed by your Yell is reduced by 8 until the end of the live phase.",
    # [2] PL!HS-bp2-002-R＋
    "{{toujyou.png|登場}}自分の控え室からコスト2以下のメンバーカードを2枚まで手札に加える。": "[On Play] Add up to 2 Member cards with Cost 2 or less from your waiting room to your hand.",
    # [2] PL!HS-bp2-002-R＋ (Second ability)
    "{{jyouji.png|常時}}自分のステージに、このメンバーよりコストの大きいメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] If you have a member with a higher Cost than this member on your stage, this member gets +3 Blades.",
    # [2] PL!HS-bp2-005-R＋
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにほかのメンバーがいる場合、自分の控え室から『みらくらぱーく！』のカードを1枚手札に加える。": "[On Play] You may put 1 card from your hand into the waiting room: If you have other members on your stage, add 1 'Mira-Cra Park!' card from your waiting room to your hand.",
    # [2] PL!HS-bp2-005-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：自分のステージのエリアすべてにメンバーが登場している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay (E): If you have members in all areas of your stage, this member gets +2 Blades until the end of the live phase.",
    # [2] PL!HS-bp2-007-R＋
    "{{toujyou.png|登場}}このメンバーよりコストが低い『スリーズブーケ』のメンバーからバトンタッチして登場した場合、自分の控え室から『蓮ノ空』のライブカードを1枚手札に加える。": "[On Play] If this member entered via Baton Touch from a 'Cerise Bouquet' member with a lower Cost, add 1 'Hasunosora' Live card from your waiting room to your hand.",
    # [2] PL!HS-bp2-007-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：これにより控え室に置いたカードがメンバーカードの場合、控え室に置いたカードと同じ名前を持つメンバー1人は、ライブ終了時まで、{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 1 card from your hand into the waiting room: If the card put into the waiting room was a Member card, 1 member with the same name gets [Heart 04] and +1 Blade until the end of the live phase.",
    # [2] PL!-bp3-004-R＋
    "{{toujyou.png|登場}}自分のステージにいるメンバー1人につき、カードを1枚引く。その後、手札を1枚控え室に置く。": "[On Play] Draw 1 card for each member on your stage. Then, put 1 card from your hand into the waiting room.",
    # [2] PL!-bp3-004-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、手札を1枚控え室に置いてもよい。そうした場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。": "[Live Start] If you have cards in your Success Live Area, you may put 1 card from your hand into the waiting room. If you do, add 1 'μ's' Live card from your waiting room to your hand.",
    # [2] PL!-bp3-008-R＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：自分の控え室から『μ's』のライブカードを1枚手札に加える。": "[Activate] [Turn 1] Set this member to Waiting state: Add 1 'μ's' Live card from your waiting room to your hand.",
    # [2] PL!-bp3-008-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}『μ's』のメンバー1人をウェイトにしてもよい：ライブ終了時まで、{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る。": "[Live Start] You may set 1 'μ's' member to Waiting state: This member gets [Heart 03][Heart 03] until the end of the live phase.",
    # [2] PL!S-bp3-001-R＋
    "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}メンバー1人をウェイトにする：ライブ終了時まで、これによってウェイト状態になったメンバーは、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。（この能力はセンターエリアに登場している場合のみ起動できる。）": '[Activate] [Center] [Turn 1] Set 1 member to Waiting state: The member set to Waiting state by this effect gets "[Continuous] Live Score +1" until the end of the live phase. (Can only be used while in the Center Area.)',
    # [2] PL!S-bp3-006-R＋
    "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：このメンバー以外の『Aqours』のメンバー1人を自分のステージから控え室に置く。そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる。（この能力はセンターエリアに登場している場合のみ起動できる。）": "[Activate] [Center] [Turn 1] Set this member to Waiting state and put 1 card from your hand into the waiting room: Put 1 other 'Aqours' member from your stage into the waiting room. If you do, play 1 'Aqours' Member card from your waiting room with Cost equal to that member's Cost + 2 into the area that member was in. (Can only be used while in the Center Area.)",
    # [2] PL!S-bp3-010-N
    "{{toujyou.png|登場}}自分のステージにいるメンバーを1人までアクティブにする。": "[On Play] Activate up to 1 member on your stage.",
    # [2] PL!N-bp3-001-R＋
    "{{live_start.png|ライブ開始時}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを1枚引き、ライブ終了時まで、自分のステージにいるメンバーは{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）": "[Live Start] You may put 1 Energy from your Energy Area under this member. If you do, draw 1 card, and your members on stage get +2 Blades until the end of the live phase. (Energy cards under members cannot be used to pay costs. When the member leaves the stage, put the underlying Energy cards into the Energy Deck.)",
    # [2] PL!-bp4-002-R＋
    "{{jyouji.png|常時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがあるかぎり、{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。": "[Continuous] As long as you have a Live card in progress with no [Live Start] or [Live Success] abilities, this member gets [Heart 06][Heart 06].",
    # [2] PL!-bp4-002-R＋ (Second ability)
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合のみ起動できる。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 'μ's' Live card from your waiting room to your hand. This ability can only be used if the total Score of cards in your Success Live Area is 6 or more.",
    # [2] PL!N-bp4-007-R＋
    "{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からライブカードを1枚手札に加える。": "[On Play] Both you and your opponent add 1 Live card from their own waiting room to their hand.",
    # [2] PL!N-bp4-007-R＋ (Second ability)
    "{{jyouji.png|常時}}自分と相手のエネルギーの合計が15枚以上あるかぎり、{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る。": "[Continuous] As long as the total number of Energy cards held by you and your opponent is 15 or more, this member gets [Heart 02][Heart 02].",
    # [2] PL!N-bp4-007-R＋ (Third ability)
    "{{live_success.png|ライブ成功時}}自分と相手はそれぞれ、自身のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Success] Both you and your opponent place 1 Energy card from their own Energy Deck into their Energy Area in Waiting state.",
    # [2] PL!N-bp4-010-R＋
    "{{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。": "[On Play] You may put 1 'Nijigasaki' Live card from your Success Live Area into the waiting room. If you do, put 1 'Nijigasaki' Live card from your waiting room into your Success Live Area.",
    # [2] PL!N-bp4-010-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}自分のライブ中の『虹ヶ咲』のライブカードを1枚選ぶ。それと同じカード名のカードが自分の成功ライブカード置き場にある場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。": "[Live Start] Choose 1 'Nijigasaki' Live card in progress. If there is a card with the same name in your Success Live Area, this member gets [Heart 04] until the end of the live phase.",
    # [2] PL!N-bp4-011-R＋
    "{{live_start.png|ライブ開始時}}手札のライブカードを1枚控え室に置いてもよい：好きなハートの色を1つ指定する。ライブ終了時まで、そのハートを1つ得る。": "[Live Start] You may put 1 Live card from your hand into the waiting room: Declare 1 Heart color. This member gets that Heart until the end of the live phase.",
    # [2] PL!N-bp4-011-R＋ (Second ability)
    "{{live_success.png|ライブ成功時}}自分のデッキの上からカードを5枚控え室に置く。その後、自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが3枚以上ある場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。": "[Live Success] Put the top 5 cards of your deck into the waiting room. Then, if there are 3 or more 'Nijigasaki' Live cards with different names in your waiting room, add 1 'Nijigasaki' Live card from your waiting room to your hand.",
    # [2] PL!SP-bp4-004-R＋
    "{{jyouji.png|常時}}このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい。": "[Continuous] When playing this card, you may Baton Touch with 2 members.",
    # [2] PL!SP-bp4-004-R＋ (Second ability)
    "{{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。": "[On Play] [Center] If this member entered via Baton Touch from 2 'Liella!' members, draw 2 cards, and play 1 'Liella!' Member card with Cost 4 or less from your waiting room to an empty area on your stage.",
    # [2] PL!SP-bp4-005-R＋
    "{{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。": "[On Play] If this member entered via Baton Touch from a 'Liella!' member and you have 7 or more Energy, place 2 Energy cards from your Energy Deck into your Energy Area in Waiting state.",
    # [2] PL!SP-bp4-005-R＋ (Second ability)
    "{{jyouji.png|常時}}自分のエネルギーが10枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as you have 10 or more Energy, this member gets +3 Blades.",
    # [2] PL!SP-bp4-008-R＋
    "{{toujyou.png|登場}}【左サイド】カードを2枚引き、手札を1枚控え室に置く。": "[On Play] [Left Side] Draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [2] PL!SP-bp4-008-R＋ (Second ability)
    "{{toujyou.png|登場}}【右サイド】エネルギーを2枚アクティブにする。": "[On Play] [Right Side] Activate 2 Energy.",
    # [2] PL!SP-bp4-008-R＋ (Third ability)
    "{{live_start.png|ライブ開始時}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)": "[Live Start] You may Position Change this member. (Move this member to a different area. If a member is in that area, move that member to the area this member was in.)",
    # [2] PL!SP-bp4-009-R
    "{{jyouji.png|常時}}自分のステージにいるメンバーのコストの合計が相手より低いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as the total Cost of members on your stage is lower than your opponent's, this member gets +3 Blades.",
    # [2] PL!SP-bp4-010-R
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}このメンバーをウェイトにする：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Activate] [Turn 1] (E), set this member to Waiting state: Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [2] PL!SP-bp4-011-R＋
    "{{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。": "[Auto] When this member enters the stage or moves to a different area, set 1 member on your opponent's stage with 3 or fewer base Blades to Waiting state.",
    # [2] PL!N-pb1-001-R
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のステージにこのメンバー以外のコスト11のメンバーがいる場合、自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。": "[On Play] You may put 1 card from your hand into the waiting room: If you have another Cost 11 member on your stage, add 1 'Nijigasaki' Live card from your waiting room to your hand.",
    # [2] PL!N-pb1-001-R (Second ability)
    "{{jyouji.png|常時}}自分のライブ中のライブカードが2枚以上あるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as you have 2 or more Live cards in progress, this member gets +2 Blades.",
    # [2] PL!N-pb1-002-R
    "{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい。": "[On Play] You may put 2 Energy from your Energy Area under this member.",
    # [2] PL!N-pb1-002-R (Second ability)
    "{{jyouji.png|常時}}このメンバーの下にエネルギーカードが2枚以上置かれているかぎり、ライブの合計スコアを＋１する。": "[Continuous] As long as there are 2 or more Energy cards under this member, Live Score +1.",
    # [2] PL!N-pb1-002-R (Note)
    "(メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す。)": "(When the member leaves the stage, return the underlying Energy cards to the Energy Deck.)",
    # [2] PL!N-pb1-003-R
    "{{kidou.png|起動}}{{icon_energy.png|E}}{{icon_energy.png|E}}このカードを手札から控え室に置く：カードを1枚引き、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は{{icon_blade.png|ブレード}}を得る。この能力は、このカードが手札にある場合のみ起動できる。": "[Activate] (E)(E), Put this card from your hand into the waiting room: Draw 1 card, and 1 'Nijigasaki' member on your stage gets +1 Blade until the end of the live phase. This ability can only be used while this card is in your hand.",
    # [2] PL!N-pb1-004-R
    "{{jyouji.png|常時}}このターンにこのメンバーが移動していないかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as this member has not moved this turn, this member gets +2 Blades.",
    # [2] PL!N-pb1-004-R (Second ability)
    "{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを公開する。公開したカードがコスト9以下のメンバーカードの場合、公開したカードを手札に加え、このメンバーはポジションチェンジする。それ以外の場合、公開したカードを控え室に置く。": "[Live Start] Reveal the top card of your deck. If it is a Member card with Cost 9 or less, add it to your hand and Position Change this member. Otherwise, put the revealed card into the waiting room.",
    # [2] PL!N-pb1-005-R
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。": "[Auto] [Turn 1] When a Cost 10 member enters your stage, draw 1 card.",
    # [2] PL!N-pb1-006-R
    "{{kidou.png|起動}}このメンバーをウェイトにする：エネルギーを1枚アクティブにする。": "[Activate] Set this member to Waiting state: Activate 1 Energy.",
    # [2] PL!N-pb1-007-R
    "{{jyouji.png|常時}}自分のライブ中のライブカードの必要ハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がそれぞれ1以上含まれるかぎり、{{icon_all.png|ハート}}を得る。": "[Continuous] As long as your Live cards in progress require 1 or more of each [Heart 01], [Heart 02], [Heart 03], [Heart 04], [Heart 05], and [Heart 06], this member gets [Heart].",
    # [2] PL!N-pb1-008-R
    "{{jyouji.png|常時}}自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり、手札にあるこのメンバーカードのコストは2減る。": "[Continuous] As long as you have a 'Nijigasaki' member in Waiting state on your stage, the Cost of this member card in your hand is reduced by 2.",
    # [2] PL!N-pb1-008-R (Second ability)
    "{{toujyou.png|登場}}自分のステージにいるメンバー1人か、エネルギーを2枚アクティブにする。": "[On Play] Activate 1 member on your stage OR activate 2 Energy.",
    # [2] PL!N-pb1-009-R
    "{{live_start.png|ライブ開始時}}このターン、ブレードハートを持たないメンバーカードが自分のライブカード置き場から控え室に置かれている場合、カードを1枚引き、ライブ終了時まで、{{heart_03.png|heart03}}{{heart_05.png|heart05}}{{heart_06.png|heart06}}を得る。": "[Live Start] If a Member card without Blade Heart was put from your Live Area into the waiting room this turn, draw 1 card, and this member gets [Heart 03][Heart 05][Heart 06] until the end of the live phase.",
    # [2] PL!N-pb1-010-R
    "{{toujyou.png|登場}}以下から1つを選ぶ。": "[On Play] Choose 1 of the following:",
    # [2] PL!N-pb1-010-R (Option 1)
    "・エネルギーを1枚アクティブにする。": "- Activate 1 Energy.",
    # [2] PL!N-pb1-010-R (Option 2)
    "・自分の控え室にある『虹ヶ咲』のライブカードを2枚まで好きな順番でデッキの上に置く。": "- Put up to 2 'Nijigasaki' Live cards from your waiting room on top of your deck in any order.",
    # [2] PL!N-pb1-011-R
    "{{jyouji.png|常時}}このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る。": "[Continuous] This member gets +1 Blade for each Energy card under it.",
    # [2] PL!N-pb1-011-R (Second ability)
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。": "[Activate] [Turn 1] Put 1 Energy from your Energy Area under this member: Add 1 'Nijigasaki' Live card from your waiting room to your hand.",
    # [2] PL!N-pb1-012-R
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のステージにこのメンバー以外のコスト11のメンバーが登場したとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Auto] [Turn 1] When another Cost 11 member enters your stage, place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [2] PL!N-pb1-012-R (Second ability)
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『虹ヶ咲』のメンバーカードを1枚手札に加える。": "[Live Success] Add 1 'Nijigasaki' Member card revealed by your Yell to your hand.",
    # [2] PL!N-pb1-013-R
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「上原歩夢」のメンバーカードを1枚ステージに登場させる。": "[On Play] You may pay (E)(E): Play 1 'Ayumu Uehara' Member card with Cost 4 or less from your hand onto the stage.",
    # [2] PL!N-pb1-014-R
    "{{toujyou.png|登場}}「中須かすみ」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。": "[On Play] If this member entered via Baton Touch from 'Kasumi Nakasu', draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [2] PL!N-pb1-015-R
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「桜坂しずく」のメンバーカードを1枚ステージに登場させる。": "[On Play] You may pay (E)(E): Play 1 'Shizuku Osaka' Member card with Cost 4 or less from your hand onto the stage.",
    # [2] PL!N-pb1-016-R
    "{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「朝香果林」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 2 cards of your deck. You may reveal 1 'Karin Asaka' Member card from among them and add it to your hand. Put the rest into the waiting room.",
    # [2] PL!N-pb1-017-R
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「宮下愛」のメンバーカードを1枚ステージに登場させる。": "[On Play] You may pay (E)(E): Play 1 'Ai Miyashita' Member card with Cost 4 or less from your hand onto the stage.",
    # [2] PL!N-pb1-018-R
    "{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「近江彼方」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 2 cards of your deck. You may reveal 1 'Kanata Konoe' Member card from among them and add it to your hand. Put the rest into the waiting room.",
    # [2] PL!N-pb1-019-R
    "{{toujyou.png|登場}}「優木せつ菜」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。": "[On Play] If this member entered via Baton Touch from 'Setsuna Yuki', draw 2 cards, then put 2 cards from your hand into the waiting room.",
    # [2] PL!N-pb1-020-R
    "{{toujyou.png|登場}}「エマ・ヴェルデ」からバトンタッチして登場した場合、カードを2枚引き、手札を2枚控え室に置く。": "[On Play] If this member entered via Baton Touch from 'Emma Verde', draw 2 cards, then put 2 cards from your hand into the waiting room.",
    # [2] PL!N-pb1-021-R
    "{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「天王寺璃奈」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 2 cards of your deck. You may reveal 1 'Rina Tennoji' Member card from among them and add it to your hand. Put the rest into the waiting room.",
    # [2] PL!N-pb1-022-R
    "{{toujyou.png|登場}}「三船栞子」からバトンタッチして登場した場合、カードを2枚引き、手札を1枚控え室に置く。": "[On Play] If this member entered via Baton Touch from 'Shioriko Mifune', draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [2] PL!N-pb1-023-R
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「ミア・テイラー」のメンバーカードを1枚ステージに登場させる。": "[On Play] You may pay (E)(E): Play 1 'Mia Taylor' Member card with Cost 4 or less from your hand onto the stage.",
    # [2] PL!N-pb1-024-R
    "{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から「鐘嵐珠」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 2 cards of your deck. You may reveal 1 'Lanzhu Zhong' Member card from among them and add it to your hand. Put the rest into the waiting room.",
    # [2] PL!N-pb1-028-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを2枚見る。その中から1枚を手札に加え、残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 2 cards of your deck. Add 1 of them to your hand, and put the rest into the waiting room.",
    # [1] PL!-sd1-001-SD
    "{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。": "[On Play] If you have 2 or more cards in your Success Live Area, add 1 Live card from your waiting room to your hand.",
    # [1] PL!-sd1-001-SD (Second ability)
    "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。": "[Continuous] This member gets +1 Blade for each card in your Success Live Area.",
    # [1] PL!-sd1-003-SD
    "{{toujyou.png|登場}}自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える。": "[On Play] Add 1 'μ's' Member card with Cost 4 or less from your waiting room to your hand.",
    # [1] PL!-sd1-003-SD (Second ability)
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。": "[Live Start] You may put 1 card from your hand into the waiting room: Choose [Heart 01], [Heart 03], or [Heart 06]. This member gets the chosen Heart until the end of the live phase.",
    # [1] PL!-sd1-004-SD
    "{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『μ's』のライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 5 cards of your deck. You may reveal 1 'μ's' Live card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!-sd1-006-SD
    "{{toujyou.png|登場}}手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く。": "[On Play] You may reveal 1 Live card from your hand: Add 1 card from your Success Live Area to your hand. If you do, put the revealed card into your Success Live Area.",
    # [1] PL!-sd1-007-SD
    "{{toujyou.png|登場}}自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。": "[On Play] Put the top 5 cards of your deck into the waiting room. If there are any Live cards among them, draw 1 card.",
    # [1] PL!-sd1-008-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のデッキの上からカードを10枚控え室に置く。": "[Activate] [Turn 1] (E)(E): Put the top 10 cards of your deck into the waiting room.",
    # [1] PL!-sd1-009-SD
    "{{live_start.png|ライブ開始時}}自分の控え室に『μ's』のカードが25枚以上ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": "[Live Start] If you have 25 or more 'μ's' cards in your waiting room, this member gets \"[Continuous] Live Score +1\" until the end of the live phase.",
    # [1] PL!-sd1-022-SD
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。": "[Live Start] For each card in your Success Live Area, reduce the Hearts required to succeed this Live card by [Heart 00][Heart 00].",
    # [1] PL!-PR-003-PR
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_03.png|heart03}}を3以上含むライブカードを1枚手札に加える。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 Live card from your waiting room that requires 3 or more [Heart 03] to your hand.",
    # [1] PL!-PR-004-PR
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から必要ハートに{{heart_01.png|heart01}}を3以上含むライブカードを1枚手札に加える。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 Live card from your waiting room that requires 3 or more [Heart 01] to your hand.",
    # [1] PL!HS-PR-016-PR
    "{{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 2 cards with the same Unit Name from your hand into the waiting room: This member gets [Heart 04][Heart 04] and +2 Blades until the end of the live phase.",
    # [1] PL!HS-PR-017-PR
    "{{live_start.png|ライブ開始時}}手札の同じユニット名を持つカード2枚を控え室に置いてもよい：ライブ終了時まで、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 2 cards with the same Unit Name from your hand into the waiting room: This member gets [Heart 05][Heart 05] and +2 Blades until the end of the live phase.",
    # [1] PL!HS-PR-019-PR
    "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_04.png|heart04}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_04.png|heart04}}を得る。": "[On Play] Put the top 3 cards of your deck into the waiting room. If they are all Member cards with [Heart 04], this member gets [Heart 04] until the end of the live phase.",
    # [1] PL!HS-PR-021-PR
    "{{toujyou.png|登場}}自分のデッキの上からカードを3枚控え室に置く。それらがすべて{{heart_01.png|heart01}}を持つメンバーカードの場合、ライブ終了時まで、{{heart_01.png|heart01}}を得る。": "[On Play] Put the top 3 cards of your deck into the waiting room. If they are all Member cards with [Heart 01], this member gets [Heart 01] until the end of the live phase.",
    # [1] LL-PR-004-PR (Fun card)
    "{{live_start.png|ライブ開始時}}相手に何が好き？と聞く。": '[Live Start] Ask your opponent "What do you like?"',
    # [1] LL-PR-004-PR (Part 2)
    "回答がチョコミントかストロベリーフレイバーかクッキー＆クリームの場合、自分と相手は手札を1枚控え室に置く。": 'If the answer is "Choco Mint", "Strawberry Flavor", or "Cookies & Cream", both you and your opponent put 1 card from your hand into the waiting room.',
    # [1] LL-PR-004-PR (Part 3)
    "回答があなたの場合、自分と相手はカードを1枚引く。": 'If the answer is "You", both you and your opponent draw 1 card.',
    # [1] LL-PR-004-PR (Part 4)
    "回答がそれ以外の場合、ライブ終了時まで、自分と相手のステージにいるメンバーは{{icon_blade.png|ブレード}}を得る。": "If the answer is anything else, all members on both players' stages get +1 Blade until the end of the live phase.",
    # [1] LL-bp1-001-R＋
    "{{toujyou.png|登場}}自分の控え室からメンバーカードを1枚手札に加える。": "[On Play] Add 1 Member card from your waiting room to your hand.",
    # [1] LL-bp1-001-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札の「上原歩夢」と「澁谷かのん」と「日野下花帆」を、好きな組み合わせで合計3枚、控え室に置いてもよい：ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋３する。」を得る。": "[Live Start] You may put a total of 3 'Ayumu Uehara', 'Kanon Shibuya', and 'Kaho Hinoshita' cards in any combination from your hand into the waiting room: This member gets \"[Continuous] Live Score +3\" until the end of the live phase.",
    # [1] LL-bp1-001-R＋ (Note)
    "（手札のこのカードもこの効果で控え室に置ける。）": "(You can also put this card from your hand into the waiting room for this effect.)",
    # [1] PL!N-bp1-026-L
    "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、エールにより公開された自分のカードの中から、『虹ヶ咲』のカードを1枚手札に加える。": "[Live Success] If your total Live Score is higher than your opponent's, add 1 'Nijigasaki' card revealed by your Yell to your hand.",
    # [1] PL!N-bp1-026-L (Note)
    "(必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う。)": "(When checking Heart requirements, ALL Blades revealed by Yell are treated as Hearts of any color.)",
    # [1] PL!N-bp1-027-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバーが持つ{{heart_01.png|heart01}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_06.png|heart06}}のうち1色につき、このカードのスコアを＋１する。": "[Live Start] For each unique Heart color ([Heart 01], [Heart 02], [Heart 03], [Heart 04], [Heart 05], [Heart 06]) held by 'Nijigasaki' members on your stage, Live Score +1 for this card.",
    # [1] PL!N-bp1-027-L (Note)
    "(エールをすべて行った後、エールで出た{{icon_draw.png|ドロー}}1つにつき、カードを1枚引く。)": "(After performing all Yells, draw 1 card for each Draw icon revealing by Yell.)",
    # [1] PL!N-bp1-028-L
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分のステージに『虹ヶ咲』のメンバーがいる場合、このカードのスコアを＋１する。": "[Live Start] You may pay (E)(E): If you have a 'Nijigasaki' member on your stage, Live Score +1 for this card.",
    # [1] PL!N-bp1-029-L
    "{{live_start.png|ライブ開始時}}自分のライブ中のカードが3枚以上ある場合、このカードのスコアを＋２する。": "[Live Start] If you have 3 or more Live cards in progress, Live Score +2 for this card.",
    # [1] PL!SP-bp1-023-L
    "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高い場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Success] If your total Live Score is higher than your opponent's, place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!SP-bp1-023-L (Note)
    "(エールで出た{{icon_score.png|スコア}}1つにつき、成功したライブのスコアの合計に1を加算する。)": "(Add 1 to the total Score of the successful Live for each Score icon revealed by Yell.)",
    # [1] PL!SP-bp1-024-L
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる「澁谷かのん」1人は{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を、「唐可可」1人は{{heart_01.png|heart01}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] 1 'Kanon Shibuya' on your stage gets [Heart 05] and +1 Blade, and 1 'Keke Tang' on your stage gets [Heart 01] and +1 Blade until the end of the live phase.",
    # [1] PL!SP-bp1-024-L (Second ability)
    "{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」と「唐可可」がいる場合、カードを1枚引く。": "[Live Success] If you have both 'Kanon Shibuya' and 'Keke Tang' on your stage, draw 1 card.",
    # [1] PL!SP-bp1-026-L
    "{{live_start.png|ライブ開始時}}自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストは{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}になる。": "[Live Start] If you have 5 or more 'Liella!' members with different names across your stage and waiting room, the Cost to use this card becomes [Heart 02][Heart 02][Heart 03][Heart 03][Heart 06][Heart 06].",
    # [1] PL!SP-bp1-027-L
    "{{live_start.png|ライブ開始時}}自分のエネルギーが12枚以上ある場合、このカードのスコアを＋１する。": "[Live Start] If you have 12 or more Energy, Live Score +1 for this card.",
    # [1] PL!HS-bp1-021-L
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、『蓮ノ空』のライブカードを1枚手札に加える。": "[Live Success] Add 1 'Hasunosora' Live card revealed by your Yell to your hand.",
    # [1] PL!HS-bp1-022-L
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に『蓮ノ空』のメンバーカードが10枚以上ある場合、このカードのスコアを＋１する。": "[Live Success] If there are 10 or more 'Hasunosora' Member cards revealed by your Yell, Live Score +1 for this card.",
    # [1] PL!HS-bp1-023-L
    "{{live_success.png|ライブ成功時}}ライブの合計スコアが相手より高く、かつ自分のステージに『蓮ノ空』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Success] If your total Live Score is higher than your opponent's and you have a 'Hasunosora' member on your stage, place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!N-sd1-001-SD
    "{{toujyou.png|登場}}自分のデッキの上からカードを5枚見る。その中から『虹ヶ咲』のライブカードを1枚まで公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] Look at the top 5 cards of your deck. You may reveal up to 1 'Nijigasaki' Live card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!N-sd1-001-SD (Second ability)
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、自分のステージにいるほかの『虹ヶ咲』のメンバーは{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay (E): Other 'Nijigasaki' members on your stage get +1 Blade until the end of the live phase.",
    # [1] PL!N-sd1-004-SD
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 1 card from your hand into the waiting room: This member gets +2 Blades until the end of the live phase.",
    # [1] PL!N-sd1-005-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のメンバーカードを1枚手札に加える。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 'Nijigasaki' Member card from your waiting room to your hand.",
    # [1] PL!N-sd1-007-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 'Nijigasaki' Live card from your waiting room to your hand.",
    # [1] PL!N-sd1-009-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}手札を1枚控え室に置く：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。": "[Activate] [Turn 1] (E)(E), Put 1 card from your hand into the waiting room: Add 1 'Nijigasaki' Live card from your waiting room to your hand.",
    # [1] PL!N-sd1-010-SD
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_04.png|heart04}}を得る。": "[Live Start] You may pay (E)(E): This member gets [Heart 04] until the end of the live phase.",
    # [1] PL!N-sd1-028-SD
    "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードのスコアを＋１する。": "[Live Start] If the total number of Blades held by members on your stage is 10 or more, Live Score +1 for this card.",
    # [1] PL!SP-sd1-001-SD
    "{{toujyou.png|登場}}自分のエネルギー6枚につき、カードを1枚引く。": "[On Play] Draw 1 card for every 6 Energy you have.",
    # [1] PL!SP-sd1-002-SD
    "{{toujyou.png|登場}}手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい。": "[On Play] You may play 1 'Liella!' Member card with Cost 4 or less from your hand onto the stage.",
    # [1] PL!SP-sd1-002-SD (Note)
    "（この効果で既にメンバーがいるエリアにも登場できる。ただし、このターンにステージに登場したメンバーがいるエリアには登場できない。）": "(You can play into an occupied area with this effect. However, you cannot play into an area where a member has already entered this turn.)",
    # [1] PL!SP-sd1-003-SD
    "{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 2 cards from your hand into the waiting room: This member gets +5 Blades until the end of the live phase.",
    # [1] PL!SP-sd1-004-SD
    "{{toujyou.png|登場}}ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[On Play] This member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [1] PL!SP-sd1-005-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の控え室からライブカードを1枚手札に加える。": "[Activate] [Turn 1] (E)(E)(E): Add 1 Live card from your waiting room to your hand.",
    # [1] PL!SP-sd1-007-SD
    "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から『Liella!』のメンバーカードを1枚手札に加える。": "[On Play] You may pay (E)(E): Add 1 'Liella!' Member card from your waiting room to your hand.",
    # [1] PL!SP-sd1-009-SD
    "{{toujyou.png|登場}}{{icon_energy.png|E}}支払ってもよい：自分のエネルギーが9枚以上ある場合、自分のデッキの上からカードを5枚見る。その中から1枚を手札に加え、残りを控え室に置く。": "[On Play] You may pay (E): If you have 9 or more Energy, look at the top 5 cards of your deck. Add 1 of them to your hand, and put the rest into the waiting room.",
    # [1] PL!SP-sd1-011-SD
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Activate] [Turn 1] (E)(E): Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!SP-sd1-016-SD
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[On Play] You may put 1 card from your hand into the waiting room: Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!SP-sd1-026-SD
    "{{live_start.png|ライブ開始時}}自分のエネルギーが9枚以上ある場合、このカードのスコアを＋１する。": "[Live Start] If you have 9 or more Energy, Live Score +1 for this card.",
    # [1] PL!SP-pb1-001-P＋
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払わないかぎり、自分の手札を2枚控え室に置く。": "[Live Start] Unless you pay (E)(E), put 2 cards from your hand into the waiting room.",
    # [1] PL!SP-pb1-001-P＋ (Second ability)
    "{{live_success.png|ライブ成功時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブの合計スコアを＋１する。": "[Live Success] You may pay (E)(E)(E)(E)(E)(E): Live Score +1.",
    # [1] PL!SP-pb1-002-P＋
    "{{jyouji.png|常時}}自分のエネルギーが12枚以上ある場合、ライブの合計スコアを＋１する。": "[Continuous] If you have 12 or more Energy, Live Score +1.",
    # [1] PL!SP-pb1-005-P＋
    "{{toujyou.png|登場}}自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[On Play] Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!SP-pb1-006-P＋
    "{{jidou.png|自動}}このメンバーが登場か、エリアを移動するたび、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Auto] Whenever this member enters the stage or moves to a different area, this member gets +2 Blades until the end of the live phase.",
    # [1] PL!SP-pb1-006-P＋ (Note)
    "(対戦相手のカードの効果でも発動する。)": "(Also activates by your opponent's card effects.)",
    # [1] PL!SP-pb1-007-P＋
    "{{live_start.png|ライブ開始時}}エネルギーを2枚アクティブにする。": "[Live Start] Activate 2 Energy.",
    # [1] PL!SP-pb1-008-P＋
    "{{toujyou.png|登場}}カードを1枚引く。その後、登場したエリアとは別の自分のエリア1つを選ぶ。このメンバーをそのエリアに移動する。選んだエリアにメンバーがいる場合、そのメンバーは、このメンバーがいたエリアに移動させる。": "[On Play] Draw 1 card. Then, choose 1 of your areas other than the one this member entered. Move this member to that area. If there is a member in the chosen area, move that member to the area this member was in.",
    # [1] PL!SP-pb1-009-P＋
    "{{toujyou.png|登場}}自分のステージにほかの『5yncri5e!』のメンバーがいる場合、カードを1枚引く。": "[On Play] If you have another '5yncri5e!' member on your stage, draw 1 card.",
    # [1] PL!SP-pb1-010-P＋
    "{{jyouji.png|常時}}自分のエネルギーが10枚以上ある場合、ステージにいるこのメンバーのコストを＋４する。": "[Continuous] If you have 10 or more Energy, this member's Cost on stage is increased by 4.",
    # [1] PL!SP-pb1-011-P＋
    "{{toujyou.png|登場}}「鬼塚冬毬」以外の『Liella!』のメンバー1人をステージから控え室に置いてもよい：自分の控え室から、これにより控え室に置いたメンバーカードを1枚、そのメンバーがいたエリアに登場させる。": "[On Play] You may put 1 'Liella!' member other than 'Tomari Onitsuka' from your stage into the waiting room: Play 1 copy of the member card put into the waiting room by this effect from your waiting room into the area that member was in.",
    # [1] PL!SP-pb1-015-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『CatChu!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 5 cards of your deck. You may reveal 1 'CatChu!' card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!SP-pb1-016-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『KALEIDOSCORE』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 5 cards of your deck. You may reveal 1 'KALEIDOSCORE' card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!SP-pb1-017-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中から『5yncri5e!』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 5 cards of your deck. You may reveal 1 '5yncri5e!' card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!SP-pb1-020-N
    "{{jidou.png|自動}}このメンバーがエリアを移動するたび、カードを1枚引く。": "[Auto] Whenever this member moves to a different area, draw 1 card.",
    # [1] PL!SP-pb1-023-L
    "{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『CatChu!』のメンバーが2人以上いる場合、エネルギーを6枚までアクティブにする。その後、自分のエネルギーがすべてアクティブ状態の場合、このカードのスコアを＋１する。": "[Live Start] If you have 2 or more 'CatChu!' members with different names on your stage, activate up to 6 Energy. Then, if all your Energy is in Active state, Live Score +1 for this card.",
    # [1] PL!SP-pb1-024-L
    "{{live_start.png|ライブ開始時}}自分のステージに名前の異なる『KALEIDOSCORE』のメンバーが2人以上いる場合、このカードのスコアを＋１する。": "[Live Start] If you have 2 or more 'KALEIDOSCORE' members with different names on your stage, Live Score +1 for this card.",
    # [1] PL!SP-pb1-025-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる、このターン中に登場、またはエリアを移動した『5yncri5e!』のメンバー1人につき、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。": "[Live Start] Reduce the Hearts required to succeed this card by [Heart 00] for each '5yncri5e!' member on your stage that entered or moved this turn.",
    # [1] PL!S-bp2-021-L
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く。": "[Live Success] Put up to 1 Live card revealed by your Yell on the bottom of your deck.",
    # [1] PL!S-bp2-022-L
    "{{live_success.png|ライブ成功時}}このターン、自分のデッキがリフレッシュしていた場合、このカードのスコアを＋２する。": "[Live Success] If your deck shuffled (refreshed) this turn, Live Score +2 for this card.",
    # [1] PL!S-bp2-023-L
    "{{live_start.png|ライブ開始時}}自分のライブカード置き場に「MY舞☆TONIGHT」以外の『Aqours』のライブカードがある場合、ライブ終了時まで、自分のステージのメンバーは{{icon_blade.png|ブレード}}を得る。": "[Live Start] If you have an 'Aqours' Live card other than 'MY Mai☆TONIGHT' in your Live Area, your members on stage get +1 Blade until the end of the live phase.",
    # [1] PL!S-bp2-024-L
    "{{jyouji.png|常時}}このカードは成功ライブカード置き場に置くことができない。": "[Continuous] This card cannot be put into the Success Live Area.",
    # [1] PL!S-bp2-025-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] If you have 2 or more cards in your Success Live Area, 1 member on your stage gets +2 Blades until the end of the live phase.",
    # [1] PL!SP-bp2-015-N
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_06.png|heart06}}を得る。": "[Auto] [Turn 1] When you reveal no cards with Blade Heart via Yell, this member gets [Heart 06] until the end of the live phase.",
    # [1] PL!SP-bp2-020-N
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_02.png|heart02}}を得る。": "[Auto] [Turn 1] When you reveal no cards with Blade Heart via Yell, this member gets [Heart 02] until the end of the live phase.",
    # [1] PL!SP-bp2-021-N
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}エールにより公開された自分のカードの中にブレードハートを持つカードがないとき、ライブ終了時まで、{{heart_03.png|heart03}}を得る。": "[Auto] [Turn 1] When you reveal no cards with Blade Heart via Yell, this member gets [Heart 03] until the end of the live phase.",
    # [1] PL!SP-bp2-023-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカード枚数が相手より少ない場合、このカードのスコアを＋１する。": "[Live Start] If you have fewer cards in your Success Live Area than your opponent, Live Score +1 for this card.",
    # [1] PL!SP-bp2-024-L
    "{{live_success.png|ライブ成功時}}自分の手札の枚数が相手より多い場合、このカードのスコアを＋１する。": "[Live Success] If you have more cards in your hand than your opponent, Live Score +1 for this card.",
    # [1] PL!SP-bp2-025-L
    "{{live_success.png|ライブ成功時}}自分のステージに「澁谷かのん」、「ウィーン・マルガレーテ」、「鬼塚冬毬」のうち、名前の異なるメンバーが2人以上いる場合、エールにより公開された自分のカードの中から、カードを1枚手札に加える。": "[Live Success] If you have 2 or more members with different names among 'Kanon Shibuya', 'Wien Margarete', and 'Tomari Onitsuka' on your stage, add 1 card revealed by your Yell to your hand.",
    # [1] PL!HS-bp2-012-N
    "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[Auto] When this member is put from the stage into the waiting room, look at the top 5 cards of your deck. You may reveal 1 Member card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!HS-bp2-013-N
    "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、自分のデッキの上からカードを5枚見る。その中からライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[Auto] When this member is put from the stage into the waiting room, look at the top 5 cards of your deck. You may reveal 1 Live card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!HS-bp2-014-N
    "{{toujyou.png|登場}}カードを1枚引く。ライブ終了時まで、自分はライブできない。": "[On Play] Draw 1 card. You cannot perform a Live until the end of the live phase.",
    # [1] PL!HS-bp2-015-N
    "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、カードを2枚引き、手札を1枚控え室に置く。": "[Auto] When this member is put from the stage into the waiting room, draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [1] PL!HS-bp2-016-N
    "{{toujyou.png|登場}}自分のデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。": "[On Play] Look at the top 2 cards of your deck. Put any number of them back on top of your deck in any order, and put the rest into the waiting room.",
    # [1] PL!HS-bp2-017-N
    "{{toujyou.png|登場}}自分の控え室にカードが10枚以上ある場合、カードを1枚引く。": "[On Play] If you have 10 or more cards in your waiting room, draw 1 card.",
    # [1] PL!HS-bp2-018-N
    "{{toujyou.png|登場}}自分のメインフェイズの場合、{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室からライブカードを1枚、表向きでライブカード置き場に置く。次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。": "[On Play] If it is your Main Phase, you may pay (E)(E): Put 1 Live card from your waiting room face up into your Live Area. The maximum number of Live cards you can set during your next Live Card Set Phase is reduced by 1.",
    # [1] PL!HS-bp2-019-L
    "{{live_start.png|ライブ開始時}}自分のステージに『蓮ノ空』のメンバーがいる場合、このカードを成功させるための必要ハートは、{{heart_01.png|heart01}}{{heart_01.png|heart01}}{{heart_00.png|heart0}}か、{{heart_04.png|heart04}}{{heart_04.png|heart04}}{{heart_00.png|heart0}}か、{{heart_05.png|heart05}}{{heart_05.png|heart05}}{{heart_00.png|heart0}}のうち、選んだ1つにしてもよい。": "[Live Start] If you have a 'Hasunosora' member on your stage, you may choose one of the following as the Heart requirement to succeed this card: [Heart 01][Heart 01][Heart 00], [Heart 04][Heart 04][Heart 00], or [Heart 05][Heart 05][Heart 00].",
    # [1] PL!HS-bp2-020-L
    "{{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。": "[Continuous] This card is treated as 'Cerise Bouquet', 'DOLLCHESTRA', and 'Mira-Cra Park!' in all areas.",
    # [1] PL!HS-bp2-020-L (Second ability)
    "{{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。": "[Live Start] Live Score +2 for this card for each 'Hasunosora' member with a different name on your stage.",
    # [1] PL!HS-bp2-021-L
    "{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_04.png|heart04}}減らす。": "[Live Start] If you have 2 or more 'Hasunosora' members on your stage that entered via Baton Touch this turn, reduce the Hearts required to succeed this card by [Heart 04].",
    # [1] PL!HS-bp2-022-L
    "{{live_start.png|ライブ開始時}}自分の控え室に『スリーズブーケ』のライブカードが3枚以上ある場合、このカードのスコアを＋１する。": "[Live Start] If you have 3 or more 'Cerise Bouquet' Live cards in your waiting room, Live Score +1 for this card.",
    # [1] PL!HS-bp2-023-L
    "{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_05.png|heart05}}減らす。": "[Live Start] If you have 2 or more 'Hasunosora' members on your stage that entered via Baton Touch this turn, reduce the Hearts required to succeed this card by [Heart 05].",
    # [1] PL!HS-bp2-024-L
    "{{live_start.png|ライブ開始時}}自分のステージに「徒町小鈴」が登場しており、かつ「徒町小鈴」よりコストの大きい「村野さやか」が登場している場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。": "[Live Start] If you have 'Kosuzu Kachi' on your stage, and 'Sayaka Murano' with a higher Cost than 'Kosuzu Kachi' is also on your stage, reduce the Hearts required to succeed this card by [Heart 00][Heart 00][Heart 00].",
    # [1] PL!HS-bp2-025-L
    "{{live_start.png|ライブ開始時}}自分のステージに、このターン中にバトンタッチして登場した『蓮ノ空』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_01.png|heart01}}減らす。": "[Live Start] If you have 2 or more 'Hasunosora' members on your stage that entered via Baton Touch this turn, reduce the Hearts required to succeed this card by [Heart 01].",
    # [1] PL!HS-bp2-026-L
    "{{live_start.png|ライブ開始時}}自分のステージの右サイドエリアに「大沢瑠璃乃」が、左サイドエリアに「安養寺姫芽」が、センターエリアに「藤島慈」がそれぞれ登場している場合、このカードのスコアを＋２する。": "[Live Start] If you have 'Rurino Osawa' in the Right Side Area, 'Hime Anyoji' in the Left Side Area, and 'Megumi Fujishima' in the Center Area, Live Score +2 for this card.",
    # [1] LL-bp2-001-R＋
    "{{jyouji.png|常時}}手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。": "[Continuous] The Cost of this member card in your hand is reduced by 1 for each other card in your hand.",
    # [1] LL-bp2-001-R＋ (Second ability)
    "{{jyouji.png|常時}}このメンバーはバトンタッチで控え室に置けない。": "[Continuous] This member cannot be put into the waiting room by Baton Touch.",
    # [1] LL-bp2-001-R＋ (Third ability)
    "{{live_start.png|ライブ開始時}}手札の「渡辺曜」と「鬼塚夏美」と「大沢瑠璃乃」を、好きな枚数控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いた枚数1枚につき、{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put any number of 'You Watanabe', 'Natsumi Onitsuka', and 'Rurino Osawa' cards from your hand into the waiting room: This member gets +1 Blade for each card put into the waiting room by this effect until the end of the live phase.",
    # [1] PL!S-pb1-001-P＋
    "{{toujyou.png|登場}}相手の手札の枚数が自分より2枚以上多い場合、自分の控え室からライブカードを1枚手札に加える。": "[On Play] If your opponent has 2 or more cards in hand than you, add 1 Live card from your waiting room to your hand.",
    # [1] PL!S-pb1-002-P＋
    "{{toujyou.png|登場}}相手は手札からライブカードを1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[On Play] Your opponent may put 1 Live card from their hand into the waiting room. If they do not, this member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [1] PL!S-pb1-003-P＋
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。": "[Live Start] You may pay (E)(E): All base Hearts of this member become [Heart 04] until the end of the live phase.",
    # [1] PL!S-pb1-003-P＋ (Second ability)
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚手札に加える。": "[Live Success] Add 1 Live card revealed by your Yell to your hand.",
    # [1] PL!S-pb1-005-P＋
    "{{jyouji.png|常時}}相手のエネルギーが自分より多い場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] If your opponent has more Energy than you, this member gets +3 Blades.",
    # [1] PL!S-pb1-006-P＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札のライブカードを1枚公開する：相手は手札を1枚控え室に置いてもよい。そうしなかった場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Activate] [Turn 1] Reveal 1 Live card from your hand: Your opponent may put 1 card from their hand into the waiting room. If they do not, this member gets +4 Blades until the end of the live phase.",
    # [1] PL!S-pb1-007-P＋
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中にライブカードが1枚以上あるとき、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Success] When there is 1 or more Live cards revealed by your Yell, place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!S-pb1-008-P＋
    "{{live_start.png|ライブ開始時}}自分か相手を選ぶ。自分は、そのプレイヤーのデッキの上からカードを2枚見る。その中から好きな枚数を好きな順番でデッキの上に置き、残りを控え室に置く。": "[Live Start] Choose yourself or your opponent. Look at the top 2 cards of that player's deck. Put any number of them back on top of the deck in any order, and put the rest into the waiting room.",
    # [1] PL!S-pb1-009-P＋
    "{{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] If there are a total of 3 or more cards in both players' Success Live Areas, this member gets +3 Blades.",
    # [1] PL!S-pb1-013-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートに{{heart_04.png|heart04}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 4 cards of your deck. You may reveal 1 Member card with 2 or more [Heart 04] or 1 Live card requiring 2 or more [Heart 04] from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!S-pb1-014-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_02.png|heart02}}を2個以上持つメンバーカードか、必要ハートに{{heart_02.png|heart02}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 4 cards of your deck. You may reveal 1 Member card with 2 or more [Heart 02] or 1 Live card requiring 2 or more [Heart 02] from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!S-pb1-015-N
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_05.png|heart05}}を2個以上持つメンバーカードか、必要ハートに{{heart_05.png|heart05}}を2以上含むライブカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 4 cards of your deck. You may reveal 1 Member card with 2 or more [Heart 05] or 1 Live card requiring 2 or more [Heart 05] from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!S-pb1-019-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_02.png|heart02}}が合計6個以上ある場合、このカードの{{live_success.png|ライブ成功時}}能力を無効にする。{{live_success.png|ライブ成功時}}相手は、エネルギーデッキからエネルギーカードを1枚ウェイト状態で置く。": "[Live Start] If 'Aqours' members on your stage have a total of 6 or more [Heart 02], negate this card's [Live Success] ability. [Live Success] Your opponent places 1 Energy card from their Energy Deck into their Energy Area in Waiting state.",
    # [1] PL!S-pb1-020-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_04.png|heart04}}が合計10個以上ある場合、このカードのスコアを＋２する。": "[Live Start] If 'Aqours' members on your stage have a total of 10 or more [Heart 04], Live Score +2 for this card.",
    # [1] PL!S-pb1-021-L
    "{{live_success.png|ライブ成功時}}自分のステージにいる『Aqours』のメンバーが持つハートに、{{heart_05.png|heart05}}が合計4個以上あり、このターン、相手が余剰のハートを持たずにライブを成功させていた場合、このカードのスコアを＋２する。": "[Live Success] If 'Aqours' members on your stage have a total of 4 or more [Heart 05], and your opponent succeeded a Live without excess Hearts this turn, Live Score +2 for this card.",
    # [1] PL!S-pb1-022-L＋
    "{{live_success.png|ライブ成功時}}このターン、ライブに勝利するプレイヤーを決定するとき、自分と相手のライブの合計スコアが同じ場合、ライブ終了時まで、自分と相手は成功ライブカード置き場にカードを置くことができない。": "[Live Success] When determining the winner of the Live this turn, if the total Live Score of you and your opponent is the same, neither player can put cards into their Success Live Area until the end of the live phase.",
    # [1] PL!S-pb1-024-L
    "{{live_success.png|ライブ成功時}}カードを2枚引き、手札を2枚控え室に置く。": "[Live Success] Draw 2 cards, then put 2 cards from your hand into the waiting room.",
    # [1] PL!-bp3-009-R＋
    "{{toujyou.png|登場}}自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く。": "[On Play] If you have a member with Cost 13 or more on your stage, draw 1 card.",
    # [1] PL!-bp3-009-R＋ (Second ability)
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバーをウェイトにする：{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、選んだハートを1つ得る。": "[Activate] [Turn 1] Set this member to Waiting state: Choose [Heart 01], [Heart 03], or [Heart 06]. This member gets the chosen Heart until the end of the live phase.",
    # [1] PL!-bp3-019-L
    "{{live_start.png|ライブ開始時}}自分のライブ中の『μ's』のカードが2枚以上ある場合、このカードのスコアを＋１する。": "[Live Start] If you have 2 or more 'μ's' Live cards in progress, Live Score +1 for this card.",
    # [1] PL!-bp3-022-L
    "{{live_start.png|ライブ開始時}}自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する。それらの中にあるライブカード1枚につき、このカードのスコアを＋１する。その後、これにより公開したカードを控え室に置く。": "[Live Start] Reveal 1 card from the top of your deck for each member on your and your opponent's stage. Live Score +1 for this card for each Live card found among them. Then, put the revealed cards into the waiting room.",
    # [1] PL!-bp3-023-L
    "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。": "[Live Start] If the total number of Blades held by members on your stage is 10 or more, reduce the Hearts required to succeed this card by [Heart 00][Heart 00].",
    # [1] PL!-bp3-024-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードがある場合、{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、選んだハートを1つ得る。": "[Live Start] If you have cards in your Success Live Area, choose [Heart 01], [Heart 03], or [Heart 06]. 1 'μ's' member on your stage gets the chosen Heart until the end of the live phase.",
    # [1] PL!-bp3-024-L (Second ability)
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にカードが2枚以上ある場合、このカードのスコアを＋１する。": "[Live Start] If you have 2 or more cards in your Success Live Area, Live Score +1 for this card.",
    # [1] PL!-bp3-025-L
    "{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートを持たない場合、このカードのスコアを＋１する。": "[Live Success] If you have no excess Hearts this turn, Live Score +1 for this card.",
    # [1] PL!-bp3-026-L
    "{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 2 cards from your hand into the waiting room: 1 member on your stage gets +3 Blades until the end of the live phase.",
    # [1] PL!-bp3-026-L (Second ability)
    "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが持つハートの総数が、相手のステージにいるメンバーが持つハートの総数より多い場合、このカードのスコアを＋１する。": "[Live Success] If the total number of Hearts held by members on your stage is greater than the total number of Hearts held by members on your opponent's stage, Live Score +1 for this card.",
    # [1] PL!S-bp3-003-R＋
    "{{toujyou.png|登場}}手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。": "[On Play] You may put 1 Live card from your hand into the waiting room: Draw 3 cards.",
    # [1] PL!S-bp3-003-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put up to 2 cards from your hand into the waiting room: This member gets +2 Blades for each card put into the waiting room by this effect until the end of the live phase.",
    # [1] PL!S-bp3-016-N
    "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、ステージにいるこのメンバーのコストを＋１する。": "[Continuous] This member's Cost on stage is increased by 1 for each card in your Success Live Area.",
    # [1] PL!S-bp3-019-L
    "{{live_success.png|ライブ成功時}}このターン、エールにより公開された自分のカードの中にブレードハートを持たないカードが0枚の場合か、または自分が余剰ハートを2つ以上持っている場合、このカードのスコアは４になる。": "[Live Success] If 0 cards revealed by your Yell this turn have no Blade Heart, OR if you have 2 or more excess Hearts, the Score of this card becomes 4.",
    # [1] PL!S-bp3-020-L
    "{{jidou.png|自動}}［ターン1回］エールにより自分のカードを1枚以上公開したとき、それらのカードの中にブレードハートを持つカードが2枚以下の場合、それらのカードをすべて控え室に置いてもよい。そのエールで得たブレードハートを失い、もう一度エールを行う。": "[Auto] [Turn 1] When you reveal 1 or more cards via Yell, if 2 or fewer of them have Blade Heart, you may put all of them into the waiting room. Lose the Blade Heart gained from that Yell, and perform Yell again.",
    # [1] PL!S-bp3-021-L
    "{{live_start.png|ライブ開始時}}自分の控え室にあるメンバーカード1枚をデッキの一番上に置いてもよい。そうした場合、ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 1 Member card from your waiting room on top of your deck. If you do, 1 member on your stage gets +1 Blade until the end of the live phase.",
    # [1] PL!S-bp3-024-L
    "{{live_start.png|ライブ開始時}}自分のステージのセンターエリアにコスト9以上の『Aqours』のメンバーがいる場合、以下から1つを選ぶ。": "[Live Start] If you have an 'Aqours' member with Cost 9 or more in your Center Area, choose 1 of the following:",
    # [1] PL!S-bp3-024-L (Options)
    "・ライブ終了時まで、自分のステージにいるメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "- 1 member on your stage gets +2 Blades until the end of the live phase.",
    "・相手のステージにいるコスト4以下のメンバー1人をウェイトにする。": "- Set 1 member with Cost 4 or less on your opponent's stage to Waiting state.",
    # [1] PL!S-bp3-025-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『Aqours』のメンバー1人を選ぶ。そのメンバーが持つ{{icon_blade.png|ブレード}}が6つ以上の場合、このカードのスコアを＋１する。": "[Live Start] Choose 1 'Aqours' member on your stage. If that member has 6 or more Blades, Live Score +1 for this card.",
    # [1] PL!N-bp3-005-R＋
    "{{jidou.png|自動}}このターン、自分のステージにメンバーが3回登場したとき、手札が5枚になるまでカードを引く。": "[Auto] When a member enters your stage for the 3rd time this turn, draw cards until you have 5 cards in your hand.",
    # [1] PL!N-bp3-005-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}このターン、自分のステージにメンバーが2回以上登場している場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[Live Start] If members have entered your stage 2 or more times this turn, this member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [1] PL!N-bp3-008-R＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}このメンバー以外の『虹ヶ咲』のメンバー1人をウェイトにする：カードを1枚引く。": "[Activate] [Turn 1] Set 1 'Nijigasaki' member other than this member to Waiting state: Draw 1 card.",
    # [1] PL!N-bp3-008-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}手札を2枚控え室に置いてもよい：自分のステージにいるこのメンバー以外のウェイト状態のメンバー1人をアクティブにする。そうした場合、ライブ終了時まで、これによりアクティブにしたメンバーと、このメンバーは、それぞれ{{heart_04.png|heart04}}を得る。": "[Live Start] You may put 2 cards from your hand into the waiting room: Activate 1 Waiting state member on your stage other than this member. If you do, that member and this member both get [Heart 04] until the end of the live phase.",
    # [1] PL!N-bp3-013-N
    "{{toujyou.png|登場}}自分のエネルギー置き場にあるエネルギー1枚をこのメンバーの下に置いてもよい。そうした場合、カードを2枚引く。（メンバーの下に置かれているエネルギーカードではコストを支払えない。メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く。）": "[On Play] You may put 1 Energy from your Energy Area under this member. If you do, draw 2 cards. (Energy cards under members cannot be used to pay costs. When the member leaves the stage, put the underlying Energy cards into the Energy Deck.)",
    # [1] PL!N-bp3-014-N
    "{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_04.png|heart04}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。": "[Live Start] Choose [Heart 01], [Heart 03], or [Heart 04]. All base Hearts of this member become the chosen Heart until the end of the live phase.",
    # [1] PL!N-bp3-015-N
    "{{live_start.png|ライブ開始時}}{{heart_02.png|heart02}}か{{heart_05.png|heart05}}か{{heart_06.png|heart06}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。": "[Live Start] Choose [Heart 02], [Heart 05], or [Heart 06]. All base Hearts of this member become the chosen Heart until the end of the live phase.",
    # [1] PL!N-bp3-023-N
    "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）": "[On Play] / [Live Start] You may set this member to Waiting state: Set 1 member with Cost 4 or less on your opponent's stage to Waiting state. (Blades held by Waiting state members do not increase the number of cards revealed by Yell.)",
    # [1] PL!N-bp3-025-L
    "{{live_start.png|ライブ開始時}}自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい。そうした場合、ライブ終了時まで、そのメンバーは、これによって置いたエネルギーカード1枚につき、［赤ハート］［赤ハート］［赤ハート］を得る。": "[Live Start] You may return any number of Energy cards from under 1 member on your stage to the Energy Deck. If you do, that member gets [Heart 01][Heart 01][Heart 01] for each Energy card returned this way until the end of the live phase.",
    # [1] PL!N-bp3-026-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にスコアが１か５のカードがある場合、このカードのスコアを＋１する。それらが両方ある場合、代わりにスコアを＋２する。": "[Live Start] If you have a card with Score 1 or 5 in your Success Live Area, Live Score +1 for this card. If you have both, Live Score +2 instead.",
    # [1] PL!N-bp3-027-L
    "{{live_success.png|ライブ成功時}}このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており、かつ自分のステージに『虹ヶ咲』のメンバーがいる場合、自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "[Live Success] If you have 1 or more excess [Heart 04] this turn and a 'Nijigasaki' member on your stage, place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!N-bp3-028-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『虹ヶ咲』のメンバー1人につき、自分のデッキの上からカードを1枚見る。その中から1枚までをデッキの上に置き、残りを控え室に置く。その後、自分のデッキの一番上のカードを1枚公開する。これによりライブカードを公開した場合、このカードのスコアを＋１する。": "[Live Start] Look at 1 card from the top of your deck for each 'Nijigasaki' member on your stage. Put up to 1 of them back on top of the deck, and put the rest into the waiting room. Then, reveal the top card of your deck. If a Live card is revealed, Live Score +1 for this card.",
    # [1] PL!N-bp3-030-L
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に{{icon_b_all.png|ALLブレード}}を持つカードが1枚以上ある場合、このカードのスコアを＋１する。": "[Live Success] If 1 or more cards revealed by your Yell have ALL Blades, Live Score +1 for this card.",
    # [1] PL!N-bp3-031-L
    "{{live_success.png|ライブ成功時}}自分のステージにいるウェイト状態のメンバー1人につき、このカードのスコアを＋１する。": "[Live Success] Live Score +1 for this card for each Waiting state member on your stage.",
    # [1] LL-bp3-001-R＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}自分の控え室にある「園田海未」と「津島善子」と「天王寺璃奈」を、合計6枚をシャッフルしてデッキの一番下に置く：エネルギーを6枚までアクティブにする。": "[Activate] [Turn 1] Shuffle a total of 6 'Umi Sonoda', 'Yoshiko Tsushima', and 'Rina Tennoji' cards from your waiting room into the bottom of your deck: Activate up to 6 Energy.",
    # [1] LL-bp3-001-R＋ (Second ability)
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay (E)(E)(E)(E)(E)(E): This member gets +3 Blades until the end of the live phase.",
    # [1] PL!-pb1-001-P＋
    "{{kidou.png|起動}}{{center.png|センター}}{{turn1.png|ターン1回}}このメンバーをウェイトにし、手札を1枚控え室に置く：ライブカードかコスト10以上のメンバーカードのどちらか1つを選ぶ。選んだカードが公開されるまで、自分のデッキの一番上からカードを１枚ずつ公開する。そのカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く。": "[Activate] [Center] [Turn 1] Set this member to Waiting state and put 1 card from your hand into the waiting room: Choose either 'Live card' or 'Member card with Cost 10 or more'. Reveal cards from the top of your deck one by one until the chosen card type is revealed. Add that card to your hand, and put all other revealed cards into the waiting room.",
    # [1] PL!-pb1-002-P＋
    "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：自分のステージにいるメンバーが『BiBi』のみの場合、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。": "[On Play] / [Live Start] You may set this member to Waiting state: If you have only 'BiBi' members on your stage, set 1 member on your opponent's stage with 3 or fewer base Blades to Waiting state.",
    # [1] PL!-pb1-002-P＋ (Second ability)
    "{{jyouji.png|常時}}相手のステージにいるウェイト状態のメンバー1人につき、{{heart_06.png|heart06}}を得る。": "[Continuous] This member gets [Heart 06] for each Waiting state member on your opponent's stage.",
    # [1] PL!-pb1-003-P＋
    "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分のステージにいる『Printemps』のメンバー1人につき、エネルギーを1枚アクティブにする。": "[On Play] You may set this member to Waiting state: Activate 1 Energy for each 'Printemps' member on your stage.",
    # [1] PL!-pb1-004-P＋
    "{{toujyou.png|登場}}{{center.png|センター}}自分の成功ライブカード置き場に{{icon_score.png|スコア}}を持つ『μ's』のカードが1枚ある場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。2枚以上ある場合、代わりに「{{jyouji.png|常時}}ライブの合計スコアを＋２する。」を得る。（この能力はセンターエリアに登場した場合のみ発動する。）": '[On Play] [Center] If you have 1 \'μ\'s\' card with Score icon in your Success Live Area, this member gets "[Continuous] Live Score +1" until the end of the live phase. If you have 2 or more, get "[Continuous] Live Score +2" instead. (Activates only when entering the Center Area.)',
    # [1] PL!-pb1-005-P＋
    "{{toujyou.png|登場}}自分の成功ライブカード置き場にカードがある場合、カードを1枚引く。": "[On Play] If you have cards in your Success Live Area, draw 1 card.",
    # [1] PL!-pb1-006-P＋
    "{{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。": "[On Play] Put up to 1 'μ's' Live card from your waiting room on top of your deck. Then, if there is a Waiting state member on your opponent's stage, draw 1 card.",
    # [1] PL!-pb1-007-P＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を3枚控え室に置く：自分のステージにほかの『lilywhite』のメンバーがいる場合、自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力を起動するためのコストは、自分の成功ライブカード置き場にあるカード1枚につき、控え室に置く手札の数が1枚減る。": "[Activate] [Turn 1] Put 3 cards from your hand into the waiting room: If you have another 'lilywhite' member on your stage, add 1 'μ's' Live card from your waiting room to your hand. The cost to activate this ability is reduced by 1 card for each card in your Success Live Area.",
    # [1] PL!-pb1-008-P＋
    "{{toujyou.png|登場}}メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く。": "[On Play] You may set up to 3 members to Waiting state: Draw 1 card for each member set to Waiting state by this effect.",
    # [1] PL!-pb1-009-P＋
    "{{toujyou.png|登場}}相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が1つ以下のメンバー1人をウェイトにする。": "[On Play] Set 1 member on your opponent's stage with 1 or fewer base Blades to Waiting state.",
    # [1] PL!-pb1-009-P＋ (Second ability)
    "{{toujyou.png|登場}}このターン、自分と相手のステージにいるメンバーは、効果によってはアクティブにならない。": "[On Play] This turn, members on both your and your opponent's stages cannot be activated by card effects.",
    # [1] PL!-pb1-010-P＋
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるほかのメンバーは{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may put 1 card from your hand into the waiting room: Other members on your stage get +1 Blade until the end of the live phase.",
    # [1] PL!-pb1-011-P＋
    "{{toujyou.png|登場}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、相手のステージにいるコスト4以下のメンバー1人をウェイトにする。": "[On Play] If you have 2 or more 'BiBi' members with different names on your stage, set 1 member with Cost 4 or less on your opponent's stage to Waiting state.",
    # [1] PL!-pb1-012-P＋
    "{{toujyou.png|登場}}自分のステージにいる『Printemps』のメンバーを1人までアクティブにする。": "[On Play] Activate up to 1 'Printemps' member on your stage.",
    # [1] PL!-pb1-013-P＋
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}{{icon_energy.png|E}}{{icon_energy.png|E}}：自分の手札を、相手は見ないで1枚選び公開する。これにより公開されたカードがライブカードの場合、ライブ終了時まで、このメンバーは「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。": '[Activate] [Turn 1] (E)(E): Your opponent chooses 1 card from your hand without looking and reveals it. If the revealed card is a Live card, this member gets "[Continuous] Live Score +1" until the end of the live phase.',
    # [1] PL!-pb1-014-P＋
    "{{jyouji.png|常時}}自分の成功ライブカード置き場に『lilywhite』のカードがある場合、手札にあるこのメンバーカードのコストは2減る。": "[Continuous] If you have a 'lilywhite' card in your Success Live Area, the Cost of this member card in your hand is reduced by 2.",
    # [1] PL!-pb1-015-P＋
    "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}{{center.png|センター}}『BiBi』のメンバー1人をウェイトにしてもよい：相手は、自身のステージにいるアクティブ状態のメンバー1人をウェイトにする。（この能力はセンターエリアにいる場合のみ発動する。）": "[On Play] / [Live Start] [Center] You may set 1 'BiBi' member to Waiting state: Your opponent sets 1 of their Active state members to Waiting state. (Activates only when in the Center Area.)",
    # [1] PL!-pb1-015-P＋ (Second ability)
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき、カードを1枚引く。": "[Auto] [Turn 1] When an opponent's Active state member with Cost 4 or less becomes Waiting state due to your card effect, draw 1 card.",
    # [1] PL!-pb1-016-P＋
    "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中から『lilywhite』のカードを1枚公開して手札に加えてもよい。残りを控え室に置く。": "[On Play] You may put 1 card from your hand into the waiting room: Look at the top 4 cards of your deck. You may reveal 1 'lilywhite' card from among them and add it to your hand. Put the rest into the waiting room.",
    # [1] PL!-pb1-017-P＋
    "{{toujyou.png|登場}}このメンバーをウェイトにしてもよい：カードを1枚引く。その後、このメンバーが『Printemps』のメンバーからバトンタッチして登場していないかぎり、手札を1枚控え室に置く。": "[On Play] You may set this member to Waiting state: Draw 1 card. Then, unless this member entered via Baton Touch from a 'Printemps' member, put 1 card from your hand into the waiting room.",
    # [1] PL!-pb1-018-P＋
    "{{toujyou.png|登場}}自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる。（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない。）": "[On Play] Both you and your opponent play 1 Member card with Cost 2 or less from your own waiting room into an empty area in Waiting state. (No other members can enter the area where a member entered by this effect this turn.)",
    # [1] PL!-pb1-028-L
    "{{live_start.png|ライブ開始時}}自分のステージにいる『Printemps』のメンバーをアクティブにする。これによりウェイト状態のメンバーが3人以上アクティブ状態になったとき、このカードのスコアを＋１する。": "[Live Start] Activate all 'Printemps' members on your stage. If 3 or more Waiting state members become Active state by this effect, Live Score +1 for this card.",
    # [1] PL!-pb1-029-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場のカードが0枚で、かつ自分のステージにいるメンバーが『lilywhite』のみの場合、このカードのスコアを＋１する。": "[Live Start] If you have 0 cards in your Success Live Area and only 'lilywhite' members on your stage, Live Score +1 for this card.",
    # [1] PL!-pb1-030-L
    "{{live_start.png|ライブ開始時}}相手のステージにウェイト状態のメンバーがいる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。": "[Live Start] If there is a Waiting state member on your opponent's stage, reduce the Hearts required to succeed this card by [Heart 00][Heart 00].",
    # [1] PL!-pb1-030-L (Second ability)
    "{{live_success.png|ライブ成功時}}自分のステージに名前の異なる『BiBi』のメンバーが2人以上いる場合、自分の控え室から『BiBi』のメンバーカードを1枚手札に加える。": "[Live Success] If you have 2 or more 'BiBi' members with different names on your stage, add 1 'BiBi' Member card from your waiting room to your hand.",
    # [1] PL!-pb1-031-L
    "{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：エールにより公開された自分のカードの中から、『μ's』のメンバーカードを1枚手札に加える。": "[Live Success] You may put 1 card from your hand into the waiting room: Add 1 'μ's' Member card revealed by your Yell to your hand.",
    # [1] PL!-pb1-032-L
    "{{live_success.png|ライブ成功時}}自分の成功ライブカード置き場に『μ's』のカードがある場合、カードを1枚引く。": "[Live Success] If you have a 'μ's' card in your Success Live Area, draw 1 card.",
    # [1] PL!-bp4-002-SEC
    "{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を2枚控え室に置く：自分の控え室から『μ's』のライブカードを1枚手札に加える。この能力は、自分の成功ライブカード置き場にあるカードのスコアの合計が７以上の場合のみ起動できる。": "[Activate] [Turn 1] Put 2 cards from your hand into the waiting room: Add 1 'μ's' Live card from your waiting room to your hand. This ability can only be used if the total Score of cards in your Success Live Area is 7 or more.",
    # [1] PL!-bp4-011-N
    "{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may set this member to Waiting state: 'μ's' member in your Center Area gets +2 Blades until the end of the live phase.",
    # [1] PL!-bp4-013-N
    "{{live_start.png|ライブ開始時}}手札を1枚控え室に置いてもよい：ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{heart_01.png|heart01}}を得る。": "[Live Start] You may put 1 card from your hand into the waiting room: 1 member on your stage other than this member gets [Heart 01] until the end of the live phase.",
    # [1] PL!-bp4-014-N
    "{{live_start.png|ライブ開始時}}自分のライブ中のライブカードに、{{live_start.png|ライブ開始時}}能力も{{live_success.png|ライブ成功時}}能力も持たないカードがある場合、ライブ終了時まで、自分のステージにいるこのメンバー以外のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] If you have a Live card in progress with no [Live Start] or [Live Success] abilities, 1 member on your stage other than this member gets +2 Blades until the end of the live phase.",
    # [1] PL!-bp4-016-N
    "{{toujyou.png|登場}}自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合、カードを1枚引く。": "[On Play] If the total Score of cards in your Success Live Area is 3 or more, draw 1 card.",
    # [1] PL!-bp4-017-N
    "{{live_start.png|ライブ開始時}}このメンバーをウェイトにしてもよい：ライブ終了時まで、自分のセンターエリアにいる『μ's』のメンバーは、{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may set this member to Waiting state: 'μ's' member in your Center Area gets +1 Blade until the end of the live phase.",
    # [1] PL!-bp4-018-N
    "{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as your total Success Live Score is higher than your opponent's, this member gets +2 Blades.",
    # [1] PL!-bp4-019-L
    "{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあり、かつ自分のステージに『μ's』のメンバーがいるかぎり、自分の成功ライブカード置き場にあるこのカードのスコアを＋５する。": "[Continuous] As long as this card is in your Success Live Area and you have a 'μ's' member on your stage, the Score of this card in your Success Live Area is increased by 5.",
    # [1] PL!-bp4-020-L
    "{{live_start.png|ライブ開始時}}自分のステージにいるメンバーが『μ's』のみの場合、自分のステージにいるメンバー1人をポジションチェンジさせてもよい。": "[Live Start] If you have only 'μ's' members on your stage, you may Position Change 1 member on your stage.",
    # [1] PL!-bp4-020-L (Second ability)
    "{{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。": "[Continuous] As long as this card is in your Success Live Area, 'μ's' member in your Center Area gets +1 Blade.",
    # [1] PL!-bp4-021-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカードのスコアの合計が６以上の場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}減らす。スコアの合計が９以上の場合、さらにこのカードのスコアを＋１する。": "[Live Start] If the total Score of cards in your Success Live Area is 6 or more, reduce the Hearts required to succeed this card by [Heart 00]. If the total is 9 or more, additionally Live Score +1 for this card.",
    # [1] PL!-bp4-022-L
    "{{live_start.png|ライブ開始時}}自分のセンターエリアに{{icon_blade.png|ブレード}}を9つ以上持つ『μ's』のメンバーがいる場合、このカードのスコアを＋２する。": "[Live Start] If you have a 'μ's' member with 9 or more Blades in your Center Area, Live Score +2 for this card.",
    # [1] PL!-bp4-023-L
    "{{live_success.png|ライブ成功時}}自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く。": "[Live Success] If you have 1 or more excess [Heart 01], draw 1 card.",
    # [1] PL!-bp4-024-L
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる『μ's』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。": "[Live Start] 1 'μ's' member on your stage gets +1 Blade until the end of the live phase.",
    # [1] PL!N-bp4-018-N
    "{{jidou.png|自動}}{{turn1.png|ターン1回}}自分のメインフェイズの間、このメンバーがアクティブ状態からウェイト状態になったとき、カードを1枚引き、手札を1枚控え室に置く。": "[Auto] [Turn 1] During your Main Phase, when this member changes from Active to Waiting state, draw 1 card, then put 1 card from your hand into the waiting room.",
    # [1] PL!N-bp4-021-N
    "{{toujyou.png|登場}}自分の控え室にあるカード1枚をデッキの一番上に置いてもよい。": "[On Play] You may put 1 card from your waiting room on top of your deck.",
    # [1] PL!N-bp4-023-N
    "{{toujyou.png|登場}}『虹ヶ咲」のメンバー1人をウェイトにしてもよい：カードを1枚引き、手札を1枚控え室に置く。": "[On Play] You may set 1 'Nijigasaki' member to Waiting state: Draw 1 card, then put 1 card from your hand into the waiting room.",
    # [1] PL!N-bp4-025-L
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[青ブレード]になる。": "[Live Start] Until the end of the live phase, all [Pink Blade], [Red Blade], [Yellow Blade], [Green Blade], [Purple Blade], and [ALL Blade] on cards revealed by your Yell become [Blue Blade].",
    # [1] PL!N-bp4-025-L (Second ability)
    "{{live_success.png|ライブ成功時}}エールにより公開された自分の『虹ヶ咲』のメンバーカードが持つハートの中に{{heart_01.png|heart01}}、{{heart_02.png|heart02}}、{{heart_03.png|heart03}}、{{heart_04.png|heart04}}、{{heart_05.png|heart05}}、{{heart_06.png|heart06}}がある場合、このカードのスコアを＋１する。": "[Live Success] If 'Nijigasaki' Member cards revealed by your Yell have [Heart 01], [Heart 02], [Heart 03], [Heart 04], [Heart 05], or [Heart 06], Live Score +1 for this card.",
    # [1] PL!N-bp4-026-L
    "{{jidou.png|自動}}自分のメインフェイズにこのカードが控え室から手札に加えられたとき、自分の手札からカード名が「DIVE!」のライブカード1枚を表向きでライブカード置き場に置いてもよい。そうした場合、次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る。": "[Auto] When this card is added to your hand from the waiting room during your Main Phase, you may put 1 'DIVE!' Live card from your hand face up into your Live Area. If you do, the maximum number of Live cards you can set during your next Live Card Set Phase is reduced by 1.",
    # [1] PL!N-bp4-026-L (Second ability)
    "{{jidou.png|自動}}このカードが表向きでライブカード置き場に置かれたとき、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Auto] When this card is placed face up in the Live Area, 1 'Nijigasaki' member on your stage gets +2 Blades until the end of the live phase.",
    # [1] PL!N-bp4-027-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場にあるカード名が「EMOTION」のカード1枚につき、このカードのスコアを＋２し、成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}増やす。": "[Live Start] For each 'EMOTION' card in your Success Live Area, Live Score +2 for this card, but increase the Hearts required to succeed it by [Heart 00][Heart 00][Heart 00].",
    # [1] PL!N-bp4-028-L
    "{{live_start.png|ライブ開始時}}自分の控え室にカード名の異なる『虹ヶ咲』のライブカードが4枚以上ある場合、このカードのスコアを＋１する。6枚以上ある場合、代わりにスコアを＋２する。": "[Live Start] If you have 4 or more 'Nijigasaki' Live cards with different names in your waiting room, Live Score +1 for this card. If you have 6 or more, Live Score +2 instead.",
    # [1] PL!N-bp4-029-L
    "{{live_start.png|ライブ開始時}}このゲームの1ターン目のライブフェイズの場合、このカードのスコアを＋１し、ライブ終了時まで、自分のステージにいる『虹ヶ咲』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。": "[Live Start] If this is the Live Phase of the first turn of the game, Live Score +1 for this card, and 1 'Nijigasaki' member on your stage gets +1 Blade until the end of the live phase.",
    # [1] PL!N-bp4-030-L
    "{{live_success.png|ライブ成功時}}以下から1つを選ぶ。自分の成功ライブカード置き場に『虹ヶ咲』のカードがある場合、代わりに1つ以上を選ぶ。": "[Live Success] Choose 1 of the following. If you have a 'Nijigasaki' card in your Success Live Area, choose 1 or more instead.",
    # [1] PL!N-bp4-030-L (Option 1)
    "・自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く。": "- Place 1 Energy card from your Energy Deck into your Energy Area in Waiting state.",
    # [1] PL!N-bp4-030-L (Option 2)
    "・自分の控え室からメンバーカードを1枚手札に加える。": "- Add 1 Member card from your waiting room to your hand.",
    # [1] PL!N-bp4-031-L
    "{{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッキの上に置く。": "[Live Start] If you have 'Nijigasaki' members in all areas of your stage and their total Cost is 20 or more, draw 3 cards, then put 3 cards from your hand on top of your deck in any order.",
    # [1] PL!SP-bp4-012-N
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、{{heart_02.png|heart02}}を得る。": "[Live Start] You may pay (E): This member gets [Heart 02] until the end of the live phase.",
    # [1] PL!SP-bp4-013-N
    "{{toujyou.png|登場}}このメンバーをポジションチェンジしてもよい。(このメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる。)": "[On Play] You may Position Change this member. (Move this member to a different area. If a member is in that area, move that member to the area this member was in.)",
    # [1] PL!SP-bp4-016-N
    "{{jidou.png|自動}}カードの効果によって自分のエネルギー置き場にエネルギーカードが置かれるたび、ライブ終了時まで、{{heart_06.png|heart06}}を得る。(相手のカードの効果でも発動する。)": "[Auto] Whenever an Energy card is placed into your Energy Area by a card effect, this member gets [Heart 06] until the end of the live phase. (Also activates by your opponent's card effects.)",
    # [1] PL!SP-bp4-017-N
    "{{live_start.png|ライブ開始時}}【左サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は左サイドエリアにいる場合のみ発動する。）": "[Live Start] [Left Side] If this member has moved areas this turn, this member gets +2 Blades until the end of the live phase. (Activates only when in the Left Side Area.)",
    # [1] PL!SP-bp4-018-N
    "{{kidou.png|起動}}このメンバーをステージから控え室に置く：自分の控え室から『Liella!』のカードを1枚手札に加える。": "[Activate] Put this member from the stage into the waiting room: Add 1 'Liella!' card from your waiting room to your hand.",
    # [1] PL!SP-bp4-020-N
    "{{live_start.png|ライブ開始時}}【右サイド】このターン、このメンバーがエリアを移動している場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。（この能力は右サイドエリアにいる場合のみ発動する。）": "[Live Start] [Right Side] If this member has moved areas this turn, this member gets +2 Blades until the end of the live phase. (Activates only when in the Right Side Area.)",
    # [1] PL!SP-bp4-021-N
    "{{jyouji.png|常時}}自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る。": "[Continuous] As long as you have more Energy than your opponent, this member gets [Heart 06].",
    # [1] PL!SP-bp4-022-N
    "{{live_start.png|ライブ開始時}}{{icon_energy.png|E}}を2つまで支払ってもよい：ライブ終了時まで、支払った{{icon_energy.png|E}}につき、{{icon_blade.png|ブレード}}を得る。": "[Live Start] You may pay up to (E)(E): This member gets +1 Blade for each (E) paid until the end of the live phase.",
    # [1] PL!SP-bp4-023-L
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージにいる、「澁谷かのん」「ウィーン・マルガレーテ」「鬼塚冬毬」のうちのメンバー1人と、これにより選んだメンバー以外の『Liella!』のメンバー1人は、{{icon_blade.png|ブレード}}を得る。": "[Live Start] Choose 1 'Kanon Shibuya', 'Wien Margarete', or 'Tomari Onitsuka' on your stage. That member and 1 other 'Liella!' member on your stage get +1 Blade until the end of the live phase.",
    # [1] PL!SP-bp4-023-L (Second ability)
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[紫ブレード]になる。": "[Live Start] Until the end of the live phase, all [Pink Blade], [Red Blade], [Yellow Blade], [Green Blade], [Blue Blade], and [ALL Blade] on cards revealed by your Yell become [Purple Blade].",
    # [1] PL!SP-bp4-024-L
    "{{live_start.png|ライブ開始時}}自分のセンターエリアにいる『Liella!』のメンバーのコストが、相手のセンターエリアにいるメンバーより高い場合、このカードのスコアを＋１する。": "[Live Start] If the Cost of the 'Liella!' member in your Center Area is higher than the Cost of the member in your opponent's Center Area, Live Score +1 for this card.",
    # [1] PL!SP-bp4-024-L (Second ability)
    "{{live_start.png|ライブ開始時}}自分のステージの左サイドエリアにいる『Liella!』のメンバーが{{heart_02.png|heart02}}を3つ以上持つ場合、そのメンバーは、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。": "[Live Start] If the 'Liella!' member in your Left Side Area has 3 or more [Heart 02], that member gets +2 Blades until the end of the live phase.",
    # [1] PL!SP-bp4-025-L
    "{{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる。": "[Live Start] Until the end of the live phase, the number of base Blades of the 'Liella!' member in your Center Area becomes 3.",
    # [1] PL!SP-bp4-025-L (Second ability)
    "{{live_success.png|ライブ成功時}}自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを＋１する。": "[Live Success] If the 'Liella!' member in your Center Area has moved this turn, Live Score +1 for this card.",
    # [1] PL!SP-bp4-026-L
    "{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中に名前が異なる『Liella!』のメンバーカードが5枚以上ある場合、このカードのスコアを＋１する。": "[Live Success] If 5 or more 'Liella!' Member cards with different names are revealed by your Yell, Live Score +1 for this card.",
    # [1] PL!SP-bp4-026-L (Second ability)
    "{{live_success.png|ライブ成功時}}自分のエネルギーが11枚以上ある場合、カードを2枚引き、手札を1枚控え室に置く。": "[Live Success] If you have 11 or more Energy, draw 2 cards, then put 1 card from your hand into the waiting room.",
    # [1] PL!SP-bp4-027-L
    "{{live_success.png|ライブ成功時}}自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)": "[Live Success] If you have only 'Liella!' members on your stage, you may Formation Change your members. (Move each member to any area. You cannot move 2 or more members to the same area with this effect.)",
    # [1] PL!SP-bp4-028-L
    "{{live_start.png|ライブ開始時}}アクティブ状態の自分のエネルギーがある場合、このカードのスコアを＋１する。": "[Live Start] If you have any Active Energy, Live Score +1 for this card.",
    # [1] LL-bp4-001-R＋
    "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}}自分のデッキの上からカードを5枚見る。その中から「絢瀬絵里」か「朝香果林」か「葉月恋」のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。その後、相手のステージにいる、これにより公開したカードのコスト以下で、かつ元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバーをすべてウェイトにする。": "[On Play] / [Live Start] Look at the top 5 cards of your deck. You may reveal 1 'Eli Ayase', 'Karin Asaka', or 'Ren Hazuki' Member card from among them and add it to your hand. Put the rest into the waiting room. Then, set all members on your opponent's stage with Cost equal to or less than the revealed card and with 3 or fewer base Blades to Waiting state.",
    # [1] PL!N-pb1-034-N
    "{{live_start.png|ライブ開始時}}{{heart_03.png|heart03}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。": "[Live Start] Choose [Heart 03], [Heart 04], or [Heart 05]. All base Hearts of this member become the chosen Heart until the end of the live phase.",
    # [1] PL!N-pb1-036-N
    "{{live_start.png|ライブ開始時}}{{heart_01.png|heart01}}か{{heart_02.png|heart02}}か{{heart_06.png|heart06}}のうち1つを選ぶ。ライブ終了時まで、このメンバーが元々持つハートは選んだハートになる。": "[Live Start] Choose [Heart 01], [Heart 02], or [Heart 06]. All base Hearts of this member become the chosen Heart until the end of the live phase.",
    # [1] PL!N-pb1-037-L
    "{{live_start.png|ライブ開始時}}このターン、自分の『虹ヶ咲』のカードの効果によってウェイト状態の自分のエネルギーをアクティブにしていた場合、このカードのスコアを＋１する。さらに、自分の『虹ヶ咲』のカードの効果によって自分のステージにいるウェイト状態のメンバーもアクティブにしていた場合、代わりにスコアを＋２する。": "[Live Start] If you activated Waiting state Energy by a 'Nijigasaki' card effect this turn, Live Score +1 for this card. Additionally, if you also activated a Waiting state member on your stage by a 'Nijigasaki' card effect, Live Score +2 instead.",
    # [1] PL!N-pb1-038-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が4の『虹ヶ咲』のライブカードがある場合、このカードのスコアを＋１する。": "[Live Start] If you have a 'Nijigasaki' Live card requiring 4 [Heart 01] in your Success Live Area or among your Live cards in progress, Live Score +1 for this card.",
    # [1] PL!N-pb1-039-L
    "{{live_start.png|ライブ開始時}}自分の成功ライブカード置き場かライブ中のライブカードの中に、必要ハートに含まれる{{heart_01.png|heart01}}が3の『虹ヶ咲』のライブカードがある場合、ライブ終了時まで、自分のステージにいる{{heart_06.png|heart06}}を持つ『虹ヶ咲』のメンバー1人は{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}{{heart_06.png|heart06}}を得る。": "[Live Start] If you have a 'Nijigasaki' Live card requiring 3 [Heart 01] in your Success Live Area or among your Live cards in progress, 1 'Nijigasaki' member with [Heart 06] on your stage gets [Heart 06][Heart 06][Heart 06][Heart 06] until the end of the live phase.",
    # [1] PL!N-pb1-042-L
    "{{live_start.png|ライブ開始時}}自分のステージに同じ名前の『虹ヶ咲』のメンバーが2人以上いる場合、このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす。": "[Live Start] If you have 2 or more 'Nijigasaki' members with the same name on your stage, reduce the Hearts required to succeed this card by [Heart 00][Heart 00][Heart 00].",
}


def normalize(text):
    text = re.sub(r"\{\{.*?\|(.*?)\}\}", r"\1", text)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"[・、。：！\!？\?\s\(\)（）/]", "", text)
    # Also standardize quotes to empty or simple
    text = text.replace('"', "").replace("「", "").replace("」", "")
    return text


with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

with open("data/manual_translations_en.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

# Create normalized map
norm_map = {normalize(k): v for k, v in translations_map.items()}

count = 0
for cid, card in cards.items():
    text = card.get("ability")
    if not text or text == "なし":
        continue

    # Check if we have a translation for this text (normalized)
    norm = normalize(text)
    if norm in norm_map:
        # We overwrite even if it exists to ensure latest translation fix (e.g. for duplicates)
        # But we verify if it helps
        if existing.get(cid) != norm_map[norm]:
            existing[cid] = norm_map[norm]
            count += 1
    elif cid in existing:
        # Skip if already exists and not in our map
        pass

with open("data/manual_translations_en.json", "w", encoding="utf-8") as f:
    json.dump(existing, f, indent=4, ensure_ascii=False)

print(f"Updated {count} translations in manual_translations_en.json")
