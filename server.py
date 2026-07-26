"""
개인용 부동산 MCP 서버.

목적: 실거래가/법령/양도세 계산을 API로 직접 확인해서 할루시네이션 없이 답하기 위한 도구 모음.
  1. get_house_trade_price       : 국토부 단독/다가구 매매 실거래가 조회
  2. get_officetel_trade_price   : 국토부 오피스텔 매매 실거래가 조회
  3. get_apt_trade_price         : 국토부 아파트 매매 실거래가 조회
  4. get_commercial_trade_price  : 국토부 상업업무용 부동산 매매 실거래가 조회
  5. get_land_trade_price        : 국토부 토지 매매 실거래가 조회
  6. search_law                  : 법제처 국가법령정보 법령/행정규칙(고시) 검색
  7. get_law_detail              : 법령 조문/고시 원문 전체 조회
  8. calc_transfer_tax           : 양도소득세 계산 (세율표는 절대 하드코딩하지 않음 — 아래 설명 참고)

세율표를 하드코딩하지 않는 이유:
  다주택 중과세율, 장기보유특별공제율, 1세대1주택 비과세 기준(현재 12억)은
  정부 정책에 따라 수시로 개정된다. 잘못된 값을 내장하면 "그럴듯하지만 틀린" 계산이
  나올 위험이 크므로, calc_transfer_tax는 세율표를 호출자가 직접 넘기도록 강제한다.
  최신 세율표는 search_law로 소득세법 시행령 별표를 조회해서 확인한 뒤 넘길 것.
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

# 국토부 실거래가 API는 RTMSDataSvc 계열 공통 규칙을 따른다.
# 신청 후 Swagger UI/기술문서에서 정확한 엔드포인트를 반드시 재확인할 것.
MOLIT_SH_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"
MOLIT_OFFI_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcOffiTrade/getRTMSDataSvcOffiTrade"
MOLIT_APT_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
MOLIT_NRG_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"
MOLIT_LAND_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcLandTrade/getRTMSDataSvcLandTrade"

LAW_SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"
LAW_SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do"

mcp = FastMCP("korea-realestate")


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


if __name__ == "__main__":
    mcp.run()
