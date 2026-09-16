# manual_lookup.py
# 자동 매칭에 실패한 장소를 사람이 직접 찾기 위한 조회 도구.
# 코드가 후보를 판단해서 고르지 않고, 후보 목록을 보여주기만 함 — 선택은 사람이 함.
#
# 사용법:
#   ./.venv/Scripts/python.exe manual_lookup.py <검색어>
#   예) ./.venv/Scripts/python.exe manual_lookup.py 리움미술관

import sys

from tour_api_collect import search_keyword2, to_dataframe

DISPLAY_COLUMNS = ["contentid", "contenttypeid", "title", "addr1", "lclsSystm1", "lclsSystm2", "lclsSystm3"]


def lookup(keyword: str):
    response = search_keyword2(keyword)
    df = to_dataframe(response)

    if df.empty:
        print(f"'{keyword}' 검색 결과 없음")
        return

    cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    print(f"'{keyword}' 검색 결과 {len(df)}건:\n")
    print(df[cols].to_string(index=False))
    print(
        "\n원하는 항목의 contentid/title/addr1/lclsSystm1/lclsSystm2/lclsSystm3 값을 "
        "data/unmatched_for_manual_review.csv에 직접 채워 넣으세요."
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: manual_lookup.py <검색어>  (예: manual_lookup.py 리움미술관)")
    else:
        lookup(" ".join(sys.argv[1:]))
