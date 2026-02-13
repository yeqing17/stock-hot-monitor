# 修改记录

## 2026-02-13

### 1. 更新雪球 Token
**文件**: `.streamlit/secrets.toml`

更新了雪球 API 的认证 token，确保雪球热榜数据获取正常。

---

### 2. 修复热搜监控模块
**文件**: `views/hotsearch.py`

#### 问题
- 百度热搜 API 返回的数据结构嵌套层级变化，导致无法正确解析热搜列表
- 其他平台（微博、抖音、知乎）存在反爬限制，数据获取不稳定

#### 修改内容

**a) 修复百度热搜数据解析 (行 106-128)**
```python
# 修复前：直接从 cards[0].content 获取
items = data['data']['cards'][0].get('content', [])

# 修复后：正确解析嵌套结构 cards[0].content[0].content
cards_content = data['data']['cards'][0].get('content', [])
items = cards_content[0].get('content', []) if cards_content else []
```

**b) 优化热度值显示逻辑 (行 115-123)**
```python
# 百度没有数字热度值，改用标签（"热"、"新"、"热议"等）
tags = []
if item.get('newHotName'):
    tags.append(item['newHotName'])
if item.get('labelTagName'):
    tags.append(item['labelTagName'])
hot = ' '.join(tags) if tags else '-'
```

**c) 精简可用平台列表 (行 260-267)**
```python
# 修改前：显示5个平台（包含不可用的）
sources = ["百度", "微博", "抖音", "头条", "知乎"]
default=["百度"]

# 修改后：只保留可用的平台
sources = ["百度", "头条"]
default=["百度", "头条"]
```

**d) 修复热度值格式化显示 (行 341-346)**
```python
# 修改前：强制转换为数字，导致字符串标签显示异常
df['hot'] = pd.to_numeric(df['hot'], errors='coerce').fillna(0)
df['hot_fmt'] = df['hot'].apply(lambda x: f"{x:,.0f}" if x > 0 else "-")

# 修改后：根据类型处理，数字格式化，字符串直接使用
df['hot_fmt'] = df['hot'].apply(
    lambda x: f"{x:,.0f}" if isinstance(x, (int, float)) and x > 0
    else (str(x) if x and x != '-' else '-')
)
```

---

### 3. 系统配置调整
**文件**: `/etc/systemd/system/stock-monitor.service`

将 systemd 服务从 `/root/stock-hot-monitor` 迁移到 `/usr/stock-hot-monitor`，统一代码维护路径。

```ini
# 修改前
WorkingDirectory=/root/stock-hot-monitor
ExecStart=/root/stock-hot-monitor/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# 修改后
WorkingDirectory=/usr/stock-hot-monitor
ExecStart=/usr/stock-hot-monitor/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 测试验证
- ✅ 百度热搜数据正常显示
- ✅ 今日头条热搜正常显示
- ✅ 雪球热榜数据正常显示
- ✅ systemd 服务从 /usr 路径正常启动
