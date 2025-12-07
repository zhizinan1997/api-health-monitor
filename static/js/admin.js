/**
 * Admin Page JavaScript
 * Handles authentication, settings, and model management
 */

// Configuration
const API_BASE = '';

// State
let token = localStorage.getItem('admin_token');
let isSetupMode = false;
let currentPage = 1;
let autoRefreshLogs = false;
let logsInterval = null;

// DOM Elements
const authPage = document.getElementById('auth-page');
const dashboard = document.getElementById('admin-dashboard');
const authForm = document.getElementById('auth-form');
const authSubtitle = document.getElementById('auth-subtitle');
const authButton = document.getElementById('auth-button');
const confirmPasswordGroup = document.getElementById('confirm-password-group');
const authError = document.getElementById('auth-error');
const langSwitchEl = document.getElementById('lang-switch');
const langSwitchDashboard = document.getElementById('lang-switch-dashboard');

/**
 * Initialize the page
 */
async function init() {
    updateUILanguage();

    // Check if admin is initialized
    const status = await checkAdminStatus();

    if (!status.initialized) {
        showSetupMode();
    } else if (token) {
        // Validate existing token
        const valid = await validateToken();
        if (valid) {
            showDashboard(status.username);
        } else {
            showLoginMode();
        }
    } else {
        showLoginMode();
    }

    // Setup event listeners
    setupEventListeners();
}

/**
 * Switch language
 */
function switchLanguage() {
    i18n.switchLang();
    updateUILanguage();
}

/**
 * Update UI with current language
 */
function updateUILanguage() {
    // Update both language switch buttons
    const langText = i18n.t('lang.switch');
    if (langSwitchEl) langSwitchEl.textContent = langText;
    if (langSwitchDashboard) langSwitchDashboard.textContent = langText;

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = i18n.t(el.dataset.i18n);
    });

    // Update placeholders
    document.querySelectorAll('[data-placeholder-i18n]').forEach(el => {
        el.placeholder = i18n.t(el.dataset['placeholder-i18n'] || el.getAttribute('data-placeholder-i18n'));
    });

    // Update page info
    const pageInfo = document.getElementById('page-info');
    if (pageInfo) {
        pageInfo.textContent = i18n.t('logs.page', { page: currentPage });
    }

    // Update auth button based on mode
    if (isSetupMode) {
        authSubtitle.textContent = i18n.t('admin.subtitle.setup');
        authButton.textContent = i18n.t('admin.createAccount');
    } else {
        authSubtitle.textContent = i18n.t('admin.subtitle.login');
        authButton.textContent = i18n.t('admin.login');
    }
}

/**
 * Check admin initialization status
 */
async function checkAdminStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/status`);
        return await response.json();
    } catch (error) {
        console.error('Failed to check admin status:', error);
        return { initialized: false };
    }
}

/**
 * Validate existing token
 */
async function validateToken() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        return response.ok;
    } catch {
        return false;
    }
}

/**
 * Show setup mode for first-time configuration
 */
function showSetupMode() {
    isSetupMode = true;
    authSubtitle.textContent = i18n.t('admin.subtitle.setup');
    authButton.textContent = i18n.t('admin.createAccount');
    confirmPasswordGroup.classList.remove('hidden');
    document.getElementById('confirm-password').required = true;
}

/**
 * Show login mode
 */
function showLoginMode() {
    isSetupMode = false;
    authSubtitle.textContent = i18n.t('admin.subtitle.login');
    authButton.textContent = i18n.t('admin.login');
    confirmPasswordGroup.classList.add('hidden');
    document.getElementById('confirm-password').required = false;
    token = null;
    localStorage.removeItem('admin_token');
}

/**
 * Show dashboard
 */
function showDashboard(username) {
    authPage.classList.add('hidden');
    dashboard.classList.remove('hidden');
    document.getElementById('admin-username').textContent = username || 'Admin';

    // Load initial data
    loadSettings();
    loadModelStatus();
    loadMonitoredModels();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Auth form
    authForm.addEventListener('submit', handleAuth);

    // Logout
    document.getElementById('logout-btn').addEventListener('click', logout);

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Status tab
    document.getElementById('test-all-btn').addEventListener('click', testAllModels);
    document.getElementById('refresh-status-btn').addEventListener('click', loadModelStatus);

    // Settings tab
    document.getElementById('fetch-models-btn').addEventListener('click', fetchAvailableModels);
    document.getElementById('save-settings-btn').addEventListener('click', saveSettings);
    document.getElementById('test-email-btn').addEventListener('click', testEmail);
    document.getElementById('test-webhook-btn').addEventListener('click', testWebhook);
    document.getElementById('test-notification-btn').addEventListener('click', testNotification);
    document.getElementById('change-password-btn').addEventListener('click', changePassword);

    // Toggle visibility for sub-settings
    document.getElementById('smtp-enabled').addEventListener('change', (e) => {
        document.getElementById('smtp-settings').style.display = e.target.checked ? 'block' : 'none';
    });
    document.getElementById('webhook-enabled').addEventListener('change', (e) => {
        document.getElementById('webhook-settings').style.display = e.target.checked ? 'block' : 'none';
    });

    // Logs tab
    document.getElementById('auto-refresh-logs').addEventListener('change', toggleLogsAutoRefresh);
    document.getElementById('log-level-filter').addEventListener('change', () => { currentPage = 1; loadLogs(); });
    document.getElementById('clear-logs-btn').addEventListener('click', clearLogs);
    document.getElementById('prev-page-btn').addEventListener('click', () => { currentPage--; loadLogs(); });
    document.getElementById('next-page-btn').addEventListener('click', () => { currentPage++; loadLogs(); });
}

/**
 * Handle authentication
 */
async function handleAuth(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    authError.classList.add('hidden');

    if (isSetupMode) {
        const confirmPassword = document.getElementById('confirm-password').value;
        if (password !== confirmPassword) {
            showAuthError(i18n.t('msg.passwordMismatch'));
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/admin/setup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                token = data.access_token;
                localStorage.setItem('admin_token', token);
                showDashboard(username);
                showToast(i18n.t('msg.accountCreated'), 'success');
            } else {
                const error = await response.json();
                showAuthError(error.detail || i18n.t('msg.connectionFailed'));
            }
        } catch (error) {
            showAuthError(i18n.t('msg.connectionFailed'));
        }
    } else {
        try {
            const response = await fetch(`${API_BASE}/api/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                token = data.access_token;
                localStorage.setItem('admin_token', token);
                showDashboard(username);
            } else {
                showAuthError(i18n.t('msg.invalidCredentials'));
            }
        } catch (error) {
            showAuthError(i18n.t('msg.connectionFailed'));
        }
    }
}

/**
 * Show auth error
 */
function showAuthError(message) {
    authError.textContent = message;
    authError.classList.remove('hidden');
}

/**
 * Logout
 */
function logout() {
    token = null;
    localStorage.removeItem('admin_token');
    dashboard.classList.add('hidden');
    authPage.classList.remove('hidden');
    showLoginMode();
}

/**
 * Switch tab
 */
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tabId}`);
        panel.classList.toggle('hidden', panel.id !== `tab-${tabId}`);
    });

    // Load tab data
    if (tabId === 'status') {
        loadModelStatus();
    } else if (tabId === 'logs') {
        loadLogs();
    }
}

/**
 * Load settings
 */
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            if (response.status === 401) {
                logout();
                return;
            }
            throw new Error('Failed to load settings');
        }

        const settings = await response.json();

        // Populate form
        document.getElementById('api-base-url').value = settings.api_base_url || '';
        document.getElementById('api-key').placeholder = settings.api_key_masked || 'sk-...';
        document.getElementById('test-interval').value = settings.test_interval_minutes;

        document.getElementById('smtp-enabled').checked = settings.smtp_enabled;
        document.getElementById('smtp-host').value = settings.smtp_host || '';
        document.getElementById('smtp-port').value = settings.smtp_port;
        document.getElementById('smtp-username').value = settings.smtp_username || '';
        document.getElementById('smtp-from').value = settings.smtp_from || '';
        document.getElementById('smtp-use-tls').checked = settings.smtp_use_tls;
        document.getElementById('admin-email').value = settings.admin_email || '';
        document.getElementById('smtp-settings').style.display = settings.smtp_enabled ? 'block' : 'none';

        document.getElementById('webhook-enabled').checked = settings.webhook_enabled;
        document.getElementById('webhook-url').value = settings.webhook_url || '';
        document.getElementById('webhook-settings').style.display = settings.webhook_enabled ? 'block' : 'none';

        document.getElementById('site-title').value = settings.site_title || '';
        document.getElementById('logo-url').value = settings.logo_url || '';

    } catch (error) {
        console.error('Failed to load settings:', error);
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Save settings
 */
async function saveSettings() {
    const settings = {
        api_base_url: document.getElementById('api-base-url').value,
        test_interval_minutes: parseInt(document.getElementById('test-interval').value) || 60,

        smtp_enabled: document.getElementById('smtp-enabled').checked,
        smtp_host: document.getElementById('smtp-host').value,
        smtp_port: parseInt(document.getElementById('smtp-port').value) || 587,
        smtp_username: document.getElementById('smtp-username').value,
        smtp_from: document.getElementById('smtp-from').value,
        smtp_use_tls: document.getElementById('smtp-use-tls').checked,
        admin_email: document.getElementById('admin-email').value,

        webhook_enabled: document.getElementById('webhook-enabled').checked,
        webhook_url: document.getElementById('webhook-url').value,

        site_title: document.getElementById('site-title').value,
        logo_url: document.getElementById('logo-url').value
    };

    // Only include API key if changed
    const apiKey = document.getElementById('api-key').value;
    if (apiKey) {
        settings.api_key = apiKey;
    }

    // Only include SMTP password if changed
    const smtpPassword = document.getElementById('smtp-password').value;
    if (smtpPassword) {
        settings.smtp_password = smtpPassword;
    }

    try {
        const response = await fetch(`${API_BASE}/api/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            showToast(i18n.t('msg.settingsSaved'), 'success');
            document.getElementById('api-key').value = '';
            document.getElementById('smtp-password').value = '';
            loadSettings();
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Fetch available models from API
 */
async function fetchAvailableModels() {
    const btn = document.getElementById('fetch-models-btn');
    const btnText = btn.querySelector('span');
    btn.disabled = true;
    btnText.textContent = i18n.t('settings.models.fetching');

    try {
        const response = await fetch(`${API_BASE}/api/models/available`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to fetch models');
        }

        const models = await response.json();
        displayAvailableModels(models);

    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = i18n.t('settings.models.fetch');
    }
}

/**
 * Display available models
 */
function displayAvailableModels(models) {
    const container = document.getElementById('available-models');
    const list = container.querySelector('.model-select-list');

    if (models.length === 0) {
        list.innerHTML = '<p class="text-muted">' + i18n.t('settings.models.noModels') + '</p>';
        container.classList.remove('hidden');
        return;
    }

    list.innerHTML = models.map(model => `
        <div class="model-select-item">
            <span>${escapeHtml(model.id)}</span>
            <input type="text" placeholder="${i18n.t('settings.models.displayName')}" value="${escapeHtml(model.id)}" data-model-id="${escapeHtml(model.id)}">
            <button class="btn btn-small btn-primary" onclick="addModel('${escapeHtml(model.id)}', this)">${i18n.t('settings.models.add')}</button>
        </div>
    `).join('');

    container.classList.remove('hidden');
}

/**
 * Add model to monitoring
 */
async function addModel(modelId, btn) {
    const displayName = btn.previousElementSibling.value || modelId;
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/models`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ model_id: modelId, display_name: displayName })
        });

        if (response.ok) {
            showToast(i18n.t('msg.modelAdded', { name: displayName }), 'success');
            btn.parentElement.remove();
            loadMonitoredModels();
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
            btn.disabled = false;
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
        btn.disabled = false;
    }
}

/**
 * Load monitored models
 */
async function loadMonitoredModels() {
    try {
        const response = await fetch(`${API_BASE}/api/models`);
        const models = await response.json();

        const list = document.getElementById('monitored-list');

        if (models.length === 0) {
            list.innerHTML = '<p class="text-muted">' + i18n.t('settings.models.noModels') + '</p>';
            return;
        }

        list.innerHTML = models.map(model => `
            <div class="monitored-item" data-model-id="${model.id}">
                <div class="monitored-item-info">
                    ${model.logo_url ? `<img src="${escapeHtml(model.logo_url)}" class="model-logo-small" alt="logo" onerror="this.style.display='none'">` : ''}
                    <div>
                        <span class="monitored-item-name">${escapeHtml(model.display_name)}</span>
                        <span class="monitored-item-id">${escapeHtml(model.model_id)}</span>
                    </div>
                </div>
                <div class="monitored-item-actions">
                    <input type="text" class="logo-input" placeholder="${i18n.t('settings.models.logoUrl')}" value="${escapeHtml(model.logo_url || '')}" data-id="${model.id}">
                    <button class="btn btn-small btn-outline" onclick="updateModelLogo(${model.id}, this)">💾</button>
                    <button class="btn btn-small btn-danger" onclick="removeModel(${model.id}, '${escapeHtml(model.display_name)}')">${i18n.t('settings.models.remove')}</button>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load monitored models:', error);
    }
}

/**
 * Update model logo
 */
async function updateModelLogo(id, btn) {
    const input = btn.previousElementSibling;
    const logoUrl = input.value;
    btn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/api/models/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ logo_url: logoUrl })
        });

        if (response.ok) {
            showToast(i18n.t('msg.logoSaved'), 'success');
            loadMonitoredModels();
        } else {
            showToast(i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    } finally {
        btn.disabled = false;
    }
}

/**
 * Remove model from monitoring
 */
async function removeModel(id, name) {
    if (!confirm(i18n.t('msg.confirmRemove', { name }))) return;

    try {
        const response = await fetch(`${API_BASE}/api/models/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            showToast(i18n.t('msg.modelRemoved', { name }), 'success');
            loadMonitoredModels();
            loadModelStatus();
        } else {
            showToast(i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Load model status
 */
async function loadModelStatus() {
    const loading = document.getElementById('status-loading');
    const list = document.getElementById('model-status-list');
    const noModels = document.getElementById('no-models');

    loading.classList.remove('hidden');
    list.classList.add('hidden');
    noModels.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/tests/stats`);
        const stats = await response.json();

        loading.classList.add('hidden');

        if (stats.length === 0) {
            noModels.classList.remove('hidden');
            return;
        }

        list.innerHTML = stats.map(model => {
            const rate = model.rate_1d;
            const isOnline = rate !== null ? rate >= 95 : null;
            const statusClass = isOnline === null ? 'unknown' : (isOnline ? 'online' : 'offline');

            return `
                <div class="model-status-item">
                    <div class="model-status-info">
                        <div class="status-indicator ${statusClass}"></div>
                        <div>
                            <div class="model-status-name">${escapeHtml(model.display_name)}</div>
                            <div class="model-status-id">${escapeHtml(model.model_name)}</div>
                        </div>
                    </div>
                    <div>
                        <span style="margin-right: 16px; color: ${rate >= 95 ? 'var(--success-color)' : rate >= 80 ? 'var(--warning-color)' : 'var(--danger-color)'}">
                            ${i18n.t('status.24h')} ${rate !== null ? rate + '%' : '--'}
                        </span>
                    </div>
                    <div class="model-status-actions">
                        <button class="btn btn-small btn-outline" onclick="testSingleModel(${model.model_id}, '${escapeHtml(model.display_name)}')">🔍 ${i18n.t('status.test')}</button>
                    </div>
                </div>
            `;
        }).join('');

        list.classList.remove('hidden');

    } catch (error) {
        loading.classList.add('hidden');
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Test single model
 */
async function testSingleModel(id, name) {
    showToast(i18n.t('msg.testing', { name }), 'warning');

    try {
        const response = await fetch(`${API_BASE}/api/tests/run/${id}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                showToast(i18n.t('msg.testSuccess', { name }), 'success');
            } else {
                showToast(i18n.t('msg.testFailed', { name, error: result.error_message || 'Failed' }), 'error');
            }
            loadModelStatus();
        } else {
            showToast(i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Test all models
 */
async function testAllModels() {
    const btn = document.getElementById('test-all-btn');
    const progress = document.getElementById('test-progress');

    btn.disabled = true;
    progress.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE}/api/tests/run-all`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const results = await response.json();
            const passed = results.filter(r => r.success).length;
            showToast(i18n.t('msg.testComplete', { passed, total: results.length }), passed === results.length ? 'success' : 'warning');
            loadModelStatus();
        } else {
            showToast(i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    } finally {
        btn.disabled = false;
        progress.classList.add('hidden');
    }
}

/**
 * Test email
 */
async function testEmail() {
    const btn = document.getElementById('test-email-btn');
    const btnText = btn.querySelector('span');
    btn.disabled = true;
    btnText.textContent = i18n.t('settings.email.sending');

    try {
        const response = await fetch(`${API_BASE}/api/settings/test-email`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            showToast(i18n.t('msg.testEmailSent'), 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = i18n.t('settings.email.test');
    }
}

/**
 * Test webhook
 */
async function testWebhook() {
    const btn = document.getElementById('test-webhook-btn');
    const btnText = btn.querySelector('span');
    btn.disabled = true;
    btnText.textContent = i18n.t('settings.webhook.sending');

    try {
        const response = await fetch(`${API_BASE}/api/settings/test-webhook`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            showToast(i18n.t('msg.testWebhookSent'), 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = i18n.t('settings.webhook.test');
    }
}

/**
 * Test notification (simulated model failure)
 */
async function testNotification() {
    const btn = document.getElementById('test-notification-btn');
    const btnText = btn.querySelector('span');
    btn.disabled = true;
    btnText.textContent = '发送中...';

    try {
        const response = await fetch(`${API_BASE}/api/settings/test-notification`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            showToast(i18n.t('msg.testNotificationSent'), 'success');
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    } finally {
        btn.disabled = false;
        btnText.textContent = i18n.t('settings.test.send');
    }
}

/**
 * Change password
 */
async function changePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;

    if (!currentPassword || !newPassword) {
        showToast(i18n.t('msg.fillPasswords'), 'error');
        return;
    }

    if (newPassword.length < 6) {
        showToast(i18n.t('msg.passwordTooShort'), 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/admin/password`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        if (response.ok) {
            showToast(i18n.t('msg.passwordChanged'), 'success');
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
        } else {
            const error = await response.json();
            showToast(error.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Load logs
 */
async function loadLogs() {
    const container = document.querySelector('.logs-list');
    const level = document.getElementById('log-level-filter').value;

    try {
        let url = `${API_BASE}/api/logs?page=${currentPage}&page_size=50`;
        if (level) url += `&level=${level}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            if (response.status === 401) {
                logout();
                return;
            }
            throw new Error('Failed to load logs');
        }

        const data = await response.json();

        container.innerHTML = data.logs.map(log => `
            <div class="log-entry">
                <span class="log-time">${formatTime(log.timestamp)}</span>
                <span class="log-level ${log.level}">${log.level}</span>
                <span class="log-source">[${log.source}]</span>
                <span class="log-message">${escapeHtml(log.message)}</span>
            </div>
        `).join('');

        // Update pagination
        document.getElementById('page-info').textContent = i18n.t('logs.page', { page: currentPage });
        document.getElementById('prev-page-btn').disabled = currentPage <= 1;
        document.getElementById('next-page-btn').disabled = data.logs.length < 50;

    } catch (error) {
        container.innerHTML = '<p style="color: #666;">' + i18n.t('msg.connectionFailed') + '</p>';
    }
}

/**
 * Toggle logs auto-refresh
 */
function toggleLogsAutoRefresh(e) {
    autoRefreshLogs = e.target.checked;

    if (autoRefreshLogs) {
        logsInterval = setInterval(loadLogs, 5000);
    } else if (logsInterval) {
        clearInterval(logsInterval);
        logsInterval = null;
    }
}

/**
 * Clear logs
 */
async function clearLogs() {
    // Using a custom confirmation approach instead of confirm()
    const confirmed = window.confirm(i18n.t('msg.confirmClearLogs'));
    if (!confirmed) {
        return;
    }

    console.log('Clearing logs...');

    try {
        const response = await fetch(`${API_BASE}/api/logs`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        console.log('Clear logs response:', response.status);

        if (response.ok) {
            showToast(i18n.t('msg.logsCleared'), 'success');
            currentPage = 1;
            await loadLogs();
        } else {
            const errorData = await response.json().catch(() => ({}));
            console.error('Clear logs failed:', errorData);
            showToast(errorData.detail || i18n.t('msg.connectionFailed'), 'error');
        }
    } catch (error) {
        console.error('Clear logs error:', error);
        showToast(i18n.t('msg.connectionFailed'), 'error');
    }
}

/**
 * Format timestamp
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Global functions for inline handlers
window.addModel = addModel;
window.removeModel = removeModel;
window.testSingleModel = testSingleModel;
window.switchLanguage = switchLanguage;
window.updateModelLogo = updateModelLogo;

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
