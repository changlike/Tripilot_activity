# debug_search.py
# 매칭 실패한 키워드 몇 개를 다른 방식으로 찔러봐서 원인을 확인하는 진단용 스크립트.
# (API 호출 아끼려고 실패 목록 중 대표적인 몇 개만 테스트)

from tour_api_collect import search_keyword2, to_dataframe

# 실패했던 것 중 "당연히 TourAPI에 있어야 할" 초유명 관광지 위주로 선정
CASES = [
    "남산서울타워",
    "스타필드 코엑스몰",
    "망원시장",
    "광화문광장",
]


def try_case(keyword):
    print(f"\n=== '{keyword}' ===")

    # 1) 원래 그대로 + areaCode=1
    r1 = to_dataframe(search_keyword2(keyword, area_code="1"))
    print(f"  areaCode=1        : {len(r1)}건", list(r1["title"]) if not r1.empty else "")

    # 2) areaCode 제거
    r2 = to_dataframe(search_keyword2(keyword, area_code=None))
    print(f"  areaCode 없음      : {len(r2)}건", list(r2["title"]) if not r2.empty else "")

    # 3) 공백 제거
    keyword_nospace = keyword.replace(" ", "")
    if keyword_nospace != keyword:
        r3 = to_dataframe(search_keyword2(keyword_nospace, area_code="1"))
        print(f"  공백제거 '{keyword_nospace}': {len(r3)}건", list(r3["title"]) if not r3.empty else "")


if __name__ == "__main__":
    for c in CASES:
        try_case(c)
