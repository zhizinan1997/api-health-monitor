# 🩺 API Health Monitor

> **中文** | [English](#english)

一个轻量级、容器化的 API 健康监控服务，专为监控 OpenAI 格式的 AI 模型接口而设计。提供实时状态展示、故障告警通知、调试日志管理等功能。

![界面预览](https://img.shields.io/badge/UI-Modern%20Gray%20Theme-10a37f?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?style=flat-square&logo=fastapi)

## ✨ 核心功能

### 用户界面
- 📊 **实时状态监控**: 24小时时间轴可视化，清晰展示每小时的连通状态
- 📈 **多时段统计**: 提供24小时、3天、7天、30天的可用率统计
- 🎨 **现代化UI**: 灰白浅色主题 + 自动暗黑模式适配，使用 Inter 字体
- 🔄 **自动刷新**: 每60秒自动更新状态数据
- 🌐 **中英双语**: 完整的国际化支持

### 管理后台
- 🔐 **安全认证**: JWT Token 身份验证机制
- ⚙️ **灵活配置**: 
  - API 接口设置（地址、密钥、测试间隔）
  - **定时测试配置**: 自定义测试起始时间（小时:分钟）
  - 邮件通知（SMTP 配置）
  - Webhook 通知（钉钉等）
  - **自定义通知内容**: 可为所有告警添加附加信息
- 📦 **模型管理**: 
  - 一键获取可用模型列表
  - **智能Logo匹配**: 自动识别GPT/Claude/Gemini等9种模型并设置logo
  - **拖拽排序**: 通过拖动调整用户界面模型显示顺序
- 💾 **智能自动保存**: 所有设置修改500ms后自动保存，带实时状态反馈
- 🧪 **实时测试**: 
  - 单个模型手动测试
  - **并行测试所有模型**: 谁先测完谁先显示，实时进度反馈
- 📝 **调试日志**: 实时日志查看、分级过滤、自动刷新

## 📝 更新日志

### v2.0.0 (2025-12-09)

#### 🐛 Bug修复
1. **错误状态显示优化**: 模型恢复正常后不再持续显示历史错误信息
2. **状态指示器实时更新**: 测试完成后管理界面状态点(红/绿)立即更新
3. **并行测试**: 改为Promise.allSettled并行执行，快速模型优先显示结果
4. **i18n简化**: 移除部分i18n调用，直接使用中文文本简化逻辑

#### ✨ 新功能
5. **防止浏览器自动填充**: 
   - 所有敏感字段添加autocomplete属性
   - 防止Edge等浏览器自动填充密码导致设置被覆盖
   
6. **智能Logo自动匹配**:
   - 添加模型时自动识别并设置logo
   - 支持GPT、Claude、Gemini、Qwen、GLM、DeepSeek、KIMI、Grok、MiniMax
   - 使用稳定的CDN链接(data.zhizinan.top)
   - 仍可手动修改logo
   
7. **模型拖拽排序**:
   - 在"已监控模型"中拖动⋮⋮图标调整顺序
   - 用户界面模型卡片按设定顺序显示
   - 自动保存排序结果
   
8. **定时测试时间配置**:
   - 可设置测试起始时间（小时:分钟）
   - 例如：起始时间00:00，间隔60分钟，则在00:00、01:00、02:00...执行测试
   - 支持更灵活的测试计划
   
9. **自定义通知内容**:
   - 可为所有告警邮件和Webhook添加附加内容
   - 适合添加联系方式、处理流程等固定信息
   - 支持纯文本，Webhook支持Markdown格式

### v1.0.0 (2025-12-08)

#### 初始版本
- 基础健康监控功能
- 邮件和Webhook告警
- 管理后台和用户界面
- Docker容器化部署
- 时区配置(Asia/Shanghai)

---

## 🛠️ 技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.11 | 运行时环境 |
| **FastAPI** | 0.104+ | Web 框架，提供 REST API |
| **SQLAlchemy** | 2.0+ | ORM 数据库操作 |
| **SQLite** | - | 轻量级数据库存储 |
| **APScheduler** | 3.10+ | 定时任务调度器 |
| **bcrypt** | - | 密码哈希加密 |
| **PyJWT** | - | JWT Token 认证 |
| **aiosmtplib** | - | 异步邮件发送 |
| **httpx** | - | 异步 HTTP 客户端 |
| **pytz** | - | 时区处理 |

### 前端
| 技术 | 用途 |
|------|------|
| **HTML5** | 页面结构 |
| **CSS3** | 灰白浅色主题 + 自动暗黑模式适配 |
| **Vanilla JavaScript** | 无框架，原生 JS 实现交互逻辑 |
| **Inter 字体** | Google Fonts 现代化字体 |

### 部署
| 技术 | 用途 |
|------|------|
| **Docker** | 容器化部署 |
| **Docker Compose** | 容器编排 |
| **Uvicorn** | ASGI 服务器 |

---

## 📁 项目结构

```
api-health-monitor/
├── app/                          # 后端 Python 代码
│   ├── __init__.py              # 包初始化文件
│   ├── main.py                  # FastAPI 应用入口，路由挂载，生命周期事件
│   ├── database.py              # SQLAlchemy 数据库配置，会话管理
│   ├── models.py                # 数据库模型定义 (Admin, Settings, MonitoredModel, TestResult, DebugLog)
│   ├── schemas.py               # Pydantic 请求/响应数据验证模型
│   ├── auth.py                  # JWT 认证、密码哈希、Token 生成与验证
│   ├── api_client.py            # OpenAI 格式 API 客户端，获取模型列表和测试连通性
│   ├── notifier.py              # 邮件 (SMTP) 和钉钉 Webhook 通知服务
│   ├── scheduler.py             # APScheduler 定时任务，自动执行模型健康检测
│   ├── logger.py                # 调试日志记录与管理
│   └── routers/                 # API 路由模块
│       ├── __init__.py          # 路由包初始化
│       ├── admin.py             # 管理员认证路由 (登录/注册/修改密码)
│       ├── settings.py          # 设置管理路由 (API配置/通知配置/测试通知)
│       ├── models.py            # 模型管理路由 (添加/删除/更新监控模型)
│       ├── tests.py             # 测试执行路由 (手动测试/获取统计数据)
│       └── logs.py              # 日志管理路由 (查看/清空调试日志)
│
├── static/                       # 前端静态资源
│   ├── index.html               # 客户端状态展示页面
│   ├── admin.html               # 管理后台页面
│   ├── css/
│   │   ├── customer.css         # 客户页面样式 (灰白主题+暗黑模式)
│   │   └── admin.css            # 管理页面样式 (ChatGPT 深色主题)
│   └── js/
│       ├── customer.js          # 客户页面交互逻辑
│       ├── admin.js             # 管理页面交互逻辑
│       └── i18n.js              # 国际化模块 (中英文翻译)
│
├── data/                         # 数据持久化目录 (Docker 挂载)
│   └── .gitkeep                 # 保持目录存在
│
├── .github/
│   └── workflows/
│       └── docker-build.yml     # GitHub Actions 自动构建镜像
│
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml           # Docker Compose 编排配置
├── requirements.txt             # Python 依赖列表
├── .gitignore                   # Git 忽略规则
└── README.md                    # 项目说明文档
```

### 核心文件详解

| 文件 | 作用 |
|------|------|
| `app/main.py` | FastAPI 应用主入口，配置 CORS、静态文件服务、路由挂载、启动/关闭事件 |
| `app/database.py` | 创建 SQLite 数据库引擎和会话工厂，提供 `get_db` 依赖注入 |
| `app/models.py` | 定义 5 个数据表：管理员、设置、监控模型、测试结果、调试日志 |
| `app/schemas.py` | Pydantic 模型，用于 API 请求参数验证和响应序列化 |
| `app/auth.py` | 使用 bcrypt 哈希密码，PyJWT 生成/验证 Token |
| `app/api_client.py` | 封装对 OpenAI 格式 API 的调用，智能处理 URL 后缀 |
| `app/notifier.py` | 异步发送邮件和钉钉通知，支持静默时间段 (23:00-08:00) |
| `app/scheduler.py` | 使用 APScheduler 定时检测，支持失败重测机制（3分钟后重测避免误报） |
| `static/js/i18n.js` | 国际化翻译字典，支持 `i18n.t('key')` 方式获取文本 |

---

## 🚀 快速部署

### 前置要求
- 安装 [Docker](https://www.docker.com/get-started)
- 确保端口 `2025` 未被占用

### 方式一：一键部署（推荐）

```bash
# 1. 创建数据目录
mkdir -p ~/api-health-monitor/data && cd ~/api-health-monitor

# 2. 拉取并运行容器
docker run -d \
  --name api-health-monitor \
  -p 2025:2025 \
  -v "$(pwd)"/data:/app/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  ghcr.io/zhizinan1997/api-health-monitor:latest
```

**Windows PowerShell:**
```powershell
# 1. 创建数据目录
New-Item -ItemType Directory -Path "$env:USERPROFILE\api-health-monitor\data" -Force
Set-Location "$env:USERPROFILE\api-health-monitor"

# 2. 拉取并运行容器
docker run -d \
  --name api-health-monitor \
  -p 2025:2025 \
  -v "$(pwd)"/data:/app/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  ghcr.io/zhizinan1997/api-health-monitor:latest
```

### 方式二：使用 Docker Compose

创建 `docker-compose.yml` 文件：
```yaml
version: '3.8'
services:
  api-health-monitor:
    image: ghcr.io/zhizinan1997/api-health-monitor:latest
    container_name: api-health-monitor
    ports:
      - "2025:2025"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

然后运行：
```bash
docker compose up -d
```

### 访问服务
- **客户状态页**: http://localhost:2025/
- **管理后台**: http://localhost:2025/admin

### 首次使用


| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | `Asia/Shanghai` | 容器时区 |
| `PORT` | `2025` | 服务监听端口 |

### 通知配置

#### 邮件通知 (SMTP)
- 支持 TLS 加密
- 支持静默时间段 (23:00-08:00 北京时间不发送)
- 需配置：SMTP 服务器、端口、用户名、密码、发件人、收件人

#### 钉钉 Webhook
- 使用钉钉群机器人的 Webhook URL
- 发送 Markdown 格式消息
- 同样支持静默时间段

---

## 📡 API 端点

### 公开接口
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings/public` | 获取站点标题和 Logo |
| GET | `/api/tests/stats` | 获取模型状态统计 |

### 认证接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/setup` | 创建管理员账号 |
| POST | `/api/admin/login` | 管理员登录 |
| POST | `/api/admin/change-password` | 修改密码 |

### 管理接口 (需 JWT Token)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/api/settings` | 获取/更新设置 |
| POST | `/api/settings/test-email` | 发送测试邮件 |
| POST | `/api/settings/test-webhook` | 发送测试 Webhook |
| POST | `/api/settings/test-notification` | 发送模拟故障告警 |
| GET | `/api/models/available` | 获取可用模型列表 |
| GET | `/api/models` | 获取已监控模型 |
| POST | `/api/models` | 添加监控模型 |
| PUT | `/api/models/{id}` | 更新模型信息 |
| DELETE | `/api/models/{id}` | 删除监控模型 |
| POST | `/api/tests/{id}` | 测试单个模型 |
| POST | `/api/tests/all` | 测试所有模型 |
| GET | `/api/logs` | 获取调试日志 |
| DELETE | `/api/logs` | 清空调试日志 |

---

## 🐳 Docker 配置

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV TZ=Asia/Shanghai
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 2025
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "2025"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  api-health-monitor:
    build: .
    container_name: api-health-monitor
    ports:
      - "2025:2025"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
```

---

## 🔧 GitHub Actions 自动构建

本项目配置了 GitHub Actions 工作流，在发布新版本时自动构建并推送 Docker 镜像到 GitHub Container Registry (GHCR)。

### 触发条件
- ✅ **发布新版本时触发** - 在 GitHub 创建 Release 并发布时自动构建
- ❌ **推送代码不触发** - 普通 push 不会构建镜像

### 配置步骤

无需额外配置，GitHub 自动提供 `GITHUB_TOKEN` 用于认证。

发布新版本：
1. 在 GitHub 仓库页面点击 `Releases` → `Create a new release`
2. 创建新标签（如 `v1.0.0`）并发布
3. Actions 会自动构建并推送镜像

### 构建产物
- `ghcr.io/zhizinan1997/api-health-monitor:v1.0.0` - 版本标签
- `ghcr.io/zhizinan1997/api-health-monitor:latest` - 最新版本
- 支持多架构：`linux/amd64`, `linux/arm64`

---

## 📄 开源协议

MIT License

---

<a name="english"></a>
## English

A lightweight, containerized API health monitoring service designed for OpenAI-format AI model APIs, featuring real-time status display, failure alerts, and debug log management with a ChatGPT-style dark UI.

### Quick Start
```bash
# Create data directory and run container
mkdir -p ~/api-health-monitor/data && cd ~/api-health-monitor

docker run -d \
  --name api-health-monitor \
  -p 2025:2025 \
  -v "$(pwd)"/data:/app/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  ghcr.io/zhizinan1997/api-health-monitor:latest
```

- **Status Page**: http://localhost:2025/
- **Admin Panel**: http://localhost:2025/admin

### Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, SQLite, APScheduler
- **Frontend**: Vanilla HTML/CSS/JS, ChatGPT-style dark theme
- **Deployment**: Docker
