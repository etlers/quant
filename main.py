import sys
import time, datetime
from numpy.core.numeric import NaN
import pandas as pd

sys.path.append("C:/Users/etlers/Documents/project/python/common")
import crawl_soup
import date_util
import conn_db

now_dtm = date_util.get_now_datetime_string()

dict_accnt_ym = {}
dict_summary_idx = {}

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
            year_div = "분기" if key >= quarter_idx else "년도"
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
    


def company_summary_index(soup, class_id, jongmok_cd, jongmok_nm):

    def remove_string(row_strip):
        return row_strip.replace("<td>","").replace("</td>","").replace("<em>","").replace("</em>","").replace('<em id="_dvr">','').replace('배','').replace('%','')

    result_jongmok_index = soup.find("div",{"class":class_id})

    list_result = str(result_jongmok_index).split("\n")

    idx = 0
    next_idx = 0
    idx_name = ""
    for row in list_result:
        row_strip = row.strip()
        if len(row_strip) == 0 or row_strip in list_skip_row or "caption" in row_strip or "table" in row_strip : continue
        if "호가 10단계" in row_strip: break
        idx += 1
        if "외국인소진율" in row_strip:
            idx_name = "외국인소진율(%)"
            next_idx = idx + 6
        elif '<em id="_dvr">' in row_strip:
            dict_summary_idx["배당수익률(%)"] = remove_string(row_strip)
            continue
        elif "동일업종 PER" in row_strip:
            idx_name = "동일업종 PER(배)"
            next_idx = idx + 1
        
        if next_idx == idx:
            dict_summary_idx[idx_name] = remove_string(row_strip)

    for key, val in dict_summary_idx.items():
        IDX_QRY = f"""
            INSERT INTO quant.jongmok_idx
                 (JONGMOK_CD, INS_DT, DIV_NM, IDX_VAL, JONGMOK_NM, MOD_DTM)
            VALUES
                 ('{jongmok_cd}', '{now_dtm.split(" ")[0]}', '{key}', {val}, '{jongmok_nm}', NOW())
            ON DUPLICATE KEY
            UPDATE IDX_VAL = {val}
                 , JONGMOK_NM = '{jongmok_nm}'
                 , MOD_DTM = NOW()
        """
        conn_db.transaction_data(IDX_QRY, db='quant')


def execute(jongmok_cd, jongmok_nm):
    url_jongmok = f"https://finance.naver.com/item/main.naver?code={jongmok_cd}"

    soup = crawl_soup.get_soup(url_jongmok)

    company_performance(soup, "section cop_analysis", jongmok_cd, jongmok_nm)
    company_summary_index(soup, "aside_invest_info", jongmok_cd, jongmok_nm)


if __name__ == "__main__":
    # execute("000250", "삼천당제약")
    
    df_stock_list = pd.read_csv("./stock_list.csv", encoding="CP949")
    df_stock_list.rename(columns = {"단축코드": 'JONGMOK_CD', "한글 종목약명": 'JONGMOK_NM', "시장구분": "MARKET_DIV", "소속부": "IN_CHARGE"}, inplace = True)
    # df_filtered = df_stock_list[((df_stock_list.MARKET_DIV == "KOSDAQ") | (df_stock_list.MARKET_DIV == "KOSPI")) & (df_stock_list.IN_CHARGE.str.contains("소속부없음") == False)]
    df_filtered = df_stock_list[((df_stock_list.MARKET_DIV == "KOSDAQ") | (df_stock_list.MARKET_DIV == "KOSPI")) & ((df_stock_list.IN_CHARGE.str.contains("소속부없음") == False) |(df_stock_list.IN_CHARGE.isnull()))]
    # print(len(df_filtered))
    idx = 0
    for (jongmok_cd, jongmok_nm) in zip(df_filtered["JONGMOK_CD"], df_filtered['JONGMOK_NM']):
        idx += 1
        print(idx, jongmok_cd, jongmok_nm)
        DEL_QRY = f"""
            DELETE FROM quant.jongmok_perform
             WHERE JONGMOK_CD = '{jongmok_cd}'
        """
        try:
            conn_db.transaction_data(DEL_QRY, db='quant')
        except:
            print(DEL_QRY)
        execute(jongmok_cd, jongmok_nm)
