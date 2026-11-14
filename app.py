# =====================================================================
# app.py  -  건강검진 결과 해석 도우미의 "화면" 파일 (Streamlit)
# =====================================================================
# 기준값과 판정 규칙은 모두 criteria.py에 있고, 이 파일은 화면만 담당합니다.
#
# [화면 구성]
#   탭 1 "결과 해석" : 안전 안내 -> 사용 방법 -> 시연 버튼 -> 입력칸(공복 안내·공복 아님 체크 포함)
#                      -> 결과 보기/모두 지우기 -> 판정 근거 보기 체크 -> 결과 요약
#                      -> 결과 카드(판정 + 내 수치 위치 막대) -> 대사증후군 체크
#                      -> "수치가 달라지면?" 체험 -> 의료진용 한 줄 요약 -> 결과 파일 다운로드
#                      -> 용어 사전 -> 출처·한계·저장 안내
#   탭 2 "검증 결과" : 검증 방법 안내 + test_criteria.py의 자동 검사 결과를 표로 보여 줌
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

# 시연용 가상 수치 (팀의 [예시수치] 표). 나중에 이 딕셔너리만 바꾸면 됩니다.
# ※ 소수점 칸(키·몸무게·허리·혈당·지질)은 170.0처럼 소수로, 나머지(나이·혈압)는 정수로 적어야 합니다.
# ※ 표의 "임신 중"은 모두 "아니오"입니다. 예시를 불러오면 임신 체크가 해제됩니다(load_example).
EXAMPLES = {
    "정상 예시": {
        "sex": "남", "age": 35, "height": 175.0, "weight": 68.0, "waist": 82.0,
        "sbp": 116, "dbp": 74, "glucose": 88.0,
        "tc": 175.0, "ldl": 95.0, "hdl": 58.0, "tg": 90.0,
    },
    "주의 예시": {
        "sex": "여", "age": 52, "height": 158.0, "weight": 60.0, "waist": 87.0,
        "sbp": 128, "dbp": 82, "glucose": 108.0,
        "tc": 215.0, "ldl": 142.0, "hdl": 52.0, "tg": 165.0,
    },
    "위험 예시": {
        "sex": "남", "age": 63, "height": 170.0, "weight": 82.0, "waist": 98.0,
        "sbp": 185, "dbp": 112, "glucose": 145.0,
        "tc": 265.0, "ldl": 195.0, "hdl": 36.0, "tg": 280.0,
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
    st.session_state.pop("not_fasting", None)  # 공복 아님 체크도 해제
    for k in NUMBER_KEYS:
        st.session_state[k] = example[k]
    st.session_state["show_result"] = False  # 결과는 "결과 보기"를 눌러야 나옴


def clear_all():
    """모든 입력칸을 비우고 결과를 숨깁니다."""
    st.session_state["sex"] = None
    st.session_state.pop("pregnant", None)
    st.session_state.pop("not_fasting", None)
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


# 결과지에 약어로 적히는 경우가 많은 항목은 약어를 함께 보여 줍니다.
ABBR = {"glucose": "FBS", "tc": "TC", "ldl": "LDL-C", "hdl": "HDL-C", "tg": "TG"}


def input_label(key):
    """입력칸 이름에 약어와 단위를 붙입니다. 예) "공복혈당 · FBS (mg/dL)" """
    limit = criteria.LIMITS[key]
    abbr = f" · {ABBR[key]}" if key in ABBR else ""
    return f"{limit['name']}{abbr} ({limit['unit']})"


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
        lines.append("**가능한 한 빨리 진료 권장**")

    lines.append(f"**{result['item']}**")
    lines.append(f"내 수치: **{value_text} {unit}**{extra}")
    lines.append(f"판정: **{result['label']}** ({result['sub_label']})")

    # 설명과 팁 (criteria.TEXTS에서 가져옴)
    text = criteria.TEXTS[key].get(result["sub_label"])
    if text:
        explain = text["explain"]
        # 빠른 진료(urgent)일 때는 빠른 진료 설명을 설명 뒤에 덧붙입니다.
        # (혈압 180/110 이상, LDL 190 이상, 중성지방 500 이상)
        urgent_text = criteria.TEXTS["urgent"].get(key)
        if result["urgent"] and urgent_text:
            explain += " " + urgent_text["explain"]
        lines.append(f"설명: {explain}")
        # 생활습관 팁: urgent일 때는 빠른 진료용 팁을 대신 보여 줍니다.
        tip = text["tip"]
        if result["urgent"] and urgent_text:
            tip = urgent_text["tip"]
        lines.append(f"생활습관 팁: {tip}")

    # 다음 행동: urgent가 가장 우선, 그다음 주의/위험
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

        # 공복이 아닌 상태라고 체크했으면 공복혈당·중성지방·LDL 카드에 안내 (판정은 그대로)
        if st.session_state.get("not_fasting") and key in criteria.FASTING_NOTE:
            st.caption(f"**⚠ {criteria.FASTING_NOTE[key]}**")

        # LDL은 개인 위험도를 반영하지 않는다는 안내 (늘 표시)
        if key == "ldl":
            st.caption(criteria.LDL_RISK_NOTE)

        # 판정 근거 (화면에서 "판정 근거 함께 보기"를 켰을 때만)
        if st.session_state.get("show_basis") and key in criteria.BASIS:
            st.caption(f"판정 근거: {criteria.BASIS[key]}")


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
                     + " (가능한 한 빨리 진료 권장 수치)")
    elif danger_items:
        lines.append("**먼저 확인할 항목**: " + ", ".join(danger_items)
                     + " (위험 범위에 해당하는 수치)")

    with box:
        with st.container(border=True):
            st.markdown("\n\n".join(lines))


def show_mets(result):
    """
    대사증후군 체크 카드를 보여 줍니다. (결과 카드들 아래)
      result : criteria.judge_mets()가 돌려준 dict
    결과 요약(정상·주의·위험 개수)에는 세지 않습니다.
    """
    # 판정 글자: 판정 불가일 때만 입력된 기준 개수를 붙입니다.
    label = result["label"]
    if result["status"] == "판정 불가":
        label += f"(입력 {result['known_count']}/5개)"

    lines = [
        "**대사증후군 체크**",
        f"판정: **{label}**",
        f"해당 개수: **{result['met_count']}/5**",
    ]

    # 기준 5개 각각의 결과
    marks = {True: "해당", False: "해당 없음", None: "입력 안 됨"}
    for ch in result["checks"]:
        lines.append(f"- {ch['name']} ({ch['rule']}): **{marks[ch['met']]}**")

    # 설명과 팁 (criteria.TEXTS["metabolic"]의 문구 그대로)
    text = criteria.TEXTS["metabolic"][result["status"]]
    lines.append(f"설명: {text['explain']}")
    lines.append(f"생활습관 팁: {text['tip']}")

    body = escape("\n\n".join(lines))

    with st.container(border=True):
        # 의심=노랑, 아님=초록, 판정 불가=파랑(안내)
        if result["status"] == "의심":
            st.warning(body)
        elif result["status"] == "아님":
            st.success(body)
        else:
            st.info(body)
        st.caption("원래 기준은 혈압·혈당·지질 약을 복용 중이면 해당으로 셉니다. "
                   "이 도구는 복용 약을 반영하지 않습니다.")
        st.caption("HDL 기준이 위 카드와 다른 이유: 대사증후군 기준은 여성에게 50 미만을 적용합니다.")
        if st.session_state.get("not_fasting"):
            st.caption(f"**⚠ {criteria.FASTING_NOTE['mets']}**")
        if st.session_state.get("show_basis"):
            st.caption(f"판정 근거: {criteria.BASIS['mets']}")


# 의료진용 한 줄 요약에 쓰는 약어 (결과지·진료 기록에서 흔히 쓰는 표기)
SHORT_NAMES = {"bmi": "BMI", "waist": "WC", "bp": "BP", "glucose": "FBS",
               "tc": "TC", "ldl": "LDL-C", "hdl": "HDL-C", "tg": "TG"}


def make_clinician_line(report_rows, mets):
    """
    의료진용 한 줄 요약을 만듭니다.
    예) BMI 24.0 | WC 87cm | BP 128/82 | FBS 108 | TC 215 | LDL-C 142 | HDL-C 52 | TG 165 | MetS 3/5
    판정된 항목의 수치만 넣고, 성별·나이는 넣지 않습니다.
    """
    parts = []
    for key, r in report_rows:
        value = r["value"]
        if isinstance(value, tuple):
            text = f"{fmt(value[0])}/{fmt(value[1])}"
        elif key == "bmi":
            text = f"{value:.1f}"
        elif key == "waist":
            text = f"{fmt(value)}cm"
        else:
            text = fmt(value)
        parts.append(f"{SHORT_NAMES[key]} {text}")
    if mets is not None:
        parts.append(f"MetS {mets['met_count']}/5")
    if st.session_state.get("not_fasting"):
        parts.append("비공복")
    return " | ".join(parts)


def make_report_html(report_rows, judged, mets):
    """
    결과 파일(검진결과_해석.html)의 내용을 글자로 만듭니다.
    파일은 서버나 컴퓨터에 저장하지 않고, 버튼을 누른 사람에게만 내려받게 합니다.
    성별·나이는 넣지 않습니다. (개인정보 최소화)
    """
    e = html.escape   # 글자를 HTML에 안전하게 넣는 도구
    count = {"normal": 0, "caution": 0, "danger": 0}
    for r in judged:
        count[r["level"]] += 1
    now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
    # 공복이 아닌 상태라고 체크했으면 파일에도 표시
    fasting_line = " · <b>공복이 아닌 상태에서 검사함</b>" if st.session_state.get("not_fasting") else ""

    # 판정 결과 표
    rows = []
    for key, r in report_rows:
        value = r["value"]
        if isinstance(value, tuple):
            value_text = f"{fmt(value[0])}/{fmt(value[1])}"
        elif key == "bmi":
            value_text = f"{value:.1f}"
        else:
            value_text = fmt(value)
        unit = criteria.CRITERIA[key]["unit"]
        judge_text = f"{r['label']} ({r['sub_label']})"
        if r["urgent"]:
            judge_text += " · 가능한 한 빨리 진료 권장"
        rows.append(f"<tr><td>{e(r['item'])}</td><td>{e(value_text)} {e(unit)}</td>"
                    f"<td class='{r['level']}'>{e(judge_text)}</td></tr>")

    # 먼저 확인할 항목
    urgent_items = [r["item"] for r in judged if r["urgent"]]
    danger_items = [r["item"] for r in judged if r["level"] == "danger"]
    first = ""
    if urgent_items:
        first = "먼저 확인할 항목: " + ", ".join(urgent_items) + " (가능한 한 빨리 진료 권장 수치)"
    elif danger_items:
        first = "먼저 확인할 항목: " + ", ".join(danger_items) + " (위험 범위에 해당하는 수치)"

    # 대사증후군
    mets_html = ""
    if mets is not None:
        label = mets["label"]
        if mets["status"] == "판정 불가":
            label += f"(입력 {mets['known_count']}/5개)"
        marks = {True: "해당", False: "해당 없음", None: "입력 안 됨"}
        items = "".join(f"<li>{e(ch['name'])} ({e(ch['rule'])}): {marks[ch['met']]}</li>"
                        for ch in mets["checks"])
        mets_html = (f"<h2>대사증후군 체크</h2><p>판정: <b>{e(label)}</b> · 해당 {mets['met_count']}/5</p>"
                     f"<ul>{items}</ul>"
                     "<p class='small'>원래 기준은 혈압·혈당·지질 약을 복용 중이면 해당으로 셉니다. "
                     "이 도구는 복용 약을 반영하지 않습니다.</p>")

    # 출처
    sources = []
    for item in criteria.CRITERIA.values():
        if item["source"] not in sources:
            sources.append(item["source"])
    source_html = "".join(f"<li>{e(src)}</li>" for src in sources)

    return f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>건강검진 결과 해석</title>
<style>
  @page {{ size: A4; margin: 14mm; }}
  body {{ font-family: sans-serif; font-size: 11pt; color: #000; line-height: 1.45;
          -webkit-print-color-adjust: exact; print-color-adjust: exact; }}  /* 인쇄할 때도 배경색 유지 */
  h1 {{ font-size: 16pt; margin: 0 0 4px; }}
  h2 {{ font-size: 12pt; margin: 14px 0 4px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ border: 1px solid #555; padding: 4px 6px; text-align: left; }}
  th {{ background: #eee; }}
  td.normal {{ background: #e6f4ea; }}
  td.caution {{ background: #fff4d6; font-weight: bold; }}
  td.danger {{ background: #fde2e1; font-weight: bold; }}
  .box {{ border: 1px solid #555; padding: 6px 8px; margin: 8px 0; }}
  .small {{ font-size: 9pt; }}
  ul {{ margin: 4px 0; padding-left: 18px; }}
</style></head><body>
<h1>건강검진 결과 해석 (교육용)</h1>
<p class="small">만든 날짜: {now} (한국 시간){fasting_line}</p>
<div class="box"><b>결과 요약</b>: 정상 {count['normal']}개 · 주의 {count['caution']}개 · 위험 {count['danger']}개<br>{e(first)}</div>
<p class="small">의료진용 요약: {e(make_clinician_line(report_rows, mets))}</p>
<h2>판정 결과</h2>
<table><tr><th>항목</th><th>내 수치</th><th>판정</th></tr>{''.join(rows)}</table>
{mets_html}
<div class="box"><b>안전 안내</b><br>이 도구는 교육용이며 의학적 진단을 대신하지 않습니다.
한 번의 측정값만으로 판정하므로 실제 진단과 다를 수 있으며, 공복 여부와 복용 중인 약은 반영하지 않습니다.
19세 미만, 임산부에게는 적용할 수 없습니다.</div>
<h2>판정 기준 출처</h2><ul class="small">{source_html}</ul>
</body></html>"""


# "수치가 달라지면?" 체험에서 고를 수 있는 항목
#   이름: (슬라이더로 바꿀 입력칸들, 판정 함수, 위치 막대 이름들)
#   BMI는 키를 그대로 두고 몸무게만 바꿉니다. 허리둘레는 체험에 넣지 않습니다.
SIM_ITEMS = {
    "BMI (몸무게)":     (["weight"],       "bmi",     ["bmi"]),
    "혈압":             (["sbp", "dbp"],   "bp",      ["sbp", "dbp"]),
    "공복혈당":         (["glucose"],      "glucose", ["glucose"]),
    "총콜레스테롤":     (["tc"],           "tc",      ["tc"]),
    "LDL 콜레스테롤":   (["ldl"],          "ldl",     ["ldl"]),
    "HDL 콜레스테롤":   (["hdl"],          "hdl",     ["hdl"]),
    "중성지방":         (["tg"],           "tg",      ["tg"]),
}

# 판정에 쓰는 criteria의 기존 판정 함수 (새 기준 숫자 없음)
SIM_JUDGES = {
    "bmi": criteria.judge_bmi, "bp": criteria.judge_bp, "glucose": criteria.judge_glucose,
    "tc": criteria.judge_tc, "ldl": criteria.judge_ldl, "hdl": criteria.judge_hdl,
    "tg": criteria.judge_tg,
}


def show_simulator(s, status):
    """
    "수치가 달라지면 판정이 어떻게 바뀔까요?" 체험 상자를 보여 줍니다.
      s      : st.session_state (입력값)
      status : 입력칸별 검사 결과 ("ok"인 칸만 체험에 씀)
    - 슬라이더 값은 sim_로 시작하는 별도 이름에 보관하므로
      위쪽 입력칸과 결과 카드는 바뀌지 않습니다.
    - 판정은 criteria의 judge 함수, 막대는 criteria.position_info를 그대로 씁니다.
    """
    # 입력(검사 통과)한 항목만 선택지에 넣습니다. BMI는 키도 있어야 합니다.
    options = []
    for name, (fields, _, _) in SIM_ITEMS.items():
        needed = fields + (["height"] if name.startswith("BMI") else [])
        if all(status[f] == "ok" for f in needed):
            options.append(name)
    if not options:
        return   # 체험할 항목이 없으면 상자를 보여 주지 않음

    with st.expander("수치가 달라지면 판정이 어떻게 바뀔까요?"):
        st.info("판정 기준이 어디서 바뀌는지 이해하기 위한 체험입니다. 목표나 치료 계획이 아닙니다.")
        choice = st.selectbox("항목 고르기", options, key="sim_item")
        fields, judge_key, bar_names = SIM_ITEMS[choice]

        # ---- 슬라이더: 시작값 = 내가 입력한 값, 범위 = 위치 막대의 양 끝 ----
        sim = {}
        for f in fields:
            mine = float(s[f])
            if f == "weight":
                info = criteria.position_info("bmi", (s["height"], mine))
                low, high, step, unit = info["weight_min"], info["weight_max"], 0.1, "kg"
            else:
                info = criteria.position_info(f, mine)
                low, high, unit = info["bar_min"], info["bar_max"], info["unit"]
                step = 1.0
            # 내 값이 막대 끝보다 바깥이면, 슬라이더에서도 고를 수 있게 범위를 넓힘
            low, high = min(low, mine), max(high, mine)
            label = f"{criteria.LIMITS[f]['name']} ({unit}) · 내가 입력한 값 {fmt(mine)}"
            # 이름에 내 입력값을 넣어, 입력값이 바뀌면 슬라이더도 새로 시작하게 함
            sim[f] = st.slider(label, min_value=float(low), max_value=float(high),
                               value=mine, step=step, key=f"sim_{f}_{mine}")

        # ---- 판정: criteria의 판정 함수 그대로 ----
        if judge_key == "bmi":
            result = SIM_JUDGES["bmi"](s["height"], sim["weight"])
            shown_value = f"BMI {result['value']:.1f} (키 {fmt(s['height'])}cm, 몸무게 {fmt(sim['weight'])}kg)"
            bars = [criteria.position_info("bmi", (s["height"], sim["weight"]))]
        elif judge_key == "bp":
            # 이완기가 수축기보다 크거나 같으면 실제 입력에서도 오류이므로 판정하지 않음
            check = criteria.validate_input("dbp", sim["dbp"], systolic=sim["sbp"])
            if check != "ok":
                st.markdown(f"**체험 값: {fmt(sim['sbp'])}/{fmt(sim['dbp'])} mmHg**\n\n{escape(check)}")
                return
            result = SIM_JUDGES["bp"](sim["sbp"], sim["dbp"])
            shown_value = f"{fmt(sim['sbp'])}/{fmt(sim['dbp'])} mmHg"
            bars = [criteria.position_info("sbp", sim["sbp"]),
                    criteria.position_info("dbp", sim["dbp"])]
        else:
            f = fields[0]
            result = SIM_JUDGES[judge_key](sim[f])
            shown_value = f"{fmt(sim[f])} {criteria.CRITERIA[judge_key]['unit']}"
            bars = [criteria.position_info(f, sim[f])]

        line = f"체험 값 **{shown_value}** → 판정 **{result['label']}** ({result['sub_label']})"
        if result["urgent"]:
            line += " · 빠른 진료 권장 범위"
        st.markdown(escape(line))

        # 위치 막대: 결과 카드와 같은 그림 함수.
        # 체험에서는 "경계까지 차이" 문구를 빼서 목표 수치처럼 보이지 않게 합니다.
        bars = [dict(b, gap_text=None) for b in bars if b is not None]
        for info in bars:
            st.markdown(position_bar_html(info, show_title=len(bars) > 1),
                        unsafe_allow_html=True)
        st.caption("판정 글자와 막대만 바뀌며, 위쪽 입력칸과 결과 카드는 그대로입니다.")


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
    report_rows = []   # 결과 파일용: (항목 key, 판정 결과) 묶음

    def record_card(key, result, *args, **kwargs):
        """카드를 그리면서, 판정된 결과는 요약용 목록과 결과 파일용 목록에도 넣습니다."""
        if result["level"] is not None:
            judged.append(result)
            report_rows.append((key, result))
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

    # (6-1) 대사증후군 체크: 결과 카드 아래에 (수치를 하나라도 입력했을 때만)
    #       빈칸·입력 오류 값은 judge_mets 안에서 "입력 안 된 것"으로 처리합니다.
    mets = None
    if shown > 0:
        mets = criteria.judge_mets(s["waist"], s["sbp"], s["dbp"],
                                   s["glucose"], s["tg"], s["hdl"], sex)
        # 대사증후군 기준 5개 중 하나도 확인할 수 없으면(빈칸·입력 오류뿐) 카드를 숨깁니다.
        if mets["known_count"] > 0:
            show_mets(mets)
        else:
            mets = None

    # (6-2) "수치가 달라지면?" 체험 (대사증후군 카드 다음)
    if judged:
        show_simulator(s, status)

    # (7) 결과 요약 채우기 (판정된 항목이 있을 때만)
    if judged:
        show_summary(summary_box, judged)

    # (8) 의료진용 한 줄 요약 (판정된 항목이 있을 때만, 복사 버튼 있음)
    if judged:
        with st.expander("의료진용 한 줄 요약"):
            st.code(make_clinician_line(report_rows, mets), language=None, wrap_lines=True)
            st.caption("단위: 혈압 mmHg, 혈당·지질 mg/dL. 진료 때 보여 주거나 복사해 쓸 수 있습니다. "
                       "성별·나이는 넣지 않습니다.")

    # (9) 결과 파일 다운로드 버튼 (판정된 항목이 있을 때만)
    if judged:
        st.download_button(
            "결과 파일 다운로드",
            data=make_report_html(report_rows, judged, mets),
            file_name="검진결과_해석.html",
            mime="text/html",
            width="stretch",
        )
        st.caption("내려받은 파일을 크롬이나 엣지로 열고 Ctrl+P를 누르면 인쇄하거나 PDF로 저장할 수 있습니다. "
                   "휴대폰에서는 결과 화면을 캡처해 두는 편이 간편합니다. "
                   "성별·나이는 파일에 넣지 않습니다.")


# 입력칸마다 연결할 용어 (도움말 ? 아이콘에 criteria.GLOSSARY 설명을 보여 줌)
# 나이는 맞는 용어가 없어 도움말이 없습니다.
HELP_TERMS = {
    "height": "BMI", "weight": "BMI", "waist": "복부비만",
    "sbp": "수축기 혈압", "dbp": "이완기 혈압", "glucose": "공복혈당",
    "tc": "총콜레스테롤", "ldl": "LDL 콜레스테롤", "hdl": "HDL 콜레스테롤", "tg": "중성지방",
}


def number_box(key):
    """숫자 입력칸 1개를 만듭니다. 범위 검사는 criteria.validate_input이 합니다."""
    term = HELP_TERMS.get(key)
    help_text = f"{term}: {criteria.GLOSSARY[term]}" if term in criteria.GLOSSARY else None
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
                        key=key, placeholder=placeholder, help=help_text)
    else:
        st.number_input(label, value=None, step=1,
                        key=key, placeholder=placeholder, help=help_text)


# =====================================================================
# 6. 화면 그리기
# =====================================================================
st.title("건강검진 결과 해석 도우미")

tab_result, tab_check = st.tabs(["결과 해석", "검증 결과"])

# ---------------- 탭 1: 결과 해석 ----------------
with tab_result:
    # 6-1. 안전 안내 (항상 보임)
    st.info("이 도구는 교육용이며 의학적 진단을 대신하지 않습니다.\n\n"
            "19세 미만, 임산부는 기준이 달라 이용할 수 없습니다.\n\n"
            "약을 드시는 중이거나 당뇨병·심혈관질환 등이 있으면 같은 수치라도 의미가 다를 수 있습니다.")

    # 6-1-1. 처음 쓰는 사람을 위한 짧은 사용 안내 (접어 둠)
    with st.expander("처음이신가요? 사용 방법"):
        st.markdown("1. 결과지의 수치를 아래 칸에 입력합니다. (나이는 꼭, 나머지는 있는 것만)\n"
                    "2. **결과 보기**를 누르면 항목별 판정과 설명이 나옵니다.\n"
                    "3. 예시 버튼으로 먼저 체험해 볼 수 있습니다.")

    # 6-2. 시연 버튼 3개 (휴대폰에서는 자동으로 세로로 쌓임)
    st.subheader("예시로 해 보기")
    cols = st.columns(3)
    for col, name in zip(cols, EXAMPLES):
        col.button(name, on_click=load_example, args=(name,), width="stretch")

    # 6-3. 입력칸
    st.subheader("내 검진 수치 입력")
    st.radio("성별 (허리둘레·대사증후군 판정에 필요)", ["남", "여"], index=None, horizontal=True, key="sex")
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

    st.caption("공복혈당은 8시간 이상, 중성지방과 LDL(계산값)은 12시간(어려우면 최소 9시간) 이상 "
               "공복 상태에서 잰 값을 기준으로 판정합니다.")
    st.checkbox("공복이 아닌 상태에서 검사했어요", key="not_fasting")
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
        st.checkbox("판정 근거(지침·쪽 번호) 함께 보기", key="show_basis")
        show_all_results()

    # 6-5-1. 용어 사전 (항상 보임)
    with st.expander("용어 사전"):
        for term, explain in criteria.GLOSSARY.items():
            st.markdown(f"**{term}**  \n{escape(explain)}")

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
    # 검증 방법 안내 (통과 개수 위)
    st.markdown("이 앱의 판정 기준은 학회 진료지침 원문에서 가져왔습니다. "
                "정답표는 코드와 별도로 지침만 보고 만들었고, "
                "아래 표는 그 정답과 프로그램의 판정을 자동으로 비교한 결과입니다.")

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
