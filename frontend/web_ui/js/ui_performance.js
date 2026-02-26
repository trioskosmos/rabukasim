/**
 * UI Performance Facade
 * Delegates to components/PerformanceRenderer.js
 */
import { PerformanceRenderer as Core } from './components/PerformanceRenderer.js';

export const PerformanceRenderer = {
    renderPerformanceGuide: () => Core.renderPerformanceGuide(),
    renderPerformanceResult: (results = null) => Core.renderPerformanceResult(results),
    renderHeartsCompact: (hearts) => Core.renderHeartsCompact(hearts),
    renderBladesCompact: (blades) => Core.renderBladesCompact(blades),
    showPerfTab: (tab) => Core.showPerfTab(tab),
    renderTurnHistory: () => Core.renderTurnHistory(),
    renderHeartProgress: (f, r) => Core.renderHeartProgress(f, r)
};
