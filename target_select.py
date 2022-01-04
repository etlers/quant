import pandas as pd
import target_foreign
import target_pbr_upjong
import target_pbr_jongmok
import target_roe
import target_dividend


def selected_jongmok(df_base):
    df_filetered = df_base[
        (df_base["ROE_MEAN"] > 0.0) & 
        (df_base["ROE_MEAN"] < 20.0) & 
        (df_base["GAP_RT"] > 0.0) & 
        (df_base["MAX_VAL"] < 30.0) &
        (df_base["JONGMOK_PBR"] < 1.0)
    ]

    print(df_filetered)


if __name__ == "__main__":
    df_foreign = target_foreign.execute()
    df_pbr_upjong = target_pbr_upjong.execute()
    df_pbr_jongmok = target_pbr_jongmok.execute()
    df_roe = target_roe.execute()
    df_dividend = target_dividend.execute()

    df_target = pd.merge(
        df_pbr_upjong, 
        df_pbr_jongmok, 
        how="left", 
        on="JONGMOK_NM"
    )
    df_target = pd.merge(
        df_target, 
        df_roe, 
        how="left", 
        on="JONGMOK_NM"
    )
    df_target = pd.merge(
        df_target, 
        df_foreign, 
        how="left", 
        on="JONGMOK_NM"
    )
    df_target = pd.merge(
        df_target, 
        df_dividend, 
        how="left", 
        on="JONGMOK_NM"
    )
    df_target = df_target.fillna(value=0.0)

    selected_jongmok(df_target)