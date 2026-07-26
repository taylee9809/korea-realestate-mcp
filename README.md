# korea-realestate-mcp

부동산 실거래가/법령/양도세 계산을 API로 직접 확인하는 개인용 MCP 서버.
재건축 단계 추적은 포함하지 않음(지자체별 공공사이트에서 수동 확인 또는 웹서치 사용).

## 1. API 키 발급 (직접 해야 함)

### (1) 국토교통부 실거래가 - 공공데이터포털
아래 5개 데이터셋을 **각각 개별로** 활용신청해야 함 (같은 계정/서비스키를 공유하지만,
승인은 데이터셋별로 따로 남). 승인 후에도 실제 반영까지 2~3일 걸릴 수 있음(포털엔 바로
"승인"으로 표시돼도 게이트웨이 반영은 별도).

| 데이터셋 | 링크 |
|---|---|
| 단독/다가구 매매 | https://www.data.go.kr/data/15126465/openapi.do |
| 오피스텔 매매 | https://www.data.go.kr/data/15126464/openapi.do |
| 아파트 매매 | https://www.data.go.kr/data/15126469/openapi.do |
| 상업업무용 부동산 매매 | https://www.data.go.kr/data/15126463/openapi.do |
| 토지 매매 | data.go.kr에서 "국토교통부 토지 매매 신고 자료" 검색 |
| 건축HUB 건축물대장정보 | https://www.data.go.kr/data/15134735/openapi.do |

1. https://www.data.go.kr 가입
2. 위 데이터셋 각각 활용신청 → 승인 대기
3. 마이페이지에서 서비스키(일반 인증키) 복사 (전부 동일한 키 사용)
4. **중요**: 엔드포인트 URL은 RTMSDataSvc 계열 명명 규칙(예: `RTMSDataSvcSHTrade`,
   `RTMSDataSvcNrgTrade`, `RTMSDataSvcLandTrade`)을 따라 작성했고 단독/다가구·아파트·오피스텔은
   실제 호출로 검증 완료. 상업업무용·토지는 아직 실제 호출 검증 전이므로, 승인 후 Swagger UI로
   재확인할 것.

### (2) 법제처 국가법령정보 Open API
1. https://open.law.go.kr 가입
2. OC(활용신청 시 사용한 이메일 아이디, @ 앞부분) 확인 — 별도 승인 절차 없이 바로 사용 가능

두 값을 `.env` 파일에 넣기 (`.env.example` 복사해서 사용):
```
MOLIT_SERVICE_KEY=발급받은키
LAW_OC=이메일아이디
```

## 2. 설치

```
cd korea-realestate-mcp
pip install -r requirements.txt
```

## 3. Claude Code에 등록

프로젝트 루트(또는 홈)의 `.mcp.json`에 추가:

```json
{
  "mcpServers": {
    "korea-realestate": {
      "command": "python",
      "args": ["C:/Users/User/Documents/korea-realestate-mcp/server.py"],
      "env": {
        "MOLIT_SERVICE_KEY": "발급받은키",
        "LAW_OC": "이메일아이디"
      }
    }
  }
}
```

## 4. 도구

- `get_house_trade_price(lawd_cd, deal_ymd)` — 단독/다가구 매매 실거래 조회
- `get_officetel_trade_price(lawd_cd, deal_ymd)` — 오피스텔 매매 실거래 조회
- `get_apt_trade_price(lawd_cd, deal_ymd)` — 아파트 매매 실거래 조회
- `get_commercial_trade_price(lawd_cd, deal_ymd)` — 상업업무용 부동산(근린생활시설·업무시설 등) 매매 실거래 조회
- `get_land_trade_price(lawd_cd, deal_ymd)` — 토지 매매 실거래 조회
  (5개 전부 파라미터 동일: 법정동코드 5자리 + 계약년월 6자리)
- `get_building_title_info(sigungu_cd, bjdong_cd, bun, ji)` — 건축물대장 표제부 조회
  (대지면적·연면적·용도·사용승인일 등). 시군구코드 5자리 + 법정동코드 뒤5자리 + 지번(본번/부번,
  4자리 0채움). 도로명주소 → 지번 변환은 별도(카카오맵 등) 필요, 이 도구는 지번 입력 후 상세정보만 조회.
- `search_law(query, target, display)` — 법령/행정규칙 검색.
  `target="law"`(기본값)면 법률/시행령/시행규칙, `target="admrul"`이면 행정규칙(고시) —
  **투기과열지구 지정, 조정대상지역 지정** 같은 부처 고시가 여기 포함됨. `target="ordin"`은 자치법규.
- `get_law_detail(doc_id, target)` — search_law 결과의 "법령일련번호"/"행정규칙일련번호"로
  조문·고시 원문 전체(제개정이유, 첨부파일 링크 등)를 조회. 지정지역 목록 같은 세부내용 확인용.
- `calc_transfer_tax(...)` — 양도소득세 계산. **세율표(tax_brackets)와 장기보유특별공제율은
  절대 기본값이 없음** — 호출 시 search_law로 확인한 최신 소득세법 시행령 별표 값을 직접 넘겨야 함.
  이유: 다주택 중과세율/공제율은 정책에 따라 자주 바뀌어서, 하드코딩하면 시점이 안 맞는 틀린
  계산이 나올 수 있기 때문.

### 커버리지 한계 (중요)
- `admrul` 검색은 부처가 "행정규칙"으로 등록한 고시만 잡힘 — 투기과열지구/조정대상지역처럼
  전국 단위 지정 고시는 잡히지만, 개별 정비구역의 토지거래허가구역 지정처럼 지역명이 제목에
  섞인 공고는 검색어가 안 맞으면 못 찾을 수 있음.
- 재건축/재개발 조합설립인가 등 정비사업 진행단계는 지자체(서울시 등)가 관리하는 데이터라
  법제처 API 대상이 아예 아님 — 이건 여전히 웹서치나 "정비사업 정보몽땅" 직접 확인이 필요함.
- 지정 고시가 "일부개정"이면 그 회차에 추가/제외된 지역만 나오고, 전체 누적 목록은 별도
  이력 조회가 필요할 수 있음.
- 도로명주소 → 지번 변환 API는 별도 미구현(주소정보누리집 juso.go.kr 활용신청 필요) —
  현재는 카카오맵 등으로 수동 변환 후 get_building_title_info에 지번 입력.

## 참고: 구분등기 다가구주택 관련

각 호실이 구분등기 되어 있으면 세법상 별도 주택으로 취급되어 다주택자 판정에 영향을 줄 수 있음.
정확한 판단은 반드시 `search_law`로 현재 시행 중인 소득세법/소득세법 시행령 조문을 확인하고,
필요하면 세무사 상담을 병행할 것 — 이 도구는 계산기일 뿐 세무 자문이 아님.
