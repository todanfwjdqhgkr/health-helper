# =====================================================================
# app.py  -  건강검진 결과 해석 도우미의 "화면" 파일 (Streamlit)
# =====================================================================
# 기준값과 판정 규칙은 모두 criteria.py에 있고, 이 파일은 화면만 담당합니다.
#
# [화면 구성]
#   탭 1 "결과 해석" : 안전 안내 -> 시연 버튼 -> 입력칸 -> 결과 보기/모두 지우기
#                      -> 결과 요약 -> 결과 카드(판정 + 내 수치 위치 막대) -> 출처·한계·저장 안내
#   탭 2 "검증 결과" : test_criteria.py의 자동 검사 결과를 표로 보여 줌
#
# [Streamlit이 동작하는 방식 - 꼭 알아 두기]
#   버튼을 누르거나 값을 바꿀 때마다 이 파일이 "위에서 아래로 처음부터 다시" 실행됩니다.
#   입력칸의 값은 st.session_state(화면 유지용 임시 보관함)에 들어 있어서
#   다시 실행되어도 사라지지 않습니다. 파일이나 서버에는 저장하지 않습니다.
#
# [실행 방법 - 명령 프롬프트]
#   cd C:\health-helper
#   py -m streamlit run app.py
#
# ※ 교육용 수업 과제이며 실제 진단 도구가 아닙니다.
# =====================================================================

from datetime import datetime, timedelta, timezone   # 실행 시각 표시용 (표준 라이브러리)
import html   # 화면에 넣는 글자를 안전하게 바꾸는 도구 (표준 라이브러리)

import pandas as pd   # 표 꾸미기용 (streamlit을 설치하면 함께 설치됨)
import streamlit as st
import criteria        # 같은 폴더의 criteria.py를 불러옵니다.
import test_criteria   # 같은 폴더의 test_criteria.py를 불러옵니다.

# 페이지 기본 설정 (이 명령은 화면 맨 처음에 한 번만 씁니다)
st.set_page_config(page_title="건강검진 결과 해석 도우미", layout="centered")


# ---------------------------------------------------------------------
# 1. 글씨 크기 조정 (부모님 세대도 읽기 쉽게)
# ---------------------------------------------------------------------
# 기본 글씨 크기를 16px -> 18px로 키우면 화면 전체 글씨가 함께 커집니다.
# 버튼 높이도 키워서 휴대폰에서 손가락으로 누르기 쉽게 했습니다.
st.markdown(
    """
    <style>
    html { font-size: 18px; }
    h1 { font-size: 1.8rem !important; line-height: 1.35 !important; }
    [data-testid="stWidgetLabel"] p { font-size: 1.05rem; }
    [data-testid="stAlert"] p { font-size: 1.05rem; line-height: 1.65; }
    .stButton button { min-height: 3rem; font-size: 1.05rem; }

    /* ---- 내 수치 위치 막대 ---- */
    .pos-bar { margin: 0.2rem 0 0.8rem 0; }
    .pos-title { font-weight: bold; margin-bottom: 0.1rem; }
    .pos-marker-row { position: relative; height: 1.3rem; }
    .pos-marker { position: absolute; transform: translateX(-50%);
                  font-size: 1.1rem; line-height: 1.3rem; }
    .pos-track { display: flex; height: 0.9rem; border-radius: 0.45rem; overflow: hidden; }
    .pos-normal  { background: #66bb6a; }   /* 정상: 초록 */
    .pos-caution { background: #ffca28; }   /* 주의: 노랑 */
    .pos-danger  { background: #ef5350; }   /* 위험: 빨강 */
    .pos-ticks { position: relative; height: 1.2rem; font-size: 0.8rem; opacity: 0.8; }
    .pos-ticks span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
    .pos-labels { display: flex; font-size: 0.85rem; }
    .pos-labels span { text-align: center; white-space: nowrap; overflow: hidden; }
    .pos-gap { margin-top: 0.3rem; font-size: 0.95rem; line-height: 1.5; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# 2. 입력칸 목록과 예시 수치
# ---------------------------------------------------------------------
# 숫자 입력칸의 이름(key). criteria.LIMITS의 이름과 똑같이 맞췄습니다.
NUMBER_KEYS = ["age", "height", "weight", "waist", "sbp", "dbp",
               "glucose", "tc", "ldl", "hdl", "tg"]

# 소수점 입력이 필요한 칸 (나머지는 정수 칸)
# 혈당·지질 칸도 소수점을 받아야 mmol/L 값(예: 5.5)을 그대로 인식해 단위 착오를 안내할 수 있습니다.
DECIMAL_KEYS = ["height", "weight", "waist", "glucose", "tc", "ldl", "hdl", "tg"]

# 시연용 가상 수치 (임시). 나중에 이 딕셔너리만 바꾸면 됩니다.
# ※ 소수점 칸(키·몸무게·허리·혈당·지질)은 170.0처럼 소수로, 나머지(나이·혈압)는 정수로 적어야 합니다.
EXAMPLES = {
    "정상 예시": {
        "sex": "남", "age": 40, "height": 170.0, "weight": 63.0, "waist": 80.0,
        "sbp": 115, "dbp": 75, "glucose": 90.0,
        "tc": 180.0, "ldl": 100.0, "hdl": 55.0, "tg": 100.0,
    },
    "주의 예시": {
        "sex": "여", "age": 50, "height": 160.0, "weight": 61.5, "waist": 88.0,
        "sbp": 130, "dbp": 85, "glucose": 110.0,
        "tc": 220.0, "ldl": 145.0, "hdl": 45.0, "tg": 170.0,
    },
    "위험 예시": {
        "sex": "남", "age": 60, "height": 170.0, "weight": 80.0, "waist": 95.0,
        "sbp": 150, "dbp": 95, "glucose": 140.0,
        "tc": 260.0, "ldl": 170.0, "hdl": 35.0, "tg": 250.0,
    },
}


# ---------------------------------------------------------------------
# 3. 화면 유지용 보관함(st.session_state) 준비
# ---------------------------------------------------------------------
# 처음 열었을 때 모든 칸을 빈칸(None)으로 만들어 둡니다.
for k in NUMBER_KEYS + ["sex"]:
    if k not in st.session_state:
        st.session_state[k] = None
if "show_result" not in st.session_state:
    st.session_state["show_result"] = False   # 결과를 보여 줄지 여부


# ---------------------------------------------------------------------
# 4. 버튼을 눌렀을 때 실행되는 함수(콜백)
# ---------------------------------------------------------------------
# 콜백은 화면을 다시 그리기 "전에" 실행됩니다.
# 그래서 여기서 입력칸 값을 바꿔도 "위젯 생성 후 값 변경" 오류가 나지 않습니다.

def load_example(name):
    """예시 수치를 입력칸에 채웁니다."""
    example = EXAMPLES[name]
    st.session_state["sex"] = example["sex"]
    st.session_state.pop("pregnant", None)   # 임신 체크는 해제 상태로
    for k in NUMBER_KEYS:
        st.session_state[k] = example[k]
    st.session_state["show_result"] = False  # 결과는 "결과 보기"를 눌러야 나옴


def clear_all():
    """모든 입력칸을 비우고 결과를 숨깁니다."""
    st.session_state["sex"] = None
    st.session_state.pop("pregnant", None)
    for k in NUMBER_KEYS:
        st.session_state[k] = None
    st.session_state["show_result"] = False


def show_result():
    """결과를 보여 주도록 표시합니다."""
    st.session_state["show_result"] = True


# ---------------------------------------------------------------------
# 5. 결과를 보여 주는 도우미 함수
# ---------------------------------------------------------------------

def fmt(number):
    """숫자를 보기 좋게 바꿉니다. 63.0 -> "63", 170.5 -> "170.5" """
    return f"{number:g}"


def escape(text):
    """
    화면 글자에서 물결표(~)가 "취소선"으로 바뀌는 것을 막습니다.
    (Streamlit 글자 표시 방식에서 ~는 취소선 기호로 쓰이기 때문)
    """
    return text.replace("~", "\\~")


def input_label(key):
    """입력칸 이름에 단위를 붙입니다. 예) "키 (cm)" """
    limit = criteria.LIMITS[key]
    return f"{limit['name']} ({limit['unit']})"


def show_error(key, message):
    """입력 오류를 테두리 상자 안에 보여 줍니다. (판정 색과 헷갈리지 않게 무채색)"""
    with st.container(border=True):
        st.markdown(f"**{criteria.LIMITS[key]['name']} 입력 오류**\n\n{escape(message)}")


def position_bar_html(info, show_title=False):
    """
    criteria.position_info()가 돌려준 정보로 "내 수치 위치 막대"를 HTML로 만듭니다.
      맨 위   : 내 위치 표시(▼)
      가운데  : 초록·노랑·빨강 구간 막대
      그 아래 : 구간 경계 숫자, 구간 이름(정상/주의/위험) -> 색만으로 구분하지 않게
      맨 아래 : 정상 범위 경계까지의 차이 문구(정상이 아닐 때만)
    """
    # ▼가 화면 밖으로 반쯤 잘리지 않도록 양 끝을 조금 안쪽으로
    marker = min(max(info["position"], 3), 97)

    parts = ['<div class="pos-bar">']
    if show_title:   # 혈압처럼 막대가 2개일 때만 이름 표시
        parts.append(f'<div class="pos-title">{html.escape(info["name"])}</div>')
    parts.append(f'<div class="pos-marker-row"><span class="pos-marker" '
                 f'style="left:{marker}%">▼</span></div>')

    # 색 구간
    parts.append('<div class="pos-track">')
    for seg in info["segments"]:
        parts.append(f'<div class="pos-{seg["level"]}" style="width:{seg["width"]}%"></div>')
    parts.append('</div>')

    # 구간 경계 숫자
    parts.append('<div class="pos-ticks">')
    for b in info["boundaries"]:
        parts.append(f'<span style="left:{b["pos"]}%">{b["value"]:g}</span>')
    parts.append('</div>')

    # 구간 이름 글자
    parts.append('<div class="pos-labels">')
    for seg in info["segments"]:
        parts.append(f'<span style="width:{seg["width"]}%">{seg["label"]}</span>')
    parts.append('</div>')

    if info["gap_text"]:
        parts.append(f'<div class="pos-gap">{html.escape(info["gap_text"])}</div>')
    parts.append('</div>')

    # 줄바꿈 없이 한 줄로 이어 붙여야 화면에서 HTML이 깨지지 않습니다.
    return "".join(parts)


def show_card(key, result, value_text, extra="", bars=None):
    """
    판정 결과 카드 1장을 보여 줍니다.
      key        : criteria의 항목 이름 (예: "glucose")
      result     : criteria.judge_...() 함수가 돌려준 dict
      value_text : 화면에 보여 줄 내 수치 글자 (예: "120/80")
      extra      : 수치 뒤에 덧붙일 설명 (BMI 계산에 쓴 키·몸무게)
      bars       : 내 수치 위치 막대 정보 목록 (criteria.position_info 결과들)
    """
    # 판정하지 않은 경우(예: 성별이 없어 허리둘레 판정 불가)는 안내만
    if result["level"] is None:
        st.info(f"**{result['item']}**\n\n{result['sub_label']}")
        return

    unit = criteria.CRITERIA[key]["unit"]
    lines = []

    # 빨리 진료가 필요한 수치면 카드 맨 앞에 굵게
    if result["urgent"]:
        lines.append("**가능한 빨리 진료 권장**")

    lines.append(f"**{result['item']}**")
    lines.append(f"내 수치: **{value_text} {unit}**{extra}")
    lines.append(f"판정: **{result['label']}** ({result['sub_label']})")

    # 설명과 팁 (criteria.TEXTS에서 가져옴)
    text = criteria.TEXTS[key].get(result["sub_label"])
    if text:
        lines.append(f"설명: {text['explain']}")
        lines.append(f"생활습관 팁: {text['tip']}")

    # 다음 행동: urgent가 가장 우선, 그다음 주의/위험
    # (정상일 때의 다음 행동 문구는 아직 정해지지 않아 표시하지 않습니다)
    next_actions = criteria.TEXTS["next_action"]
    if result["urgent"]:
        lines.append(f"다음 행동: {next_actions['urgent']}")
    elif result["level"] in next_actions:
        lines.append(f"다음 행동: {next_actions[result['level']]}")

    body = escape("\n\n".join(lines))

    # 카드 = 테두리 상자 안에 [판정 글자 상자] + [내 수치 위치 막대]
    with st.container(border=True):
        # 판정에 따라 색을 다르게: 정상=초록, 주의=노랑, 위험=빨강
        if result["level"] == "normal":
            st.success(body)
        elif result["level"] == "caution":
            st.warning(body)
        else:
            st.error(body)

        # 내 수치 위치 막대 (그릴 수 없는 막대는 건너뜀)
        bars = [b for b in (bars or []) if b is not None]
        for info in bars:
            st.markdown(position_bar_html(info, show_title=len(bars) > 1),
                        unsafe_allow_html=True)
        if bars:
            st.caption("▼ 표시는 판정 기준 구간에서 내 수치의 위치이며, 다른 사람과 비교한 순위가 아닙니다. "
                       "막대의 구간 너비는 보기 쉽게 같은 크기로 그렸습니다.")


def show_summary(box, judged):
    """
    결과 카드들 맨 위에 요약을 보여 줍니다.
      - 정상/주의/위험 개수
      - 먼저 확인할 항목: urgent 항목이 있으면 그 항목, 없으면 위험 항목
        (둘 다 없으면 이 줄은 보여 주지 않습니다)
    """
    count = {"normal": 0, "caution": 0, "danger": 0}
    for r in judged:
        count[r["level"]] += 1

    lines = [f"**결과 요약**: 정상 {count['normal']}개 · "
             f"주의 {count['caution']}개 · 위험 {count['danger']}개"]

    urgent_items = [r["item"] for r in judged if r["urgent"]]
    danger_items = [r["item"] for r in judged if r["level"] == "danger"]
    if urgent_items:
        lines.append("**먼저 확인할 항목**: " + ", ".join(urgent_items)
                     + " (가능한 빨리 진료 권장 수치)")
    elif danger_items:
        lines.append("**먼저 확인할 항목**: " + ", ".join(danger_items)
                     + " (위험 범위에 해당하는 수치)")

    with box:
        with st.container(border=True):
            st.markdown("\n\n".join(lines))


def show_all_results():
    """입력한 항목만 골라 판정하고 카드를 보여 줍니다."""
    s = st.session_state   # 짧게 쓰려고 이름을 붙임
    sex = s["sex"]
    # 임신 체크는 여성일 때만 화면에 있으므로, 여성일 때만 값을 읽습니다.
    pregnant = s.get("pregnant", False) if sex == "여" else False

    # (1) 대상자 확인: 19세 미만이거나 임신 중이면 결과 대신 안내만
    eligibility = criteria.check_eligibility(s["age"], sex, pregnant)
    if not eligibility["eligible"]:
        st.warning(escape(eligibility["message"]))
        return

    # (2) 모든 칸의 입력 상태 검사: "empty" / "ok" / 오류 메시지
    status = {k: criteria.validate_input(k, s[k]) for k in NUMBER_KEYS}
    # 이완기 혈압은 수축기 혈압보다 작은지도 함께 검사
    status["dbp"] = criteria.validate_input("dbp", s["dbp"], systolic=s["sbp"])

    def ok_value(k):
        """검사를 통과한 값만 돌려주고, 빈칸이면 None"""
        return s[k] if status[k] == "ok" else None

    shown = 0   # 화면에 보여 준 카드 수

    # 결과 요약 자리: 카드보다 "위"에 보이도록 빈 상자를 먼저 만들어 두고,
    # 카드를 모두 그린 뒤에 내용을 채웁니다.
    summary_box = st.container()
    judged = []   # 판정된 결과(정상/주의/위험)를 모아 두는 목록

    def record_card(key, result, *args, **kwargs):
        """카드를 그리면서, 판정된 결과는 요약용 목록에도 넣습니다."""
        if result["level"] is not None:
            judged.append(result)
        show_card(key, result, *args, **kwargs)

    def show_pair(key, k1, k2, judge):
        """두 값이 필요한 항목(BMI: 키+몸무게, 혈압: 수축기+이완기)을 처리합니다."""
        if status[k1] == "empty" and status[k2] == "empty":
            return 0   # 둘 다 비었으면 건너뜀
        errors = [k for k in (k1, k2) if status[k] not in ("ok", "empty")]
        if errors:
            for k in errors:
                show_error(k, status[k])
            return 1
        # 하나만 입력했으면 judge 함수가 "판정 안 함" 결과를 돌려줍니다.
        result = judge(ok_value(k1), ok_value(k2))
        if result["level"] is None:
            record_card(key, result, "")
        elif key == "bmi":
            extra = f" (키 {fmt(s['height'])}cm, 몸무게 {fmt(s['weight'])}kg로 계산)"
            bars = [criteria.position_info("bmi", (s["height"], s["weight"]))]
            record_card(key, result, f"{result['value']:.1f}", extra, bars)
        else:
            bars = [criteria.position_info("sbp", s["sbp"]),
                    criteria.position_info("dbp", s["dbp"])]
            record_card(key, result, f"{fmt(s['sbp'])}/{fmt(s['dbp'])}", bars=bars)
        return 1

    # (3) BMI
    shown += show_pair("bmi", "height", "weight", criteria.judge_bmi)

    # (4) 허리둘레: 성별이 필요
    if status["waist"] != "empty":
        shown += 1
        if status["waist"] != "ok":
            show_error("waist", status["waist"])
        else:
            bars = [criteria.position_info("waist", s["waist"], sex)]
            record_card("waist", criteria.judge_waist(s["waist"], sex), fmt(s["waist"]),
                      bars=bars)

    # (5) 혈압
    shown += show_pair("bp", "sbp", "dbp", criteria.judge_bp)

    # (6) 값 하나로 판정하는 항목
    singles = [
        ("glucose", criteria.judge_glucose),
        ("tc", criteria.judge_tc),
        ("ldl", criteria.judge_ldl),
        ("hdl", criteria.judge_hdl),
        ("tg", criteria.judge_tg),
    ]
    for key, judge in singles:
        if status[key] == "empty":
            continue
        shown += 1
        if status[key] != "ok":
            show_error(key, status[key])
        else:
            record_card(key, judge(s[key]), fmt(s[key]),
                      bars=[criteria.position_info(key, s[key])])

    if shown == 0:
        st.info("판정할 수치를 하나 이상 입력해 주세요.")

    # (7) 결과 요약 채우기 (판정된 항목이 있을 때만)
    if judged:
        show_summary(summary_box, judged)


def number_box(key):
    """숫자 입력칸 1개를 만듭니다. 범위 검사는 criteria.validate_input이 합니다."""
    # 나이는 이용 대상(19세 이상) 확인에 꼭 필요하므로 "필수"로 표시합니다.
    # 나머지 칸은 비워 두면 그 항목만 판정하지 않습니다.
    if key == "age":
        label = input_label(key) + " · 필수"
        placeholder = "꼭 입력해 주세요"
    else:
        label = input_label(key)
        placeholder = "입력하지 않아도 됩니다"

    if key in DECIMAL_KEYS:
        st.number_input(label, value=None, step=0.1, format="%.1f",
                        key=key, placeholder=placeholder)
    else:
        st.number_input(label, value=None, step=1,
                        key=key, placeholder=placeholder)


# =====================================================================
# 6. 화면 그리기
# =====================================================================
st.title("건강검진 결과 해석 도우미")

tab_result, tab_check = st.tabs(["결과 해석", "검증 결과"])

# ---------------- 탭 1: 결과 해석 ----------------
with tab_result:
    # 6-1. 안전 안내 (항상 보임)
    st.info("이 도구는 교육용이며 의학적 진단을 대신하지 않습니다.\n\n"
            "19세 미만, 임산부는 기준이 달라 이용할 수 없습니다.")

    # 6-2. 시연 버튼 3개 (휴대폰에서는 자동으로 세로로 쌓임)
    st.subheader("예시로 해 보기")
    cols = st.columns(3)
    for col, name in zip(cols, EXAMPLES):
        col.button(name, on_click=load_example, args=(name,), width="stretch")

    # 6-3. 입력칸
    st.subheader("내 검진 수치 입력")
    st.radio("성별", ["남", "여"], index=None, horizontal=True, key="sex")
    if st.session_state["sex"] == "여":
        st.checkbox("임신 중입니다", key="pregnant")

    number_box("age")

    col1, col2 = st.columns(2)
    with col1:
        number_box("height")
    with col2:
        number_box("weight")
    number_box("waist")

    col1, col2 = st.columns(2)
    with col1:
        number_box("sbp")
    with col2:
        number_box("dbp")

    number_box("glucose")
    number_box("tc")
    number_box("ldl")
    number_box("hdl")
    number_box("tg")

    # 6-4. 결과 보기 / 모두 지우기 버튼
    col1, col2 = st.columns(2)
    with col1:
        st.button("결과 보기", on_click=show_result, type="primary", width="stretch")
    with col2:
        st.button("모두 지우기", on_click=clear_all, width="stretch")

    # 6-5. 결과 카드
    if st.session_state["show_result"]:
        st.subheader("결과")
        show_all_results()

    # 6-6. 출처, 한계, 저장 안내
    st.divider()
    st.subheader("판정 기준 출처")
    # criteria.CRITERIA에서 출처를 자동으로 모읍니다. (같은 출처는 한 번만)
    sources = []
    for item in criteria.CRITERIA.values():
        if item["source"] not in sources:
            sources.append(item["source"])
    st.markdown("\n".join(f"- {src}" for src in sources))

    st.subheader("이 도구의 한계")
    st.markdown(
        "- 한 번의 측정값만으로 판정하므로 실제 진단과 다를 수 있습니다.\n"
        "- 공복 여부와 복용 중인 약은 반영하지 않습니다.\n"
        "- 19세 미만, 임산부에게는 적용할 수 없습니다."
    )
    st.markdown("**입력값은 계산에만 쓰이고 저장되지 않습니다.**")

# ---------------- 탭 2: 검증 결과 ----------------
with tab_check:
    # 화면이 다시 그려질 때마다 검사를 새로 실행합니다. (파일로 저장하지 않음)
    results = test_criteria.run_tests()
    total = len(results)
    passed = sum(1 for r in results if r["통과여부"])

    # 한국 시간(UTC+9)으로 실행 시각 표시
    # (인터넷에 배포한 서버는 다른 나라 시간일 수 있어서 직접 +9시간을 정해 줌)
    korea_time = timezone(timedelta(hours=9))
    run_time = datetime.now(korea_time).strftime("%Y-%m-%d %H:%M:%S")

    # 맨 위 요약: 모두 통과면 초록, 하나라도 실패면 빨강
    summary = f"**총 {total}개 중 {passed}개 통과**"
    if passed == total:
        st.success(summary)
    else:
        st.error(f"{summary}\n\n실패 {total - passed}개 (아래 표에서 빨간 줄)")
    st.write(f"실행 시각: {run_time} (한국 시간)")

    # 표 만들기: 통과여부(True/False)를 "통과"/"실패" 글자로 바꿈
    table = pd.DataFrame(results)
    table["통과여부"] = table["통과여부"].map({True: "통과", False: "실패"})

    def highlight_fail(row):
        """실패한 줄만 연한 빨간 배경 + 진한 빨간 굵은 글씨로 칠합니다."""
        if row["통과여부"] == "실패":
            style = "background-color: #fde2e2; color: #8a1c1c; font-weight: bold;"
        else:
            style = ""
        return [style] * len(row)

    st.dataframe(table.style.apply(highlight_fail, axis=1),
                 hide_index=True, width="stretch")
