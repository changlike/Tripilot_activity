# preprocess_activities.py
# tour_api_collect.py가 만든 data/activities_raw.csv를 정제해 activities 테이블용으로 다듬는다.
# 카테고리 재태깅(신체계 lclsSystm -> Tripilot 내부 카테고리) 매핑표는 아직 팀 확정 전이라
# 이 단계에서는 결측치 처리 / 중복 제거까지만 수행한다.

import pandas as pd

RAW_PATH = "data/activities_raw.csv"
OUT_PATH = "data/activities_clean.csv"

REQUIRED_FIELDS = ["contentid", "title", "addr1"]

# dtype=str + keep_default_na=False: contentid 같은 숫자열이 float(.0)로 승격되거나
# lclsSystm1="NA"(자연 코드)가 pandas 기본 결측 문자열과 겹쳐 사라지는 걸 막기 위함.
READ_KW = dict(encoding="utf-8-sig", dtype=str, keep_default_na=False, na_filter=False)


def load_raw(path=RAW_PATH):
    return pd.read_csv(path, **READ_KW)


def drop_missing_required(df: pd.DataFrame):
    """contentid/title/addr1처럼 필수인 필드가 비어 있는 행은 별도로 분리."""
    missing_mask = (df[REQUIRED_FIELDS] == "").any(axis=1)
    return df[~missing_mask].copy(), df[missing_mask].copy()


def drop_duplicate_content(df: pd.DataFrame):
    """서로 다른 후보 장소가 같은 contentId로 매칭된 경우 중복 제거."""
    before = len(df)
    deduped = df.drop_duplicates(subset="contentid", keep="first").copy()
    return deduped, before - len(deduped)


def preprocess(path=RAW_PATH):
    raw_df = load_raw(path)
    clean_df, missing_df = drop_missing_required(raw_df)
    clean_df, dup_count = drop_duplicate_content(clean_df)

    stats = {
        "원본 건수": len(raw_df),
        "필수값 결측 제외": len(missing_df),
        "contentId 중복 제외": dup_count,
        "최종 건수": len(clean_df),
    }
    return clean_df, missing_df, stats


if __name__ == "__main__":
    clean_df, missing_df, stats = preprocess()
    clean_df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    for k, v in stats.items():
        print(f"{k}: {v}")
