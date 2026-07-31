"""
개인용 부동산 MCP 서버.

목적: 실거래가/법령/양도세 계산을 API로 직접 확인해서 할루시네이션 없이 답하기 위한 도구 모음.
   1. search_address              : 도로명주소 API로 주소 → 법정동코드/지번 변환
   2. get_house_trade_price       : 국토부 단독/다가구 매매 실거래가 조회
   3. get_house_rent_price        : 국토부 단독/다가구 전월세 실거래가 조회
   4. get_officetel_trade_price   : 국토부 오피스텔 매매 실거래가 조회
   5. get_officetel_rent_price    : 국토부 오피스텔 전월세 실거래가 조회
   6. get_apt_trade_price         : 국토부 아파트 매매 실거래가 조회
   7. get_apt_rent_price          : 국토부 아파트 전월세 실거래가 조회
   8. get_commercial_trade_price  : 국토부 상업업무용 부동산 매매 실거래가 조회
   9. get_land_trade_price        : 국토부 토지 매매 실거래가 조회
  10. get_villa_trade_price       : 국토부 연립다세대(빌라) 매매 실거래가 조회
  11. get_villa_rent_price        : 국토부 연립다세대(빌라) 전월세 실거래가 조회
  12. get_building_title_info     : 건축HUB 건축물대장(표제부) - 대지면적/연면적/용도 조회
  13. search_law                  : 법제처 국가법령정보 법령/행정규칙(고시) 검색
  14. get_law_detail              : 법령 조문/고시 원문 전체 조회
  15. calc_transfer_tax           : 양도소득세 계산 (세율표는 절대 하드코딩하지 않음 — 아래 설명 참고)
  16. calc_jeonse_ratio           : 전세가율 계산 (깡통전세 위험 구간 표시)
  17. generate_landlord_disclosure_request : 임대인 정보제시의무 요청서 문안 생성

세율표를 하드코딩하지 않는 이유:
  다주택 중과세율, 장기보유특별공제율, 1세대1주택 비과세 기준(현재 12억)은
  정부 정책에 따라 수시로 개정된다. 잘못된 값을 내장하면 "그럴듯하지만 틀린" 계산이
  나올 위험이 크므로, calc_transfer_tax는 세율표를 호출자가 직접 넘기도록 강제한다.
  최신 세율표는 search_law로 소득세법 시행령 별표를 조회해서 확인한 뒤 넘길 것.

의도적으로 포함하지 않은 것 — 등기부등본 조회:
  근저당권·소유자 일치 여부 확인은 위험진단에서 제일 중요하지만, 인터넷등기소는
  개별 문서 열람에 오픈API가 없고 CODEF 등 3자 API를 거치면 건당 비용이 발생한다.
  이 서버는 "비용 없는 공공데이터"만 다룬다는 원칙을 지키기 위해 등기부등본은
  일부러 자동화하지 않았다 — 사용자가 직접 열람한 내용을 텍스트로 붙여넣어 해석을
  요청하는 방식으로 우회할 것.
"""
import os
from typing import Optional

import httpx
import xmltodict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

MOLIT_SERVICE_KEY = os.environ.get("MOLIT_SERVICE_KEY", "")
LAW_OC = os.environ.get("LAW_OC", "")
JUSO_API_KEY = os.environ.get("JUSO_API_KEY", "")

# 국토부 실거래가 API는 RTMSDataSvc 계열 공통 규칙을 따른다.
# 신청 후 Swagger UI/기술문서에서 정확한 엔드포인트를 반드시 재확인할 것.
MOLIT_SH_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"
MOLIT_OFFI_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"
MOLIT_APT_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
MOLIT_NRG_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
MOLIT_LAND_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcLandTrade/getRTMSDataSvcLandTrade"
MOLIT_RH_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcRHTrade/getRTMSDataSvcRHTrade"

# 전월세 실거래가 — 매매와 동일한 서비스키를 쓰지만 데이터셋 활용신청은 별도로 해야 한다.
# 아직 실제 호출로 검증 전이므로 승인 후 Swagger UI로 엔드포인트/파라미터를 재확인할 것.
MOLIT_SH_RENT_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcSHRent/getRTMSDataSvcSHRent"
MOLIT_OFFI_RENT_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent"
MOLIT_APT_RENT_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptRent/getRTMSDataSvcAptRent"
MOLIT_RH_RENT_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcRHRent/getRTMSDataSvcRHRent"

# 건축HUB 건축물대장정보 서비스 (별도 활용신청 필요, data.go.kr id 15134735)
# 표제부(getBrTitleInfo) 실제 호출로 확인한 결과 위반건축물여부 필드는 없음(2026-08-01 확인).
# 위반건축물 여부가 필요하면 건축HUB의 다른 하위서비스(기본개요 등)를 별도 활용신청해서
# 조사해야 함 — 아직 이 서버엔 미포함.
BLD_TITLE_INFO_URL = "http://apis.data.go.kr/1613000/BldRgstHubService/getBrTitleInfo"

LAW_SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"
LAW_SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do"

# 도로명주소 API (행정안전부, business.juso.go.kr 무료 승인키 발급 필요)
JUSO_API_URL = "https://business.juso.go.kr/addrlink/addrLinkApi.do"

mcp = FastMCP("korea-realestate")


@mcp.tool()
async def search_address(keyword: str, page: int = 1, count_per_page: int = 10) -> dict:
    """도로명주소 API로 주소를 검색해서 법정동코드/지번 등을 조회한다.

    다른 도구들이 요구하는 lawd_cd/sigungu_cd/bjdong_cd/bun/ji를 도로명주소나 지번주소
    텍스트만으로 알아내기 위한 도구. 응답의 건물관리번호(bdMgtSn, 19자리)를
    "법정동코드(10) + 지하여부(1) + 본번(4) + 부번(4)" 규칙으로 파싱해서 함께 반환한다.

    주의: 이 파싱 규칙은 공식 문서 기준으로 작성했지만 실제 응답으로 아직 검증하지
    않았음 — 처음 쓸 때 결과의 "bdMgtSn" 원본 값과 "파싱코드"를 대조해서 확인할 것.

    Args:
        keyword: 검색할 주소 (도로명 또는 지번, 예: "서울 강동구 천호동 145-12")
        page: 페이지 번호
        count_per_page: 페이지당 결과 수
    """
    if not JUSO_API_KEY:
        raise RuntimeError("JUSO_API_KEY가 설정되지 않았습니다 (.env 확인, business.juso.go.kr에서 무료 발급)")

    params = {
        "confmKey": JUSO_API_KEY,
        "currentPage": page,
        "countPerPage": count_per_page,
        "keyword": keyword,
        "resultType": "json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(JUSO_API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", {})
    juso_list = results.get("juso") or []

    parsed = []
    for j in juso_list:
        bd_mgt_sn = j.get("bdMgtSn", "")
        codes = None
        if len(bd_mgt_sn) == 19:
            codes = {
                "lawd_cd": bd_mgt_sn[0:5],
                "sigungu_cd": bd_mgt_sn[0:5],
                "bjdong_cd": bd_mgt_sn[5:10],
                "지하여부": bd_mgt_sn[10] == "1",
                "bun": bd_mgt_sn[11:15],
                "ji": bd_mgt_sn[15:19],
            }
        parsed.append({**j, "파싱코드": codes})

    return {"common": results.get("common"), "juso": parsed}


@mcp.tool()
async def get_house_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 단독/다가구 매매 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 종로구 = "11110")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    # 이 API는 JSON을 지원하지 않고 XML만 지원한다 (기술문서 확인 완료)
    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_SH_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_house_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 단독/다가구 전월세 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 종로구 = "11110")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_SH_RENT_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_officetel_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 오피스텔 매매 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 송파구 = "11710")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_OFFI_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_officetel_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 오피스텔 전월세 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 송파구 = "11710")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_OFFI_RENT_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_apt_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 아파트 매매 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 송파구 = "11710")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_APT_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_apt_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 아파트 전월세 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 송파구 = "11710")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_APT_RENT_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_commercial_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 상업업무용 부동산(근린생활시설, 업무시설 등) 매매 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 마포구 = "11440")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_NRG_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_land_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 토지 매매 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 마포구 = "11440")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_LAND_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_villa_trade_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 연립다세대(빌라) 매매 실거래가를 조회한다.

    전세사기 위험이 실제로 집중되는 주택 유형이라 단독/다가구·아파트·오피스텔과
    별도 카테고리로 존재함 (이전까지 이 서버에 빠져있던 항목).

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 강서구 = "11500")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_RH_TRADE_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_villa_rent_price(lawd_cd: str, deal_ymd: str) -> dict:
    """국토교통부 연립다세대(빌라) 전월세 실거래가를 조회한다.

    Args:
        lawd_cd: 법정동코드 앞 5자리 (예: 서울 강서구 = "11500")
        deal_ymd: 계약년월 6자리 (예: "202506")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_RH_RENT_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def get_building_title_info(
    sigungu_cd: str, bjdong_cd: str, bun: str = "0000", ji: str = "0000"
) -> dict:
    """건축HUB 건축물대장(표제부)에서 대지면적·연면적·용도·사용승인일 등을 조회한다.

    Args:
        sigungu_cd: 시군구코드 5자리 (예: 서울 강동구 = "11740")
        bjdong_cd: 법정동코드 뒤 5자리 (예: 천호동 = "10900")
        bun: 지번 본번 4자리, 0 채움 (예: 145번지 = "0145")
        ji: 지번 부번 4자리, 0 채움 (예: 12 = "0012", 본번만 있으면 "0000")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "sigunguCd": sigungu_cd,
        "bjdongCd": bjdong_cd,
        "bun": bun,
        "ji": ji,
        "numOfRows": "100",
        "pageNo": "1",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(BLD_TITLE_INFO_URL, params=params)
        resp.raise_for_status()
        return xmltodict.parse(resp.text)


@mcp.tool()
async def search_law(query: str, target: str = "law", display: int = 20) -> dict:
    """법제처 국가법령정보에서 법령 또는 행정규칙(고시)을 검색한다.

    Args:
        query: 검색할 법령명/고시명 또는 키워드
        target: "law"(법률/시행령/시행규칙, 기본값) 또는 "admrul"(행정규칙 — 투기과열지구
                지정, 조정대상지역 지정 등 부처 고시가 여기 포함됨) 또는 "ordin"(자치법규)
        display: 결과 개수 (최대 100)

    검색 결과의 "법령일련번호"(law) 또는 "행정규칙일련번호"(admrul) 값을
    get_law_detail의 doc_id로 넘기면 조문/고시 원문 전체를 볼 수 있다.
    """
    if not LAW_OC:
        raise RuntimeError("LAW_OC가 설정되지 않았습니다 (.env 확인)")

    params = {
        "OC": LAW_OC,
        "target": target,
        "type": "JSON",
        "query": query,
        "display": display,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(LAW_SEARCH_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_law_detail(doc_id: str, target: str = "law") -> dict:
    """법령 조문 또는 행정규칙(고시) 원문 전체를 조회한다.

    Args:
        doc_id: search_law 결과의 "법령일련번호"(target="law") 또는
                "행정규칙일련번호"(target="admrul") 값
        target: search_law에서 사용한 것과 동일하게 "law" 또는 "admrul" 지정
    """
    if not LAW_OC:
        raise RuntimeError("LAW_OC가 설정되지 않았습니다 (.env 확인)")

    params = {
        "OC": LAW_OC,
        "target": target,
        "type": "JSON",
        "ID": doc_id,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(LAW_SERVICE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def calc_transfer_tax(
    purchase_price: int,
    sale_price: int,
    holding_years: float,
    necessary_expenses: int,
    tax_brackets: list[dict],
    long_term_deduction_rate: float,
    basic_deduction: int = 2_500_000,
    surcharge_rate: float = 0.0,
) -> dict:
    """양도소득세를 계산한다. 세율/공제율은 반드시 search_law로 확인한 최신 값을 넘길 것.

    Args:
        purchase_price: 매수 가격 (원)
        sale_price: 매도 가격 (원)
        holding_years: 보유 기간 (년)
        necessary_expenses: 취득세, 중개보수 등 필요경비 (원)
        tax_brackets: [{"upto": 과세표준 상한(원, 마지막 구간은 None), "rate": 세율(0~1), "deduction": 누진공제액(원)}, ...]
                      최신 소득세법 시행령 별표에서 확인해서 넘길 것 — 하드코딩된 기본값 없음
        long_term_deduction_rate: 장기보유특별공제율 (0~1), 다주택 중과 대상이면 0으로 넘길 것
        basic_deduction: 양도소득 기본공제 (기본 250만원, 연 1회)
        surcharge_rate: 다주택자 중과세율 가산분 (0~1), 해당 없으면 0

    Returns:
        계산 과정이 담긴 dict (양도차익, 과세표준, 산출세액 등 단계별로 반환 — 검증 가능하도록)
    """
    gain = sale_price - purchase_price - necessary_expenses
    if gain <= 0:
        return {"양도차익": gain, "납부세액": 0, "비고": "양도차익 없음(손실 또는 0)"}

    long_term_deduction = int(gain * long_term_deduction_rate)
    income_after_deduction = gain - long_term_deduction
    taxable_base = max(income_after_deduction - basic_deduction, 0)

    base_rate = 0.0
    progressive_deduction = 0
    for bracket in sorted(tax_brackets, key=lambda b: (b["upto"] is not None, b["upto"] or 0)):
        base_rate = bracket["rate"]
        progressive_deduction = bracket["deduction"]
        if bracket["upto"] is None or taxable_base <= bracket["upto"]:
            break

    applied_rate = base_rate + surcharge_rate
    calculated_tax = int(taxable_base * applied_rate) - progressive_deduction
    calculated_tax = max(calculated_tax, 0)

    local_income_tax = int(calculated_tax * 0.1)

    return {
        "양도차익": gain,
        "장기보유특별공제": long_term_deduction,
        "공제후소득금액": income_after_deduction,
        "기본공제": basic_deduction,
        "과세표준": taxable_base,
        "적용세율(기본+중과)": applied_rate,
        "누진공제": progressive_deduction,
        "양도소득세": calculated_tax,
        "지방소득세(10%)": local_income_tax,
        "총납부세액": calculated_tax + local_income_tax,
    }


@mcp.tool()
def calc_jeonse_ratio(sale_price: int, jeonse_deposit: int) -> dict:
    """전세가율(전세보증금 ÷ 매매가)을 계산하고 위험 구간을 표시한다.

    전세가율이 높을수록 매매가가 조금만 하락해도 보증금을 못 돌려받는
    "깡통전세" 위험이 커진다. 아래 구간 기준은 법적/절대적 안전선이 아니라
    통상적으로 언급되는 경계값이므로 참고용으로만 쓸 것 — 지역·건물 유형별
    시세 변동성이 다르므로 sale_price 자체가 실제 시세를 반영하는지도
    get_apt_trade_price 등으로 별도 확인해야 함.

    Args:
        sale_price: 비교 대상 매매 실거래가/시세 (원)
        jeonse_deposit: 확인하려는 전세보증금 (원)

    Returns:
        전세가율과 구간별 코멘트가 담긴 dict
    """
    if sale_price <= 0:
        raise ValueError("sale_price는 0보다 커야 합니다")

    ratio = jeonse_deposit / sale_price

    if ratio >= 0.9:
        risk = "매우 위험 — 매매가 소폭 하락만으로도 보증금 미반환 가능성"
    elif ratio >= 0.8:
        risk = "위험 — 통상 깡통전세 경계선으로 언급되는 구간"
    elif ratio >= 0.7:
        risk = "주의 — 지역·건물 유형별 시세 변동폭을 함께 확인할 것"
    else:
        risk = "상대적으로 안전 — 다만 근저당 등 다른 위험요소는 별도 확인 필요"

    return {
        "매매가": sale_price,
        "전세보증금": jeonse_deposit,
        "전세가율": round(ratio, 4),
        "전세가율(%)": round(ratio * 100, 2),
        "위험도코멘트": risk,
    }


@mcp.tool()
def generate_landlord_disclosure_request(
    tenant_name: str = "", property_address: str = ""
) -> dict:
    """임대차 계약 전 임대인에게 요구할 수 있는 법정 정보제시 요청서 문안을 만든다.

    2023.4.18 시행된 주택임대차보호법 제3조의7(임대인의 정보 제시 의무)에 근거한
    통상적인 요구 항목으로 구성한 템플릿. 조문 자체를 실시간 조회하지는 않으므로,
    실제 사용 전 search_law("주택임대차보호법")로 현재 시행 중인 조문과 시행일을
    반드시 재확인할 것 — 이 도구는 법률 자문이 아니라 요청서 초안 생성기임.

    Args:
        tenant_name: 요청서에 넣을 임차예정인 이름 (생략 가능)
        property_address: 대상 주택 주소 (생략 가능)
    """
    header = (
        f"{property_address} 임대차계약 관련 정보제시 요청"
        if property_address
        else "임대차계약 관련 정보제시 요청"
    )
    signer = tenant_name or "임차예정인"

    body = (
        "주택임대차보호법 제3조의7에 따라 계약 체결 전 아래 정보의 제시를 요청합니다.\n"
        "1. 해당 주택의 확정일자 부여일, 차임 및 보증금 등 정보(선순위 임차인 현황)\n"
        "2. 국세징수법 제108조에 따른 납세증명서(국세 완납 여부)\n"
        "3. 지방세징수법 제5조에 따른 납세증명서(지방세 완납 여부)\n"
        "※ 임대인은 위 서류 제시 대신 열람에 동의하는 방식으로도 응할 수 있습니다."
    )

    return {
        "제목": header,
        "요청인": signer,
        "본문": body,
        "주의": "요청 거부 시 효과·예외 등 세부내용은 search_law로 최신 조문을 반드시 재확인할 것",
    }


if __name__ == "__main__":
    mcp.run()
