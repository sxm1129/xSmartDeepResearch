# 阿里云容器镜像服务 (ACR) 推送指南

### 1. 登录阿里云镜像仓库
```bash
docker login --username=sxm1129@126.com crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com
# 密码: hs@A1b2c3d4e5
```

### 2. 自动化打包并推送 (推荐 - 全能版)
无论您是在 Mac M1 还是 Intel 上，都可以运行此脚本一键打造 **"万能镜像"** (同时支持 AMD64 和 ARM64)。

```bash
# 给予权限 (只需一次)
chmod +x deploy/build_and_push_universal.sh

# 一键打包并推送前端 + 后端 (支持 Linux 服务器和 M1 Mac)
./deploy/build_and_push_universal.sh
```
*构建镜像名：`contenthub-backend`, `contenthub-frontend`*
*注意：此脚本利用 `buildx` 打造多架构镜像，拉取时会自动匹配当前系统架构。*

### 3. 在服务器上拉取并部署 (通用)
在您的 Linux 服务器或另一台 Mac 上，可以使用我为您准备的一键部署脚本。该脚本会自动完成：登录 -> 拉取镜像 -> 打标签 -> 启动生产容器。

```bash
# 1. 登录阿里云 (只需一次)
docker login --username=sxm1129@126.com crpi-feit7ei40cgu7xjt.cn-shenzhen.personal.cr.aliyuncs.com

# 2. 赋予脚本执行权限
chmod +x deploy/deploy_docker_linux.sh

# 3. 执行部署
./deploy/deploy_docker_linux.sh
```
### 6. 镜像公共服务 (如 MySQL) 到私有仓库
为了在没有外网或外网较慢的服务器上部署，建议将 MySQL 镜像也转存到您的阿里云仓库：

```bash
# 给予脚本权限
chmod +x deploy/mirror_mysql.sh

# 运行转存脚本 (会自动拉取 amd64 版本并推送)
./deploy/mirror_mysql.sh
```

转存后，生产环境的 `docker-compose.prod.yml` 已经配置好直接拉取您阿里云仓库里的 MySQL 镜像。

### 4. 统一镜像 (Monolith) 构建
如果您希望将所有服务 (Backend + Frontend + Remotion) 打包进一个统一的镜像：

```bash
# 给予脚本权限
chmod +x deploy/build_and_push_monolith.sh

# 构建并推送统一镜像 (支持 amd64/arm64)
./deploy/build_and_push_monolith.sh
```
*镜像名：`dolphin-all-in-one`*

### 5. 统一镜像服务管理 (本地)
使用 `docker-server.sh` 脚本方便地管理统一镜像容器：

```bash
# 赋予权限
chmod +x docker-server.sh

# 启动服务
./docker-server.sh start

# 停止服务
./docker-server.sh stop

# 重启服务
./docker-server.sh restart

# 查看状态
./docker-server.sh status

# 查看实时日志
./docker-server.sh logs

# 更新镜像
./docker-server.sh pull
```
