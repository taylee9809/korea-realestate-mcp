# korea-realestate-mcp

구분등기된 다가구주택 1채를 추적하기 위한 개인용 MCP 서버.
실거래가 조회, 법령 조회, 양도소득세 계산 3가지만 한다. 재건축 단계 추적은 포함하지 않음(지자체별 공공사이트에서 수동 확인 또는 웹서치 사용).

## 1. API 키 발급 (직접 해야 함)

### (1) 국토교통부 실거래가 - 공공데이터포털
1. https://www.data.go.kr 가입
2. "국토교통부_단독/다가구 매매 실거래가 자료" 검색 (https://www.data.go.kr/data/15126465/openapi.do)
3. 활용신청 → 승인 대기 (보통 자동승인, 최대 1일)
4. 마이페이지에서 서비스키(일반 인증키) 복사
5. **중요**: 승인 후 상세페이지의 Swagger UI 또는 "기술문서.hwp"를 열어서 `server.py`의
   `MOLIT_SH_TRADE_URL`이 실제 엔드포인트와 일치하는지 반드시 확인할 것.
   (RTMSDataSvc 계열 명명 규칙을 따라 작성했지만, data.go.kr이 공식 문서를 다운로드 없이
   공개하지 않아 이번 조사로는 100% 확정하지 못했음)

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

- `get_house_trade_price(lawd_cd, deal_ymd)` — 법정동코드(5자리) + 계약년월(6자리)로 단독/다가구 실거래 조회
- `search_law(query, display)` — 법령명/키워드로 법령 검색 (예: "소득세법")
- `calc_transfer_tax(...)` — 양도소득세 계산. **세율표(tax_brackets)와 장기보유특별공제율은
  절대 기본값이 없음** — 호출 시 search_law로 확인한 최신 소득세법 시행령 별표 값을 직접 넘겨야 함.
  이유: 다주택 중과세율/공제율은 정책에 따라 자주 바뀌어서, 하드코딩하면 시점이 안 맞는 틀린
  계산이 나올 수 있기 때문.

## 참고: 구분등기 다가구주택 관련

각 호실이 구분등기 되어 있으면 세법상 별도 주택으로 취급되어 다주택자 판정에 영향을 줄 수 있음.
정확한 판단은 반드시 `search_law`로 현재 시행 중인 소득세법/소득세법 시행령 조문을 확인하고,
필요하면 세무사 상담을 병행할 것 — 이 도구는 계산기일 뿐 세무 자문이 아님.
