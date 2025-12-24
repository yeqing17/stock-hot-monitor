# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# --- Language Config ---
L = {
    "title": "同花顺热门股票榜",
    "settings": "设置", "refresh": "刷新数据", "filters": "筛选条件",
    "quick_filter": "快捷筛选",
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
    "change_pct": "涨跌幅", "hotness": "热度", "rank": "排名", "link": "链接", "view": "查看"
}

# st.set_page_config 已在主程序设置

@st.cache_data(ttl=300)
def fetch_data():
    """使用同花顺官方 API 获取热股榜，并补充涨跌幅数据"""
    try:
        url = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock"
        params = {'stock_type': 'a', 'type': 'hour', 'list_type': 'normal'}
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.10jqka.com.cn/'}
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        
        if data.get('status_code') == 0 and data.get('data'):
            stocks = data['data'].get('stock_list', [])
            if stocks:
                df = pd.DataFrame(stocks)
                codes = df['code'].tolist()
                
                # 保存原始热度值
                df['hot_value'] = df['rate'].astype(float)
                
                # 获取涨跌幅和现价数据
                quote_map = get_stock_quotes(codes)
                df['rate'] = df['code'].map(lambda x: quote_map.get(x, {}).get('chg', 0))
                df['new_price'] = df['code'].map(lambda x: quote_map.get(x, {}).get('price', 0))
                
                return df, time.strftime('%Y-%m-%d %H:%M:%S')
        return None, None
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return None, None

def get_stock_quotes(codes):
    """从东方财富接口获取股票涨跌幅和现价"""
    if not codes:
        return {}
    try:
        secids = []
        for code in codes:
            if code.startswith('6'):
                secids.append(f"1.{code}")
            else:
                secids.append(f"0.{code}")
        
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {'fltt': '2', 'fields': 'f2,f3,f12', 'secids': ','.join(secids)}
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://quote.eastmoney.com/'}
        
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        
        result = {}
        if data.get('data', {}).get('diff'):
            for item in data['data']['diff']:
                code = item.get('f12', '')
                result[code] = {'chg': item.get('f3', 0), 'price': item.get('f2', 0)}
        return result
    except:
        return {}


def normalize_columns(df):
    """标准化列名 - 适配同花顺官方 API + 东方财富涨跌幅"""
    df = df.reset_index(drop=True)
    
    # 列名映射
    col_map = {
        'code': 'Code',
        'name': 'Name',
        'new_price': 'Price',
        'rate': 'Chg%',
        'order': 'Rank',
        'hot_value': 'Hot',
    }
    
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    
    # 如果没有 Rank 列，根据行号生成排名
    if 'Rank' not in df.columns:
        df['Rank'] = range(1, len(df) + 1)
    
    # 只保留需要的列
    keep_cols = ['Rank', 'Code', 'Name', 'Price', 'Chg%', 'Hot']
    df = df[[c for c in keep_cols if c in df.columns]]
    
    return df

def main():
    st.title(L["title"])
    
    data, utime = fetch_data()
    if data is None:
        st.error("获取数据失败，请检查网络或稍后重试")
        st.stop()
    
    df = normalize_columns(data.copy())
    
    # 确保数值列为数值类型
    for c in ['Price', 'Chg%', 'Hot']:
        if c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            except TypeError:
                pass
    
    # 排名直接用行号（数据本身已按热度排序）
    df['Rank'] = range(1, len(df) + 1)
    
    df0 = df.copy()
    
    with st.sidebar:
        st.header(L["settings"])
        if st.button(L["refresh"], use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
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
        if 'Chg%' in df0.columns:
            with st.expander(L["custom_range"]):
                mn, mx = float(df0['Chg%'].min() or -10), float(df0['Chg%'].max() or 10)
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
            hover_data={'Name': True, 'Code': True, 'Price': ':.2f', 'Chg%': ':.2f', 'Hot': ':,.0f'} if 'Code' in df.columns else {'Name': True, 'Chg%': ':.2f', 'Hot': ':,.0f'})
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
        if 'Hot' in df.columns:
            with c1:
                st.subheader(L["hotness_top"])
                top = df.nlargest(15, 'Hot')[['Name', 'Hot', 'Chg%']].copy() if 'Chg%' in df.columns else df.nlargest(15, 'Hot')[['Name', 'Hot']].copy()
                if 'Chg%' in top.columns:
                    top['C'] = top['Chg%'].apply(lambda x: '#f5222d' if x > 0 else '#00a854' if x < 0 else '#666')
                else:
                    top['C'] = '#1890ff'
                fig = go.Figure(go.Bar(x=top['Hot'], y=top['Name'], orientation='h', marker_color=top['C'],
                    text=top['Hot'].apply(lambda x: f'{x:,.0f}'), textposition='outside'))
                fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
                st.plotly_chart(fig, use_container_width=True)
        
        if 'Chg%' in df.columns:
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
                if 'Rank' in df.columns:
                    st.subheader(L["rank_rising"])
                    top = df.nsmallest(15, 'Rank')[['Name', 'Rank', 'Chg%']].copy()
                    if len(top) > 0:
                        top['C'] = top['Chg%'].apply(lambda x: '#f5222d' if x > 0 else '#00a854' if x < 0 else '#666')
                        fig = go.Figure(go.Bar(x=top['Rank'], y=top['Name'], orientation='h', marker_color=top['C'],
                            text=top['Rank'].apply(lambda x: f'{int(x)}'), textposition='outside'))
                        fig.update_layout(height=500, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=10, b=40))
                        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.subheader(L["details"])
        dfd = df.copy()
        
        if 'Code' in dfd.columns:
            dfd['Link'] = dfd['Code'].apply(lambda c: f"https://www.iwencai.com/unifiedwap/result?w={c}")
        
        def color_chg(val):
            if pd.isna(val): return ''
            if val > 0: return 'background-color: #ffccc7; color: #cf1322'
            elif val < 0: return 'background-color: #d9f7be; color: #389e0d'
            return ''
        
        # 调整列顺序，排名放第一列
        cols_order = ['Rank', 'Name', 'Code', 'Price', 'Chg%', 'Hot', 'Link']
        cols_order = [c for c in cols_order if c in dfd.columns]
        dfd = dfd[cols_order]
        
        fmt_dict = {}
        if 'Price' in dfd.columns: fmt_dict['Price'] = '{:.2f}'
        if 'Chg%' in dfd.columns: fmt_dict['Chg%'] = '{:+.2f}%'
        if 'Hot' in dfd.columns: fmt_dict['Hot'] = '{:,.0f}'
        if 'Rank' in dfd.columns: fmt_dict['Rank'] = '{:.0f}'
        
        styled = dfd.style
        if 'Chg%' in dfd.columns:
            styled = styled.applymap(color_chg, subset=['Chg%'])
        styled = styled.format(fmt_dict, na_rep='-')
        
        col_config = {
            "Rank": st.column_config.NumberColumn(L["rank"], width="small"),
            "Name": st.column_config.TextColumn(L["name"], width="medium"),
            "Code": st.column_config.TextColumn(L["code"], width="small"),
            "Price": st.column_config.NumberColumn(L["price"], width="small"),
            "Chg%": st.column_config.NumberColumn(L["change_pct"], width="small"),
            "Hot": st.column_config.NumberColumn(L["hotness"], width="small"),
        }
        if 'Link' in dfd.columns:
            col_config["Link"] = st.column_config.LinkColumn(L["link"], display_text=L["view"], width="large")
        
        st.dataframe(styled, hide_index=True, use_container_width=True, height=600, column_config=col_config)

if __name__ == "__main__":
    main()
