#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺热股榜 - 直接 API 方式（不依赖 pywencai）
数据来源: dq.10jqka.com.cn
"""

import requests
import pandas as pd
import time


def fetch_tonghuashun_hot(stock_type='a', list_type='hour', count=100):
    """
    获取同花顺热股榜数据
    
    参数:
        stock_type: 'a' A股, 'hk' 港股, 'us' 美股
        list_type: 'hour' 小时榜, 'day' 日榜
        count: 获取数量
    
    返回:
        DataFrame 或 None
    """
    url = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock"
    
    params = {
        'stock_type': stock_type,
        'type': list_type,
        'list_type': 'normal',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.10jqka.com.cn/',
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get('status_code') == 0 and data.get('data'):
            stocks = data['data'].get('stock_list', [])
            if stocks:
                df = pd.DataFrame(stocks)
                # 重命名列
                col_map = {
                    'code': '代码',
                    'name': '名称',
                    'hot_value': '热度',
                    'rate': '涨跌幅',
                    'order': '排名',
                    'rise_and_fall': '涨跌额',
                    'new_price': '现价',
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                return df
        return None
    except Exception as e:
        print(f"获取数据失败: {e}")
        return None


def main():
    print("同花顺热股榜 - API 直接获取")
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    df = fetch_tonghuashun_hot()
    
    if df is not None and not df.empty:
        print(f"获取成功！共 {len(df)} 条数据\n")
        
        # 显示前20条
        display_cols = ['排名', '名称', '代码', '现价', '涨跌幅', '热度']
        display_cols = [c for c in display_cols if c in df.columns]
        
        print(df[display_cols].head(20).to_string(index=False))
        
        # 统计信息
        if '涨跌幅' in df.columns:
            df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
            up = len(df[df['涨跌幅'] > 0])
            down = len(df[df['涨跌幅'] < 0])
            print(f"\n统计: 上涨 {up} 只, 下跌 {down} 只")
    else:
        print("获取数据失败")


if __name__ == "__main__":
    main()
