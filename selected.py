"""
    영업이익이 늘어나고 있음
    PER, PBR 이 두 값이 1에 가까움
    주당 순이익이 커야 함(EPS / 주가 * 100)
"""
import sys
import time, datetime
import pandas as pd

sys.path.append("C:/Users/etlers/Documents/project/python/common")
import date_util
import conn_db

now_dtm = date_util.get_now_datetime_string()

perform_qry = """
SELECT *
  FROM quant.jongmok_perform
"""


def performance_data():
    result = conn_db.query_data(perform_qry)

    print(result)


def execute():
    performance_data()


if __name__ == "__main__":
    execute()