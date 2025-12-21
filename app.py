# -*- coding: utf-8 -*-
import streamlit as st

# 定义页面 - 使用 views/ 目录避免 Streamlit 自动识别
home = st.Page("app_home.py", title="汇总看板", icon="📊", default=True)
xueqiu = st.Page("views/xueqiu.py", title="雪球热股", icon="⚪")
eastmoney = st.Page("views/eastmoney.py", title="东方财富", icon="💰")
tonghuashun = st.Page("views/tonghuashun.py", title="同花顺", icon="🃏")
hotsearch = st.Page("views/hotsearch.py", title="热搜监控", icon="🔍")

pg = st.navigation([home, xueqiu, eastmoney, tonghuashun, hotsearch])
st.set_page_config(page_title="股票热榜监控", page_icon="📈", layout="wide")
pg.run()
