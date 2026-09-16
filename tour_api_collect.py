# tour_api_collect.py
# "영어권 인기관광지" 리스트(data/popular_places_seoul_en.csv)로 범위를 좁혀
# TourAPI에서 해당 장소만 상세정보를 받아오는 코드.

import os
import re
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import unquote

# .env 파일이 있으면 그 안의 값들을 환경변수로 불러옴 (없어도 에러 안 남)
load_dotenv()

# 키는 환경변수(.env 또는 터미널의 export/set)에서 가져옴.
# 공공데이터포털이 발급하는 "인증키(Encoding)" 버전을 그대로 넣어두면,
# requests가 params=에서 다시 한번 인코딩해 이중 인코딩(403 Forbidden)이 나므로
# 여기서 한 번 디코딩해 항상 원문 키 상태로 맞춰준다.
_raw_key = os.environ.get("TOUR_API_KEY")
API_KEY = unquote(_raw_key) if _raw_key else None

if not API_KEY:
    raise ValueError("TOUR_API_KEY가 없습니다. 환경변수로 설정하고 실행해주세요.")

BASE_URL = "https://apis.data.go.kr/B551011/KorService2"
AREA_LIST_URL = f"{BASE_URL}/areaBasedList2"
SEARCH_KEYWORD_URL = f"{BASE_URL}/searchKeyword2"

POPULAR_PLACES_PATH = "data/popular_places_seoul_en.csv"


def fetch_activities(area_code="1", page=1, rows=100):
    """
    지역 전체를 페이지 단위로 훑는 기존 방식(현재는 사용하지 않음, 참고/폴백용).
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
    res = requests.get(AREA_LIST_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json()


def search_keyword2(keyword, area_code=None, rows=10):
    """
    장소명(keyword)으로 TourAPI를 검색해 실제 contentId를 조회.
    임의로 contentId를 만들어 쓸 수 없어서(9/16 확인), 반드시 이 호출로
    실제 값을 먼저 받아와야 함.
    """
    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "Tripilot",
        "keyword": keyword,
        "areaCode": area_code,
        "numOfRows": rows,
        "pageNo": 1,
        "_type": "json",
    }
    res = requests.get(SEARCH_KEYWORD_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json()


def to_dataframe(api_response):
    body = api_response["response"]["body"]
    total_count = body["totalCount"]
    if total_count == 0:
        return pd.DataFrame()
    items = body["items"]["item"]
    # totalCount == 1이면 items가 dict 하나로 오는 경우가 있어 리스트로 맞춰줌
    if isinstance(items, dict):
        items = [items]
    return pd.DataFrame(items)


def load_popular_places(path=POPULAR_PLACES_PATH):
    """extract_popular_places.py가 만들어 둔 "영어권 인기관광지" 리스트를 읽어옴."""
    return pd.read_csv(path, encoding="utf-8-sig")


def pick_best_match(df: pd.DataFrame, keyword: str):
    """
    searchKeyword2 결과 중 실제 원하는 장소를 고른다.
    (areaCode 없이 검색하면 "GS25 남산서울타워점" 같은 주변 매장도 같이 걸려서,
    제목이 keyword와 정확히 일치하는 걸 최우선으로 채택한다.)
    """
    exact = df[df["title"] == keyword]
    if not exact.empty:
        candidates = exact
    else:
        candidates = df

    # 동명이인 방지: 주소에 "서울"이 포함된 후보를 우선
    if "addr1" in candidates.columns:
        seoul = candidates[candidates["addr1"].astype(str).str.contains("서울", na=False)]
        if not seoul.empty:
            candidates = seoul

    return candidates.iloc[0].to_dict()


def generate_keyword_variants(name: str):
    """
    데이터랩 표기명은 TourAPI 등록명과 괄호/공백/복합표기가 달라서 그대로 검색하면
    실패하는 경우가 많음(9/17 확인). 원본을 1순위로 하고, 아래 순서로 변형을 시도한다.
    """
    variants = [name]

    no_brackets = re.sub(r"\[[^\]]*\]", "", name).strip()
    no_brackets = re.sub(r"\s+", " ", no_brackets)
    if no_brackets and no_brackets not in variants:
        variants.append(no_brackets)

    # 괄호 문자만 제거하고 안의 텍스트는 남김 (예: "롯데백화점 (본점)" -> "롯데백화점 본점")
    paren_as_text = re.sub(r"[()]", "", no_brackets).strip()
    paren_as_text = re.sub(r"\s+", " ", paren_as_text)
    if paren_as_text and paren_as_text not in variants:
        variants.append(paren_as_text)

    # 괄호와 그 안 내용을 통째로 제거 (예: "(주) 교보문고" -> "교보문고")
    no_paren_content = re.sub(r"\([^)]*\)", "", no_brackets).strip()
    if no_paren_content and no_paren_content not in variants:
        variants.append(no_paren_content)

    no_space = name.replace(" ", "")
    if no_space not in variants:
        variants.append(no_space)

    # 가운뎃점(·)으로 두 장소가 합쳐진 표기는 앞부분만 시도 (공백 제거 버전도 함께)
    if "·" in name:
        first_part = name.split("·")[0].strip()
        if first_part and first_part not in variants:
            variants.append(first_part)
        first_part_no_space = first_part.replace(" ", "")
        if first_part_no_space and first_part_no_space not in variants:
            variants.append(first_part_no_space)

    return variants


def resolve_content_ids(popular_places: pd.DataFrame, area_code=None, sleep_sec=0.1):
    """
    popular_places의 각 장소(korean_name 우선, 없으면 english_name)로
    searchKeyword2를 호출해 실제 contentId를 매칭한다.
    (searchKeyword2는 keyword+areaCode를 같이 주면 결과가 비어버리는 경우가 많아
    기본은 areaCode 없이 검색하고, 대신 제목 일치/서울 주소 우선으로 후보를 고른다.)
    원래 이름으로 실패하면 generate_keyword_variants()의 변형들을 순서대로 재시도하고,
    어떤 키워드로 매칭됐는지 match_keyword에 남긴다. 끝까지 실패한 건만 unmatched로 남긴다.
    """
    matched_rows = []
    unmatched = []

    for _, place in popular_places.iterrows():
        base_keyword = place["korean_name"] if pd.notna(place["korean_name"]) else place["english_name"]

        df = pd.DataFrame()
        matched_keyword = None
        for keyword in generate_keyword_variants(base_keyword):
            response = search_keyword2(keyword, area_code=area_code)
            df = to_dataframe(response)
            time.sleep(sleep_sec)
            if not df.empty:
                matched_keyword = keyword
                break

        if df.empty:
            unmatched.append({
                "english_name": place["english_name"],
                "korean_name": place["korean_name"],
                "raw_categories": place["raw_categories"],
            })
            continue

        best = pick_best_match(df, matched_keyword)
        matched_rows.append({
            "english_name": place["english_name"],
            "korean_name": place["korean_name"],
            "raw_categories": place["raw_categories"],
            "match_type": "auto",
            "match_keyword": matched_keyword,
            "contentid": best.get("contentid"),
            "contenttypeid": best.get("contenttypeid"),
            "title": best.get("title"),
            "addr1": best.get("addr1"),
            "lclsSystm1": best.get("lclsSystm1"),
            "lclsSystm2": best.get("lclsSystm2"),
            "lclsSystm3": best.get("lclsSystm3"),
        })

    matched_df = pd.DataFrame(matched_rows)
    return matched_df, unmatched


def collect_all_activities(popular_places_path=POPULAR_PLACES_PATH, area_code=None):
    """
    전 지역 순회가 아니라, "영어권 인기관광지" 리스트로 좁힌 장소만 조회.
    자동 매칭 실패 건은 데이터프레임으로 같이 반환 (수기 큐레이션용 템플릿 작성에 사용).
    """
    popular_places = load_popular_places(popular_places_path)
    matched_df, unmatched = resolve_content_ids(popular_places, area_code=area_code)
    unmatched_df = pd.DataFrame(unmatched)

    if unmatched:
        print(f"[경고] {len(unmatched)}건 contentId 매칭 실패: {[u['english_name'] for u in unmatched]}")

    return matched_df, unmatched_df


if __name__ == "__main__":
    result_df, unmatched_df = collect_all_activities()
    result_df.to_csv("data/activities_raw.csv", index=False, encoding="utf-8-sig")

    if not unmatched_df.empty:
        # 사람이 직접 찾아서 채워 넣을 빈 컬럼들을 붙여 템플릿으로 저장.
        # manual_lookup.py로 후보를 찾은 뒤, contentid/title/addr1/lclsSystm1~3을 수기로 채워넣으면
        # merge_manual_overrides.py가 이 값들을 activities_raw.csv에 합쳐준다.
        for col in ["contentid", "contenttypeid", "title", "addr1", "lclsSystm1", "lclsSystm2", "lclsSystm3", "note"]:
            unmatched_df[col] = ""
        unmatched_df.to_csv("data/unmatched_for_manual_review.csv", index=False, encoding="utf-8-sig")
        print(f"수기 검토 템플릿 저장: data/unmatched_for_manual_review.csv ({len(unmatched_df)}건)")

    print(f"조회 대상: {len(load_popular_places())}건, 자동 매칭 성공: {len(result_df)}건")
