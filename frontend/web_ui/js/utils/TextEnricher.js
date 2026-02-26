import { State } from '../state.js';
import { ICON_DATA_URIs } from '../assets_registry.js';

// Pre-compiled regex patterns for performance
const REGEX_HTML_TAG = /<[^>]+>/g;
const REGEX_CURLY_TAG = /{{(.*?)\|(.*?)}}/g;
const REGEX_COLORS = /(ピンク|レッド|赤|イエロー|黄|グリーン|緑|ブルー|青|パープル|紫|オール|Pink|Red|Yellow|Green|Blue|Purple|All)/g;
const REGEX_MECHANICS = /(ハート|ピース|エナジー|ボルテージ|勧誘|Hearts|Blades|Energy|Voltage|Scout|Yell|RUSH|LIVE|LIVE!|Appeal|HEART|DREAM)/g;
const REGEX_SUCCESS = /(SUCCESS|成功)/g;
const REGEX_FAILURE = /(FAILURE|失敗)/g;
const REGEX_CARD_NUM = /(PL![\w-]+)/g;
const REGEX_NEWLINE = /\\n/g;

// Pre-built zone regex
const ZONE_LIST = ['控え室', 'メンバー置場', 'ライブ置場', 'エナジー置場', '待機室', '手札', 'デッキ', '山札', 'Discard', 'Stage', 'Live Zone', 'Hand', 'Deck', 'Performance'];
const REGEX_ZONES = new RegExp(`(${ZONE_LIST.join('|')})`, 'g');

// Pre-built icon map with pre-compiled regexes
export const ICON_MAP = {
    '登場時': { path: 'toujyou.png', regex: /【登場時】/g },
    '[Play]': { path: 'toujyou.png', regex: /\[Play\]/g },
    'Play': { path: 'toujyou.png', regex: /【Play】/g },
    '自動': { path: 'jidou.png', regex: /【自動】/g },
    '[Auto]': { path: 'jidou.png', regex: /\[Auto\]/g },
    'Auto': { path: 'jidou.png', regex: /【Auto】/g },
    '永続': { path: 'jyouji.png', regex: /【永続】/g },
    '[Always]': { path: 'jyouji.png', regex: /\[Always\]/g },
    'Always': { path: 'jyouji.png', regex: /【Always】/g },
    '起動': { path: 'kidou.png', regex: /【起動】/g },
    '[Act]': { path: 'kidou.png', regex: /\[Act\]/g },
    'Act': { path: 'kidou.png', regex: /【Act】/g },
    'ターン1': { path: 'turn1.png', regex: /【ターン1】/g },
    'Turn 1': { path: 'turn1.png', regex: /【Turn 1】/g },
    '[Turn 1]': { path: 'turn1.png', regex: /\[Turn 1\]/g },
    'ライブスタート': { path: 'live_start.png', regex: /【ライブスタート】/g },
    'LIVE START': { path: 'live_start.png', regex: /【LIVE START】/g },
    '[Start]': { path: 'live_start.png', regex: /\[Start\]/g },
    'ピンク': { path: 'color_pink.png', regex: /【ピンク】/g },
    'Pink': { path: 'color_pink.png', regex: /【Pink】/g },
    'レッド': { path: 'color_red.png', regex: /【レッド】/g },
    '赤': { path: 'color_red.png', regex: /【赤】/g },
    'Red': { path: 'color_red.png', regex: /【Red】/g },
    'イエロー': { path: 'color_yellow.png', regex: /【イエロー】/g },
    '黄': { path: 'color_yellow.png', regex: /【黄】/g },
    'Yellow': { path: 'color_yellow.png', regex: /【Yellow】/g },
    'グリーン': { path: 'color_green.png', regex: /【グリーン】/g },
    '緑': { path: 'color_green.png', regex: /【緑】/g },
    'Green': { path: 'color_green.png', regex: /【Green】/g },
    'ブルー': { path: 'color_blue.png', regex: /【ブルー】/g },
    '青': { path: 'color_blue.png', regex: /【青】/g },
    'Blue': { path: 'color_blue.png', regex: /【Blue】/g },
    'パープル': { path: 'color_purple.png', regex: /【パープル】/g },
    '紫': { path: 'color_purple.png', regex: /【紫】/g },
    'Purple': { path: 'color_purple.png', regex: /【Purple】/g },
    'オール': { path: 'icon_all.png', regex: /【オール】/g },
    'All': { path: 'icon_all.png', regex: /【All】/g },
    'ライブ開始時': { path: 'live_start.png', regex: /【ライブ開始時】/g },
    '成功時': { path: 'live_success.png', regex: /【成功時】/g },
    'ライブ成功時': { path: 'live_success.png', regex: /【ライブ成功時】/g },
    'LIVE SUCCESS': { path: 'live_success.png', regex: /【LIVE SUCCESS】/g },
    '[Success]': { path: 'live_success.png', regex: /\[Success\]/g },
    'エネ': { path: 'icon_energy.png', regex: /【エネ】/g },
    'Energy': { path: 'icon_energy.png', regex: /【Energy】/g },
    'エネルギー': { path: 'icon_energy.png', regex: /【エネルギー】/g },
    'ハート': { path: 'heart_01.png', regex: /【ハート】/g },
    'Hearts': { path: 'heart_01.png', regex: /【Hearts】/g },
    'ピース': { path: 'heart_01.png', regex: /【ピース】/g },
    'ピンクハート': { path: 'heart_00.png', regex: /【ピンクハート】/g },
    'Pink Hearts': { path: 'heart_00.png', regex: /【Pink Hearts】/g },
    'レッドハート': { path: 'heart_01.png', regex: /【レッドハート】/g },
    'Red Hearts': { path: 'heart_01.png', regex: /【Red Hearts】/g },
    'イエローハート': { path: 'heart_02.png', regex: /【イエローハート】/g },
    'Yellow Hearts': { path: 'heart_02.png', regex: /【Yellow Hearts】/g },
    'グリーンハート': { path: 'heart_03.png', regex: /【グリーンハート】/g },
    'Green Hearts': { path: 'heart_03.png', regex: /【Green Hearts】/g },
    'ブルーハート': { path: 'heart_04.png', regex: /【ブルーハート】/g },
    'Blue Hearts': { path: 'heart_04.png', regex: /【Blue Hearts】/g },
    'パープルハート': { path: 'heart_05.png', regex: /【パープルハート】/g },
    'Purple Hearts': { path: 'heart_05.png', regex: /【Purple Hearts】/g },
    '全色ハート': { path: 'heart_06.png', regex: /【全色ハート】/g },
    'All Color Hearts': { path: 'heart_06.png', regex: /【All Color Hearts】/g },
    'ブレード': { path: 'icon_blade.png', regex: /【ブレード】/g },
    'Blade': { path: 'icon_blade.png', regex: /【Blade】/g },
    'Blades': { path: 'icon_blade.png', regex: /【Blades】/g },
    '開始時': { path: 'live_start.png', regex: /【開始時】/g },
};

// Pre-built icon replacement strings
const ICON_REPLACEMENTS = {};
for (const [key, data] of Object.entries(ICON_MAP)) {
    let style = 'height: 1.1em; vertical-align: middle;';
    if (data.path.includes('live_start') || data.path.includes('live_success')) {
        style += ' min-width: 3.5em;';
    } else if (data.path.includes('all')) {
        style += ' min-width: 2em;';
    }

    let src = data.path.includes('/') ? `img/${data.path}` : `img/texticon/${data.path}`;
    const iconKey = data.path.replace('.png', '');
    if (typeof ICON_DATA_URIs !== 'undefined' && ICON_DATA_URIs[iconKey]) {
        src = ICON_DATA_URIs[iconKey];
    }

    ICON_REPLACEMENTS[key] = {
        regex: data.regex,
        replacement: `<span class="icon-wrapper"><img src="${src}" alt="${key}" style="${style}" onerror="this.style.visibility='hidden'"></span>`
    };
}


export const TextEnricher = {
    enrichAbilityText: (text) => {
        if (!text) return "";

        const placeholders = [];

        text = text.replace(REGEX_HTML_TAG, (match) => {
            const id = `__TAG_${placeholders.length}__`;
            placeholders.push(match);
            return id;
        });

        text = text.replace(REGEX_CURLY_TAG, (match) => {
            const id = `__PH_${placeholders.length}__`;
            placeholders.push(match);
            return id;
        });

        text = text.replace(REGEX_COLORS, match => {
            const m = match.toLowerCase();
            let cls = 'hl-keyword';
            if (m.includes('pink') || m.includes('red') || m === 'ピンク' || m === 'レッド' || m === '赤') cls = 'hl-heart';
            if (m.includes('yellow') || m.includes('green') || m === 'イエロー' || m === '黄' || m === 'グリーン' || m === '緑') cls = 'hl-energy';
            if (m.includes('blue') || m.includes('purple') || m === 'ブルー' || m === '青' || m === 'パープル' || m === '紫') cls = 'hl-blade';
            return `<span class="${cls}">${match}</span>`;
        });

        text = text.replace(REGEX_ZONES, '<span class="hl-zone">$1</span>');
        text = text.replace(REGEX_MECHANICS, '<span class="hl-keyword">$1</span>');
        text = text.replace(REGEX_SUCCESS, '<span class="hl-success">$1</span>');
        text = text.replace(REGEX_FAILURE, '<span class="hl-failure">$1</span>');
        text = text.replace(REGEX_CARD_NUM, '<span class="hl-card">$1</span>');

        for (let i = placeholders.length - 1; i >= 0; i--) {
            text = text.replace(`__TAG_${i}__`, placeholders[i]);
            text = text.replace(`__PH_${i}__`, placeholders[i]);
        }

        for (const data of Object.values(ICON_REPLACEMENTS)) {
            data.regex.lastIndex = 0;
            text = text.replace(data.regex, data.replacement);
        }

        text = text.replace(REGEX_CURLY_TAG, (match, img, alt) => {
            let src = "img/" + img;
            if (img.endsWith('.png') && !img.includes('/')) {
                src = "img/texticon/" + img;
            }
            let style = "height: 1.1em; vertical-align: middle;";
            if (img.includes('live_start') || img.includes('live_success')) {
                style += ' min-width: 3.2em;';
            }
            const iconKey = img.replace('.png', '');
            if (typeof ICON_DATA_URIs !== 'undefined' && ICON_DATA_URIs[iconKey]) {
                src = ICON_DATA_URIs[iconKey];
            }
            return `<span class="icon-wrapper"><img src="${src}" alt="${alt}" style="${style}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"><span style="display:none;">${alt}</span></span>`;
        });
        text = text.replace(REGEX_NEWLINE, '<br>');

        return text;
    },

    getEffectiveAbilityText: (card) => {
        const raw = TextEnricher.getEffectiveRawText(card);
        return TextEnricher.enrichAbilityText(raw);
    },

    getEffectiveRawText: (card) => {
        if (!card) return "";
        const lang = State.currentLang;

        // 1. Try language-specific original text first
        let text = lang === 'en' ? (card.original_text_en || card.original_text) : card.original_text;

        // 2. If missing, try rich ability fields directly on specific object
        if (!text) text = card.ability || card.ability_text || card.text;

        // 3. Fallback to indexer if needed
        if (!text && card.id !== undefined) {
            const indexed = State.resolveCardData(card.id);
            if (indexed && indexed !== card) {
                text = lang === 'en' ? (indexed.original_text_en || indexed.original_text) : indexed.original_text;
                if (!text) text = indexed.ability || indexed.ability_text || indexed.text || indexed.original_text;
            }
        }

        return text || "";
    },

    isGenericInstruction: (text) => {
        if (!text) return true;
        const genericPatterns = [
            /戻して引き直します/,
            /引き直します/,
            /何もしない/,
            /次へ進みます/,
            /終了します/,
            /を確定して/,
            /キャンセルします/,
            /^Confirm$/i,
            /^Pass$/i,
            /^Skip$/i,
            /^Decline$/i,
            /^No$/i,
            /^Yes$/i
        ];
        return genericPatterns.some(p => p.test(text));
    },

    isRichAbility: (text) => {
        if (!text) return false;
        return text.includes('{{') || text.includes('【') || text.includes('[') || text.length > 25;
    },

    getEffectiveActionText: (action) => {
        if (!action) return "";
        const rawText = action.raw_text || action.text || "";

        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;

        if (action.source_card_id !== undefined && action.source_card_id !== -1) {
            const srcCard = State.resolveCardData(action.source_card_id);
            if (srcCard && (srcCard.text || srcCard.ability_text || srcCard.original_text || srcCard.ability)) {
                return TextEnricher.enrichAbilityText(TextEnricher.getEffectiveRawText(srcCard));
            }
        }

        let effectiveText = rawText;
        if ((currentLang === 'en' || showFriendlyAbilities) && window.translateAbility) {
            effectiveText = window.translateAbility(rawText, currentLang);
        } else if (currentLang === 'jp') {
            const srcCard = State.resolveCardData(action.source_card_id);
            if (srcCard && (srcCard.original_text || srcCard.ability)) {
                effectiveText = srcCard.original_text || srcCard.ability;
            } else if (window.translateAbility) {
                effectiveText = window.translateAbility(rawText, 'jp');
            }
        }

        let text = TextEnricher.enrichAbilityText(effectiveText);

        text = text.replace(/TRIGGER:\s*/g, '');
        text = text.replace(/\[TRIGGER\]\s*/g, '');

        return text;
    },

    getActionTags: (action, vertical = false) => {
        if (!action || !action.triggers) return "";
        const tags = [];
        if (action.triggers.includes(1)) tags.push(`<img src="img/texticon/toujyou.png" alt="[登場時]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(2)) tags.push(`<img src="img/texticon/live_kaishi.png" alt="[開始時]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(7)) tags.push(`<img src="img/texticon/kidou.png" alt="[起動]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(6)) tags.push(`<img src="img/texticon/jyouji.png" alt="[常時]" style="height:14px; vertical-align:middle;">`);

        if (tags.length === 0) return "";
        if (vertical) {
            return `<div style="display:flex; flex-direction:column; align-items:center; gap:1px; margin-left:4px;">${tags.join('')}</div>`;
        }
        return `<div style="display:flex; gap:3px; margin-top:2px;">${tags.join('')}</div>`;
    }
};
