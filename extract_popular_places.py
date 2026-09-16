# extract_popular_places.py
# 데이터랩 "외국인 관심 관광지_영어권" 원본에서 상위 장소 리스트를 추출한다.
# TourAPI 호출 범위를 이 리스트로 좁히기 위한 전 단계 스크립트.

import re
import pandas as pd

SRC_PATH = "data/20260916164304_외국인 관심 관광지/20260916164304_외국인 관심 관광지_영어권.csv"
OUT_PATH = "data/popular_places_seoul_en.csv"

# "English Name (한글명)" 형태에서 맨 끝 괄호를 한글명으로 분리.
# 한글명 안에 괄호가 또 중첩된 경우(예: "...(북한산국립공원(서울))")가 있어
# 단순 정규식으로는 잘못 분리되므로, 끝에서부터 괄호 짝을 맞춰 찾는다.


def split_name(raw_name: str):
    s = raw_name.strip()
    if s.endswith(")"):
        depth = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ")":
                depth += 1
            elif s[i] == "(":
                depth -= 1
                if depth == 0:
                    return s[:i].strip(), s[i + 1:-1].strip()
    # 괄호 형식이 아닌 예외 케이스 ("Harmony Mart ... / 하모니마트 ...")
    if "/" in s:
        en, kr = s.split("/", 1)
        return en.strip(), kr.strip()
    return s, None


def extract_popular_places(src_path: str = SRC_PATH) -> pd.DataFrame:
    df = pd.read_csv(src_path, encoding="utf-8-sig")

    names_split = df["관광지명"].apply(split_name)
    df["english_name"] = names_split.apply(lambda t: t[0])
    df["korean_name"] = names_split.apply(lambda t: t[1])

    grouped = (
        df.groupby(["english_name", "korean_name"])["구분"]
        .apply(lambda s: ";".join(sorted(set(s))))
        .reset_index()
        .rename(columns={"구분": "raw_categories"})
    )
    grouped["raw_category_count"] = grouped["raw_categories"].str.split(";").apply(len)
    grouped = grouped.sort_values("english_name").reset_index(drop=True)
    return grouped


if __name__ == "__main__":
    raw_df = pd.read_csv(SRC_PATH, encoding="utf-8-sig")
    result = extract_popular_places()
    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"원본 행 수: {len(raw_df)}")
    print(f"고유 장소 수: {len(result)}")
    print(f"이름 파싱 실패(한글명 없음): {result['korean_name'].isna().sum()}건")
    print(f"저장 위치: {OUT_PATH}")
