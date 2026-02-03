# xSmartDeepResearch 服务器部署指南

您可以使用以下步骤在您的 Linux 服务器（Ubuntu/CentOS 等）上快速部署 xSmartDeepResearch。

## 1. 环境准备
确保您的服务器已安装：
- **Docker**
- **Docker Compose**

## 2. 文件准备
在服务器上创建一个目录（例如 `/opt/xsmart`），并将以下文件上传到该目录：
1.  **`.env`**: 您的环境变量配置文件（包含 API Key、数据库连接等）。
2.  **`docker-compose.yml`**: 使用项目中的 `deploy/docker-compose.prod.yml`。

> [!IMPORTANT]
> 如果您将 `docker-compose.prod.yml` 放在与 `.env` 同级的目录，请将文件内的 `env_file` 和 `volumes` 路径中的 `../` 去掉。

## 3. 登录阿里云仓库
由于镜像在私有仓库中，您需要先进行登录：
```bash
docker login --username=[您的阿里云账号] crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com
```

## 4. 启动服务
在目录下执行：
```bash
# 拉取最新镜像
docker compose -f docker-compose.prod.yml pull

# 后台启动服务
docker compose -f docker-compose.prod.yml up -d
```

## 5. 验证部署
- **前端访问**：`http://[服务器IP]`
- **接口访问**：`http://[服务器IP]:8000/health`
- **查看日志**：`docker compose -f docker-compose.prod.yml logs -f`
