# Apostify：AI驱动的视频创作与多平台自动化发布工具

## 项目概述

Apostify 是一个基于 Python 的自动化内容发布平台，专为 AI 生成内容（视频、文字、图片）的自动化上传与发布而设计。它通过集成 Telegram Bot（或 WhatsApp、飞书等）、n8n 和 Playwright，构建了一个高效的自动化工作流，助力内容创作者实现从 AI 视频生成到多平台发布的无缝衔接。其核心亮点在于：

- **AI 视频创作与审核**：支持 AI 生成的视频、文字和图片内容，通过 Telegram 机器人自动发送给作者进行审核。
- **多平台自动发布**：审核通过的内容可自动上传至 YouTube、抖音、小红书等主流媒体平台。
- **定时 Cookie 更新**：通过 Playwright 实现多账号管理，定期自动更新 Cookie，确保发布流程的稳定性。
- **高度可定制**：支持自部署，适用于个人或团队的内容创作与分发需求。

Apostify 旨在简化内容创作与发布的复杂流程，为内容创作者、营销团队和自动化爱好者提供高效、可靠的解决方案。

## 多平台支持
| 序号 | 平台        | 是否支持 | 备注           |
|----|-----------|------|--------------|
| 1  | 小红书       | ✅    |              |
| 2  | 抖音        | ✅    |              |
| 3  | 今日头条      | ❌    | 开发中          |
| 4  | 视频号       | ✅     |              |
| 5  | 快手        | ❌    | 开发中          |
| 6  | YouTube   | ❌    | n8n有节点，可能不开发 |
| 7  | TikTok    | ❌    | 开发中          |
| 8  | Instagram | ❌    | 开发中          |

## 技术栈

- **后端**：Django
- **自动化**：n8n（工作流编排）、Playwright（浏览器自动化）
- **消息通知**：Telegram Bot、WhatsApp、飞书
- **前端**：暂无
- **数据库**：Postgres、Redis
- **部署**：Docker

## 安装方式

### 前置条件

- Python >= 3.10.8
- Docker
- n8n >= 1.106.4
- Playwright >= 1.55.0
- Telegram Bot Token（或 WhatsApp、飞书等消息平台 Token）
- 目标平台（如 YouTube、抖音）的 账号（用于扫码登录）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/TheSongg/apostify.git
   cd apostify
   ```

2. **安装依赖**
   ```bash
   uv pip install -r .requirements.txt
   ```

3. **配置环境变量**
   修改项目根目录下 `.env` 文件里的以下配置：
   ```plaintext
   # Telegram Bot（或其他平台）
   TG_BOT_TOKEN=your bot token 
   CHAT_ID=your telegram id

   # PG 数据库
   DB_NAME=your db name 
   DB_USER=your db user
   DB_PASSWORD=your db password
   DB_HOST=your db host
   DB_PORT=your db post
   
   #  Redis
   REDIS_HOST=your redis host
   REDIS_PASSWORD=your redis password
   REDIS_PORT=your redis port

   # Playwright 配置
   CHROME_DRIVER=your playwright path
   ```

4. **安装 n8n**
   通过 Docker 安装 n8n：
   ```bash
   docker run -it -d --rm --name n8n \
   -p 5678:5678 \
   -e GENERIC_TIMEZONE="Asia/Shanghai" \
   -e TZ="Asia/Shanghai" \
   -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
   -e N8N_RUNNERS_ENABLED=true \
   -e N8N_SECURE_COOKIE=true \
   -e N8N_PROTOCOL=https \
   -e N8N_EDITOR_BASE_URL=https://your domain name \
   -e N8N_ENDPOINT_WEBHOOK=/webhook \
   -e N8N_ENDPOINT_WEBHOOK_TEST=/webhook-cf \
   -e N8N_ENDPOINT_API=/api \
   -e N8N_DEFAULT_LOCALE=zh-CN \
   -e N8N_HOST=your domain name \
   -e WEBHOOK_URL=https://your domain name \
   -v n8n_data:/home/node/.n8n \
   n8nio/n8n
   ```

5. **配置 Playwright**
   通过 Docker 启动 Playwright Server：
   ```bash
   docker run -it -d \
   --name playwright \
   -p 9323:9323 \
   -v ~/.playwright-data:/var/plawright \
   --ipc=host \
   mcr.microsoft.com/playwright/python \
   bash -c "python -m playwright run-server --host=0.0.0.0 --port-9323"
   ```

6. **启动 PostgreSQL**
   ```bash
   docker run -it -d \
   --name postgres-container \
   -e POSTGRES_USER=youruser \
   -e POSTGRES_PASSWORD=yourpassword \
   -e POSTGRES_DB=yourdb \
   -p 5432:5432 \
   -v pgdata:/var/lib/postgresql/data \
   postgres:latest
   ```
   
7. **启动 Redis**
   ```bash
   docker run -d \
   --name redis-container \
   -p 6379:6379 \
   -e REDIS_PASSWORD=yourpassword \
   redis:latest \
   redis-server --appendonly yes --requirepass yourpassword
   ```

8. **启动 Apostify**
   ```bash
   python manage.py runserver 8000 --settings=core.settings
   ```

9. **启动 celery worker**
   ```bash
   celery -A core worker -l INFO --concurrency=4
   ```

10. **启动 celery beat**
   ```bash
   celery -A core beat --scheduler django_celery_beat.schedulers:DatabaseScheduler -l INFO
   ```

## 使用示例
 TBD

## 贡献

欢迎为 Apostify 贡献代码！请按照以下步骤：

1. Fork 本仓库。
2. 创建特性分支（`git checkout -b feature/xxx`）。
3. 提交更改（`git commit -m 'Add xxx feature'`）。
4. 推送分支（`git push origin feature/xxx`）。
5. 创建 Pull Request。

## 许可证

本项目采用 Apache 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 联系方式

- **GitHub Issues**：报告 Bug 或提出功能请求。
- **邮箱**：starmm012969@163.com、starmm012969@gmail.com
