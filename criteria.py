# =====================================================================
# criteria.py  -  건강검진 결과 해석 도우미의 "기준값과 판정 규칙" 파일
# =====================================================================
# 이 파일은 화면(streamlit)과 상관없는 순수 파이썬 파일입니다.
# app.py(화면)와 test_criteria.py(자동 검사)가 "import criteria"로 불러 씁니다.
#
# [이 파일의 구성 순서]
#   1. LEVEL_LABELS : 판정 단계 이름(normal/caution/danger -> 정상/주의/위험)
#   2. CRITERIA     : 항목별 판정 기준 숫자와 출처
#   3. LIMITS       : 입력 허용 범위 (벗어나면 판정하지 않고 "입력 오류")
#                     + 단위 착오 안내(UNIT_HINT_ITEMS, UNIT_HINT_TEXT)
#   4. TEXTS        : 항목별·판정별 설명과 생활습관 팁, 빠른 진료 문구,
#                     대사증후군 문구(아직 화면에 쓰지 않음), 다음 행동 문구
#   5. GLOSSARY     : 용어 설명 (팀의 [용어] 표 그대로)
#   6. 함수들       : 입력 검사(validate_input), 대상자 확인(check_eligibility),
#                     항목별 판정(judge_bmi ~ judge_tg), 대사증후군 체크(judge_mets)
#                     내 수치 위치 막대 정보(position_info)
#   7. 맨 아래      : 이 파일을 직접 실행했을 때 예시 판정 결과 출력
#
# [판정 경계 규칙 - 모든 항목 공통]
#   모든 구간은 "A 이상 B 미만"입니다.
#   예) 정상 70 이상 100 미만 -> 70은 정상, 100은 다음 구간(주의)
#   코드에서는 min(이상)과 max(미만)로 적고, None은 "끝이 없음"을 뜻합니다.
#
# [판정 결과(dict)의 모양 - 모든 judge_ 함수 공통]
#   item      : 항목 이름 (예: "공복혈당")
#   value     : 판정에 쓴 값 (혈압은 (수축기, 이완기) 묶음)
#   level     : "normal" / "caution" / "danger"  (판정하지 않았으면 None)
#   label     : "정상" / "주의" / "위험"           (판정하지 않았으면 "판정 안 함")
#   sub_label : 자세한 구분 (예: "공복혈당장애 범위")
#   urgent    : 빨리 진료가 필요한 수치이면 True
#   source    : 기준의 출처
#
# ※ 교육용 수업 과제이며 실제 진단 도구가 아닙니다.
# =====================================================================

import math                                   # 숫자가 정상적인 값인지 확인할 때 사용
from decimal import Decimal, ROUND_HALF_UP    # BMI를 정확하게 반올림할 때 사용


# ---------------------------------------------------------------------
# 1. 판정 단계 이름
# ---------------------------------------------------------------------
LEVEL_LABELS = {
    "normal": "정상",
    "caution": "주의",
    "danger": "위험",
}


# ---------------------------------------------------------------------
# 2. CRITERIA : 판정 기준
# ---------------------------------------------------------------------
# ranges 안의 한 줄 = 한 구간
#   min       : 이 값 "이상" (None이면 아래쪽 끝이 없음)
#   max       : 이 값 "미만" (None이면 위쪽 끝이 없음)
#   level     : 판정 단계
#   sub_label : 자세한 구분
# urgent_from : 이 값 "이상"이면 urgent=True
CRITERIA = {
    "bmi": {
        "name": "체질량지수(BMI)",
        "unit": "kg/m²",
        "source": "대한비만학회 비만 진료지침 2022",
        "ranges": [
            {"min": None, "max": 18.5, "level": "caution", "sub_label": "저체중"},
            {"min": 18.5, "max": 23,   "level": "normal",  "sub_label": "정상 범위"},
            {"min": 23,   "max": 25,   "level": "caution", "sub_label": "비만 전단계"},
            {"min": 25,   "max": None, "level": "danger",  "sub_label": "비만"},
        ],
    },
    "waist": {
        "name": "허리둘레",
        "unit": "cm",
        "source": "대한비만학회 비만 진료지침 2022",
        # 허리둘레는 성별에 따라 기준이 다릅니다.
        "ranges_by_sex": {
            "남": [
                {"min": None, "max": 90,   "level": "normal",  "sub_label": "정상 범위"},
                {"min": 90,   "max": None, "level": "caution", "sub_label": "복부비만"},
            ],
            "여": [
                {"min": None, "max": 85,   "level": "normal",  "sub_label": "정상 범위"},
                {"min": 85,   "max": None, "level": "caution", "sub_label": "복부비만"},
            ],
        },
    },
    "bp": {
        "name": "혈압",
        "unit": "mmHg",
        "source": "대한고혈압학회 고혈압 진료지침 2026",
        # 혈압은 수축기·이완기 두 숫자를 함께 보므로 구간표 대신 아래처럼 적습니다.
        # 정상: 수축기 120 미만 "그리고" 이완기 80 미만
        "normal_below": {"sbp": 120, "dbp": 80},
        # 위험(고혈압 범위): 수축기 140 이상 "또는" 이완기 90 이상
        "danger_from": {"sbp": 140, "dbp": 90},
        # urgent: 수축기 180 이상 "또는" 이완기 110 이상
        "urgent_from": {"sbp": 180, "dbp": 110},
        # 그 밖의 경우는 모두 주의
        "sub_labels": {
            "normal": "정상 범위",
            "caution": "정상보다 높은 범위",
            "danger": "고혈압 범위",
        },
    },
    "glucose": {
        "name": "공복혈당",
        "unit": "mg/dL",
        "source": "대한당뇨병학회 당뇨병 진료지침 2025",
        "ranges": [
            {"min": None, "max": 70,   "level": "caution", "sub_label": "저혈당 범위"},
            {"min": 70,   "max": 100,  "level": "normal",  "sub_label": "정상 범위"},
            {"min": 100,  "max": 126,  "level": "caution", "sub_label": "공복혈당장애 범위"},
            {"min": 126,  "max": None, "level": "danger",  "sub_label": "당뇨병 범위"},
        ],
    },
    "tc": {
        "name": "총콜레스테롤",
        "unit": "mg/dL",
        "source": "한국지질·동맥경화학회 이상지질혈증 진료지침 제5판(2022)",
        "ranges": [
            {"min": None, "max": 200,  "level": "normal",  "sub_label": "정상 범위"},
            {"min": 200,  "max": 240,  "level": "caution", "sub_label": "경계 범위"},
            {"min": 240,  "max": None, "level": "danger",  "sub_label": "높은 범위"},
        ],
    },
    "ldl": {
        "name": "LDL 콜레스테롤",
        "unit": "mg/dL",
        "source": "한국지질·동맥경화학회 이상지질혈증 진료지침 제5판(2022)",
        "ranges": [
            {"min": None, "max": 130,  "level": "normal",  "sub_label": "정상 범위"},
            {"min": 130,  "max": 160,  "level": "caution", "sub_label": "경계 범위"},
            {"min": 160,  "max": None, "level": "danger",  "sub_label": "높은 범위"},
        ],
        "urgent_from": 190,
    },
    "hdl": {
        "name": "HDL 콜레스테롤",
        "unit": "mg/dL",
        "source": "한국지질·동맥경화학회 이상지질혈증 진료지침 제5판(2022)",
        "ranges": [
            {"min": None, "max": 40,   "level": "danger",  "sub_label": "낮은 범위"},
            {"min": 40,   "max": None, "level": "normal",  "sub_label": "정상 범위"},
        ],
    },
    "tg": {
        "name": "중성지방",
        "unit": "mg/dL",
        "source": "한국지질·동맥경화학회 이상지질혈증 진료지침 제5판(2022)",
        "ranges": [
            {"min": None, "max": 150,  "level": "normal",  "sub_label": "정상 범위"},
            {"min": 150,  "max": 200,  "level": "caution", "sub_label": "경계 범위"},
            {"min": 200,  "max": None, "level": "danger",  "sub_label": "높은 범위"},
        ],
        "urgent_from": 500,
    },
    # 대사증후군 체크: 아래 5개 기준 중 3개 이상이면 "대사증후군 의심"
    # (경계 규칙은 다른 항목과 같이 "이상"/"미만"만 씁니다)
    "mets": {
        "name": "대사증후군",
        "source": "AHA/NHLBI 대사증후군 진단 기준(Grundy 등, 2005) 및 대한비만학회 한국인 복부비만 허리둘레 기준",
        "need_count": 3,                       # 이 개수 이상 해당하면 "의심"
        "waist_from": {"남": 90, "여": 85},    # 허리둘레 이상
        "sbp_from": 130,                       # 수축기 혈압 이상  (둘 중 하나라도)
        "dbp_from": 85,                        # 이완기 혈압 이상
        "glucose_from": 100,                   # 공복혈당 이상
        "tg_from": 150,                        # 중성지방 이상
        "hdl_below": {"남": 40, "여": 50},     # HDL 미만 (여성 기준이 HDL 카드와 다름)
    },
}


# ---------------------------------------------------------------------
# 3. LIMITS : 입력 허용 범위
# ---------------------------------------------------------------------
# 이 범위는 "판정 기준"이 아니라 "입력 실수를 걸러내는 범위"입니다.
# 그래서 양쪽 끝을 모두 포함합니다. (min 이상 max 이하)
# 예) 나이 19~120 -> 19와 120 모두 입력 가능
LIMITS = {
    "age":     {"name": "나이",           "min": 19,  "max": 120,  "unit": "세"},
    "height":  {"name": "키",             "min": 100, "max": 230,  "unit": "cm"},
    "weight":  {"name": "몸무게",         "min": 25,  "max": 300,  "unit": "kg"},
    "waist":   {"name": "허리둘레",       "min": 40,  "max": 200,  "unit": "cm"},
    "sbp":     {"name": "수축기 혈압",    "min": 60,  "max": 300,  "unit": "mmHg"},
    "dbp":     {"name": "이완기 혈압",    "min": 30,  "max": 200,  "unit": "mmHg"},
    "glucose": {"name": "공복혈당",       "min": 20,  "max": 600,  "unit": "mg/dL"},
    "tc":      {"name": "총콜레스테롤",   "min": 50,  "max": 700,  "unit": "mg/dL"},
    "ldl":     {"name": "LDL 콜레스테롤", "min": 10,  "max": 500,  "unit": "mg/dL"},
    "hdl":     {"name": "HDL 콜레스테롤", "min": 5,   "max": 200,  "unit": "mg/dL"},
    "tg":      {"name": "중성지방",       "min": 10,  "max": 5000, "unit": "mg/dL"},
}

# 단위 착오 안내
# 아래 항목에 "허용 범위보다 작은 값"(0보다는 큰 값)이 들어오면
# mmol/L 단위로 잘못 입력했을 가능성이 있어 안내 문구를 덧붙입니다.
# (새 기준 숫자 없이 위 LIMITS의 최솟값만 그대로 씁니다)
UNIT_HINT_ITEMS = ["glucose", "tc", "ldl", "hdl", "tg"]
UNIT_HINT_TEXT = "mmol/L 단위로 입력하신 것 같습니다. 결과지의 mg/dL 값을 입력해 주세요."


# ---------------------------------------------------------------------
# 4. TEXTS : 화면에 보여 줄 문구
# ---------------------------------------------------------------------
# TEXTS[항목][sub_label] = {"explain": 설명, "tip": 생활습관 팁}
# sub_label을 열쇠로 쓰는 이유: 같은 "주의"라도
# 저체중과 비만 전단계처럼 설명이 달라야 하기 때문입니다.
# 문구는 팀의 [문구] 표 그대로입니다.
# 단, 9·10번 혈압 문구(설명·팁)는 "수축기 또는 이완기"가 분명히 드러나도록 표현만 고쳤습니다. (기준 숫자는 같음)
# 각 문구 위의 "출처" 주석은 [문구] 표의 출처 칸입니다. 화면에는 표시하지 않습니다.
TEXTS = {
    "bmi": {
        # [문구] 1번 / 출처: 비만 진료지침 2022 p.123 (Table 2)
        "저체중": {
            "explain": "BMI가 18.5 미만으로 저체중 범위에 해당합니다. 키에 비해 몸무게가 적은 편이라는 뜻입니다.",
            "tip": "끼니를 거르지 말고 골고루 먹는 것이 좋습니다.",
        },
        # [문구] 2번 / 출처: 비만 진료지침 2022 p.123 (Table 2), 운동 p.3 (R4-2, J Obes Metab Syndr 2023;32:1-24)
        "정상 범위": {
            "explain": "BMI가 18.5~22.9로 정상 범위에 해당합니다. 키에 비해 몸무게가 알맞다는 뜻입니다.",
            "tip": "지금처럼 규칙적으로 운동하며 체중을 유지하는 것이 좋습니다.",
        },
        # [문구] 3번 / 출처: 비만 진료지침 2022 p.123 (Table 2), 운동 p.3 (R4-2, J Obes Metab Syndr 2023;32:1-24)
        "비만 전단계": {
            "explain": "BMI가 23~24.9로 비만 전단계에 해당합니다. 체중과 관련된 질환 위험이 늘기 시작하는 구간이라는 뜻입니다.",
            "tip": "유산소 운동을 일주일에 150분 이상 하는 것이 좋습니다.",
        },
        # [문구] 4번 / 출처: 비만 진료지침 2022 p.123 (Table 2), 운동 p.3 (R4-2, J Obes Metab Syndr 2023;32:1-24)
        "비만": {
            "explain": "BMI가 25 이상으로 비만 범위에 해당합니다. 당뇨병, 고혈압 같은 질환 위험이 높아질 수 있다는 뜻입니다.",
            "tip": "유산소 운동을 일주일에 150분 이상, 근력 운동을 일주일에 2~3번 하는 것이 좋습니다.",
        },
    },
    "waist": {
        # [문구] 5번 / 출처: 비만 진료지침 2022 p.123 (Table 2), 운동 p.3 (R4-2, J Obes Metab Syndr 2023;32:1-24)
        "정상 범위": {
            "explain": "허리둘레가 남성 90cm, 여성 85cm 미만으로 정상 범위에 해당합니다. 배 주변에 지방이 많이 쌓이지 않았다는 뜻입니다.",
            "tip": "지금처럼 규칙적으로 운동하는 것이 좋습니다.",
        },
        # [문구] 6번 / 출처: 비만 진료지침 2022 p.123 (Table 2), 운동 p.3 (R4-2, J Obes Metab Syndr 2023;32:1-24)
        "복부비만": {
            "explain": "허리둘레가 남성 90cm, 여성 85cm 이상으로 복부비만 범위에 해당합니다. 배 주변에 지방이 많아 대사질환 위험이 높아질 수 있다는 뜻입니다.",
            "tip": "유산소 운동을 일주일에 150분 이상 하는 것이 좋습니다.",
        },
    },
    "bp": {
        # [문구] 7번 / 출처: 고혈압 진료지침 2026 p.4/21 (Table 1), 생활요법 p.11/21
        "정상 범위": {
            "explain": "혈압이 120/80 미만으로 정상 범위에 해당합니다. 심뇌혈관질환 위험이 가장 낮은 혈압이라는 뜻입니다.",
            "tip": "싱겁게 먹는 습관을 유지하는 것이 좋습니다.",
        },
        # [문구] 8번 / 출처: 고혈압 진료지침 2026 p.4/21 (Table 1), 생활요법 p.11/21
        "정상보다 높은 범위": {
            "explain": "혈압이 정상보다 조금 높은 주의 범위에 해당합니다. 아직 고혈압은 아니지만 관리가 필요하다는 뜻입니다.",
            "tip": "음식을 싱겁게 먹고 술을 줄이는 것이 좋습니다.",
        },
        # [문구] 9번 / 출처: 고혈압 진료지침 2026 p.4/21 (Table 1), 생활요법 p.11/21
        "고혈압 범위": {
            "explain": "혈압이 수축기 140 이상 또는 이완기 90 이상으로 고혈압 범위에 해당합니다. 혈압 관리가 필요하다는 뜻입니다.",
            "tip": "소금과 술을 줄이고 규칙적으로 운동하는 것이 좋습니다.",
        },
    },
    "glucose": {
        # [문구] 11번 / 출처: 당뇨병 진료지침 2025 Suppl. Table 5 (저혈당 분류)
        "저혈당 범위": {
            "explain": "공복혈당이 70 미만으로 낮은 범위에 해당합니다. 어지럼이나 식은땀 같은 저혈당 증상이 나타날 수 있는 수치라는 뜻입니다.",
            "tip": "끼니를 거르지 않는 것이 좋습니다.",
        },
        # [문구] 12번 / 출처: 당뇨병 진료지침 2025 p.584 (Table 1), 예방 권고 p.590
        "정상 범위": {
            "explain": "공복혈당이 100 미만으로 정상 범위에 해당합니다. 혈당이 잘 유지되고 있다는 뜻입니다.",
            "tip": "지금처럼 규칙적으로 운동하는 것이 좋습니다.",
        },
        # [문구] 13번 / 출처: 당뇨병 진료지침 2025 p.584 (Table 1), 예방 권고 p.590
        "공복혈당장애 범위": {
            "explain": "공복혈당이 100~125로 공복혈당장애(당뇨병 전단계) 범위에 해당합니다. 당뇨병으로 진행할 가능성이 있다는 뜻입니다.",
            "tip": "중간 강도 운동을 일주일에 150분 이상 하고, 과체중이면 체중을 5% 이상 줄이는 것이 좋습니다.",
        },
        # [문구] 14번 / 출처: 당뇨병 진료지침 2025 p.584 (Table 1), 예방 권고 p.590
        "당뇨병 범위": {
            "explain": "공복혈당이 126 이상으로 당뇨병 범위에 해당합니다. 당뇨병인지는 다른 날 다시 검사해서 확인한다는 뜻입니다.",
            "tip": "진료를 받아 다시 검사하고, 중간 강도 운동을 일주일에 150분 이상 하는 것이 좋습니다.",
        },
    },
    "tc": {
        # [문구] 15번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 식사요법 p.55
        "정상 범위": {
            "explain": "총콜레스테롤이 200 미만으로 적정 범위에 해당합니다. 혈액 속 콜레스테롤의 전체 양이 알맞다는 뜻입니다.",
            "tip": "기름진 고기 같은 포화지방을 적게 먹는 습관을 유지하는 것이 좋습니다.",
        },
        # [문구] 16번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 포화지방 p.56
        "경계 범위": {
            "explain": "총콜레스테롤이 200~239로 경계 범위에 해당합니다. 콜레스테롤이 조금 높은 편이라는 뜻입니다.",
            "tip": "기름진 고기, 버터 같은 포화지방을 줄이는 것이 좋습니다.",
        },
        # [문구] 17번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.56~57
        "높은 범위": {
            "explain": "총콜레스테롤이 240 이상으로 높은 범위에 해당합니다. 혈관 건강을 위해 관리가 필요하다는 뜻입니다.",
            "tip": "포화지방을 줄이고 트랜스지방은 피하는 것이 좋습니다.",
        },
    },
    "ldl": {
        # [문구] 18번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 식이섬유 p.58
        "정상 범위": {
            "explain": "LDL 콜레스테롤이 130 미만으로 정상 범위에 해당합니다. 혈관에 쌓이기 쉬운 콜레스테롤이 알맞다는 뜻입니다.",
            "tip": "채소와 통곡물로 식이섬유를 충분히 먹는 것이 좋습니다.",
        },
        # [문구] 19번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.56, p.58
        "경계 범위": {
            "explain": "LDL 콜레스테롤이 130~159로 경계 범위에 해당합니다. 나쁜 콜레스테롤이 조금 높은 편이라는 뜻입니다.",
            "tip": "포화지방을 줄이고 식이섬유를 하루 25g 이상 먹는 것이 좋습니다.",
        },
        # [문구] 20번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.56~57
        "높은 범위": {
            "explain": "LDL 콜레스테롤이 160 이상으로 높은 범위에 해당합니다. 혈관 건강을 위해 관리가 필요하다는 뜻입니다.",
            "tip": "포화지방을 줄이고 트랜스지방은 피하는 것이 좋습니다.",
        },
    },
    "hdl": {
        # [문구] 23번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 운동요법 p.68, 금연 p.76
        "낮은 범위": {
            "explain": "HDL 콜레스테롤이 40 미만으로 낮은 범위에 해당합니다. 혈관을 보호하는 좋은 콜레스테롤이 부족하다는 뜻입니다.",
            "tip": "규칙적으로 운동하고, 담배를 피운다면 끊는 것이 좋습니다.",
        },
        # [문구] 22번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 운동요법 p.68
        "정상 범위": {
            "explain": "HDL 콜레스테롤이 40 이상으로 정상 범위에 해당합니다. 혈관을 보호하는 좋은 콜레스테롤이 충분하다는 뜻입니다.",
            "tip": "지금처럼 규칙적으로 운동하는 것이 좋습니다.",
        },
    },
    "tg": {
        # [문구] 24번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.60~61
        "정상 범위": {
            "explain": "중성지방이 150 미만으로 적정 범위에 해당합니다. 혈액 속 지방이 알맞다는 뜻입니다.",
            "tip": "단 음식과 술을 적게 먹는 습관을 유지하는 것이 좋습니다.",
        },
        # [문구] 25번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 탄수화물·당류 p.60
        "경계 범위": {
            "explain": "중성지방이 150~199로 경계 범위에 해당합니다. 혈액 속 지방이 조금 높은 편이라는 뜻입니다.",
            "tip": "밥, 빵 같은 탄수화물과 단 음식을 줄이는 것이 좋습니다.",
        },
        # [문구] 26번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.60~61
        "높은 범위": {
            "explain": "중성지방이 200 이상으로 높은 범위에 해당합니다. 혈관 건강을 위해 관리가 필요하다는 뜻입니다.",
            "tip": "단 음식을 줄이고, 술은 하루 1~2잔 이내로 줄이거나 가급적 끊는 것이 좋습니다.",
        },
    },

    # 빠른 진료(urgent) 문구: TEXTS["urgent"][항목]
    # urgent일 때 카드의 설명 뒤에 "explain"을 덧붙여 보여 줍니다.
    # urgent일 때는 일반 판정의 팁 대신 이 "tip"을 보여 줍니다.
    "urgent": {
        # [문구] 10번 / 출처: 고혈압 진료지침 2026 p.4/21 (Table 1), p.8/21 (180/110 기준)
        "bp": {
            "explain": "혈압이 수축기 180 이상 또는 이완기 110 이상으로 매우 높은 범위에 해당합니다. 빨리 진료가 필요하다는 뜻입니다.",
            "tip": "안정한 뒤 다시 재도 수축기 180 이상 또는 이완기 110 이상이면 가능한 빨리 진료를 받는 것이 좋습니다.",
        },
        # [문구] 21번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), p.43 (190 이상 권고), p.56
        "ldl": {
            "explain": "LDL 콜레스테롤이 190 이상으로 매우 높은 범위에 해당합니다. 다른 위험 요인과 상관없이 치료가 권고되는 수치라는 뜻입니다.",
            "tip": "진료를 받고, 포화지방을 줄이는 것이 좋습니다.",
        },
        # [문구] 27번 / 출처: 이상지질혈증 진료지침 제5판 p.33 (표 2-1), 알코올 p.60~61
        "tg": {
            "explain": "중성지방이 500 이상으로 매우 높은 범위에 해당합니다. 빨리 진료가 필요한 수치라는 뜻입니다.",
            "tip": "진료를 받고, 술은 가급적 끊는 것이 좋습니다.",
        },
    },

    # 대사증후군 문구: 대사증후군 기능이 생기면 쓸 수 있도록 넣어만 두었습니다.
    # (지금 화면에는 표시하지 않습니다.)
    "metabolic": {
        # [문구] 28번 / 출처: Grundy 2005 p.2739 (Table 2), 비만 진료지침 2022 p.5 (한국 기준), 운동 p.3 (R4-2)
        "의심": {
            "explain": "대사증후군 기준 5가지 중 3가지 이상에 해당합니다. 심혈관질환과 당뇨병 위험이 함께 높아질 수 있는 상태라는 뜻입니다.",
            "tip": "유산소 운동을 일주일에 150분 이상 하며 해당 항목을 하나씩 줄여 가는 것이 좋습니다.",
        },
        # [문구] 29번 / 출처: Grundy 2005 p.2739 (Table 2)
        "아님": {
            "explain": "대사증후군 기준 5가지 중 해당하는 것이 2가지 이하입니다. 지금은 대사증후군 기준에 해당하지 않는다는 뜻입니다.",
            "tip": "해당하는 항목이 있다면 그 항목부터 관리하는 것이 좋습니다.",
        },
        # [문구] 30번 / 출처: Grundy 2005 p.2739 (Table 2, 5개 중 3개 기준)
        "판정 불가": {
            "explain": "입력하지 않은 항목이 있어 대사증후군 여부를 판단할 수 없습니다. 빈 항목 결과에 따라 판정이 달라질 수 있다는 뜻입니다.",
            "tip": "빈 항목을 모두 입력하면 판정할 수 있습니다.",
        },
    },

    # 다음 행동 문구 (확정 문구)
    "next_action": {
        "caution": "생활습관을 점검하고 다음 검진 때 다시 확인해 보세요.",
        "danger": "의료진과 상담해 보세요.",
        "urgent": "가능한 빨리 의료진의 진료를 받으세요.",
    },
}


# ---------------------------------------------------------------------
# 5. GLOSSARY : 용어 설명 (팀의 [용어] 표 그대로)
# ---------------------------------------------------------------------
# 화면의 입력칸 도움말(?)과 "용어 사전" 펼침 상자에서 씁니다.
# 출처(쪽 번호)는 팀원작업표 [용어] 탭에 적혀 있습니다.
GLOSSARY = {
    # 출처: 대한비만학회 비만 진료지침 2022
    "BMI": "몸무게(kg)를 키(m)의 제곱으로 나눈 값으로, 키에 비해 몸무게가 어느 정도인지 보여 줍니다. 근육이 많은 사람은 실제 체지방보다 높게 나올 수 있어 허리둘레와 함께 봅니다.",
    # 출처: 대한고혈압학회 고혈압 진료지침 2026
    "수축기 혈압": "심장이 수축해 피를 내보낼 때 혈관에 걸리는 압력입니다. 혈압을 ‘120/80’처럼 적을 때 앞의 큰 숫자입니다.",
    # 출처: 대한고혈압학회 고혈압 진료지침 2026
    "이완기 혈압": "심장이 쉬면서 다시 피를 채울 때 혈관에 남아 있는 압력입니다. 혈압을 ‘120/80’처럼 적을 때 뒤의 작은 숫자입니다.",
    # 출처: 대한당뇨병학회 당뇨병 진료지침 2025
    "공복혈당": "8시간 이상 아무것도 먹지 않은 상태에서 잰 혈액 속 포도당 농도입니다. 식사의 영향을 받지 않아 혈당 조절 상태를 보는 기본 검사입니다.",
    # 출처: 한국지질·동맥경화학회 이상지질혈증 진료지침 제5판
    "총콜레스테롤": "혈액 속 콜레스테롤의 전체 양입니다. LDL과 HDL 등 여러 종류의 콜레스테롤이 모두 포함됩니다.",
    # 출처: 한국지질·동맥경화학회 이상지질혈증 진료지침 제5판
    "LDL 콜레스테롤": "콜레스테롤을 혈관 쪽으로 옮기는 물질로, 많으면 혈관 벽에 쌓이기 쉬워 '나쁜 콜레스테롤'이라고 부릅니다. 심장과 뇌혈관 질환 위험과 관련이 깊어 이상지질혈증에서 가장 중요하게 보는 수치입니다.",
    # 출처: 한국지질·동맥경화학회 이상지질혈증 진료지침 제5판
    "HDL 콜레스테롤": "혈관에 남은 콜레스테롤을 간으로 되돌려 보내는 역할을 해 '좋은 콜레스테롤'이라고 부릅니다. 다른 수치와 달리 낮을수록 좋지 않습니다.",
    # 출처: 한국지질·동맥경화학회 이상지질혈증 진료지침 제5판
    "중성지방": "몸에 에너지로 저장되는 지방의 한 형태로, 기름진 음식뿐 아니라 남는 탄수화물과 술로도 만들어집니다. 식사 직후에는 높게 나올 수 있어 공복 상태에서 재는 것이 일반적입니다.",
    # 출처: 대한비만학회 비만 진료지침 2022
    "복부비만": "배 부분에 지방이 많이 쌓인 상태로, 허리둘레로 판단합니다. 한국인은 남성 90cm, 여성 85cm 이상을 기준으로 씁니다.",
    # 출처: Grundy SM 외, Circulation 2005
    "대사증후군": "복부비만, 높은 혈압, 높은 공복혈당, 높은 중성지방, 낮은 HDL 중 여러 가지가 한 사람에게 함께 나타나는 상태입니다. 이 5가지 중 3가지 이상이면 대사증후군 기준에 해당합니다.",
}


# =====================================================================
# 6. 함수들
# =====================================================================

def _is_empty(value):
    """빈칸인지 확인합니다. (None 또는 빈 글자 "")"""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _to_number(value):
    """값을 숫자(float)로 바꿉니다. 바꿀 수 없으면 None을 돌려줍니다."""
    # True/False는 파이썬에서 숫자처럼 취급되므로 따로 막습니다.
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    # "nan"(숫자 아님), "inf"(무한대) 같은 특수한 값도 막습니다.
    if not math.isfinite(number):
        return None
    return number


def validate_input(item, value, systolic=None):
    """
    입력값을 검사합니다.
      item     : LIMITS의 항목 이름 (예: "glucose", "sbp")
      value    : 사용자가 입력한 값
      systolic : 이완기 혈압(dbp)을 검사할 때만, 수축기 혈압 값을 같이 넣습니다.
    돌려주는 값:
      "empty"     -> 빈칸
      "ok"        -> 문제없음
      그 밖의 글자 -> 화면에 보여 줄 오류 메시지
                     (혈당·지질 항목이 허용 범위보다 작으면 단위 착오 안내를 덧붙임)
    """
    if item not in LIMITS:
        return "알 수 없는 항목입니다."

    limit = LIMITS[item]

    if _is_empty(value):
        return "empty"

    number = _to_number(value)
    if number is None:
        return f"{limit['name']}은(는) 숫자로 입력해 주세요."

    # 허용 범위 검사 (min 이상 max 이하)
    if number < limit["min"] or number > limit["max"]:
        message = (f"{limit['name']}은(는) {limit['min']}~{limit['max']} "
                   f"{limit['unit']} 범위로 입력해 주세요.")
        # 단위 착오 안내: 혈당·지질 항목에 허용 범위보다 작은 값(음수·0 제외)
        if item in UNIT_HINT_ITEMS and 0 < number < limit["min"]:
            message += " " + UNIT_HINT_TEXT
        return message

    # 이완기 혈압은 수축기 혈압보다 작아야 합니다.
    if item == "dbp" and not _is_empty(systolic):
        sbp_number = _to_number(systolic)
        if sbp_number is not None and number >= sbp_number:
            return "이완기 혈압은 수축기 혈압보다 작아야 합니다."

    return "ok"


def check_eligibility(age, sex, pregnant):
    """
    판정 대상자인지 확인합니다.
      age      : 나이
      sex      : "남" / "여" / None(선택 안 함)
      pregnant : 임신 중이면 True
    돌려주는 값: {"eligible": True/False, "message": 안내 문구}
    """
    age_check = validate_input("age", age)
    if age_check == "empty":
        return {"eligible": False, "message": "나이를 입력해 주세요."}

    age_number = _to_number(age)
    # 19세 미만은 입력 허용 범위(19~120) 밖이지만, 안내 문구를 따로 보여 줍니다.
    if age_number is not None and age_number < 19:
        return {"eligible": False,
                "message": "이 앱은 19세 이상 성인을 대상으로 합니다. "
                           "19세 미만은 판정하지 않습니다."}

    if age_check != "ok":
        return {"eligible": False, "message": age_check}

    # 임신 여부: 남성으로 선택한 경우가 아니면 확인합니다.
    if pregnant is True and sex != "남":
        return {"eligible": False,
                "message": "임신 중에는 판정 기준이 다를 수 있어 판정하지 않습니다."}

    return {"eligible": True, "message": "판정할 수 있습니다."}


def _find_range(number, ranges):
    """구간표(ranges)에서 숫자가 들어가는 구간을 찾습니다. (A 이상 B 미만)"""
    for r in ranges:
        above_min = (r["min"] is None) or (number >= r["min"])
        below_max = (r["max"] is None) or (number < r["max"])
        if above_min and below_max:
            return r
    return None  # 구간이 빈틈없이 짜여 있으므로 실제로는 여기 오지 않습니다.


def _make_result(key, value, level, sub_label, urgent=False):
    """판정 결과 dict를 만듭니다. 모든 judge_ 함수가 같은 모양을 쓰도록 합니다."""
    return {
        "item": CRITERIA[key]["name"],
        "value": value,
        "level": level,
        "label": LEVEL_LABELS[level] if level else "판정 안 함",
        "sub_label": sub_label,
        "urgent": urgent,
        "source": CRITERIA[key]["source"],
    }


def _judge_by_ranges(key, value):
    """구간표 하나로 판정하는 항목(공복혈당, 지질 4개)에 공통으로 쓰는 함수"""
    number = _to_number(value)
    if number is None:
        return _make_result(key, value, None, "값이 없어 판정하지 않았습니다.")

    r = _find_range(number, CRITERIA[key]["ranges"])

    # urgent 기준이 있는 항목만 확인합니다. (이상)
    urgent_from = CRITERIA[key].get("urgent_from")
    urgent = (urgent_from is not None) and (number >= urgent_from)

    return _make_result(key, number, r["level"], r["sub_label"], urgent)


def calc_bmi(height_cm, weight_kg):
    """BMI를 계산하고 소수 첫째 자리까지 반올림합니다. (예: 22.95 -> 23.0)"""
    height_m = float(height_cm) / 100
    bmi = float(weight_kg) / (height_m * height_m)
    # 파이썬 기본 round()는 0.5를 짝수 쪽으로 반올림하는 특징이 있어서
    # 학교에서 배우는 "사사오입" 방식(ROUND_HALF_UP)으로 반올림합니다.
    return float(Decimal(str(bmi)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def judge_bmi(height_cm, weight_kg):
    """키(cm)와 몸무게(kg)로 BMI를 계산해 판정합니다."""
    if _to_number(height_cm) is None or _to_number(weight_kg) is None:
        return _make_result("bmi", None, None, "키와 몸무게가 모두 있어야 판정합니다.")

    bmi = calc_bmi(height_cm, weight_kg)
    r = _find_range(bmi, CRITERIA["bmi"]["ranges"])
    return _make_result("bmi", bmi, r["level"], r["sub_label"])


def judge_waist(waist_cm, sex):
    """허리둘레(cm)를 성별 기준으로 판정합니다. 성별이 없으면 판정하지 않습니다."""
    number = _to_number(waist_cm)
    if number is None:
        return _make_result("waist", waist_cm, None, "값이 없어 판정하지 않았습니다.")

    ranges_by_sex = CRITERIA["waist"]["ranges_by_sex"]
    if sex not in ranges_by_sex:
        return _make_result("waist", number, None, "성별 정보가 없어 판정하지 않았습니다.")

    r = _find_range(number, ranges_by_sex[sex])
    return _make_result("waist", number, r["level"], r["sub_label"])


def judge_bp(sbp, dbp):
    """수축기·이완기 혈압(mmHg)을 함께 판정합니다. 둘 다 있어야 판정합니다."""
    s = _to_number(sbp)
    d = _to_number(dbp)
    if s is None or d is None:
        return _make_result("bp", (sbp, dbp), None,
                            "수축기와 이완기 혈압이 모두 있어야 판정합니다.")

    c = CRITERIA["bp"]

    # 위험: 수축기 140 이상 "또는" 이완기 90 이상
    if s >= c["danger_from"]["sbp"] or d >= c["danger_from"]["dbp"]:
        level = "danger"
    # 정상: 수축기 120 미만 "그리고" 이완기 80 미만
    elif s < c["normal_below"]["sbp"] and d < c["normal_below"]["dbp"]:
        level = "normal"
    # 나머지: 주의
    else:
        level = "caution"

    # urgent: 수축기 180 이상 "또는" 이완기 110 이상
    urgent = s >= c["urgent_from"]["sbp"] or d >= c["urgent_from"]["dbp"]

    return _make_result("bp", (s, d), level, c["sub_labels"][level], urgent)


def judge_glucose(value):
    """공복혈당(mg/dL)을 판정합니다."""
    return _judge_by_ranges("glucose", value)


def judge_tc(value):
    """총콜레스테롤(mg/dL)을 판정합니다."""
    return _judge_by_ranges("tc", value)


def judge_ldl(value):
    """LDL 콜레스테롤(mg/dL)을 판정합니다. 190 이상이면 urgent=True"""
    return _judge_by_ranges("ldl", value)


def judge_hdl(value):
    """HDL 콜레스테롤(mg/dL)을 판정합니다."""
    return _judge_by_ranges("hdl", value)


def judge_tg(value):
    """중성지방(mg/dL)을 판정합니다. 500 이상이면 urgent=True"""
    return _judge_by_ranges("tg", value)


def _checked_number(item, value, systolic=None):
    """
    대사증후군 체크용: 입력 검사를 통과한 값만 숫자로 돌려줍니다.
    빈칸이거나 입력 오류이면 None(입력 안 된 것으로 처리)을 돌려줍니다.
    """
    if validate_input(item, value, systolic=systolic) != "ok":
        return None
    return float(value)


def judge_mets(waist, sbp, dbp, glucose, tg, hdl, sex):
    """
    대사증후군 기준 5개를 확인합니다.
      waist, sbp, dbp, glucose, tg, hdl : 입력값 (빈칸·입력 오류는 입력 안 된 것으로 처리)
      sex : "남" / "여" / None  (없으면 허리둘레·HDL 기준은 입력 안 된 것으로 처리)

    기준별 결과 met: True(해당) / False(해당 없음) / None(입력 안 됨)

    판정 순서:
      1) 해당 개수가 3개 이상            -> "대사증후군 의심" (빈 기준이 있어도)
      2) 5개 모두 입력됐고 3개 미만      -> "대사증후군 아님"
      3) 그 밖(빈 기준이 있고 3개 미만)  -> "판정 불가"

    돌려주는 값(dict):
      item       : "대사증후군"
      status     : "의심" / "아님" / "판정 불가"  (TEXTS["metabolic"]의 열쇠)
      label      : "대사증후군 의심" / "대사증후군 아님" / "판정 불가"
      met_count  : 해당 개수 n  (n/5로 표시)
      known_count: 입력된 기준 개수 m  (판정 불가일 때 "입력 m/5개"로 표시)
      checks     : 기준 5개의 목록 [{"name", "rule", "met"}]
      urgent     : 항상 False (대사증후군 체크에는 빠른 진료 권고가 없음)
      source     : 출처
    """
    c = CRITERIA["mets"]
    has_sex = sex in ("남", "여")

    w = _checked_number("waist", waist)
    s = _checked_number("sbp", sbp)
    d = _checked_number("dbp", dbp, systolic=sbp)   # 이완기는 수축기보다 작아야 통과
    g = _checked_number("glucose", glucose)
    t = _checked_number("tg", tg)
    h = _checked_number("hdl", hdl)

    # ---- 기준 1: 허리둘레 (성별이 있어야 판단) ----
    if w is None or not has_sex:
        waist_met = None
    else:
        waist_met = w >= c["waist_from"][sex]

    # ---- 기준 2: 혈압 (수축기 130 이상 "또는" 이완기 85 이상) ----
    # 하나라도 기준 이상이면 해당, 둘 다 입력됐고 둘 다 미만이면 해당 없음,
    # 그 밖(한쪽만 입력됐고 그 값이 기준 미만)은 알 수 없으므로 입력 안 됨
    if (s is not None and s >= c["sbp_from"]) or (d is not None and d >= c["dbp_from"]):
        bp_met = True
    elif s is not None and d is not None:
        bp_met = False
    else:
        bp_met = None

    # ---- 기준 3, 4: 공복혈당, 중성지방 ----
    glucose_met = None if g is None else g >= c["glucose_from"]
    tg_met = None if t is None else t >= c["tg_from"]

    # ---- 기준 5: HDL (성별이 있어야 판단) ----
    if h is None or not has_sex:
        hdl_met = None
    else:
        hdl_met = h < c["hdl_below"][sex]

    checks = [
        {"name": "허리둘레",
         "rule": f"남 {c['waist_from']['남']} 이상 · 여 {c['waist_from']['여']} 이상 (cm)",
         "met": waist_met},
        {"name": "혈압",
         "rule": f"수축기 {c['sbp_from']} 이상 또는 이완기 {c['dbp_from']} 이상 (mmHg)",
         "met": bp_met},
        {"name": "공복혈당",
         "rule": f"{c['glucose_from']} 이상 (mg/dL)",
         "met": glucose_met},
        {"name": "중성지방",
         "rule": f"{c['tg_from']} 이상 (mg/dL)",
         "met": tg_met},
        {"name": "HDL 콜레스테롤",
         "rule": f"남 {c['hdl_below']['남']} 미만 · 여 {c['hdl_below']['여']} 미만 (mg/dL)",
         "met": hdl_met},
    ]

    met_count = sum(1 for ch in checks if ch["met"] is True)
    known_count = sum(1 for ch in checks if ch["met"] is not None)

    if met_count >= c["need_count"]:
        status = "의심"
    elif known_count == len(checks):
        status = "아님"
    else:
        status = "판정 불가"

    labels = {"의심": "대사증후군 의심", "아님": "대사증후군 아님", "판정 불가": "판정 불가"}

    return {
        "item": c["name"],
        "status": status,
        "label": labels[status],
        "met_count": met_count,
        "known_count": known_count,
        "checks": checks,
        "urgent": False,
        "source": c["source"],
    }


# ---------------------------------------------------------------------
# 내 수치 위치 막대용 정보 (position_info)
# ---------------------------------------------------------------------
# 막대 구간의 경계는 위 CRITERIA의 숫자만 그대로 씁니다. (새 기준 숫자 없음)
#
# [막대를 그리는 방식]
#   - 휴대폰에서도 "정상/주의/위험" 글자가 읽히도록 구간마다 같은 너비로 그립니다.
#     (예: 공복혈당은 4구간이라 각 25%)
#   - 내 값은 "자기 구간 안에서" 비율대로 위치를 잡습니다.
#     예) 공복혈당 110 -> 100 이상 126 미만 구간(50~75%)의 약 38% 지점 -> 약 59.6%
#   - 끝이 열린 구간(예: 70 미만, 126 이상)은 막대 끝을 정해야 하므로
#     "옆 구간의 너비"와 "경계값의 20%" 중 큰 값만큼 여유를 둡니다.
#     이 여유는 화면 표시용일 뿐 판정 기준이 아닙니다.
#   - 막대 끝보다 바깥 값은 막대 끝(0% 또는 100%)에 표시합니다.

POSITION_PAD_RATIO = 0.2   # 막대 양 끝 여유: 경계값의 20% (화면 표시용)


def _bar_ranges(item, sex):
    """막대에 쓸 구간표를 CRITERIA에서 꺼냅니다. 없으면 None"""
    if item in ("sbp", "dbp"):
        # 혈압은 수축기·이완기 막대를 따로 그립니다.
        c = CRITERIA["bp"]
        return [
            {"min": None, "max": c["normal_below"][item], "level": "normal"},
            {"min": c["normal_below"][item], "max": c["danger_from"][item], "level": "caution"},
            {"min": c["danger_from"][item], "max": None, "level": "danger"},
        ]
    if item == "waist":
        return CRITERIA["waist"]["ranges_by_sex"].get(sex)   # 성별 없으면 None
    if item in CRITERIA and "ranges" in CRITERIA[item]:
        return CRITERIA[item]["ranges"]
    return None


def _round1(number):
    """소수 첫째 자리까지 사사오입 반올림"""
    return float(Decimal(str(number)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def position_info(item, value, sex=None):
    """
    결과 카드의 "내 수치 위치 막대"에 필요한 정보를 돌려줍니다.
      item  : "bmi", "waist", "sbp"(수축기), "dbp"(이완기), "glucose", "tc", "ldl", "hdl", "tg"
      value : 내 수치. 단, BMI는 (키 cm, 몸무게 kg) 묶음으로 넣습니다.
              (몸무게 차이를 계산하려면 키가 필요하기 때문)
      sex   : "남"/"여" (허리둘레에서만 사용)
    그릴 수 없으면(성별 없는 허리둘레, 값 없음 등) None을 돌려줍니다.

    돌려주는 dict
      name       : 막대 이름 (예: "수축기 혈압")
      value      : 막대에 표시한 값 (BMI는 반올림한 BMI)
      unit       : 단위
      segments   : 구간 목록 [{"level", "label", "width"(%)}]
      boundaries : 구간 경계 [{"value": 경계 숫자, "pos": 막대 위 위치(%)}]
      position   : 내 값의 위치 (0~100 %)
      gap        : 정상 범위 경계까지의 차이 (정상 구간이면 None, BMI는 kg)
      gap_text   : 화면에 보여 줄 차이 문구 (정상 구간이면 None)
      bar_min, bar_max       : 막대의 왼쪽 끝·오른쪽 끝 값 (BMI는 BMI 값)
                               ("수치가 달라지면?" 체험의 슬라이더 범위로 씁니다)
      weight_min, weight_max : BMI일 때만, 막대 양 끝에 해당하는 몸무게(kg)
                               (키를 그대로 두었을 때. BMI가 아니면 None)
    """
    ranges = _bar_ranges(item, sex)
    if ranges is None:
        return None

    # ---- 1) 막대에 표시할 값 정하기 ----
    height = weight = None
    if item == "bmi":
        try:
            height, weight = value
        except (TypeError, ValueError):
            return None
        if _to_number(height) is None or _to_number(weight) is None:
            return None
        height, weight = float(height), float(weight)
        number = calc_bmi(height, weight)
    else:
        number = _to_number(value)
        if number is None:
            return None

    # ---- 2) 끝이 열린 구간에 막대 끝 정하기 (화면 표시용 여유) ----
    count = len(ranges)
    edges = []   # 각 구간의 (아래 끝, 위 끝)
    for i, r in enumerate(ranges):
        low, high = r["min"], r["max"]
        if low is None:
            neighbor = ranges[i + 1] if i + 1 < count else None
            width = (neighbor["max"] - neighbor["min"]) if neighbor and neighbor["max"] is not None else 0
            low = high - max(width, high * POSITION_PAD_RATIO)
        if high is None:
            neighbor = ranges[i - 1] if i > 0 else None
            width = (neighbor["max"] - neighbor["min"]) if neighbor and neighbor["min"] is not None else 0
            high = low + max(width, low * POSITION_PAD_RATIO)
        edges.append((low, high))

    # ---- 3) 내 값의 위치(%) 계산: 구간마다 같은 너비, 구간 안에서는 비율대로 ----
    seg_width = 100 / count
    index = None
    for i, r in enumerate(ranges):
        above_min = (r["min"] is None) or (number >= r["min"])   # A 이상
        below_max = (r["max"] is None) or (number < r["max"])    # B 미만
        if above_min and below_max:
            index = i
            break
    low, high = edges[index]
    fraction = (number - low) / (high - low)
    fraction = min(max(fraction, 0), 1)      # 막대 밖 값은 끝에 붙임
    position = round((index + fraction) * seg_width, 1)

    segments = [{"level": r["level"], "label": LEVEL_LABELS[r["level"]], "width": seg_width}
                for r in ranges]
    boundaries = [{"value": ranges[i]["min"], "pos": round(i * seg_width, 1)}
                  for i in range(1, count)]

    # ---- 4) 정상 범위 경계까지의 차이 ----
    if item == "bmi":
        name, unit = "BMI", CRITERIA["bmi"]["unit"]
    elif item in ("sbp", "dbp"):
        name, unit = LIMITS[item]["name"], CRITERIA["bp"]["unit"]
    else:
        name, unit = CRITERIA[item]["name"], CRITERIA[item]["unit"]

    gap = None
    gap_text = None
    if ranges[index]["level"] != "normal":
        normal = next(r for r in ranges if r["level"] == "normal")
        # 정상 구간보다 낮은지, 높은지 확인하고 가장 가까운 경계를 고릅니다.
        if normal["min"] is not None and number < normal["min"]:
            boundary, side = normal["min"], "낮은"
        else:
            boundary, side = normal["max"], "높은"

        if item == "bmi":
            # 키를 그대로 두었을 때, 경계 BMI가 되는 몸무게와의 차이(kg)
            height_m = height / 100
            boundary_weight = boundary * height_m * height_m
            gap = _round1(abs(weight - boundary_weight))
            boundary_text = f"BMI {boundary:g}"
            gap_unit = "kg"
            extra = "키가 같다면 몸무게로 "
        else:
            gap = _round1(abs(number - boundary))
            boundary_text = f"{boundary:g} {unit}"
            gap_unit = unit
            extra = ""

        if gap == 0:
            gap_text = f"현재 값은 정상 범위 경계({boundary_text})와 거의 같습니다."
        else:
            gap_text = (f"현재 값은 정상 범위 경계({boundary_text})보다 {side} 쪽이며, "
                        f"{extra}정상 범위 경계까지 약 {gap:g} {gap_unit} 차이가 있습니다.")

    return {
        "name": name,
        "value": number,
        "unit": unit,
        "segments": segments,
        "boundaries": boundaries,
        "position": position,
        "gap": gap,
        "gap_text": gap_text,
        # 막대 양 끝 (위 2)에서 정한 값 그대로. 새 기준 숫자가 아닙니다.
        "bar_min": edges[0][0],
        "bar_max": edges[-1][1],
        # BMI 막대 양 끝을 몸무게로 바꾼 값 (몸무게 = BMI × 키(m)²)
        "weight_min": _round1(edges[0][0] * (height / 100) ** 2) if item == "bmi" else None,
        "weight_max": _round1(edges[-1][1] * (height / 100) ** 2) if item == "bmi" else None,
    }


# =====================================================================
# 7. 직접 실행했을 때만 동작하는 부분
#    명령 프롬프트에서:  py criteria.py
#    (app.py나 test_criteria.py가 import할 때는 실행되지 않습니다.)
# =====================================================================
if __name__ == "__main__":
    print("=== 공복혈당 판정 예시 ===")
    for g in [69, 70, 99, 100, 125, 126]:
        r = judge_glucose(g)
        print(f"공복혈당 {g:>3} -> {r['label']} ({r['sub_label']}), urgent={r['urgent']}")

    print()
    print("=== 혈압 판정 예시 ===")
    for s, d in [(119, 79), (120, 79), (139, 89), (140, 80), (120, 90)]:
        r = judge_bp(s, d)
        print(f"혈압 {s}/{d} -> {r['label']} ({r['sub_label']}), urgent={r['urgent']}")
