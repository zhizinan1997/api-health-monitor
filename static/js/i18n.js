/**
 * Internationalization (i18n) Support
 * Supports English and Simplified Chinese
 */

const i18n = {
    currentLang: localStorage.getItem('lang') || 'zh',

    translations: {
        en: {
            // Customer Page
            'site.title': 'API Health Monitor',
            'site.lastUpdated': 'Last Updated:',
            'site.loading': 'Loading status...',
            'site.noModels.title': 'No Models Configured',
            'site.noModels.desc': 'The administrator has not configured any models for monitoring yet.',
            'site.footer': 'Monitoring {count} models • Auto-refresh every 60 seconds',
            'site.error.title': 'Unable to Load Status',
            'site.error.desc': 'Failed to connect to the monitoring service. Please try again later.',

            // Status
            'status.online': 'Online',
            'status.offline': 'Issues Detected',
            'status.noData': 'No Data',

            // Progress bar
            'progress.24hAgo': '24 Hours Ago',
            'progress.now': 'Now',
            'progress.success': 'Online',
            'progress.failure': 'Failed',
            'progress.noData': 'No data',

            // Stats
            'stats.1d': '24H',
            'stats.3d': '3 Days',
            'stats.7d': '7 Days',
            'stats.30d': '30 Days',

            // Error
            'error.lastError': 'Last Error',

            // Admin Page
            'admin.title': 'API Health Monitor',
            'admin.subtitle.login': 'Admin Login',
            'admin.subtitle.setup': 'First-time Setup - Create Admin Account',
            'admin.username': 'Username',
            'admin.password': 'Password',
            'admin.confirmPassword': 'Confirm Password',
            'admin.login': 'Login',
            'admin.createAccount': 'Create Account',
            'admin.logout': 'Logout',

            // Admin Panel
            'panel.title': 'Admin Panel',
            'tab.status': 'Status',
            'tab.settings': 'Settings',
            'tab.logs': 'Logs',

            // Status Tab
            'status.title': 'Model Connectivity Status',
            'status.testAll': 'Test All Models',
            'status.refresh': 'Refresh',
            'status.testing': 'Testing models...',
            'status.loading': 'Loading status...',
            'status.noModels': 'No models configured. Go to Settings to add models.',
            'status.test': 'Test',
            'status.24h': '24h:',

            // Settings Tab
            'settings.api.title': 'API Configuration',
            'settings.api.baseUrl': 'API Base URL',
            'settings.api.key': 'API Key',
            'settings.api.interval': 'Test Interval (minutes)',

            'settings.models.title': 'Model Management',
            'settings.models.fetch': 'Fetch Available Models',
            'settings.models.fetching': 'Fetching...',
            'settings.models.monitored': 'Monitored Models',
            'settings.models.noModels': 'No models being monitored',
            'settings.models.add': 'Add',
            'settings.models.remove': 'Remove',
            'settings.models.displayName': 'Display name',
            'settings.models.logoUrl': 'Logo URL',

            'settings.email.title': 'Email Notifications',
            'settings.email.enable': 'Enable Email Notifications',
            'settings.email.host': 'SMTP Host',
            'settings.email.port': 'Port',
            'settings.email.username': 'Username',
            'settings.email.password': 'Password',
            'settings.email.passwordHint': 'Leave empty to keep current',
            'settings.email.from': 'From Address',
            'settings.email.adminEmail': 'Admin Email',
            'settings.email.useTls': 'Use TLS',
            'settings.email.test': 'Send Test Email',
            'settings.email.sending': 'Sending...',

            'settings.webhook.title': 'Webhook Notifications (DingTalk)',
            'settings.webhook.enable': 'Enable Webhook Notifications',
            'settings.webhook.url': 'Webhook URL',
            'settings.webhook.test': 'Send Test Message',
            'settings.webhook.sending': 'Sending...',

            'settings.display.title': 'Display Settings',
            'settings.display.siteTitle': 'Site Title',
            'settings.display.logoUrl': 'Logo URL',

            'settings.account.title': 'Account Settings',
            'settings.account.currentPassword': 'Current Password',
            'settings.account.newPassword': 'New Password',
            'settings.account.change': 'Change Password',

            'settings.test.title': 'Test Notification',
            'settings.test.desc': 'Send a simulated model failure alert to test if email and webhook are working.',
            'settings.test.send': 'Send Test Alert',

            'settings.save': 'Save Settings',

            // Logs Tab
            'logs.title': 'Debug Logs',
            'logs.autoRefresh': 'Auto-refresh',
            'logs.allLevels': 'All Levels',
            'logs.clear': 'Clear Logs',
            'logs.prev': '← Previous',
            'logs.next': 'Next →',
            'logs.page': 'Page {page}',

            // Messages
            'msg.accountCreated': 'Admin account created successfully!',
            'msg.settingsSaved': 'Settings saved successfully!',
            'msg.passwordChanged': 'Password changed successfully!',
            'msg.modelAdded': 'Model "{name}" added',
            'msg.modelRemoved': 'Model "{name}" removed',
            'msg.testComplete': 'Test complete: {passed}/{total} passed',
            'msg.testEmailSent': 'Test email sent!',
            'msg.testWebhookSent': 'Test message sent!',
            'msg.logsCleared': 'Logs cleared',
            'msg.testing': 'Testing {name}...',
            'msg.testSuccess': '{name}: ✓ Online',
            'msg.testFailed': '{name}: ✗ {error}',
            'msg.connectionFailed': 'Connection failed',
            'msg.invalidCredentials': 'Invalid username or password',
            'msg.passwordMismatch': 'Passwords do not match',
            'msg.fillPasswords': 'Please fill in both password fields',
            'msg.passwordTooShort': 'New password must be at least 6 characters',
            'msg.confirmRemove': 'Remove "{name}" from monitoring?',
            'msg.confirmClearLogs': 'Clear all debug logs?',
            'msg.logoSaved': 'Logo saved!',
            'msg.saveSettingsFirst': 'Please save settings first!',
            'msg.testNotificationSent': 'Test alert sent successfully!',

            // Language
            'lang.switch': '中文'
        },
        zh: {
            // Customer Page
            'site.title': 'API 健康监控',
            'site.lastUpdated': '最后更新：',
            'site.loading': '正在加载状态...',
            'site.noModels.title': '暂无监控模型',
            'site.noModels.desc': '管理员尚未配置任何需要监控的模型。',
            'site.footer': '正在监控 {count} 个模型 • 每60秒自动刷新',
            'site.error.title': '无法加载状态',
            'site.error.desc': '连接监控服务失败，请稍后再试。',

            // Status
            'status.online': '在线',
            'status.offline': '存在问题',
            'status.noData': '暂无数据',

            // Progress bar
            'progress.24hAgo': '24小时前',
            'progress.now': '现在',
            'progress.success': '正常',
            'progress.failure': '故障',
            'progress.noData': '无数据',

            // Stats
            'stats.1d': '24小时',
            'stats.3d': '3天',
            'stats.7d': '7天',
            'stats.30d': '30天',

            // Error
            'error.lastError': '最近错误',

            // Admin Page
            'admin.title': 'API 健康监控',
            'admin.subtitle.login': '管理员登录',
            'admin.subtitle.setup': '首次配置 - 创建管理员账号',
            'admin.username': '用户名',
            'admin.password': '密码',
            'admin.confirmPassword': '确认密码',
            'admin.login': '登录',
            'admin.createAccount': '创建账号',
            'admin.logout': '退出登录',

            // Admin Panel
            'panel.title': '管理面板',
            'tab.status': '状态',
            'tab.settings': '设置',
            'tab.logs': '日志',

            // Status Tab
            'status.title': '模型连通性状态',
            'status.testAll': '测试所有模型',
            'status.refresh': '刷新',
            'status.testing': '正在测试模型...',
            'status.loading': '正在加载状态...',
            'status.noModels': '暂无监控模型，请前往设置页面添加。',
            'status.test': '测试',
            'status.24h': '24小时：',

            // Settings Tab
            'settings.api.title': 'API 配置',
            'settings.api.baseUrl': 'API 地址',
            'settings.api.key': 'API 密钥',
            'settings.api.interval': '测试间隔（分钟）',

            'settings.models.title': '模型管理',
            'settings.models.fetch': '获取可用模型列表',
            'settings.models.fetching': '获取中...',
            'settings.models.monitored': '已监控模型',
            'settings.models.noModels': '暂无监控模型',
            'settings.models.add': '添加',
            'settings.models.remove': '移除',
            'settings.models.displayName': '显示名称',
            'settings.models.logoUrl': 'Logo 链接',

            'settings.email.title': '邮件通知',
            'settings.email.enable': '启用邮件通知',
            'settings.email.host': 'SMTP 服务器',
            'settings.email.port': '端口',
            'settings.email.username': '用户名',
            'settings.email.password': '密码',
            'settings.email.passwordHint': '留空保持当前密码',
            'settings.email.from': '发件人地址',
            'settings.email.adminEmail': '管理员邮箱',
            'settings.email.useTls': '使用 TLS',
            'settings.email.test': '发送测试邮件',
            'settings.email.sending': '发送中...',

            'settings.webhook.title': 'Webhook 通知（钉钉）',
            'settings.webhook.enable': '启用 Webhook 通知',
            'settings.webhook.url': 'Webhook 地址',
            'settings.webhook.test': '发送测试消息',
            'settings.webhook.sending': '发送中...',

            'settings.display.title': '显示设置',
            'settings.display.siteTitle': '站点标题',
            'settings.display.logoUrl': 'Logo 图片链接',

            'settings.account.title': '账号设置',
            'settings.account.currentPassword': '当前密码',
            'settings.account.newPassword': '新密码',
            'settings.account.change': '修改密码',

            'settings.test.title': '测试通知',
            'settings.test.desc': '发送模拟的模型故障告警，用于测试邮件和Webhook是否正常工作。',
            'settings.test.send': '发送测试告警',

            'settings.save': '保存设置',

            // Logs Tab
            'logs.title': '调试日志',
            'logs.autoRefresh': '自动刷新',
            'logs.allLevels': '所有级别',
            'logs.clear': '清空日志',
            'logs.prev': '← 上一页',
            'logs.next': '下一页 →',
            'logs.page': '第 {page} 页',

            // Messages
            'msg.accountCreated': '管理员账号创建成功！',
            'msg.settingsSaved': '设置保存成功！',
            'msg.passwordChanged': '密码修改成功！',
            'msg.modelAdded': '已添加模型：{name}',
            'msg.modelRemoved': '已移除模型：{name}',
            'msg.testComplete': '测试完成：{passed}/{total} 通过',
            'msg.testEmailSent': '测试邮件发送成功！',
            'msg.testWebhookSent': '测试消息发送成功！',
            'msg.logsCleared': '日志已清空',
            'msg.testing': '正在测试 {name}...',
            'msg.testSuccess': '{name}：✓ 在线',
            'msg.testFailed': '{name}：✗ {error}',
            'msg.connectionFailed': '连接失败',
            'msg.invalidCredentials': '用户名或密码错误',
            'msg.passwordMismatch': '两次密码输入不一致',
            'msg.fillPasswords': '请填写两个密码字段',
            'msg.passwordTooShort': '新密码至少需要6个字符',
            'msg.confirmRemove': '确定要移除 "{name}" 吗？',
            'msg.confirmClearLogs': '确定要清空所有日志吗？',
            'msg.logoSaved': 'Logo 已保存！',
            'msg.saveSettingsFirst': '请先保存设置！',
            'msg.testNotificationSent': '测试告警发送成功！',

            // Language
            'lang.switch': 'EN'
        }
    },

    /**
     * Get translation for a key
     */
    t(key, params = {}) {
        const lang = this.translations[this.currentLang] || this.translations['en'];
        let text = lang[key] || this.translations['en'][key] || key;

        // Replace parameters
        for (const [k, v] of Object.entries(params)) {
            text = text.replace(`{${k}}`, v);
        }

        return text;
    },

    /**
     * Switch language
     */
    switchLang() {
        this.currentLang = this.currentLang === 'en' ? 'zh' : 'en';
        localStorage.setItem('lang', this.currentLang);
        return this.currentLang;
    },

    /**
     * Set language
     */
    setLang(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('lang', lang);
        }
    },

    /**
     * Get current language
     */
    getLang() {
        return this.currentLang;
    }
};

// Export for use
window.i18n = i18n;
