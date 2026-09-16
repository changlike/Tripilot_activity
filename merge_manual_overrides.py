# merge_manual_overrides.py
# data/unmatched_for_manual_review.csv에서 사람이 직접 contentid 등을 채워 넣은 행들을
# data/activities_raw.csv(자동 매칭 결과)에 합쳐서 최종본을 만든다.

import pandas as pd

AUTO_PATH = "data/activities_raw.csv"
REVIEW_PATH = "data/unmatched_for_manual_review.csv"
OUT_PATH = "data/activities_raw.csv"  # 같은 파일에 덮어씀 (자동+수기 합본)


def merge():
    auto_df = pd.read_csv(AUTO_PATH, encoding="utf-8-sig")
    review_df = pd.read_csv(REVIEW_PATH, encoding="utf-8-sig")

    # contentid가 채워진 행만 "수기 확정"으로 간주
    filled = review_df[review_df["contentid"].notna() & (review_df["contentid"].astype(str).str.strip() != "")].copy()
    still_empty = review_df[~review_df.index.isin(filled.index)].copy()

    filled["match_type"] = "manual"
    filled["match_keyword"] = ""

    cols = [c for c in auto_df.columns]
    filled = filled.reindex(columns=cols, fill_value="")

    merged = pd.concat([auto_df, filled], ignore_index=True)
    merged.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    still_empty.to_csv(REVIEW_PATH, index=False, encoding="utf-8-sig")

    print(f"수기 확정 {len(filled)}건 병합 -> {OUT_PATH} (총 {len(merged)}건)")
    print(f"아직 미확정: {len(still_empty)}건 (data/unmatched_for_manual_review.csv에 남아있음)")


if __name__ == "__main__":
    merge()
