import { DOMUtils } from './utils/DOMUtils.js';
import { DOM_IDS } from './constants_dom.js';

document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const leftSidebar = DOMUtils.getElement(DOM_IDS.SIDEBAR_LEFT);
    const rightSidebar = DOMUtils.getElement(DOM_IDS.SIDEBAR_RIGHT);
    const resizerLeft = DOMUtils.getElement(DOM_IDS.RESIZER_LEFT);
    const resizerRight = DOMUtils.getElement(DOM_IDS.RESIZER_RIGHT);

    const STORAGE_KEY_LEFT = 'lovelive_layout_left_width';
    const STORAGE_KEY_RIGHT = 'lovelive_layout_right_width';

    // Min/Max constraints
    const MIN_WIDTH = 150;
    const MAX_WIDTH_PCT = 0.45; // 45% of screen width

    // Restore Preferences
    const savedLeftObj = localStorage.getItem(STORAGE_KEY_LEFT);
    const savedRightObj = localStorage.getItem(STORAGE_KEY_RIGHT);

    if (savedLeftObj && leftSidebar) DOMUtils.setStyle(DOM_IDS.SIDEBAR_LEFT, 'width', savedLeftObj + 'px');
    if (savedRightObj && rightSidebar) DOMUtils.setStyle(DOM_IDS.SIDEBAR_RIGHT, 'width', savedRightObj + 'px');

    // Drag State
    let isResizingLeft = false;
    let isResizingRight = false;

    // --- Left Resizer Logic ---
    if (resizerLeft) {
        resizerLeft.addEventListener('mousedown', (e) => {
            isResizingLeft = true;
            resizerLeft.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none'; // Prevent text selection
        });
    }

    // --- Right Resizer Logic ---
    if (resizerRight) {
        resizerRight.addEventListener('mousedown', (e) => {
            isResizingRight = true;
            resizerRight.classList.add('resizing');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
    }

    // --- Global Mouse Move ---
    document.addEventListener('mousemove', (e) => {
        if (!isResizingLeft && !isResizingRight) return;

        const containerWidth = window.innerWidth;

            if (isResizingLeft && leftSidebar) {
            // New Width = Mouse X position
            let newWidth = e.clientX;

            // Constrain
            if (newWidth < MIN_WIDTH) newWidth = MIN_WIDTH;
            if (newWidth > containerWidth * MAX_WIDTH_PCT) newWidth = containerWidth * MAX_WIDTH_PCT;

            leftSidebar.style.width = newWidth + 'px';
        }

            if (isResizingRight && rightSidebar) {
            // New Width = Container Width - Mouse X position
            let newWidth = containerWidth - e.clientX;

            // Constrain
            if (newWidth < MIN_WIDTH) newWidth = MIN_WIDTH;
            if (newWidth > containerWidth * MAX_WIDTH_PCT) newWidth = containerWidth * MAX_WIDTH_PCT;

            rightSidebar.style.width = newWidth + 'px';
        }
    });

    // --- Global Mouse Up ---
    document.addEventListener('mouseup', () => {
        if (isResizingLeft) {
            isResizingLeft = false;
            if (resizerLeft) resizerLeft.classList.remove('resizing');
            if (leftSidebar) localStorage.setItem(STORAGE_KEY_LEFT, parseInt(leftSidebar.style.width));
        }
        if (isResizingRight) {
            isResizingRight = false;
            if (resizerRight) resizerRight.classList.remove('resizing');
            if (rightSidebar) localStorage.setItem(STORAGE_KEY_RIGHT, parseInt(rightSidebar.style.width));
        }

        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    });
});

/**
 * Mobile Sidebar Logic
 */
export function toggleSidebar() {
    const sidebars = document.querySelectorAll('.sidebar');
    const btn = DOMUtils.getElement(DOM_IDS.MOBILE_SIDEBAR_TOGGLE);
    if (!sidebars.length || !btn) return;

    let isActive = false;
    sidebars.forEach(s => {
        s.classList.toggle('active');
        if (s.classList.contains('active')) isActive = true;
    });

    document.body.classList.toggle('sidebar-open');

    if (isActive) {
        btn.textContent = 'X';
        btn.style.background = '#444';
    } else {
        btn.textContent = '=';
        btn.style.background = 'var(--accent-pink)';
    }
}

/**
 * Tabbed Board Switching
 */
export function switchBoard(side) {
    const playerBoard = DOMUtils.getElement(DOM_IDS.CONTAINER_BOARD_PLAYER);
    const opponentBoard = DOMUtils.getElement(DOM_IDS.CONTAINER_BOARD_OPPONENT);
    const playerBtn = DOMUtils.getElement(DOM_IDS.BTN_SHOW_PLAYER);
    const opponentBtn = DOMUtils.getElement(DOM_IDS.BTN_SHOW_OPPONENT);

    if (!playerBoard || !opponentBoard || !playerBtn || !opponentBtn) return;

    if (side === 'player') {
        DOMUtils.show(DOM_IDS.CONTAINER_BOARD_PLAYER);
        DOMUtils.hide(DOM_IDS.CONTAINER_BOARD_OPPONENT);
        DOMUtils.addClass(DOM_IDS.BTN_SHOW_PLAYER, 'active');
        DOMUtils.removeClass(DOM_IDS.BTN_SHOW_OPPONENT, 'active');
    } else {
        DOMUtils.hide(DOM_IDS.CONTAINER_BOARD_PLAYER);
        DOMUtils.show(DOM_IDS.CONTAINER_BOARD_OPPONENT);
        DOMUtils.removeClass(DOM_IDS.BTN_SHOW_PLAYER, 'active');
        DOMUtils.addClass(DOM_IDS.BTN_SHOW_OPPONENT, 'active');
    }
}
