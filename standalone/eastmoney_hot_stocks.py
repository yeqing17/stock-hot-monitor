# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# --- Language Config ---
L = {
    "title": "东方财富人气榜",
    "settings": "设置", "refresh": "刷新数据", "filters": "筛选条件",
    "market": "市场", "quick_filter": "快捷筛选",
    "limit_up": "涨停", "limit_down": "跌停",
    "rising": "上涨", "falling": "下跌", "reset": "重置",
    "custom_range": "自定义涨跌幅", "results": "筛选结果",
    "updated": "更新时间", "stocks": "只",
    "view_mode": "视图模式", "table": "表格", "heatmap": "热力图",
    "bubble": "气泡图", "rankings": "排行榜",
    "heatmap_title": "人气热力图", "heatmap_desc": "方块大小=热度指数, 颜色=涨跌幅",
    "bubble_title": "人气-涨跌幅气泡图", "bubble_desc": "X轴=热度指数, Y轴=涨跌幅",
    "hotness_top": "人气Top15", "gainers": "涨幅Top15",
    "losers": "跌幅Top15", "rank_rising": "排名上升Top15",
    "details": "股票详情", "no_data": "暂无数据",
    "name": "名称", "code": "代码", "price": "现价",
    "change_pct": "涨跌幅", "change": "涨跌额", "hotness": "热度指数",
    "rank": "排名", "rank_chg": "排名变化",
    "link": "链接", "view": "查看"
}

st.set_page_config(page_title="东方财富人气榜", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=60)
def fetch_data(market="all"):
    """
    获取东方财富人气榜数据
    market: all-全部, ab-A股, hk-港股, us-美股
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://guba.eastmoney.com/rank/',
    }
    
    # 东方财富人气榜API - 使用带排名变化的接口
    market_map = {"all": "", "ab": "A", "hk": "HK", "us": "US"}
    market_code = market_map.get(market, "")
    
    # 尝试使用网页版API
    url = "https://guba.eastmoney.com/interface/GetData.aspx"
    params = {
        "path": "newtopic/api/NewTopicApiController/GetHotStockRankList",
        "param": f"marketType={market_code}&pageIndex=1&pageSize=100",
        "env": "2"
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get('re') and isinstance(data['re'], list):
            return data['re'], time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"网页API失败: {e}")
    
    # 备用：使用原来的API
    market_map2 = {"all": "0", "ab": "1", "hk": "2", "us": "3"}
    market_code2 = market_map2.get(market, "0")
    
    url = "https://emappdata.eastmoney.com/stockrank/getAllCurrentList"
    payload = {
        "appId": "appId01",
        "globalId": "786e4c21-70dc-435a-93bb-38",
        "marketType": market_code2,
        "pageNo": 1,
        "pageSize": 100
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get('code') == 0 and data.get('data'):
            rank_data = data['data']
            codes = [item['sc'] for item in rank_data]
            detail_info = fetch_stock_detail(codes)
            
            for item in rank_data:
                code = item['sc']
                if code in detail_info:
                    item.update(detail_info[code])
            
            return rank_data, time.strftime('%Y-%m-%d %H:%M:%S')
        return None, None
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return None, None


@st.cache_data(ttl=60)
def fetch_stock_detail(codes):
    """获取股票详细信息（名称、现价、涨跌幅等）"""
    if not codes:
        return {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    # 构建secids: 根据代码前缀判断市场
    secids = []
    for code in codes:
        pure_code = code.replace('SZ', '').replace('SH', '').replace('HK', '').replace('US', '')
        if code.startswith('SZ'):
            secids.append(f"0.{pure_code}")
        elif code.startswith('SH'):
            secids.append(f"1.{pure_code}")
        elif code.startswith('HK'):
            secids.append(f"116.{pure_code}")
        else:
            secids.append(f"105.{pure_code}")
    
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        'fltt': '2',
        'fields': 'f2,f3,f4,f12,f14',
        'secids': ','.join(secids),
    }
    
    result = {}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                code = item.get('f12', '')
                # 找到对应的原始代码
                for orig_code in codes:
                    if code in orig_code:
                        result[orig_code] = {
                            'name': item.get('f14', ''),
                            'price': item.get('f2', '-'),
                            'chg_pct': item.get('f3', 0),
                            'chg': item.get('f4', 0),
                        }
                        break
    except Exception as e:
        print(f"获取股票详情失败: {e}")
    
    return result


def process_data(raw_data):
    """处理原始数据"""
    # 打印第一条数据用于调试
    if raw_data:
        print("API返回的字段:", raw_data[0].keys())
        print("第一条数据:", raw_data[0])
    
    records = []
    for item in raw_data:
        # 兼容两种API格式
        record = {
            'Rank': item.get('rk') or item.get('rank') or item.get('Rank', 0),
            'Code': item.get('sc') or item.get('stockcode') or item.get('code', ''),
            'Name': item.get('name') or item.get('stockname') or item.get('sn', ''),
            'Price': item.get('price') or item.get('newprice', '-'),
            'Chg%': item.get('chg_pct') or item.get('zdfd') or item.get('change', 0),
            'Chg': item.get('chg') or item.get('zde', 0),
            'RankChg': item.get('rc') or item.get('rankchg') or item.get('change_rank', 0),
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # 转换数值类型
    for c in ['Rank', 'RankChg', 'Chg%', 'Chg']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    
    # 热度指数：根据排名计算（排名越靠前，热度越高）
    if 'Rank' in df.columns and len(df) > 0:
        max_rank = len(df)
        df['Hot'] = ((max_rank - df['Rank'] + 1) / max_rank * 100).round(1)
    
    return df


def main():
    st.title(L["title"])
    
    with st.sidebar:
        st.header(L["settings"])
        
        # 市场选择
        market_options = {"全部": "all", "A股": "ab", "港股": "hk", "美股": "us"}
        market_label = st.selectbox(L["market"], list(market_options.keys()))
        market = market_options[market_label]
        
        if st.button(L["refresh"], use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    raw_data, utime = fetch_data(market)
    if raw_data is None:
        st.error("获取数据失败，请检查网络或稍后重试")
        st.stop()
    
    df = process_data(raw_data)
    if df.empty:
        st.warning("暂无数据")
        st.stop()
    
    df0 = df.copy()
    
    with st.sidebar:
        st.divider()
        st.header(L["filters"])
        
        st.subheader(L["quick_filter"])
        c1, c2 = st.columns(2)
        btn_lu = c1.button(L["limit_up"], use_container_width=True)
        btn_ld = c2.button(L["limit_down"], use_container_width=True)
        c3, c4 = st.columns(2)
        btn_up = c3.button(L["rising"], use_container_width=True)
        btn_dn = c4.button(L["falling"], use_container_width=True)
        
        if st.button(L["reset"], use_container_width=True):
            st.rerun()
        
        if 'Chg%' in df.columns:
            if btn_lu: df = df[df['Chg%'] >= 9.9]
            elif btn_ld: df = df[df['Chg%'] <= -9.9]
            elif btn_up: df = df[df['Chg%'] > 0]
            elif btn_dn: df = df[df['Chg%'] < 0]
        
        st.divider()
        if 'Chg%' in df0.columns and len(df0) > 0:
            with st.expander(L["custom_range"]):
                min_val = df0['Chg%'].min()
                max_val = df0['Chg%'].max()
                mn = float(min_val) if pd.notna(min_val) else -10.0
                mx = float(max_val) if pd.notna(max_val) else 10.0
                if mn == mx:
                    mn, mx = -10.0, 10.0
                rng = st.slider("Chg%", mn, mx, (mn, mx), step=0.5)
                if rng != (mn, mx):
                    df = df[(df['Chg%'] >= rng[0]) & (df['Chg%'] <= rng[1])]
        
        st.divider()
        st.metric(L["results"], f"{len(df)} {L['stocks']}")
    
    # 顶部信息栏
    up_cnt = len(df[df['Chg%'] > 0]) if 'Chg%' in df.columns else 0
    dn_cnt = len(df[df['Chg%'] < 0]) if 'Chg%' in df.columns else 0
    lu_cnt = len(df[df['Chg%'] >= 9.9]) if 'Chg%' in df.columns else 0
    ld_cnt = len(df[df['Chg%'] <= -9.9]) if 'Chg%' in df.columns else 0
    
    st.markdown(f"**{utime}** | 🔴上涨 {up_cnt} | 🟢下跌 {dn_cnt} | 涨停 {lu_cnt} | 跌停 {ld_cnt} | 共 {len(df)} 只")
    
    view = st.radio(L["view_mode"], [L["table"], L["heatmap"], L["bubble"], L["rankings"]], horizontal=True, label_visibility="collapsed")
    
    if view == L["heatmap"] and 'Hot' in df.columns and 'Chg%' in df.columns:
        st.subheader(L["heatmap_title"])
        st.caption(L["heatmap_desc"])
        fig = px.treemap(df, path=['Name'], values='Hot', color='Chg%',
            color_continuous_scale=['#00a854', '#ffec3d', '#f5222d'],
            color_continuous_midpoint=0,
            hover_data={'Name': True, 'Code': True, 'Chg%': ':.2f', 'Hot': ':,.0f'})
        fig.update_layout(height=700, margin=dict(t=30, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    
    elif view == L["bubble"] and 'Hot' in df.columns and 'Chg%' in df.columns:
        st.subheader(L["bubble_title"])
        st.caption(L["bubble_desc"])
        fig = px.scatter(df, x='Hot', y='Chg%', size='Hot', color='Chg%',
            color_continuous_scale=['#00a854', '#ffec3d', '#f5222d'], color_continuous_midpoint=0,
            hover_name='Name', text='Name', size_max=60)
        fig.update_traces(textposition='top center', textfont_size=10)
        fig.update_layout(height=600)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig, use_container_width=True)

    
    elif view == L["rankings"]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(L["hotness_top"])
            top = df.nlargest(15, 'Hot')[['Name', 'Hot', 'Chg%']].copy()
            top['C'] = top['Chg%'].apply(lambda x: '#f5222d' if x > 0 else '#00a854' if x < 0 else '#666')
            fig = go.Figure(go.Bar(x=top['Hot'], y=top['Name'], orientation='h', marker_color=top['C'],
                text=top['Hot'].apply(lambda x: f'{x:,.0f}'), textposition='outside'))
            fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader(L["gainers"])
            top = df.nlargest(15, 'Chg%')[['Name', 'Chg%']].copy()
            fig = go.Figure(go.Bar(x=top['Chg%'], y=top['Name'], orientation='h', marker_color='#f5222d',
                text=top['Chg%'].apply(lambda x: f'{x:+.2f}%'), textposition='outside'))
            fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
            st.plotly_chart(fig, use_container_width=True)
        
        c3, c4 = st.columns(2)
        with c3:
            st.subheader(L["losers"])
            top = df.nsmallest(15, 'Chg%')[['Name', 'Chg%']].copy()
            fig = go.Figure(go.Bar(x=top['Chg%'].abs(), y=top['Name'], orientation='h', marker_color='#00a854',
                text=top['Chg%'].apply(lambda x: f'{x:.2f}%'), textposition='outside'))
            fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
            st.plotly_chart(fig, use_container_width=True)
        
        with c4:
            st.subheader(L["rank_rising"])
            # 排名变化：正数表示排名上升
            if 'RankChg' in df.columns:
                rising = df[df['RankChg'] > 0].copy()
                if len(rising) > 0:
                    top = rising.nlargest(15, 'RankChg')[['Name', 'RankChg', 'Chg%']].copy()
                    top['C'] = top['Chg%'].apply(lambda x: '#f5222d' if x > 0 else '#00a854' if x < 0 else '#666')
                    fig = go.Figure(go.Bar(x=top['RankChg'], y=top['Name'], orientation='h', marker_color=top['C'],
                        text=top['RankChg'].apply(lambda x: f'↑{int(x)}'), textposition='outside'))
                    fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(L["no_data"])
    
    else:
        st.subheader(L["details"])
        dfd = df.copy()
        
        if 'Code' in dfd.columns:
            dfd['Link'] = dfd['Code'].apply(lambda c: f"https://guba.eastmoney.com/list,{c}.html")
        
        def color_chg(val):
            if pd.isna(val): return ''
            if val > 0: return 'background-color: #ffccc7; color: #cf1322'
            elif val < 0: return 'background-color: #d9f7be; color: #389e0d'
            return ''
        
        # 格式化排名变化显示：正数加↑，负数加↓
        if 'RankChg' in dfd.columns:
            def fmt_rank_chg(val):
                if pd.isna(val) or val == 0: return '-'
                if val > 0: return f'↑{int(val)}'
                return f'↓{int(abs(val))}'
            dfd['RankChg'] = dfd['RankChg'].apply(fmt_rank_chg)
        
        # 调整列顺序
        cols_order = ['Rank', 'Name', 'Code', 'Price', 'Chg%', 'Chg', 'Hot', 'RankChg', 'Link']
        cols_order = [c for c in cols_order if c in dfd.columns]
        dfd = dfd[cols_order]
        
        fmt_dict = {'Chg%': '{:+.2f}%', 'Chg': '{:+.2f}', 'Hot': '{:.1f}', 'Rank': '{:.0f}'}
        fmt_dict = {k: v for k, v in fmt_dict.items() if k in dfd.columns}
        
        styled = dfd.style
        if 'Chg%' in dfd.columns:
            styled = styled.map(color_chg, subset=['Chg%'])
        styled = styled.format(fmt_dict, na_rep='-')
        
        col_config = {
            "Rank": L["rank"], "Name": L["name"], "Code": L["code"], "Price": L["price"],
            "Chg%": L["change_pct"], "Chg": L["change"], "Hot": L["hotness"],
            "RankChg": L["rank_chg"]
        }
        if 'Link' in dfd.columns:
            col_config["Link"] = st.column_config.LinkColumn(L["link"], display_text=L["view"])
        
        st.dataframe(styled, hide_index=True, use_container_width=True, height=600, column_config=col_config)

if __name__ == "__main__":
    main()
