# =====================================================================
# test_criteria.py  -  criteria.py의 판정이 맞는지 자동으로 검사하는 파일
# =====================================================================
# [사용 방법 - 명령 프롬프트]
#   cd C:\health-helper
#   py test_criteria.py
#   -> 케이스마다 [통과]/[실패]가 한 줄씩 나오고,
#      결과가 같은 폴더의 test_result.csv로 저장됩니다. (엑셀로 열 수 있음)
#
# app.py의 "검증 결과" 탭도 이 파일의 run_tests()를 불러 써서 표로 보여 줍니다.
# (앱에서 실행할 때는 csv 파일을 만들지 않습니다.)
#
# [검사 케이스를 바꾸려면]
#   아래 TEST_CASES 리스트만 통째로 바꾸면 됩니다. 나머지 코드는 손대지 않아도 됩니다.
#
#   케이스 1개 = 딕셔너리 1개
#     "번호"       : 케이스 번호
#     "항목"       : BMI / 허리둘레 / 혈압 / 공복혈당 / 총콜레스테롤 / LDL / HDL / 중성지방
#     "입력값"     : 항목에 필요한 값들 (이름은 아래 표 참고)
#     "기대판정"   : 정상 / 주의 / 위험 / 입력 오류 / 판정 안 함
#     "기대urgent" : True 또는 False (검사하지 않으려면 이 줄을 아예 빼기)
#     "기대차이"   : 정상 범위 경계까지의 차이 (검사하지 않으려면 이 줄을 아예 빼기)
#                    {막대 이름: 차이} 모양. 막대 이름은 bmi/waist/sbp/dbp/glucose/tc/ldl/hdl/tg
#                    예) {"glucose": 10}, 혈압은 {"sbp": 15, "dbp": 5}, BMI는 kg 단위
#                    소수 첫째 자리까지 비교합니다.
#     "메모"       : 이 케이스를 넣은 이유
#
#   항목별 "입력값" 이름
#     BMI          : height(키), weight(몸무게)
#     허리둘레     : waist(허리둘레), sex("남" 또는 "여", 없으면 None)
#     혈압         : sbp(수축기), dbp(이완기)
#     공복혈당     : glucose
#     총콜레스테롤 : tc
#     LDL          : ldl
#     HDL          : hdl
#     중성지방     : tg
#   빈칸은 "" 로, 글자 입력은 "abc"처럼 따옴표 안에 적습니다.
# =====================================================================

TEST_CASES = [
    # ---- 공복혈당 경계값 ----
    {"번호": 1, "항목": "공복혈당", "입력값": {"glucose": 69}, "기대판정": "주의", "메모": "70 미만 저혈당 범위"},
    {"번호": 2, "항목": "공복혈당", "입력값": {"glucose": 70}, "기대판정": "정상", "메모": "정상 시작 경계(이상)"},
    {"번호": 3, "항목": "공복혈당", "입력값": {"glucose": 99}, "기대판정": "정상", "메모": "정상 끝"},
    {"번호": 4, "항목": "공복혈당", "입력값": {"glucose": 100}, "기대판정": "주의", "메모": "공복혈당장애 시작 경계"},
    {"번호": 5, "항목": "공복혈당", "입력값": {"glucose": 125}, "기대판정": "주의", "메모": "공복혈당장애 끝"},
    {"번호": 6, "항목": "공복혈당", "입력값": {"glucose": 126}, "기대판정": "위험", "메모": "당뇨병 범위 시작 경계"},

    # ---- 혈압 경계값 ----
    {"번호": 7, "항목": "혈압", "입력값": {"sbp": 119, "dbp": 79}, "기대판정": "정상", "메모": "둘 다 정상 미만"},
    {"번호": 8, "항목": "혈압", "입력값": {"sbp": 120, "dbp": 79}, "기대판정": "주의", "메모": "수축기만 120 경계"},
    {"번호": 9, "항목": "혈압", "입력값": {"sbp": 139, "dbp": 89}, "기대판정": "주의", "메모": "고혈압 범위 직전"},
    {"번호": 10, "항목": "혈압", "입력값": {"sbp": 140, "dbp": 80}, "기대판정": "위험", "기대urgent": False, "메모": "수축기만 140 경계"},
    {"번호": 11, "항목": "혈압", "입력값": {"sbp": 120, "dbp": 90}, "기대판정": "위험", "메모": "이완기만 90 경계"},

    # ---- 입력 오류 ----
    {"번호": 12, "항목": "공복혈당", "입력값": {"glucose": -5}, "기대판정": "입력 오류", "메모": "음수"},
    {"번호": 13, "항목": "공복혈당", "입력값": {"glucose": ""}, "기대판정": "판정 안 함", "메모": "빈칸은 오류가 아니라 판정하지 않음"},
    {"번호": 14, "항목": "공복혈당", "입력값": {"glucose": "abc"}, "기대판정": "입력 오류", "메모": "숫자가 아닌 글자"},
    {"번호": 15, "항목": "혈압", "입력값": {"sbp": 400, "dbp": 80}, "기대판정": "입력 오류", "메모": "수축기 허용 범위(60~300) 밖"},
    {"번호": 16, "항목": "혈압", "입력값": {"sbp": 120, "dbp": 130}, "기대판정": "입력 오류", "메모": "이완기가 수축기보다 큼"},

    # ---- 정상 범위 경계까지 차이 ----
    {"번호": 17, "항목": "공복혈당", "입력값": {"glucose": 110}, "기대판정": "주의", "기대차이": {"glucose": 10}, "메모": "100 미만 경계보다 10 높음"},
    {"번호": 18, "항목": "HDL", "입력값": {"hdl": 35}, "기대판정": "위험", "기대차이": {"hdl": 5}, "메모": "40 이상 경계보다 5 낮음(높아지는 방향)"},
    {"번호": 19, "항목": "혈압", "입력값": {"sbp": 135, "dbp": 85}, "기대판정": "주의", "기대차이": {"sbp": 15, "dbp": 5}, "메모": "수축기 120, 이완기 80 경계"},
    {"번호": 20, "항목": "BMI", "입력값": {"height": 170, "weight": 75}, "기대판정": "위험", "기대차이": {"bmi": 8.5}, "메모": "BMI 23이 되는 몸무게 66.47kg과의 차이"},

    # ---- 단위 착오 (mmol/L 값을 입력한 경우) ----
    {"번호": 21, "항목": "공복혈당", "입력값": {"glucose": 5.5}, "기대판정": "입력 오류", "메모": "mmol/L 값으로 보이는 작은 값"},
    {"번호": 22, "항목": "총콜레스테롤", "입력값": {"tc": 5.2}, "기대판정": "입력 오류", "메모": "mmol/L 값으로 보이는 작은 값"},
]


# =====================================================================
# 여기부터는 검사를 실행하는 코드입니다. (케이스를 바꿀 때는 손대지 않아도 됨)
# =====================================================================

import csv                 # csv 파일 저장용 (표준 라이브러리)
from pathlib import Path   # 파일 위치를 다루는 도구 (표준 라이브러리)

import criteria


# 항목 이름 -> (숫자 입력값 이름들, 판정 함수)
# app.py와 같은 순서·같은 방식으로 판정하도록 맞췄습니다.
ITEMS = {
    "BMI":          (["height", "weight"], criteria.judge_bmi),
    "허리둘레":     (["waist"],            criteria.judge_waist),   # sex는 따로 넘김
    "혈압":         (["sbp", "dbp"],       criteria.judge_bp),
    "공복혈당":     (["glucose"],          criteria.judge_glucose),
    "총콜레스테롤": (["tc"],               criteria.judge_tc),
    "LDL":          (["ldl"],              criteria.judge_ldl),
    "HDL":          (["hdl"],              criteria.judge_hdl),
    "중성지방":     (["tg"],               criteria.judge_tg),
}


def _show_inputs(inputs):
    """입력값을 사람이 읽기 쉬운 글자로 바꿉니다. 예) 수축기 혈압=120, 이완기 혈압=80"""
    parts = []
    for name, value in inputs.items():
        # 이름을 한국어로 (LIMITS에 없는 sex는 "성별")
        korean = criteria.LIMITS[name]["name"] if name in criteria.LIMITS else "성별"
        if value is None or value == "":
            shown = "(빈칸)"
        elif isinstance(value, str):
            shown = f'"{value}"'
        else:
            shown = str(value)
        parts.append(f"{korean}={shown}")
    return ", ".join(parts)


def _judge_one(case):
    """
    케이스 1개를 app.py와 같은 순서로 판정합니다.
      1) 입력 검사(validate_input) -> 하나라도 오류면 "입력 오류"
      2) 빈칸이 있으면 "판정 안 함"
      3) 판정 함수 실행 -> 정상/주의/위험 (또는 판정 안 함)
    돌려주는 값: (실제 판정, 실제 urgent)
    """
    if case["항목"] not in ITEMS:
        return "알 수 없는 항목", None

    fields, judge = ITEMS[case["항목"]]
    inputs = case["입력값"]

    # 1) 입력 검사
    statuses = []
    for f in fields:
        if f == "dbp":
            # 이완기는 수축기보다 작은지도 함께 검사
            statuses.append(criteria.validate_input(f, inputs.get(f), systolic=inputs.get("sbp")))
        else:
            statuses.append(criteria.validate_input(f, inputs.get(f)))

    if any(s not in ("ok", "empty") for s in statuses):
        return "입력 오류", None

    # 2) 빈칸 확인
    if "empty" in statuses:
        return "판정 안 함", None

    # 3) 판정 (validate_input을 통과했으므로 숫자로 바꿔서 넘김)
    values = [float(inputs[f]) for f in fields]
    if case["항목"] == "허리둘레":
        result = judge(values[0], inputs.get("sex"))
    else:
        result = judge(*values)
    return result["label"], result["urgent"]


def _actual_gaps(case):
    """
    "기대차이"에 적힌 막대마다 criteria.position_info()로 실제 차이를 구합니다.
    돌려주는 값: {막대 이름: 실제 차이(소수 첫째 자리) 또는 None}
    """
    inputs = case["입력값"]
    gaps = {}
    for bar in case["기대차이"]:
        if bar == "bmi":
            value = (inputs.get("height"), inputs.get("weight"))
        else:
            value = inputs.get(bar)
        info = criteria.position_info(bar, value, inputs.get("sex"))
        gaps[bar] = None if info is None or info["gap"] is None else round(info["gap"], 1)
    return gaps


def _gap_text(gaps):
    """차이 dict를 글자로 바꿉니다. 예) {"sbp": 15} -> "차이 sbp=15" """
    shown = []
    for bar, gap in gaps.items():
        shown.append(f"{bar}={'없음' if gap is None else format(gap, 'g')}")
    return "차이 " + ", ".join(shown)


def run_tests():
    """
    TEST_CASES를 모두 실행하고 결과 리스트를 돌려줍니다.
    결과 1개 = {"번호", "항목", "입력값", "기대", "실제", "통과여부"}
    """
    results = []
    for case in TEST_CASES:
        expected = case["기대판정"]
        try:
            actual, actual_urgent = _judge_one(case)
        except Exception as error:   # 코드가 멈추지 않도록, 문제가 생기면 실패로 기록
            actual, actual_urgent = f"실행 중 오류: {error}", None

        passed = (actual == expected)
        expected_text = expected
        actual_text = actual

        # 기대urgent가 적혀 있는 케이스만 urgent도 비교
        if "기대urgent" in case:
            passed = passed and (actual_urgent == case["기대urgent"])
            expected_text += f" / urgent={case['기대urgent']}"
            actual_text += f" / urgent={actual_urgent}"

        # 기대차이가 적혀 있는 케이스만 "정상 범위 경계까지 차이"도 비교
        if "기대차이" in case:
            expected_gaps = {bar: round(float(g), 1) for bar, g in case["기대차이"].items()}
            try:
                actual_gaps = _actual_gaps(case)
            except Exception as error:
                actual_gaps = {bar: None for bar in expected_gaps}
                actual_text += f" / 차이 계산 중 오류: {error}"
            passed = passed and (actual_gaps == expected_gaps)
            expected_text += " / " + _gap_text(expected_gaps)
            actual_text += " / " + _gap_text(actual_gaps)

        results.append({
            "번호": case["번호"],
            "항목": case["항목"],
            "입력값": _show_inputs(case["입력값"]),
            "기대": expected_text,
            "실제": actual_text,
            "통과여부": passed,
        })
    return results


# =====================================================================
# 직접 실행했을 때만 동작하는 부분:  py test_criteria.py
# (app.py가 import할 때는 실행되지 않으므로 csv도 만들지 않습니다.)
# =====================================================================
if __name__ == "__main__":
    results = run_tests()

    for r in results:
        mark = "[통과]" if r["통과여부"] else "[실패]"
        print(f"{mark} {r['번호']}. {r['항목']} ({r['입력값']}) "
              f"기대: {r['기대']} / 실제: {r['실제']}")

    passed_count = sum(1 for r in results if r["통과여부"])

    # 결과를 이 파일과 같은 폴더의 test_result.csv로 저장
    # (utf-8-sig: 엑셀에서 열어도 한글이 깨지지 않는 저장 방식)
    csv_path = Path(__file__).parent / "test_result.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["번호", "항목", "입력값", "기대", "실제", "통과여부"])
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["통과여부"] = "통과" if r["통과여부"] else "실패"
            writer.writerow(row)

    print(f"(결과 저장: {csv_path})")
    print(f"총 {len(results)}개 중 {passed_count}개 통과")
