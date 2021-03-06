import sys
import time, datetime
from numpy.core.numeric import NaN
import pandas as pd
from pandas.io import html

sys.path.append("../pycom")
import crawl_soup
import date_util
import conn_db

import requests
from bs4 import BeautifulSoup as bs
import html5lib

now_dtm = date_util.get_now_datetime_string()

dict_accnt_ym = {}

list_skip_row = [
    '</th>', '<th>', '</td>', '<td>', '</tr>', '<tr>', '<td class="">', '</dl>', '<dl>', '</li>', '</ul>', '<ul>', '</div>', '</em>',
    '<td class="t_line cell_strong">', '<td class="last cell_strong">', '<tr class="line_end">'
]


def company_performance(soup, class_id, jongmok_cd, jongmok_nm):
    result_jongmok_perform = soup.find("div",{"class":class_id})

    list_result = str(result_jongmok_perform).split("\n")

    idx = 0
    next_idx = 0
    header_cnt = 0
    list_item = []
    list_item_result = []
    item_start_tf = False
    for row in list_result:
        row_strip = row.strip()
        if len(row_strip) == 0 or row_strip in list_skip_row : continue

        if "no_data" in row_strip or "null" in row_strip or '<em class="f_up">' == row_strip:
            row_strip = 0

        idx += 1        
        if row_strip == '<th class="" scope="col">' or row_strip == '<th class="last cell_strong" scope="col">' or row_strip == '<th class="t_line cell_strong" scope="col">':
            next_idx = idx + 1
            header_cnt += 1
        if "h_th2 th_cop_anal" in str(row_strip) and 'scope="row' in str(row_strip):
            if len(list_item) > 0:
                list_item_result.append(list_item)
            list_item = []
            item_start_tf = True
            row_strip = row_strip.split("<strong>")[1].split("</strong>")[0]
        
        if item_start_tf:
            list_item.append(row_strip)

        if idx == next_idx:
            dict_accnt_ym[header_cnt] = row_strip.replace('<em>(E)</em>','')

    quarter_idx = 0
    pre_ym = ""
    for key, val in dict_accnt_ym.items():
        if pre_ym == "":
            pre_ym = val
            continue
        if pre_ym > val:
            quarter_idx = key
            break
        pre_ym = val

    for items in list_item_result:        
        for key, val in dict_accnt_ym.items():
            try:
                perform_val = float(str(items[key]).replace(",",""))
            except:
                perform_val = 0
            year_div = "??????" if key >= quarter_idx else "??????"
            ACCNT_QRY = f"""
                INSERT INTO quant.jongmok_perform
                     (JONGMOK_CD, DIV_NM, IDX, YEAR_MM, YEAR_DIV, PERFORM_VAL, JONGMOK_NM, MOD_DTM)
                VALUES
                     ('{jongmok_cd}', '{items[0]}', {key}, '{val}', '{year_div}', {perform_val}, '{jongmok_nm}', NOW())
            """
            try:
                conn_db.transaction_data(ACCNT_QRY, db='quant')
            except:
                print(ACCNT_QRY)


def execute(jongmok_cd, jongmok_nm):
    url_jongmok = f"https://finance.naver.com/item/coinfo.naver?code={jongmok_cd}"

    url = 'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=005930'
    # url = url_tmpl % ('005930', '4', 'Y') # ????????????, 4(IFRS ??????), Y:??? ??????

    # df = pd.read_html(url, flavor='html5lib')
    # df = dfs[0]
    # df = df.set_index('??????????????????')
    # df.head()
    # df.head(10) # 10??? ????????? ??????(?????? 32??? ??????)
    # print(df[11])

    soup = bs(html, 'html.parser')
    tables = soup.select("table")


    # company_performance(soup, "section cop_analysis", jongmok_cd, jongmok_nm)


if __name__ == "__main__":
    jongmok_cd = "005930"
    jongmok_nm = "????????????"
    execute(jongmok_cd, jongmok_nm)
    # df_stock_list = pd.read_csv("./stock_list.csv", encoding="CP949")
    # df_stock_list.rename(columns = {"????????????": 'JONGMOK_CD', "?????? ????????????": 'JONGMOK_NM', "????????????": "MARKET_DIV", "?????????": "IN_CHARGE"}, inplace = True)
    # df_filtered = df_stock_list[((df_stock_list.MARKET_DIV == "KOSDAQ") | (df_stock_list.MARKET_DIV == "KOSPI")) & ((df_stock_list.IN_CHARGE.str.contains("???????????????") == False) |(df_stock_list.IN_CHARGE.isnull()))]
    
    # idx = 0
    # for (jongmok_cd, jongmok_nm) in zip(df_filtered["JONGMOK_CD"], df_filtered['JONGMOK_NM']):
    #     idx += 1
    #     print(idx, jongmok_cd, jongmok_nm)
    #     DEL_QRY = f"""
    #         DELETE FROM quant.jongmok_perform
    #          WHERE JONGMOK_CD = '{jongmok_cd}'
    #     """
    #     try:
    #         conn_db.transaction_data(DEL_QRY, db='quant')
    #     except:
    #         print(DEL_QRY)
        # execute(jongmok_cd, jongmok_nm)
