/**
 * translator.js - Modular Ability Translator
 * Parity version with original ability_translator.js logic
 */

import { NAME_MAP } from './names.js';
import { TriggerType, Opcodes as EffectType } from '../generated_constants.js';

let translations = {};
let currentLanguage = 'jp';

/**
 * Loads translation data for the specified language.
 * @param {string} lang - 'jp' or 'en'
 */
export async function loadTranslations(lang = 'jp') {
    if (translations[lang]) {
        currentLanguage = lang;
        return translations[lang];
    }

    try {
        const response = await fetch(`./js/i18n/locales/${lang}.json`);
        if (!response.ok) throw new Error(`Failed to load ${lang} translations`);
        const data = await response.json();
        translations[lang] = data;

        // Backward compatibility globals
        if (typeof window !== 'undefined') {
            if (lang === 'jp') window.currentTranslationsJP = data;
            if (lang === 'en') window.currentTranslationsEN = data;
            window.translations = translations; // Expose the full map
        }

        currentLanguage = lang;
        return data;
    } catch (error) {
        console.error('Translation load error:', error);
        // Fallback to empty structure if failed
        translations[lang] = { triggers: {}, opcodes: {}, params: {}, misc: {} };
        return translations[lang];
    }
}

// Global exposure for TextEnricher.js and UI components
if (typeof window !== 'undefined') {
    window.translateAbility = translateAbility;
    window.translateCard = translateCard;
    window.translateMetadata = translateMetadata;
    window.t = t;
}

/**
 * Generic translation function for UI labels.
 * Supports parameter substitution like {count}.
 * @param {string} key
 * @param {Object} params
 * @returns {string}
 */
export function t(key, params = {}) {
    const langData = translations[currentLanguage] || translations.jp || {};
    let text = (langData.ui && langData.ui[key]) ? langData.ui[key] : key;

    for (const [k, v] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return text;
}

export const GROUP_ID_MAP = {
    0: "μ's",
    1: "Aqours",
    2: "虹ヶ咲",
    3: "リエラ",
    4: "蓮ノ空",
    10: "A-RISE",
    11: "Saint Snow",
    12: "Sunny Passion",
    13: "スクールアイドルミュージカル",
    98: "LIVE",
    99: "OTHER"
};

export const UNIT_ID_MAP = {
    0: "Printemps",
    1: "lily white",
    2: "BiBi",
    3: "CYaRon!",
    4: "AZALEA",
    5: "Guilty Kiss",
    6: "DiverDiva",
    7: "A・ZU・NA",
    8: "QU4RTZ",
    9: "R3BIRTH",
    10: "CatChu!",
    11: "KALEIDOSCORE",
    12: "5yncri5e!",
    13: "スリーズブーケ",
    14: "DOLLCHESTRA",
    15: "みらくらぱーく！",
    16: "Edel Stein",
    17: "AIscream",
    99: "OTHER"
};

/**
 * Translates a piece of metadata like a series or unit name.
 * @param {string} text 
 * @param {string} category 'GROUPS' or 'UNITS'
 * @returns {string}
 */
export function translateMetadata(text, category) {
    if (!text) return "";
    if (currentLanguage === 'jp') return text;

    const langData = translations[currentLanguage] || {};
    if (langData.params && langData.params[category] && langData.params[category][text]) {
        return langData.params[category][text];
    }
    return text;
}

/**
 * Translates all metadata for a card.
 * @param {Object} card 
 * @returns {Object} { name, groups, units }
 */
export function translateCard(card) {
    if (!card) return { name: "", groups: [], units: [] };

    let name = card.name || "";
    let groups = card.groups || [];
    let units = card.units || [];

    if (currentLanguage === 'en') {
        // Translate Name (Handle compound names like A & B & C)
        if (NAME_MAP[name]) {
            name = NAME_MAP[name];
        } else if (name.includes('&') || name.includes('/') || name.includes('／') || name.includes('＆') || name.includes('・')) {
            // Split by various delimiters common in multi-character cards
            const delimiters = /(&|\/|／|＆|・)/;
            const parts = name.split(delimiters);
            const translatedParts = parts.map(part => {
                const trimmed = part.trim();
                if (!trimmed) return part;
                // If it's a delimiter, keep it
                if (trimmed.length === 1 && "&/／＆・".includes(trimmed)) return part;
                return NAME_MAP[trimmed] || trimmed;
            });
            name = translatedParts.join('');
        }

        // Translate Groups/Series (handle IDs or strings)
        groups = groups.map(g => {
            const str = typeof g === 'number' ? GROUP_ID_MAP[g] : g;
            return translateMetadata(str, 'GROUPS');
        });

        // Translate Units (handle IDs or strings)
        units = units.map(u => {
            const str = typeof u === 'number' ? UNIT_ID_MAP[u] : u;
            return translateMetadata(str, 'UNITS');
        });
    }

    return { name, groups, units };
}

export function translateAbility(rawText, lang = 'jp') {
    if (!rawText) return '';
    const tData = translations[lang] || translations.jp; // Fallback to JP if loaded, or raw if not
    if (!tData || Object.keys(tData).length === 0) return rawText;

    const lines = rawText.split('\n');
    const translatedLines = [];

    for (let line of lines) {
        line = line.trim();
        if (!line || line.startsWith('//')) {
            translatedLines.push(line);
            continue;
        }

        // --- Heuristic Check for Raw Japanese ---
        if (lang === 'en' && /[亜-熙ぁ-んァ-ヶ]/.test(line) && !line.includes('EFFECT:') && !line.includes('CONDITION:') && !line.includes('COST:')) {
            translatedLines.push(translateHeuristic(line, tData));
            continue;
        }

        if (line.startsWith('TRIGGER:')) {
            const triggerKey = line.replace('TRIGGER:', '').trim();
            const id = TriggerType[triggerKey];
            if (id !== undefined && tData.triggers[id]) {
                translatedLines.push(tData.triggers[id]);
            } else {
                const displayLabel = triggerKey.toLowerCase()
                    .split('_')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                translatedLines.push(lang === 'jp' ? `【${triggerKey}】` : `[${displayLabel}]`);
            }
            continue;
        }

        let prefix = "", body = line, isPseudo = false;
        const upperLine = line.toUpperCase();
        if (upperLine.startsWith('CONDITION:')) { prefix = tData.misc.condition_prefix; body = line.substr(10).trim(); isPseudo = true; }
        else if (upperLine.startsWith('COST:')) { prefix = tData.misc.cost_prefix; body = line.substr(5).trim(); isPseudo = true; }
        else if (upperLine.startsWith('EFFECT:')) { prefix = tData.misc.effect_prefix; body = line.substr(7).trim(); isPseudo = true; }
        else if (line.match(/^\d+:/)) { const m = line.match(/^\d+:/); prefix = m[0] + " "; body = line.replace(m[0], '').trim(); isPseudo = true; }
        else if (line.includes('->') || Object.keys(EffectType).some(op => line.includes(op + '('))) {
            isPseudo = true;
        }

        if (!isPseudo) {
            translatedLines.push(line);
            continue;
        }

        const isOnce = body.toLowerCase().includes('(once per turn)');
        if (isOnce) body = body.replace(/\(once per turn\)/i, '').trim();
        const isOpt = body.toLowerCase().includes('(optional)');
        if (isOpt) body = body.replace(/\(optional\)/i, '').trim();

        const translatedBody = body.split(';').map(sub => {
            const parts = sub.split('->').map(s => s.trim());
            const consumedKeys = new Set();
            if (parts.length > 1) {
                const trgtMatch = parts[1].match(/^(\w+)(?:\s*\{(.*?)\})?/);
                const allParams = (trgtMatch && trgtMatch[2]) ? parseParams(trgtMatch[2]) : {};
                const actOp = parts[0].split('(')[0];
                const joiner = (lang === 'en' ? ((actOp.startsWith('RECOVER') || actOp === 'MOVE_TO_DECK') ? " from " : " to ") : " ");
                const actionPart = translatePart(parts[0], tData, lang, allParams, consumedKeys);
                const targetPart = translatePart(parts[1], tData, lang, allParams, consumedKeys);
                return actionPart + joiner + targetPart;
            }
            return translatePart(parts[0], tData, lang, {}, consumedKeys);
        }).join('; ');

        let result = prefix + translatedBody;
        if (isOnce) result = tData.misc.once_per_turn + "\n" + result;
        if (isOpt) result += tData.misc.optional;
        translatedLines.push(result);
    }

    return translatedLines.join('\n');
}

function translatePart(part, tData, lang, allParams, consumedKeys) {
    if (!part) return '';
    const opcodeMatch = part.match(/^(\w+)(?:\((.*)\))?(?:\s*\{(.*?)\})?/);
    if (!opcodeMatch) return part;

    const opcode = opcodeMatch[1];
    const args = opcodeMatch[2] ? opcodeMatch[2].split(',') : [];
    const localParams = opcodeMatch[3] ? parseParams(opcodeMatch[3]) : {};

    // Merge params: local part params override global block params
    const combinedParams = { ...allParams, ...localParams };

    let template = tData.opcodes[opcode] || opcode;
    let translated = template;

    // Numerical value substitution
    if (args.length > 0) {
        translated = translated.replace(/{value}/g, args[0]);
    }

    let targetNames = "";
    let pStrings = [];
    let colorVal = combinedParams.COLOR;

    // Parameter substitution
    for (const [k, v] of Object.entries(combinedParams)) {
        const placeholder = `{${k.toLowerCase()}}`;
        let replacement = null;

        if (tData.params[k]) {
            replacement = tData.params[k][v] || v;
        } else if (k === 'NAME' || k === 'NAMES') {
            replacement = v.split('/').map(n => NAME_MAP[n] || n).join(lang === 'en' ? ' & ' : '＆');
        } else if (k === 'COLOR') {
            replacement = tData.params.COLOR[v] || v;
        } else {
            replacement = v;
        }

        if (replacement !== null) {
            if (translated.includes(placeholder)) {
                translated = translated.replace(placeholder, replacement);
                consumedKeys.add(k);
            } else if (k === 'KEYWORD' && translated.includes('{keyword}')) {
                translated = translated.replace('{keyword}', replacement);
                consumedKeys.add(k);
            } else if (k === 'GROUP' && translated.includes('{group}')) {
                translated = translated.replace('{group}', replacement);
                consumedKeys.add(k);
            } else if (k === 'ZONE' && translated.includes('{zone}')) {
                translated = translated.replace('{zone}', replacement);
                consumedKeys.add(k);
            } else if (k === 'NAME' || k === 'NAMES') {
                targetNames = replacement;
            } else if (!consumedKeys.has(k)) {
                pStrings.push(replacement);
                consumedKeys.add(k);
            }
        }
    }

    // Color/Icon handling
    if (colorVal && (opcode === 'HEARTS' || opcode === 'ADD_HEARTS' || opcode === 'SET_HEARTS' || opcode === 'PAY_ENERGY' || opcode === 'ENERGY')) {
        const cName = tData.params.COLOR[colorVal] || colorVal;
        const iconTag = (opcode.includes('HEART')) ? `【${cName} Hearts】` : `【${cName} Energy】`;
        if (lang === 'jp') {
            const jpCName = tData.params.COLOR[colorVal] || colorVal;
            const jpIconTag = (opcode.includes('HEART')) ? `【${jpCName}ハート】` : `【${jpCName}エネ】`;
            translated = translated.replace(/【ハート】|ハート|【エネ】|エネ/, jpIconTag);
        } else {
            translated = translated.replace(/【Hearts】|Hearts|【Energy】|Energy/, iconTag);
        }
    }

    if (lang === 'en') translated = translated.replace('{filter}', "").replace('{to}', "the Deck");

    if (opcode === 'CARD_DISCARD') {
        const discardText = (lang === 'en' ? "Discard" : "控え室");
        translated = targetNames ? `${discardText} (${targetNames})` : discardText;
    } else {
        if (translated.includes('{name}')) translated = translated.replace('{name}', targetNames || "");
        else if (targetNames) translated += ` (${targetNames})`;
        if (pStrings.length > 0) translated += ` [${pStrings.join(', ')}]`;
    }

    return translated.trim().replace(/\s+/g, ' ');
}

function translateHeuristic(text, tData) {
    if (!text) return "";
    let result = text;

    // Use heuristic patterns from JSON if available
    if (tData.heuristics && Array.isArray(tData.heuristics)) {
        for (const h of tData.heuristics) {
            const regex = new RegExp(h.jp, 'g');
            result = result.replace(regex, h.en);
        }
    }
    return result;
}

function parseParams(paramsStr) {
    const params = {};
    const pairs = paramsStr.split(',');
    for (const pair of pairs) {
        const [k, v] = pair.split('=');
        if (k && v) params[k.trim()] = v.trim();
    }
    return params;
}

export function getCurrentTranslations() {
    return translations[currentLanguage];
}
