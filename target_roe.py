"""
    외국인 지분율
"""
import pandas as pd
import matplotlib.pyplot as plt
import os, sys

sys.path.append("/home/ubuntu/etlers/pysrc/pycom")
import conn_db


run_qry = """
select JONGMOK_NM 
     , YEAR_MM 
     , PERFORM_VAL 
  from quant.jongmok_perform
 where 1 = 1
   and YEAR_DIV = '년도'
   and PERFORM_VAL != 0
   and DIV_NM = 'ROE(지배주주)'
"""
list_result = []

def execute(qry=run_qry):
    
    list_data = conn_db.query_data(qry, dbname="quant")
    df_base = pd.DataFrame(list_data, columns=["JONGMOK_NM", "YEAR_MM", "PERFORM_VAL"])

    df_jongmok_list = df_base[["JONGMOK_NM"]].drop_duplicates()
    
    for idx, row in df_jongmok_list.iterrows():
        df_jongmok = df_base[df_base.JONGMOK_NM == row.JONGMOK_NM]
        roe_mean = round(df_jongmok.PERFORM_VAL.mean(), 2)
        if roe_mean > 14.99:
            list_result.append([row.JONGMOK_NM, roe_mean])

    df_roe = pd.DataFrame(list_result, columns=["JONGMOK_NM", "ROE_MEAN"])
    return df_roe


if __name__ == "__main__":
    execute(run_qry)