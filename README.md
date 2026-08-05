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
| 단독/다가구 전월세 | data.go.kr에서 "국토교통부 단독/다가구 전월세 자료" 검색 |
| 오피스텔 매매 | https://www.data.go.kr/data/15126464/openapi.do |
| 오피스텔 전월세 | data.go.kr에서 "국토교통부 오피스텔 전월세 자료" 검색 |
| 아파트 매매 | https://www.data.go.kr/data/15126469/openapi.do |
| 아파트 전월세 | data.go.kr에서 "국토교통부 아파트 전월세 자료" 검색 |
| 상업업무용 부동산 매매 | https://www.data.go.kr/data/15126463/openapi.do |
| 토지 매매 | data.go.kr에서 "국토교통부 토지 매매 신고 자료" 검색 |
| 연립다세대(빌라) 매매 | data.go.kr에서 "국토교통부 연립다세대 매매 실거래가 자료" 검색 |
| 연립다세대(빌라) 전월세 | data.go.kr에서 "국토교통부 연립다세대 전월세 자료" 검색 |
| 건축HUB 건축물대장정보 | https://www.data.go.kr/data/15134735/openapi.do |

1. https://www.data.go.kr 가입
2. 위 데이터셋 각각 활용신청 → 승인 대기
3. 마이페이지에서 서비스키(일반 인증키) 복사 (전부 동일한 키 사용)
4. **중요**: 엔드포인트 URL은 RTMSDataSvc 계열 명명 규칙(예: `RTMSDataSvcSHTrade`,
   `RTMSDataSvcNrgTrade`, `RTMSDataSvcLandTrade`)을 따라 작성했고 단독/다가구·아파트·오피스텔
   **매매**는 실제 호출로 검증 완료. 상업업무용·토지·전월세 4종·연립다세대 매매/전월세는
   아직 실제 호출 검증 전이므로, 승인 후 Swagger UI로 엔드포인트/파라미터를 반드시 재확인할 것.

### (2) 한국자산관리공사 온비드(공매) - 공공데이터포털
국토부와 별개 제공기관이지만 **data.go.kr 계정 단위 서비스키를 그대로 재사용** 가능
(실제 호출로 확인). 아래 5개 데이터셋 전부 구현+검증 완료 (공고목록은 당초 계획에
없었지만, 공고상세 조회에 필요한 pbancMngNo를 구하려면 반드시 필요해서 추가함).

| 데이터셋 | 링크 | 구현 상태 |
|---|---|---|
| 부동산 물건목록 | https://www.data.go.kr/data/15157207/openapi.do | ✅ 구현+검증 완료 |
| 부동산 물건상세 | https://www.data.go.kr/data/15157247/openapi.do | ✅ 구현+검증 완료 |
| 공고목록 | https://www.data.go.kr/data/15157216/openapi.do | ✅ 구현+검증 완료 (당초 계획에 없던 5번째 데이터셋 — 공고상세 조회에 필요한 pbancMngNo 확보용) |
| 공고상세 | https://www.data.go.kr/data/15157218/openapi.do | ✅ 구현+검증 완료 |
| 코드조회 | https://www.data.go.kr/data/15000920/openapi.do | ✅ 구현+검증 완료 |

### (3) 법제처 국가법령정보 Open API
1. https://open.law.go.kr 가입
2. OC(활용신청 시 사용한 이메일 아이디, @ 앞부분) 확인 — 별도 승인 절차 없이 바로 사용 가능

### (4) 도로명주소 API (주소 → 법정동코드/지번 변환)
1. https://business.juso.go.kr 가입 → Open API 신청
2. 별도 심사 없이 바로 승인키(confmKey) 발급됨 (무료)

### (5) 카카오 로컬 API (입지조건 — 지하철/학교/어린이집 거리)
1. https://developers.kakao.com 가입 → 애플리케이션 생성 → REST API 키 확인
2. **중요**: 키만 발급받으면 안 되고, 앱 설정의 "제품 설정 → 카카오맵"을 별도로
   활성화해야 함 — 안 하면 403 `OPEN_MAP_AND_LOCAL` 에러 (korea-realestate-qgis
   프로젝트에서 2026-08-04 실제로 겪음)

### (6) 온비드 입찰결과/통계, HUG 전세자금보증 — 미검증, 별도 활용신청 필요할 수 있음
`get_auction_bid_result`/`get_auction_regional_stats`/`get_auction_usage_stats`(온비드,
B010003 기관)와 `get_jeonse_guarantee_products`/`get_jeonse_guarantee_detail`(HUG,
B551408 기관)은 GitHub 공개 프로젝트(tlee0818/data-go-kr-realestate-mcp, MIT)
소스코드에서 URL만 확인했고 이 서버에서 실제 호출 검증은 안 함. 온비드 계열은 기존
서비스키로 될 가능성이 높지만, HUG는 완전히 다른 기관이라 data.go.kr에서 해당
데이터셋을 별도로 찾아 활용신청해야 할 수 있음 — 처음 호출해서 키 오류가 나면
data.go.kr에서 "HUG 전세자금보증" 등으로 검색해서 개별 활용신청할 것.

### (7) 전국공인중개사사무소표준데이터 — 공공데이터포털
1. https://www.data.go.kr/data/15107745/openapi.do 접속 → 로그인 → "활용신청"
2. 개발/운영 단계 모두 **자동승인**이라 신청 즉시 서비스키가 활성화됨 (기존
   MOLIT_SERVICE_KEY와 동일한 계정 서비스키를 그대로 씀 — 별도 키 발급 불필요, 이
   데이터셋에 대해서만 활용신청을 한 번 더 해야 함)
3. **주의**: 문서에 나온 필드별 검색 파라미터(instt_nm, RPRSV_NM 등)는 실제로
   동작하지 않음 (2026-08-06 실호출로 확인 — 정확히 같은 값을 넘겨도
   NODATA_ERROR). 그래서 get_broker_offices는 이 API를 직접 호출하는 대신
   `scripts/build_broker_cache.py`로 미리 전량(6.8만여건)을 받아 로컬 캐시로
   저장해두고, 그 캐시를 읽어 필터링하는 방식으로 구현함 — 아래 "캐시 빌드" 참고.

### (8) 브이월드(V-World) — 토지이용계획 자동화
data.go.kr과 완전히 별도인 국토교통부 산하 공간정보 오픈플랫폼.
1. https://www.vworld.kr 가입 → 로그인 → "인증키" 메뉴 → 오픈API 인증키 신청 (무료, 이메일 인증만 하면 승인)
2. **도메인 등록 필수**: 로컬 개발은 `localhost`, 실서버 배포 시 그 도메인으로 재등록해야 함 — 안 하면 호출이 막힘
3. 2026-08-06 실제 호출로 검증 완료 (지오코딩 + 용도지역 조회 둘 다 정상 동작 확인)

일곱 값을 `.env` 파일에 넣기 (`.env.example` 복사해서 사용):
```
MOLIT_SERVICE_KEY=발급받은키
LAW_OC=이메일아이디
JUSO_API_KEY=발급받은승인키
KAKAO_REST_API_KEY=발급받은REST키
VWORLD_API_KEY=발급받은인증키
VWORLD_DOMAIN=localhost
```

## 2. 설치

```
cd korea-realestate-mcp
pip install -r requirements.txt
```

### 캐시 빌드 (공인중개사사무소 검색용, 최초 1회 + 가끔 갱신)

`get_broker_offices`는 라이브 API 대신 로컬 캐시(`data/broker_offices.json`)를
읽는다. 위 (7)번에서 활용신청 승인 후 아래 스크립트를 실행해서 캐시를 만들 것
(약 68 페이지, 1~2분 소요):

```
python scripts/build_broker_cache.py
```

데이터 갱신주기가 연 1회(개별 지자체는 월 1회)라 캐시가 며칠~몇 주 묵어도
문제없음 — 가끔(월 1회 정도) 재실행해서 갱신하면 됨.

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
        "LAW_OC": "이메일아이디",
        "JUSO_API_KEY": "발급받은승인키",
        "KAKAO_REST_API_KEY": "발급받은REST키"
      }
    }
  }
}
```

## 4. 도구

- `search_address(keyword, page, count_per_page)` — 도로명주소 API로 주소 검색 → 다른 도구가
  요구하는 lawd_cd/sigungu_cd/bjdong_cd/bun/ji를 admCd/lnbrMnnm/lnbrSlno 필드 조합으로
  함께 반환. **2026-08-06 실제 호출로 검증 완료** (강남구 테헤란로 101 → lawd_cd "11680",
  bjdong_cd "10100", bun "0821" 정상 확인). 원래는 건물관리번호(bdMgtSn)를 19자리로 잘라
  쓰려 했으나 실제론 25자리라 그 방식은 폐기 — admCd 등 명확한 별도 필드를 직접 쓰는
  방식으로 다시 구현함.
- `get_house_trade_price(lawd_cd, deal_ymd)` / `get_house_rent_price(...)` — 단독/다가구 매매·전월세
- `get_officetel_trade_price(lawd_cd, deal_ymd)` / `get_officetel_rent_price(...)` — 오피스텔 매매·전월세
- `get_apt_trade_price(lawd_cd, deal_ymd)` / `get_apt_rent_price(...)` — 아파트 매매·전월세
- `get_commercial_trade_price(lawd_cd, deal_ymd)` — 상업업무용 부동산(근린생활시설·업무시설 등) 매매
- `get_land_trade_price(lawd_cd, deal_ymd)` — 토지 매매
- `get_villa_trade_price(lawd_cd, deal_ymd)` / `get_villa_rent_price(...)` — 연립다세대(빌라) 매매·전월세.
  전세사기 위험이 실제로 집중되는 주택 유형이라 별도 추가함.
  (매매·전월세 도구 전부 파라미터 동일: 법정동코드 5자리 + 계약년월 6자리. 전월세 4종·연립다세대
  매매/전월세는 아직 실제 호출 검증 전 — 위 API 키 발급 섹션 참고)
- `get_building_title_info(sigungu_cd, bjdong_cd, bun, ji)` — 건축물대장 표제부 조회
  (대지면적·연면적·용도·사용승인일 등). **위반건축물여부 필드는 없음** (2026-08-01 실제 호출로 확인) —
  필요하면 건축HUB의 다른 하위서비스를 별도 활용신청해야 함, 아직 미구현.
- `search_law(query, target, display)` — 법령/행정규칙 검색.
  `target="law"`(기본값)면 법률/시행령/시행규칙, `target="admrul"`이면 행정규칙(고시) —
  **투기과열지구 지정, 조정대상지역 지정** 같은 부처 고시가 여기 포함됨. `target="ordin"`은 자치법규.
- `get_law_detail(doc_id, target)` — search_law 결과의 "법령일련번호"/"행정규칙일련번호"로
  조문·고시 원문 전체(제개정이유, 첨부파일 링크 등)를 조회. 지정지역 목록 같은 세부내용 확인용.
- `calc_transfer_tax(...)` — 양도소득세 계산. **세율표(tax_brackets)와 장기보유특별공제율은
  절대 기본값이 없음** — 호출 시 search_law로 확인한 최신 소득세법 시행령 별표 값을 직접 넘겨야 함.
  이유: 다주택 중과세율/공제율은 정책에 따라 자주 바뀌어서, 하드코딩하면 시점이 안 맞는 틀린
  계산이 나올 수 있기 때문.
- `calc_jeonse_ratio(sale_price, jeonse_deposit)` — 전세가율 계산과 깡통전세 위험 구간 코멘트.
  구간 기준은 참고용이며 법적 안전선이 아님.
- `generate_landlord_disclosure_request(tenant_name, property_address)` — 주택임대차보호법
  제3조의7(임대인 정보제시의무)에 근거한 요청서 문안 생성. 법률 자문이 아니라 초안 생성기 —
  실사용 전 search_law로 현재 조문 재확인 필요.
- `get_auction_list(prpt_div_cd, pvct_trgt_yn, sido, sigungu, emd, bid_start_date, bid_end_date,
  lowest_price_start, lowest_price_end, num_of_rows, page_no)` — 온비드(캠코) 공매 부동산
  물건목록 조회(입찰 중/입찰예정만). **실제 호출로 검증 완료**.
- `get_auction_detail(cltr_mng_no, pbct_cdtn_no)` — 물건목록에서 얻은 물건관리번호로 소재지
  전체주소·면적상세·감정평가정보·사진/위치도 URL·등기사항증명서 주요정보 등 상세 조회.
  **실제 호출로 검증 완료**.
- `get_auction_notice_list(cltr_type_cd, prpt_div_cd, opbd_date_start, opbd_date_end, ...)` —
  공매 공고목록 조회. 물건목록/물건상세엔 공고관리번호(pbancMngNo)가 없어서, 공고상세를
  조회하려면 이 도구로 먼저 pbancMngNo를 구해야 함. **실제 호출로 검증 완료**.
- `get_auction_notice(pbanc_mng_no)` — 공매 공고문 전문·참가수수료 등 공고상세 조회.
  **실제 호출로 검증 완료**.
- `get_onbid_usage_code(up_ctgr_id, num_of_rows, page_no)` — 온비드 용도코드(재산유형 하위
  분류) 체계 조회. **실제 호출로 검증 완료**.
- `get_onbid_address(sido, sigungu, emd, num_of_rows, page_no)` — 온비드 소재지 주소(시도/
  시군구/읍면동/상세) 계층 조회. **실제 호출로 검증 완료**.
- `get_nearby_amenities(address, category_group_code, radius_m)` — 카카오 로컬 API로 주소
  반경 내 지하철역·학교·어린이집 등 조회 (내부적으로 지오코딩+카테고리검색 2단계를 묶음).
  체크리스트 "⑤ 입지조건" [수동] 항목 자동화용. **실제 호출로 검증 완료** (2026-08-04,
  korea-realestate-qgis 프로젝트에서 같은 API로 검증됨).
- `analyze_price_trend(monthly_deal_amounts)` — 여러 달치 실거래가를 월별 추이(평균·중앙값·
  거래량·전월대비 변동률)로 계산. 순수 계산 도구라 API 키 불필요 — get_apt_trade_price 등을
  여러 달 반복 호출한 결과를 정리해서 넘겨야 함.
- `compare_regions(regions)` — 2개 이상 지역의 실거래가를 평균가·중앙값·㎡당 단가로 비교.
  순수 계산 도구, API 키 불필요.
- `get_auction_bid_result(cltr_mng_no, pbct_cdtn_no)` — 온비드 공매 물건의 입찰결과(낙찰
  여부·낙찰가) 조회. **미검증** — GitHub 공개 프로젝트에서 URL만 확인, 위 (6)번 섹션 참고.
- `get_auction_regional_stats(num_of_rows, page_no)` / `get_auction_usage_stats(...)` —
  온비드 지역별/용도별 낙찰 통계. **미검증**, 위 (6)번 섹션 참고.
- `get_jeonse_guarantee_products(region_code, num_of_rows, page_no)` /
  `get_jeonse_guarantee_detail(prod_id, num_of_rows, page_no)` — HUG 전세자금보증상품
  지역별 한도/상세정보 조회. **미검증**, 위 (6)번 섹션 참고 — 파라미터명(region_code,
  prod_id)도 추정치라 첫 호출 시 빈 값으로 시도해서 실제 응답 구조부터 확인할 것.
- `vworld_geocode_address(address, addr_type)` — 브이월드 지오코더로 주소를 좌표로 변환.
  **실제 호출로 검증 완료** (2026-08-06).
- `get_land_use_zoning(address)` — 브이월드로 용도지역·용도지구·용도구역·토지거래허가구역
  조회. 체크리스트 "③ 토지이용계획" [수동] 항목 자동화. **실제 호출로 검증 완료**
  (2026-08-06, 강남구 역삼동 826 → 일반상업지역 정상 반환 확인). 건폐율·용적률 상한,
  지구단위계획, 도시계획시설, 42개 다른 법령 지정사항은 아직 미구현 — korean-land-mcp
  참고해서 레이어 추가 이식 가능.
- `get_broker_offices(region_keyword, name_keyword, limit)` — 전국 공인중개사사무소를
  주소/제공기관명(region_keyword) 또는 상호명(name_keyword) 부분 문자열로 검색.
  로컬 캐시(`data/broker_offices.json`) 기반 — 위 "캐시 빌드" 섹션 먼저 실행해야 함.
  **실제 호출로 검증 완료** (2026-08-06, 전국 67,963건 수집 확인, "노원구"로 719건
  매칭 확인). API 원본 서버 쪽 필드 검색이 동작하지 않아 로컬 필터링 방식을 씀 —
  위 (7)번 섹션 참고. 중개보조원수·소속공인중개사수·홈페이지주소·위경도는 원본
  데이터에도 미기재인 레코드가 많음(빈 문자열로 옴).

### 커버리지 한계 (중요)
- `admrul` 검색은 부처가 "행정규칙"으로 등록한 고시만 잡힘 — 투기과열지구/조정대상지역처럼
  전국 단위 지정 고시는 잡히지만, 개별 정비구역의 토지거래허가구역 지정처럼 지역명이 제목에
  섞인 공고는 검색어가 안 맞으면 못 찾을 수 있음.
- 재건축/재개발 조합설립인가 등 정비사업 진행단계는 지자체(서울시 등)가 관리하는 데이터라
  법제처 API 대상이 아예 아님 — 이건 여전히 웹서치나 "정비사업 정보몽땅" 직접 확인이 필요함.
- 지정 고시가 "일부개정"이면 그 회차에 추가/제외된 지역만 나오고, 전체 누적 목록은 별도
  이력 조회가 필요할 수 있음.
- **등기부등본은 의도적으로 미구현.** 근저당권·소유자 일치 확인이 위험진단에서 제일 중요하지만,
  인터넷등기소는 개별 문서 열람 오픈API가 없고 CODEF 등 3자 API는 건당 비용이 발생함. 이 서버는
  "비용 없는 공공데이터"만 다룬다는 원칙을 지키려고 자동화하지 않음 — 사용자가 직접 열람한 내용을
  붙여넣어 해석을 요청하는 방식으로 우회할 것.
- `search_address`의 코드 파싱은 실제 호출로 검증 완료 (위 섹션 참고). 전월세 4종·
  연립다세대 매매/전월세 엔드포인트는 아직 실제 호출로 검증 전임 (위 각 섹션 참고).
- **토지이용계획 자동화(용도지역/지구/구역, 토지거래허가구역)는 브이월드로 구현+검증
  완료** (2026-08-06). 단 건폐율·용적률 상한, 지구단위계획, 도시계획시설, 42개 다른
  법령 지정사항은 아직 없음 — `UrbanWatcherKr/korean-land-mcp`(MIT, ★15) 참고해서
  레이어 추가 이식 가능.
- **공인중개사 등록현황 조회는 `get_broker_offices`로 구현+검증 완료** (2026-08-06,
  전국 67,963건). `tlee0818/data-go-kr-realestate-mcp`의 관련 메서드는 실제로는
  "영천시" 한정 데이터였음(전국 조회 불가) — 대신 표준데이터셋 오픈API를 새로 찾아
  검증함. 단 이 API는 서버 쪽 필드 검색이 실제로 동작하지 않아서 로컬 캐시 방식으로
  구현했고, 캐시는 수동으로 가끔(월 1회 정도) 갱신해줘야 함 — 위 (7)번·"캐시 빌드"
  섹션 참고.

## 참고: 구분등기 다가구주택 관련

각 호실이 구분등기 되어 있으면 세법상 별도 주택으로 취급되어 다주택자 판정에 영향을 줄 수 있음.
정확한 판단은 반드시 `search_law`로 현재 시행 중인 소득세법/소득세법 시행령 조문을 확인하고,
필요하면 세무사 상담을 병행할 것 — 이 도구는 계산기일 뿐 세무 자문이 아님.
