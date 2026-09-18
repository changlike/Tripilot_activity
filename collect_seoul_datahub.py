# collect_seoul_datahub.py
# 서울 데이터 허브 "웰컴 투 서울, 관광지 분석"(https://data.seoul.go.kr/bsp/wgs/theme/detail/9.do)
# 대시보드가 내부적으로 호출하는 공개 JSON API를 그대로 호출해 CSV로 저장한다.
# 로그인/서비스키 불필요 (브라우저 Network 탭에서 확인한 그대로의 GET 요청).

import csv
import time
import requests

BASE_URL = "https://data.seoul.go.kr/bsp/wgs/theme/data/9/2"

# 지금은 액티비티 에이전트가 다루는 5개 권역만 수집한다.
# 전체 118개 관광지 목록이 필요해지면 base-data 엔드포인트로 목록을 받아
# 이 리스트 대신 순회하면 된다: GET .../theme/base-data/9?crtr_yr=YYYY&crtr_mm=MM
TARGET_PLACES = [
    ("관광특구", "홍대 관광특구"),
    ("관광특구", "명동 관광특구"),
    ("발달상권", "성수카페거리"),
    ("고궁·문화유산", "경복궁"),
    ("관광특구", "잠실 관광특구"),
]

DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
AGE_KEYS = ["tenage_belo", "twenty", "thirty", "forty", "ffty", "sxty_abov"]
SIDO_KEYS = [
    "seoul", "gyeonggi", "incheon", "gangwon", "sejong", "daejeon", "chungnam", "chungbuk",
    "jeonbuk", "jeonnam", "gwangju", "gyeonbuk", "gyeonnam", "daegu", "busan", "ulsan", "jeju",
]


def fetch(tour_area_ctgry: str, tour_area_nm: str, crtr_yr: str, crtr_mm: str) -> dict:
    params = {
        "crtr_yr": crtr_yr,
        "crtr_mm": crtr_mm,
        "tour_area_ctgry": tour_area_ctgry,
        "tour_area_nm": tour_area_nm,
    }
    res = requests.get(BASE_URL, params=params, timeout=10)
    res.raise_for_status()
    return res.json()["data"]


def collect(crtr_yr="2026", crtr_mm="07", places=TARGET_PLACES, sleep_sec=0.3):
    summary_rows = []
    nationality_rows = []
    monthly_trend_rows = []

    for ctgry, nm in places:
        data = fetch(ctgry, nm, crtr_yr, crtr_mm)

        vst = data.get("TourCtgrySeoulNativeFrgnrVstCnt", [{}])[0]
        age = data.get("TourCtgrySeoulAgegrdVstCnt", [{}])[0]
        day = data.get("TourCtgrySeoulDayVstRt", [{}])[0]
        area = data.get("TourCtgrySeoulAreaVstRt", [{}])[0]

        row = {
            "장소명": nm,
            "카테고리": ctgry,
            "기준연도": crtr_yr,
            "기준월": crtr_mm,
            "내국인_방문객수": vst.get("native_vst_cnt"),
            "내국인_전년동월": vst.get("native_prvyy_vst_cnt"),
            "내국인_증감률": vst.get("native_icrndcr_rt"),
            "외국인_방문객수": vst.get("frgnr_vst_cnt"),
            "외국인_전년동월": vst.get("frgnr_prvyy_vst_cnt"),
            "외국인_증감률": vst.get("frgnr_icrndcr_rt"),
        }
        # 연령대별 방문객수 (주의: 단기 외국인은 제외된 값 — 내국인+장기체류 외국인 기준)
        for k in AGE_KEYS:
            row[f"연령_{k}_방문객수"] = age.get(f"{k}_vst_cnt")
        # 요일별 방문 비율
        for k in DAY_KEYS:
            row[f"요일_{k}_비율"] = day.get(f"{k}_vst_rt")
        row["전체방문자수(요일집계기준)"] = day.get("all_vst_cnt")
        # 방문객 출신 시도 비율
        for k in SIDO_KEYS:
            row[f"출신시도_{k}_비율"] = area.get(f"{k}_vst_rt")
        summary_rows.append(row)

        # 국적별 x 시간대별 체류인구 (장소당 수백 행 — 별도 롱포맷 테이블로 저장)
        for r in data.get("TourCtgryFrgnrStayTmznAgeDstb", []):
            nationality_rows.append({
                "장소명": nm,
                "카테고리": ctgry,
                "기준연도": crtr_yr,
                "기준월": crtr_mm,
                "국적명": r.get("nlty_nm"),
                "체류시작시간대": r.get("stay_bgng_time"),
                "체류인구수": r.get("stay_popl_cnt"),
            })

        # 월별 방문자수 추이 (최근 12개월)
        for r in data.get("TourCtgrySeoulMmnlyVstCntIcrndcrRt", []):
            monthly_trend_rows.append({
                "장소명": nm,
                "카테고리": ctgry,
                "연도": r.get("crtr_yr"),
                "월": r.get("crtr_mm"),
                "방문자수": r.get("vst_cnt"),
                "전년동월대비증감률": r.get("vst_icrndcr_rt"),
            })

        time.sleep(sleep_sec)

    return summary_rows, nationality_rows, monthly_trend_rows


def save_csv(rows, path):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    summary, nationality, monthly = collect()

    save_csv(summary, "data/seoul_datahub_summary.csv")
    save_csv(nationality, "data/seoul_datahub_nationality_time.csv")
    save_csv(monthly, "data/seoul_datahub_monthly_trend.csv")

    print(f"summary: {len(summary)}행 -> data/seoul_datahub_summary.csv")
    print(f"nationality_time: {len(nationality)}행 -> data/seoul_datahub_nationality_time.csv")
    print(f"monthly_trend: {len(monthly)}행 -> data/seoul_datahub_monthly_trend.csv")
