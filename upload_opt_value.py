#-*- coding: utf-8 -*-
"""
    Author. CHOI JooYong

    Desciption
        사용자가 정의한 옵션 정보 CSV 파일을 MSSQL 테이블로 업로드
        Python xlrd(openpyxl) 라이브러리 설치 필요
        사용자가 작성한 엑셀파일은 동일한 경로에 있다고 가정
        시나리오 코드에 대한 법인코드(Corp Code) 오류가 존재하면 메세지 출력하고 해당 시나리오는 건너뜀
        시나리오 코드 자체가 존재하지 않으면 pp_scenario & pp_scenario_map 테이블에 데이터 저장
        usrId, host 파라미터는 필수

    실행예
        python3 upload_opt_value.py --excel_file=PP_ExcelUpload_20210222.xlsx --host=http://34.64.217.52:8091 > opt_result.txt

    실행에 필요한 인자 값
        Named Parameter
            parser.add_argument('--excel_file', default = 'opt_val.xlsx')
            parser.add_argument('--host', default = '')
            parser.add_argument('--usrId', default = '')
"""

# 실행인자
import argparse
# 월요일 및 주차
from datetime import datetime, timedelta
# Rest API 파라미터
import json
# 파일 삭제
import os
# csv 데이터 읽어와 데이터 프레임으로 정의
import pandas as pd
# Rest API 호출
import requests


###############################################################################################
# 전역변수
###############################################################################################
# rest api server
headers = {'Content-Type': 'application/json; chearset=utf-8'}
# 현재일시, 주차 설정
now = datetime.now()
year_week = now.strftime('%Y') + now.strftime("%V")
current_dtm = now.strftime('%Y%m%d%H%M%S')
current_dt = now.strftime('%Y%m%d')
# 실제 저장되는 값 리스트
opt_value_list = []
# 예상 유효성 검사 데이터 리스트
lov_return_list = []
# 파일 경로 디렉터리
file_path = "./excel/"
# 유효성 검증 오류내역 저장 파일
validation_error_file = "validation_error.xlsx"
# 시나리오 존재 확인을 위한 리스트
scenario_check_list = []
scenario_map_check_list = []


# 입력 파라미터 확인
def check_arguments(args):
    if args.usrId == "":
        print("사용자 아이디 확인")
        return False
    elif args.host == "":
        print("Rest API 주소 확인")
        return False

    return True


# 시나리오코드에 대한 corp code 오류 로그 출력
def print_error(scenario_code, scenario_value, return_value):
    print("#" * 100)
    print("# 시나리오 CORP CODE 오류내역")
    print("#" * 100)
    print("# Scenario Code. " + scenario_code)
    print("# Table Corp CD. " + scenario_value)
    print("# Input Corp CD. " + return_value)
    print("#" * 100)
    print()


# 요청 및 결과에 대한 로그 출력
def print_insert_row_count(result_list, req_list):
    
    # 처리결과
    def job_request_log():
        print("#" * 100)
        print("# 요청에 대한 처리 결과")
        print("#" * 100)
        print('#  - errorCnt.  {0:>10}'.format(str(result_list["errorCnt"])) + " 건")
        print('#  - insertCnt. {0:>10}'.format(str(result_list["insertCnt"])) + " 건")
        print('#  - prcsCnt.   {0:>10}'.format(str(result_list["prcsCnt"])) + " 건")
        print('#  - deleteCnt. {0:>10}'.format(str(result_list["deleteCnt"])) + " 건")
        print('#  - updateCnt. {0:>10}'.format(str(result_list["updateCnt"])) + " 건")
        print("#" * 100)
    
    # 요청내역
    def req_detail():
        print()
        print("#" * 100)
        print("# 대상 시나리오코드 목록")
        print("#" * 100)
        print("# 전체. 시나리오 " + str(len(req_list)) + " 개, " + str(len(opt_value_list)) + " 건")
        print("#" * 100)
        idx = 0
        for list_val in req_list:
            idx += 1
            print("{0:>3}.".format(str(idx)) + " " + list_val.split(".")[0])
        print("#" * 100)
        print()

    req_detail()
    job_request_log()

# 검증을 위한 딕셔너리
lov_check_dict = {}
num_check_dict = {}
mon_check_dict = {}
null_check_dict = {}
scenario_check_dict = {}


# 유효성 체크를 위한 검증 데이터 딕셔너리 생성
def get_validation_data(rest_api_ip_addr_port):
        
    # 구분에 따른 딕셔너리 분류하기
    def make_validation_dictionary(result_list):
        for opt in result_list:
            check_target = False
            if (opt["optLovNm"] != None and opt["optLovNm"][:4] == "LOV_"):
                lov_check_dict[opt["optCd"]] = opt["optLovNm"]
                check_target = True
            else:
                if (opt["optDataTp"] == "PERCENT" or opt["optDataTp"] == "NUM"):
                    check_target = True
                    num_check_dict[opt["optCd"]] = opt["optDataTp"]
                elif opt["optDataTp"] == "DATE_MONDAY":
                    check_target = True
                    mon_check_dict[opt["optCd"]] = opt["optDataTp"]
            # 널 불가
            if opt["nullYn"] == "N":
                null_check_dict[opt["optCd"]] = "N"
    
    # pp_code lov 데이터 결과 리스트에 추가
    def make_code_dictionary(result_list):
        for key, value in lov_check_dict.items():
            for code in result_list:
                grp_cd_dict = {}
                if code["grpCd"] == value:
                    grp_cd_dict["grpCd"] = code["grpCd"]
                    grp_cd_dict["cd"] = code["cd"]
                    lov_return_list.append(grp_cd_dict)

    # 시나리오 데이터
    def make_scenario_dictionary(result_list):
        # scenarioCd, corpCd
        for scenario in result_list:
            scenario_check_dict[scenario["scenarioCd"]] = scenario["corpCd"]
            scenario_check_list.append(scenario["scenarioCd"])

    # 시나리오 맵 데이터 리스트 만들기
    def make_scenario_map_list(result_list):
        for scenario_map in result_list:
            scenario_map_check_list.append(scenario_map["scenarioCd"] + ":" + scenario_map["mapTp"] + ":" + scenario_map["mapCd"])
    

    # 파라미터 정의
    opt_validation_dict = {
        "Session": {
            "usrId": "upload_opt_value",
            "sysDttm": current_dtm,
            "pgmNm": "upload_opt_value",
            "jobId": 0,
            "jobGrpId": 0,
            "osPrcsId": 0,
            "url": "",
            "step": ""
        },
        "InParm": [
            
        ]
    }
    # JSON 파라미터 생성
    param_json_data = json.dumps(opt_validation_dict, ensure_ascii=False, indent="\t")
    # 서버 호출
    url_rest_api = rest_api_ip_addr_port + "/de/excel"
    # thcha
    print(url_rest_api)
    response = requests.get(url_rest_api, headers=headers, data=param_json_data)
    # 결과를 JSON 형태로 변환
    result_json = response.json()
    # 결과코드 확인
    result_code = result_json["OutResult"]["rtnCd"]
    # rest api 오류인 경우
    if result_code != 1:
        print(response)
        return response
    # 유효성 검사 딕셔너리 데이터 생성
    make_validation_dictionary(result_json["OutOptLst"])
    # pp_code 에서 lov 데이터 찾아 리스트 만들기
    make_code_dictionary(result_json["OutCodeLst"])
    # 시나리오 데이터 리스트 만들기
    make_scenario_dictionary(result_json["OutScenarioLst"])
    # 시나리오 맵 데이터 리스트 만들기
    make_scenario_map_list(result_json["OutScenarioMapLst"])
    # LOV 유효성 검사
    key_list = []
    for read_dict in lov_return_list:
        for key, value in read_dict.items():
            if key == "grpCd":
                # 값에 "LOV_" 제거하면서 키 리스트에 추가
                key_list.append(value)
    # 중복 제거
    key_list = list(set(key_list))
    # 유효성 검사를 위한 딕셔너리
    validation_dict = {}
    # 키 목록을 읽으면서 유효성 데이터 추출해서 딕셔너리의 리스트로 추가
    for opt_code in key_list:
        # 키에 대한 유효성 데이터 리스트
        value_list = []
        for read_dict in lov_return_list:
            # 키와 동일한 그룹만 대상으로 함
            if read_dict["grpCd"] != opt_code: continue
            # 있으면 유효성 검증을 위한 코드 값 리스트로 추가
            value_list.append(read_dict["cd"])
        # 최종 딕셔너리 생성
        validation_dict[opt_code] = value_list
    
    return validation_dict


# 사용자가 입력하는 컬럼을 rest api에서 사용하는 컬럼으로 변경
change_name_dict = {
    "algo": "algoCd",
    "algorithm_code": "algoCd",
    "product": "prdCd",
    "account": "custCd",
    "dc_flag": "dcTp",
    "dc_type": "dcTp",
    "affiliate_branch_code": "corpCd",
}

# 시나리오 오류 확인을 위한 변수 초기화
scenario_error_list = []
scenario_value_list = []
# 시나리오 등록을 위한 변수 초기화
scenario_list = []
scenario_map_list = []


# 미존재 시나리오 등록을 위한 데이터 생성
def make_scenario_data(scenario_df, scenario_cd):
    # SCENARIO_CD, USE_YN, SCENARIO_JOB_NM_ALIAS, DESCR, CORP_CD, SIMUL_YN
    # SCENARIO_CD, MAP_TP, MAP_CD, USE_YN
    # 회신을 위한 corp code
    corp_code = ""
    for _, row in scenario_df.iterrows():
        if type(row["scenario_code"]) != str: continue
        scenario_dict = {}
        scenario_map_dict = {}
        # 고정 값
        # 시나리오
        scenario_dict["scenarioCd"] = scenario_cd.split(".")[0]
        scenario_dict["useYn"] = "Y"
        scenario_dict["scenarioJobNmAlias"] = scenario_cd.split(".")[0]
        scenario_dict["descr"] = scenario_cd.split(".")[0]
        scenario_dict["mdlngNm"] = "SELLOUT_%%JOP_TP%%"
        scenario_dict["simulYn"] = "Y"
        # 시나리오 맵
        scenario_map_dict["scenarioCd"] = scenario_cd.split(".")[0]
        scenario_map_dict["useYn"] = "Y"
        # corp code
        if row["scenario_code"].lower() == "affiliate_branch_code":
            scenario_dict["corpCd"] = row[scenario_cd]
            corp_code = row[scenario_cd]
            # 시나리오 체크 리스트에 없으면
            if scenario_cd.split(".")[0] not in scenario_check_list:
                # 시나리오 테이블 추가
                scenario_list.append(scenario_dict)
        # 이하 시나리오 맵
        elif (row["scenario_code"].lower() == "product" or row["scenario_code"].lower() == "account" or row["scenario_code"].lower() == "dc_type"):
            # 기존거에 존재하면 그냥 나감
            if row["scenario_code"].lower() == "product":
                scenario_map_dict["mapTp"] = "PRD_CD"
                scenario_map_tp = "PRD_CD"
            elif row["scenario_code"].lower() == "account":
                scenario_map_dict["mapTp"] = "CUST_CD"
                scenario_map_tp = "CUST_CD"
            elif row["scenario_code"].lower() == "dc_type":
                scenario_map_dict["mapTp"] = "DC_TP"
                scenario_map_tp = "DC_TP"
            # 키 체크
            if (scenario_cd.split(".")[0] + ":" + scenario_map_tp + ":" + str(row[scenario_cd])) not in scenario_map_check_list:
                scenario_map_dict["mapCd"] = row[scenario_cd]
                # 시나리오 맵 테이블 추가
                scenario_map_list.append(scenario_map_dict)
        # 시나리오 맵 알고리즘
        elif row["scenario_code"].lower()[:16] == "hyper_parameter_":
            # selection 경우는 그냥 지나감
            if "selection" in row["scenario_code"].lower(): continue
            # 알고리즘 코드
            scenario_map_dict["mapTp"] = "ALGO_CD"
            scenario_map_dict["mapCd"] = row["scenario_code"].replace("hyper_parameter_", "")
            if str(row[scenario_cd]) == "nan":
                scenario_map_dict["useYn"] = "N"
            # 시나리오 맵 테이블 추가
            scenario_map_list.append(scenario_map_dict)
        else:
            continue
    # 시나리오 맵 OPT_CD 추가
    scenario_map_dict = {}
    scenario_map_dict["scenarioCd"] = scenario_cd.split(".")[0]
    scenario_map_dict["useYn"] = "Y"    
    scenario_map_dict["mapTp"] = "OPT_CD"
    scenario_map_dict["mapCd"] = "opt_all"
    scenario_map_list.append(scenario_map_dict)

    return corp_code


# 컬럼 단위로 잘라 생성한 데이터 프레임으로 파라미터 및 유효성 검증에 사용할 딕셔너리 생성
def remake_opt_df(df_opt, scenario_cd, corp_code):

    # Key 생성
    def make_dictionary_list():
        key_yn = True
        opt_value_dict = {}
        opt_value_dict["scenarioCd"] = scenario_cd.split(".")[0]
        
        # key 먼저 생성
        for _, row in df_opt.iterrows():
            # 세 개 컬럼은 제외
            if (row["scenario_code"].lower() == "affiliate_branch_code" or row["scenario_code"].lower() == "affiliate_branch_name" or row["scenario_code"].lower() == "division_code") : continue
            # 키 컬럼이 끝났다면 빠져나감
            if key_yn == False: break
            # 현재 사용하고 있는 컬럼 명칭으로 키컬럼 변경
            key_name = change_name_dict[row["scenario_code"]]
            # 키 딕셔너리 추가. 없으면 "*"로 변경
            if str(row[scenario_cd]) == "nan":
                opt_value_dict[key_name] = "*"
            else:
                opt_value_dict[key_name] = row[scenario_cd]
            # 알고리즘이 나왔다는 것은 키 컬럼의 종료를 의미
            if (row["scenario_code"].lower() == "algorithm_code"):
                key_yn = False
        
        # 키 컬럼 제외를 위한 체크
        key_yn = True
        # cd, value 추가
        for _, row in df_opt.iterrows():
            # 알고리즘이 나왔다는 것은 키 컬럼은 다 읽었다는 의미로 다음 값 읽음
            if (row["scenario_code"] == "algorithm_code"):
                key_yn = False
                continue
            # 키 컬럼이 끝날 때까지는 지나감
            if key_yn == True: continue
            # nan 값은 제외
            if str(row["scenario_code"]) == "nan": continue
            # 매번 키에 하나의 컬럼에 대한 값만 추가해야 하므로 새롭게 키 딕셔너리 복사
            temp_dict = opt_value_dict.copy()
            # 키만 있는 임시 딕셔너리에 컬럼 값 추가
            option_code = row["scenario_code"]
            # 날짜형의 경우 문자형으로 변환
            if type(row[scenario_cd]) == datetime:
                option_value = row[scenario_cd].strftime('%Y-%m-%d')
            else:
                option_value = row[scenario_cd]
            # "nan" -> ""
            if str(option_value) == "nan":
                option_value = ""            
            # Option Code & Value
            temp_dict["optCd"] = option_code
            temp_dict["optVal"] = option_value
            print(option_code, option_value)
            # USE_YN   
            temp_dict["useYn"] = "Y"
            # 전체 리스트에 추가
            opt_value_list.append(temp_dict)
    
    # 딕셔러니 리스트 생성
    make_dictionary_list()


# 에러 저장을 위한 데이터 프레임
error_df =  pd.DataFrame(columns=["scenarioCd", "dcTp", "custCd", "prdCd", "algoCd", "optCd", "optVal", "validation_list"])
error_dict = {}
scenarioCd_list = []
dcTp_list = []
custCd_list = []
prdCd_list = []
algoCd_list = []
optCd_list = []
optVal_list = []
valid_list = []
# 유효성 검사를 위한 딕셔너리 데이터 생성함수
# args를 전달할 방법이 없음 
#validation_dict = get_validation_data()


# 엑셀 파일을 읽어서 파라미터를 생성하고 rest api 호출
# thcha def execute(excel_file):
def execute(excel_file, args):
    # 호스트 인자로 유효성 검사를 위한 데이터 추출 함수 호출
    validation_dict = get_validation_data(args.host)   
    # execute 함수 내로 옮겨 옴
    # 데이터 유효성 검사
    def check_data_validation(opt_dict, excel_file):

        # number type
        def check_numeric_data(opt_code, opt_value):
            try:
                # 존재하면 숫자 확인 대상
                tmp = num_check_dict[opt_code]
                # 널은 그냥 나감
                if opt_value == "":
                    return True
                # 널이 아니면 숫자여부 확인
                elif (type(opt_value) == int or type(opt_value) == float):
                    return True
                else:
                    # 비율의 경우로 스트링으로 들어오는 경우 숫자 변환이 가능한지 확인
                    if ("ratio" in opt_code and type(opt_value) == str):
                        try:
                            tmp = int(opt_value)
                            return True
                        except:
                            return False
                    return False
            except:
                return True

        # monday
        def check_monday_data(opt_code, opt_value):
            try:
                # 존재하면 월요일 확인 대상
                tmp = mon_check_dict[opt_code]
                # 월요일 만들기. 사용자가 월요일을 입력하는데 입력하지 않은 경우 처리
                input_dt = datetime.strptime(opt_value, '%Y-%m-%d')
                monday_dt = input_dt - timedelta(days = input_dt.weekday())                        
                # 입력 받은 값과 월요일 확인
                if opt_value == monday_dt.strftime('%Y-%m-%d'):
                    return True
                else:
                    return False
            except:
                return True

        # not null
        def check_not_null_data(opt_code, opt_value):
            try:
                # 존재하면 널 불가로 확인 대상
                tmp = null_check_dict[opt_code]            
                # 입력 받은 값이 존재하는지 확인
                if (str(opt_value) == "nan" or len(opt_value) == 0):
                    return False
                else:
                    return True
            except:
                return True    

        # 유효성 결과
        lov_valid_tf = True
        num_valid_tf = True
        mon_valid_tf = True
        # 엑셀에서 추출한 데이터 읽기
        for read_dict in opt_dict:
            opt_code = read_dict["optCd"]
            opt_value = read_dict["optVal"]
            # LOV 데이터의 경우 유효성 딕셔너리의 키를 통해 값 확인.
            try:
                # 키에 대한 값 리스트 추출
                validation_list = validation_dict["LOV_" + opt_code]
                # 존재하면서 널 허용이고 널이면 그냥 빠져나감
                try:
                    tmp = null_check_dict[opt_code]
                    not_null_yn = "N"
                except:
                    not_null_yn = "Y"
                # 널 허용이고 값이 없으면 다음 처리
                if not_null_yn == "N":
                    if (str(opt_value) != "nan" and len(opt_value) != 0):
                        # 값 리스트에 없으면 내용 출력 후 결과 값 오류로 변경
                        if str(opt_value) not in validation_list:
                            # 변동 파라미터
                            scenarioCd_list.append(read_dict["scenarioCd"])
                            dcTp_list.append(read_dict["dcTp"])
                            custCd_list.append(read_dict["custCd"])
                            prdCd_list.append(read_dict["prdCd"])
                            algoCd_list.append(read_dict["algoCd"])
                            # 유효성 파라미터
                            optCd_list.append(opt_code)
                            optVal_list.append(opt_value)
                            valid_list.append(str(validation_list))
                            # 결과코드
                            lov_valid_tf = False
            # LOV가 아닌 경우의 체크
            except:
                # 널 불가
                null_valid_tf = check_not_null_data(opt_code, opt_value)
                if null_valid_tf == False:
                    valid_list.append("NOT_NULL")
                # 숫자 체크
                num_valid_tf = check_numeric_data(opt_code, opt_value)
                if num_valid_tf == False:
                    valid_list.append("NUM")
                # 월요일 체크
                mon_valid_tf = check_monday_data(opt_code, opt_value)
                if mon_valid_tf == False:
                    valid_list.append("DATE_MONDAY")
                # 에러가 존재하는 경우만 추가
                if (null_valid_tf == False or num_valid_tf == False or mon_valid_tf == False):
                    # 변동 파라미터
                    scenarioCd_list.append(read_dict["scenarioCd"])
                    dcTp_list.append(read_dict["dcTp"])
                    custCd_list.append(read_dict["custCd"])
                    prdCd_list.append(read_dict["prdCd"])
                    algoCd_list.append(read_dict["algoCd"])
                    # 유효성 파라미터
                    optCd_list.append(opt_code)
                    optVal_list.append(opt_value)

        # 유효성 검증 오류내역 딕셔너리에 추가
        def add_error_dict():
            error_dict["scenarioCd"] = scenarioCd_list
            error_dict["dcTp"] = dcTp_list
            error_dict["custCd"] = custCd_list
            error_dict["prdCd"] = prdCd_list
            error_dict["algoCd"] = algoCd_list
            error_dict["optCd"] = optCd_list
            error_dict["optVal"] = optVal_list
            error_dict["validation_list"] = valid_list
        
        # 오류인 경우 CSV 생성을 위한 딕셔너리 데이터 생성
        if len(scenarioCd_list) > 0:
            add_error_dict()
            return False
        else:
            return True

    # 시나리오 vs corp_cd 확인
    def check_scenario_vs_corp(chk_df, scenario_cd, corp_code):
        # key 먼저 생성
        for _, row in chk_df.iterrows():
            # corp code 비교
            if row["scenario_code"].lower() == "affiliate_branch_code":
                # 존재는 하지만 다르면 오류
                if row[scenario_cd] != corp_code:
                    return row[scenario_cd]
            else:
                continue
        # corp cd 오류만 아니면 정상으로 처리
        return True

    # 요청내역 출력을 위한 리스트
    check_column_list = []
    # 엑셀파일 불러오기
    df_opt = pd.read_excel(excel_file)    
    # 몇 개의 열이 나올지 모르므로 첫번째 열을 제외한 나온 열 수만큼 읽음
    for idx in range(len(df_opt.columns)):
        column_list = []
        # 첫번째 컬럼은 무조건 쌍으로 움직임
        column_list.append(df_opt.columns[0])
        if idx > 0:
            # 열 첫번째가 공백이라면 시나리오가 더이상 없는 것으로 간주
            if (str(df_opt.columns[idx]).lower() == "nan" or df_opt.columns[idx] is None or len(df_opt.columns[idx].strip())) == 0: break
            # 목록에 시나리오코드 추가
            column_list.append(df_opt.columns[idx])                        
            # 시나리오 존재여부 확인. 있으면 CORP CD 값은 일치해야 함을 확인
            corp_code = ""
            try:
                corp_code = scenario_check_dict[column_list[1]]
                # 시나리오는 존재해도 corp code 값은 없을 수 있기에 확인하러 감
                return_value = check_scenario_vs_corp(df_opt[column_list], column_list[1], corp_code)
                if type(return_value) == str:
                    # 일치하지 않는다면 오류를 출력하고 다음 시나리오를 읽음
                    print_error(column_list[1], corp_code, return_value)
                    continue
            except:
                # 없으면 등록하기 위한 데이터 추가
                corp_code = make_scenario_data(df_opt[column_list], column_list[1])
            # 실제 데이터로 opt_val 등록을 위한 파라미터 생성하기
            remake_opt_df(df_opt[column_list], df_opt.columns[idx], corp_code)
            # 요청 요약내역 딕셔너리 리스트 생성
            check_column_list.append(df_opt.columns[idx])
            
    # 옵션 코드, 값 딕셔너리 리스트 추가
    param_dict= {}
    in_param_list = []
    param_dict["saveType"] = "DELETE_INSERT"
    param_dict["optCat"] = "ALL"
    in_param_list.append(param_dict)
    # 최종 데이터 등록 및 유효성 검사를 위한 딕셔너리
    in_params_dict = {
        "Session": {
            "usrId": args.usrId, #thcha "upload_opt_value",
            "sysDttm": current_dtm,
            "pgmNm": "upload_opt_value",
            "jobId": 0,
            "jobGrpId": 0,
            "osPrcsId": 0,
            "url": args.host, #thcha "",
            "step": ""
        }
    }
    in_params_dict["InParm"] = in_param_list
    in_params_dict["InOptValLst"] = opt_value_list
    # 시나리오 코드가 정상인 경우 이후 데이터의 유효성 검사
    validation_tf = check_data_validation(in_params_dict["InOptValLst"], excel_file)
    # 유효성 검증 오류가 존재하는 경우
    if validation_tf == False:
        print("Validation Error!!")
        error_df = pd.DataFrame.from_dict(error_dict)
        error_df = error_df[["scenarioCd", "dcTp", "custCd", "prdCd", "algoCd", "optCd", "optVal", "validation_list"]]
        # 확인을 위한 CSV 파일로 생성
        error_df.to_excel(validation_error_file, index=False, encoding="utf-8-sig")
        return False
    # 정상이면 데이터 저장을 위한 rest api 서버 호출
    else:
        # 등록할 시나리오 정보 추가
        in_params_dict["InScenarioLst"] = scenario_list
        in_params_dict["InScenarioMapLst"] = scenario_map_list
        # 딕셔너리 데이터 JSON 타입 파라미터로 변환
        param_json_data = json.dumps(in_params_dict, ensure_ascii=False, indent="\t")
        print(param_json_data)
        # 서버 호출. 
        #thcha url_rest_api = rest_api_ip_addr_port + "/de/excel"
        url_rest_api = args.host + "/de/excel"
        # thcha
        print(url_rest_api)
        response = requests.post(url_rest_api, headers=headers, data=param_json_data)
        # 결과를 JSON 형태로 변환
        result_json = response.json()
        # 결과코드 확인
        result_code = result_json["OutResult"]["rtnCd"]
        # 오류인 경우
        if result_code != 1:
            print(response)
            print(result_json)
        else:
            # 요약내용 프린트
            print_insert_row_count(result_json["OutResult"], check_column_list)
            #print(result_json)

# 프로그램 시작
if __name__ == "__main__":
    # 파라미터를 받아와 정의
    parser = argparse.ArgumentParser()
    parser.add_argument('--excel_file', default = 'opt_val.xlsx')
    parser.add_argument('--host', default = '')
    parser.add_argument('--usrId', default = '')
    # 입력 파라미터 확인
    args = parser.parse_args()
    #
    #thcha
    # print(args.excel_file)
    # print(args.host)
    # print(args.usrId)
    # thcha
    if check_arguments(args) == True:
        # 엑셀 확장자 확인. 없으면 붙여줌
        if args.excel_file[len(args.excel_file)-5:] != ".xlsx":
            args.excel_file = args.excel_file + ".xlsx"
        # 입력받은 파일 명칭으로 생성
        validation_error_file = file_path + args.excel_file.replace(".xlsx", "").replace(".XLSX", "") + "_" + validation_error_file
        # 수행 전 기존 오류 검증내역 파일 존재하면 삭제
        if os.path.exists(validation_error_file):
            os.remove(validation_error_file)
        # 입력받은 엑셀 파일로 실행
        # thcha execute(file_path + args.excel_file)
        execute(file_path + args.excel_file, args)
