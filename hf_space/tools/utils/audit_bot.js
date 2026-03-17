/**
 * Lovecasim Audit Bot
 * Automates gameplay and scans for "undefined" or broken action text.
 */
(function () {
    console.log("[AuditBot] Starting...");

    const ERROR_PATTERNS = [/undefined/i, /null/i, /\[object Object\]/];
    let actionCount = 0;
    let errorFound = false;

    async function audit() {
        if (errorFound) return;

        const actions = document.querySelectorAll('.action-btn, .sub-action');
        if (actions.length === 0) {
            // If no actions, maybe wait or force advance if stuck
            console.log("[AuditBot] No actions found. Waiting...");
            const forceBtn = document.querySelector('button[onclick="forceAdvance()"]');
            if (forceBtn) {
                console.log("[AuditBot] Forcing advance...");
                forceBtn.click();
            }
            return;
        }

        console.log(`[AuditBot] Found ${actions.length} actions.`);

        // Scan for errors
        actions.forEach(btn => {
            const text = btn.innerText || "";
            const title = btn.querySelector('.action-title')?.innerText || "";
            const details = btn.querySelector('.action-details')?.innerText || "";
            const combined = (text + " " + title + " " + details).toLowerCase();

            for (const pattern of ERROR_PATTERNS) {
                if (pattern.test(combined)) {
                    console.error(`[AuditBot] DETECTED BROKEN ACTION: "${combined}"`, btn);
                    errorFound = true;
                    window.auditError = {
                        text: combined,
                        phase: document.getElementById('diag-phase')?.innerText,
                        player: document.getElementById('diag-player')?.innerText
                    };
                    return;
                }
            }
        });

        if (errorFound) {
            console.log("[AuditBot] STOPPING DUE TO ERROR.");
            return;
        }

        // Pick a random action (prefer ID 0 "Pass" less often to keep the game moving)
        let targetAction = actions[Math.floor(Math.random() * actions.length)];

        // Strategy: if many actions, try to pick non-pass ones
        if (actions.length > 1) {
            const nonPass = Array.from(actions).filter(a => !a.innerText.includes("END PHASE") && !a.innerText.includes("フェイズ終了"));
            if (nonPass.length > 0) {
                targetAction = nonPass[Math.floor(Math.random() * nonPass.length)];
            }
        }

        console.log(`[AuditBot] Clicking action: ${targetAction.innerText.trim().split('\n')[0]}`);
        targetAction.click();
        actionCount++;

        if (actionCount > 500) {
            console.log("[AuditBot] Reached action limit. Stopping.");
            return;
        }

        // Schedule next check
        setTimeout(audit, 1000);
    }

    // Start auditing after a short delay
    setTimeout(audit, 2000);
})();
