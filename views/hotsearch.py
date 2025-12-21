# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import time
import json
import os

# --- Language Config ---
L = {
    "title": "热搜股票监控",
    "settings": "设置", "refresh": "刷新数据",
    "source": "数据源",
    "updated": "更新时间", "results": "相关结果",
    "no_data": "暂无股票相关热搜",
    "keywords": "股票关键词"
}

# 自定义关键词保存文件
CUSTOM_KEYWORDS_FILE = "custom_keywords.txt"

# 默认股票相关关键词
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

# 预设的自定义关键词（热门概念）
PRESET_CUSTOM_KEYWORDS = ['商业航天', '机器人', '无人机', '量子', '卫星']

# st.set_page_config 已在主程序设置


def load_custom_keywords():
    """从文件加载自定义关键词"""
    if os.path.exists(CUSTOM_KEYWORDS_FILE):
        with open(CUSTOM_KEYWORDS_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return '\n'.join(PRESET_CUSTOM_KEYWORDS)


def save_custom_keywords(keywords_text):
    """保存自定义关键词到文件"""
    with open(CUSTOM_KEYWORDS_FILE, 'w', encoding='utf-8') as f:
        f.write(keywords_text)


def is_stock_related(title, keywords):
    """判断标题是否与股票相关"""
    for keyword in keywords:
        if keyword in title:
            return True, keyword
    return False, None


@st.cache_data(ttl=300)
def fetch_weibo_hot():
    """获取微博热搜 - 官方API"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    results = []
    try:
        # 微博官方热搜API
        url = "https://weibo.com/ajax/side/hotSearch"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('data') and data['data'].get('realtime'):
            for i, item in enumerate(data['data']['realtime'][:50]):
                title = item.get('word', '')
                hot = item.get('num', 0)
                if title:
                    results.append({
                        'rank': i + 1,
                        'title': title,
                        'hot': hot,
                        'url': f"https://s.weibo.com/weibo?q=%23{title}%23",
                        'source': '微博'
                    })
    except Exception as e:
        print(f"微博热搜失败: {e}")
    return results


@st.cache_data(ttl=300)
def fetch_baidu_hot():
    """获取百度热搜 - 官方API"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
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
                    results.append({
                        'rank': i + 1,
                        'title': title,
                        'hot': hot,
                        'url': url_link,
                        'source': '百度'
                    })
    except Exception as e:
        print(f"百度热搜失败: {e}")
    return results


@st.cache_data(ttl=300)
def fetch_douyin_hot():
    """获取抖音热搜"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    results = []
    try:
        # 抖音热点榜API
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('data') and data['data'].get('word_list'):
            for i, item in enumerate(data['data']['word_list'][:50]):
                title = item.get('word', '')
                hot = item.get('hot_value', 0)
                if title:
                    results.append({
                        'rank': i + 1,
                        'title': title,
                        'hot': hot,
                        'url': f"https://www.douyin.com/search/{title}",
                        'source': '抖音'
                    })
    except Exception as e:
        print(f"抖音热搜失败: {e}")
    return results


@st.cache_data(ttl=300)
def fetch_toutiao_hot():
    """获取今日头条热搜"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    results = []
    try:
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('data'):
            for i, item in enumerate(data['data'][:50]):
                title = item.get('Title', '')
                hot = item.get('HotValue', 0)
                url_link = item.get('Url', '')
                if title:
                    results.append({
                        'rank': i + 1,
                        'title': title,
                        'hot': hot,
                        'url': url_link,
                        'source': '头条'
                    })
    except Exception as e:
        print(f"头条热搜失败: {e}")
    return results


@st.cache_data(ttl=300)
def fetch_zhihu_hot():
    """获取知乎热榜"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    results = []
    try:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('data'):
            for i, item in enumerate(data['data'][:50]):
                target = item.get('target', {})
                title = target.get('title', '')
                hot = item.get('detail_text', '0').replace('万热度', '0000').replace('热度', '')
                url_link = f"https://www.zhihu.com/question/{target.get('id', '')}"
                if title:
                    results.append({
                        'rank': i + 1,
                        'title': title,
                        'hot': hot,
                        'url': url_link,
                        'source': '知乎'
                    })
    except Exception as e:
        print(f"知乎热榜失败: {e}")
    return results


def filter_stock_related(items, keywords):
    """筛选股票相关的热搜"""
    stock_items = []
    for item in items:
        is_related, keyword = is_stock_related(item['title'], keywords)
        if is_related:
            item['keyword'] = keyword
            stock_items.append(item)
    return stock_items


def main():
    st.title(L["title"])
    
    # 构建关键词列表
    keywords = DEFAULT_KEYWORDS.copy()
    
    # 从文件加载自定义关键词
    saved_keywords = load_custom_keywords()
    
    with st.sidebar:
        st.header(L["settings"])
        
        if st.button(L["refresh"], use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        sources = st.multiselect(
            L["source"],
            ["百度", "微博", "抖音", "头条", "知乎"],
            default=["百度"]  # 默认只选百度，因为其他平台可能有反爬限制
        )
        
        st.caption("💡 部分平台可能因反爬限制无法获取数据")
        
        st.divider()
        
        with st.expander(L["keywords"], expanded=True):
            custom_keywords = st.text_area(
                "自定义关键词（每行一个，按 Ctrl+Enter 保存）",
                value=saved_keywords,
                height=150,
                key="custom_kw_input"
            )
            # 如果内容有变化，保存到文件
            if custom_keywords != saved_keywords:
                save_custom_keywords(custom_keywords)
                st.toast("已保存")
    
    # 添加自定义关键词
    if custom_keywords:
        for kw in custom_keywords.strip().split('\n'):
            kw = kw.strip()
            if kw and kw not in keywords:
                keywords.append(kw)
    
    all_items = []
    
    with st.spinner("正在获取热搜数据..."):
        if "微博" in sources:
            all_items.extend(fetch_weibo_hot())
        if "百度" in sources:
            all_items.extend(fetch_baidu_hot())
        if "抖音" in sources:
            all_items.extend(fetch_douyin_hot())
        if "头条" in sources:
            all_items.extend(fetch_toutiao_hot())
        if "知乎" in sources:
            all_items.extend(fetch_zhihu_hot())
    
    stock_items = filter_stock_related(all_items, keywords)
    utime = time.strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown(f"**{utime}** | 共获取 {len(all_items)} 条热搜 | 股票相关 {len(stock_items)} 条 | 关键词 {len(keywords)} 个")
    
    # 显示当前使用的关键词
    with st.expander(f"📋 查看全部关键词 ({len(keywords)} 个)"):
        # 分类显示
        custom_kws = [kw for kw in keywords if kw not in DEFAULT_KEYWORDS]
        if custom_kws:
            st.markdown(f"**自定义关键词 ({len(custom_kws)}):** {', '.join(custom_kws)}")
            st.divider()
        st.markdown(f"**默认关键词 ({len(DEFAULT_KEYWORDS)}):** {', '.join(DEFAULT_KEYWORDS)}")
    
    if not stock_items:
        st.info(L["no_data"])
        with st.expander("查看全部热搜"):
            if all_items:
                df_all = pd.DataFrame(all_items)
                st.dataframe(df_all, hide_index=True, use_container_width=True)
    else:
        active_sources = [s for s in sources if any(i['source'] == s for i in stock_items)]
        tab_names = [f"全部 ({len(stock_items)})"] + [f"{s} ({len([i for i in stock_items if i['source']==s])})" for s in active_sources]
        tabs = st.tabs(tab_names)
        
        with tabs[0]:
            display_items(stock_items)
        
        for idx, source in enumerate(active_sources):
            with tabs[idx + 1]:
                display_items([i for i in stock_items if i['source'] == source])


def display_items(items):
    if not items:
        st.info(L["no_data"])
        return
    
    df = pd.DataFrame(items)
    if 'hot' in df.columns:
        df['hot'] = pd.to_numeric(df['hot'], errors='coerce').fillna(0)
        df['hot_fmt'] = df['hot'].apply(lambda x: f"{x:,.0f}" if x > 0 else "-")
    
    cols = ['rank', 'title', 'keyword', 'hot_fmt', 'source', 'url']
    cols = [c for c in cols if c in df.columns]
    df_display = df[cols].copy()
    df_display.columns = ['排名', '标题', '关键词', '热度', '来源', '链接'][:len(cols)]
    
    col_config = {}
    if '链接' in df_display.columns:
        col_config['链接'] = st.column_config.LinkColumn("链接", display_text="查看")
    
    st.dataframe(df_display, hide_index=True, use_container_width=True, height=500, column_config=col_config)


if __name__ == "__main__":
    main()
