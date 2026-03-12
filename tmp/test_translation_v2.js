
const NAME_MAP = {
    "\u4e0a\u539f \u6b69\u5922": "Ayumu Uehara",
    "\u6dcb\u8c37 \u304b\u306e\u3093": "Kanon Shibuya",
    "\u65e5\u91ce\u4e0b \u82b1\u5e06": "Kaho Hinoshita",
    "\u4e0a\u539f\u6b69\u5922": "Ayumu Uehara",
    "\u6dcb\u8c37\u304b\u306e\u3093": "Kanon Shibuya",
    "\u65e5\u91ce\u4e0b\u82b1\u5e06": "Kaho Hinoshita"
};

function translateCardName(name) {
    if (NAME_MAP[name]) {
        return NAME_MAP[name];
    } else if (name.includes('&') || name.includes('/') || name.includes('\uff0f') || name.includes('\uff06') || name.includes('\u30fb')) {
        const delimiters = /(&|\/|\uff0f|\uff06|\u30fb)/;
        const parts = name.split(delimiters);
        const translatedParts = parts.map(part => {
            const trimmed = part.trim();
            if (!trimmed) return part;
            if (trimmed.length === 1 && "&/\uff0f\uff06\u30fb".includes(trimmed)) return part;
            return NAME_MAP[trimmed] || trimmed;
        });
        return translatedParts.join('');
    }
    return name;
}

const tests = [
    "\u4e0a\u539f\u6b69\u5922",
    "\u4e0a\u539f\u6b69\u5922&\u6dcb\u8c37\u304b\u306e\u3093&\u65e5\u91ce\u4e0b\u82b1\u5e06",
    "\u6dcb\u8c37\u304b\u306e\u3093\uff0f\u65e5\u91ce\u4e0b\u82b1\u5e06",
    "Unknown Character",
    "\u4e0a\u539f\u6b69\u5922\uff06\u6dcb\u8c37\u304b\u306e\u3093"
];

tests.forEach(t => {
    console.log(`Original: ${t}`);
    console.log(`Translated: ${translateCardName(t)}`);
    console.log('---');
});
