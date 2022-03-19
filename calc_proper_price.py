"""
1. EPS * PER
2. BPS
3. EPS * 10
4. EPS * ROE * 100
5. 지배주주순이익 * PER / 유통주식수
6. 당기순이익 * PER / 유통주식수
7. (자기자본 + (초과이익 / 할인율)) / 유통주식수
"""
import pandas as pd


df_stock_list = pd.read_csv("./stock_list.csv", encoding="CP949")
df_stock_list.rename(columns = {"단축코드": 'JONGMOK_CD', "한글 종목약명": 'JONGMOK_NM', "상장주식수": "STOCK_AMT"}, inplace = True)


def execute():
    pass


if __name__ == "__main__":
    execute()