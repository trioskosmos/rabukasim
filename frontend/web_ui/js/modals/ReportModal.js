import { Network } from '../network.js';

export const ReportModal = {
    openReportModal: () => {
        const modal = document.getElementById('report-modal');
        if (modal) modal.style.display = 'flex';
    },

    closeReportModal: () => {
        const modal = document.getElementById('report-modal');
        if (modal) modal.style.display = 'none';
    },

    submitReport: async () => {
        const explanation = document.getElementById('report-explanation').value;
        if (!explanation) {
            alert("Please provide an explanation of the issue.");
            return;
        }

        const success = await Network.submitReport(explanation);
        if (success) {
            alert("Report submitted successfully! Thank you for your feedback.");
            document.getElementById('report-explanation').value = "";
            ReportModal.closeReportModal();
        } else {
            alert("Failed to submit report. You can still 'Download JSON' to save it manually.");
        }
    },

    downloadReport: () => {
        const explanation = document.getElementById('report-explanation').value;
        const reportData = Network._buildSlimReport(explanation);
        reportData.userAgent = navigator.userAgent;

        const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        a.download = `lovecasim_report_${ts}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};
