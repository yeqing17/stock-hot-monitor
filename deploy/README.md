# 服务器部署指南

## 环境要求

- 系统：Ubuntu 20.04/22.04 或 Debian 11/12
- 配置：1核1G 以上（推荐 2核2G）
- 需要开放 8501 端口

## 一键部署

SSH 登录服务器后执行：

```bash
# 下载并运行部署脚本
curl -fsSL https://raw.githubusercontent.com/yeqing17/stock-hot-monitor/main/deploy/install.sh | bash
```

或者手动执行：

```bash
# 克隆项目
git clone https://github.com/yeqing17/stock-hot-monitor.git
cd stock-hot-monitor

# 运行部署脚本
bash deploy/install.sh
```

## 部署后配置

### 修改雪球 Token

```bash
nano ~/stock-hot-monitor/.streamlit/secrets.toml
```

修改为你自己的 Token：

```toml
XUEQIU_U = "你的U值"
XUEQIU_TOKEN = "你的Token"
```

然后重启服务：

```bash
sudo systemctl restart stock-monitor
```

### 云服务器安全组配置

在腾讯云/阿里云控制台，需要在安全组中放行 8501 端口：

1. 进入轻量服务器控制台
2. 找到「防火墙」或「安全组」
3. 添加规则：TCP 端口 8501，来源 0.0.0.0/0

## 常用命令

```bash
# 查看服务状态
sudo systemctl status stock-monitor

# 查看实时日志
sudo journalctl -u stock-monitor -f

# 重启服务
sudo systemctl restart stock-monitor

# 停止服务
sudo systemctl stop stock-monitor

# 启动服务
sudo systemctl start stock-monitor

# 更新代码
cd ~/stock-hot-monitor && git pull && sudo systemctl restart stock-monitor
```

## 使用 Nginx 反向代理（可选）

如果想用 80 端口或配置域名：

```bash
# 安装 nginx
sudo apt install nginx -y

# 配置反向代理
sudo tee /etc/nginx/sites-available/stock-monitor << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 改成你的域名或 IP

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
EOF

# 启用配置
sudo ln -sf /etc/nginx/sites-available/stock-monitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 常见问题

### Q: 同花顺数据获取失败？
A: 正常现象，pywencai 有时会被限流，刷新几次或稍后再试。

### Q: 访问不了？
A: 检查云服务器安全组是否放行了 8501 端口。

### Q: 如何更新到最新版本？
A: 执行 `cd ~/stock-hot-monitor && git pull && sudo systemctl restart stock-monitor`
