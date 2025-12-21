# -*- coding: utf-8 -*-
import streamlit as st
import pywencai
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

st.set_page_config(page_title="同花顺热榜", page_icon="🔥", layout="wide", initial_sidebar_state="expanded")

@st.cache_data(ttl=300)
def fetch_data():
    try:
        df = pywencai.get(query='热门个股排名', loop=True)
        if isinstance(df, pd.DataFrame) and not df.empty:
            # 打印列名用于调试
            print("返回的列名:", df.columns.tolist())
            print("数据类型:", df.dtypes)
            return df, time.strftime('%Y-%m-%d %H:%M:%S')
        return None, None
    except Exception as e:
        st.error(f"获取数据失败: {e}")
        return None, None


def normalize_columns(df):
    """标准化列名，适配不同返回格式"""
    # 先重置索引，确保数据结构正确
    df = df.reset_index(drop=True)
    
    # 根据实际返回的列名进行精确映射
    # 返回的列名: ['股票代码', '股票简称', '最新价', '最新涨跌幅', '个股热度排名[20251220]', '个股热度[20251220]', 'market_code', 'code']
    col_map = {}
    used_targets = set()  # 避免重复映射
    
    for col in df.columns:
        target = None
        if col == '股票代码':
            target = 'Code'
        elif col == '股票简称':
            target = 'Name'
        elif col == '最新价':
            target = 'Price'
        elif '涨跌幅' in col:
            target = 'Chg%'
        elif '个股热度排名' in col:
            target = 'Rank'
        elif '个股热度' in col and '排名' not in col:
            target = 'Hot'
        
        if target and target not in used_targets:
            col_map[col] = target
            used_targets.add(target)
    
    df = df.rename(columns=col_map)
    
    # 只保留需要的列
    keep_cols = ['Code', 'Name', 'Price', 'Chg%', 'Hot', 'Rank']
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
    for c in ['Price', 'Chg%', 'Hot', 'Rank']:
        if c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            except TypeError:
                # 如果列不是标准类型，跳过转换
                pass
    
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
        
        # 调整列顺序
        cols_order = ['Name', 'Code', 'Price', 'Chg%', 'Hot', 'Rank', 'Link']
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
            "Name": L["name"], "Code": L["code"], "Price": L["price"],
            "Chg%": L["change_pct"], "Hot": L["hotness"], "Rank": L["rank"]
        }
        if 'Link' in dfd.columns:
            col_config["Link"] = st.column_config.LinkColumn(L["link"], display_text=L["view"])
        
        st.dataframe(styled, hide_index=True, use_container_width=True, height=600, column_config=col_config)

if __name__ == "__main__":
    main()
