
const NAME_MAP = {
    "上原 歩夢": "Ayumu Uehara",
    "澁谷 かのん": "Kanon Shibuya",
    "日野下 花帆": "Kaho Hinoshita",
    "上原歩夢": "Ayumu Uehara",
    "澁谷かのん": "Kanon Shibuya",
    "日野下花帆": "Kaho Hinoshita"
};

function translateCardName(name) {
    if (NAME_MAP[name]) {
        return NAME_MAP[name];
    } else if (name.includes('&') || name.includes('/') || name.includes('／') || name.includes('＆') || name.includes('・')) {
        const delimiters = /(&|\/|／|＆|・)/;
        const parts = name.split(delimiters);
        const translatedParts = parts.map(part => {
            const trimmed = part.trim();
            if (!trimmed) return part;
            if (trimmed.length === 1 && "&/／＆・".includes(trimmed)) return part;
            return NAME_MAP[trimmed] || trimmed;
        });
        return translatedParts.join('');
    }
    return name;
}

const tests = [
    "上原歩夢",
    "上原歩夢&澁谷かのん&日野下花帆",
    "澁谷かのん／日野下花帆",
    "Unknown Character",
    "上原歩夢＆澁谷かのん"
];

tests.forEach(t => {
    console.log(`Original: ${t}`);
    console.log(`Translated: ${translateCardName(t)}`);
    console.log('---');
});
