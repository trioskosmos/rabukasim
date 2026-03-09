1.  **Analyze Q102 and Q73 for PL!N-bp1-011-R (id 4340)**:
    *   **Card Effect:** "You may put 1 card from your hand into the waiting room: Reveal cards from the top of your deck one by one until a Live card is revealed. Add that Live card to your hand, and put all other revealed cards into the waiting room."
    *   **Q73:** When revealing cards, if the main deck runs out, we must perform a "refresh" by taking the waiting room (discard pile), shuffling it to form a new deck, and then *continue* resolving the effect. The cards already revealed during this effect *are not included* in the refresh.
    *   **Q102:** What happens if there are no Live cards in the main deck OR the waiting room? "We resolve the effect as much as possible. We reveal all cards from the main deck, perform a refresh, then reveal all cards from the new main deck. At this point, the resolution of 'Reveal cards from the top of your deck one by one until a Live card is revealed' ends. Since there is no Live card to add to hand, the revealed cards are placed in the waiting room, and another refresh occurs."

2.  **Analyze Current `O_REVEAL_UNTIL` Implementation**:
    *   The current `O_REVEAL_UNTIL` code in `engine_rust_src/src/core/logic/interpreter/handlers/movement.rs` handles the iteration over the deck:
        ```rust
        O_REVEAL_UNTIL => {
            let mut found = false;
            let mut revealed_count = 0;
            while !found && !state.players[p_idx].deck.is_empty() {
                // ...
                if let Some(cid) = state.players[p_idx].deck.pop() {
                    // ... check if match
                    if matches {
                        // ... move to hand/discard
                        found = true;
                    } else {
                        state.players[p_idx].discard.push(cid);
                    }
                }
            }
        }
        ```
    *   **Flaws**:
        *   It directly pushes non-matching cards to the discard pile *immediately*. This means they will be part of the deck refresh if the deck runs out during the reveal! This violates Q73. It should hold the revealed cards aside until the end of the effect or until a live card is found, and then put them in the waiting room.
        *   It doesn't handle deck refresh correctly within the loop if the deck runs out before finding a match. It just stops because of `!state.players[p_idx].deck.is_empty()`. It needs to refresh the deck once if the deck becomes empty and keep looking.
        *   To fully align with Q102, if a deck refresh happens, and the new deck *also* runs out without finding a match, it should stop, put the held cards in the waiting room, which will trigger *another* deck refresh.

3.  **Plan to Fix**:
    *   **Modify `O_REVEAL_UNTIL` in `engine_rust_src/src/core/logic/interpreter/handlers/movement.rs`**:
        *   Maintain a `revealed_cards` vector (using `SmallVec` or `Vec`) to hold non-matching cards temporarily.
        *   Instead of a simple `while !deck.is_empty()`, we need a loop that pops from the deck. If the deck becomes empty while `!found`, we check if a refresh is needed. We should only refresh once during this reveal process to avoid infinite loops (or keep track of how many cards we checked vs deck size). Actually, the rules say "if the deck runs out, refresh. If the new deck runs out, stop". So we can use a boolean flag `has_refreshed` to allow exactly one refresh during this loop.
        *   Inside the loop:
            *   Pop card from deck.
            *   Trigger OnReveal.
            *   Check if matches.
            *   If matches:
                *   Move the *matching* card to its destination (hand or discard).
                *   `found = true`
                *   break.
            *   If not matches:
                *   Add to `revealed_cards`.
            *   If deck is empty and `!found`:
                *   If `!has_refreshed`:
                    *   `state.resolve_deck_refresh(p_idx);`
                    *   `has_refreshed = true;`
                *   If `has_refreshed` (already refreshed once and still empty):
                    *   break.
        *   After the loop:
            *   Move all cards in `revealed_cards` to the discard pile.
            *   We might need to trigger another deck refresh if putting `revealed_cards` into the discard caused something that needs a refresh? Wait, moving cards to discard doesn't trigger refresh directly, refresh is only triggered when deck runs out *and* we try to draw/deal damage/pop. BUT Q102 explicitly says "...put revealed cards in waiting room, and a refresh occurs." This implies the *new deck* ran out, so the deck is currently empty. The rules for Love Live! say if your deck is empty, you refresh immediately. So we should call `state.resolve_deck_refresh(p_idx);` or rely on a check at the end of the effect. Let's just check if the deck is empty at the very end of the handler, and if so, refresh. Actually `resolve_deck_refresh` handles checking if the deck is empty. Wait, `resolve_deck_refresh` in `game.rs` only does the refresh if `self.players[player_idx].deck.is_empty()`. So we can safely call it after pushing cards to discard.

    *   **Write QA Test**: Add a test in `engine_rust_src/src/qa_verification_tests.rs` (or similar, usually `qa_verification_tests.rs`) for Q102 and Q73. We'll use card 4340 (PL!N-bp1-011-R).

4.  **Review the Plan**: I will use `request_plan_review` with this plan.
