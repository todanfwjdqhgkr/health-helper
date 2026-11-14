# 건강검진 결과 해석 도우미

성인이 건강검진 결과지의 수치를 입력하면 항목별로 정상·주의·위험을 판정하고, 쉬운 설명과 생활습관 팁, 다음 행동을 알려 주는 교육용 웹앱입니다.

> 이 도구는 교육용이며 의학적 진단을 대신하지 않습니다. 19세 미만과 임산부는 기준이 달라 이용할 수 없습니다.

## 1. 실행 방법

### 방법 ① 인터넷 링크 (설치 필요 없음)

https://khu-health-checkup.streamlit.app/

무료 서버라서 한동안 접속이 없으면 앱이 잠들어 있을 수 있습니다. 깨우기 버튼(Yes, get this app back up 등)이 보이면 누르고 1분 정도 기다리면 됩니다.

### 방법 ② 내 컴퓨터에서 실행 (Windows 기준)

1. 파이썬 설치: python.org에서 Python 3.12 이상을 설치합니다. 설치 첫 화면에서 "Add python.exe to PATH"를 체크합니다. (개발은 Python 3.14에서 했습니다.)
2. 이 폴더(app.py가 있는 폴더)에서 명령 프롬프트를 열고 아래를 차례로 입력합니다.

```
py -m pip install streamlit
py -m streamlit run app.py
```

3. 브라우저가 자동으로 열리고 앱이 나타납니다. 열리지 않으면 주소창에 `localhost:8501`을 입력합니다.

필요한 라이브러리는 streamlit 하나뿐입니다(requirements.txt). API 키, 계정, 유료 서비스는 필요하지 않습니다.

## 2. 사용 방법과 예시 입력

1. 결과지의 수치를 입력합니다. 나이는 꼭 입력하고, 나머지는 있는 것만 입력하면 됩니다.
2. **결과 보기**를 누르면 항목별 판정 카드가 나옵니다.
3. 화면 위쪽의 **정상 예시 / 주의 예시 / 위험 예시** 버튼을 누르면 아래 가상 수치가 자동으로 들어갑니다. (모두 가상 수치입니다.)

| 구분 | 성별 | 나이 | 키 | 몸무게 | 허리 | 혈압 | 공복혈당 | 총콜 | LDL | HDL | 중성지방 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 정상 예시 | 남 | 35 | 175 | 68 | 82 | 116/74 | 88 | 175 | 95 | 58 | 90 |
| 주의 예시 | 여 | 52 | 158 | 60 | 87 | 128/82 | 108 | 215 | 142 | 52 | 165 |
| 위험 예시 | 남 | 63 | 170 | 82 | 98 | 185/112 | 145 | 265 | 195 | 36 | 280 |

예상 결과

- 정상 예시: 8개 항목 모두 정상, 대사증후군 기준 해당 0/5
- 주의 예시: HDL만 정상, 나머지 7개는 주의, 대사증후군 의심 3/5 (허리둘레·공복혈당·중성지방)
- 위험 예시: 허리둘레는 주의, 나머지 7개는 위험, 혈압과 LDL에 "가능한 한 빨리 진료 권장" 표시, 대사증후군 의심 5/5

## 3. 주요 기능

- 항목별 판정 카드: BMI, 허리둘레, 혈압, 공복혈당, 총콜레스테롤, LDL, HDL, 중성지방
- 판정 기준 안에서 내 수치의 위치를 보여 주는 막대와 "정상 범위 경계까지의 차이"
- 결과 요약(정상·주의·위험 개수)과 먼저 확인할 항목
- 대사증후군 체크(5개 기준 중 3개 이상이면 의심)
- 수치가 달라지면 판정이 어떻게 바뀌는지 보는 체험(슬라이더)
- 용어 사전, 결과 파일 다운로드(인쇄·PDF 저장용), 의료진용 한 줄 요약(복사 가능)
- 판정 근거(지침·쪽 번호) 보기, 공복이 아닌 상태 안내
- 안전 장치: 19세 미만·임산부 제외, 입력 오류 안내, 단위(mmol/L) 착오 안내, 빠른 진료가 필요한 수치 강조

## 4. 검증 방법

판정이 맞는지는 자동 검사로 확인합니다.

- 앱의 **검증 결과** 탭에서 바로 볼 수 있습니다.
- 내 컴퓨터에서는 `py test_criteria.py`를 실행하면 결과가 화면에 나오고 test_result.csv로도 저장됩니다.

검사 케이스 67개는 팀원이 코드를 보지 않고 진료지침 원문만 보고 정답을 따로 만든 것입니다. 모든 판정 경계값(예: 공복혈당 99·100·125·126), 입력 오류, 이용 대상 제외, 대사증후군을 포함하며, 67개 모두 통과했습니다. 이후 사용자 관점 검토와 최종 점검을 거쳐 문구와 안내를 다듬었으며, 이 과정에서 AI 도구를 교차 검토에 활용했습니다.

## 5. 판정 기준 출처

1. Haam JH, Kim BT, Kim EM, et al. Diagnosis of obesity: 2022 update of clinical practice guidelines for obesity by the Korean Society for the Study of Obesity. J Obes Metab Syndr. 2023;32(2):121-129. (BMI, 허리둘레: p.123 Table 2)
2. Lee EM, Cho IJ, Kang HT, et al. Highlights of the 2026 Korean Society of Hypertension guidelines for the management of hypertension: what's new and what has changed. Clin Hypertens. 2026;32:e31. (혈압 분류: p.3 Table 1, 180/110: p.8)
3. Kang S, Kang SM, Choi JH, et al. 2025 clinical practice guidelines for diabetes management in Korea: recommendation of the Korean Diabetes Association. Diabetes Metab J. 2025;49(4):582-783. (공복혈당: p.584 Table 1)
4. 한국지질·동맥경화학회 진료지침위원회. 이상지질혈증 진료지침 제5판. 2022. (지질 분류: p.33 표 2-1)
5. Grundy SM, Cleeman JI, Daniels SR, et al. Diagnosis and management of the metabolic syndrome: an American Heart Association/National Heart, Lung, and Blood Institute scientific statement. Circulation. 2005;112(17):2735-2752. (대사증후군: p.2739 Table 2)
6. Lee SY, Park HS, Kim DJ, et al. Appropriate waist circumference cutoff points for central obesity in Korean adults. Diabetes Res Clin Pract. 2007;75(1):72-80. (한국인 허리둘레 90/85 cm)

생활습관 팁과 설명 문구의 출처(쪽 번호)는 criteria.py의 각 문구 위 주석에 적혀 있습니다.

## 6. 한계

- 한 번의 측정값만으로 판정하므로 실제 진단과 다를 수 있습니다. 진단은 반복 측정과 의료진의 판단이 필요합니다.
- 공복 여부와 복용 중인 약은 반영하지 않습니다. 대사증후군 원래 기준은 약 복용도 해당으로 셉니다.
- 지질 분류는 개인의 심혈관질환 위험도를 고려하지 않은 것으로, 지침에서도 치료의 근거나 목표로 쓰지 않는다고 밝히고 있습니다(이상지질혈증 진료지침 제5판 p.33).
- 공복혈당 70 mg/dL 미만 기준은 원래 당뇨병 환자의 저혈당 분류 기준을 참고한 것입니다.
- 19세 미만과 임산부에게는 적용할 수 없습니다.

## 7. 개인정보

- 입력값은 판정 계산에만 쓰이고 파일이나 데이터베이스에 저장되지 않습니다.
- 인터넷 링크로 실행할 때는 계산을 위해 입력값이 앱 서버로 전달되지만, 저장하지 않습니다.
- 결과 파일에는 성별과 나이를 넣지 않습니다.
- 개발과 테스트에는 가상 수치만 사용했고, 실제 환자 자료는 사용하지 않았습니다.

## 8. 파일 구성

| 파일 | 역할 |
| --- | --- |
| app.py | 화면 (Streamlit) |
| criteria.py | 기준값, 입력 허용 범위, 설명 문구, 용어, 판정 함수 |
| test_criteria.py | 자동 검사 67개 |
| requirements.txt | 필요한 라이브러리 목록 (streamlit) |
| code_explanation.md | 코드 구조와 데이터 흐름 설명 |

## 9. 개발 방법과 AI 사용

이 프로젝트는 바이브코딩 방식으로 진행했습니다. 기능 설계와 판정 규칙, 기준값 선정과 진료지침 원문 대조, 독립 정답표 작성과 자동 검증, 설명 문구 작성, 단계별 실행 확인과 수정 결정은 팀이 직접 했고, 코드 작성에는 Anthropic의 Claude를 도구로 활용했습니다.
