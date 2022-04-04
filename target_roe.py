from cmath import nan
import pandas as pd
import datetime
import time
import requests
import numpy as np
import os


# 데이터 저장 폴더
root_dir = "./bs_analysis/"

start = time.time()
# 데이터 프레임에 적용할 컬럼 정의
list_columns = [
    "DT", "CD", "NM", "ROE", "PER", "PBR", "PROFIT", "INCOME", 
    "FRGN_RT", "END_PRC", "VOL", "PRC_AVG_5", "VOL_AVG_5", "PRC_AVG_10", "VOL_AVG_10", "PRC_MEDIAN", "VOL_MEDIAN", 
    "REMAIN_SELL", "REMAIN_BUY", "REMAIN_BUY_AMOUNT",
    "DAY_SUMMARY",
]
# 재무제표
list_balance = [
    "CD", "NM", "ROE", "PER", "PBR", "PROFIT", "INCOME"
]
# 일 거래 종합
list_day_summary = [
    "DT", "CD", "NM", 
    "FRGN_RT", 
    "END_PRC", "VOL", "PRC_AVG_5", "VOL_AVG_5", "PRC_AVG_10", "VOL_AVG_10", "PRC_MEDIAN", "VOL_MEDIAN", 
    "REMAIN_SELL", "REMAIN_BUY", "REMAIN_BUY_AMOUNT",
    "DAY_SUMMARY"
]


list_result = []
list_recent_data = []
list_no_data = []
dt = datetime.datetime.now().strftime("%Y-%m-%d")
base_delete_dt = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")


def convert_type(df_base, col, as_type):
    df_base[col] = df_base[col].astype(as_type)
    return df_base

# 일 집계
def get_day_summary(df_deal_summary):
    dict_deal_sumamry = {}

    for idx in [3, 4, 5, 10]:
        dict_deal_sumamry[df_deal_summary.iloc[idx][2]] = df_deal_summary.iloc[idx][3]
        if idx == 10:
            dict_deal_sumamry[df_deal_summary.iloc[idx][0]] = df_deal_summary.iloc[idx][1]

    return dict_deal_sumamry

# 매수 대기 잔액
def get_remain_buy_amount(df_remain_vol):
    # 매수 잔량 금액
    df_remain_vol = df_remain_vol.drop(columns=["Unnamed: 2"], axis=1)
    df_remain_vol = df_remain_vol.fillna(0)
    df_remain_vol["SUM_SELL"] = df_remain_vol["매도잔량"].astype(int) * df_remain_vol["매도호가"].astype(int)
    df_remain_vol["SUM_BUY"] = df_remain_vol["매수잔량"].astype(int) * df_remain_vol["매수호가"].astype(int)
    df_remain_vol.drop((df_remain_vol.index[df_remain_vol["SUM_SELL"] == 0]) & (df_remain_vol.index[df_remain_vol["SUM_BUY"] == 0]), inplace = True)
    df_remain_vol["NM"] = "SAMSUNG"
    df_grouped = df_remain_vol.groupby(["NM"]).agg({
        "SUM_SELL": "sum", "SUM_BUY": "sum",
    })
    df_grouped.columns = ["REMAIN_SELL_SUM", "REMAIN_BUY_SUM"]
    df_grouped = df_grouped.reset_index()
    df_grouped["REMAIN_GAP_BUY_AMOUNT"] = ((df_grouped["REMAIN_BUY_SUM"] - df_grouped["REMAIN_SELL_SUM"]) / 1000000).astype(int)

    return df_grouped.REMAIN_GAP_BUY_AMOUNT.values[0]

# 일 거래 종합 - 잔량
def get_remain_deal_amount(cd, nm):
    url = f"https://finance.naver.com/item/sise.naver?code={cd}"
    list_df = pd.read_html(url, encoding="euc-kr")
    # 매도대기
    remain_sell = list_df[3].iloc[0][0]
    # 매수대기
    remain_buy = list_df[3].iloc[0][2]
    # 일 집계
    dict_deal_sumamry = get_day_summary(list_df[1])
    # 매수대기 잔액
    remain_buy_amount = get_remain_buy_amount(list_df[2])

    return remain_sell, remain_buy, remain_buy_amount, dict_deal_sumamry


# 일 거래 종합 - 외국인, 종가, 거래량
def get_day_info(cd, nm):
    
    # 그룹 함수 적용
    def get_grouped(df_base):
        df_grouped = df_base.groupby(["NM"]).agg({
            "종가": "mean", "거래량": "mean",
        })
        df_grouped.columns = ["PRC_AVG", "VOL_AVG",]
        df_grouped = df_grouped.reset_index()

        return df_grouped
    
    pg = 1
    headers = {
        "referer" : f"https://finance.naver.com/item/sise_day.naver?code={cd}&page={pg}",    
        "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36" 
    }
    
    url = f"https://finance.naver.com/item/sise_day.naver?code={cd}&page={pg}"
    res = requests.get(url=url, headers=headers)      
    # Pandas : read_html() > table element 추출 가능
    df_data = pd.read_html(res.text)[0].dropna().set_index("날짜").reset_index()
    # 전일비에 부호 지정
    df_data['전일비'] = df_data.종가.diff(-1).fillna(0).astype(int)
    end_prc = int(df_data.iloc[0][1])
    vol = df_data.iloc[0][6]
    df_data["NM"] = nm
    # 5일평균, 10일 평균, 중위값,
    # prc_avg_5, prc_avg_10, vol_avg_5, vol_avg_10, prc_median, vol_median
    # 5일 평균
    df_grouped = get_grouped(df_data.head(5))
    prc_avg_5 = float(str(df_grouped["PRC_AVG"].iloc[0]))
    vol_avg_5 = float(str(df_grouped["VOL_AVG"].iloc[0]))
    # 10일 평균
    df_grouped = get_grouped(df_data)
    prc_avg_10 = float(str(df_grouped["PRC_AVG"].iloc[0]))
    vol_avg_10 = float(str(df_grouped["VOL_AVG"].iloc[0]))
    # 중앙 값
    prc_median = np.median(list(df_data["종가"]))
    vol_median = np.median(list(df_data["거래량"]))
    # 최근 10일 거래 데이터
    for col in df_data.columns:
        if (col == "NM") or (col == "날짜"): continue
        df_data = convert_type(df_data, col, as_type=int)
        
    list_row = df_data.values.tolist()
    for idx in range(len(list_row)):
        list_recent_data.append(list_row[idx])
    return end_prc, vol, prc_avg_5, vol_avg_5, prc_avg_10, vol_avg_10, prc_median, vol_median


# ROE 값이 기준값 이상인 것만 고른다
def get_roe_more_than_base(cd, nm):
    roe_base = 15.0
    url = f"https://finance.naver.com/item/main.naver?code={cd}"
    
    list_roe = []
    list_per = []
    list_pbr = []
    list_profit = []
    list_income = []
    
    try:
        list_df = pd.read_html(url, encoding="euc-kr")
        df_bs_sheet = list_df[3]
        df_bs_sheet = df_bs_sheet.fillna(0)
        
        roe = 0.0
        
        if ".03" in str(df_bs_sheet["최근 연간 실적"].loc[0]).split(" ")[0]:
            roe = float(df_bs_sheet.fillna(0).iloc[5].loc["최근 연간 실적", "2021.03"][0])
            list_ym = ["2019.03","2020.03","2021.03"]
        elif ".06" in str(df_bs_sheet["최근 연간 실적"].loc[0]).split(" ")[0]:
            roe = float(df_bs_sheet.fillna(0).iloc[5].loc["최근 연간 실적", "2021.06"][0])
            list_ym = ["2019.06","2020.06","2021.06"]
        elif ".09" in str(df_bs_sheet["최근 연간 실적"].loc[0]).split(" ")[0]:
            roe = float(df_bs_sheet.fillna(0).iloc[5].loc["최근 연간 실적", "2021.09"][0])
            list_ym = ["2019.09","2020.09","2021.09"]
        else:
            try:
                roe = float(df_bs_sheet.fillna(0).iloc[5].loc["최근 연간 실적", "2021.12(E)"][0])
                list_ym = ["2018.12","2019.12","2020.12","2021.12(E)"]
            except:
                roe = float(df_bs_sheet.fillna(0).iloc[5].loc["최근 연간 실적", "2021.12"][0])
                list_ym = ["2019.12","2020.12","2021.12"]
    
        if roe >= roe_base:
            # 일 거래 종합
            end_prc, vol, prc_avg_5, vol_avg_5, prc_avg_10, vol_avg_10, prc_median, vol_median = get_day_info(cd, nm)
            # df_recent_data = pd.concat(df_recent_data, df_data)
            # 일 거래 종합 - 잔량
            remain_sell, remain_buy, remain_buy_amount, dict_deal_sumamry = get_remain_deal_amount(cd, nm)
            # 거래량
            list_deal_vol = list_df[0][2][0].split(" ")
            deal_volume = list_deal_vol[len(list_deal_vol)-1].replace(",","")
            # 외국인
            frgn_rt = float(list_df[6][1].iloc[2].replace("%", ""))
            # 데이터 생성
            for ym in list_ym:
                try:
                    list_roe.append(float(df_bs_sheet.iloc[5].loc["최근 연간 실적", ym][0]))
                    list_per.append(float(df_bs_sheet.iloc[10].loc["최근 연간 실적", ym][0]))
                    list_pbr.append(float(df_bs_sheet.iloc[12].loc["최근 연간 실적", ym][0]))
                    if type(df_bs_sheet.iloc[1].loc["최근 연간 실적", ym][0]) is str:
                        list_profit.append(int(df_bs_sheet.iloc[1].loc["최근 연간 실적", ym][0].replace(",", "")))
                    else:
                        list_profit.append(int(df_bs_sheet.iloc[1].loc["최근 연간 실적", ym][0]))
                    if type(df_bs_sheet.iloc[2].loc["최근 연간 실적", ym][0]) is str:
                        list_income.append(int(df_bs_sheet.iloc[2].loc["최근 연간 실적", ym][0].replace(",", "")))
                    else:
                        list_income.append(int(df_bs_sheet.iloc[2].loc["최근 연간 실적", ym][0]))
                except:
                    pass
            
            list_result.append([dt, "A" + cd, nm, 
                                list_roe, list_per, list_pbr, list_profit, list_income, 
                                frgn_rt, int(end_prc), int(vol), int(prc_avg_5), int(vol_avg_5), int(prc_avg_10), int(vol_avg_10), int(prc_median), int(vol_median), 
                                int(remain_sell), int(remain_buy), int(remain_buy_amount),
                                str(dict_deal_sumamry)
                               ])
    except Exception as e:
        list_no_data.append([cd, nm, e])

def execute():
    # get_roe_more_than_base("298540", "더네이쳐홀딩스")
    # get_roe_more_than_base("000215", "DL우")
    df_jongmok = pd.read_csv("./csv/stock_list.csv", encoding="utf-8-sig")[["단축코드", "한글 종목약명"]]
    df_jongmok = df_jongmok.rename(columns={"단축코드":"CD", "한글 종목약명":"NM"})
    for index, row in df_jongmok.iterrows():
        get_roe_more_than_base(str(row.CD), row.NM)

    # Today's dataframe
    df_now = pd.DataFrame(data=list_result, columns=list_columns)
    df_now[list_balance].to_csv(f"{root_dir}balance_sheet.csv", encoding="utf-8-sig", index=False)
    # 파일 존재여부 확인 후 없으면 저장하고 종료.
    day_summary_csv_file = f"{root_dir}day_summary.csv"
    day_summary_backup = f"{root_dir}backup/day_summary{dt.replace('-','')}.csv"
    if os.path.exists(day_summary_csv_file) == False:
        df_now[list_day_summary].to_csv(day_summary_csv_file, encoding="utf-8-sig", index=False)
    # 존재하면 붙여주고 종료
    else:
        df_pre = pd.read_csv(day_summary_csv_file, encoding="utf-8-sig")
        # backup summary file
        df_pre.to_csv(day_summary_backup, encoding="utf-8-sig", index=False)
        # Day Summary Possesion
        df_result = pd.concat([df_now[list_day_summary], df_pre]).drop_duplicates()
        # 기준일자(10일) 이전 데이터 삭제
        df_result.drop(df_result.index[df_result["DT"] < base_delete_dt], inplace = True)
        # Save result dataframe to csv file 
        df_result.to_csv(day_summary_csv_file, encoding="utf-8-sig", index=False)
        
    print("#" * 100)
    # 오류 데이터
    df_no_data = pd.DataFrame(data=list_no_data, columns=["CD", "NM", "MESSAGE"])
    df_no_data.to_csv(f"{root_dir}no_data.csv", encoding="utf-8-sig", index=False)
    # 최근 10일 데이터
    list_recent_columns=["날짜","종가","전일비","시가","고가","저가","거래량","NM"]
    df_recent_data = pd.DataFrame(data=list_recent_data, columns=list_recent_columns)
    df_recent_data.to_csv(f"{root_dir}recent_deal.csv", encoding="utf-8-sig", index=False)


if __name__ == "__main__":
    # 로직 수행
    execute()
    # 결과
    print(len(list_result), " 건")
    # 소요시간
    end = time.time()
    print(f"Elapsed Seconds: {end - start}")