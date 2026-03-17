import './assets_registry.js';
import { initializeGlobals } from './compat.js';
import { AppController } from './app_controller.js';
import { ModalManager } from './utils/ModalManager.js';
import { DOM_IDS } from './constants_dom.js';

export async function initialize() {
    initializeGlobals({ restartPolling: AppController.restartPolling });
    try {
        await AppController.initialize();
    } catch (error) {
        console.error('[Init] Initialization Failed:', error);
        ModalManager.show(DOM_IDS.MODAL_ROOM);
    }
}
