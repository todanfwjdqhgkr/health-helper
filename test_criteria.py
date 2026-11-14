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
#                    / 이용 대상 / 대사증후군
#     "입력값"     : 항목에 필요한 값들 (이름은 아래 표 참고)
#     "기대판정"   : 정상 / 주의 / 위험 / 입력 오류 / 판정 안 함
#                    (이용 대상은 이용 가능 / 판정 안 함)
#                    (대사증후군은 대사증후군 의심 / 대사증후군 아님 / 판정 불가)
#     "기대urgent" : True 또는 False (검사하지 않으려면 이 줄을 아예 빼기)
#                    입력 오류·판정 안 함·이용 대상은 빠른 진료 권고가 없으므로 실제값이 False입니다.
#     "기대해당개수", "기대해당기준" : 대사증후군 케이스에서만 씁니다. (검사하지 않으려면 빼기)
#                    해당 개수(n/5)와 해당하는 기준 이름 목록
#                    기준 이름: 허리둘레 / 혈압 / 공복혈당 / 중성지방 / HDL 콜레스테롤
#     "기대차이"   : 정상 범위 경계까지의 차이 (검사하지 않으려면 이 줄을 아예 빼기)
#                    {막대 이름: 차이} 모양. 막대 이름은 bmi/waist/sbp/dbp/glucose/tc/ldl/hdl/tg
#                    예) {"glucose": 10}, 혈압은 {"sbp": 15, "dbp": 5}, BMI는 kg 단위
#                    소수 첫째 자리까지 비교합니다.
#     "메모"       : 이 케이스를 넣은 이유와 근거 (비교하지 않음, 참고용)
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
#     이용 대상    : age(나이), sex("남"/"여"/None), pregnant(임신 중이면 True, 아니면 False)
#                    -> criteria.check_eligibility로 검사합니다.
#                       eligible=True 이면 "이용 가능", False 이면 "판정 안 함"
#     대사증후군   : waist, sbp, dbp, glucose, tg, hdl, sex
#                    -> criteria.judge_mets로 검사합니다. (빈칸·입력 오류는 입력 안 된 것으로 처리)
#   빈칸은 "" 로, 글자 입력은 "abc"처럼 따옴표 안에 적습니다.
# =====================================================================

TEST_CASES = [
    # ---- 공복혈당 경계값 (1~6) ----
    {"번호": 1, "항목": "공복혈당", "입력값": {"glucose": 69}, "기대판정": "주의", "기대urgent": False,
     "메모": "70 미만은 저혈당 기준(치료 중 환자 대상) - 기준대조 4번 메모 참고 / 근거: 당뇨병 진료지침 2025 Suppl. Table 5 (저혈당 Level 1 <70)"},
    {"번호": 2, "항목": "공복혈당", "입력값": {"glucose": 70}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 당뇨병 진료지침 2025 p.584 (Table 1)"},
    {"번호": 3, "항목": "공복혈당", "입력값": {"glucose": 99}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 당뇨병 진료지침 2025 p.584 (Table 1)"},
    {"번호": 4, "항목": "공복혈당", "입력값": {"glucose": 100}, "기대판정": "주의", "기대urgent": False,
     "메모": "공복혈당장애 / 근거: 당뇨병 진료지침 2025 p.584 (Table 1)"},
    {"번호": 5, "항목": "공복혈당", "입력값": {"glucose": 125}, "기대판정": "주의", "기대urgent": False,
     "메모": "공복혈당장애 / 근거: 당뇨병 진료지침 2025 p.584 (Table 1)"},
    {"번호": 6, "항목": "공복혈당", "입력값": {"glucose": 126}, "기대판정": "위험", "기대urgent": False,
     "메모": "당뇨병 범위 / 근거: 당뇨병 진료지침 2025 p.584 (Table 1)"},

    # ---- 혈압 경계값 (7~17) ----
    {"번호": 7, "항목": "혈압", "입력값": {"sbp": 119, "dbp": 79}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 8, "항목": "혈압", "입력값": {"sbp": 120, "dbp": 79}, "기대판정": "주의", "기대urgent": False,
     "메모": "주의혈압 / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 9, "항목": "혈압", "입력값": {"sbp": 119, "dbp": 80}, "기대판정": "주의", "기대urgent": False,
     "메모": "고혈압 전단계(이완기 80) / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 10, "항목": "혈압", "입력값": {"sbp": 129, "dbp": 79}, "기대판정": "주의", "기대urgent": False,
     "메모": "주의혈압 / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 11, "항목": "혈압", "입력값": {"sbp": 130, "dbp": 80}, "기대판정": "주의", "기대urgent": False,
     "메모": "고혈압 전단계 / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 12, "항목": "혈압", "입력값": {"sbp": 139, "dbp": 89}, "기대판정": "주의", "기대urgent": False,
     "메모": "고혈압 전단계 / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 13, "항목": "혈압", "입력값": {"sbp": 140, "dbp": 79}, "기대판정": "위험", "기대urgent": False,
     "메모": "1기 고혈압(수축기 단독) / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 14, "항목": "혈압", "입력값": {"sbp": 119, "dbp": 90}, "기대판정": "위험", "기대urgent": False,
     "메모": "이완기 단독 고혈압(2026 신설) / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 15, "항목": "혈압", "입력값": {"sbp": 179, "dbp": 100}, "기대판정": "위험", "기대urgent": False,
     "메모": "2기 고혈압, 180/110 미만 / 근거: 고혈압 진료지침 2026 p.4/21 (Table 1)"},
    {"번호": 16, "항목": "혈압", "입력값": {"sbp": 180, "dbp": 100}, "기대판정": "위험", "기대urgent": True,
     "메모": "수축기 180 이상 / 근거: 고혈압 진료지침 2026 p.8/21 (응급 기준), p.4/21"},
    {"번호": 17, "항목": "혈압", "입력값": {"sbp": 150, "dbp": 110}, "기대판정": "위험", "기대urgent": True,
     "메모": "이완기 110 이상 / 근거: 고혈압 진료지침 2026 p.8/21 (응급 기준), p.4/21"},

    # ---- BMI 경계값 (18~23) : "BMI 계산값"은 참고용 메모이며 비교하지 않음 ----
    {"번호": 18, "항목": "BMI", "입력값": {"height": 160, "weight": 47.1}, "기대판정": "주의", "기대urgent": False,
     "메모": "저체중 / BMI 계산값 18.4(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 19, "항목": "BMI", "입력값": {"height": 160, "weight": 47.4}, "기대판정": "정상", "기대urgent": False,
     "메모": "BMI 계산값 18.5(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 20, "항목": "BMI", "입력값": {"height": 160, "weight": 58.6}, "기대판정": "정상", "기대urgent": False,
     "메모": "BMI 계산값 22.9(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 21, "항목": "BMI", "입력값": {"height": 160, "weight": 58.9}, "기대판정": "주의", "기대urgent": False,
     "메모": "비만 전단계 / BMI 계산값 23(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 22, "항목": "BMI", "입력값": {"height": 160, "weight": 63.7}, "기대판정": "주의", "기대urgent": False,
     "메모": "비만 전단계 / BMI 계산값 24.9(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 23, "항목": "BMI", "입력값": {"height": 160, "weight": 64.0}, "기대판정": "위험", "기대urgent": False,
     "메모": "1단계 비만 / BMI 계산값 25(참고용) / 근거: 비만 진료지침 2022 p.123 (Table 2)"},

    # ---- 허리둘레 경계값 (24~28) ----
    {"번호": 24, "항목": "허리둘레", "입력값": {"waist": 89, "sex": "남"}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 25, "항목": "허리둘레", "입력값": {"waist": 90, "sex": "남"}, "기대판정": "주의", "기대urgent": False,
     "메모": "복부비만 / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 26, "항목": "허리둘레", "입력값": {"waist": 84, "sex": "여"}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 27, "항목": "허리둘레", "입력값": {"waist": 85, "sex": "여"}, "기대판정": "주의", "기대urgent": False,
     "메모": "복부비만 / 근거: 비만 진료지침 2022 p.123 (Table 2)"},
    {"번호": 28, "항목": "허리둘레", "입력값": {"waist": 90, "sex": None}, "기대판정": "판정 안 함", "기대urgent": False,
     "메모": "성별이 없으면 성별별 기준(남 90/여 85) 적용 불가 / 근거: 비만 진료지침 2022 p.123 (Table 2)"},

    # ---- 총콜레스테롤 경계값 (29~32) ----
    {"번호": 29, "항목": "총콜레스테롤", "입력값": {"tc": 199}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 30, "항목": "총콜레스테롤", "입력값": {"tc": 200}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 31, "항목": "총콜레스테롤", "입력값": {"tc": 239}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 32, "항목": "총콜레스테롤", "입력값": {"tc": 240}, "기대판정": "위험", "기대urgent": False,
     "메모": "높음 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},

    # ---- LDL 경계값 (33~38) ----
    {"번호": 33, "항목": "LDL", "입력값": {"ldl": 129}, "기대판정": "정상", "기대urgent": False,
     "메모": "원문 정상(100~129) / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 34, "항목": "LDL", "입력값": {"ldl": 130}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 35, "항목": "LDL", "입력값": {"ldl": 159}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 36, "항목": "LDL", "입력값": {"ldl": 160}, "기대판정": "위험", "기대urgent": False,
     "메모": "높음 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 37, "항목": "LDL", "입력값": {"ldl": 189}, "기대판정": "위험", "기대urgent": False,
     "메모": "높음(190 미만) / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 38, "항목": "LDL", "입력값": {"ldl": 190}, "기대판정": "위험", "기대urgent": True,
     "메모": "매우 높음(190 이상) / 근거: 이상지질혈증 진료지침 제5판 p.43, p.33 (표 2-1)"},

    # ---- HDL 경계값 (39~40) ----
    {"번호": 39, "항목": "HDL", "입력값": {"hdl": 39}, "기대판정": "위험", "기대urgent": False,
     "메모": "낮음 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 40, "항목": "HDL", "입력값": {"hdl": 40}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},

    # ---- 중성지방 경계값 (41~46) ----
    {"번호": 41, "항목": "중성지방", "입력값": {"tg": 149}, "기대판정": "정상", "기대urgent": False,
     "메모": "근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 42, "항목": "중성지방", "입력값": {"tg": 150}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 43, "항목": "중성지방", "입력값": {"tg": 199}, "기대판정": "주의", "기대urgent": False,
     "메모": "경계 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 44, "항목": "중성지방", "입력값": {"tg": 200}, "기대판정": "위험", "기대urgent": False,
     "메모": "높음 / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 45, "항목": "중성지방", "입력값": {"tg": 499}, "기대판정": "위험", "기대urgent": False,
     "메모": "높음(500 미만) / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},
    {"번호": 46, "항목": "중성지방", "입력값": {"tg": 500}, "기대판정": "위험", "기대urgent": True,
     "메모": "매우 높음(500 이상) / 근거: 이상지질혈증 진료지침 제5판 p.33 (표 2-1)"},

    # ---- 입력 오류 (47~52) ----
    {"번호": 47, "항목": "혈압", "입력값": {"sbp": 400, "dbp": 80}, "기대판정": "입력 오류", "기대urgent": False,
     "메모": "근거: 프로그램 규칙(입력 허용 범위)"},
    {"번호": 48, "항목": "혈압", "입력값": {"sbp": 80, "dbp": 120}, "기대판정": "입력 오류", "기대urgent": False,
     "메모": "근거: 프로그램 규칙(이완기는 수축기보다 작아야 함)"},
    {"번호": 49, "항목": "공복혈당", "입력값": {"glucose": -5}, "기대판정": "입력 오류", "기대urgent": False,
     "메모": "근거: 프로그램 규칙"},
    {"번호": 50, "항목": "공복혈당", "입력값": {"glucose": "abc"}, "기대판정": "입력 오류", "기대urgent": False,
     "메모": "abc (글자) / 근거: 프로그램 규칙"},
    {"번호": 51, "항목": "공복혈당", "입력값": {"glucose": ""}, "기대판정": "판정 안 함", "기대urgent": False,
     "메모": "근거: 프로그램 규칙(빈칸은 카드 없음)"},
    {"번호": 52, "항목": "BMI", "입력값": {"height": 50, "weight": 60}, "기대판정": "입력 오류", "기대urgent": False,
     "메모": "근거: 프로그램 규칙"},

    # ---- 이용 대상 확인 (53~55) : criteria.check_eligibility로 검사 ----
    # 표에 "임신 중 체크"가 적혀 있지 않은 53, 54번은 체크하지 않은 것으로 보고 pregnant=False
    {"번호": 53, "항목": "이용 대상", "입력값": {"age": 18, "sex": "남", "pregnant": False}, "기대판정": "판정 안 함", "기대urgent": False,
     "메모": "근거: 기획(19세 미만 제외)"},
    {"번호": 54, "항목": "이용 대상", "입력값": {"age": 19, "sex": "남", "pregnant": False}, "기대판정": "이용 가능", "기대urgent": False,
     "메모": "근거: 기획(성인)"},
    {"번호": 55, "항목": "이용 대상", "입력값": {"age": 30, "sex": "여", "pregnant": True}, "기대판정": "판정 안 함", "기대urgent": False,
     "메모": "근거: 기획(임산부 제외)"},

    # ---- 대사증후군 (M1~M6) : criteria.judge_mets로 검사 ----
    # 기대값은 팀 표(이전에 주석으로 남겨 둔 내용) 그대로입니다.
    # 근거: Grundy 2005 p.2739 (Table 2) + Lee 2007 p.72 / 빠른 진료 권고: 모두 아니오
    {"번호": "M1", "항목": "대사증후군",
     "입력값": {"waist": 80, "sbp": 110, "dbp": 70, "glucose": 90, "tg": 100, "hdl": 55, "sex": "남"},
     "기대판정": "대사증후군 아님", "기대urgent": False, "기대해당개수": 0, "기대해당기준": [],
     "메모": "0/5 해당"},
    {"번호": "M2", "항목": "대사증후군",
     "입력값": {"waist": 92, "sbp": 135, "dbp": 80, "glucose": 90, "tg": 100, "hdl": 55, "sex": "남"},
     "기대판정": "대사증후군 아님", "기대urgent": False, "기대해당개수": 2, "기대해당기준": ["허리둘레", "혈압"],
     "메모": "2/5 해당 (허리, 혈압)"},
    {"번호": "M3", "항목": "대사증후군",
     "입력값": {"waist": 92, "sbp": 135, "dbp": 80, "glucose": 105, "tg": 100, "hdl": 55, "sex": "남"},
     "기대판정": "대사증후군 의심", "기대urgent": False, "기대해당개수": 3,
     "기대해당기준": ["허리둘레", "혈압", "공복혈당"],
     "메모": "3/5 해당 (허리, 혈압, 혈당)"},
    {"번호": "M4", "항목": "대사증후군",
     "입력값": {"waist": 88, "sbp": 140, "dbp": 90, "glucose": 110, "tg": 180, "hdl": 45, "sex": "여"},
     "기대판정": "대사증후군 의심", "기대urgent": False, "기대해당개수": 5,
     "기대해당기준": ["허리둘레", "혈압", "공복혈당", "중성지방", "HDL 콜레스테롤"],
     "메모": "5/5 해당 (허리 88≥85, 혈압, 혈당, 중성지방, HDL 45<50)"},
    {"번호": "M5", "항목": "대사증후군",
     "입력값": {"waist": 92, "sbp": 135, "dbp": 80, "glucose": "", "tg": "", "hdl": 55, "sex": "남"},
     "기대판정": "판정 불가", "기대urgent": False, "기대해당개수": 2, "기대해당기준": ["허리둘레", "혈압"],
     "메모": "확인된 2개 해당 (허리, 혈압) + 빈칸 2개 → 3개 이상 여부 알 수 없음"},
    {"번호": "M6", "항목": "대사증후군",
     "입력값": {"waist": 80, "sbp": 110, "dbp": 70, "glucose": 105, "tg": 160, "hdl": 45, "sex": "여"},
     "기대판정": "대사증후군 의심", "기대urgent": False, "기대해당개수": 3,
     "기대해당기준": ["공복혈당", "중성지방", "HDL 콜레스테롤"],
     "메모": "3/5 해당 (혈당, 중성지방, HDL 45<50 / 허리 80은 해당 없음)"},

    # ---- 정상 범위 경계까지 차이 (56~59, 기존 17~20번) ----
    {"번호": 56, "항목": "공복혈당", "입력값": {"glucose": 110}, "기대판정": "주의", "기대차이": {"glucose": 10}, "메모": "100 미만 경계보다 10 높음"},
    {"번호": 57, "항목": "HDL", "입력값": {"hdl": 35}, "기대판정": "위험", "기대차이": {"hdl": 5}, "메모": "40 이상 경계보다 5 낮음(높아지는 방향)"},
    {"번호": 58, "항목": "혈압", "입력값": {"sbp": 135, "dbp": 85}, "기대판정": "주의", "기대차이": {"sbp": 15, "dbp": 5}, "메모": "수축기 120, 이완기 80 경계"},
    {"번호": 59, "항목": "BMI", "입력값": {"height": 170, "weight": 75}, "기대판정": "위험", "기대차이": {"bmi": 8.5}, "메모": "BMI 23이 되는 몸무게 66.47kg과의 차이"},

    # ---- 단위 착오 (60~61, 기존 21~22번 / mmol/L 값을 입력한 경우) ----
    {"번호": 60, "항목": "공복혈당", "입력값": {"glucose": 5.5}, "기대판정": "입력 오류", "메모": "mmol/L 값으로 보이는 작은 값"},
    {"번호": 61, "항목": "총콜레스테롤", "입력값": {"tc": 5.2}, "기대판정": "입력 오류", "메모": "mmol/L 값으로 보이는 작은 값"},
]


# =====================================================================
# 여기부터는 검사를 실행하는 코드입니다. (케이스를 바꿀 때는 손대지 않아도 됨)
# =====================================================================

import csv                 # csv 파일 저장용 (표준 라이브러리)
from pathlib import Path   # 파일 위치를 다루는 도구 (표준 라이브러리)

import criteria


# 항목 이름 -> (숫자 입력값 이름들, 판정 함수)
# app.py와 같은 순서·같은 방식으로 판정하도록 맞췄습니다.
# ("이용 대상"은 판정 함수가 아니라 check_eligibility로 따로 검사합니다.)
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

# LIMITS에 없는 입력값의 한국어 이름
EXTRA_NAMES = {"sex": "성별", "pregnant": "임신 중"}


def _show_inputs(inputs):
    """입력값을 사람이 읽기 쉬운 글자로 바꿉니다. 예) 수축기 혈압=120, 이완기 혈압=80"""
    parts = []
    for name, value in inputs.items():
        # 이름을 한국어로 (LIMITS에 있으면 그 이름, 없으면 EXTRA_NAMES에서 찾기)
        if name in criteria.LIMITS:
            korean = criteria.LIMITS[name]["name"]
        else:
            korean = EXTRA_NAMES.get(name, name)

        if value is True:
            shown = "예"
        elif value is False:
            shown = "아니오"
        elif value is None or value == "":
            shown = "(빈칸)"
        elif isinstance(value, str):
            shown = f'"{value}"'
        else:
            shown = str(value)
        parts.append(f"{korean}={shown}")
    return ", ".join(parts)


def _judge_eligibility(case):
    """
    "이용 대상" 케이스를 criteria.check_eligibility로 검사합니다.
      eligible=True  -> "이용 가능"
      eligible=False -> "판정 안 함"
    대상 확인 단계에는 빠른 진료 권고가 없으므로 urgent는 False입니다.
    """
    inputs = case["입력값"]
    result = criteria.check_eligibility(inputs.get("age"), inputs.get("sex"),
                                        inputs.get("pregnant", False))
    label = "이용 가능" if result["eligible"] else "판정 안 함"
    return label, False


def _judge_mets(case):
    """"대사증후군" 케이스를 criteria.judge_mets로 검사합니다. (결과 dict를 그대로 돌려줌)"""
    inputs = case["입력값"]
    return criteria.judge_mets(inputs.get("waist"), inputs.get("sbp"), inputs.get("dbp"),
                               inputs.get("glucose"), inputs.get("tg"), inputs.get("hdl"),
                               inputs.get("sex"))


def _judge_one(case):
    """
    케이스 1개를 app.py와 같은 순서로 판정합니다.
      1) 입력 검사(validate_input) -> 하나라도 오류면 "입력 오류"
      2) 빈칸이 있으면 "판정 안 함"
      3) 판정 함수 실행 -> 정상/주의/위험 (또는 판정 안 함)
    돌려주는 값: (실제 판정, 실제 urgent)
    입력 오류이거나 빈칸이라 판정하지 않으면 빠른 진료 권고도 없으므로 urgent는 False입니다.
    """
    if case["항목"] == "이용 대상":
        return _judge_eligibility(case)
    if case["항목"] == "대사증후군":
        result = _judge_mets(case)
        return result["label"], result["urgent"]

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
        return "입력 오류", False

    # 2) 빈칸 확인
    if "empty" in statuses:
        return "판정 안 함", False

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

        # 대사증후군 케이스: 해당 개수(n/5)와 해당 기준 이름도 비교
        if "기대해당개수" in case or "기대해당기준" in case:
            try:
                mets = _judge_mets(case)
                actual_count = mets["met_count"]
                actual_names = [ch["name"] for ch in mets["checks"] if ch["met"] is True]
            except Exception as error:
                actual_count, actual_names = None, []
                actual_text += f" / 대사증후군 계산 중 오류: {error}"
            if "기대해당개수" in case:
                passed = passed and (actual_count == case["기대해당개수"])
                expected_text += f" / 해당 {case['기대해당개수']}/5"
                actual_text += f" / 해당 {actual_count}/5"
            if "기대해당기준" in case:
                passed = passed and (sorted(actual_names) == sorted(case["기대해당기준"]))
                expected_text += " / 해당 기준: " + (", ".join(case["기대해당기준"]) or "없음")
                actual_text += " / 해당 기준: " + (", ".join(actual_names) or "없음")

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
            # 번호가 숫자(1)와 글자(M1)로 섞여 있어 표가 깨지지 않도록 모두 글자로 바꿉니다.
            "번호": str(case["번호"]),
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
