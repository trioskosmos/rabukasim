/**
 * UI Logs Facade
 * Delegates to components/LogRenderer.js, utils/LogFilter.js, and utils/PerformanceMonitor.js
 */
import { LogRenderer } from './components/LogRenderer.js';
import { LogFilter } from './utils/LogFilter.js';
import { PerformanceMonitor } from './utils/PerformanceMonitor.js';

export const Logs = {
    // --- Rendering ---
    renderRuleLog: (containerId) => LogRenderer.renderRuleLog(containerId),
    renderActiveAbilities: (containerId, abilities) => LogRenderer.renderActiveAbilities(containerId, abilities),
    renderActiveEffects: (state, p0, p1, t) => LogRenderer.renderActiveEffects(state, p0, p1, t),
    updateLogDifferential: (containerId) => LogRenderer.updateLogDifferential(containerId),

    // --- Filtering ---
    get filterState() { return LogFilter.filterState; },
    applyFilters: (events) => LogFilter.applyFilters(events),
    toggleEventType: (eventType) => {
        LogFilter.toggleEventType(eventType);
        LogRenderer.renderRuleLog();
    },
    togglePlayer: (playerId) => {
        LogFilter.togglePlayer(playerId);
        LogRenderer.renderRuleLog();
    },
    setSearchText: (text) => {
        LogFilter.setSearchText(text);
        LogRenderer.renderRuleLog();
    },
    setTurnFilter: (turn) => {
        LogFilter.setTurnFilter(turn);
        LogRenderer.renderRuleLog();
    },
    resetFilters: () => {
        LogFilter.resetFilters();
        LogRenderer.renderRuleLog();
    },
    renderFilterControls: (container, t) => LogFilter.renderFilterControls(container, t),

    // --- Performance ---
    startPerfMeasure: () => PerformanceMonitor.startPerfMeasure(),
    endPerfMeasure: (startMark) => PerformanceMonitor.endPerfMeasure(startMark),
    recordEntryCount: (count) => PerformanceMonitor.recordEntryCount(count),
    getPerfReport: () => PerformanceMonitor.getPerfReport(),
    checkPerformance: (threshold) => PerformanceMonitor.checkPerformance(threshold)
};
