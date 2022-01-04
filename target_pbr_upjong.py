"""
    종목 PBR
"""
import pandas as pd
import matplotlib.pyplot as plt
import os, sys

sys.path.append("/home/ubuntu/etlers/pysrc/pycom")
import conn_db

qry_columns = ["JONGMOK_NM", "INS_DT", "IDX_VAL", "DIV_NM"]
run_qry = """
SELECT JONGMOK_NM
     , INS_DT
     , IDX_VAL
     , DIV_NM
  FROM quant.jongmok_idx T1
 WHERE 1 = 1
   AND DIV_NM = '동일업종 PER(배)'
   AND INS_DT >= DATE_ADD(NOW(), INTERVAL -5 Day)
"""
list_result = []

def execute(qry=run_qry):
    
    list_data = conn_db.query_data(qry, dbname="quant")
    df_base = pd.DataFrame(list_data, columns=qry_columns)
    df_lupjong_pbr = df_base[df_base["INS_DT"] == df_base.INS_DT.max()][["JONGMOK_NM", "IDX_VAL"]]
    df_lupjong_pbr = df_lupjong_pbr.rename(columns = {"IDX_VAL": "UPJONG_PBR"})

    return df_lupjong_pbr


if __name__ == "__main__":
    execute(run_qry)