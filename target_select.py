import argparse
from cmath import nan
import pandas as pd
import numpy as np
import statistics
import requests
import datetime


# 데이터 저장 폴더
root_dir = "./bs_analysis/"

list_ordered_key = ["CD", "DT"]
list_using_columns = [
    "NM", "FRGN_RT", "END_PRC", "VOL", "REMAIN_BUY", "REMAIN_SELL", "REMAIN_BUY_AMOUNT",
    "PRC_AVG_5", "VOL_AVG_5", "PRC_AVG_10", "VOL_AVG_10", "PRC_MEDIAN", "VOL_MEDIAN", "DAY_SUMMARY"
]
list_columns = [
    "CD", "NM",
    "LAST_FRGN_RT", "LAST_END_PRC", "PRC_MEDIAN", "LAST_PRC_AVG_5", "LAST_PRC_AVG_10",
    "LAST_VOL", "VOL_MEDIAN",
    "ROE", "ROE_AVG", "PER", "PBR", "PROFIT",
    "FRGN_RT", "END_PRC", "VOL", "REMAIN_DEAL"
]
dict_rename_cols = {
    "CD": "코드",
    "NM": "종목",
    "LAST_FRGN_RT": "최근 외국인 지분율",
    "LAST_END_PRC": "최근 종가", 
    "PRC_MEDIAN": "최근10일 종가 중간값", 
    "LAST_PRC_AVG_5": "최근5일 종가 평균", 
    "LAST_PRC_AVG_10": "최근10일 종가 평균",
    "LAST_VOL": "마지막 거래량", 
    "VOL_MEDIAN": "최근10일 거래량 중간값",
    "ROE": "자기자본이익률(ROE)", 
    "ROE_AVG": "ROE 평균", 
    "PER": "주가수익비율", 
    "PBR": "주가순자산비율", 
    "PROFIT": "영업이익",
    "FRGN_RT": "외국인지분율", 
    "END_PRC": "종가", 
    "VOL": "거래량", 
    "REMAIN_DEAL": "매수잔액",
}
# 작업일자
dt = datetime.datetime.now().strftime("%Y-%m-%d")

# 일 집계 데이터 추출
df_calc_base = pd.read_csv(f"{root_dir}day_summary.csv", encoding="utf-8-sig")[list_ordered_key + list_using_columns]
# 살려는 양이 더 많은지 확인을 위해
df_calc_base.fillna(value=0, inplace=True)
# df_calc_base["REMAIN_GAP_BUY"] = df_calc_base["REMAIN_BUY"] - df_calc_base["REMAIN_SELL"]
df_calc_base["REMAIN_DEAL"] = df_calc_base["REMAIN_BUY_AMOUNT"]
df_calc_base = df_calc_base.sort_values(list_ordered_key)


def send_message_to_slack(msg):
    msg = msg.replace('"', "'").replace("/","")
    url = "https://hooks.slack.com/services/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"
    payload = { "text" : msg } 
    response = requests.post(url, json=payload)
    print(response)
    

# 리스트의 평균 추출
def get_avg_in_list(col, last_value=False):
    try:
        list_val = eval(col)
    except:
        list_val = col

    # 리스트의 마지막 값 추출
    if last_value:
        return list_val[-1]
    else:
        return round(statistics.mean(list_val), 2)


# 값 증가 여부 추가
def check_rising_list_val(col):
    try:
        list_val = eval(col)
    except:
        list_val = col
    
    if len(list_val) < 2:
        return "N"
    
    pre_val = 0
    for val in list_val:
        if pre_val == 0:
            pre_val = val
            continue
        elif val < pre_val:
            return "N"
        
        pre_val = val
            
    return "Y"

# 추세 딕셔너리 생성
def make_rising_dict(df_base, base_day):
    # 추세 데이터 추출 시에 사용할 컬럼 인덱스 딕셔너리
    dict_col_index = {}
    # 추세 데이터 리스트
    list_cols = []
    # 추세에서 제외할 컬럼 정의
    list_no_target_columns = ["CD", "NM", "DT", "DAY_SUMMARY"]
    # 추세 대상이 되는 컬럼
    idx = 0
    for col in df_base.columns:
        if col in list_no_target_columns: continue
        list_cols.append(col)
        dict_col_index[col] = idx
        idx += 1
    # 종목
    list_nm = df_base["NM"].unique()
    # 추세 딕셔너리
    dict_rising = {}
    # 딕셔너리 데이터 생성
    for nm in list_nm:
        list_dict = []
        for col in list_cols:
            dict_col_list_val = {}
            list_val = list(df_base[df_base["NM"] == nm][["NM", col]].head(base_day).T.reset_index().loc[1])[1:]
            dict_col_list_val[col] = list_val
            list_dict.append(dict_col_list_val)
        dict_rising[nm] = list_dict
    
    return dict_rising, dict_col_index


# 처음 마지막 값
def make_first_last_value(df_base, col):
    df_first_last = df_base.groupby(["NM"]).agg(
        FIRST_VAL=(col, "first"), 
        LAST_VAL=(col, "last")).reset_index()

    df_first_last["GAP"] = df_first_last["LAST_VAL"] - df_first_last["FIRST_VAL"]
    df_first_last["GAP_RT"] = round((df_first_last["GAP"] / df_first_last["FIRST_VAL"]) * 100, 2)
    
    df_first_last = df_first_last.rename(
        columns={"FIRST_VAL": f"FIRST_{col}", "LAST_VAL": f"LAST_{col}"}
    )

    return df_first_last.sort_values(by=["GAP_RT"], ascending=False).fillna(0.0)

# 외국인 보유비율
def get_frgn_rt_df():
    col = "FRGN_RT"
    # 정렬
    df_frgn_rt = df_calc_base.sort_values(by=list_ordered_key)
    # 최초 마지막 값 구성
    df_frgn_rt_calc = make_first_last_value(df_frgn_rt, col)

    return df_frgn_rt_calc

# 종가 데이터
def get_end_prc_df():
    # 종가
    col = "END_PRC"
    # 정렬
    df_end_prc = df_calc_base.sort_values(by=list_ordered_key)
    # 최초 마지막 값 구성
    df_end_prc_calc = make_first_last_value(df_end_prc, col)

    # 최근 5일 종가 평균
    df_end_prc_avg = make_first_last_value(df_end_prc, "PRC_AVG_5")[["NM", "LAST_PRC_AVG_5"]]
    df_end_prc_calc = pd.merge(df_end_prc_calc, df_end_prc_avg, how="inner", on=["NM"])
    # 최근 10일 종가 평균
    df_end_prc_avg = make_first_last_value(df_end_prc, "PRC_AVG_10")[["NM", "LAST_PRC_AVG_10"]]
    df_end_prc_calc = pd.merge(df_end_prc_calc, df_end_prc_avg, how="inner", on=["NM"])

    return df_end_prc_calc

# 거래량 데이터
def get_deal_vol_df():
    # 거래량
    col = "VOL"
    # 정렬
    df_deal_vol = df_calc_base.sort_values(by=list_ordered_key)
    # 최초 마지막 값 구성
    df_deal_vol_calc = make_first_last_value(df_deal_vol, col)

    return df_deal_vol_calc

# 잔량 데이터
def get_remain_buy_df():
    # 거래 잔량
    col = "REMAIN_DEAL"
    # 정렬
    df_remain_gap_buy = df_calc_base.sort_values(by=list_ordered_key)
    # 최초 마지막 값 구성
    df_remain_gap_buy_calc = make_first_last_value(df_remain_gap_buy, col)

    return df_remain_gap_buy_calc

# 재무제표 데이터
def get_balance_sheet_df(df_day_summary):

    # 종가 위치(비율) 추출
    def get_end_prc_position(df_base):
        
        # 금액 딕셔너리 분리
        def split_prc_from_dict_summary(dict_base_prc):
            list_prc = []
            if type(dict_base_prc) == str:
                dict_base_prc = eval(dict_base_prc)
            
            for val in dict_base_prc.values():
                list_prc.append(val)

            return list_prc
        
        # 리스트로 받아서 시리즈로 변경 처리
        list_prc = df_base["DAY_SUMMARY"].apply(lambda X: split_prc_from_dict_summary(X)).to_list()[0]

        dict_cols = {}
        dict_cols["START_PRC"] = int(list_prc[0])
        dict_cols["HIGH_PRC"] = int(list_prc[1])
        dict_cols["HIGHEST_PRC"] = int(list_prc[2])
        dict_cols["LOW_PRC"] = int(list_prc[3])
        dict_cols["LOWEST_PRC"] = int(list_prc[4])

        return pd.Series(dict_cols, index=["START_PRC", "HIGH_PRC", "HIGHEST_PRC", "LOW_PRC", "LOWEST_PRC"])

    # 금액 대비 종가의 비율
    def insert_end_price_rate(df_base):
        # 가장 최근 종가 위치 추출. vs_start_prc, vs_high_prc, vs_highest_prc, vs_low_prc, vs_lowest_prc
        df_recent_prc_position = df_base[df_base["DT"] == df_base["DT"].max()]
        df_recent_prc_position = df_recent_prc_position.groupby(["CD"]).agg(
            END_PRC=("END_PRC", "first"),
            DAY_SUMMARY=("DAY_SUMMARY", "first")).reset_index()
        df_recent_prc_position = df_recent_prc_position.groupby(["CD", "END_PRC"]).apply(get_end_prc_position)
        df_recent_prc_position = df_recent_prc_position.reset_index()
        # 금액 적용 
        df_recent_prc_position["VS_START_PRC"] = round((df_recent_prc_position["START_PRC"] / df_recent_prc_position["END_PRC"]) * 100, 2)
        df_recent_prc_position["VS_HIGH_PRC"] = round((df_recent_prc_position["HIGH_PRC"] / df_recent_prc_position["END_PRC"]) * 100, 2)
        df_recent_prc_position["VS_HIGHEST_PRC"] = round((df_recent_prc_position["HIGHEST_PRC"] / df_recent_prc_position["END_PRC"]) * 100, 2)
        df_recent_prc_position["VS_LOW_PRC"] = round((df_recent_prc_position["LOW_PRC"] / df_recent_prc_position["END_PRC"]) * 100, 2)
        df_recent_prc_position["VS_LOWEST_PRC"] = round((df_recent_prc_position["LOWEST_PRC"] / df_recent_prc_position["END_PRC"]) * 100, 2)
        # 최종 계산 데이터
        return df_recent_prc_position

    # 추세 딕셔너리 생성
    dict_rising, dict_col_index = make_rising_dict(df_day_summary, 5)
    # 각종 집계한 데이터와 딕셔너리 호출
    df_frgn_rt_calc = get_frgn_rt_df()
    df_end_prc_calc = get_end_prc_df()
    df_deal_vol_calc = get_deal_vol_df()
    df_remain_gap_buy_calc = get_remain_buy_df()
    # 재무제표 선정 종목
    df_balance = pd.read_csv(f"{root_dir}balance_sheet.csv", encoding="utf-8-sig")
    # 추세 데이터 추가
    for col, idx in dict_col_index.items():
        df_balance[col] = df_balance["NM"].apply(lambda X: dict_rising[X][idx][col])
    # 이하 필터링 이전 데이터 옆으로 붙이기. 새로운 값 사용을 위해 기존 값 뒤에 "x" 추가. suffixes = ('_x', ''),
    # 가장 최근 중간 값 추출
    df_recent_median = df_day_summary.groupby(["CD"]).agg(
        PRC_MEDIAN=("PRC_MEDIAN", "first"), 
        VOL_MEDIAN=("VOL_MEDIAN", "first")).reset_index()
    # 중간 값
    df_balance = pd.merge(
        df_balance, 
        df_recent_median[["CD", "PRC_MEDIAN", "VOL_MEDIAN"]], 
        how="inner", 
        suffixes = ('_x', ''),
        on=["CD"])
    # 마지막 외국인 지분율
    df_balance = pd.merge(
        df_balance,
        df_frgn_rt_calc[["NM", "LAST_FRGN_RT"]],
        how="inner", 
        suffixes = ('_x', ''),
        on=["NM"])
    # 종가
    df_balance = pd.merge(
        df_balance,
        df_end_prc_calc[["NM", "LAST_END_PRC", "LAST_PRC_AVG_5", "LAST_PRC_AVG_10"]],
        how="inner", 
        suffixes = ('_x', ''),
        on=["NM"])
    # 종가 비율 계산 컬럼
    df_recent_prc_position = insert_end_price_rate(df_day_summary)
    # 종가 위치
    df_balance = pd.merge(
        df_balance, 
        df_recent_prc_position[["CD", "VS_START_PRC", "VS_HIGH_PRC", "VS_HIGHEST_PRC", "VS_LOW_PRC", "VS_LOWEST_PRC"]], 
        how="inner", 
        suffixes = ('_x', ''),
        on=["CD"])
    # 거래량
    df_balance = pd.merge(
        df_balance,
        df_deal_vol_calc[["NM", "LAST_VOL"]],
        how="inner", 
        suffixes = ('_x', ''),
        on=["NM"])
    # 거랭 잔량
    df_balance = pd.merge(
        df_balance,
        df_remain_gap_buy_calc[["NM", "LAST_REMAIN_DEAL"]],
        how="inner", 
        suffixes = ('_x', ''),
        on=["NM"])

    return df_balance


def execute():
    # 최종 정제한 데이터
    df_balance = get_balance_sheet_df(df_calc_base)
    # 계속 증가하는지 여부
    # ROE가 증가하는지
    df_balance["RISING_ROE"] = df_balance["ROE"].apply(lambda X: check_rising_list_val(X))
    # ROE 평균
    df_balance["ROE_AVG"] = df_balance["ROE"].apply(lambda X: get_avg_in_list(X))
    # 영업이익이 증가하는지
    df_balance["RISING_PROFIT"] = df_balance["PROFIT"].apply(lambda X: check_rising_list_val(X))
    # 외국인 지분율이 증가하는지
    df_balance["RISING_FRGN_RT"] = df_balance["FRGN_RT"].apply(lambda X: check_rising_list_val(X))
    # 매수 잔량이 증가하는지
    df_balance["RISING_REMAIN_DEAL"] = df_balance["REMAIN_DEAL"].apply(lambda X: check_rising_list_val(X))
    # 종가가 기준(평균? 중간 값?) 이하인지
    df_balance["PRC_BASE"] = np.where(df_balance["LAST_END_PRC"] < df_balance["PRC_MEDIAN"], "Y", "N")
    # 거래량이 중간 값 이상인지
    df_balance["VOL_BASE"] = np.where(df_balance["LAST_VOL"] > df_balance["VOL_MEDIAN"], "Y", "N")
    # 매수 대기가 많은지
    df_balance["REMAIN_GAP_BUY_BASE"] = np.where(df_balance["LAST_REMAIN_DEAL"] > 0, "Y", "N")
    # 전체 조건 적용 이전 데이터
    df_balance.to_csv(f"{root_dir}target/pre_targeting_{dt.replace('-','')}.csv", encoding="utf-8-sig", index=-False)
    # 최종 선택 종목
    df_selected = df_balance[
        # 덜 중요한 순서
        # (df_balance["RISING_REMAIN_DEAL"] == "Y") &
        # (df_balance["VOL_BASE"] == "Y") &
        # 종가가 중간 값 아래인 경우
        # (df_balance["PRC_BASE"] == "Y") &
        # 이하 필수
        # 외국인 지분율이 떨어지지 않은 경우
        (df_balance["RISING_FRGN_RT"] == "Y") &
        # 매수 대기가 존재하는 경우
        (df_balance["REMAIN_GAP_BUY_BASE"] == "Y") &
        # 매수 잔량이 존재하고 ROE는 계속 증가, 15 이상이고 영업이익도 계속 증가하는 종목
        (df_balance["LAST_FRGN_RT"] > 4.99) &
        (df_balance["RISING_ROE"] == "Y") & 
        (df_balance["ROE_AVG"] > 14.99) & 
        (df_balance["RISING_PROFIT"] == "Y")
    ]
    # ROE 평균이 큰 순서로 정렬
    df_selected = df_selected[list_columns].sort_values(by=["ROE_AVG"], ascending=False).rename(columns=dict_rename_cols)
    df_selected.to_csv(f"{root_dir}target/selected_target_{dt.replace('-','')}.csv", encoding="utf-8-sig", index=-False)
    
    return df_selected


if __name__ == "__main__":

    # Change showing type of trend list
    def remake_flow_view(list_val):
        result = ""
        for val in list_val:
            result += format(val, ",") + " > "
            
        return result[:len(result)-3].strip()

    # Up & down average of list value
    def remake_up_down_rate(list_val):
        list_down_rt = []
        list_up_rt = []
        
        for idx in range(len(list_val)-1):
            pre_prc = list_val[idx]
            next_prc = list_val[idx+1]
            if next_prc > pre_prc:
                list_up_rt.append((next_prc-pre_prc) / pre_prc)
            else:
                list_down_rt.append((next_prc-pre_prc) / pre_prc)
                
        if len(list_up_rt) == 0:
            up_rt = 0.00
        else:
            up_rt = round(np.average(list_up_rt) * 100, 2)
        if len(list_down_rt) == 0:
            down_rt = 0.00
        else:
            down_rt = round(np.average(list_down_rt) * 100, 2)

        return up_rt, down_rt

    # Define main parameter
    parser = argparse.ArgumentParser()
    parser.add_argument('--slack', default = 'N')
    # Setting input parameter
    args = parser.parse_args()
    # Run selecting target logic
    df_selected = execute()
    # Has no result
    if df_selected.empty:
        print(f"{dt}. 조건에 맞는 대상 데이터 없음")
    else:
        df_selected["매수대기"] = df_selected["매수잔액"].apply(lambda X: get_avg_in_list(X, last_value=True))
        df_result = df_selected[["코드", "종목", "최근 외국인 지분율", "최근 종가", "종가", "최근10일 종가 중간값", "마지막 거래량", "최근10일 거래량 중간값", "ROE 평균", "매수대기"]]
        # 결과
        result_head  =  "###############################" + "\n"
        result_head += f"# 데이터 추출일자: {dt} #" + "\n"
        result_head +=  "###############################" + "\n"
        result_body = ""
        rcnt = 0
        for idx, row in df_result.iterrows():
            pass_tf = False
            end_prc = int(row["최근 종가"])
            mid_prc = int(row["최근10일 종가 중간값"])
            prc_rt = round((end_prc / mid_prc) * 100, 1)
            end_vol = int(row["마지막 거래량"])
            mid_vol = int(row["최근10일 거래량 중간값"])
            vol_rt = round((end_vol / mid_vol) * 100, 1)
            remain_qty = int(row["매수대기"] * 1000000 / end_prc)
            remain_rt = round((remain_qty / end_vol) * 100, 1)
            # 종가 110% 이하인 경우. 90% 이상인 경우 단, 종가가 100% 아래이면 대상으로 선정. 잔액 -5% 이상인 경우
            if prc_rt > 110.0:
                pass_tf = True
            elif vol_rt < 90.0:
                pass_tf = True
                if prc_rt < 100.0:
                    pass_tf = False
            elif remain_rt < -5.0:
                pass_tf = True
            # 대상 제외
            if pass_tf == True: continue
            # 추출 개 저장
            rcnt += 1
            # 대상 출력
            up_rt, down_rt = remake_up_down_rate(row["종가"])
            print_val =  f'# {row["종목"]} [{row["코드"].replace("A","")}]\n'
            print_val += f' - ROE 평균: {row["ROE 평균"]}%\n'
            print_val += f' - 외국인 지분율: {row["최근 외국인 지분율"]}%\n'
            print_val += f' - 종가[최근10일 중간값]: {format(end_prc, ",")} [{format(mid_prc, ",")}. {prc_rt}%]\n'
            print_val += f' - 종가 추세: {remake_flow_view(row["종가"])}\n'
            print_val += f' - 종가 평균 {up_rt}% 상승 {down_rt}% 하락\n'
            print_val += f' - 거래량[최근10일 중간값]: {format(end_vol, ",")} [{format(mid_vol, ",")}. {vol_rt}%]\n'
            print_val += f' - 매수대기 잔액: {format(int(row["매수대기"]), ",")} (백만원) [{format(remain_qty, ",")} 주]\n'
            print_val += f' - 거래량 대비 매수대기 잔액 비율: {remain_rt}%\n'
            result_body += print_val
        # Check sending message through slack 슬랙 메세지 전송을 선택했으면 전송
        if rcnt == 0:
            result_body = "# 조건에 맞는 대상 데이터 없음"
        result_msg = result_head + result_body
        if args.slack.upper() == "Y":
            send_message_to_slack(result_msg)
        # Show the result on screen
        print(result_msg)