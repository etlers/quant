import os, sys

from requests.models import requote_uri

sys.path.append("../pycom")
import crawl_soup
import date_util
import conn_db

url_main = "https://finance.naver.com/item/main.nhn?code=122630"


def execute():

    def replace_char(in_string):
        return in_string.replace('<span class="blind">','').replace("</span>","")

    soup = crawl_soup.get_soup(url_main)

    kodex_idx = str(soup.find("div",{"class":"today"})).split("\n")

    idx = 0
    now_price = ""
    num_sign = 1
    up_dn_price = 0
    up_dn_rt = 0.0
    for row in kodex_idx:
        idx += 1
        if idx == 4:
            now_price = replace_char(row)
        elif idx == 11:
            if "하락" in row:
                num_sign = -1
        elif idx == 12:
            up_dn_price = int(replace_char(row.replace(",","")))
        elif idx == 18:
            up_dn_rt = float(replace_char(row.replace(",","")))
    
    result = f"{now_price} [{up_dn_price * num_sign:,}, {up_dn_rt * num_sign}%]"
    return result


if __name__ == "__main__":
    execute()