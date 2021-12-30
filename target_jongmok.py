import pandas as pd
import matplotlib.pyplot as plt
import os, sys

sys.path.append("/home/ubuntu/etlers/pysrc/pycom")
import conn_db


forgn_qry = """
SELECT JONGMOK_NM
     , INS_DT
     , IDX_VAL
     , DIV_NM
  FROM quant.jongmok_idx T1
 INNER JOIN quant.holiday T2
    ON T2.DT = T1.INS_DT
   AND T2.HOLI_YN = 'N'
 WHERE 1 = 1
   AND INS_DT >= DATE_ADD(NOW(), INTERVAL -10 Day)
"""

perform_qry = """
SELECT JONGMOK_NM
     , DIV_NM
     , PERFORM_VAL 
     , YEAR_MM 
     , IDX
     , YEAR_DIV
  FROM quant.jongmok_perform
 WHERE 1 = 1
   AND PERFORM_VAL != 0
"""

list_matched = []

def increasing_jongmok(df_foreign, df_filtered, df_perform, df_upjong_pbr):

    def check_perform_val(jongmok_nm):
        df_jongmok_roe = df_perform[(df_perform["JONGMOK_NM"] == jongmok_nm) & (df_perform["DIV_NM"] == "ROE(지배주주)") & (df_perform["YEAR_DIV"] == "분기")]
        df_jongmok_roe = df_jongmok_roe.sort_values("YEAR_MM")
        if len(df_jongmok_roe) < 4:
            return -999, -999
        
        for idx, row in df_jongmok_roe.iterrows():
            if (row.PERFORM_VAL < 15.0) or (row.PERFORM_VAL > 25.0):
                return -999, -999
        
        roe_mean = round(df_jongmok_roe.PERFORM_VAL.mean(), 2)
        
        df_jongmok_pbr = df_perform[(df_perform["JONGMOK_NM"] == jongmok_nm) & (df_perform["DIV_NM"] == "PBR(배)")]
        try:
            pbr_recent = df_jongmok_pbr.at[df_jongmok_pbr.index[-1], "PERFORM_VAL"]
        except:
            pbr_recent = -999
        
        return roe_mean, pbr_recent

    def find_rising(jongmok_nm, roe_mean, pbr_recent):
        df_jongmok = df_foreign[df_foreign["JONGMOK_NM"] == jongmok_nm]
        df_jongmok = df_jongmok.sort_values("INS_DT")
        idx_val = 0.0
        for idx, row in df_jongmok.iterrows():
            if idx_val == 0.0:
                idx_val = row.IDX_VAL
                continue
            elif idx_val > row.IDX_VAL:
                return False
            idx_val = row.IDX_VAL

        df_jongmok_pbr = df_upjong_pbr[(df_upjong_pbr["JONGMOK_NM"] == jongmok_nm)]
        df_jongmok_pbr = df_jongmok_pbr[(df_jongmok_pbr["INS_DT"] == df_jongmok_pbr.INS_DT.min())]
        try:
            pbr_compare = df_jongmok_pbr.at[df_jongmok_pbr.index[-1], 'IDX_VAL']
        except:
            pbr_compare = -999
        
        if roe_mean < 1.0:
            list_matched.append(f"* {jongmok_nm} : [{idx_val}%] [{roe_mean}] [{pbr_recent} VS {pbr_compare}]")
        else:
            list_matched.append(f"{jongmok_nm} : [{idx_val}%] [{roe_mean}] [{pbr_recent} VS {pbr_compare}]")


    for idx, rows in df_filtered.iterrows():
        result_roe, result_pbr = check_perform_val(rows.JONGMOK_NM)
        if result_roe == -999:
            continue

        find_rising(rows.JONGMOK_NM, result_roe, result_pbr)
        
    for nm in list_matched:
        print(nm)
        df_plot = df_foreign[(df_foreign["JONGMOK_NM"] == nm)][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]
        fig, axs = plt.subplots(figsize=(8, 4))
        df_plot.groupby(df_plot["INS_DT"])["IDX_VAL"].max().plot(
            kind="line", rot=0, ax=axs
        )

def execute(df_jongmok_idx, df_perform):
    # df_jongmok_idx = pd.read_csv("jongmok_idx.csv", parse_dates=True)
    df_upjong_pbr = df_jongmok_idx[df_jongmok_idx["DIV_NM"] == "동일업종 PER(배)"][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]
    df_foreign = df_jongmok_idx[df_jongmok_idx["DIV_NM"] == "외국인소진율(%)"][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]

    df_min_dt = df_foreign[df_foreign["INS_DT"] == df_foreign.INS_DT.min()]
    df_max_dt = df_foreign[df_foreign["INS_DT"] == df_foreign.INS_DT.max()]
    df_min_max_dt = pd.merge(
        df_min_dt, 
        df_max_dt, 
        how="left", 
        on="JONGMOK_NM")[["JONGMOK_NM","IDX_VAL_x","IDX_VAL_y"]]
    df_min_max_dt = df_min_max_dt.rename(columns = {"INS_DT_x": "INS_DT", "IDX_VAL_x": "MIN_VAL", "IDX_VAL_y": "MAX_VAL"})
    df_min_max_dt["GAP"] = df_min_max_dt["MAX_VAL"] - df_min_max_dt["MIN_VAL"]
    df_min_max_dt["GAP_RT"] = round((df_min_max_dt["GAP"] / df_min_max_dt["MIN_VAL"]) * 100, 2)
    df_filtered = df_min_max_dt[(df_min_max_dt["GAP_RT"] > 5.0) & (df_min_max_dt["MAX_VAL"] < 15.0) & (df_min_max_dt["MIN_VAL"] > 3.0)]
    
    increasing_jongmok(df_foreign, df_filtered, df_perform, df_upjong_pbr)

if __name__ == "__main__":
    list_data = conn_db.query_data(forgn_qry, dbname="quant")
    df_base = pd.DataFrame(list_data, columns=["JONGMOK_NM", "INS_DT", "IDX_VAL", "DIV_NM"])
    list_data = conn_db.query_data(perform_qry, dbname="quant")
    df_perform = pd.DataFrame(list_data, columns=["JONGMOK_NM", "DIV_NM", "PERFORM_VAL", "YEAR_MM", "IDX", "YEAR_DIV"])

    execute(df_base, df_perform)