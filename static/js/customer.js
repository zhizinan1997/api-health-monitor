/**
 * Customer Page JavaScript
 * Loads and displays model connectivity status
 */

// Configuration
const API_BASE = '';
const REFRESH_INTERVAL = 60000; // 60 seconds

// State
let modelStats = [];

// DOM Elements
const loadingEl = document.getElementById('loading');
const emptyStateEl = document.getElementById('empty-state');
const modelListEl = document.getElementById('model-list');
const siteTitleEl = document.getElementById('site-title');
const logoEl = document.getElementById('logo');
const lastCheckTimeEl = document.getElementById('last-check-time');
const nextCheckTimeEl = document.getElementById('next-check-time');

/**
 * Initialize the page
 */
async function init() {
    await loadSettings();
    await loadScheduleInfo();
    await loadModelStats();

    // Auto-refresh
    setInterval(async () => {
        await loadScheduleInfo();
        await loadModelStats();
    }, REFRESH_INTERVAL);
}

/**
 * Update footer text
 */
function updateFooter() {
    const footerEl = document.getElementById('footer-text');
    if (footerEl) {
        footerEl.innerHTML = `正在监控 <span id="model-count">${modelStats.length}</span> 个模型 • 每60秒自动刷新`;
    }
}

/**
 * Load site settings (logo, title)
 */
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings/public`);
        if (response.ok) {
            const settings = await response.json();

            // Update site title
            if (settings.site_title) {
                siteTitleEl.textContent = settings.site_title;
                document.title = settings.site_title;
            }

            // Update logo
            if (settings.logo_url) {
                logoEl.src = settings.logo_url;
                logoEl.classList.remove('hidden');
                logoEl.onerror = () => {
                    logoEl.classList.add('hidden');
                };
            }
        }
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

/**
 * Load schedule info (last and next check times)
 */
async function loadScheduleInfo() {
    try {
        const response = await fetch(`${API_BASE}/api/tests/schedule-info`);
        if (response.ok) {
            const info = await response.json();
            
            if (lastCheckTimeEl) {
                lastCheckTimeEl.textContent = info.last_run_time || i18n.t('schedule.notYet');
            }
            if (nextCheckTimeEl) {
                nextCheckTimeEl.textContent = info.next_run_time || '--';
            }
        }
    } catch (error) {
        console.error('Failed to load schedule info:', error);
    }
}

/**
 * Load model statistics
 */
async function loadModelStats() {
    try {
        const response = await fetch(`${API_BASE}/api/tests/stats`);

        if (!response.ok) {
            throw new Error('Failed to fetch stats');
        }

        modelStats = await response.json();

        // Update UI
        renderModelList();
        updateLastUpdated();

    } catch (error) {
        console.error('Failed to load model stats:', error);
        showError();
    }
}

/**
 * Render the model list
 */
function renderModelList() {
    loadingEl.classList.add('hidden');

    if (modelStats.length === 0) {
        emptyStateEl.classList.remove('hidden');
        modelListEl.classList.add('hidden');
        updateFooter();
        return;
    }

    emptyStateEl.classList.add('hidden');
    modelListEl.classList.remove('hidden');
    updateFooter();

    modelListEl.innerHTML = modelStats.map(model => createModelCard(model)).join('');
}

/**
 * Create a model card HTML
 */
function createModelCard(model) {
    // Check current status
    const lastStatus = model.hourly_status && model.hourly_status.length > 0
        ? model.hourly_status[model.hourly_status.length - 1]
        : null;

    // Model is online if the most recent test was successful
    let isOnline = null;
    if (lastStatus && lastStatus.success === true) {
        isOnline = true;
    } else if (lastStatus && lastStatus.success === false) {
        isOnline = false;
    } else if (model.rate_1d !== null) {
        isOnline = model.rate_1d >= 95;
    }

    const statusClass = isOnline === null ? 'unknown' : (isOnline ? 'online' : 'offline');
    const statusText = isOnline === null ? '暂无数据' : (isOnline ? '在线' : '异常');

    const progressBar = createProgressBar(model.hourly_status);
    const rate24h = calculateRate24h(model.hourly_status);
    const errorInfo = createErrorInfo(model);

    return `
        <div class="model-card">
            <div class="model-header">
                <div class="model-info">
                    ${model.logo_url ? `<img src="${escapeHtml(model.logo_url)}" class="model-logo" alt="logo" onerror="this.style.display='none'">` : ''}
                    <div>
                        <div class="model-name">${escapeHtml(model.display_name)}</div>
                    </div>
                </div>
                <div class="model-status ${statusClass}">
                    <span class="status-dot"></span>
                    ${statusText}
                </div>
            </div>
            
            <div class="progress-section">
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        ${progressBar}
                    </div>
                    <div class="progress-ticks">
                        <span>24h前</span>
                        <span>18h</span>
                        <span>12h</span>
                        <span>6h</span>
                        <span>现在</span>
                    </div>
                </div>
                <div class="rate-badge ${getValueColorClass(rate24h)}">
                    <span class="rate-value">${rate24h !== null ? rate24h + '%' : '--'}</span>
                    <span class="rate-label">24h可用</span>
                </div>
            </div>
            
            ${errorInfo}
        </div>
    `;
}

/**
 * Create progress bar slots with tooltips
 */
function createProgressBar(hourlyStatus) {
    return hourlyStatus.map((status, index) => {
        let slotClass = 'unknown';
        let tooltip = `${formatHour(status.hour)}: 无数据`;

        if (status.success === true) {
            slotClass = 'success';
            tooltip = `${formatHour(status.hour)}: ✓ 正常`;
        } else if (status.success === false) {
            slotClass = 'failure';
            tooltip = `${formatHour(status.hour)}: ✗ 故障`;
        }

        return `<div class="progress-slot ${slotClass}" data-tooltip="${tooltip}"></div>`;
    }).join('');
}

/**
 * Calculate 24h success rate based on green slots
 */
function calculateRate24h(hourlyStatus) {
    if (!hourlyStatus || hourlyStatus.length === 0) return null;
    
    let greenCount = 0;
    hourlyStatus.forEach(status => {
        if (status.success === true) greenCount++;
    });
    
    return Math.round(greenCount / 24 * 100 * 10) / 10;
}

/**
 * Create error info section
 */
function createErrorInfo(model) {
    // Check the most recent hourly status slot for current status
    const lastStatus = model.hourly_status && model.hourly_status.length > 0
        ? model.hourly_status[model.hourly_status.length - 1]
        : null;

    // Model is online if the most recent test was successful
    const isOnline = lastStatus && lastStatus.success === true;

    // Don't show error if model is currently online or has no error
    if (isOnline || (!model.last_error_code && !model.last_error_message)) {
        return '';
    }

    const errorCode = model.last_error_code ? `<span class="error-code">Error ${model.last_error_code}</span>` : '';
    const errorMessage = model.last_error_message || 'Unknown error';

    return `
        <div class="error-info">
            <div class="error-title">${i18n.t('error.lastError')}</div>
            <div class="error-message">${errorCode}${escapeHtml(errorMessage)}</div>
        </div>
    `;
}

/**
 * Get color class based on value
 */
function getValueColorClass(value) {
    if (value === null) return 'neutral';
    if (value >= 99) return 'good';
    if (value >= 95) return 'warning';
    return 'bad';
}

/**
 * Format hour for display
 */
function formatHour(hour) {
    return `${hour.toString().padStart(2, '0')}:00`;
}

/**
 * Update last updated timestamp
 */
function updateLastUpdated() {
    const now = new Date();
    lastUpdatedEl.textContent = now.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Show error state
 */
function showError() {
    loadingEl.classList.add('hidden');
    emptyStateEl.innerHTML = `
        <div class="empty-icon">⚠️</div>
        <h2>${i18n.t('site.error.title')}</h2>
        <p>${i18n.t('site.error.desc')}</p>
    `;
    emptyStateEl.classList.remove('hidden');
    modelListEl.classList.add('hidden');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global function for language switch
window.switchLanguage = switchLanguage;

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
