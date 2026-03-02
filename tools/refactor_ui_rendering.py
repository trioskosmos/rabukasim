import re


def main():
    path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\frontend\web_ui\js\ui_rendering.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # We want to replace the bodies of the extracted functions with calls to the new modules.

    # First, add the imports at the top
    if "import { CardRenderer }" not in content:
        imports = """import { CardRenderer } from './components/CardRenderer.js';
import { BoardRenderer } from './components/BoardRenderer.js';
import { ActionMenu } from './components/ActionMenu.js';
"""
        content = re.sub(r"(import { State } from '\./state\.js';)", r"\1\n" + imports, content)

    # Now we need to replace the implementations.
    # Since we know the signatures from the outline, we can use regex to replace from "renderBoard: (..." to the next function.

    replacements = {
        r"renderBoard:\s*\(state, p0, p1, validTargets = \{ stage: \{\}, discard: \{\}, hasSelection: false \}\) => \{.*?(?=\n\s*renderDeckCounts:)": "renderBoard: (state, p0, p1, validTargets = { stage: {}, discard: {}, hasSelection: false }) => {\n        BoardRenderer.renderBoard(state, p0, p1, validTargets, Rendering.showDiscardModal);\n    },",
        r"renderDeckCounts:\s*\(p0, p1\) => \{.*?(?=\n\s*renderCards:)": "renderDeckCounts: (p0, p1) => {\n        BoardRenderer.renderDeckCounts(p0, p1);\n    },",
        r"renderCards:\s*\(containerId, cards, clickable = false, mini = false, selectedIndices = \[\], validActionMap = \{\}, hasGlobalSelection = false\) => \{.*?(?=\n\s*renderStage:)": "renderCards: (containerId, cards, clickable = false, mini = false, selectedIndices = [], validActionMap = {}, hasGlobalSelection = false) => {\n        CardRenderer.renderCards(containerId, cards, clickable, mini, selectedIndices, validActionMap, hasGlobalSelection);\n    },",
        r"renderStage:\s*\(containerId, stage, clickable, validActionMap = \{\}, hasGlobalSelection = false\) => \{.*?(?=\n\s*renderEnergy:)": "renderStage: (containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) => {\n        CardRenderer.renderStage(containerId, stage, clickable, validActionMap, hasGlobalSelection);\n    },",
        r"renderEnergy:\s*\(containerId, energy, clickable = false, validActionMap = \{\}, hasGlobalSelection = false\) => \{.*?(?=\n\s*renderLiveZone:)": "renderEnergy: (containerId, energy, clickable = false, validActionMap = {}, hasGlobalSelection = false) => {\n        BoardRenderer.renderEnergy(containerId, energy, clickable, validActionMap, hasGlobalSelection, State.data);\n    },",
        r"renderLiveZone:\s*\(containerId, liveCards, visible, validActionMap = \{\}, hasGlobalSelection = false\) => \{.*?(?=\n\s*renderDiscardPile:)": "renderLiveZone: (containerId, liveCards, visible, validActionMap = {}, hasGlobalSelection = false) => {\n        CardRenderer.renderLiveZone(containerId, liveCards, visible, validActionMap, hasGlobalSelection);\n    },",
        r"renderDiscardPile:\s*\(containerId, discard, playerIdx, validActionMap = \{\}, hasGlobalSelection = false\) => \{.*?(?=\n\s*renderActiveEffects:)": "renderDiscardPile: (containerId, discard, playerIdx, validActionMap = {}, hasGlobalSelection = false) => {\n        CardRenderer.renderDiscardPile(containerId, discard, playerIdx, validActionMap, hasGlobalSelection, Rendering.showDiscardModal);\n    },",
        r"renderGameOver:\s*\(state\) => \{.*?(?=\n\s*showDiscardModal:)": "renderGameOver: (state) => {\n        ActionMenu.renderGameOver(state);\n    },",
        r"renderActions:\s*\(\) => \{.+?(?=\n\s*renderPerformanceGuide:)": "renderActions: () => {\n        ActionMenu.renderActions();\n    },",
        r"renderLookedCards:\s*\(\) => \{.+?(?=\n\s*renderPerformanceResult:)": "renderLookedCards: () => {\n        CardRenderer.renderLookedCards();\n    },",
    }

    for pattern, replacement in replacements.items():
        new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
        if count == 0:
            print(f"Warning: Failed to replace pattern starting with {pattern[:50]}")
        content = new_content

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Successfully refactored ui_rendering.js")


if __name__ == "__main__":
    main()
