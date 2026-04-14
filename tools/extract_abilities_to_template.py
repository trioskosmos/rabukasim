DSL_PATTERNS = [
        # ===== SENTENCE SKELETON PATTERNS =====
        # Extracted from actual abilities - game terms are variables (in brackets)
        # These patterns capture the sentence structure, not individual words
        # Word boundaries (\b) ensure patterns don't match too far back

        # From: "自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。"
        {
            "name": "zone_card_count_condition_zone_to_zone_add",
            "regex": r"([^。]+)の([^。]+)にカードが(\d+)枚以上ある場合、([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE1⟧の⟦ZONE1⟧にカードが⟦NUMBER1⟧枚以上ある場合、⟦SOURCE2⟧の⟦ZONE2⟧から⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に加える",
            "structure": "Zone card count condition to zone add",
        },

        # From: "自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。"
        {
            "name": "per_card_resource_gain",
            "regex": r"([^。]+)の([^。]+)にあるカード(\d+)枚につき、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にあるカード⟦NUMBER⟧枚につき、⟦RESOURCE⟧を得る",
            "structure": "Per card resource gain",
        },

        # From: "このメンバーをステージから控え室に置く：自分の控え室からメンバーカードを1枚手札に加える。"
        {
            "name": "activation_cost_zone_to_zone_add",
            "regex": r"([^。]+)を([^。]+)から([^。]+)に置く：([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦COST_TARGET⟧を⟦SOURCE_ZONE⟧から⟦DESTINATION_ZONE⟧に置く：⟦SOURCE⟧の⟦ZONE⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
            "structure": "Activation cost zone to zone add",
        },

        # From: "自分の控え室からメンバーカードを1枚手札に加える"
        {
            "name": "zone_to_zone_add",
            "regex": r"([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE⟧の⟦ZONE⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
            "structure": "Zone to zone add",
        },

        # From: "このメンバーをステージから控え室に置く"
        {
            "name": "activation_cost_zone_to_zone",
            "regex": r"([^。]+)を([^。]+)から([^。]+)に置く",
            "template": "⟦COST_TARGET⟧を⟦SOURCE_ZONE⟧から⟦DESTINATION_ZONE⟧に置く",
            "structure": "Activation cost zone to zone",
        },


        # From: "自分のデッキの上からカードを5枚見る。"
        {
            "name": "deck_top_look",
            "regex": r"\b([^。]+)の([^。]+)の上から([^。]+)を(\d+)枚見る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧の上から⟦RESOURCE⟧を⟦NUMBER⟧枚見る",
            "structure": "Deck top look",
        },

        # From: "その中から『μ's』のライブカードを1枚公開して手札に加えてもよい。"
        {
            "name": "from_among_reveal_add_optional",
            "regex": r"\bその中から『([^』]+)』の([^。]+)を(\d+)枚公開して([^。]+)に加えてもよい",
            "template": "その中から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚公開して⟦ZONE⟧に加えてもよい",
            "structure": "From among reveal add optional",
        },

        # From: "残りを控え室に置く。"
        {
            "name": "remainder_place",
            "regex": r"\b残りを([^。]+)に置く",
            "template": "残りを⟦ZONE⟧に置く",
            "structure": "Remainder place",
        },

        # From: "手札を1枚控え室に置いてもよい"
        {
            "name": "zone_to_zone_optional",
            "regex": r"([^。]+)を(\d+)枚([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置いてもよい",
            "structure": "Zone to zone optional",
        },

        # From: "相手のステージにいるコスト4以下のメンバー1人をウェイトにする"
        {
            "name": "zone_members_cost_below_wait",
            "regex": r"([^。]+)の([^。]+)いるコスト(\d+)以下の([^。]+)(\d+)人を([^。]+)にする",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以下の⟦TARGET⟧⟦NUMBER⟧人を⟦STATE⟧にする",
            "structure": "Zone members cost below wait",
        },

        # From: "カードを1枚引き"
        {
            "name": "card_draw",
            "regex": r"([^。]+)を(\d+)枚引き",
            "template": "⟦RESOURCE⟧を⟦NUMBER⟧枚引き",
            "structure": "Card draw",
        },

        # From: "ライブの合計スコアを+１する"
        {
            "name": "score_modify",
            "regex": r"([^。]+)の([^。]+)を([^。]+)する",
            "template": "⟦TARGET⟧の⟦ATTRIBUTE⟧を⟦MODIFIER⟧する",
            "structure": "Score modify",
        },

        # From: "手札のライブカードを1枚公開してもよい"
        {
            "name": "zone_card_reveal_optional",
            "regex": r"([^。]+)の([^。]+)を(\d+)枚公開してもよい",
            "template": "⟦SOURCE⟧の⟦CARD_TYPE⟧を⟦NUMBER⟧枚公開してもよい",
            "structure": "Zone card reveal optional",
        },

        # From: "そうした場合、これにより公開したカードを自分の成功ライブカード置き場に置く"
        {
            "name": "conditional_place",
            "regex": r"そうした場合、これにより([^。]+)した([^。]+)を([^。]+)の([^。]+)に置く",
            "template": "そうした場合、これにより⟦ACTION⟧した⟦TARGET⟧を⟦SOURCE⟧の⟦ZONE⟧に置く",
            "structure": "Conditional place",
        },

        # From: "自分のデッキの上からカードを10枚控え室に置く"
        {
            "name": "deck_top_place",
            "regex": r"([^。]+)の([^。]+)の上から([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦SOURCE⟧の⟦ZONE⟧の上から⟦RESOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置く",
            "structure": "Deck top place",
        },

        # From: "それらの中にライブカードがある場合、カードを1枚引く"
        {
            "name": "condition_draw",
            "regex": r"それらの中に([^。]+)がある場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "それらの中に⟦CARD_TYPE⟧がある場合、⟦RESOURCE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Condition draw",
        },

        # From: "手札をすべて公開する"
        {
            "name": "zone_reveal_all",
            "regex": r"\b([^。]+)をすべて([^。]+)する",
            "template": "⟦SOURCE⟧をすべて⟦ACTION⟧する",
            "structure": "Zone reveal all",
        },

        # From: "自分のステージにこのメンバー以外の『EdelNote』のメンバーがいるかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "condition_zone_member_presence_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)がいるかぎり、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦CONDITION⟧がいるかぎり、⟦RESOURCE⟧を得る",
            "structure": "Condition zone member presence resource gain",
        },

        # From: "自分のステージにいるコスト4以上の『スリーズブーケ』以外のメンバー1人につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "zone_member_cost_except_group_per_member_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)いるコスト(\d+)以上の([^。]+)以外の([^。]+)(\d+)人につき、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以上の⟦EXCEPT_GROUP⟧以外の⟦TARGET⟧⟦NUMBER⟧人につき、⟦RESOURCE⟧を得る",
            "structure": "Zone member cost except group per member resource gain",
        },

        # From: "自分の成功ライブカード置き場にあるカードのスコアの合計が相手より高いかぎり、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "zone_card_score_comparison_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)の([^。]+)が([^。]+)より([^。]+)かぎり、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧かぎり、⟦RESOURCE⟧を得る",
            "structure": "Zone card score comparison condition resource gain",
        },

        # From: "自分のステージにいるメンバーが持つ{{icon_blade.png|ブレード}}の合計が10以上の場合"
        {
            "name": "zone_member_resource_total_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)が持つ([^。]+)の([^。]+)が(\d+)以上の場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が持つ⟦RESOURCE⟧の⟦ATTRIBUTE⟧が⟦NUMBER⟧以上の場合",
            "structure": "Zone member resource total condition",
        },

        # From: "自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり"
        {
            "name": "zone_member_cost_distinct_count_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)が([^。]+)メンバーが(\d+)人以上いるかぎり",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦ATTRIBUTE⟧が⟦CONDITION⟧メンバーが⟦NUMBER⟧人以上いるかぎり",
            "structure": "Zone member cost distinct count condition",
        },

        # From: "自分のステージにいるメンバーがちょうど2人であるかぎり"
        {
            "name": "zone_member_exact_count_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)がちょうど(\d+)人であるかぎり",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧がちょうど⟦NUMBER⟧人であるかぎり",
            "structure": "Zone member exact count condition",
        },

        # From: "自分のステージにいるメンバーが『Liella!』のみで"
        {
            "name": "zone_member_group_only_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)が『([^』]+)』のみで",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が『⟦GROUP⟧』のみで",
            "structure": "Zone member group only condition",
        },

        # From: "このカードを成功させるための必要ハートを{{heart_00.png|heart0}}{{heart_00.png|heart0}}{{heart_00.png|heart0}}減らす"
        {
            "name": "cost_heart_reduce",
            "regex": r"\b([^。]+)を成功させるための必要ハートを([^。]+)減らす",
            "template": "⟦TARGET⟧を成功させるための必要ハートを⟦MODIFIER⟧減らす",
            "structure": "Cost heart reduce",
        },

        # From: "このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる"
        {
            "name": "cost_heart_become_less",
            "regex": r"\b([^。]+)を成功させるための必要ハートは([^。]+)少なくなる",
            "template": "⟦TARGET⟧を成功させるための必要ハートは⟦MODIFIER⟧少なくなる",
            "structure": "Cost heart become less",
        },

        # From: "自分のステージに同じ名前の『虹ヶ咲』のメンバーが2人以上いる場合"
        {
            "name": "zone_member_same_name_group_count_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)の『([^』]+)』の([^。]+)が(\d+)人以上いる場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦ATTRIBUTE⟧の『⟦GROUP⟧』の⟦TARGET⟧が⟦NUMBER⟧人以上いる場合",
            "structure": "Zone member same name group count condition",
        },

        # From: "自分のステージにほかのメンバーがおり、かつこれにより公開した手札の中にライブカードがない場合"
        {
            "name": "multi_condition_zone_card_presence",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)がおり、かつこれにより([^。]+)した([^。]+)の中に([^。]+)がない場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦CONDITION1⟧がおり、かつこれにより⟦ACTION⟧した⟦ZONE2⟧の中に⟦CARD_TYPE⟧がない場合",
            "structure": "Multi condition zone card presence",
        },

        # From: "このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る"
        {
            "name": "card_location_condition_zone_member_resource_gain",
            "regex": r"\b([^。]+)が([^。]+)にあるかぎり、([^。]+)の([^。]+)にいる([^。]+)は([^。]+)を得る",
            "template": "⟦CARD⟧が⟦ZONE1⟧にあるかぎり、⟦SOURCE⟧の⟦ZONE2⟧にいる⟦TARGET⟧は⟦RESOURCE⟧を得る",
            "structure": "Card location condition zone member resource gain",
        },

        # From: "自分と相手のエネルギーの合計が15枚以上あるかぎり"
        {
            "name": "energy_total_condition_resource_gain",
            "regex": r"\b([^。]+)と([^。]+)の([^。]+)の([^。]+)が(\d+)枚以上あるかぎり",
            "template": "⟦SOURCE1⟧と⟦SOURCE2⟧の⟦RESOURCE⟧の⟦ATTRIBUTE⟧が⟦NUMBER⟧枚以上あるかぎり",
            "structure": "Energy total condition resource gain",
        },

        # From: "このメンバーをポジションチェンジしてもよい"
        {
            "name": "position_change_optional",
            "regex": r"\b([^。]+)を([^。]+)してもよい",
            "template": "⟦TARGET⟧を⟦ACTION⟧してもよい",
            "structure": "Position change optional",
        },

        # From: "自分のステージにいるメンバーをフォーメーションチェンジしてもよい"
        {
            "name": "formation_change_optional",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)を([^。]+)してもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧を⟦ACTION⟧してもよい",
            "structure": "Formation change optional",
        },

        # From: "このターン、自分が余剰ハートに{{heart_04.png|heart04}}を1つ以上持っており"
        {
            "name": "turn_surplus_heart_condition",
            "regex": r"\b([^。]+)、([^。]+)が([^。]+)に([^。]+)を(\d+)つ以上持っており",
            "template": "⟦TURN⟧、⟦SOURCE⟧が⟦ZONE⟧に⟦RESOURCE⟧を⟦NUMBER⟧つ以上持っており",
            "structure": "Turn surplus heart condition",
        },

        # From: "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く"
        {
            "name": "energy_deck_place_wait_state",
            "regex": r"\b([^。]+)の([^。]+)から、([^。]+)を(\d+)枚([^。]+)で置く",
            "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦STATE⟧で置く",
            "structure": "Energy deck place wait state",
        },

        # From: "エールにより公開された自分のカードの中にライブカードが1枚以上あるとき"
        {
            "name": "cheer_revealed_card_condition",
            "regex": r"\b([^。]+)により([^。]+)した([^。]+)の中に([^。]+)が(\d+)枚以上あるとき",
            "template": "⟦CONTEXT⟧により⟦ACTION⟧した⟦ZONE⟧の中に⟦CARD_TYPE⟧が⟦NUMBER⟧枚以上あるとき",
            "structure": "Cheer revealed card condition",
        },

        # From: "相手のライブカード置き場にあるすべてのライブカードは、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる"
        {
            "name": "zone_all_cards_cost_increase",
            "regex": r"\b([^。]+)の([^。]+)にあるすべての([^。]+)は、([^。]+)ための([^。]+)が([^。]+)多くなる",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にあるすべての⟦CARD_TYPE⟧は、⟦CONTEXT⟧ための⟦COST⟧が⟦MODIFIER⟧多くなる",
            "structure": "Zone all cards cost increase",
        },

        # From: "自分のライブカード置き場にあるこのカード以外の『蓮ノ空』のカード1枚につき、このカードの必要ハートを{{heart_04.png|heart04}}{{heart_04.png|heart04}}減らす"
        {
            "name": "zone_card_except_group_per_card_cost_reduce",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)以外の『([^』]+)』の([^。]+)(\d+)枚につき、([^。]+)の([^。]+)を([^。]+)減らす",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦EXCEPT_CARD⟧以外の『⟦GROUP⟧』の⟦CARD_TYPE⟧⟦NUMBER⟧枚につき、⟦TARGET⟧の⟦COST⟧を⟦MODIFIER⟧減らす",
            "structure": "Zone card except group per card cost reduce",
        },

        # From: "自分の控え室にある、カード名の異なるライブカードを2枚選ぶ"
        {
            "name": "zone_select_different_name_cards",
            "regex": r"\b([^。]+)の([^。]+)にある、([^。]+)の([^。]+)を(\d+)枚選ぶ",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある、⟦CONDITION⟧の⟦CARD_TYPE⟧を⟦NUMBER⟧枚選ぶ",
            "structure": "Zone select different name cards",
        },

        # From: "そうした場合、相手はそれらのカードのうち1枚を選ぶ"
        {
            "name": "opponent_select_from_cards",
            "regex": r"\bそうした場合、([^。]+)は([^。]+)の([^。]+)を選ぶ",
            "template": "そうした場合、⟦OPPONENT⟧は⟦SOURCE⟧の⟦NUMBER⟧を選ぶ",
            "structure": "Opponent select from cards",
        },

        # From: "これにより相手に選ばれたカードを自分の手札に加える"
        {
            "name": "opponent_selected_card_add",
            "regex": r"\b([^。]+)により([^。]+)に([^。]+)された([^。]+)を([^。]+)の([^。]+)に加える",
            "template": "⟦CONTEXT⟧により⟦SOURCE⟧に⟦ACTION⟧された⟦CARD⟧を⟦DESTINATION_SOURCE⟧の⟦DESTINATION⟧に加える",
            "structure": "Opponent selected card add",
        },

        # From: "【左サイド】{{heart_02.png|heart02}}{{heart_02.png|heart02}}{{heart_02.png|heart02}}を得る"
        {
            "name": "side_specific_resource_gain",
            "regex": r"\【([^】]+)】([^。]+)を得る",
            "template": "【⟦SIDE⟧】⟦RESOURCE⟧を得る",
            "structure": "Side specific resource gain",
        },

        # From: "自分のライブ中のライブカードが2枚以上あるかぎり"
        {
            "name": "live_card_count_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)が(\d+)枚以上あるかぎり",
            "template": "⟦SOURCE⟧の⟦CONTEXT⟧の⟦CARD_TYPE⟧が⟦NUMBER⟧枚以上あるかぎり",
            "structure": "Live card count condition resource gain",
        },

        # From: "このターンにこのメンバーが移動していないかぎり"
        {
            "name": "turn_member_not_moved_condition",
            "regex": r"\b([^。]+)に([^。]+)が([^。]+)していないかぎり",
            "template": "⟦TURN⟧に⟦TARGET⟧が⟦ACTION⟧していないかぎり",
            "structure": "Turn member not moved condition",
        },

        # From: "手札にあるこのメンバーカードのコストは2減る"
        {
            "name": "hand_card_cost_reduce",
            "regex": r"\b([^。]+)にある([^。]+)の([^。]+)は(\d+)減る",
            "template": "⟦ZONE⟧にある⟦CARD⟧の⟦ATTRIBUTE⟧は⟦NUMBER⟧減る",
            "structure": "Hand card cost reduce",
        },

        # From: "自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く"
        {
            "name": "zone_group_card_deck_top_place",
            "regex": r"\b([^。]+)から『([^』]+)』の([^。]+)を(\d+)枚まで([^。]+)の([^。]+)に置く",
            "template": "⟦SOURCE⟧から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦DESTINATION⟧の⟦POSITION⟧に置く",
            "structure": "Zone group card deck top place",
        },

        # From: "自分のステージにいるほかの『みらくらぱーく！』のメンバー1人につき"
        {
            "name": "zone_other_group_member_per_member_condition",
            "regex": r"\b([^。]+)の([^。]+)いるほかの『([^』]+)』の([^。]+)(\d+)人につき",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いるほかの『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER⟧人につき",
            "structure": "Zone other group member per member condition",
        },

        # From: "バトンタッチして登場した場合"
        {
            "name": "baton_touch_appearance_condition",
            "regex": r"\b([^。]+)して([^。]+)した場合",
            "template": "⟦ACTION⟧して⟦TRIGGER⟧した場合",
            "structure": "Baton touch appearance condition",
        },

        # From: "エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[紫ブレード]、{{icon_b_all.png|ALLブレード}}は、すべて[青ブレード]になる"
        {
            "name": "blade_transformation",
            "regex": r"\b([^。]+)によって([^。]+)される([^。]+)の([^。]+)が持つ([^。]+)は、すべて([^。]+)になる",
            "template": "⟦CONTEXT⟧によって⟦ACTION⟧される⟦SOURCE⟧の⟦CARD_TYPE⟧が持つ⟦ATTRIBUTE⟧は、すべて⟦TRANSFORM⟧になる",
            "structure": "Blade transformation",
        },

        # From: "すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う"
        {
            "name": "card_identity_change",
            "regex": r"\bすべての([^。]+)にある([^。]+)は『([^』]+)』として扱う",
            "template": "すべての⟦ZONE⟧にある⟦CARD⟧は『⟦GROUP⟧』として扱う",
            "structure": "Card identity change",
        },

        # From: "自分のステージにウェイト状態の『虹ヶ咲』のメンバーがいるかぎり"
        {
            "name": "zone_wait_state_member_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)の『([^』]+)』の([^。]+)いるかぎり",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の『⟦GROUP⟧』の⟦TARGET⟧いるかぎり",
            "structure": "Zone wait state member condition",
        },

        # From: "自分のステージにいるこのメンバー以外の『A-RISE』のメンバー1人につき"
        {
            "name": "zone_this_member_except_group_per_member_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)以外の『([^』]+)』の([^。]+)(\d+)人につき",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦EXCEPT_MEMBER⟧以外の『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER⟧人につき",
            "structure": "Zone this member except group per member condition",
        },

        # From: "このメンバーの下にあるエネルギーカード1枚につき"
        {
            "name": "member_under_energy_card_per_card_condition",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)(\d+)枚につき",
            "template": "⟦MEMBER⟧の⟦LOCATION⟧にある⟦CARD_TYPE⟧⟦NUMBER⟧枚につき",
            "structure": "Member under energy card per card condition",
        },

        # From: "メンバー1人をポジションチェンジさせてもよい"
        {
            "name": "member_position_change_optional",
            "regex": r"\b([^。]+)(\d+)人を([^。]+)させてもよい",
            "template": "⟦TARGET⟧⟦NUMBER⟧人を⟦ACTION⟧させてもよい",
            "structure": "Member position change optional",
        },

        # From: "メンバーのいないエリアに登場させる"
        {
            "name": "summon_to_empty_area",
            "regex": r"\b([^。]+)のいない([^。]+)に([^。]+)させる",
            "template": "⟦TARGET⟧のいない⟦ZONE⟧に⟦ACTION⟧させる",
            "structure": "Summon to empty area",
        },

        # From: "このターン、自分のステージにメンバーが3回登場したとき"
        {
            "name": "turn_member_appearance_count_trigger",
            "regex": r"\b([^。]+)、([^。]+)の([^。]+)に([^。]+)が(\d+)回([^。]+)したとき",
            "template": "⟦TURN⟧、⟦SOURCE⟧の⟦ZONE⟧に⟦TARGET⟧が⟦NUMBER⟧回⟦ACTION⟧したとき",
            "structure": "Turn member appearance count trigger",
        },

        # From: "手札が5枚になるまでカードを引く"
        {
            "name": "draw_until_condition",
            "regex": r"\b([^。]+)が(\d+)枚になるまで([^。]+)を([^。]+)",
            "template": "⟦ZONE⟧が⟦NUMBER⟧枚になるまで⟦CARD_TYPE⟧を⟦ACTION⟧",
            "structure": "Draw until condition",
        },

        # From: "コスト10の『Liella!』のメンバーカードを自分の手札から登場させるためのコストは2減る"
        {
            "name": "specific_card_cost_reduce",
            "regex": r"\bコスト(\d+)の『([^』]+)』の([^。]+)を([^。]+)から([^。]+)させるための([^。]+)は(\d+)減る",
            "template": "コスト⟦COST⟧の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦SOURCE⟧から⟦ACTION⟧させるための⟦ATTRIBUTE⟧は⟦MODIFIER⟧減る",
            "structure": "Specific card cost reduce",
        },

        # From: "手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる"
        {
            "name": "hand_card_cost_reduce_per_hand_card",
            "regex": r"\b([^。]+)にある([^。]+)の([^。]+)は、([^。]+)以外の([^。]+)(\d+)枚につき、(\d+)少なくなる",
            "template": "⟦ZONE⟧にある⟦CARD⟧の⟦ATTRIBUTE⟧は、⟦EXCEPT_CARD⟧以外の⟦SOURCE⟧⟦NUMBER1⟧枚につき、⟦NUMBER2⟧少なくなる",
            "structure": "Hand card cost reduce per hand card",
        },

        # From: "この能力は、このカードが自分のエールによって公開されている場合のみ発動する"
        {
            "name": "ability_activation_condition",
            "regex": r"\b([^。]+)は、([^。]+)が([^。]+)の([^。]+)によって([^。]+)されている([^。]+)のみ([^。]+)する",
            "template": "⟦ABILITY⟧は、⟦CARD⟧が⟦SOURCE⟧の⟦CONTEXT⟧によって⟦STATE⟧されている⟦CONDITION⟧のみ⟦ACTION⟧する",
            "structure": "Ability activation condition",
        },

        # From: "相手のステージにいるウェイト状態のメンバー1人につき"
        {
            "name": "opponent_zone_wait_state_member_per_member_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)(\d+)人につき",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧⟦NUMBER⟧人につき",
            "structure": "Opponent zone wait state member per member condition",
        },

        # From: "相手のステージにいるウェイト状態のメンバーの数まで"
        {
            "name": "opponent_zone_member_count_limit",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)の([^。]+)まで",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧の⟦ATTRIBUTE⟧まで",
            "structure": "Opponent zone member count limit",
        },

        # From: "このターン、自分のステージにいるほかのメンバーがエリアを移動している場合"
        {
            "name": "turn_other_member_moved_condition",
            "regex": r"\b([^。]+)、([^。]+)の([^。]+)いるほかの([^。]+)が([^。]+)を([^。]+)している場合",
            "template": "⟦TURN⟧、⟦SOURCE⟧の⟦ZONE⟧いるほかの⟦TARGET⟧が⟦OBJECT⟧を⟦ACTION⟧している場合",
            "structure": "Turn other member moved condition",
        },

        # From: "そのメンバーが持つ{{heart_03.png|heart03}}2つにつき"
        {
            "name": "member_resource_per_resource_condition",
            "regex": r"\b([^。]+)が持つ([^。]+)(\d+)つにつき",
            "template": "⟦MEMBER⟧が持つ⟦RESOURCE⟧⟦NUMBER⟧つにつき",
            "structure": "Member resource per resource condition",
        },

        # From: "この能力では{{heart_00.png|heart0}}は3つまでしか減らない"
        {
            "name": "ability_limitation",
            "regex": r"\b([^。]+)では([^。]+)は(\d+)つまでしか([^。]+)ない",
            "template": "⟦ABILITY⟧では⟦RESOURCE⟧は⟦NUMBER⟧つまでしか⟦LIMITATION⟧ない",
            "structure": "Ability limitation",
        },

        # From: "手札からコスト4以下の『Liella!』のメンバーカードを1枚ステージに登場させてもよい"
        {
            "name": "hand_cost_group_card_summon_optional",
            "regex": r"\b([^。]+)からコスト(\d+)以下の『([^』]+)』の([^。]+)を(\d+)枚([^。]+)に([^。]+)させてもよい",
            "template": "⟦SOURCE⟧からコスト⟦COST⟧以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧させてもよい",
            "structure": "Hand cost group card summon optional",
        },

        # From: "ライブカードが公開されるまで、自分のデッキの一番上のカードを公開し続ける"
        {
            "name": "continuous_reveal_until_condition",
            "regex": r"\b([^。]+)が([^。]+)まで、([^。]+)の([^。]+)の([^。]+)を([^。]+)し続ける",
            "template": "⟦CARD_TYPE⟧が⟦CONDITION⟧まで、⟦SOURCE⟧の⟦ZONE⟧の⟦POSITION⟧を⟦ACTION⟧し続ける",
            "structure": "Continuous reveal until condition",
        },

        # From: "効果によってはアクティブにならない"
        {
            "name": "effect_prevent_state_change",
            "regex": r"\b([^。]+)によっては([^。]+)に([^。]+)ない",
            "template": "⟦CONTEXT⟧によっては⟦STATE⟧に⟦NEGATION⟧ない",
            "structure": "Effect prevent state change",
        },

        # From: "エネルギー1枚をそのメンバーの下に置く"
        {
            "name": "energy_under_member_place",
            "regex": r"\b([^。]+)(\d+)枚を([^。]+)の([^。]+)に置く",
            "template": "⟦RESOURCE⟧⟦NUMBER⟧枚を⟦TARGET⟧の⟦LOCATION⟧に置く",
            "structure": "Energy under member place",
        },

        # From: "メンバーの下に置かれているエネルギーカードではコストを支払えない"
        {
            "name": "energy_under_member_restriction",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)されている([^。]+)では([^。]+)を([^。]+)ない",
            "template": "⟦MEMBER⟧の⟦LOCATION⟧に⟦STATE⟧されている⟦CARD_TYPE⟧では⟦COST⟧を⟦ACTION⟧ない",
            "structure": "Energy under member restriction",
        },

        # From: "メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く"
        {
            "name": "member_leave_energy_return",
            "regex": r"\b([^。]+)が([^。]+)から([^。]+)とき、([^。]+)に([^。]+)されている([^。]+)は([^。]+)に置く",
            "template": "⟦MEMBER⟧が⟦ZONE1⟧から⟦ACTION⟧とき、⟦LOCATION⟧に⟦STATE⟧されている⟦CARD_TYPE⟧は⟦DESTINATION⟧に置く",
            "structure": "Member leave energy return",
        },

        # From: "能力を持たないメンバーカード"
        {
            "name": "ability_less_card",
            "regex": r"\b([^。]+)を([^。]+)ない([^。]+)",
            "template": "⟦ATTRIBUTE⟧を⟦NEGATION⟧ない⟦CARD_TYPE⟧",
            "structure": "Ability less card",
        },

        # From: "自分か相手を選ぶ"
        {
            "name": "player_selection",
            "regex": r"\b([^。]+)か([^。]+)を選ぶ",
            "template": "⟦PLAYER1⟧か⟦PLAYER2⟧を選ぶ",
            "structure": "Player selection",
        },

        # From: "元々持つ{{icon_blade.png|ブレード}}の数は3つになる"
        {
            "name": "original_resource_count_set",
            "regex": r"\b([^。]+)持つ([^。]+)の([^。]+)は(\d+)つになる",
            "template": "⟦MODIFIER⟧持つ⟦RESOURCE⟧の⟦ATTRIBUTE⟧は⟦NUMBER⟧つになる",
            "structure": "Original resource count set",
        },

        # From: "このメンバーがウェイト状態であるかぎり"
        {
            "name": "member_state_condition",
            "regex": r"\b([^。]+)が([^。]+)であるかぎり",
            "template": "⟦MEMBER⟧が⟦STATE⟧であるかぎり",
            "structure": "Member state condition",
        },

        # From: "自分の成功ライブカード置き場にあるカードのスコアの合計が３以上の場合"
        {
            "name": "zone_card_score_total_condition",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)の([^。]+)の([^。]+)が(\d+)以上の場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧の⟦ATTRIBUTE1⟧の⟦ATTRIBUTE2⟧が⟦NUMBER⟧以上の場合",
            "structure": "Zone card score total condition",
        },

        # From: "自分のステージにほかの『5yncri5e!』のメンバーがいる場合"
        {
            "name": "zone_other_group_member_presence_condition",
            "regex": r"\b([^。]+)の([^。]+)にほかの『([^』]+)』の([^。]+)いる場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にほかの『⟦GROUP⟧』の⟦TARGET⟧いる場合",
            "structure": "Zone other group member presence condition",
        },

        # From: "その後、登場したエリアとは別の自分のエリア1つを選ぶ"
        {
            "name": "select_different_area",
            "regex": r"\bその後、([^。]+)した([^。]+)とは([^。]+)の([^。]+)(\d+)つを選ぶ",
            "template": "その後、⟦ACTION⟧した⟦ZONE1⟧とは⟦DIFFERENT⟧の⟦ZONE2⟧⟦NUMBER⟧つを選ぶ",
            "structure": "Select different area",
        },

        # From: "自分のステージに「米女メイ」がいる場合、さらにカードを1枚引く"
        {
            "name": "specific_member_condition_additional_draw",
            "regex": r"\b([^。]+)の([^。]+)に「([^」]+)」いる場合、さらに([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に「⟦MEMBER⟧」いる場合、さらに⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Specific member condition additional draw",
        },

        # From: "自分のエネルギー置き場にあるエネルギー2枚をこのメンバーの下に置いてもよい"
        {
            "name": "energy_zone_to_member_under_optional",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)(\d+)枚を([^。]+)の([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦RESOURCE⟧⟦NUMBER⟧枚を⟦TARGET⟧の⟦LOCATION⟧に置いてもよい",
            "structure": "Energy zone to member under optional",
        },

        # From: "そうした場合、相手はカードを1枚引く"
        {
            "name": "condition_opponent_draw",
            "regex": r"\bそうした場合、([^。]+)は([^。]+)を(\d+)枚([^。]+)",
            "template": "そうした場合、⟦OPPONENT⟧は⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Condition opponent draw",
        },

        # From: "自分の控え室にある、自分のステージにいるすべてのメンバーと異なるグループ名を持つカード1枚を手札に加える"
        {
            "name": "zone_different_group_name_card_add",
            "regex": r"\b([^。]+)の([^。]+)にある、([^。]+)の([^。]+)いるすべての([^。]+)と([^。]+)([^。]+)を持つ([^。]+)(\d+)枚を([^。]+)に加える",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある、⟦SOURCE2⟧の⟦ZONE2⟧いるすべての⟦TARGET⟧と⟦DIFFERENT⟧⟦ATTRIBUTE⟧を持つ⟦CARD_TYPE⟧⟦NUMBER⟧枚を⟦DESTINATION⟧に加える",
            "structure": "Zone different group name card add",
        },

        # From: "自分のステージにいるメンバーを、それぞれ好きなエリアに移動させてもよい"
        {
            "name": "move_members_to_preferred_areas_optional",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)を、それぞれ([^。]+)の([^。]+)に([^。]+)させてもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧を、それぞれ⟦PREFERENCE⟧の⟦DESTINATION⟧に⟦ACTION⟧させてもよい",
            "structure": "Move members to preferred areas optional",
        },

        # From: "自分のカードの効果によって、相手のステージにいるアクティブ状態のコスト4以下のメンバーがウェイト状態になったとき"
        {
            "name": "effect_opponent_state_change_trigger",
            "regex": r"\b([^。]+)の([^。]+)によって、([^。]+)の([^。]+)いる([^。]+)のコスト(\d+)以下の([^。]+)が([^。]+)になったとき",
            "template": "⟦SOURCE⟧の⟦CONTEXT⟧によって、⟦OPPONENT⟧の⟦ZONE⟧いる⟦STATE1⟧のコスト⟦COST⟧以下の⟦TARGET⟧が⟦STATE2⟧になったとき",
            "structure": "Effect opponent state change trigger",
        },

        # From: "自分のステージにほかのメンバーがいない場合、自分はライブできない"
        {
            "name": "no_other_members_condition_prevent_live",
            "regex": r"\b([^。]+)の([^。]+)にほかの([^。]+)いない場合、([^。]+)は([^。]+)できない",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にほかの⟦TARGET⟧いない場合、⟦PLAYER⟧は⟦ACTION⟧できない",
            "structure": "No other members condition prevent live",
        },

        # From: "自分のステージにコスト13以上のメンバーがいる場合、カードを1枚引く"
        {
            "name": "zone_cost_member_condition_draw",
            "regex": r"\b([^。]+)の([^。]+)にコスト(\d+)以上の([^。]+)いる場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にコスト⟦COST⟧以上の⟦TARGET⟧いる場合、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Zone cost member condition draw",
        },

        # From: "このカードのプレイに際し、2人のメンバーとバトンタッチしてもよい"
        {
            "name": "card_play_baton_touch_optional",
            "regex": r"\b([^。]+)の([^。]+)に際し、(\d+)人の([^。]+)と([^。]+)してもよい",
            "template": "⟦CARD⟧の⟦CONTEXT⟧に際し、⟦NUMBER⟧人の⟦TARGET⟧と⟦ACTION⟧してもよい",
            "structure": "Card play baton touch optional",
        },

        # From: "自分のステージに、元々持つハートの数より多い数のハートを持つメンバーがいる場合"
        {
            "name": "original_heart_count_comparison_condition",
            "regex": r"\b([^。]+)の([^。]+)、([^。]+)持つ([^。]+)の([^。]+)より([^。]+)の([^。]+)を持つ([^。]+)いる場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧、⟦MODIFIER⟧持つ⟦ATTRIBUTE1⟧の⟦ATTRIBUTE2⟧より⟦COMPARISON⟧の⟦RESOURCE⟧を持つ⟦TARGET⟧いる場合",
            "structure": "Original heart count comparison condition",
        },

        # From: "自分の成功ライブカード置き場にカードがある場合"
        {
            "name": "zone_card_presence_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)ある場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦CARD_TYPE⟧ある場合",
            "structure": "Zone card presence condition",
        },

        # From: "その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つメンバーカードを3枚まで公開して手札に加えてもよい"
        {
            "name": "select_cards_with_specific_resources_optional",
            "regex": r"\bその中から([^。]+)を持つ([^。]+)を(\d+)枚まで([^。]+)して([^。]+)に加えてもよい",
            "template": "その中から⟦RESOURCE⟧を持つ⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦ACTION⟧して⟦DESTINATION⟧に加えてもよい",
            "structure": "Select cards with specific resources optional",
        },

        # From: "自分のメインフェイズの場合"
        {
            "name": "phase_condition",
            "regex": r"\b([^。]+)の([^。]+)の場合",
            "template": "⟦SOURCE⟧の⟦PHASE⟧の場合",
            "structure": "Phase condition",
        },

        # From: "表向きでライブカード置き場に置く"
        {
            "name": "face_up_placement",
            "regex": r"\b([^。]+)で([^。]+)に置く",
            "template": "⟦STATE⟧で⟦ZONE⟧に置く",
            "structure": "Face up placement",
        },

        # From: "次のライブカードセットフェイズで自分がライブカード置き場に置けるカード枚数の上限が1枚減る"
        {
            "name": "phase_limit_reduction",
            "regex": r"\b([^。]+)の([^。]+)で([^。]+)が([^。]+)に([^。]+)できる([^。]+)の([^。]+)が(\d+)枚([^。]+)",
            "template": "⟦TIME⟧の⟦PHASE⟧で⟦PLAYER⟧が⟦ZONE⟧に⟦ACTION⟧できる⟦CARD_TYPE⟧の⟦LIMIT⟧が⟦NUMBER⟧枚⟦MODIFICATION⟧",
            "structure": "Phase limit reduction",
        },

        # From: "このメンバーは自分のアクティブフェイズにアクティブにしない"
        {
            "name": "phase_based_action_prevention",
            "regex": r"\b([^。]+)は([^。]+)の([^。]+)に([^。]+)に([^。]+)ない",
            "template": "⟦MEMBER⟧は⟦PLAYER⟧の⟦PHASE⟧に⟦ACTION⟧に⟦NEGATION⟧ない",
            "structure": "Phase based action prevention",
        },

        # From: "自分のライブ中のライブカードの必要ハートの中に...がそれぞれ1以上含まれるかぎり"
        {
            "name": "multi_resource_each_condition",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)の([^。]+)に([^。]+)が([^。]+)(\d+)以上([^。]+)かぎり",
            "template": "⟦SOURCE⟧の⟦CONTEXT⟧の⟦CARD_TYPE⟧の⟦ATTRIBUTE⟧に⟦RESOURCE⟧が⟦CONDITION⟧⟦NUMBER⟧以上⟦STATE⟧かぎり",
            "structure": "Multi resource each condition",
        },

        # From: "エールにより公開された自分のカードの中から、ライブカードを1枚までデッキの一番下に置く"
        {
            "name": "from_revealed_cards_to_deck_bottom",
            "regex": r"\b([^。]+)により([^。]+)された([^。]+)の中から、([^。]+)を(\d+)枚まで([^。]+)の([^。]+)に置く",
            "template": "⟦CONTEXT⟧により⟦ACTION⟧された⟦SOURCE⟧の中から、⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦DESTINATION⟧の⟦POSITION⟧に置く",
            "structure": "From revealed cards to deck bottom",
        },

        # From: "このカードは成功ライブカード置き場に置くことができない"
        {
            "name": "card_placement_restriction",
            "regex": r"\b([^。]+)は([^。]+)に([^。]+)ことができない",
            "template": "⟦CARD⟧は⟦ZONE⟧に⟦ACTION⟧ことができない",
            "structure": "Card placement restriction",
        },

        # From: "自分のステージにいるメンバーのコストの合計が相手より低い場合"
        {
            "name": "member_cost_total_comparison_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)の([^。]+)が([^。]+)より([^。]+)場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧の⟦ATTRIBUTE⟧の⟦TOTAL⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合",
            "structure": "Member cost total comparison condition",
        },

        # From: "自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合"
        {
            "name": "combined_zone_card_count_condition",
            "regex": r"\b([^。]+)と([^。]+)の([^。]+)に([^。]+)が([^。]+)(\d+)枚以上ある場合",
            "template": "⟦SOURCE1⟧と⟦SOURCE2⟧の⟦ZONE⟧に⟦CARD_TYPE⟧が⟦TOTAL⟧⟦NUMBER⟧枚以上ある場合",
            "structure": "Combined zone card count condition",
        },

        # From: "自分のエネルギーが7枚以上ある場合"
        {
            "name": "energy_count_condition",
            "regex": r"\b([^。]+)の([^。]+)が(\d+)枚以上ある場合",
            "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦NUMBER⟧枚以上ある場合",
            "structure": "Energy count condition",
        },

        # From: "そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい"
        {
            "name": "score_based_energy_payment_optional",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)の([^。]+)を([^。]+)してもよい",
            "template": "⟦CARD⟧の⟦ATTRIBUTE⟧に⟦EQUAL⟧の⟦RESOURCE⟧を⟦ACTION⟧してもよい",
            "structure": "Score based energy payment optional",
        },

        # From: "バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える"
        {
            "name": "baton_touch_specific_card_recovery",
            "regex": r"\b([^。]+)して([^。]+)した場合、この([^。]+)で([^。]+)された『([^』]+)』の([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦ACTION⟧して⟦TRIGGER⟧した場合、この⟦CONTEXT⟧で⟦PLACED⟧された『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
            "structure": "Baton touch specific card recovery",
        },

        # From: "自分のメインフェイズの間、自分のカードが1枚以上いずれかの領域から控え室に置かれるたび"
        {
            "name": "phase_based_trigger_on_card_discard",
            "regex": r"\b([^。]+)の([^。]+)の間、([^。]+)の([^。]+)が(\d+)枚以上([^。]+)の([^。]+)から([^。]+)に([^。]+)たび",
            "template": "⟦SOURCE⟧の⟦PHASE⟧の間、⟦OWNER⟧の⟦CARD_TYPE⟧が⟦NUMBER⟧枚以上⟦SOURCE2⟧の⟦ZONE⟧から⟦DESTINATION⟧に⟦ACTION⟧たび",
            "structure": "Phase based trigger on card discard",
        },

        # From: "そのカードの{{toujyou.png|登場}}能力1つを発動させる"
        {
            "name": "trigger_ability_activation",
            "regex": r"\b([^。]+)の(\{\\{[^}]+\}\})([^。]+)(\d+)つを([^。]+)させる",
            "template": "⟦CARD⟧の⟦TRIGGER⟧⟦ABILITY_TYPE⟧⟦NUMBER⟧つを⟦ACTION⟧させる",
            "structure": "Trigger ability activation",
        },

        # From: "自分のステージに「澁谷かのん」と「唐可可」がいる場合"
        {
            "name": "specific_member_pair_condition",
            "regex": r"\b([^。]+)の([^。]+)に「([^」]+)」と「([^」]+)」いる場合",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に「⟦MEMBER1⟧」と「⟦MEMBER2⟧」いる場合",
            "structure": "Specific member pair condition",
        },

        # From: "自分は、そのプレイヤーのデッキの一番上のカードを見る"
        {
            "name": "look_at_deck_top",
            "regex": r"\b([^。]+)は、その([^。]+)の([^。]+)の([^。]+)の([^。]+)を([^。]+)",
            "template": "⟦PLAYER⟧は、その⟦TARGET_PLAYER⟧の⟦ZONE⟧の⟦POSITION⟧の⟦CARD_TYPE⟧を⟦ACTION⟧",
            "structure": "Look at deck top",
        },

        # From: "自分のライブカード置き場に必要ハートの合計が8以上の『Liella!』のライブカードがあるかぎり"
        {
            "name": "live_card_heart_total_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)の([^。]+)が(\d+)以上の『([^』]+)』の([^。]+)あるかぎり",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦ATTRIBUTE⟧の⟦TOTAL⟧が⟦NUMBER⟧以上の『⟦GROUP⟧』の⟦CARD_TYPE⟧あるかぎり",
            "structure": "Live card heart total condition",
        },

        # From: "このメンバーはバトンタッチで控え室に置けない"
        {
            "name": "baton_touch_restriction",
            "regex": r"\b([^。]+)は([^。]+)で([^。]+)に([^。]+)ない",
            "template": "⟦MEMBER⟧は⟦ACTION⟧で⟦DESTINATION⟧に⟦NEGATION⟧ない",
            "structure": "Baton touch restriction",
        },

        # From: "このメンバーを今いるエリア以外のエリアに移動させる"
        {
            "name": "move_to_different_area",
            "regex": r"\b([^。]+)を([^。]+)いる([^。]+)以外の([^。]+)に([^。]+)させる",
            "template": "⟦TARGET⟧を⟦CURRENT⟧いる⟦ZONE1⟧以外の⟦ZONE2⟧に⟦ACTION⟧させる",
            "structure": "Move to different area",
        },

        # From: "そのエリアにメンバーがいる場合、そのメンバーはこのメンバーがいたエリアに移動させる"
        {
            "name": "swap_members",
            "regex": r"\bその([^。]+)に([^。]+)いる場合、その([^。]+)は([^。]+)の([^。]+)いた([^。]+)に([^。]+)させる",
            "template": "その⟦ZONE1⟧に⟦TARGET1⟧いる場合、その⟦TARGET1⟧は⟦TARGET2⟧の⟦MEMBER⟧いた⟦ZONE2⟧に⟦ACTION⟧させる",
            "structure": "Swap members",
        },

        # From: "そうした場合、そのライブカードを手札に加える"
        {
            "name": "conditional_card_add",
            "regex": r"\bそうした場合、その([^。]+)を([^。]+)に加える",
            "template": "そうした場合、その⟦CARD⟧を⟦DESTINATION⟧に加える",
            "structure": "Conditional card add",
        },

        # From: "{{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる"
        {
            "name": "ability_cost_payment_activation",
            "regex": r"\b(\{\\{[^}]+\}\})([^。]+)が([^。]+)を持つ場合、([^。]+)して([^。]+)させる",
            "template": "⟦TRIGGER⟧⟦ABILITY⟧が⟦COST⟧を持つ場合、⟦PAYMENT⟧して⟦ACTION⟧させる",
            "structure": "Ability cost payment activation",
        },

        # From: "自分のステージにいるメンバーのうち、センターエリアにいるメンバーが最も大きいコストを持つ場合"
        {
            "name": "highest_cost_member_condition",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)のうち、([^。]+)にいる([^。]+)が([^。]+)大きい([^。]+)を持つ場合",
            "template": "⟦SOURCE⟧の⟦ZONE1⟧いる⟦TARGET⟧のうち、⟦ZONE2⟧にいる⟦TARGET2⟧が⟦SUPERLATIVE⟧大きい⟦ATTRIBUTE⟧を持つ場合",
            "structure": "Highest cost member condition",
        },

        # From: "自分はそれらの中から「中須かすみ」のカードを1枚選ぶ"
        {
            "name": "select_specific_member_card",
            "regex": r"\b([^。]+)は([^。]+)の中から「([^」]+)」の([^。]+)を(\d+)枚選ぶ",
            "template": "⟦PLAYER⟧は⟦SOURCE⟧の中から「⟦MEMBER⟧」の⟦CARD_TYPE⟧を⟦NUMBER⟧枚選ぶ",
            "structure": "Select specific member card",
        },

        # From: "自分のステージにいる「中須かすみ」1人は、これにより選んだカードが持つ色のハートを1つずつ得る"
        {
            "name": "member_gains_hearts_from_selected_card_colors",
            "regex": r"\b([^。]+)の([^。]+)いる「([^」]+)」(\d+)人は、([^。]+)により([^。]+)([^。]+)が持つ([^。]+)の([^。]+)を(\d+)つずつ([^。]+)",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる「⟦MEMBER⟧」⟦NUMBER⟧人は、⟦CONTEXT⟧により⟦SELECTED⟧⟦CARD⟧が持つ⟦ATTRIBUTE⟧の⟦RESOURCE⟧を⟦NUMBER2⟧つずつ⟦ACTION⟧",
            "structure": "Member gains hearts from selected card colors",
        },

        # From: "公開したカードをすべて控え室に置く"
        {
            "name": "discard_all_revealed_cards",
            "regex": r"\b([^。]+)した([^。]+)をすべて([^。]+)に置く",
            "template": "⟦ACTION⟧した⟦CARD_TYPE⟧をすべて⟦DESTINATION⟧に置く",
            "structure": "Discard all revealed cards",
        },

        # From: "自分のエネルギー6枚につき、カードを1枚引く"
        {
            "name": "per_energy_draw",
            "regex": r"\b([^。]+)の([^。]+)(\d+)枚につき、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧の⟦RESOURCE⟧⟦NUMBER1⟧枚につき、⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦ACTION⟧",
            "structure": "Per energy draw",
        },

        # From: "【右サイド】エネルギーを2枚アクティブにする"
        {
            "name": "side_specific_energy_activation",
            "regex": r"\【([^】]+)】([^。]+)を(\d+)枚([^。]+)にする",
            "template": "【⟦SIDE⟧】⟦RESOURCE⟧を⟦NUMBER⟧枚⟦STATE⟧にする",
            "structure": "Side specific energy activation",
        },

        # From: "自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合"
        {
            "name": "dual_zone_card_count_condition",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)が(\d+)枚で、かつ([^。]+)の([^。]+)に([^。]+)が(\d+)枚以上ある場合",
            "template": "⟦SOURCE1⟧の⟦ZONE1⟧の⟦CARD_TYPE⟧が⟦NUMBER1⟧枚で、かつ⟦SOURCE2⟧の⟦ZONE2⟧に⟦CARD_TYPE2⟧が⟦NUMBER2⟧枚以上ある場合",
            "structure": "Dual zone card count condition",
        },

        # From: "自分のステージにいるメンバーが持つハートに{{heart_02.png|heart02}}が合計5つ以上ある場合、相手のライブ開始時、相手のライブカード置き場にあるライブカード1枚は、成功させるための必要ハートが{{heart_00.png|heart0}}多くなる"
        {
            "name": "heart_total_condition_opponent_phase_cost_increase",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)が持つ([^。]+)に([^。]+)が([^。]+)(\d+)つ以上ある場合、([^。]+)の([^。]+)、([^。]+)の([^。]+)にある([^。]+)(\d+)枚は、([^。]+)ための([^。]+)が([^。]+)多くなる",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が持つ⟦HEART_TYPE⟧に⟦RESOURCE⟧が⟦TOTAL⟧⟦NUMBER⟧つ以上ある場合、⟦OPPONENT⟧の⟦PHASE⟧、⟦OPPONENT⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧⟦NUMBER2⟧枚は、⟦CONTEXT⟧ための⟦COST⟧が⟦MODIFIER⟧多くなる",
            "structure": "Heart total condition opponent phase cost increase",
        },

        # From: "自分のデッキの一番上から4枚目に置いてもよい"
        {
            "name": "place_at_specific_deck_position",
            "regex": r"\b([^。]+)の([^。]+)から(\d+)枚目に([^。]+)てもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧から⟦POSITION⟧枚目に⟦ACTION⟧てもよい",
            "structure": "Place at specific deck position",
        },

        # From: "これにより控え室に置いたメンバーカードの{{toujyou.png|登場}}能力1つを発動させる"
        {
            "name": "placed_card_trigger_ability_activation",
            "regex": r"\b([^。]+)により([^。]+)に([^。]+)した([^。]+)の(\{\\{[^}]+\}\})([^。]+)(\d+)つを([^。]+)させる",
            "template": "⟦CONTEXT⟧により⟦ZONE⟧に⟦PLACED⟧した⟦CARD⟧の⟦TRIGGER⟧⟦ABILITY⟧⟦NUMBER⟧つを⟦ACTION⟧させる",
            "structure": "Placed card trigger ability activation",
        },

        # From: "自分のデッキの上から、自分と相手のステージにいるメンバー1人につき、1枚公開する"
        {
            "name": "per_member_reveal_from_deck",
            "regex": r"\b([^。]+)の([^。]+)から、([^。]+)と([^。]+)の([^。]+)いる([^。]+)(\d+)人につき、(\d+)枚([^。]+)する",
            "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦SOURCE1⟧と⟦SOURCE2⟧の⟦ZONE2⟧いる⟦TARGET⟧⟦NUMBER1⟧人につき、⟦NUMBER2⟧枚⟦ACTION⟧する",
            "structure": "Per member reveal from deck",
        },

        # From: "それらの中にあるライブカード1枚につき、このカードのスコアを+１する"
        {
            "name": "per_live_card_score_increase",
            "regex": r"\b([^。]+)の中にある([^。]+)(\d+)枚につき、([^。]+)の([^。]+)を([^。]+)する",
            "template": "⟦SOURCE⟧の中にある⟦CARD_TYPE⟧⟦NUMBER1⟧枚につき、⟦TARGET⟧の⟦ATTRIBUTE⟧を⟦MODIFICATION⟧する",
            "structure": "Per live card score increase",
        },

        # From: "デッキの上からカードを5枚控え室に置く"
        {
            "name": "deck_top_to_discard",
            "regex": r"\b([^。]+)の([^。]+)から([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦ZONE⟧の⟦POSITION⟧から⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置く",
            "structure": "Deck top to discard",
        },

        # From: "このカードを控え室からステージに登場させる"
        {
            "name": "summon_from_discard",
            "regex": r"\b([^。]+)を([^。]+)から([^。]+)に([^。]+)させる",
            "template": "⟦CARD⟧を⟦SOURCE⟧から⟦DESTINATION⟧に⟦ACTION⟧させる",
            "structure": "Summon from discard",
        },

        # From: "この能力は、このカードが控え室にある場合のみ起動できる"
        {
            "name": "ability_activation_location_restriction",
            "regex": r"\b([^。]+)は、([^。]+)が([^。]+)にある([^。]+)のみ([^。]+)できる",
            "template": "⟦ABILITY⟧は、⟦CARD⟧が⟦ZONE⟧にある⟦CONDITION⟧のみ⟦ACTION⟧できる",
            "structure": "Ability activation location restriction",
        },

        # From: "相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ"
        {
            "name": "select_specific_member_except",
            "regex": r"\b([^。]+)の([^。]+)いる「([^」]+)」以外の([^。]+)を(\d+)人選ぶ",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる「⟦MEMBER⟧」以外の⟦TARGET⟧を⟦NUMBER⟧人選ぶ",
            "structure": "Select specific member except",
        },

        # From: "そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合"
        {
            "name": "heart_color_comparison",
            "regex": r"\b([^。]+)が持つ([^。]+)と、([^。]+)が持つ([^。]+)の中に([^。]+)の([^。]+)がある場合",
            "template": "⟦MEMBER1⟧が持つ⟦HEART1⟧と、⟦MEMBER2⟧が持つ⟦HEART2⟧の中に⟦COMPARISON⟧の⟦COLOR⟧がある場合",
            "structure": "Heart color comparison",
        },

        # From: "それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う"
        {
            "name": "cost_and_blade_count_comparison",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)が([^。]+)場合、([^。]+)の([^。]+)の([^。]+)が([^。]+)場合についても([^。]+)を([^。]+)",
            "template": "⟦MEMBERS⟧の⟦ATTRIBUTE1⟧が⟦CONDITION1⟧場合、⟦MODIFIER⟧の⟦ATTRIBUTE2⟧の⟦ATTRIBUTE3⟧が⟦CONDITION2⟧場合についても⟦ACTION⟧を⟦PERFORM⟧",
            "structure": "Cost and blade count comparison",
        },

        # From: "ライブの合計スコアが相手より高い場合、カードを1枚引く"
        {
            "name": "live_score_comparison_draw",
            "regex": r"\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Live score comparison draw",
        },

        # From: "自分のステージにコスト10のメンバーが登場したとき"
        {
            "name": "specific_cost_member_appearance_trigger",
            "regex": r"\b([^。]+)の([^。]+)にコスト(\d+)の([^。]+)が([^。]+)したとき",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にコスト⟦COST⟧の⟦TARGET⟧が⟦ACTION⟧したとき",
            "structure": "Specific cost member appearance trigger",
        },

        # From: "このメンバーをウェイトにし、手札を1枚控え室に置く：カードを1枚引く"
        {
            "name": "wait_and_discard_then_draw",
            "regex": r"\b([^。]+)を([^。]+)し、([^。]+)を(\d+)枚([^。]+)に置く：([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦TARGET⟧を⟦STATE⟧し、⟦CARD1⟧を⟦NUMBER1⟧枚⟦ZONE⟧に置く：⟦CARD2⟧を⟦NUMBER2⟧枚⟦ACTION⟧",
            "structure": "Wait and discard then draw",
        },

        # From: "このメンバーがいるエリアとは別の自分のエリア1つを選ぶ"
        {
            "name": "select_different_area_from_member",
            "regex": r"\b([^。]+)いる([^。]+)とは([^。]+)の([^。]+)(\d+)つを選ぶ",
            "template": "⟦MEMBER⟧いる⟦ZONE1⟧とは⟦DIFFERENT⟧の⟦ZONE2⟧⟦NUMBER⟧つを選ぶ",
            "structure": "Select different area from member",
        },

        # From: "そうした場合、自分の控え室から、そのメンバーのコストに2を足した数に等しいコストの『Aqours』のメンバーカードを1枚、そのメンバーがいたエリアに登場させる"
        {
            "name": "cost_calculation_summon",
            "regex": r"\bそうした場合、([^。]+)の([^。]+)から、その([^。]+)の([^。]+)に(\d+)を([^。]+)した([^。]+)に([^。]+)コストの『([^』]+)』の([^。]+)を(\d+)枚、その([^。]+)いた([^。]+)に([^。]+)させる",
            "template": "そうした場合、⟦SOURCE⟧の⟦ZONE⟧から、その⟦MEMBER⟧の⟦ATTRIBUTE⟧に⟦NUMBER1⟧を⟦OPERATION⟧した⟦CALCULATED⟧に⟦EQUAL⟧コストの『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER2⟧枚、その⟦MEMBER2⟧いた⟦ZONE2⟧に⟦ACTION⟧させる",
            "structure": "Cost calculation summon",
        },

        # From: "（この能力はセンターエリアに登場している場合のみ起動できる"
        {
            "name": "area_restriction_ability_activation",
            "regex": r"\（([^。]+)は([^。]+)に([^。]+)している([^。]+)のみ([^。]+)できる",
            "template": "（⟦ABILITY⟧は⟦ZONE⟧に⟦STATE⟧している⟦CONDITION⟧のみ⟦ACTION⟧できる",
            "structure": "Area restriction ability activation",
        },

        # From: "メンバーを3人までウェイトにしてもよい：これによりウェイト状態にしたメンバー1人につき、カードを1枚引く"
        {
            "name": "per_member_wait_then_draw",
            "regex": r"\b([^。]+)を(\d+)人まで([^。]+)してもよい：これにより([^。]+)にした([^。]+)(\d+)人につき、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦TARGET⟧を⟦NUMBER1⟧人まで⟦STATE⟧してもよい：これにより⟦STATE2⟧にした⟦TARGET2⟧⟦NUMBER2⟧人につき、⟦CARD_TYPE⟧を⟦NUMBER3⟧枚⟦ACTION⟧",
            "structure": "Per member wait then draw",
        },

        # From: "エネルギーを2枚アクティブにする"
        {
            "name": "energy_activation",
            "regex": r"\b([^。]+)を(\d+)枚([^。]+)にする",
            "template": "⟦RESOURCE⟧を⟦NUMBER⟧枚⟦STATE⟧にする",
            "structure": "Energy activation",
        },

        # From: "手札からコスト4以下の「ミア・テイラー」のメンバーカードを1枚ステージに登場させる"
        {
            "name": "hand_specific_member_summon",
            "regex": r"\b([^。]+)からコスト(\d+)以下の「([^」]+)」の([^。]+)を(\d+)枚([^。]+)に([^。]+)させる",
            "template": "⟦SOURCE⟧からコスト⟦COST⟧以下の「⟦MEMBER⟧」の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧させる",
            "structure": "Hand specific member summon",
        },

        # From: "相手のステージにウェイト状態のメンバーが2人以上いるかぎり"
        {
            "name": "opponent_wait_member_count_condition",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)の([^。]+)が(\d+)人以上いるかぎり",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の⟦TARGET⟧が⟦NUMBER⟧人以上いるかぎり",
            "structure": "Opponent wait member count condition",
        },

        # From: "自分のステージにいるメンバーの{{live_success.png|ライブ成功時}}能力が解決するたび、カードを1枚引く"
        {
            "name": "ability_resolution_trigger",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の(\{\\{[^}]+\}\})([^。]+)が([^。]+)たび、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧の⟦TRIGGER⟧⟦ABILITY⟧が⟦ACTION⟧たび、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DRAW⟧",
            "structure": "Ability resolution trigger",
        },

        # From: "その中から『虹ヶ咲』のライブカードを1枚まで公開して手札に加えてもよい"
        {
            "name": "select_specific_group_live_card_optional",
            "regex": r"\bその中から『([^』]+)』の([^。]+)を(\d+)枚まで([^。]+)して([^。]+)に加えてもよい",
            "template": "その中から『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚まで⟦ACTION⟧して⟦DESTINATION⟧に加えてもよい",
            "structure": "Select specific group live card optional",
        },

        # From: "そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く"
        {
            "name": "conditional_group_live_card_placement",
            "regex": r"\bそうした場合、([^。]+)の([^。]+)にある『([^』]+)』の([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "そうした場合、⟦SOURCE⟧の⟦ZONE⟧にある『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に置く",
            "structure": "Conditional group live card placement",
        },

        # From: "ライブ終了時まで、自分はライブできない"
        {
            "name": "temporary_live_prevention",
            "regex": r"\b([^。]+)まで、([^。]+)は([^。]+)できない",
            "template": "⟦TIME⟧まで、⟦PLAYER⟧は⟦ACTION⟧できない",
            "structure": "Temporary live prevention",
        },

        # From: "（この能力は左サイドエリアか右サイドエリアに登場した場合のみ発動する"
        {
            "name": "side_area_activation_restriction",
            "regex": r"\（([^。]+)は([^。]+)か([^。]+)に([^。]+)した([^。]+)のみ([^。]+)する",
            "template": "（⟦ABILITY⟧は⟦ZONE1⟧か⟦ZONE2⟧に⟦ACTION⟧した⟦CONDITION⟧のみ⟦ACTIVATE⟧する",
            "structure": "Side area activation restriction",
        },

        # From: "({{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。)"
        {
            "name": "parenthesized_ability_cost_activation",
            "regex": r"\((\{\\{[^}]+\}\})([^。]+)が([^。]+)を持つ場合、([^。]+)して([^。]+)させる。",
            "template": "(⟦TRIGGER⟧⟦ABILITY⟧が⟦COST⟧を持つ場合、⟦PAYMENT⟧して⟦ACTION⟧させる。",
            "structure": "Parenthesized ability cost activation",
        },

        # From: "（{{toujyou.png|登場}}能力がコストを持つ場合、支払って発動させる。）"
        {
            "name": "parenthesized_japanese_ability_cost_activation",
            "regex": r"\（(\{\\{[^}]+\}\})([^。]+)が([^。]+)を持つ場合、([^。]+)して([^。]+)させる。）",
            "template": "（⟦TRIGGER⟧⟦ABILITY⟧が⟦COST⟧を持つ場合、⟦PAYMENT⟧して⟦ACTION⟧させる。）",
            "structure": "Parenthesized japanese ability cost activation",
        },

        # From: "ステージの左サイドエリアに登場しているなら、カードを2枚引く"
        {
            "name": "area_specific_appearance_condition_draw",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)しているなら、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦ZONE⟧の⟦AREA⟧に⟦STATE⟧しているなら、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Area specific appearance condition draw",
        },

        # From: "それらがすべてメンバーカードの場合、カードを1枚引く"
        {
            "name": "all_cards_type_condition_draw",
            "regex": r"\b([^。]+)が([^。]+)([^。]+)の場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦THEY⟧が⟦ALL⟧⟦CARD_TYPE⟧の場合、⟦CARD_TYPE2⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "All cards type condition draw",
        },

        # From: "相手のステージにいるウェイト状態のメンバー1人につき、{{icon_blade.png|ブレード}}を得る"
        {
            "name": "opponent_wait_member_per_member_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)(\d+)人につき、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧⟦NUMBER⟧人につき、⟦RESOURCE⟧を得る",
            "structure": "Opponent wait member per member resource gain",
        },

        # From: "そのライブカードを手札に加え、これにより公開されたほかのすべてのカードを控え室に置く"
        {
            "name": "conditional_card_add_and_discard_others",
            "regex": r"\bその([^。]+)を([^。]+)に加え、([^。]+)により([^。]+)された([^。]+)すべての([^。]+)を([^。]+)に置く",
            "template": "その⟦CARD⟧を⟦DESTINATION⟧に加え、⟦CONTEXT⟧により⟦REVEALED⟧された⟦OTHER⟧すべての⟦CARD_TYPE⟧を⟦DESTINATION2⟧に置く",
            "structure": "Conditional card add and discard others",
        },

        # From: "自分のステージにいる『DOLLCHESTRA』のメンバー1人を選ぶ。ライブ終了時まで、このメンバーのコストは、選んだメンバーが元々持つコストより1低い値に等しくなる"
        {
            "name": "select_member_and_cost_modification",
            "regex": r"\b([^。]+)の([^。]+)いる『([^』]+)』の([^。]+)(\d+)人を選ぶ。([^。]+)まで、([^。]+)の([^。]+)は、([^。]+)([^。]+)が([^。]+)持つ([^。]+)より(\d+)低い([^。]+)に([^。]+)なる",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER1⟧人を選ぶ。⟦TIME⟧まで、⟦MEMBER⟧の⟦ATTRIBUTE⟧は、⟦SELECTED⟧⟦MEMBER2⟧が⟦ORIGINAL⟧持つ⟦COST⟧より⟦NUMBER2⟧低い⟦VALUE⟧に⟦EQUAL⟧なる",
            "structure": "Select member and cost modification",
        },

        # From: "自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る"
        {
            "name": "score_based_card_reveal",
            "regex": r"\b([^。]+)の([^。]+)から、([^。]+)の([^。]+)の([^。]+)に(\d+)を([^。]+)した([^。]+)に等しい([^。]+)見る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧から、⟦SOURCE2⟧の⟦LIVE⟧の⟦ATTRIBUTE1⟧に⟦NUMBER⟧を⟦OPERATION⟧した⟦CALCULATED⟧に等しい⟦COUNT⟧見る",
            "structure": "Score based card reveal",
        },

        # From: "その中から各グループ名につき1枚ずつ公開し、3枚まで手札に加えてもよい"
        {
            "name": "per_group_reveal",
            "regex": r"\bその中から([^。]+)([^。]+)につき(\d+)枚ずつ([^。]+)し、(\d+)枚まで([^。]+)に加えてもよい",
            "template": "その中から⟦EACH⟧⟦ATTRIBUTE⟧につき⟦NUMBER1⟧枚ずつ⟦ACTION⟧し、⟦NUMBER2⟧枚まで⟦DESTINATION⟧に加えてもよい",
            "structure": "Per group reveal",
        },

        # From: "自分のステージにいるメンバー1人の下にあるエネルギーカードを、好きな枚数エネルギーデッキに置いてもよい"
        {
            "name": "optional_energy_placement_from_member",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)(\d+)人の([^。]+)にある([^。]+)を、([^。]+)([^。]+)([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧⟦NUMBER⟧人の⟦LOCATION⟧にある⟦CARD_TYPE⟧を、⟦ANY⟧⟦COUNT⟧⟦DESTINATION⟧に置いてもよい",
            "structure": "Optional energy placement from member",
        },

        # From: "自分のステージにいるメンバーがちょうど2人であるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "exact_member_count_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)が([^。]+)(\d+)人であるかぎり、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧が⟦EXACT⟧⟦NUMBER⟧人であるかぎり、⟦RESOURCE⟧を得る",
            "structure": "Exact member count condition resource gain",
        },

        # From: "自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "dual_zone_card_count_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)が(\d+)枚で、かつ([^。]+)の([^。]+)に([^。]+)が(\d+)枚以上ある場合、([^。]+)を得る",
            "template": "⟦SOURCE1⟧の⟦ZONE1⟧の⟦CARD_TYPE⟧が⟦NUMBER1⟧枚で、かつ⟦SOURCE2⟧の⟦ZONE2⟧に⟦CARD_TYPE2⟧が⟦NUMBER2⟧枚以上ある場合、⟦RESOURCE⟧を得る",
            "structure": "Dual zone card count condition resource gain",
        },

        # From: "自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、{{heart_05.png|heart05}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "distinct_cost_member_count_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)([^。]+)が([^。]+)([^。]+)の([^。]+)が(\d+)人以上いるかぎり、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦ZONE⟧⟦ATTRIBUTE⟧が⟦DISTINCT⟧⟦MODIFIER⟧の⟦TARGET⟧が⟦NUMBER⟧人以上いるかぎり、⟦RESOURCE⟧を得る",
            "structure": "Distinct cost member count condition resource gain",
        },

        # From: "自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる"
        {
            "name": "cost_total_condition_summon",
            "regex": r"\b([^。]+)から、([^。]+)の([^。]+)が(\d+)以下になるように([^。]+)を(\d+)枚まで([^。]+)に([^。]+)させる",
            "template": "⟦SOURCE⟧から、⟦ATTRIBUTE⟧の⟦TOTAL⟧が⟦NUMBER1⟧以下になるように⟦CARD_TYPE⟧を⟦NUMBER2⟧枚まで⟦DESTINATION⟧に⟦ACTION⟧させる",
            "structure": "Cost total condition summon",
        },

        # From: "自分のエネルギーが相手より多いかぎり、{{heart_06.png|heart06}}を得る"
        {
            "name": "energy_comparison_condition_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)が([^。]+)より([^。]+)かぎり、([^。]+)を得る",
            "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧かぎり、⟦RESOURCE2⟧を得る",
            "structure": "Energy comparison condition resource gain",
        },

        # From: "自分が余剰ハートに{{heart_01.png|heart01}}を1つ以上持つ場合、カードを1枚引く"
        {
            "name": "surplus_heart_condition_draw",
            "regex": r"\b([^。]+)が([^。]+)に([^。]+)を(\d+)つ以上持つ場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦SOURCE⟧が⟦ZONE⟧に⟦RESOURCE⟧を⟦NUMBER1⟧つ以上持つ場合、⟦CARD_TYPE⟧を⟦NUMBER2⟧枚⟦ACTION⟧",
            "structure": "Surplus heart condition draw",
        },

        # From: "自分は、そのプレイヤーの控え室にあるライブカードを1枚、そのプレイヤーのデッキの一番下に置く"
        {
            "name": "player_selection_card_placement",
            "regex": r"\b([^。]+)は、その([^。]+)の([^。]+)にある([^。]+)を(\d+)枚、その([^。]+)の([^。]+)の([^。]+)に置く",
            "template": "⟦PLAYER⟧は、その⟦TARGET_PLAYER⟧の⟦ZONE⟧にある⟦CARD_TYPE⟧を⟦NUMBER⟧枚、その⟦TARGET_PLAYER2⟧の⟦ZONE2⟧の⟦POSITION⟧に置く",
            "structure": "Player selection card placement",
        },

        # From: "ライブの合計スコアが相手より高い場合、このカードを手札に加えてもよい"
        {
            "name": "live_score_comparison_card_add_optional",
            "regex": r"\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合、([^。]+)を([^。]+)に加えてもよい",
            "template": "⟦SOURCE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合、⟦CARD⟧を⟦DESTINATION⟧に加えてもよい",
            "structure": "Live score comparison card add optional",
        },

        # From: "メンバーの下に置かれているエネルギーカードではコストを支払えない"
        {
            "name": "member_under_energy_cost_restriction",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)いる([^。]+)では([^。]+)を([^。]+)ない",
            "template": "⟦MEMBER⟧の⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧では⟦COST⟧を⟦PAYMENT⟧ない",
            "structure": "Member under energy cost restriction",
        },

        # From: "メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く"
        {
            "name": "member_leave_energy_return",
            "regex": r"\b([^。]+)が([^。]+)から([^。]+)とき、([^。]+)に([^。]+)いる([^。]+)は([^。]+)に置く",
            "template": "⟦MEMBER⟧が⟦ZONE⟧から⟦ACTION⟧とき、⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧は⟦DESTINATION⟧に置く",
            "structure": "Member leave energy return",
        },

        # From: "（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない"
        {
            "name": "area_placement_turn_restriction",
            "regex": r"\（([^。]+)で([^。]+)した([^。]+)の([^。]+)([^。]+)には、この([^。]+)に([^。]+)は([^。]+)できない",
            "template": "（⟦EFFECT⟧で⟦SUMMONED⟧した⟦MEMBER⟧の⟦AREA⟧⟦LOCATION⟧には、この⟦TURN⟧に⟦MEMBER2⟧は⟦ACTION⟧できない",
            "structure": "Area placement turn restriction",
        },

        # From: "これにより置いた枚数分カードを引く"
        {
            "name": "per_discarded_card_draw",
            "regex": r"\b([^。]+)により([^。]+)した([^。]+)([^。]+)を([^。]+)",
            "template": "⟦CONTEXT⟧により⟦PLACED⟧した⟦COUNT⟧⟦ACTION⟧を⟦DRAW⟧",
            "structure": "Per discarded card draw",
        },

        # From: "これにより登場したメンバーがブレードハートを持つ場合、このメンバーをウェイトにする"
        {
            "name": "summoned_member_condition_wait",
            "regex": r"\b([^。]+)により([^。]+)した([^。]+)が([^。]+)を持つ場合、([^。]+)を([^。]+)にする",
            "template": "⟦CONTEXT⟧により⟦SUMMONED⟧した⟦MEMBER⟧が⟦ATTRIBUTE⟧を持つ場合、⟦TARGET⟧を⟦STATE⟧にする",
            "structure": "Summoned member condition wait",
        },

        # From: "自分と相手はそれぞれ、自身の控え室からコスト2以下のメンバーカードを1枚、メンバーのいないエリアにウェイト状態で登場させる"
        {
            "name": "both_players_summon",
            "regex": r"\b([^。]+)と([^。]+)は([^。]+)、([^。]+)の([^。]+)からコスト(\d+)以下の([^。]+)を(\d+)枚、([^。]+)の([^。]+)([^。]+)に([^。]+)で([^。]+)させる",
            "template": "⟦PLAYER1⟧と⟦PLAYER2⟧は⟦EACH⟧、⟦SELF⟧の⟦ZONE⟧からコスト⟦COST⟧以下の⟦CARD_TYPE⟧を⟦NUMBER⟧枚、⟦MEMBER⟧の⟦CONDITION⟧⟦AREA⟧に⟦STATE⟧で⟦ACTION⟧させる",
            "structure": "Both players summon",
        },

        # From: "このメンバーがウェイト状態であるかぎり、{{heart_05.png|heart05}}を得る"
        {
            "name": "member_state_condition_resource_gain",
            "regex": r"\b([^。]+)が([^。]+)であるかぎり、([^。]+)を得る",
            "template": "⟦MEMBER⟧が⟦STATE⟧であるかぎり、⟦RESOURCE⟧を得る",
            "structure": "Member state condition resource gain",
        },

        # From: "自分の手札からコスト4以下の『虹ヶ咲』のメンバーカードを1枚ステージに登場させる"
        {
            "name": "hand_specific_group_member_summon",
            "regex": r"\b([^。]+)からコスト(\d+)以下の『([^』]+)』の([^。]+)を(\d+)枚([^。]+)に([^。]+)させる",
            "template": "⟦SOURCE⟧からコスト⟦COST⟧以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に⟦ACTION⟧させる",
            "structure": "Hand specific group member summon",
        },

        # From: "センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはセンターエリアに移動させる"
        {
            "name": "center_member_position_change",
            "regex": r"\b([^。]+)いる([^。]+)を([^。]+)いる([^。]+)以外の([^。]+)に([^。]+)させる。その([^。]+)に([^。]+)いる場合、その([^。]+)は([^。]+)に([^。]+)させる",
            "template": "⟦ZONE⟧いる⟦TARGET⟧を⟦CURRENT⟧いる⟦AREA⟧以外の⟦ZONE2⟧に⟦ACTION⟧させる。その⟦ZONE3⟧に⟦TARGET2⟧いる場合、その⟦TARGET2⟧は⟦DESTINATION⟧に⟦ACTION2⟧させる",
            "structure": "Center member position change",
        },

        # From: "これによりライブカードを控え室に置いた場合、さらにカードを1枚引く"
        {
            "name": "conditional_live_card_discard_draw",
            "regex": r"\b([^。]+)により([^。]+)を([^。]+)に([^。]+)した場合、さらに([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦CONTEXT⟧により⟦CARD⟧を⟦DESTINATION⟧に⟦PLACED⟧した場合、さらに⟦CARD2⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Conditional live card discard draw",
        },

        # From: "相手に何が好き？と聞く。"
        {
            "name": "ask_question",
            "regex": r"\b([^。]+)に([^。]+)と聞く。",
            "template": "⟦TARGET⟧に⟦QUESTION⟧と聞く。",
            "structure": "Ask question",
        },

        # From: "エールによって公開される自分のカードの枚数が8枚減る"
        {
            "name": "reveal_count_reduction",
            "regex": r"\b([^。]+)によって([^。]+)される([^。]+)の([^。]+)の([^。]+)が(\d+)枚([^。]+)",
            "template": "⟦CONTEXT⟧によって⟦REVEALED⟧される⟦SOURCE⟧の⟦CARD⟧の⟦COUNT⟧が⟦NUMBER⟧枚⟦REDUCTION⟧",
            "structure": "Reveal count reduction",
        },

        # From: "カードを1枚引く"
        {
            "name": "simple_draw_card",
            "regex": r"\b([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Simple draw card",
        },

        # From: "相手のステージにいるウェイト状態のメンバーの数まで、自分の控え室にある『虹ヶ咲』のメンバーカードを選ぶ"
        {
            "name": "wait_member_count_selection",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)の([^。]+)の([^。]+)まで、([^。]+)の([^。]+)にある『([^』]+)』の([^。]+)を選ぶ",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦STATE⟧の⟦TARGET⟧の⟦COUNT⟧まで、⟦SOURCE2⟧の⟦ZONE2⟧にある『⟦GROUP⟧』の⟦CARD_TYPE⟧を選ぶ",
            "structure": "Wait member count selection",
        },

        # From: "それらを好きな順番でデッキの上に置く"
        {
            "name": "place_in_any_order_on_deck",
            "regex": r"\b([^。]+)を([^。]+)の([^。]+)で([^。]+)の([^。]+)に置く",
            "template": "⟦THEY⟧を⟦ANY⟧の⟦ORDER⟧で⟦ZONE⟧の⟦POSITION⟧に置く",
            "structure": "Place in any order on deck",
        },

        # From: "自分のステージにいる{{heart_01.png|heart01}}と{{heart_06.png|heart06}}以外の色のハートを持つメンバー1人につき、このカードの必要ハートを{{heart_00.png|heart0}}減らす"
        {
            "name": "heart_color_exception_per_member_cost_reduction",
            "regex": r"\b([^。]+)の([^。]+)いる([^。]+)と([^。]+)以外の([^。]+)の([^。]+)を持つ([^。]+)(\d+)人につき、([^。]+)の([^。]+)を([^。]+)([^。]+)",
            "template": "⟦SOURCE⟧の⟦ZONE⟧いる⟦HEART1⟧と⟦HEART2⟧以外の⟦COLOR⟧の⟦HEART⟧を持つ⟦TARGET⟧⟦NUMBER⟧人につき、⟦CARD⟧の⟦COST⟧を⟦MODIFIER⟧⟦ACTION⟧",
            "structure": "Heart color exception per member cost reduction",
        },

        # From: "このメンバーがエリアを移動するたび、カードを1枚引く"
        {
            "name": "member_movement_trigger_draw",
            "regex": r"\b([^。]+)が([^。]+)を([^。]+)するたび、([^。]+)を(\d+)枚([^。]+)",
            "template": "⟦MEMBER⟧が⟦ZONE⟧を⟦ACTION⟧するたび、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DRAW⟧",
            "structure": "Member movement trigger draw",
        },

        # From: "その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く"
        {
            "name": "then_opponent_wait_member_condition_draw",
            "regex": r"\bその後、([^。]+)の([^。]+)に([^。]+)の([^。]+)いる場合、([^。]+)を(\d+)枚([^。]+)",
            "template": "その後、⟦SOURCE⟧の⟦ZONE⟧に⟦STATE⟧の⟦TARGET⟧いる場合、⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦ACTION⟧",
            "structure": "Then opponent wait member condition draw",
        },

        # From: "このメンバーの下にあるエネルギーカード1枚につき、{{icon_blade.png|ブレード}}を得る"
        {
            "name": "member_under_energy_per_energy_resource_gain",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)(\d+)枚につき、([^。]+)を得る",
            "template": "⟦MEMBER⟧の⟦LOCATION⟧にある⟦CARD_TYPE⟧⟦NUMBER⟧枚につき、⟦RESOURCE⟧を得る",
            "structure": "Member under energy per energy resource gain",
        },

        # From: "・このカードの必要ハートを{{heart_06.png|heart06}}減らす。"
        {
            "name": "bullet_point_cost_reduction",
            "regex": r"\・([^。]+)の([^。]+)を([^。]+)([^。]+)",
            "template": "・⟦CARD⟧の⟦COST⟧を⟦MODIFIER⟧⟦ACTION⟧",
            "structure": "Bullet point cost reduction",
        },

        # From: "・自分のステージにいる『SaintSnow』のメンバー1人をポジションチェンジさせる。"
        {
            "name": "bullet_position_change",
            "regex": r"\・([^。]+)の([^。]+)いる『([^』]+)』の([^。]+)(\d+)人を([^。]+)させる。",
            "template": "・⟦SOURCE⟧の⟦ZONE⟧いる『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER⟧人を⟦ACTION⟧させる。",
            "structure": "Bullet position change",
        },

        # From: "選んだハートを1つ得る"
        {
            "name": "selected_resource_gain",
            "regex": r"\b([^。]+)([^。]+)を(\d+)つ得る",
            "template": "⟦SELECTED⟧⟦RESOURCE⟧を⟦NUMBER⟧つ得る",
            "structure": "Selected resource gain",
        },

        # From: "自分はそのカードを控え室に置いてもよい"
        {
            "name": "optional_card_discard",
            "regex": r"\b([^。]+)はその([^。]+)を([^。]+)に置いてもよい",
            "template": "⟦PLAYER⟧はその⟦CARD⟧を⟦DESTINATION⟧に置いてもよい",
            "structure": "Optional card discard",
        },

        # From: "そのメンバーが持つ{{heart_03.png|heart03}}2つにつき、このカードの必要ハートを{{heart_00.png|heart0}}減らす"
        {
            "name": "per_heart_cost_reduction",
            "regex": r"\bその([^。]+)が持つ([^。]+)(\d+)つにつき、([^。]+)の([^。]+)を([^。]+)([^。]+)",
            "template": "その⟦MEMBER⟧が持つ⟦RESOURCE⟧⟦NUMBER1⟧つにつき、⟦CARD⟧の⟦COST⟧を⟦MODIFIER⟧⟦ACTION⟧",
            "structure": "Per heart cost reduction",
        },

        # From: "そのエールで得たブレードハートを失い、もう一度エールを行う"
        {
            "name": "lose_resource_and_retry",
            "regex": r"\bその([^。]+)で([^。]+)([^。]+)を([^。]+)、もう一度([^。]+)を([^。]+)",
            "template": "その⟦CONTEXT⟧で⟦GAINED⟧⟦RESOURCE⟧を⟦LOSE⟧、もう一度⟦ACTION⟧を⟦PERFORM⟧",
            "structure": "Lose resource and retry",
        },

        # From: "この効果ではライブの合計スコアは０未満にはならない"
        {
            "name": "score_floor_restriction",
            "regex": r"\b([^。]+)では([^。]+)の([^。]+)は(\d+)未満には([^。]+)ない",
            "template": "⟦EFFECT⟧では⟦LIVE⟧の⟦SCORE⟧は⟦NUMBER⟧未満には⟦NEGATION⟧ない",
            "structure": "Score floor restriction",
        },

        # From: "6枚以上ある場合、代わりにスコアを+２する"
        {
            "name": "alternative_condition_score_increase",
            "regex": r"\b(\d+)枚以上ある場合、([^。]+)に([^。]+)を([^。]+)する",
            "template": "⟦NUMBER1⟧枚以上ある場合、⟦ALTERNATIVE⟧に⟦SCORE⟧を⟦MODIFIER⟧する",
            "structure": "Alternative condition score increase",
        },

        # From: "{{center.png|センター}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}{{heart_03.png|heart03}}を得る"
        {
            "name": "position_resource_gain",
            "regex": r"\b(\{\\{[^}]+\}\})([^。]+)を得る",
            "template": "⟦POSITION⟧⟦RESOURCE⟧を得る",
            "structure": "Position resource gain",
        },

        # From: "ライブカードが3枚以上ある場合、代わりに合計スコアを+２する"
        {
            "name": "alternative_condition_total_score_increase",
            "regex": r"\b([^。]+)が(\d+)枚以上ある場合、([^。]+)に([^。]+)を([^。]+)する",
            "template": "⟦CARD⟧が⟦NUMBER1⟧枚以上ある場合、⟦ALTERNATIVE⟧に⟦SCORE⟧を⟦MODIFIER⟧する",
            "structure": "Alternative condition total score increase",
        },

        # From: "この能力を起動するためのコストは自分のステージにいるメンバーの中のグループ名1種類につき、{{icon_energy.png|E}}減る"
        {
            "name": "per_group_cost_reduction",
            "regex": r"\b([^。]+)を([^。]+)するための([^。]+)は([^。]+)の([^。]+)いる([^。]+)の中の([^。]+)(\d+)種類につき、([^。]+)([^。]+)",
            "template": "⟦ABILITY⟧を⟦ACTION⟧するための⟦COST⟧は⟦SOURCE⟧の⟦ZONE⟧いる⟦TARGET⟧の中の⟦ATTRIBUTE⟧⟦NUMBER⟧種類につき、⟦RESOURCE⟧⟦REDUCTION⟧",
            "structure": "Per group cost reduction",
        },

        # From: "そのカードの{{toujyou.png|登場}}能力1つを発動させる"
        {
            "name": "card_trigger_ability_activation",
            "regex": r"\bその([^。]+)の(\{\\{[^}]+\})(\{\\{[^}]+\})(\d+)つを([^。]+)させる",
            "template": "その⟦CARD⟧の⟦ICON1⟧⟦ICON2⟧⟦NUMBER⟧つを⟦ACTION⟧させる",
            "structure": "Card trigger ability activation",
        },

        # From: "このメンバーが元々持つハートは選んだハートになる"
        {
            "name": "original_heart_replacement",
            "regex": r"\b([^。]+)が([^。]+)持つ([^。]+)は([^。]+)([^。]+)になる",
            "template": "⟦MEMBER⟧が⟦ORIGINAL⟧持つ⟦HEART⟧は⟦SELECTED⟧⟦HEART2⟧になる",
            "structure": "Original heart replacement",
        },

        # From: "この能力では{{heart_00.png|heart0}}は3つまでしか減らない"
        {
            "name": "ability_limitation",
            "regex": r"\b([^。]+)では([^。]+)は(\d+)つまでしか([^。]+)ない",
            "template": "⟦ABILITY⟧では⟦RESOURCE⟧は⟦NUMBER⟧つまでしか⟦LIMITATION⟧ない",
            "structure": "Ability limitation",
        },

        # From: "（メンバーの下に置かれているエネルギーカードではコストを支払えない"
        {
            "name": "parenthesized_energy_cost_restriction",
            "regex": r"\（([^。]+)の([^。]+)に([^。]+)いる([^。]+)では([^。]+)を([^。]+)ない",
            "template": "（⟦MEMBER⟧の⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧では⟦COST⟧を⟦PAYMENT⟧ない",
            "structure": "Parenthesized energy cost restriction",
        },

        # From: "メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに置く"
        {
            "name": "parenthesized_member_leave_energy_return",
            "regex": r"\（([^。]+)が([^。]+)から([^。]+)とき、([^。]+)に([^。]+)いる([^。]+)は([^。]+)に置く",
            "template": "（⟦MEMBER⟧が⟦ZONE⟧から⟦ACTION⟧とき、⟦LOCATION⟧に⟦PLACED⟧いる⟦CARD_TYPE⟧は⟦DESTINATION⟧に置く",
            "structure": "Parenthesized member leave energy return",
        },

        # From: "（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない"
        {
            "name": "parenthesized_area_placement_turn_restriction",
            "regex": r"\（([^。]+)で([^。]+)した([^。]+)の([^。]+)([^。]+)には、この([^。]+)に([^。]+)は([^。]+)できない",
            "template": "（⟦EFFECT⟧で⟦SUMMONED⟧した⟦MEMBER⟧の⟦AREA⟧⟦LOCATION⟧には、この⟦TURN⟧に⟦MEMBER2⟧は⟦ACTION⟧できない",
            "structure": "Parenthesized area placement turn restriction",
        },

        # From: "（メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない"
        {
            "name": "parenthesized_formation_change_restriction",
            "regex": r"\（([^。]+)を([^。]+)([^。]+)の([^。]+)に([^。]+)させる。([^。]+)で([^。]+)の([^。]+)に(\d+)人以上の([^。]+)を([^。]+)させることはできない",
            "template": "（⟦MEMBERS⟧を⟦EACH⟧⟦ANY⟧の⟦AREA⟧に⟦MOVE⟧させる。⟦EFFECT⟧で⟦AREA2⟧の⟦ZONE⟧に⟦NUMBER⟧人以上の⟦MEMBER2⟧を⟦ACTION⟧させることはできない",
            "structure": "Parenthesized formation change restriction",
        },

        # From: "（センターにいるメンバーを今いるエリア以外のエリアに移動させる。そのエリアにメンバーがいる場合、そのメンバーはセンターエリアに移動させる"
        {
            "name": "parenthesized_center_member_position_change",
            "regex": r"\（([^。]+)いる([^。]+)を([^。]+)いる([^。]+)以外の([^。]+)に([^。]+)させる。その([^。]+)に([^。]+)いる場合、その([^。]+)は([^。]+)に([^。]+)させる",
            "template": "（⟦ZONE⟧いる⟦TARGET⟧を⟦CURRENT⟧いる⟦AREA⟧以外の⟦ZONE2⟧に⟦ACTION⟧させる。その⟦ZONE3⟧に⟦TARGET2⟧いる場合、その⟦TARGET2⟧は⟦DESTINATION⟧に⟦ACTION2⟧させる",
            "structure": "Parenthesized center member position change",
        },

        # From: "（この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない"
        {
            "name": "parenthesized_effect_area_turn_restriction",
            "regex": r"\（([^。]+)で([^。]+)した([^。]+)の([^。]+)には、この([^。]+)に([^。]+)は([^。]+)できない",
            "template": "（⟦EFFECT⟧で⟦SUMMONED⟧した⟦MEMBER⟧の⟦AREA⟧には、この⟦TURN⟧に⟦MEMBER2⟧は⟦ACTION⟧できない",
            "structure": "Parenthesized effect area turn restriction",
        },

        # From: "（この能力は左サイドエリアにいる場合のみ発動する"
        {
            "name": "side_area_activation",
            "regex": r"\（([^。]+)は([^。]+)に([^。]+)場合のみ([^。]+)する",
            "template": "（⟦ABILITY⟧は⟦ZONE⟧に⟦CONDITION⟧場合のみ⟦ACTION⟧する",
            "structure": "Side area activation",
        },

        # From: "それ以外の場合、公開したカードを控え室に置く"
        {
            "name": "else_condition_discard",
            "regex": r"\b([^。]+)の場合、([^。]+)を([^。]+)に置く",
            "template": "⟦OTHERWISE⟧場合、⟦CARD⟧を⟦DESTINATION⟧に置く",
            "structure": "Else condition discard",
        },

        # From: "自分のデッキの一番上のカードを控え室に置いてもよい"
        {
            "name": "optional_deck_top_discard",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)の([^。]+)を([^。]+)に置いてもよい",
            "template": "⟦SOURCE⟧の⟦ZONE⟧の⟦POSITION⟧の⟦CARD⟧を⟦DESTINATION⟧に置いてもよい",
            "structure": "Optional deck top discard",
        },

        # From: "(相手のカードの効果でも発動する"
        {
            "name": "opponent_effect_activation",
            "regex": r"\(相手の([^。]+)の([^。]+)でも([^。]+)する",
            "template": "(相手の⟦CARD⟧の⟦EFFECT⟧でも⟦ACTION⟧する",
            "structure": "Opponent effect activation",
        },

        # From: "その中から1枚を手札に加える"
        {
            "name": "select_one_from_revealed",
            "regex": r"\bその中から(\d+)枚を([^。]+)に([^。]+)する",
            "template": "その中から⟦NUMBER⟧枚を⟦DESTINATION⟧に⟦ACTION⟧する",
            "structure": "Select one from revealed",
        },

        # From: "代わりに1つ以上を選ぶ"
        {
            "name": "alternative_selection_count",
            "regex": r"\b([^。]+)に(\d+)つ以上を([^。]+)",
            "template": "⟦ALTERNATIVE⟧に⟦NUMBER⟧つ以上を⟦SELECT⟧",
            "structure": "Alternative selection count",
        },

        # From: "」を得る"
        {
            "name": "quoted_ability_gain",
            "regex": r"\」を([^。]+)",
            "template": "」を⟦ACTION⟧",
            "structure": "Quoted ability gain",
        },

        # From: "、{{icon_all.png|ハート}}を得る"
        {
            "name": "condition_resource_gain_simple",
            "regex": r"、([^。]+)を([^。]+)",
            "template": "、⟦RESOURCE⟧を⟦ACTION⟧",
            "structure": "Condition resource gain simple",
        },

        # From: "自分はこの手順をさらに4回まで繰り返してもよい"
        {
            "name": "repeat_procedure",
            "regex": r"\b([^。]+)はこの([^。]+)をさらに(\d+)回まで([^。]+)してもよい",
            "template": "⟦PLAYER⟧はこの⟦PROCEDURE⟧をさらに⟦NUMBER⟧回まで⟦REPEAT⟧してもよい",
            "structure": "Repeat procedure",
        },

        # From: "(" opening parenthesis
        {
            "name": "open_parenthesis",
            "regex": r"\(",
            "template": "(",
            "structure": "Open parenthesis",
        },

        # From: ")" closing parenthesis
        {
            "name": "close_parenthesis",
            "regex": r"\)",
            "template": ")",
            "structure": "Close parenthesis",
        },

        # From: "（" opening japanese parenthesis
        {
            "name": "open_japanese_parenthesis",
            "regex": r"\（",
            "template": "（",
            "structure": "Open japanese parenthesis",
        },

        # From: "）" closing japanese parenthesis
        {
            "name": "close_japanese_parenthesis",
            "regex": r"\）",
            "template": "）",
            "structure": "Close japanese parenthesis",
        },

        # From: '"' opening quote
        {
            "name": "open_quote",
            "regex": r'"',
            "template": '"',
            "structure": "Open quote",
        },

        # From: '"' closing quote
        {
            "name": "close_quote",
            "regex": r'"',
            "template": '"',
            "structure": "Close quote",
        },

        # From: "そのカードの{{toujyou.png|登場}}能力1つを発動させる"
        {
            "name": "card_trigger_ability_activation_v2",
            "regex": r"\bその([^。]+)の([^。]+)(\d+)つを([^。]+)させる",
            "template": "その⟦CARD⟧の⟦ABILITY_TYPE⟧⟦NUMBER⟧つを⟦ACTION⟧させる",
            "structure": "Card trigger ability activation v2",
        },

        # From: "自分のエネルギーが10枚以上あるかぎり"
        {
            "name": "energy_count_condition_v2",
            "regex": r"\b([^。]+)の([^。]+)が(\d+)枚以上あるかぎり",
            "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦NUMBER⟧枚以上あるかぎり",
            "structure": "Energy count condition v2",
        },

        # From: "ライブの合計スコアが相手より高い場合"
        {
            "name": "live_score_comparison_condition_v2",
            "regex": r"\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合",
            "template": "⟦SOURCE⟧の⟦ATTRIBUTE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合",
            "structure": "Live score comparison condition v2",
        },

        # From: "相手のエネルギーが自分より多い場合"
        {
            "name": "opponent_energy_comparison_condition",
            "regex": r"\b([^。]+)の([^。]+)が([^。]+)より([^。]+)場合",
            "template": "⟦SOURCE⟧の⟦RESOURCE⟧が⟦COMPARISON_TARGET⟧より⟦COMPARISON⟧場合",
            "structure": "Opponent energy comparison condition",
        },

        # From: "その中から1枚を手札に加える"
        {
            "name": "select_one_from_revealed_v2",
            "regex": r"\bその中から(\d+)枚を([^。]+)に([^。]+)",
            "template": "その中から⟦NUMBER⟧枚を⟦DESTINATION⟧に⟦ACTION⟧",
            "structure": "Select one from revealed v2",
        },

        # From: "ステージのセンターエリアにいる場合"
        {
            "name": "center_area_condition_v2",
            "regex": r"\b([^。]+)の([^。]+)に([^。]+)場合",
            "template": "⟦ZONE⟧の⟦AREA⟧に⟦STATE⟧場合",
            "structure": "Center area condition v2",
        },

        # From: "それらが両方ある場合"
        {
            "name": "both_conditions_met",
            "regex": r"\b([^。]+)が([^。]+)ある場合",
            "template": "⟦THEY⟧が⟦BOTH⟧ある場合",
            "structure": "Both conditions met",
        },

        # From: "・" bullet point
        {
            "name": "bullet_point",
            "regex": r"\・",
            "template": "・",
            "structure": "Bullet point",
        },

        # From: "自分のライブ中のライブカードに"
        {
            "name": "zone_card_condition_v2",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)に",
            "template": "⟦SOURCE⟧の⟦STATE⟧の⟦CARD_TYPE⟧に",
            "structure": "Zone card condition v2",
        },

        # From: "控え室に置く手札の数が1枚減る"
        {
            "name": "placed_cards_cost_reduction",
            "regex": r"\b([^。]+)に([^。]+)([^。]+)の([^。]+)が(\d+)枚([^。]+)",
            "template": "⟦DESTINATION⟧に⟦PLACED⟧⟦SOURCE⟧の⟦COUNT⟧が⟦NUMBER⟧枚⟦REDUCTION⟧",
            "structure": "Placed cards cost reduction",
        },

        # From: "自分のステージに"
        {
            "name": "simple_zone_condition",
            "regex": r"\b([^。]+)の([^。]+)に",
            "template": "⟦SOURCE⟧の⟦ZONE⟧に",
            "structure": "Simple zone condition",
        },

        # From: "のみ起動できる"
        {
            "name": "activation_restriction",
            "regex": r"\のみ([^。]+)できる",
            "template": "のみ⟦ACTION⟧できる",
            "structure": "Activation restriction",
        },

        # From: "対戦相手のカードの効果でも発動する"
        {
            "name": "opponent_card_effect_activation",
            "regex": r"\b([^。]+)の([^。]+)の([^。]+)でも([^。]+)する",
            "template": "⟦OPPONENT⟧の⟦CARD⟧の⟦EFFECT⟧でも⟦ACTION⟧する",
            "structure": "Opponent card effect activation",
        },

        # From: "あるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う"
        {
            "name": "card_name_treatment",
            "regex": r"\b([^。]+)この([^。]+)は『([^』]+)』、『([^』]+)』、『([^』]+)』として扱う",
            "template": "⟦LOCATION⟧この⟦CARD⟧は『⟦GROUP1⟧』、『⟦GROUP2⟧』、『⟦GROUP3⟧』として扱う",
            "structure": "Card name treatment",
        },

        # From: "も登場できる"
        {
            "name": "can_summon",
            "regex": r"\も([^。]+)できる",
            "template": "も⟦ACTION⟧できる",
            "structure": "Can summon",
        },

        # From: "は登場できない"
        {
            "name": "cannot_summon",
            "regex": r"\は([^。]+)できない",
            "template": "は⟦ACTION⟧できない",
            "structure": "Cannot summon",
        },

        # From: "いる『Aqours』のメンバー1人を選ぶ"
        {
            "name": "select_specific_group_member",
            "regex": r"\いる『([^』]+)』の([^。]+)(\d+)人を選ぶ",
            "template": "いる『⟦GROUP⟧』の⟦TARGET⟧⟦NUMBER⟧人を選ぶ",
            "structure": "Select specific group member",
        },

        # From: "ライブ終了時まで"
        {
            "name": "duration_until_live_end",
            "regex": r"\b([^。]+)終了時まで",
            "template": "⟦EVENT⟧終了時まで",
            "structure": "Duration until live end",
        },

        # From: "必要ハートに{{heart_03.png|heart03}}を3以上含む"
        {
            "name": "resource_requirement",
            "regex": r"\b([^。]+)に([^。]+)を(\d+)以上含む",
            "template": "⟦REQUIREMENT_TYPE⟧に⟦RESOURCE⟧を⟦NUMBER⟧以上含む",
            "structure": "Resource requirement",
        },

        # From: "自分の成功ライブカード置き場にあるカード1枚につき、このカードを成功させるための必要ハートは{{heart_00.png|heart0}}{{heart_00.png|heart0}}少なくなる。"
        {
            "name": "per_card_cost_reduction",
            "regex": r"自分の([^。]+)にあるカード(\d+)枚につき、このカードを成功させるための必要ハートは([^。]+)少なくなる。",
            "template": "自分の⟦ZONE⟧にあるカード⟦NUMBER⟧枚につき、このカードを成功させるための必要ハートは⟦MODIFIER⟧少なくなる。",
            "structure": "Per card cost reduction",
        },

        # From: "ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る。"
        {
            "name": "duration_gain_ability",
            "regex": r"([^。]+)終了時まで、「([^」]+)」を得る。",
            "template": "⟦EVENT⟧終了時まで、「⟦ABILITY⟧」を得る。",
            "structure": "Duration gain ability",
        },

        # From: "カードを1枚引き、手札を1枚控え室に置く。"
        {
            "name": "draw_discard_combined_with_period",
            "regex": r"([^。]+)を(\d+)枚引き、([^。]+)を(\d+)枚([^。]+)に置く。",
            "template": "⟦RESOURCE1⟧を⟦NUMBER1⟧枚引き、⟦RESOURCE2⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に置く。",
            "structure": "Draw discard combined with period",
        },

        # From: "。"
        {
            "name": "period",
            "regex": r"。",
            "template": "。",
            "structure": "Period",
        },

        # From: "（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）"
        {
            "name": "parenthetical_restriction",
            "regex": r"（([^。]+)が持つ([^。]+)は、([^。]+)で([^。]+)する([^。]+)を([^。]+)ない。）",
            "template": "（⟦CONDITION⟧が持つ⟦RESOURCE⟧は、⟦CONTEXT⟧で⟦ACTION⟧する⟦ATTRIBUTE⟧を⟦MODIFIER⟧ない。）",
            "structure": "Parenthetical restriction",
        },

        # From: "\n・"
        {
            "name": "newline_bullet",
            "regex": r"\n・",
            "template": "\n・",
            "structure": "Newline bullet",
        },

        # From: "ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。"
        {
            "name": "duration_resource_gain_with_period",
            "regex": r"([^。]+)終了時まで、([^。]+)を得る。",
            "template": "⟦EVENT⟧終了時まで、⟦RESOURCE⟧を得る。",
            "structure": "Duration resource gain with period",
        },


        # From: "{{toujyou.png|登場}}"
        {
            "name": "trigger_appearance_icon",
            "regex": r"\{\{toujyou\.png\|登場\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Appearance trigger icon",
        },

        # From: "{{jidou.png|自動}}"
        {
            "name": "trigger_automatic_icon",
            "regex": r"\{\{jidou\.png\|自動\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Automatic trigger icon",
        },

        # From: "{{live_start.png|ライブ開始時}}"
        {
            "name": "trigger_live_start_icon",
            "regex": r"\{\{live_start\.png\|ライブ開始時\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Live start trigger icon",
        },

        # From: "{{kidou.png|起動}}"
        {
            "name": "trigger_activation_icon",
            "regex": r"\{\{kidou\.png\|起動\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Activation trigger icon",
        },

        # From: "{{jyouji.png|常時}}"
        {
            "name": "trigger_constant_icon",
            "regex": r"\{\{jyouji\.png\|常時\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Constant trigger icon",
        },

        # From: "{{live_success.png|ライブ成功時}}"
        {
            "name": "trigger_live_success_icon",
            "regex": r"\{\{live_success\.png\|ライブ成功時\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Live success trigger icon",
        },

        # From: "{{turn1.png|ターン1回}}"
        {
            "name": "trigger_turn1_icon",
            "regex": r"\{\{turn1\.png\|ターン1回\}\}",
            "template": "⟦TRIGGER⟧",
            "structure": "Turn 1 trigger icon",
        },

        # From: "{{icon_energy.png|E}}"
        {
            "name": "resource_energy_icon",
            "regex": r"\{\{icon_energy\.png\|E\}\}",
            "template": "⟦RESOURCE⟧",
            "structure": "Energy resource icon",
        },

        # From: "{{heart_01.png|heart01}}"
        {
            "name": "resource_heart01_icon",
            "regex": r"\{\{heart_01\.png\|heart01\}\}",
            "template": "⟦RESOURCE⟧",
            "structure": "Heart01 resource icon",
        },

        # From: "{{heart_03.png|heart03}}"
        {
            "name": "resource_heart03_icon",
            "regex": r"\{\{heart_03\.png\|heart03\}\}",
            "template": "⟦RESOURCE⟧",
            "structure": "Heart03 resource icon",
        },

        # From: "{{heart_06.png|heart06}}"
        {
            "name": "resource_heart06_icon",
            "regex": r"\{\{heart_06\.png\|heart06\}\}",
            "template": "⟦RESOURCE⟧",
            "structure": "Heart06 resource icon",
        },

        # From: "\n" (newline between sentences)
        {
            "name": "newline",
            "regex": r"\n",
            "template": "\n",
            "structure": "Newline",
        },






        # From: "その中からメンバーカードを1枚公開して手札に加えてもよい。"
        {
            "name": "from_among_member_card_reveal_add_optional",
            "regex": r"\bその中から([^。]+)を(\d+)枚公開して([^。]+)に加えてもよい",
            "template": "その中から⟦CARD_TYPE⟧を⟦NUMBER⟧枚公開して⟦ZONE⟧に加えてもよい",
            "structure": "From among member card reveal add optional",
        },

        # From: "その中から1枚を手札に加え、"
        {
            "name": "from_among_add_simple",
            "regex": r"\bその中から(\d+)枚を([^。]+)に加え、",
            "template": "その中から⟦NUMBER⟧枚を⟦ZONE⟧に加え、",
            "structure": "From among add simple",
        },

        # From: "自分の成功ライブカード置き場にあるカードを1枚手札に加える。"
        {
            "name": "zone_card_count_add",
            "regex": r"\b([^。]+)の([^。]+)にある([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE⟧の⟦ZONE⟧にある⟦RESOURCE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
            "structure": "Zone card count add",
        },


        # From: "手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。"
        {
            "name": "zone_to_zone_optional_deck_top_look",
            "regex": r"\b([^。]+)を(\d+)枚([^。]+)に置いてもよい：([^。]+)の([^。]+)の上から([^。]+)を(\d+)枚見る",
            "template": "⟦SOURCE⟧を⟦NUMBER1⟧枚⟦DESTINATION1⟧に置いてもよい：⟦SOURCE2⟧の⟦ZONE⟧の上から⟦RESOURCE⟧を⟦NUMBER2⟧枚見る",
            "structure": "Zone to zone optional deck top look",
        },

        # From: "手札のライブカードを1枚公開してもよい：自分の成功ライブカード置き場にあるカードを1枚手札に加える。"
        {
            "name": "zone_card_reveal_optional_zone_card_count_add",
            "regex": r"\b([^。]+)の([^。]+)を(\d+)枚公開してもよい：([^。]+)の([^。]+)にある([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE1⟧の⟦CARD_TYPE⟧を⟦NUMBER1⟧枚公開してもよい：⟦SOURCE2⟧の⟦ZONE⟧にある⟦RESOURCE⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に加える",
            "structure": "Zone card reveal optional zone card count add",
        },


        # From: "{{jidou.png|自動}}このメンバーがステージから控え室に置かれたとき、メンバー1人をアクティブにしてもよい。"
        {
            "name": "automatic_trigger_state_change_optional",
            "regex": r"\b([^。]+)が([^。]+)から([^。]+)に([^。]+)とき、([^。]+)(\d+)人を([^。]+)にしてもよい",
            "template": "⟦TARGET⟧が⟦SOURCE⟧から⟦DESTINATION⟧に⟦TRIGGER⟧とき、⟦NEW_TARGET⟧⟦NUMBER⟧人を⟦STATE⟧にしてもよい",
            "structure": "Automatic trigger state change optional",
        },

        # From: "{{jyouji.png|常時}}自分か相手のステージにコスト13以上のメンバーがいる場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。"
        {
            "name": "condition_or_zone_cost_above_resource_gain",
            "regex": r"\b([^。]+)か([^。]+)の([^。]+)にコスト(\d+)以上の([^。]+)いる場合、([^。]+)を得る",
            "template": "⟦SOURCE1⟧か⟦SOURCE2⟧の⟦ZONE⟧にコスト⟦COST⟧以上の⟦TARGET⟧いる場合、⟦RESOURCE⟧を得る",
            "structure": "Condition or zone cost above resource gain",
        },

        # From: "{{heart_01.png|heart01}}か{{heart_03.png|heart03}}か{{heart_06.png|heart06}}のうち、1つを選ぶ。"
        {
            "name": "resource_selection",
            "regex": r"\b([^。]+)か([^。]+)か([^。]+)のうち、(\d+)つを選ぶ",
            "template": "⟦RESOURCE1⟧か⟦RESOURCE2⟧か⟦RESOURCE3⟧のうち、⟦NUMBER⟧つを選ぶ",
            "structure": "Resource selection",
        },

        # From: "自分の控え室からコスト4以下の『μ's』のメンバーカードを1枚手札に加える。"
        {
            "name": "zone_cost_group_card_add",
            "regex": r"\b([^。]+)の([^。]+)からコスト(\d+)以下の『([^』]+)』の([^。]+)を(\d+)枚([^。]+)に加える",
            "template": "⟦SOURCE⟧の⟦ZONE⟧からコスト⟦COST⟧以下の『⟦GROUP⟧』の⟦CARD_TYPE⟧を⟦NUMBER⟧枚⟦DESTINATION⟧に加える",
            "structure": "Zone cost group card add",
        },

        # From: "以下から1つを選ぶ。"
        {
            "name": "select_from_below",
            "regex": r"\b以下から(\d+)つを選ぶ",
            "template": "以下から⟦NUMBER⟧つを選ぶ",
            "structure": "Select from below",
        },

        # From: "カードを1枚引き、手札を1枚控え室に置く。"
        {
            "name": "draw_discard_combined",
            "regex": r"\b([^。]+)を(\d+)枚引き、([^。]+)を(\d+)枚([^。]+)に置く",
            "template": "⟦RESOURCE1⟧を⟦NUMBER1⟧枚引き、⟦RESOURCE2⟧を⟦NUMBER2⟧枚⟦DESTINATION⟧に置く",
            "structure": "Draw discard combined",
        },

        # From: "その中から好きな枚数を好きな順番でデッキの上に置き、"
        {
            "name": "from_among_place_deck_top_with_remainder",
            "regex": r"\bその中から好きな枚数を好きな順番で([^。]+)の上に置き、",
            "template": "その中から好きな枚数を好きな順番で⟦ZONE⟧の上に置き、",
            "structure": "From among place deck top with remainder",
        },

        # From: "このメンバーをウェイトにしてもよい：相手のステージにいるコスト4以下のメンバー1人をウェイトにする。"
        {
            "name": "state_change_optional_cost_condition_state_change",
            "regex": r"\b([^。]+)を([^。]+)にしてもよい：([^。]+)の([^。]+)いるコスト(\d+)以下の([^。]+)(\d+)人を([^。]+)にする",
            "template": "⟦TARGET⟧を⟦STATE1⟧にしてもよい：⟦SOURCE⟧の⟦ZONE⟧いるコスト⟦COST⟧以下の⟦NEW_TARGET⟧⟦NUMBER⟧人を⟦STATE2⟧にする",
            "structure": "State change optional cost condition state change",
        },

        # From: "（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）"
        {
            "name": "parenthetical_restriction",
            "regex": r"\b（([^。]+)が持つ([^。]+)は、([^。]+)で([^。]+)する([^。]+)を([^。]+)ない。）",
            "template": "（⟦CONDITION⟧が持つ⟦RESOURCE⟧は、⟦CONTEXT⟧で⟦ACTION⟧する⟦ATTRIBUTE⟧を⟦MODIFIER⟧ない。）",
            "structure": "Parenthetical restriction",
        },

        # From: "必要ハートを確認する時、エールで出た{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う"
        {
            "name": "blade_heart_treatment_literal",
            "regex": r"必要ハートを確認する時、エールで出た",
            "template": "必要ハートを確認する時、エールで出た",
            "structure": "Blade heart treatment literal",
        },

        # From: "メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す"
        {
            "name": "member_leave_energy_return_literal",
            "regex": r"メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す",
            "template": "メンバーがステージから離れたとき、下に置かれているエネルギーカードはエネルギーデッキに戻す",
            "structure": "Member leave energy return literal",
        },

        # From: "能力がコストを持つ場合、支払って発動させる"
        {
            "name": "ability_cost_activation_literal",
            "regex": r"能力がコストを持つ場合、支払って発動させる",
            "template": "能力がコストを持つ場合、支払って発動させる",
            "structure": "Ability cost activation literal",
        },

        # From: "メンバーをそれぞれ好きなエリアに移動させる"
        {
            "name": "formation_change_literal",
            "regex": r"メンバーをそれぞれ好きなエリアに移動させる",
            "template": "メンバーをそれぞれ好きなエリアに移動させる",
            "structure": "Formation change literal",
        },

        # From: "2人以上のメンバーを移動させることはできない"
        {
            "name": "cannot_move_multiple_literal",
            "regex": r"2人以上のメンバーを移動させることはできない",
            "template": "2人以上のメンバーを移動させることはできない",
            "structure": "Cannot move multiple literal",
        },

        # From: "移動させてもよい"
        {
            "name": "optional_move_literal",
            "regex": r"移動させてもよい",
            "template": "移動させてもよい",
            "structure": "Optional move literal",
        },

        # From: "置ける"
        {
            "name": "can_place_literal",
            "regex": r"置ける",
            "template": "置ける",
            "structure": "Can place literal",
        },

        # From: "、"
        {
            "name": "comma_literal",
            "regex": r"、",
            "template": "、",
            "structure": "Comma literal",
        },

        # From: "支払ってもよい"
        {
            "name": "optional_payment_literal",
            "regex": r"支払ってもよい",
            "template": "支払ってもよい",
            "structure": "Optional payment literal",
        },

        # From: "加える"
        {
            "name": "add_to_hand_literal",
            "regex": r"加える",
            "template": "加える",
            "structure": "Add to hand literal",
        },

        # From: "置かれた"
        {
            "name": "placed_passive_literal",
            "regex": r"置かれた",
            "template": "置かれた",
            "structure": "Placed passive literal",
        },

        # From: "移動させる"
        {
            "name": "move_verb_literal",
            "regex": r"移動させる",
            "template": "移動させる",
            "structure": "Move verb literal",
        },

        # From: "{{center.png|センター}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る"
        {
            "name": "position_blade_resource_gain",
            "regex": r"\{\{center\.png\|センター\}\}\{\{icon_blade\.png\|ブレード\}\}\{\{icon_blade\.png\|ブレード\}\}を得る",
            "template": "⟦POSITION⟧⟦BLADE⟧⟦BLADE⟧を得る",
            "structure": "Position blade resource gain",
        },

        # From: "{{icon_b_all.png|ALLブレード}}は任意の色のハートとして扱う"
        {
            "name": "all_blade_treatment",
            "regex": r"\{\{icon_b_all\.png\|ALLブレード\}\}は任意の色のハートとして扱う",
            "template": "⟦ALL_BLADE⟧は任意の色のハートとして扱う",
            "structure": "All blade treatment",
        },

        # From: "{{center.png|センター}}"
        {
            "name": "center_icon",
            "regex": r"\{\{center\.png\|センター\}\}",
            "template": "⟦CENTER⟧",
            "structure": "Center icon",
        },

        # From: "を得る" resource gain verb
        {
            "name": "resource_gain_verb_exact",
            "regex": r"を得る",
            "template": "を得る",
            "structure": "Resource gain verb exact",
        },
    ]

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def check_pattern_overlap(patterns: list[dict[str, Any]], cards_file: Path) -> list[dict[str, Any]]:
    """
    Check for overlap between patterns using actual ability texts.
    Returns a list of overlapping pattern pairs.
    """
    overlaps = []
    
    # Load cards to get actual ability texts
    with open(cards_file, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    # Get ability texts from cards
    ability_texts = []
    for card_id, card in cards.items():
        ability = card.get("ability", "")
        if ability:
            ability_texts.append(ability)
    
    # Compile all patterns
    compiled_patterns = []
    for pattern in patterns:
        try:
            compiled = re.compile(pattern["regex"])
            compiled_patterns.append({
                "name": pattern["name"],
                "regex": pattern["regex"],
                "compiled": compiled,
            })
        except re.error as e:
            print(f"ERROR: Invalid regex in pattern '{pattern['name']}': {e}")
    
    # Check for overlaps using actual ability texts (scan all texts)
    for text in ability_texts:
        matches_in_text = []
        for pattern in compiled_patterns:
            matches = list(pattern["compiled"].finditer(text))
            if matches:
                for match in matches:
                    matches_in_text.append({
                        "pattern_name": pattern["name"],
                        "start": match.start(),
                        "end": match.end(),
                        "matched_text": match.group(0),
                    })
        
        # Check for overlapping matches in this text
        for i, match1 in enumerate(matches_in_text):
            for match2 in matches_in_text[i+1:]:
                # Check if ranges overlap
                if not (match1["end"] <= match2["start"] or match2["end"] <= match1["start"]):
                    overlaps.append({
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "pattern1": match1["pattern_name"],
                        "pattern2": match2["pattern_name"],
                        "match1_text": match1["matched_text"],
                        "match2_text": match2["matched_text"],
                        "overlap_range": (max(match1["start"], match2["start"]), min(match1["end"], match2["end"])),
                    })
    
    return overlaps


def load_cards(cards_file: Path) -> dict[str, dict[str, Any]]:
    with open(cards_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def all_ability_texts(cards: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    abilities = []
    for card_id, card in cards.items():
        ability = card.get("ability", "")
        if ability:
            # Split ability by newlines to handle multiple abilities per card
            ability_parts = ability.split("\n")
            for part in ability_parts:
                if part.strip():  # Skip empty lines
                    abilities.append({"ability": part.strip(), "card_id": card_id})
    return abilities


def group_unique_abilities(abilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group unique abilities and track which cards have them."""
    unique_abilities = {}
    for ability_data in abilities:
        ability_text = ability_data["ability"]
        card_id = ability_data["card_id"]
        
        if ability_text not in unique_abilities:
            unique_abilities[ability_text] = {
                "ability": ability_text,
                "card_ids": [],
            }
        unique_abilities[ability_text]["card_ids"].append(card_id)
    
    # Convert to list
    return list(unique_abilities.values())


def match_dsl_patterns(texts: list[dict[str, Any]]) -> dict[str, Any]:
    dsl_patterns = DSL_PATTERNS

    text_matches = []
    pattern_counts = Counter()
    pattern_variables = {}
    
    total_characters = 0
    total_covered_characters = 0

    for text_data in texts:
        text = text_data.get("ability") or text_data.get("clause", "")
        card_ids = text_data.get("card_ids", [])
        if not text:
            continue
            
        total_characters += len(text)
        matches = []
        
        for pattern in dsl_patterns:
            for match in re.finditer(pattern["regex"], text):
                variables = list(match.groups())
                matches.append({
                    "pattern_name": pattern["name"],
                    "structure": pattern["structure"],
                    "template": pattern["template"],
                    "matched_text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "variables": variables,
                })
                pattern_counts[pattern["name"]] += 1

                if pattern["name"] not in pattern_variables:
                    pattern_variables[pattern["name"]] = []
                pattern_variables[pattern["name"]].append(variables)

        if matches:
            covered = [False] * len(text)
            for m in matches:
                for i in range(m["start"], m["end"]):
                    if i < len(covered):
                        covered[i] = True
            
            coverage = sum(covered) / len(covered) if covered else 0
            total_covered_characters += sum(covered)
            
            text_matches.append({
                "original": text,
                "matches": matches,
                "coverage": coverage,
                "match_count": len(matches),
                "card_ids": card_ids,
            })
        else:
            text_matches.append({
                "original": text,
                "matches": [],
                "coverage": 0.0,
                "match_count": 0,
                "card_ids": card_ids,
            })

    total_coverage = total_covered_characters / total_characters if total_characters > 0 else 0

    return {
        "total_texts": len(texts),
        "total_characters": total_characters,
        "total_covered_characters": total_covered_characters,
        "total_coverage_percentage": total_coverage * 100,
        "unique_patterns": len(pattern_counts),
        "pattern_counts": dict(pattern_counts),
        "pattern_variables": pattern_variables,
        "text_matches": text_matches,
    }


def extract_abilities(cards_file: Path, rules_file: Path, output_file: Path, metadata_file: Path, show_summary: bool = True) -> dict[str, Any]:
    cards = load_cards(cards_file)
    abilities = all_ability_texts(cards)
    unique_abilities = group_unique_abilities(abilities)

    dsl_pattern_analysis = match_dsl_patterns(unique_abilities)

    result = {
        "schema": "ability_skeletons.v6",
        "source": str(cards_file),
        "rules_source": str(rules_file),
        "metadata_source": str(metadata_file),
        "dsl_pattern_analysis": dsl_pattern_analysis,
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if show_summary:
        print_summary(dsl_pattern_analysis)

    return result


def print_summary(analysis: dict[str, Any]) -> None:
    print("=" * 80)
    print("PATTERN MATCHING SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal abilities: {analysis.get('total_texts', 0)}")
    print(f"Total characters: {analysis.get('total_characters', 0)}")
    print(f"Total covered characters: {analysis.get('total_covered_characters', 0)}")
    print(f"Total text coverage: {analysis.get('total_coverage_percentage', 0):.1f}%")
    print(f"Unique patterns: {analysis.get('unique_patterns', 0)}")
    
    print("\n" + "=" * 80)
    print("TOP PATTERNS BY MATCH COUNT")
    print("=" * 80)
    
    pattern_counts = analysis.get('pattern_counts', {})
    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
    
    for pattern, count in sorted_patterns[:20]:
        print(f"{pattern:40s}: {count:4d} matches")
    
    print("\n" + "=" * 80)
    print("EXAMPLE MATCHES (first 5 abilities)")
    print("=" * 80)
    
    text_matches = analysis.get('text_matches', [])
    for i, match in enumerate(text_matches[:5]):
        print(f"\n--- Ability {i+1} ---")
        print(f"Coverage: {match.get('coverage', 0) * 100:.1f}%")
        print(f"Patterns matched: {match.get('match_count', 0)}")
        print(f"Original: {match.get('original', '')[:100]}...")
        
        if match.get('matches'):
            print("Matched patterns:")
            for m in match['matches'][:3]:
                print(f"  - {m['pattern_name']}: {m['matched_text'][:50]}...")
    
    print("\n" + "=" * 80)
    print("NO COVERAGE EXAMPLES (first 5)")
    print("=" * 80)
    
    no_coverage_count = 0
    for match in text_matches:
        if match.get('coverage', 0) == 0:
            print(f"\n--- No Coverage {no_coverage_count + 1} ---")
            print(f"Original: {match.get('original', '')[:100]}...")
            no_coverage_count += 1
            if no_coverage_count >= 5:
                break

    print("\n" + "=" * 80)
    print("UNCOVERED/PARTIALLY COVERED ABILITIES (lowest coverage)")
    print("=" * 80)

    # Debug: Show coverage distribution for ALL abilities
    coverage_values = [m.get('coverage', 0) for m in text_matches]
    print(f"\nCoverage distribution (ALL abilities):")
    print(f"  Total abilities: {len(coverage_values)}")
    print(f"  Min: {min(coverage_values) * 100:.1f}%")
    print(f"  Max: {max(coverage_values) * 100:.1f}%")
    print(f"  Mean: {sum(coverage_values) / len(coverage_values) * 100:.1f}%")
    below_100 = sum(1 for c in coverage_values if c < 1.0)
    print(f"  Abilities below 100%: {below_100}/{len(coverage_values)}")

    # Sort by coverage (ascending) to show least covered first
    sorted_by_coverage = sorted(text_matches, key=lambda x: x.get('coverage', 0))

    # Only show abilities below 100% coverage
    below_100_matches = [m for m in sorted_by_coverage if m.get('coverage', 0) < 1.0]
    print(f"\nShowing {len(below_100_matches)} abilities with <100% coverage:")

    for i, match in enumerate(below_100_matches[:50]):
        print(f"\n--- Ability {i+1} (Coverage: {match.get('coverage', 0) * 100:.1f}%) ---")
        original = match.get('original', '')

        # Build coverage breakdown
        covered = [False] * len(original)
        for m in match.get('matches', []):
            for j in range(m['start'], m['end']):
                if j < len(covered):
                    covered[j] = True

        # Mark covered parts with [COVERED] and uncovered with [UNCOVERED]
        coverage_breakdown = ""
        idx = 0
        while idx < len(original):
            if covered[idx]:
                # Start of covered section
                start = idx
                while idx < len(original) and covered[idx]:
                    idx += 1
                coverage_breakdown += f"[COVERED: {original[start:idx]}]"
            else:
                # Start of uncovered section
                start = idx
                while idx < len(original) and not covered[idx]:
                    idx += 1
                coverage_breakdown += f"[UNCOVERED: {original[start:idx]}]"

        print(f"Coverage breakdown:")
        print(f"  {coverage_breakdown}")
        print(f"Original: {original}")


if __name__ == "__main__":
    cards_file = Path("data/cards.json")
    rules_file = Path("data/rules.txt")
    output_file = Path("data/abilities_extracted.json")
    metadata_file = Path("data/metadata.json")

    # First, check for pattern overlap
    print("=" * 80)
    print("CHECKING FOR PATTERN OVERLAP")
    print("=" * 80)
    overlaps = check_pattern_overlap(DSL_PATTERNS, cards_file)
    
    if overlaps:
        print(f"\nWARNING: Found {len(overlaps)} pattern overlaps!")
        print("\nOverlapping patterns:")
        for i, overlap in enumerate(overlaps[:20]):
            print(f"\n--- Overlap {i+1} ---")
            print(f"Text: {overlap['text']}")
            print(f"Pattern 1: {overlap['pattern1']} matched '{overlap['match1_text']}'")
            print(f"Pattern 2: {overlap['pattern2']} matched '{overlap['match2_text']}'")
            print(f"Overlap range: {overlap['overlap_range']}")
        
        print("\n" + "=" * 80)
        print("OVERLAP DETECTION COMPLETE - PROCEEDING WITH CAUTION")
        print("=" * 80)
    else:
        print("\nNo pattern overlaps detected.")
        print("=" * 80)

    extract_abilities(cards_file, rules_file, output_file, metadata_file)
