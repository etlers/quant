import requests
import sys
import time, datetime
from bs4 import BeautifulSoup as bs
<<<<<<< HEAD
import pandas as pd
=======
import kodex_reverage
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca

sys.path.append("/home/ubuntu/etlers/pysrc/pycom")

import crawl_soup

# import send_slack_message as SSM
# import common_util as CU

url_index = "https://kr.investing.com/currencies/us-dollar-index"
url_currency = "https://kr.investing.com/currencies/usd-krw"
url_kodex = "https://finance.naver.com/"

line_len = 70


def get_soup(url):
    response = requests.get( url, headers={"User-agent": "Mozilla/5.0"} )
    soup = bs(response.text, 'html.parser')

    return soup


def make_usd_index():
    soup = crawl_soup.get_soup(url_index)

    historical_usd_idx = soup.find("div",{"class":"clear overviewDataTable overviewDataTableWithTooltip"})

    if historical_usd_idx is None: return -1

    idx = 0
    dict_usd_idx = {}
    for row in historical_usd_idx:
        row_string = str(row).strip()
        if len(row_string) == 0: continue
        idx += 1
        temp = str(row_string.split('<span class="float_lang_base_1">')[1:]).replace("['","")
        list_temp = temp.replace("</span><span class=","").split('"float_lang_base_2 bold">')
        dict_usd_idx[idx] = [list_temp[0].replace(" ",""), list_temp[1].replace("</span></div>']","")]
    
    return dict_usd_idx


# Now Currency & 52 weeks average
def make_usd_krw():
<<<<<<< HEAD
    soup = get_soup(url_currency)

    current_usd_krw = soup.find("div",{"class":"instrument-price_instrument-price__3uw25 flex items-end flex-wrap font-bold"})
    current_usd_krw = float(str(current_usd_krw).split("instrument-price-last")[1].split("</span>")[0].replace('">','').replace(",",""))
    
    dict_usd_krw = {}
    
    idx = 0
    dict_usd_krw[idx] = current_usd_krw
    
    currency_range = soup.find("div",{"class":"mb-5 bg-background-surface border-b-2 pb-5 instrumentOverview_overview-section__2hN4A"})
    currency_range = str(currency_range).split("52주 변동폭")[1].split("1년 변동률")[0]
    list_range = currency_range.split("<span>")
    
    for val in list_range:
        try:
            num_value = float(val.replace(",","").replace("</span>",""))
            idx += 1
            dict_usd_krw[idx] = num_value
        except:
            pass
=======
    soup = crawl_soup.get_soup(url_currency)
    
    list_usd_krw = soup.find("div",{"class":"instrument-price_instrument-price__3uw25 flex items-end flex-wrap font-bold"})
    
    if list_usd_krw is None: return -1

    idx = 0
    dict_usd_krw = {}
    for row in list_usd_krw:
        row_string = str(row).strip()
        if 'data-test="instrument-price-last' in row_string:
            now_currency = float(row_string.split(">")[1].replace("</span>", "").replace(",", "").replace("</span", ""))
            idx += 1
            dict_usd_krw[idx] = now_currency
            break
        """
        if len(row_string) == 0: continue
        idx += 1
        print(idx, row_string)
        if idx == 1:
            dict_usd_krw[idx] = row_string.split('<div class="')[1].split(" ")[0]
        else:
            list_val = []
            for val in row_string.split("\n"):
                if "span class" not in val: continue
                list_val.append(val.split('">')[1].replace("</span>",""))
            dict_usd_krw[idx] = list_val
        """
            
    str_avg_dt = str(soup.find("div",{"class":"mb-5 bg-background-surface border-b-2 pb-5 instrumentOverview_overview-section__2hN4A"}))
    list_temp = str_avg_dt.split('<span class="key-info_dd-numeric__2cYjc"><span>')[1:]
    for row in list_temp:
        dt_val = float(row.split('</span')[0].replace(",", ""))
        idx += 1
        # 2: 전일 종가, 3: 매수, 4: 금일 변동, 5: 금일 변동, 6: 금일 시가, 7: 매도, 8: 52주 변동폭, 9: 52주 변동폭, 10: 1년 변동률
        dict_usd_krw[idx] = dt_val
    # for row in list_temp:
    #     print(row)
    # for row in list_usd_krw:
    #     row_string = str(row).strip()
    #     if len(row_string) == 0: continue
    #     idx += 1
    #     temp = str(row_string.split('<span class="key-info_dd-numeric__2cYjc"><span>')[1:]).replace("['","")
    #     print(temp)
    #     """
    #     temp = str(row_string.split('<span class="float_lang_base_1">')[1:]).replace("['","")
    #     list_temp = temp.replace("</span><span class=","").split('"float_lang_base_2 bold">')
    #     dict_usd_krw[idx] = [list_temp[0].replace(" ",""), list_temp[1].replace("</span></div>']","")]
    #     """
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca
    
    return dict_usd_krw


<<<<<<< HEAD
print("#" * 50)
print("# Index - [Real Time, VS Rate]")
print("#" * 50)
=======
def make_kodex_index():
    soup = crawl_soup.get_soup(url_kodex)

    kodex_idx = soup.find("div",{"class":"dsc_area dsc_area2"})
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca

idx = 0
while True:
    now_dtm = datetime.datetime.now()
    run_dt = now_dtm.strftime("%Y%m%d")
    run_dtm = now_dtm.strftime("%Y-%m-%d %H:%M:%S")

    dict_usd_idx = make_usd_index()
    dict_usd_krw = make_usd_krw()
    
<<<<<<< HEAD
=======
    if dict_usd_idx == -1:
        print("dict_usd_idx is None")
        return -1
    elif dict_usd_krw == -1:
        print("dict_usd_krw is None")
        return -1
    
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca
    # USD Index 52w Average
    year_avg_idx = (float(dict_usd_idx[10][1].split(" - ")[0].replace(",","")) + float(dict_usd_idx[10][1].split(" - ")[1].replace(",",""))) / 2
    # Now Index
    cur_idx = float(dict_usd_idx[4][1].replace(",",""))
    # USD KRW 52w Average
<<<<<<< HEAD
    year_avg_cur = (dict_usd_krw[1] + dict_usd_krw[2]) / 2
    # Now Currency
    now_cur = dict_usd_krw[0]
=======
    year_avg_cur = round((dict_usd_krw[8] + dict_usd_krw[9]) / 2, 2)
    # year_avg_cur = (float(dict_usd_krw[8][1].split(" - ")[0].replace(",","")) + float(dict_usd_krw[8][1].split(" - ")[1].replace(",",""))) / 2
    # Now Currency
    now_cur = dict_usd_krw[1]
    # now_cur = float(dict_usd_krw[2][0].replace(",",""))
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca
    # Dollar Gap Rate
    # usd_gap_rate = cur_idx / now_cur * 100
    # Dollar Gap Rate - 52w
    year_avg_usd_gap_rate = year_avg_idx / year_avg_cur * 100
    # Proper USD KRW
    
    proper_cur = round(cur_idx / year_avg_usd_gap_rate * 100, 2)
<<<<<<< HEAD
    now_rate = round((now_cur / proper_cur) * 100, 2)
    now_cur = '{:.2f}'.format(round(now_cur, 2))
    now_rate = '{:.2f}'.format(round(now_rate, 2))
    
    proper_cur = '{:.2f}'.format(round(cur_idx / year_avg_usd_gap_rate * 100, 2))
    result = f" {proper_cur} - [{now_cur}, {now_rate}%]"
    print(result)
    
    time.sleep(5)
=======
    # Kodex
    buy_amount = 0
    forgn_rt = 0.0
    if run_dtm.split(" ")[1].replace(":","") > "063000" or run_dtm.split(" ")[1].replace(":","") < "000000":
        pass
    else:
        dict_kodex_idx = make_kodex_index()        
        for row in dict_kodex_idx.values():
            if row > 0:
                buy_amount += row
        try:
            forgn_rt = round((dict_kodex_idx["외국인"] / buy_amount) * 100, 2)
        except:
            forgn_rt = 0.0
        try:
            kodex_status = kodex_reverage.execute()
        except:
            kodex_status = "No result"
    # Result
    now_rate = round((now_cur / proper_cur) * 100, 2)
    now_cur = '{:.2f}'.format(round(now_cur, 2))
    now_rate = '{:.2f}'.format(round(now_rate, 2))
    forgn_rt = '{:.2f}'.format(round(forgn_rt, 2))
    base_currency = '{:.2f}'.format(round(proper_cur, 2))
    try:
        result = f" {base_currency} - [{now_cur}, {now_rate}%] [{forgn_rt}% - ({dict_kodex_idx['외국인']} / {buy_amount})] [{dict_kodex_idx['개인']}, {dict_kodex_idx['기관']}] {kodex_status}"
    except:
        result = f" {base_currency} - [{now_cur}, {now_rate}%]"
    print(result)


if __name__ == "__main__":
    
    print("#" * line_len)

    while True:
        now_dtm = datetime.datetime.now()
        run_dtm = now_dtm.strftime("%Y-%m-%d %H:%M:%S")
        run_hh = now_dtm.strftime("%H")

        if execute(run_dtm) == -1:
            break
        time.sleep(5)

    print("#" * line_len)
>>>>>>> 28a06aa6377d24b5d1141e740bd3440926b8a8ca
