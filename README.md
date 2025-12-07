# API Health Monitor

Docker容器化的AI API健康监控系统，用于监控OpenWebUI/NewAPI的OpenAI格式API连通性。

## 功能特点

- 🔍 **定时测试**：按设定间隔自动测试API模型连通性
- 📊 **状态展示**：24小时进度条显示 + 多时段连通率统计
- 📧 **邮件告警**：通过SMTP发送失败通知（夜间静默：23:00-08:00）
- 🔔 **钉钉推送**：Webhook集成钉钉群机器人
- 🔐 **管理界面**：首次设置账号、配置API、管理模型
- 📈 **90天历史**：保留90天测试记录用于趋势分析

## 快速开始

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 启动容器

```bash
docker-compose up -d
```

### 3. 访问界面

- 客户页面：http://localhost:2025
- 管理界面：http://localhost:2025/admin

### 4. 首次配置

1. 访问 `/admin`，设置管理员账号密码
2. 在设置页面配置API地址和密钥
3. 点击"获取模型列表"，选择需要监控的模型
4. 配置邮件/Webhook通知（可选）
5. 保存设置

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TZ` | 时区 | `Asia/Shanghai` |
| `SECRET_KEY` | JWT密钥 | 随机值（生产环境请更改） |
| `DATA_DIR` | 数据目录 | `/app/data` |

### 数据持久化

SQLite数据库存储在 `/app/data` 目录，通过volume挂载实现持久化：

```yaml
volumes:
  - ./data:/app/data
```

## Nginx反代配置示例

```nginx
server {
    listen 443 ssl;
    server_name health.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:2025;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 界面说明

### 客户页面（公开）

- 显示所有监控模型的24小时连通状态
- 进度条：绿色=正常，红色=故障，灰色=无数据
- 显示1天/3天/7天/30天连通率
- 每60秒自动刷新

### 管理界面（需登录）

**状态选项卡**
- 查看所有模型实时状态
- 一键测试所有模型
- 单独测试单个模型

**设置选项卡**
- API配置：接口地址、密钥、测试间隔
- 模型管理：获取可用模型列表、添加/移除监控
- 邮件通知：SMTP配置、开关控制
- Webhook通知：钉钉机器人配置、开关控制
- 显示设置：站点标题、Logo

**日志选项卡**
- 实时查看调试日志
- 支持按级别筛选
- 自动刷新功能

## API端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 容器健康检查 |
| GET | `/api/admin/status` | 检查是否已初始化 |
| POST | `/api/admin/setup` | 首次设置账号 |
| POST | `/api/admin/login` | 登录 |
| GET/PUT | `/api/settings` | 获取/更新设置 |
| GET | `/api/models` | 获取监控模型列表 |
| GET | `/api/tests/stats` | 获取连通率统计 |

## 许可证

MIT License
