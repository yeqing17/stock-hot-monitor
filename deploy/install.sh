#!/bin/bash
# 股票热榜监控 - 一键部署脚本 (Ubuntu/Debian)
# 使用方法: bash install.sh

set -e

echo "========== 股票热榜监控 部署脚本 =========="

# 更新系统
echo ">>> 更新系统包..."
sudo apt update && sudo apt upgrade -y

# 安装 Python 和 pip
echo ">>> 安装 Python..."
sudo apt install -y python3 python3-pip python3-venv git

# 克隆项目
echo ">>> 克隆项目..."
cd ~
if [ -d "stock-hot-monitor" ]; then
    cd stock-hot-monitor && git pull
else
    git clone https://github.com/yeqing17/stock-hot-monitor.git
    cd stock-hot-monitor
fi

# 创建虚拟环境
echo ">>> 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo ">>> 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建 secrets.toml
echo ">>> 配置 secrets..."
mkdir -p .streamlit
if [ ! -f ".streamlit/secrets.toml" ]; then
    cat > .streamlit/secrets.toml << 'EOF'
XUEQIU_U = "2069380474"
XUEQIU_TOKEN = "b1bb0c37f38b0bb4a7f9455cefa1fed6e50b28c2"
EOF
    echo "已创建默认 secrets.toml，请稍后修改为你自己的 Token"
fi

# 创建 systemd 服务
echo ">>> 配置系统服务..."
sudo tee /etc/systemd/system/stock-monitor.service > /dev/null << EOF
[Unit]
Description=Stock Hot Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/stock-hot-monitor
ExecStart=$HOME/stock-hot-monitor/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
echo ">>> 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable stock-monitor
sudo systemctl restart stock-monitor

# 开放防火墙端口
echo ">>> 配置防火墙..."
sudo ufw allow 8501/tcp 2>/dev/null || true

echo ""
echo "========== 部署完成 =========="
echo "访问地址: http://你的服务器IP:8501"
echo ""
echo "常用命令:"
echo "  查看状态: sudo systemctl status stock-monitor"
echo "  查看日志: sudo journalctl -u stock-monitor -f"
echo "  重启服务: sudo systemctl restart stock-monitor"
echo "  停止服务: sudo systemctl stop stock-monitor"
echo ""
echo "修改 Token: nano ~/stock-hot-monitor/.streamlit/secrets.toml"
