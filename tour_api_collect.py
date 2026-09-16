# tour_api_collect.py
# TourAPI에서 서울 지역 관광지 목록을 받아오는 코드

import os
import requests
import pandas as pd

# 키는 환경변수에서 가져옴 — 터미널에서 실행 전에
# export TOUR_API_KEY="발급받은키값"  (맥/리눅스)
# set TOUR_API_KEY=발급받은키값        (윈도우)
# 이렇게 한 줄 실행해두면, 코드에는 키가 안 보여도 알아서 읽어옴
API_KEY = os.environ.get("TOUR_API_KEY")

if not API_KEY:
    raise ValueError("TOUR_API_KEY가 없습니다. 환경변수로 설정하고 실행해주세요.")

# TourAPI 지역기반 관광정보 조회 URL (KorService2, 신체계 기준)
URL = "https://apis.data.go.kr/B551011/KorService2/areaBasedList2"

def fetch_activities(area_code="1", page=1, rows=100):
    """
    area_code: 지역코드 ("1" = 서울)
    page: 페이지 번호
    rows: 한 번에 몇 건 받을지
    """
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "Tripilot",
        "areaCode": area_code,
        "pageNo": page,
        "numOfRows": rows,
        "_type": "json",
    }
    res = requests.get(URL, params=params, timeout=10)
    res.raise_for_status()  # 요청이 실패하면 여기서 바로 에러를 알려줌
    return res.json()