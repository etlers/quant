"""
    최근 3년간 15%
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
   AND INS_DT >= DATE_ADD(NOW(), INTERVAL -20 Day)
"""
base_min_val = 3.0


def execute(qry=run_qry):
    
    list_data = conn_db.query_data(qry, dbname="quant")
    df_base = pd.DataFrame(list_data, columns=qry_columns)

    df_foreign = df_base[df_base["DIV_NM"] == "외국인소진율(%)"][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]

    df_min_dt = df_foreign[df_foreign["INS_DT"] == df_foreign.INS_DT.min()]
    df_max_dt = df_foreign[df_foreign["INS_DT"] == df_foreign.INS_DT.max()]
    df_min_max_dt = pd.merge(
        df_min_dt, 
        df_max_dt, 
        how="left", 
        on="JONGMOK_NM")[["JONGMOK_NM","IDX_VAL_x","IDX_VAL_y"]]
    df_min_max_dt = df_min_max_dt.rename(columns = {"INS_DT_x": "INS_DT", "IDX_VAL_x": "MIN_VAL", "IDX_VAL_y": "MAX_VAL"})
    df_min_max_dt["GAP"] = round(df_min_max_dt["MAX_VAL"] - df_min_max_dt["MIN_VAL"], 2)
    df_min_max_dt["GAP_RT"] = round((df_min_max_dt["GAP"] / df_min_max_dt["MIN_VAL"]) * 100, 2)
    df_filtered = df_min_max_dt[(df_min_max_dt["MIN_VAL"] > base_min_val)]
    
    return df_filtered


if __name__ == "__main__":
    execute(run_qry)