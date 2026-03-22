
import { InteractionAdapter } from './js/interaction_adapter.js';

// Mock state
const state = {
    legal_actions: [
        { id: 11000, type: 'LOOK_AND_CHOOSE' },
        { id: 11005, type: 'LOOK_AND_CHOOSE' },
        { id: 0, type: 'PASS' }
    ],
    pending_choice: {
        choice_type: 18, // LookAndChoose
        selection_cards: [{}, {}, {}, {}, {}, {}] // 6 cards
    }
};

const valid = InteractionAdapter.get_valid_targets(state);

console.log("Valid targets:", JSON.stringify(valid, null, 2));

if (valid.selection && valid.selection[0] === 11000 && valid.selection[5] === 11005) {
    console.log("VERIFICATION SUCCESS: 11000 range correctly mapped to selection field.");
} else {
    console.error("VERIFICATION FAILED: 11000 range NOT correctly mapped.");
    process.exit(1);
}
