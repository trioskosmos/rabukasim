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
