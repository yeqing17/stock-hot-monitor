# 📈 股票热榜监控

一个基于 Streamlit 的股票热榜聚合监控系统，整合多个平台的热门股票数据。

## 功能特点

- ⚪ **雪球热股** - 雪球平台热门股票排行
- 💰 **东方财富** - 东方财富股吧人气排行
- 🃏 **同花顺** - 同花顺热门个股排名
- 🔍 **热搜监控** - 百度/微博等平台股票相关热搜

### 主要功能

- 📊 汇总看板 - 一页查看所有平台热股 Top15 + 热搜摘要
- 📈 多种可视化视图（表格、热力图、气泡图、排行榜）
- 🔄 实时数据刷新
- 🎯 智能筛选（涨停、跌停、上涨、下跌）
- 🔑 自定义关键词监控
- 📱 响应式布局，支持手机/平板

## 快速开始

### 安装依赖

```bash
pip install streamlit requests pandas plotly
```

### 运行

```bash
streamlit run app.py
```

浏览器访问 http://localhost:8501

## 项目结构

```
├── app.py                 # 主程序入口（导航配置）
├── app_home.py            # 汇总看板页面
├── views/                 # 页面视图
│   ├── xueqiu.py          # 雪球热股
│   ├── eastmoney.py       # 东方财富
│   ├── tonghuashun.py     # 同花顺
│   └── hotsearch.py       # 热搜监控
├── assets/                # 静态资源（logo图标）
│   ├── xueqiu.ico
│   ├── eastmoney.ico
│   └── iwencai.ico
├── standalone/            # 独立运行版本
├── deploy/                # 服务器部署脚本
├── custom_keywords.txt    # 自定义关键词配置
├── .streamlit/
│   ├── config.toml        # Streamlit 配置
│   └── secrets.toml       # 密钥配置（不提交）
└── README.md
```

## 配置说明

### 雪球 Token 配置

在 `.streamlit/secrets.toml` 中配置：

```toml
XUEQIU_U = "your_u_value"
XUEQIU_TOKEN = "your_token"
```

或设置环境变量 `XUEQIU_U` 和 `XUEQIU_TOKEN`

### 自定义关键词

热搜监控页面支持自定义关键词，配置保存在 `custom_keywords.txt`

## 技术栈

- **Streamlit** - Web 框架
- **Plotly** - 可视化图表
- **Pandas** - 数据处理
- **Requests** - HTTP 请求

## 部署

### Streamlit Cloud（国外）

1. Fork 本仓库到你的 GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io) 并登录 GitHub
3. 选择仓库，Main file 填写 `app.py`
4. 在 Advanced settings → Secrets 中配置雪球 Token
5. 点击 Deploy

> 注意：Streamlit Cloud 服务器在国外，同花顺数据可能无法获取

### 国内服务器部署

推荐使用阿里云/腾讯云轻量服务器（2核2G 即可）

```bash
# SSH 登录服务器后执行一键部署
curl -fsSL https://raw.githubusercontent.com/yeqing17/stock-hot-monitor/main/deploy/install.sh | bash
```

详细部署说明见 [deploy/README.md](deploy/README.md)

## 数据来源

- 雪球：https://xueqiu.com
- 东方财富：https://guba.eastmoney.com
- 同花顺：https://10jqka.com.cn
- 百度热搜：https://top.baidu.com

## 免责声明

本项目仅供学习交流使用，数据来源于各平台公开接口，不构成任何投资建议。
