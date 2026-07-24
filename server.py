"""
개인용 부동산 MCP 서버.

목적: 구분등기된 다가구주택 1개를 추적하기 위한 3가지 도구만 제공한다.
  1. get_house_trade_price : 국토부 단독/다가구 매매 실거래가 조회
  2. search_law             : 법제처 국가법령정보 법령 조회 (시행일 기준 최신 조문 확인용)
  3. calc_transfer_tax      : 양도소득세 계산 (세율표는 절대 하드코딩하지 않음 — 아래 설명 참고)

세율표를 하드코딩하지 않는 이유:
  다주택 중과세율, 장기보유특별공제율, 1세대1주택 비과세 기준(현재 12억)은
  정부 정책에 따라 수시로 개정된다. 잘못된 값을 내장하면 "그럴듯하지만 틀린" 계산이
  나올 위험이 크므로, calc_transfer_tax는 세율표를 호출자가 직접 넘기도록 강제한다.
  최신 세율표는 search_law로 소득세법 시행령 별표를 조회해서 확인한 뒤 넘길 것.
"""
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

MOLIT_SERVICE_KEY = os.environ.get("MOLIT_SERVICE_KEY", "")
LAW_OC = os.environ.get("LAW_OC", "")

# 국토부 실거래가 API는 RTMSDataSvc 계열 공통 규칙을 따른다.
# 신청 후 Swagger UI/기술문서에서 정확한 엔드포인트를 반드시 재확인할 것.
MOLIT_SH_TRADE_URL = "http://apis.data.go.kr/1613000/RTMSDataSvcSHTrade/getRTMSDataSvcSHTrade"

LAW_SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"

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

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000",
        "pageNo": "1",
        "_type": "json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(MOLIT_SH_TRADE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def search_law(query: str, display: int = 20) -> dict:
    """법제처 국가법령정보에서 법령을 검색한다 (예: 소득세법, 종합부동산세법).

    Args:
        query: 검색할 법령명 또는 키워드
        display: 결과 개수 (최대 100)
    """
    if not LAW_OC:
        raise RuntimeError("LAW_OC가 설정되지 않았습니다 (.env 확인)")

    params = {
        "OC": LAW_OC,
        "target": "law",
        "type": "JSON",
        "query": query,
        "display": display,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(LAW_SEARCH_URL, params=params)
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
