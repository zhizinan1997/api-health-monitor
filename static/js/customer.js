/**
 * Customer Page JavaScript
 * Loads and displays model connectivity status
 */

// Configuration
const API_BASE = '';
const REFRESH_INTERVAL = 60000; // 60 seconds

// State
let settings = null;
let modelStats = [];

// DOM Elements
const loadingEl = document.getElementById('loading');
const emptyStateEl = document.getElementById('empty-state');
const modelListEl = document.getElementById('model-list');
const lastUpdatedEl = document.getElementById('last-updated');
const modelCountEl = document.getElementById('model-count');
const siteTitleEl = document.getElementById('site-title');
const logoEl = document.getElementById('logo');
const langSwitchEl = document.getElementById('lang-switch');
const lastCheckTimeEl = document.getElementById('last-check-time');
const nextCheckTimeEl = document.getElementById('next-check-time');

/**
 * Initialize the page
 */
async function init() {
    updateUILanguage();
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
 * Switch language
 */
function switchLanguage() {
    i18n.switchLang();
    updateUILanguage();
    renderModelList();
}

/**
 * Update UI with current language
 */
function updateUILanguage() {
    // Update language switch button
    langSwitchEl.textContent = i18n.t('lang.switch');

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = i18n.t(el.dataset.i18n);
    });

    // Update footer
    updateFooter();
}

/**
 * Update footer text
 */
function updateFooter() {
    const footerEl = document.getElementById('footer-text');
    if (footerEl) {
        footerEl.innerHTML = i18n.t('site.footer', { count: `<span id="model-count">${modelStats.length}</span>` });
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
    // Check the most recent hourly status slot for current status
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
        // No recent test, fall back to rate check
        isOnline = model.rate_1d >= 95;
    }

    const statusClass = isOnline === null ? 'unknown' : (isOnline ? 'online' : 'offline');
    const statusText = isOnline === null ? i18n.t('status.noData') : (isOnline ? i18n.t('status.online') : i18n.t('status.offline'));

    const progressBar = createProgressBar(model.hourly_status);
    const statsRow = createStatsRow(model);
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
                <div class="progress-label">
                    <span>${i18n.t('progress.24hAgo')}</span>
                    <span>${i18n.t('progress.now')}</span>
                </div>
                <div class="progress-bar">
                    ${progressBar}
                </div>
            </div>
            
            <div class="stats-row">
                ${statsRow}
            </div>
            
            ${errorInfo}
        </div>
    `;
}

/**
 * Create progress bar slots
 */
function createProgressBar(hourlyStatus) {
    return hourlyStatus.map((status, index) => {
        let slotClass = 'unknown';
        let tooltip = `${formatHour(status.hour)}: ${i18n.t('progress.noData')}`;

        if (status.success === true) {
            slotClass = 'success';
            tooltip = `${formatHour(status.hour)}: ✓ ${i18n.t('progress.success')}`;
        } else if (status.success === false) {
            slotClass = 'failure';
            tooltip = `${formatHour(status.hour)}: ✗ ${i18n.t('progress.failure')}`;
        }

        return `<div class="progress-slot ${slotClass}" data-tooltip="${tooltip}"></div>`;
    }).join('');
}

/**
 * Create stats row - 只显示24小时成功率，基于格子颜色计算
 */
function createStatsRow(model) {
    // 基于24个格子计算成功率：绿色格子数/24*100%
    let greenCount = 0;
    let totalSlots = 0;
    
    if (model.hourly_status && model.hourly_status.length > 0) {
        model.hourly_status.forEach(status => {
            if (status.success === true) {
                greenCount++;
                totalSlots++;
            } else if (status.success === false) {
                totalSlots++;
            }
            // success === null 的不计入总数
        });
    }
    
    // 计算成功率
    let rate24h = null;
    if (totalSlots > 0) {
        rate24h = Math.round(greenCount / 24 * 100 * 10) / 10; // 保留一位小数
    }
    
    const value = rate24h !== null ? `${rate24h}%` : '--';
    const colorClass = getValueColorClass(rate24h);

    return `
        <div class="stat-item">
            <span class="stat-label">${i18n.t('stats.1d')}</span>
            <span class="stat-value ${colorClass}">${value}</span>
        </div>
    `;
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
