![# Apostify](assets/logo.png)

# AI驱动的视频创作与多平台自动化发布工具

## 📖 项目概述

Apostify 是一个基于 Python 的自动化内容发布平台，专为视频、文字、图片的自动发布而设计。

它通过集成 [Telegram Bot](https://telegram.org/)、[n8n](https://n8n.io/) 和 [Playwright](https://playwright.dev/)，构建了一个高效的自动化工作流，助力内容创作者实现从 AI 视频生成到多平台发布的无缝衔接。其核心亮点在于：

- **AI 视频创作与审核**：借助n8n和大模型生成AI视频，通过 Telegram Bot自动发送给作者进行审核。
- **多平台自动发布**：审核通过的内容可自动上传至 YouTube、抖音、小红书等主流媒体平台。
- **定时 Cookie 更新**：多平台、多账号管理，定期自动更新 Cookie，确保发布流程的稳定性。
- **高度可定制**：支持自部署，适用于个人或团队的内容创作与分发需求。


## ✨ 多平台支持
> **注意：**  
> 当前版本每个平台只支持一个账号自动刷新cookie。 

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

## 🎯 技术栈

- **后端**：Django
- **自动化**：n8n（工作流编排）、Playwright（浏览器自动化）、Telegram Bot
- **消息通知**：Telegram Bot
- **前端**：n8n web
- **数据库**：Postgres、Redis
- **部署**：Docker
- **代理**： Nginx

## 🚀 安装方式

### 📋 前置条件

- linux 系统（配置 >= 2C6G）
- Docker
- Telegram Bot Token
- 目标平台（如 YouTube、抖音、小红书）的 账号

### 💡 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/TheSongg/apostify.git
   cd apostify/docker/
   ```

 **配置环境变量**
   修改 `apostify/docker/` 目录下 `.env` 文件里的以下配置。
   
   以下为必须**修改**的参数：  
   
   | 参数名称                | 说明                 | 默认值                |
   |---------------------|--------------------|--------------------|
   | X-API-KEY           | 接口鉴权 key           | your_key           |
   | TG_BOT_TOKEN        | Telegram 机器人 Token | N/A                |
   | CHAT_ID             | Telegram 目标聊天 ID   | N/A                |
   | N8N_HOST            | n8n 域名             | N/A                |
   | N8N_EDITOR_BASE_URL | n8n 访问 URL         | https://{N8N_HOST} |
   | WEBHOOK_URL         | n8n Webhook 基础 URL | https://{N8N_HOST} |
   | POSTGRES_USER       | PostgreSQL 超级用户    | your_user          |
   | POSTGRES_PASSWORD   | PostgreSQL 超级用户密码  | your_passwd        |
   | REDIS_PASSWORD      | Redis 密码           | your_passwd        |
   | VNC_PASSWORD        | vnc桌面登录密码，查看浏览器    | your_passwd        |

   <details>
      <summary>非必须修改的参数</summary>

   | 参数名称                      | 说明                      | 默认值           |
   |---------------------------|-------------------------|---------------|
   | N8N_PROTOCOL              | n8n 服务协议（必须 https）      | https         |
   | N8N_ENDPOINT_WEBHOOK      | n8n Webhook 接口路径        | webhook       |
   | N8N_ENDPOINT_WEBHOOK_TEST | n8n Webhook 测试接口路径      | webhook-test  |
   | N8N_DEFAULT_LOCALE        | n8n 默认语言/区域             | zh-CN         |
   | HEADLESS                  | 浏览器是否无头模式               | True          |
   | COOKIE_INTERVAL_TIME      | Cookie 自动刷新间隔           | 12            |
   | COOKIE_PERIOD             | Cookie 自动刷新周期           | hours         |
   | DEFAULT_TIMEOUT           | 页面加载超时时间（毫秒）            | 120000        |
   | COOKIE_MAX_WAIT           | 等待用户扫码获取 Cookie 最大时间（秒） | 180           |
   | MAX_RETRIES               | 上传重试次数                  | 3             |
   | APOSTITFY_PORT            | 后端服务端口                  | 8000          |
   | POSTGRES_DB               | PostgreSQL 默认数据库名称      | progres       |
   | POSTGRES_POST             | PostgreSQL 端口号          | 5432          |
   | POSTGRES_APOSTIFY_DB      | Apostify 服务使用的数据库名称     | apostify      |
   | POSTGRES_N8N_DB           | n8n 服务使用的数据库名称          | n8n           |
   | REDIS_PORT                | Redis 端口号               | 6379          |
   | GENERIC_TIMEZONE          | 系统通用时区                  | Asia/Shanghai |
   | TZ                        | 容器/系统时区环境变量             | Asia/Shanghai |
   | VNC_PORT                  | 原始vnc端口                 | 5901          |
   | NO_VNC_PORT               | vnc web端口               | 6901          |
   | VNC_RESOLUTION            | vnc桌面分辨率                | 1280x800      |
   
   </details>


3. **启动项目**
    进入 `apostify/docker/` 目录，执行以下命令启动项目：
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **检查**
    一共4个容器，检查是否都启动成功：
   ```bash
   docker ps
   ```

## 📚 使用示例
   ```bash
   TODO
   ```

## 🤝 贡献

欢迎为 Apostify 贡献代码！请按照以下步骤：

1. Fork 本仓库。
2. 创建特性分支（`git checkout -b feature/xxx`）。
3. 提交更改（`git commit -m 'Add xxx feature'`）。
4. 推送分支（`git push origin feature/xxx`）。
5. 创建 Pull Request。

## 🔐 许可证

本项目采用 Apache 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 💬 联系方式

- **GitHub Issues**：报告 Bug 或提出功能请求。
- **邮箱**：starmm012969@163.com、starmm012969@gmail.com

## ⚠️ 免责声明

> ⚠️ **注意**  
> 本项目仅供学习与研究使用，严禁用于任何违法违规行为。  
> 使用本项目即表示您已知悉并同意遵守相关法律法规，所有后果由用户自行承担。


### 1. 项目目的与性质
本项目（以下简称 **“本项目”**）作为技术研究与学习工具而创建，旨在探索和学习网络及相关技术，特别是自媒体平台相关的数据技术研究。  
本项目仅供学习者与研究者进行 **技术交流** 之用。


### 2. 法律合规性声明
本项目开发者（以下简称 **“开发者”**）郑重提醒用户：  
在下载、安装和使用本项目时，应严格遵守中华人民共和国的相关法律法规，包括但不限于：

- 《中华人民共和国网络安全法》  
- 《中华人民共和国反间谍法》  
- 及其他所有适用的国家法律和政策  

因使用本项目而产生的任何法律责任，均由用户自行承担，**与平台无关**。


### 3. 使用目的限制
- 本项目 **严禁** 用于任何非法目的。  
- 本项目 **不得** 用于非学习、非研究的商业行为。  
- 用户 **不得** 利用本项目进行：
  - 非法侵入他人计算机系统  
  - 侵犯他人知识产权  
  - 侵犯他人其他合法权益  

用户应保证其使用目的 **仅限于个人学习和技术研究**，不得从事任何形式的违法活动。


### 4. 免责声明
- 开发者已尽最大努力确保本项目的正当性与安全性。  
- 然而，开发者 **不对用户因使用本项目而可能引起的任何直接或间接损失承担责任**，包括但不限于：  
  - 数据丢失  
  - 设备损坏  
  - 法律诉讼  


### 5. 知识产权声明
- 本项目的知识产权归 **开发者** 所有。  
- 本项目受到 **著作权法**、**国际著作权条约** 及其他相关法律法规的保护。  
- 用户在遵守本声明及相关法律法规的前提下，可以下载和使用本项目。


### 6. 最终解释权
- 本项目的最终解释权归 **开发者** 所有。  
- 开发者保留随时修改或更新本免责声明的权利，恕不另行通知。  
