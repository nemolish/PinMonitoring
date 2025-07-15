import pandas as pd
import requests
import baostock as bs
from datetime import datetime


def get_stock_k(stock_code):
    # 登陆系统
    lg = bs.login()
    # 显示登陆返回信息
    print('login respond error_code:' + lg.error_code)
    print('login respond  error_msg:' + lg.error_msg)

    rs = bs.query_history_k_data_plus(stock_code,
                                 "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg",
                                      start_date='2024-07-01', end_date='2025-06-30',
                                      frequency="m", adjustflag="3")

    print('query_history_k_data respond error_code:' + rs.error_code)
    print('query_history_k_data respond  error_msg:' + rs.error_msg)

    # 打印结果集
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)

    # 结果集输出到csv文件
    result.to_csv("year_k_data.csv", index=False)
    print(result)

    # 登出系统
    bs.logout()

# 示例使用
if __name__ == "__main__":
    # 股票代码示例：sh600000（浦发银行）
    stock_code = "sh.600000"
    print(f"正在获取 {stock_code} 的年K线数据...")

    # year_k_data = get_stock_year_k(stock_code)
    get_stock_k(stock_code)

    # if year_k_data is not None:
    #     print("\n年K线数据:")
    #     print(year_k_data)
    #
    #     # 保存到CSV文件
    #     csv_file = f"{stock_code}_year_k.csv"
    #     year_k_data.to_csv(csv_file, index=False)
    #     print(f"\n数据已保存到 {csv_file}")