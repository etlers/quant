import pandas as pd
import matplotlib.pyplot as plt

df_jongmok_idx = pd.read_csv("jongmok_idx.csv", parse_dates=True)
df_jongmok_idx = df_jongmok_idx[df_jongmok_idx["DIV_NM"] == "외국인소진율(%)"][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]

df_min_dt = df_jongmok_idx[df_jongmok_idx["INS_DT"] == df_jongmok_idx.INS_DT.min()]
df_max_dt = df_jongmok_idx[df_jongmok_idx["INS_DT"] == df_jongmok_idx.INS_DT.max()]
df_min_max_dt = pd.merge(df_min_dt, df_max_dt, how="left", on="JONGMOK_NM")[["JONGMOK_NM","IDX_VAL_x","IDX_VAL_y"]]
df_min_max_dt = df_min_max_dt.rename(columns = {"INS_DT_x": "INS_DT", "IDX_VAL_x": "MIN_VAL", "IDX_VAL_y": "MAX_VAL"})
df_min_max_dt["GAP"] = df_min_max_dt["MAX_VAL"] - df_min_max_dt["MIN_VAL"]
df_min_max_dt["GAP_RT"] = round((df_min_max_dt["GAP"] / df_min_max_dt["MIN_VAL"]) * 100, 2)
df_filtered = df_min_max_dt[(df_min_max_dt["GAP_RT"] > 5.0) & (df_min_max_dt["MAX_VAL"] < 15.0) & (df_min_max_dt["MIN_VAL"] > 3.0)]

list_matched = []

def find_rising(jongmok_nm):
    df_jongmok = df_jongmok_idx[df_jongmok_idx["JONGMOK_NM"] == jongmok_nm]
    df_jongmok = df_jongmok.sort_values("INS_DT")
    idx_val = 0.0
    for idx, row in df_jongmok.iterrows():
        if idx_val == 0.0:
            idx_val = row.IDX_VAL
            continue
        elif idx_val > row.IDX_VAL:
            return False
        idx_val = row.IDX_VAL
    
    list_matched.append(jongmok_nm)


for idx, rows in df_filtered.iterrows():
    find_rising(rows.JONGMOK_NM)
    
for nm in list_matched:
    df_plot = df_jongmok_idx[(df_jongmok_idx["JONGMOK_NM"] == nm)][["JONGMOK_NM", "INS_DT", "IDX_VAL"]]
    fig, axs = plt.subplots(figsize=(8, 4))
    df_plot.groupby(df_plot["INS_DT"])["IDX_VAL"].max().plot(
        kind="line", rot=0, ax=axs
    )
