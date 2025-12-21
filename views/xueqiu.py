# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import os

# --- Language Config ---
L = {
    "title": "雪球热门股票榜",
    "settings": "设置", "refresh": "刷新数据", "filters": "筛选条件",
    "exchange": "交易所", "quick_filter": "快捷筛选",
    "limit_up": "涨停", "limit_down": "跌停",
    "rising": "上涨", "falling": "下跌", "reset": "重置",
    "custom_range": "自定义涨跌幅", "results": "筛选结果",
    "updated": "更新时间", "stocks": "只",
    "view_mode": "视图模式", "table": "表格", "heatmap": "热力图",
    "bubble": "气泡图", "rankings": "排行榜",
    "heatmap_title": "热度热力图", "heatmap_desc": "方块大小=热度, 颜色=涨跌幅",
    "bubble_title": "热度-涨跌幅气泡图", "bubble_desc": "X轴=热度, Y轴=涨跌幅",
    "hotness_top": "热度Top15", "gainers": "涨幅Top15",
    "losers": "跌幅Top15", "rank_rising": "排名上升Top15",
    "details": "股票详情", "no_data": "暂无数据",
    "name": "名称", "code": "代码", "price": "现价",
    "change_pct": "涨跌幅", "change": "涨跌额", "hotness": "热度",
    "rank_chg": "排名变化", "link": "链接", "view": "查看"
}

@st.cache_data(ttl=60)
def fetch_data():
    try:
        u = st.secrets.get("XUEQIU_U") or os.getenv("XUEQIU_U", "2069380474")
        t = st.secrets.get("XUEQIU_TOKEN") or os.getenv("XUEQIU_TOKEN", "b1bb0c37f38b0bb4a7f9455cefa1fed6e50b28c2")
    except:
        u = os.getenv("XUEQIU_U", "")
        t = os.getenv("XUEQIU_TOKEN", "")
    
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://xueqiu.com/'}
    ts = int(time.time() * 1000)
    url = f"https://stock.xueqiu.com/v5/stock/hot_stock/list.json?page=1&size=100&order=desc&order_by=value&_={ts}&type=20&x=0.5"
    
    try:
        with requests.Session() as s:
            s.headers.update(headers)
            s.cookies.update({'u': u, 'xq_a_token': t})
            r = s.get(url, timeout=10)
            r.raise_for_status()
        data = r.json()
        if data.get('error_code') != 0:
            return None, None
        return data['data']['items'], time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None, None

st.title(L["title"])

data, utime = fetch_data()
if data is None:
    st.error("Failed to fetch data")
    st.stop()

df = pd.DataFrame(data)
cols = ['name','symbol','current','percent','chg','exchange','value','rank_change']
df = df[[c for c in cols if c in df.columns]]
df = df.rename(columns={'name':'Name','symbol':'Code','current':'Price','percent':'Chg%','chg':'Chg','exchange':'Exch','value':'Hot','rank_change':'Rank'})

for c in ['Price','Chg%','Chg','Hot']:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='coerce')
if 'Rank' in df.columns:
    df['Rank'] = pd.to_numeric(df['Rank'], errors='coerce').astype('Int64')

df0 = df.copy()

with st.sidebar:
    st.header(L["settings"])
    if st.button(L["refresh"], use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.header(L["filters"])
    
    if 'Exch' in df.columns:
        exs = df0['Exch'].dropna().unique().tolist()
        sel = st.multiselect(L["exchange"], exs, default=exs)
        df = df[df['Exch'].isin(sel)]
    
    st.divider()
    st.subheader(L["quick_filter"])
    c1,c2 = st.columns(2)
    btn_lu = c1.button(L["limit_up"], use_container_width=True)
    btn_ld = c2.button(L["limit_down"], use_container_width=True)
    c3,c4 = st.columns(2)
    btn_up = c3.button(L["rising"], use_container_width=True)
    btn_dn = c4.button(L["falling"], use_container_width=True)
    
    if st.button(L["reset"], use_container_width=True):
        st.rerun()
    
    if 'Chg%' in df.columns:
        if btn_lu: df = df[df['Chg%']>=9.9]
        elif btn_ld: df = df[df['Chg%']<=-9.9]
        elif btn_up: df = df[df['Chg%']>0]
        elif btn_dn: df = df[df['Chg%']<0]
    
    st.divider()
    if 'Chg%' in df0.columns:
        with st.expander(L["custom_range"]):
            mn,mx = float(df0['Chg%'].min() or -10), float(df0['Chg%'].max() or 10)
            rng = st.slider("Chg%", mn, mx, (mn,mx), step=0.5)
            if rng != (mn,mx):
                df = df[(df['Chg%']>=rng[0])&(df['Chg%']<=rng[1])]
    
    st.divider()
    st.metric(L["results"], f"{len(df)} {L['stocks']}")

up_cnt = len(df[df['Chg%']>0]) if 'Chg%' in df.columns else 0
dn_cnt = len(df[df['Chg%']<0]) if 'Chg%' in df.columns else 0
lu_cnt = len(df[df['Chg%']>=9.9]) if 'Chg%' in df.columns else 0
ld_cnt = len(df[df['Chg%']<=-9.9]) if 'Chg%' in df.columns else 0

st.markdown(f"**{utime}** | 🔴上涨 {up_cnt} | 🟢下跌 {dn_cnt} | 涨停 {lu_cnt} | 跌停 {ld_cnt} | 共 {len(df)} 只")

view = st.radio(L["view_mode"], [L["table"], L["heatmap"], L["bubble"], L["rankings"]], horizontal=True, label_visibility="collapsed")

if view == L["heatmap"]:
    st.subheader(L["heatmap_title"])
    st.caption(L["heatmap_desc"])
    fig = px.treemap(df, path=['Exch','Name'] if 'Exch' in df.columns else ['Name'],
        values='Hot', color='Chg%', color_continuous_scale=['#00a854','#ffec3d','#f5222d'],
        color_continuous_midpoint=0, hover_data={'Name':True,'Code':True,'Price':':.2f','Chg%':':.2f','Hot':':,.0f'})
    fig.update_layout(height=700, margin=dict(t=30,l=10,r=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

elif view == L["bubble"]:
    st.subheader(L["bubble_title"])
    st.caption(L["bubble_desc"])
    fig = px.scatter(df, x='Hot', y='Chg%', size='Hot', color='Chg%',
        color_continuous_scale=['#00a854','#ffec3d','#f5222d'], color_continuous_midpoint=0,
        hover_name='Name', hover_data={'Code':True,'Price':':.2f','Exch':True}, text='Name', size_max=60)
    fig.update_traces(textposition='top center', textfont_size=10)
    fig.update_layout(height=600)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    st.plotly_chart(fig, use_container_width=True)

elif view == L["rankings"]:
    c1,c2 = st.columns(2)
    with c1:
        st.subheader(L["hotness_top"])
        top = df.nlargest(15,'Hot')[['Name','Hot','Chg%']].copy()
        top['C'] = top['Chg%'].apply(lambda x:'#f5222d' if x>0 else '#00a854' if x<0 else '#666')
        fig = go.Figure(go.Bar(x=top['Hot'],y=top['Name'],orientation='h',marker_color=top['C'],
            text=top['Hot'].apply(lambda x:f'{x:,.0f}'),textposition='outside'))
        fig.update_layout(height=500,yaxis=dict(autorange="reversed"),margin=dict(l=10,r=10,t=10,b=40))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader(L["gainers"])
        top = df.nlargest(15,'Chg%')[['Name','Chg%']].copy()
        fig = go.Figure(go.Bar(x=top['Chg%'],y=top['Name'],orientation='h',marker_color='#f5222d',
            text=top['Chg%'].apply(lambda x:f'{x:+.2f}%'),textposition='outside'))
        fig.update_layout(height=500,yaxis=dict(autorange="reversed"),margin=dict(l=10,r=10,t=10,b=40))
        st.plotly_chart(fig, use_container_width=True)
    
    c3,c4 = st.columns(2)
    with c3:
        st.subheader(L["losers"])
        top = df.nsmallest(15,'Chg%')[['Name','Chg%']].copy()
        fig = go.Figure(go.Bar(x=top['Chg%'].abs(),y=top['Name'],orientation='h',marker_color='#00a854',
            text=top['Chg%'].apply(lambda x:f'{x:.2f}%'),textposition='outside'))
        fig.update_layout(height=500,yaxis=dict(autorange="reversed"),margin=dict(l=10,r=10,t=10,b=40))
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.subheader(L["rank_rising"])
        if 'Rank' in df.columns:
            top = df[df['Rank']>0].nlargest(15,'Rank')[['Name','Rank','Chg%']].copy()
            if len(top)>0:
                top['C'] = top['Chg%'].apply(lambda x:'#f5222d' if x>0 else '#00a854' if x<0 else '#666')
                fig = go.Figure(go.Bar(x=top['Rank'],y=top['Name'],orientation='h',marker_color=top['C'],
                    text=top['Rank'].apply(lambda x:f'+{x}'),textposition='outside'))
                fig.update_layout(height=500,yaxis=dict(autorange="reversed"),margin=dict(l=10,r=10,t=10,b=40))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(L["no_data"])

else:
    st.subheader(L["details"])
    dfd = df.copy()
    
    if 'Code' in dfd.columns: 
        dfd['Link'] = dfd['Code'].apply(lambda c:f"https://xueqiu.com/S/{c}")
    
    def color_chg(val):
        if pd.isna(val): return ''
        if val > 0: return 'background-color: #ffccc7; color: #cf1322'
        elif val < 0: return 'background-color: #d9f7be; color: #389e0d'
        return ''
    
    cols_order = ['Name', 'Code', 'Price', 'Chg%', 'Chg', 'Exch', 'Hot', 'Rank', 'Link']
    cols_order = [c for c in cols_order if c in dfd.columns]
    dfd = dfd[cols_order]
    
    styled = dfd.style.map(color_chg, subset=['Chg%', 'Chg'] if 'Chg' in dfd.columns else ['Chg%'])
    styled = styled.format({
        'Price': '{:.2f}',
        'Chg%': '{:+.2f}%',
        'Chg': '{:+.2f}',
        'Hot': '{:,.0f}',
        'Rank': '{:+d}'
    }, na_rep='-')
    
    st.dataframe(styled, hide_index=True, use_container_width=True, height=600, 
        column_config={
            "Name": L["name"], "Code": L["code"], "Price": L["price"],
            "Chg%": L["change_pct"], "Chg": L["change"], "Exch": L["exchange"],
            "Hot": L["hotness"], "Rank": L["rank_chg"],
            "Link": st.column_config.LinkColumn(L["link"], display_text=L["view"])
        })
