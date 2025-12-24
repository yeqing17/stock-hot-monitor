# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import time
import os

# 自定义样式
st.markdown("""
<style>
    .block-container {padding-top: 3rem; padding-bottom: 0rem;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=120)
def fetch_xueqiu_top15():
    try:
        u = os.getenv("XUEQIU_U", "2069380474")
        t = os.getenv("XUEQIU_TOKEN", "b1bb0c37f38b0bb4a7f9455cefa1fed6e50b28c2")
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://xueqiu.com/'}
        ts = int(time.time() * 1000)
        url = f"https://stock.xueqiu.com/v5/stock/hot_stock/list.json?page=1&size=15&order=desc&order_by=value&_={ts}&type=20&x=0.5"
        with requests.Session() as s:
            s.headers.update(headers)
            s.cookies.update({'u': u, 'xq_a_token': t})
            r = s.get(url, timeout=10)
            data = r.json()
        if data.get('error_code') == 0 and data.get('data', {}).get('items'):
            items = data['data']['items'][:15]
            return [{'name': i['name'], 'chg': i.get('percent', 0)} for i in items]
    except:
        pass
    return []

@st.cache_data(ttl=120)
def fetch_eastmoney_top15():
    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://guba.eastmoney.com/rank/'}
        url = "https://emappdata.eastmoney.com/stockrank/getAllCurrentList"
        payload = {"appId": "appId01", "globalId": "786e4c21-70dc-435a-93bb-38", "marketType": "0", "pageNo": 1, "pageSize": 15}
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        data = r.json()
        if data.get('code') == 0 and data.get('data'):
            codes = [item['sc'] for item in data['data'][:15]]
            secids = []
            for code in codes:
                pure = code.replace('SZ', '').replace('SH', '')
                if code.startswith('SZ'):
                    secids.append(f"0.{pure}")
                else:
                    secids.append(f"1.{pure}")
            detail_url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
            params = {'fltt': '2', 'fields': 'f3,f12,f14', 'secids': ','.join(secids)}
            r2 = requests.get(detail_url, params=params, headers=headers, timeout=10)
            detail = r2.json()
            result = []
            if detail.get('data', {}).get('diff'):
                for item in detail['data']['diff'][:15]:
                    result.append({'name': item.get('f14', ''), 'chg': item.get('f3', 0)})
            return result
    except:
        pass
    return []

@st.cache_data(ttl=120)
def fetch_tonghuashun_top15():
    """使用同花顺官方 API 获取热股榜，并补充涨跌幅数据"""
    try:
        # 获取热股榜
        url = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock"
        params = {'stock_type': 'a', 'type': 'hour', 'list_type': 'normal'}
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.10jqka.com.cn/'}
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('status_code') == 0 and data.get('data'):
            stocks = data['data'].get('stock_list', [])[:15]
            codes = [s.get('code', '') for s in stocks]
            
            # 获取涨跌幅数据
            chg_map = get_stock_changes(codes)
            
            return [{'name': s.get('name', ''), 'chg': chg_map.get(s.get('code', ''), 0)} for s in stocks]
    except:
        pass
    return []

def get_stock_changes(codes):
    """从东方财富接口获取股票涨跌幅"""
    if not codes:
        return {}
    try:
        # 构建 secids
        secids = []
        for code in codes:
            if code.startswith('6'):
                secids.append(f"1.{code}")
            else:
                secids.append(f"0.{code}")
        
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {'fltt': '2', 'fields': 'f3,f12', 'secids': ','.join(secids)}
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        
        result = {}
        if data.get('data', {}).get('diff'):
            for item in data['data']['diff']:
                code = item.get('f12', '')
                chg = item.get('f3', 0)
                result[code] = chg
        return result
    except:
        return {}

def render_stock_table(data):
    if not data:
        st.info("暂无数据")
        return
    rows = []
    for i, item in enumerate(data[:15]):
        name = item.get('name', '')
        try:
            chg = float(item.get('chg', 0)) if item.get('chg') else 0
        except:
            chg = 0
        if chg > 0:
            chg_str = f"🔴 +{chg:.2f}%"
        elif chg < 0:
            chg_str = f"🟢 {chg:.2f}%"
        else:
            chg_str = "⚪ 0.00%"
        if i == 0:
            rank = "🥇"
        elif i == 1:
            rank = "🥈"
        elif i == 2:
            rank = "🥉"
        else:
            rank = f"{i+1}"
        rows.append({"排名": rank, "股票": name, "涨跌幅": chg_str})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True, height=565)

def render_title_with_logo(logo_path, title):
    col1, col2 = st.columns([0.08, 0.92])
    with col1:
        st.image(logo_path, width=28)
    with col2:
        st.markdown(f"<p style='font-weight:bold;font-size:18px;margin:0;padding-top:2px;'>{title}</p>", unsafe_allow_html=True)

# 紧凑的标题栏
col_title, col_btn = st.columns([6, 1])
with col_title:
    st.markdown(f"### 📈 股票热榜监控 <span style='font-size:14px;color:#888;font-weight:normal;margin-left:20px;'>⏰ {time.strftime('%Y-%m-%d %H:%M:%S')}</span>", unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 刷新", type="primary"):
        st.cache_data.clear()
        st.rerun()

# 三列布局
col1, col2, col3 = st.columns(3)

with col1:
    render_title_with_logo("assets/xueqiu.ico", "雪球热股")
    with st.spinner(""):
        xueqiu_data = fetch_xueqiu_top15()
    render_stock_table(xueqiu_data)
    st.page_link("views/xueqiu.py", label="查看完整榜单 →", use_container_width=True)

with col2:
    render_title_with_logo("assets/eastmoney.ico", "东方财富")
    with st.spinner(""):
        eastmoney_data = fetch_eastmoney_top15()
    render_stock_table(eastmoney_data)
    st.page_link("views/eastmoney.py", label="查看完整榜单 →", use_container_width=True)

with col3:
    render_title_with_logo("assets/iwencai.ico", "同花顺")
    with st.spinner(""):
        tonghuashun_data = fetch_tonghuashun_top15()
    render_stock_table(tonghuashun_data)
    st.page_link("views/tonghuashun.py", label="查看完整榜单 →", use_container_width=True)


# ========== 热搜监控摘要 ==========

# 默认股票关键词
DEFAULT_KEYWORDS = [
    '股', 'A股', '港股', '美股', '股市', '股票', '大盘', '指数', '上证', '深证', '创业板', '科创板',
    '涨停', '跌停', '涨幅', '跌幅', '暴涨', '暴跌', '大涨', '大跌', '飙升', '崩盘',
    '牛市', '熊市', '行情', '走势', '反弹', '回调', '震荡',
    '上市', 'IPO', '退市', '停牌', '复牌', '增发', '配股', '分红', '派息',
    '财报', '业绩', '营收', '净利', '利润', '亏损', '盈利',
    '收购', '并购', '重组', '借壳',
    '基金', '券商', '证券', '私募', '公募', '北向资金', '外资', '主力',
    '证监会', '央行', '降息', '降准', '加息', 'LPR',
    '新能源', '光伏', '锂电', '芯片', '半导体', '人工智能', 'AI', '医药', '白酒', '银行', '地产',
    '茅台', '宁德', '比亚迪', '腾讯', '阿里', '华为', '小米', '特斯拉', '英伟达',
]

def load_custom_keywords():
    if os.path.exists("custom_keywords.txt"):
        with open("custom_keywords.txt", 'r', encoding='utf-8') as f:
            return [kw.strip() for kw in f.read().strip().split('\n') if kw.strip()]
    return []

@st.cache_data(ttl=300)
def fetch_baidu_hot():
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
    results = []
    try:
        url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get('data') and data['data'].get('cards'):
            items = data['data']['cards'][0].get('content', [])
            for i, item in enumerate(items[:50]):
                title = item.get('word', '') or item.get('query', '')
                hot = item.get('hotScore', 0)
                url_link = item.get('url', f"https://www.baidu.com/s?wd={title}")
                if title:
                    results.append({'rank': i + 1, 'title': title, 'hot': hot, 'url': url_link, 'source': '百度'})
    except:
        pass
    return results

def filter_stock_related(items, keywords):
    stock_items = []
    for item in items:
        for kw in keywords:
            if kw in item['title']:
                item['keyword'] = kw
                stock_items.append(item)
                break
    return stock_items

# 热搜监控区域
st.divider()
st.markdown("### 🔍 热搜监控")

keywords = DEFAULT_KEYWORDS + load_custom_keywords()
with st.spinner(""):
    baidu_items = fetch_baidu_hot()
    stock_items = filter_stock_related(baidu_items, keywords)

if stock_items:
    st.caption(f"百度热搜中发现 {len(stock_items)} 条股票相关内容")
    df = pd.DataFrame(stock_items[:10])  # 只显示前10条
    df['hot'] = pd.to_numeric(df['hot'], errors='coerce').fillna(0)
    df_display = df[['rank', 'title', 'keyword', 'source']].copy()
    df_display.columns = ['排名', '标题', '关键词', '来源']
    st.dataframe(df_display, hide_index=True, use_container_width=True, height=200)
else:
    st.info("暂无股票相关热搜")

st.page_link("views/hotsearch.py", label="查看完整热搜 →", use_container_width=True)
