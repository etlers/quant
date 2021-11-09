"""
    영업이익이 늘어나고 있음
    PER(주가 수익비율)
     - PER이 낮다. 주식가격이 수익에 비해 낮다. 쯕, 현재 주식이 싸다. 미래성장 가치가 반영되지 않은 것으로 IT 등 성장주는 높게 나옴
    PBR(주당순자산비율)
     - 낮을수록 저평가 되었다
    ROE(자기자본이익률로 투입자본 대비 이익 비율)
     - 높을수록 좋다. 3년연속 15% 이상인 기업이 좋다
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
SELECT T1.YEAR_MM
     , T1.PERFORM_VAL
  FROM quant.jongmok_perform T1
 WHERE 1 = 1
   and JONGMOK_CD = '$$CD$$'
   AND YEAR_DIV = '$$YEAR_DIV$$'
   AND DIV_NM = '$$DIV_NM$$'
   AND YEAR_MM < date_format(NOW(), '%Y.%m')
"""
list_target = []

# 외국인 지분율이 너무 많거나 적지 않아야 함.
foreigner_qry = """
SELECT T1.jongmok_cd
     , T1.JONGMOK_NM
     , T1.IDX_VAL AS POSS_RT
     , (SELECT IDX_VAL FROM quant.jongmok_idx WHERE jongmok_cd = t1.jongmok_cd AND DIV_NM = '동일업종 PER(배)') AS BASE_PER
     , T2.YEAR_MM
     , T2.PERFORM_VAL
  FROM quant.jongmok_idx T1
 INNER JOIN quant.jongmok_perform T2
    ON 1 = 1
   AND T1.jongmok_cd = t2.jongmok_cd
   AND T2.YEAR_MM < date_format(NOW(), '%Y.%m')
   AND T2.YEAR_DIV = '년도'
   AND T2.DIV_NM LIKE '%ROE%'
 WHERE 1 = 1
   AND T1.DIV_NM = '외국인소진율(%)'
   AND T1.IDX_VAL BETWEEN 7.5 AND 15.0
   AND T1.INS_DT = (SELECT MAX(INS_DT) FROM quant.jongmok_idx WHERE JONGMOK_CD = T1.JONGMOK_CD)
 ORDER BY T1.JONGMOK_CD, T2.YEAR_MM
"""

list_div_nm = [
    "PBR(배)", "PER(배)", "영업이익률", "부채비율"
]
list_year_div = [
    "년도", "분기"
]


def performance_data(cd, year_div, div_nm):
    extract_qry = perform_qry.replace("$$CD$$",cd).replace("$$YEAR_DIV$$",year_div).replace("$$DIV_NM$$",div_nm)

    rows = conn_db.query_data(extract_qry)

    for row in rows:
        print(row)


def make_target_list():

    # ROE 기준으로 3년 연속 증가했고 10% 이상인 데이터
    def check_roe(cd, df_base):
        pre_roe = 0.0
        for roe in df_base["ROE"]:
            if roe < pre_roe: return
            if roe < 10.0: return
            pre_roe = roe
        list_target.append(cd)

    rows = conn_db.query_data(foreigner_qry)
    df_target = pd.DataFrame(rows, columns=["CD", "NM", "POSS_RT", "BASE_PER", "YM", "ROE"])
    df_code = df_target[["CD"]].drop_duplicates()
    
    for cd in df_code["CD"]:
        check_roe(cd, df_target[(df_target.CD == cd)])    


def execute():
    make_target_list()

    for cd in list_target:
        for year_div in list_year_div:
            for div_nm in list_div_nm:
                performance_data(cd, year_div, div_nm)


if __name__ == "__main__":
    execute()