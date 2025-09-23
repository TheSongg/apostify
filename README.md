![# Apostify](assets/logo.png)

# AI驱动的视频创作与多平台自动化发布工具

## 项目概述

Apostify 是一个基于 Python 的自动化内容发布平台，专为 AI 生成内容（视频、文字、图片）的自动化上传与发布而设计。它通过集成 Telegram Bot、n8n 和 Playwright，构建了一个高效的自动化工作流，助力内容创作者实现从 AI 视频生成到多平台发布的无缝衔接。其核心亮点在于：

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
| 4  | 视频号       | ✅    |              |
| 5  | 快手        | ❌    | 开发中          |
| 6  | YouTube   | ❌    | n8n有节点，可能不开发 |
| 7  | TikTok    | ❌    | 开发中          |
| 8  | Instagram | ❌    | 开发中          |

## 技术栈

- **后端**：Django
- **自动化**：n8n（工作流编排）、Playwright（浏览器自动化）、Telegram Bot
- **消息通知**：Telegram Bot
- **前端**：n8n web
- **数据库**：Postgres、Redis
- **部署**：Docker
- **代理**： Nginx

## 安装方式

### 前置条件

- linux 系统（配置 >= 2C2G）
- Docker
- Telegram Bot Token
- 目标平台（如 YouTube、抖音）的 账号（用于扫码登录）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/TheSongg/apostify.git
   cd apostify/docker/
   ```

2. **配置环境变量**
   修改 `apostify/docker/`目录下 `.env` 文件里的以下配置：
   
   | 参数名称                      | 说明                          | 默认值                  | 是否必须修改默认值 |
   |---------------------------|-----------------------------|----------------------|-----------|
   | X-API-KEY                 | 接口鉴权key                     | your_key             | 是         |
   | TG_BOT_TOKEN              | Telegram 机器人 Token          | N/A                  | 是         |
   | CHAT_ID                   | Telegram 目标聊天 ID            | N/A                  | 是         |
   | N8N_PROTOCOL              | n8n 服务协议（必须https）           | https                | 否         |
   | N8N_HOST                  | n8n 域名                      | N/A                  | 是         |
   | N8N_EDITOR_BASE_URL       | n8n 访问 URL                  | https://{N8N_HOST}   | 是         |
   | WEBHOOK_URL               | n8n Webhook 基础 URL          | https://{N8N_HOST}   | 是         |
   | N8N_ENDPOINT_WEBHOOK      | n8n Webhook 接口路径            | webhook              | 否         |
   | N8N_ENDPOINT_WEBHOOK_TEST | n8n Webhook 测试接口路径          | webhook-test         | 否         |
   | N8N_DEFAULT_LOCALE        | n8n 默认语言/区域                 | zh-CN                | 否         |
   | PLAYWRIGHT_PORT           | Playwright 浏览器调试端口          | 9222                 | 否         |
   | CHROME_DRIVER             | Playwright 浏览器 WebSocket 地址 | ws://playwright:9222 | 否         |
   | HEADLESS                  | 浏览器是否无头模式                   | False                | 否         |
   | COOKIE_INTERVAL_HOURS     | Cookie 默认刷新时间（小时）           | 12                   | 否         |
   | DEFAULT_TIMEOUT           | 页面加载超时时间（毫秒）                | 120000               | 否         |
   | COOKIE_MAX_WAIT           | 等待用户扫码获取 Cookie 最大时间（秒）     | 180                  | 否         |
   | MAX_RETRIES               | 上传重试次数                      | 3                    | 否         |
   | APOSTITFY_PORT            | 后端服务端口                      | 8000                 | 否         |
   | POSTGRES_USER             | PostgreSQL 超级用户             | your_user            | 是         |
   | POSTGRES_PASSWORD         | PostgreSQL 超级用户密码           | your_passwd          | 是         |
   | POSTGRES_DB               | PostgreSQL 默认数据库名称          | progres              | 否         |
   | POSTGRES_POST             | PostgreSQL 端口号              | 5432                 | 否         |
   | POSTGRES_APOSTIFY_DB      | Apostify 服务使用的数据库名称         | apostify             | 否         |
   | POSTGRES_N8N_DB           | n8n 服务使用的数据库名称              | n8n                  | 否         |
   | REDIS_PASSWORD            | Redis 密码                    | your_passwd          | 是         |
   | REDIS_PORT                | Redis 端口号                   | 6379                 | 否         |
   | GENERIC_TIMEZONE          | 系统通用时区                      | Asia/Shanghai        | 否         |
   | TZ                        | 容器/系统时区环境变量                 | Asia/Shanghai        | 否         |

3. **启动项目**
    进入 `apostify/docker/` 目录，执行以下命令启动项目：
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **检查**
    一共7个容器，检查是否都启动成功：
   ```bash
   docker ps
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
