# -*- coding: utf-8 -*-
import requests
from bs4 import  BeautifulSoup
import pandas as pd
import time


def get_cbond_data():
    url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple?page=1&num=1000&sort=symbol&asc=1&node=hskzz_z&_s_r_a=page"

    params = {
        "page": 1,
        "num": 1000,
        "sort": "symbol",
        "asc": 1,
        "node": "hskzz_z",
        "_s_r_a": "page"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "http://vip.stock.finance.sina.com.cn/mkt/",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        stocks = response.json()

        # df = pd.DataFrame(stocks)
        # columns_mapping = {
        #     "symbol": "代码",
        #     "name": "名称",
        #     "trade": "最新价",
        #     "pricechange": "涨跌额",
        #     "changepercent": "涨跌幅(%)",
        #     "buy": "买入价",
        #     "sell": "卖出价",
        #     "settlement": "昨日收盘价",
        #     "open": "今日开盘价",
        #     "high": "最高价",
        #     "low": "最低价",
        #     "volume": "成交量(手)",
        #     "amount": "成交额(万)",
        #     "ticktime": "更新时间"
        # }
        #
        # df = df[list(columns_mapping.keys())]
        # df = df.rename(columns=columns_mapping)
        #
        # df["日期"] = pd.to_datetime("today").strftime("%Y-%m-%d")

        result = []
        threshold = 11 / 100.0
        for stock in stocks:
            try:
                low = float(stock['low'])
                changepercent = float(stock['changepercent'])
                settlement = (float(stock['settlement']) + float(stock['trade'])) / 2

                if low > 0 and changepercent <10 and changepercent > -10 and low < settlement * (1 - threshold):
                    result.append(stock)
            except (KeyError, ValueError):
                # 如果数据缺失或格式错误，跳过该股票
                continue
        return result

    except Exception as e:
        return None


result_data = get_cbond_data()

if result_data is not None:
    print(result_data)
else:
    print("未能获取可转债插针数据")

