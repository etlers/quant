import FinanceDataReader as fdr
# import pymysql
# import datetime
import pandas as pd
# from dateutil.relativedelta import relativedelta 
# import math

# 최신 미국 주식 LIST 가져오기
df_nasdaq = fdr.StockListing('NASDAQ')
df_nyse = fdr.StockListing('NYSE')
df_amex = fdr.StockListing('AMEX')
df_stock = pd.concat([df_nasdaq,df_nyse,df_amex])
# df_stock = df_stock.reset_index()
# nasdaq = df_nasdaq.Symbol.tolist()
# nyse = df_nyse.Symbol.tolist()
# amex = df_amex.Symbol.tolist()

# stock_list = nasdaq+nyse+amex
# stock_list = nasdaq+nyse

# print(df_nyse[df_nyse.Symbol == 'PFE'])

df_stock.to_csv("./stock_list_us.csv", index=False)