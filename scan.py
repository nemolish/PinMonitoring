# -*- coding: utf-8 -*-
import requests
from bs4 import  BeautifulSoup
import pandas as pd
# import akshare as ak
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import re
import json

import base64

def add_to_16(value):
    return str.encode(value, 'utf-8')

# 加密函数
def aes_encrypt(text, key):
    # 创建AES cipher对象
    cipher  = AES.new(add_to_16(key), AES.MODE_ECB)
    # 加密并添加padding
    padded_data = pad(add_to_16(text), AES.block_size)

    encrypted = cipher.encrypt(padded_data)
    return encrypted.hex()

def get_jisilu_key():
    # 先获取登录页面获取必要token/cookie
    login_page = requests.get('https://www.jisilu.cn/account/login/')

    pattern = r"var key = '(.*?)';"
    match = re.search(pattern, login_page.text)

    if match:
        return match.group(1)
    else:
        return '397151C04723421F'
def get_jisilu_session():
    session = requests.Session()

    key = get_jisilu_key()

    login_data = {
        'user_name': aes_encrypt('', key),
        'password': aes_encrypt('', key),
        'aes': 1,
        'auto_login': 0
    }


    response = session.post('https://www.jisilu.cn/webapi/account/login_process/', data=login_data)
    print(response.text)  # 查看登录是否成功
    return session

def get_kzz_code_from_jisilu(session):
    # 可转债列表
    list = session.get('https://www.jisilu.cn/webapi/cb/list/')
    # 退市可转债列表
    delisted = session.get('https://www.jisilu.cn/webapi/cb/delisted/')
    print(list.json)
    list_object = json.loads(list.text)
    delisted_object = json.loads(delisted.text)
    result = []
    threshold = 11 / 100.0
    for stock in list_object['data']:
        try:
            result.append(stock['bond_id'])
        except (KeyError, ValueError):
            # 如果数据缺失或格式错误，跳过该股票
            continue

    for stock in delisted_object['data']:
        try:
            result.append(stock['bond_id'])
        except (KeyError, ValueError):
            # 如果数据缺失或格式错误，跳过该股票
            continue
    return result


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


def fetch_cb_daily_kline(stock_code):
    """
    通过新浪财经API获取可转债日K线数据

    参数:
        stock_code (str): 可转债代码，如 '110059'（浦发转债）

    返回:
        DataFrame: 包含日K线数据（日期、开盘价、最高价、最低价、收盘价、成交量等）
    """
    # 判断市场（沪市 or 深市）
    if stock_code.startswith(('110', '113')):
        symbol = f"sh{stock_code}"  # 沪市可转债
    elif stock_code.startswith(('123', '127', '128')):
        symbol = f"sz{stock_code}"  # 深市可转债
    else:
        raise ValueError("不支持的转债代码格式！")

    # 新浪财经API（日K线数据）
    url = f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol={symbol}&scale=240&ma=5&datalen=1000"

    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()

        if not data:
            print(f"未找到可转债 {stock_code} 的数据！")
            return None

        # 转换为DataFrame
        df = pd.DataFrame(data)
        df['day'] = pd.to_datetime(df['day'])  # 转换日期格式
        df.set_index('day', inplace=True)

        # 重命名列（新浪返回的字段名是中文）
        column_map = {
            'open': '开盘价',
            'high': '最高价',
            'low': '最低价',
            'close': '收盘价',
            'volume': '成交量'
        }
        df.rename(columns=column_map, inplace=True)

        return df

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    except ValueError as e:
        print(f"数据解析失败: {e}")
        return None

session = get_jisilu_session()
kzz_id = get_kzz_code_from_jisilu(session)
print(kzz_id)
# bond_zh_cov_df = ak.bond_zh_cov()
# print(bond_zh_cov_df)
# # 示例：获取浦发转债（110059）的日K线数据
# if __name__ == "__main__":
#     stock_code = "110059"  # 可转债代码
#     kline_data = fetch_cb_daily_kline(stock_code)
#
#     if kline_data is not None:
#         print(f"可转债 {stock_code} 的日K线数据（最近5条）：")
#         print(kline_data.tail())  # 显示最近5天的数据
#
# result_data = get_cbond_data()
#
# if result_data is not None:
#     print(result_data)
# else:
#     print("未能获取可转债插针数据")

