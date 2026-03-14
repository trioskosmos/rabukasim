/**
 * ZoneViewer Component
 * Handles the display of deck, discard, and various "card list" viewports.
 */
import * as i18n from '../i18n/index.js';
import { fixImg } from '../constants.js';
import { Tooltips } from '../ui_tooltips.js';
import { State } from '../state.js';

export const ZoneViewer = {
    cache: {
        modal: null,
        title: null,
        container: null
    },

    init: () => {
        ZoneViewer.cache.modal = document.getElementById('discard-modal');
        ZoneViewer.cache.title = document.getElementById('discard-modal-title');
        ZoneViewer.cache.container = document.getElementById('discard-modal-cards');
    },

    showDiscard: (playerIdx) => {
        if (!ZoneViewer.cache.modal) ZoneViewer.init();
        const state = State.data;
        if (!state) return;

        const player = state.players[playerIdx];
        const discard = player.discard || [];
        const isMe = playerIdx === State.perspectivePlayer;
        const count = discard.length;

        ZoneViewer.cache.title.textContent = isMe ? i18n.t('your_discard_title', { count }) : i18n.t('opp_discard_title', { count });
        ZoneViewer.cache.container.innerHTML = '';
        ZoneViewer.cache.container.className = 'selection-grid';

        if (discard.length === 0) {
            ZoneViewer.cache.container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; opacity: 0.5; padding: 40px;">${i18n.t('no_cards_discard')}</div>`;
        } else {
            discard.forEach((card) => {
                const div = ZoneViewer._createCardElement(card);
                ZoneViewer.cache.container.appendChild(div);
            });
        }
        ZoneViewer.cache.modal.style.display = 'flex';
    },

    showZoneViewer: (playerIdx) => {
        if (!ZoneViewer.cache.modal) ZoneViewer.init();
        const state = State.data;
        if (!state) return;

        const player = state.players[playerIdx];
        const isMe = playerIdx === State.perspectivePlayer;

        ZoneViewer.cache.title.textContent = isMe ? i18n.t('your_viewer_title') : i18n.t('opp_viewer_title');
        ZoneViewer.cache.container.innerHTML = '';
        ZoneViewer.cache.container.className = 'zone-viewer-grid';

        const addSection = (label, cards, isDeck = false) => {
            if (!cards || cards.length === 0) return;

            const section = document.createElement('div');
            section.className = 'zone-viewer-section';
            section.innerHTML = `<h3>${label} (${cards.length})</h3>`;

            const grid = document.createElement('div');
            grid.className = 'selection-grid';

            let sortedCards = [...cards];
            if (isDeck) sortedCards.sort((a, b) => (a.id || 0) - (b.id || 0));

            sortedCards.forEach(card => {
                const div = ZoneViewer._createCardElement(card, true);
                grid.appendChild(div);
            });

            section.appendChild(grid);
            ZoneViewer.cache.container.appendChild(section);
        };

        const addEmptySection = (label) => {
            const section = document.createElement('div');
            section.className = 'zone-viewer-section';
            section.innerHTML = `<h3>${label} (0)</h3><div style="opacity:0.5; padding:10px;">${i18n.t('no_cards_zone')}</div>`;
            ZoneViewer.cache.container.appendChild(section);
        };

        const deck = player.deck_cards || player.deck || player.full_deck || [];
        const energyDeck = player.energy_deck_cards || player.energy_deck || [];

        deck.length > 0 ? addSection(i18n.t('member_deck_rem'), deck, true) : addEmptySection(i18n.t('member_deck_rem'));
        energyDeck.length > 0 ? addSection(i18n.t('energy_deck_rem'), energyDeck, true) : addEmptySection(i18n.t('energy_deck_rem'));

        addSection(i18n.t('hand'), player.hand);
        addSection(i18n.t('stage'), player.stage);
        addSection(i18n.t('energy'), player.energy ? player.energy.map(e => e.card || e) : []);
        addSection(i18n.t('success_zone'), player.success_lives || player.success_pile);
        addSection(i18n.t('discard_pile'), player.discard);

        ZoneViewer.cache.modal.style.display = 'flex';
    },

    _createCardElement: (card, isMini = false) => {
        if (!card) return document.createElement('div');
        const div = document.createElement('div');
        div.className = isMini ? 'card card-mini' : 'card';
        const imgPath = card.img || card.img_path || '';
        div.innerHTML = `<img src="${fixImg(imgPath)}" onerror="this.src='img/texticon/icon_energy.png'">`;
        
        const rawText = Tooltips.getEffectiveRawText(card);
        if (rawText) div.setAttribute('data-text', rawText);
        if (card.id !== undefined) div.setAttribute('data-card-id', card.id);
        
        Tooltips.attachCardData(div, card);
        return div;
    }
};
