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
  18. get_auction_list              : 온비드(캠코) 공매 부동산 물건목록 조회
  19. get_auction_detail            : 온비드(캠코) 공매 부동산 물건상세 조회
  20. get_auction_notice_list       : 온비드(캠코) 공매 공고목록 조회 (공고관리번호 확보용)
  21. get_auction_notice            : 온비드(캠코) 공매 공고상세(공고문 전문 등) 조회
  22. get_onbid_usage_code          : 온비드 용도 코드(재산유형 하위 분류) 조회
  23. get_onbid_address             : 온비드 소재지 주소(시도/시군구/읍면동/상세) 조회
  24. get_nearby_amenities          : 카카오 카테고리 검색 - 반경 내 지하철/학교/어린이집 등 거리
  25. analyze_price_trend           : 월별 실거래가 리스트 → 추이 통계(평균/중앙값/변동률/거래량)
  26. compare_regions               : 여러 지역 실거래가 리스트 → 비교 통계
  27. get_auction_bid_result        : 온비드 공매 물건 입찰결과상세 (낙찰가/낙찰여부 등)
  28. get_auction_regional_stats    : 온비드 지역별 낙찰 통계
  29. get_auction_usage_stats       : 온비드 용도별 낙찰 통계
  30. get_jeonse_guarantee_products : HUG 전세자금보증상품 추천/지역별 한도 조회
  31. get_jeonse_guarantee_detail   : HUG 전세자금보증상품 상세정보 조회
  32. vworld_geocode_address        : 브이월드 주소 → 좌표(PNU 포함) 변환
  33. get_land_use_zoning           : 브이월드 용도지역/지구/구역+토지거래허가구역 조회
                                      (체크리스트 "③ 토지이용계획" 자동화)
  34. get_broker_offices            : 전국 공인중개사사무소 조회 (지역/상호명 키워드)
                                      — 로컬 캐시 기반, 아래 설명 참고

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

공인중개사사무소 조회가 로컬 캐시 기반인 이유 (2026-08-06):
  data-go-kr-realestate-mcp(tlee0818)의 get_result_14는 "영천시" 한정 데이터라 전국
  조회가 안 됐음(잘못 가져다 쓸 뻔한 사례). 대신 표준데이터셋
  "전국공인중개사사무소표준데이터"(data.go.kr id 15107745)의 오픈API
  tn_pubr_public_med_office_api를 찾아 실호출로 검증함 — 전국 67,963건, 자동승인,
  정상 동작. 단 문서에 나온 필드별 검색 파라미터(instt_nm, RPRSV_NM 등)는 실제로
  동작하지 않음(정확히 같은 값을 넘겨도 NODATA_ERROR) — pageNo/numOfRows/type만
  신뢰 가능. 그래서 get_broker_offices는 이 API를 직접 호출하지 않고,
  scripts/build_broker_cache.py로 미리 전량 받아둔 data/broker_offices.json을
  읽어서 로컬 필터링한다. 데이터 갱신주기가 연 1회(개별 지자체는 월 1회)라 캐시가
  며칠 묵어도 문제없음 — 가끔 build_broker_cache.py를 재실행해서 갱신할 것.
"""
import json
import os
from pathlib import Path
from typing import Optional

import httpx
import xmltodict
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

MOLIT_SERVICE_KEY = os.environ.get("MOLIT_SERVICE_KEY", "")
LAW_OC = os.environ.get("LAW_OC", "")
JUSO_API_KEY = os.environ.get("JUSO_API_KEY", "")
KAKAO_REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY", "")
VWORLD_API_KEY = os.environ.get("VWORLD_API_KEY", "")
VWORLD_DOMAIN = os.environ.get("VWORLD_DOMAIN", "localhost")

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

# 온비드(한국자산관리공사) 공매 부동산 물건목록/물건상세 조회 서비스.
# data.go.kr id 15157207(목록)/15157247(상세), 공식 OpenAPI 활용가이드 문서로
# 엔드포인트/파라미터 확인 후 2026-08-04 실제 호출로 검증 완료(resultCode 00).
# MOLIT_SERVICE_KEY는 data.go.kr 계정 단위 서비스키라 다른 기관(국토부) API와
# 동일한 키를 그대로 재사용할 수 있음 — 단, 데이터셋별 활용신청은 각각 따로 필요.
ONBID_RLST_LIST_URL = "https://apis.data.go.kr/B010003/OnbidRlstListSrvc2/getRlstCltrList2"
ONBID_RLST_DETAIL_URL = "https://apis.data.go.kr/B010003/OnbidRlstDtlSrvc2/getRlstDtlInf2"

# 온비드 공고목록/공고상세 조회 서비스 (data.go.kr id 15157216/15157218).
# 물건목록/물건상세 응답엔 공고관리번호(pbancMngNo)가 없어서, 공고상세를 부르려면
# 먼저 공고목록에서 pbancMngNo를 얻어야 한다. 둘 다 2026-08-04 실제 호출로 검증 완료.
ONBID_PBANC_LIST_URL = "https://apis.data.go.kr/B010003/OnbidPbancListSrvc2/getPbancList2"
ONBID_PBANC_DETAIL_URL = "https://apis.data.go.kr/B010003/OnbidPbancDtlnfSrvc2/getPbancDtlInf2"

# 온비드 코드/주소 조회 서비스 (data.go.kr id 15000920). 2026-08-04 실제 호출로 검증 완료.
ONBID_USG_CODE_URL = "https://apis.data.go.kr/B010003/OnbidCodeSrvc/getOnbidUsgCodeInfo"
ONBID_ADDR_URL = "https://apis.data.go.kr/B010003/OnbidCodeSrvc/getOnbidDtlAddrInfo"

# 온비드 입찰결과상세/통계 서비스. URL은 GitHub 공개 프로젝트(tlee0818/data-go-kr-realestate-mcp,
# MIT 라이선스) 소스코드에서 확인함 — 물건목록/상세와 같은 기관(B010003) 산하라 같은
# MOLIT_SERVICE_KEY로 동작할 가능성이 높지만, 이 3개는 아직 이 서버에서 실제 호출로
# 검증하지 않았음. 데이터셋별 활용신청이 안 돼 있으면 첫 호출에서 키 오류가 날 수 있음.
ONBID_BID_RESULT_URL = "https://apis.data.go.kr/B010003/OnbidCltrBidRsltDtlSrvc2/getCltrBidRsltDtl2"
ONBID_REGIONAL_STATS_URL = "https://apis.data.go.kr/B010003/OnbidClarBidStatsSrvc/getKamcoCltrClarStats"
ONBID_USAGE_STATS_URL = "https://apis.data.go.kr/B010003/OnbidUsgBidStatsSrvc/getKamcoCltrUsgStats"

# HUG(주택도시보증공사) 전세자금보증상품 서비스. 기관코드가 B551408로 온비드(B010003)나
# 국토부(1613000)와 다른 별도 기관 — 활용신청도 별도로 필요할 가능성이 높음. URL 출처는
# 위와 동일(tlee0818 소스코드), 이 서버에서 실제 호출 검증 전.
HUG_JNSE_MAX_RENT_URL = "https://apis.data.go.kr/B551408/jnse-rcmd-info-v2/jnse-max-rent-amt-list-v2"
HUG_JNSE_RCMD_URL = "https://apis.data.go.kr/B551408/jnse-rcmd-info-v2/jnse-rcmd-list-v2"
HUG_JNSE_PROD_DTL_URL = "https://apis.data.go.kr/B551408/jnse-rcmd-info-v2/jnse-prod-dtl-info-v2"

# 카카오 로컬 API — 카테고리 검색(지하철역/학교/어린이집 등 반경 내 시설). 무료지만
# developers.kakao.com에서 REST API 키 발급 후 "카카오맵" 제품을 별도로 활성화해야
# 동작함(korea-realestate-qgis 프로젝트에서 2026-08-04 이 함정을 실제로 겪고 확인함).
KAKAO_CATEGORY_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/category.json"
KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"

# 브이월드(V-World, 국토교통부 산하 공간정보 오픈플랫폼) — data.go.kr과 완전히 별도
# 기관·별도 키. vworld.kr에서 무료 발급, 도메인 등록 필수(로컬 개발은 "localhost",
# 실서버 배포 시 재등록 필요). 호출 패턴은 GitHub 공개 프로젝트(UrbanWatcherKr/
# korean-land-mcp, MIT)의 실제 동작 코드를 그대로 참고해서 작성함 — geocode(주소→좌표)
# 후 그 좌표로 GetFeature(레이어별 조회)를 호출하는 2단계 구조.
VWORLD_ADDRESS_URL = "https://api.vworld.kr/req/address"
VWORLD_DATA_URL = "https://api.vworld.kr/req/data"

# 용도지역/지구/구역 레이어 ID (korean-land-mcp의 LAYERS 정의를 그대로 참고).
# 국토계획법상 하나의 필지는 "용도지역" 4종 중 정확히 하나에만 속해야 정상.
VWORLD_USE_ZONE_LAYERS = {
    "LT_C_UQ111": "도시지역",
    "LT_C_UQ112": "관리지역",
    "LT_C_UQ113": "농림지역",
    "LT_C_UQ114": "자연환경보전지역",
}
VWORLD_USE_DISTRICT_LAYERS = {
    "LT_C_UQ121": "경관지구",
    "LT_C_UQ123": "고도지구",
    "LT_C_UQ124": "방화지구",
    "LT_C_UQ125": "방재지구",
    "LT_C_UQ126": "보호지구",
    "LT_C_UQ128": "취락지구",
    "LT_C_UQ129": "개발진흥지구",
    "LT_C_UQ130": "특정용도제한지구",
}
VWORLD_USE_AREA_LAYERS = {
    "LT_C_UD801": "개발제한구역",
    "LT_C_UQ162": "도시자연공원구역",
}
VWORLD_EXTRA_LAYERS = {
    "LT_C_UQ141": "토지거래허가구역",
}

# 전국공인중개사사무소표준데이터 로컬 캐시 (scripts/build_broker_cache.py로 생성).
# 이 API는 서버 쪽 필드 검색이 실제로 동작하지 않아서(모듈 docstring 참고) 매 호출마다
# API를 부르는 대신 미리 받아둔 캐시를 읽어 로컬에서 필터링한다.
BROKER_CACHE_PATH = Path(__file__).resolve().parent / "data" / "broker_offices.json"

mcp = FastMCP("korea-realestate")


@mcp.tool()
async def search_address(keyword: str, page: int = 1, count_per_page: int = 10) -> dict:
    """도로명주소 API로 주소를 검색해서 법정동코드/지번 등을 조회한다.

    다른 도구들이 요구하는 lawd_cd/sigungu_cd/bjdong_cd/bun/ji를 도로명주소나 지번주소
    텍스트만으로 알아내기 위한 도구. 응답의 admCd(법정동코드 10자리)/lnbrMnnm(지번
    본번)/lnbrSlno(지번 부번) 필드를 조합해서 "파싱코드"로 함께 반환한다.

    2026-08-06 실제 호출로 검증 완료 — 애초에 건물관리번호(bdMgtSn)를 "법정동코드(10)+
    지하여부(1)+본번(4)+부번(4)=19자리" 규칙으로 잘라서 쓰려 했으나, 실제 bdMgtSn은
    25자리이고(예: "1168010100108210001000001") 남는 자리가 건물 단위 일련번호 등
    단순 지번과 다른 값이라 그 방식은 폐기함. 대신 admCd/lnbrMnnm/lnbrSlno가 이미
    명확한 별도 필드로 오길래 그걸 직접 조합하는 방식으로 다시 씀 — 이쪽이 훨씬 안전함.

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
        adm_cd = j.get("admCd", "")
        codes = None
        if len(adm_cd) == 10:
            codes = {
                "lawd_cd": adm_cd[0:5],
                "sigungu_cd": adm_cd[0:5],
                "bjdong_cd": adm_cd[5:10],
                "산번지여부": j.get("mtYn") == "1",
                "bun": (j.get("lnbrMnnm") or "0").zfill(4),
                "ji": (j.get("lnbrSlno") or "0").zfill(4),
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


@mcp.tool()
async def get_auction_list(
    prpt_div_cd: str,
    pvct_trgt_yn: str = "N",
    sido: str = "",
    sigungu: str = "",
    emd: str = "",
    bid_start_date: str = "",
    bid_end_date: str = "",
    lowest_price_start: Optional[int] = None,
    lowest_price_end: Optional[int] = None,
    num_of_rows: int = 100,
    page_no: int = 1,
) -> dict:
    """온비드(캠코) 공매 부동산 물건목록을 조회한다 (입찰 중/입찰예정 물건만).

    응답의 물건관리번호(cltrMngNo)+공매조건번호(pbctCdtnNo)는 추후 물건상세 조회
    도구(미구현)의 입력값으로 쓸 수 있음. ltnoPnu(지번PNU)/rdnmPnu(도로명PNU)와
    lctnSdnm/Sggnm/EmdNm(소재지)이 지도 좌표 변환(search_address·카카오 지오코딩)의
    입력으로 쓰인다 — 위경도 좌표 자체는 이 API가 주지 않음.

    Args:
        prpt_div_cd: 재산유형코드, 쉼표로 복수 가능 (필수). 0007=압류재산, 0010=국유재산,
            0005=기타일반재산, 0004=불용품, 0002=공유재산, 0003=금융권담보재산,
            0006=유입재산, 0008=수탁재산, 0011=공공개발재산, 0013=파산재산
        pvct_trgt_yn: 수의계약가능여부 (필수). "Y"=수의계약 가능, "N"=수의계약 불가능
        sido: 소재지 시도명 (예: "경기도") — 생략 가능
        sigungu: 소재지 시군구명 (예: "고양시 일산동구") — 생략 가능
        emd: 소재지 읍면동명 (예: "마두동") — 생략 가능
        bid_start_date: 검색할 입찰기간 시작일자 (yyyyMMdd) — 생략 가능
        bid_end_date: 검색할 입찰기간 종료일자 (yyyyMMdd) — 생략 가능
        lowest_price_start: 최저입찰가격 범위 최소값(원) — 생략 가능
        lowest_price_end: 최저입찰가격 범위 최대값(원) — 생략 가능
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
        "prptDivCd": prpt_div_cd,
        "pvctTrgtYn": pvct_trgt_yn,
    }
    if sido:
        params["lctnSdnm"] = sido
    if sigungu:
        params["lctnSggnm"] = sigungu
    if emd:
        params["lctnEmdNm"] = emd
    if bid_start_date:
        params["bidPrdYmdStart"] = bid_start_date
    if bid_end_date:
        params["bidPrdYmdEnd"] = bid_end_date
    if lowest_price_start is not None:
        params["lowstBidPrcStart"] = lowest_price_start
    if lowest_price_end is not None:
        params["lowstBidPrcEnd"] = lowest_price_end

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_RLST_LIST_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_auction_detail(
    cltr_mng_no: str, pbct_cdtn_no: Optional[int] = None
) -> dict:
    """온비드(캠코) 공매 부동산 물건상세를 조회한다 (get_auction_list 결과 기반).

    소재지 전체주소(zadrNm 지번주소, cltrRadr 도로명주소), 면적상세(sqmsList),
    감정평가정보(apslEvlClgList), 사진/360도사진/동영상/위치도 URL, 등기사항증명서
    주요정보(rgstPrmrInfList), 임대차정보(leasInfList), 배분요구사항(dtbtRqrMtrsList),
    점유관계(ocpyRelList) 등을 반환한다. 압류재산(prptDivCd=0007)이 아니면 임대차·배분
    요구·점유관계·등기 관련 목록은 대부분 비어있음.

    Args:
        cltr_mng_no: 물건관리번호 (get_auction_list 응답의 cltrMngNo, 필수)
        pbct_cdtn_no: 공매조건번호 (get_auction_list 응답의 pbctCdtnNo, 생략 가능하지만
            물건이 여러 공매조건으로 나올 수 있어 함께 넘기는 게 안전함)
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "resultType": "json",
        "cltrMngNo": cltr_mng_no,
    }
    if pbct_cdtn_no is not None:
        params["pbctCdtnNo"] = pbct_cdtn_no

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_RLST_DETAIL_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_auction_notice_list(
    cltr_type_cd: str,
    prpt_div_cd: str,
    opbd_date_start: str,
    opbd_date_end: str,
    bid_div_cd: str = "",
    dsps_mthod_cd: str = "",
    pbanc_ymd_start: str = "",
    pbanc_ymd_end: str = "",
    bid_prd_ymd_start: str = "",
    bid_prd_ymd_end: str = "",
    onbid_pbanc_nm: str = "",
    org_nm: str = "",
    num_of_rows: int = 100,
    page_no: int = 1,
) -> dict:
    """온비드(캠코) 공매 공고목록을 조회한다. 응답의 pbancMngNo를 get_auction_notice에
    넘기면 공고문 전문 등 상세를 볼 수 있음 — get_auction_list/get_auction_detail에는
    pbancMngNo가 없어서 공고상세를 조회하려면 반드시 이 도구를 먼저 거쳐야 함.

    Args:
        cltr_type_cd: 물건유형코드 (필수). "0001"=부동산, "0002"=자동차, "0003"=동산
        prpt_div_cd: 재산유형코드, 쉼표로 복수 가능 (필수). 0007=압류재산, 0010=국유재산,
            0005=기타일반재산, 0004=불용품, 0002=공유재산, 0003=금융권담보재산,
            0006=유입재산, 0008=수탁재산, 0011=공공개발재산, 0013=파산재산
        opbd_date_start: 검색할 개찰일 시작일자 (yyyyMMdd, 필수)
        opbd_date_end: 검색할 개찰일 종료일자 (yyyyMMdd, 필수)
        bid_div_cd: 입찰구분코드 — "0001"=인터넷, "0002"=현장 — 생략 가능
        dsps_mthod_cd: 처분방식코드 — "0001"=매각, "0002"=임대 — 생략 가능
        pbanc_ymd_start: 검색할 공고일 시작일자 (yyyyMMdd) — 생략 가능
        pbanc_ymd_end: 검색할 공고일 종료일자 (yyyyMMdd) — 생략 가능
        bid_prd_ymd_start: 검색할 입찰기간 시작일자 (yyyyMMdd) — 생략 가능
        bid_prd_ymd_end: 검색할 입찰기간 종료일자 (yyyyMMdd) — 생략 가능
        onbid_pbanc_nm: 공고명 검색어 — 생략 가능
        org_nm: 공고기관명 — 생략 가능
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
        "cltrTypeCd": cltr_type_cd,
        "prptDivCd": prpt_div_cd,
        "opbdDtStart": opbd_date_start,
        "opbdDtEnd": opbd_date_end,
    }
    if bid_div_cd:
        params["bidDivCd"] = bid_div_cd
    if dsps_mthod_cd:
        params["dspsMthodCd"] = dsps_mthod_cd
    if pbanc_ymd_start:
        params["pbancYmdStart"] = pbanc_ymd_start
    if pbanc_ymd_end:
        params["pbancYmdEnd"] = pbanc_ymd_end
    if bid_prd_ymd_start:
        params["bidPrdYmdStart"] = bid_prd_ymd_start
    if bid_prd_ymd_end:
        params["bidPrdYmdEnd"] = bid_prd_ymd_end
    if onbid_pbanc_nm:
        params["onbidPbancNm"] = onbid_pbanc_nm
    if org_nm:
        params["orgNm"] = org_nm

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_PBANC_LIST_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_auction_notice(pbanc_mng_no: str) -> dict:
    """온비드(캠코) 공매 공고상세(공고문 전문, 참가수수료 등)를 조회한다.

    Args:
        pbanc_mng_no: 공고관리번호 (get_auction_notice_list 응답의 pbancMngNo,
            예: "202602-00271-00")
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "resultType": "json",
        "pbancMngNo": pbanc_mng_no,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_PBANC_DETAIL_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_onbid_usage_code(up_ctgr_id: str = "", num_of_rows: int = 100, page_no: int = 1) -> dict:
    """온비드 용도 코드(재산유형 하위 분류 체계)를 조회한다.

    get_auction_list/get_auction_detail 응답의 cltrUsgLclsCtgrId/MclsCtgrId/SclsCtgrId
    (용도대/중/소분류코드)가 어떤 체계로 구성돼 있는지 확인할 때 씀. 최상위(부동산,
    ctgrId="10000")는 up_ctgr_id="" (생략)로 조회되고, up_ctgr_id를 넘기면 그 코드의
    바로 하위 분류만 나옴.

    Args:
        up_ctgr_id: 상위 카테고리 ID (예: "10000"=부동산). 생략하면 전체 코드 조회
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    if up_ctgr_id:
        params["upCtgrId"] = up_ctgr_id

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_USG_CODE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_onbid_address(
    sido: str = "", sigungu: str = "", emd: str = "", num_of_rows: int = 100, page_no: int = 1
) -> dict:
    """온비드에 등록된 소재지 주소(시도/시군구/읍면동/상세주소)를 계층적으로 조회한다.

    get_auction_list의 sido/sigungu/emd 필터에 어떤 정확한 표기(예: "서울특별시" vs
    "서울시")를 써야 하는지 미리 확인하는 용도로 쓸 수 있음. 필터를 아예 안 주면 결과가
    아주 많으므로 최소 sido는 넘기는 걸 권장.

    Args:
        sido: 시도명 필터 (예: "서울특별시") — 생략 가능
        sigungu: 시군구명 필터 (예: "강남구") — 생략 가능
        emd: 읍면동명 필터 (예: "대치동") — 생략 가능
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    if sido:
        params["sdnm"] = sido
    if sigungu:
        params["sggnm"] = sigungu
    if emd:
        params["emdNm"] = emd

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_ADDR_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_nearby_amenities(address: str, category_group_code: str, radius_m: int = 1000) -> dict:
    """주소 반경 내 지하철역·학교·어린이집 등 편의시설을 카카오 로컬 API로 조회한다.

    체크리스트 "⑤ 입지조건"([수동] 항목이던 도로·대중교통·학교 거리)을 자동화하는 도구.
    내부에서 주소를 먼저 카카오 주소검색으로 지오코딩한 뒤, 그 좌표를 중심으로 카테고리
    검색을 한다 — 두 단계 호출을 하나로 묶은 것.

    Args:
        address: 기준 주소 (지번 또는 도로명, 예: "서울 강동구 천호동 145-12")
        category_group_code: 카카오 카테고리 그룹 코드. 자주 쓰는 것:
            "SW8"=지하철역, "SC4"=학교, "PS3"=어린이집·유치원, "AC5"=학원,
            "MT1"=대형마트, "HP8"=병원, "PM9"=약국, "BK9"=은행
        radius_m: 검색 반경(미터), 최대 20000
    """
    if not KAKAO_REST_API_KEY:
        raise RuntimeError("KAKAO_REST_API_KEY가 설정되지 않았습니다 (.env 확인)")

    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

    async with httpx.AsyncClient(timeout=15) as client:
        geo_resp = await client.get(
            KAKAO_ADDRESS_SEARCH_URL, headers=headers, params={"query": address}
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        documents = geo_data.get("documents", [])
        if not documents:
            return {"error": f"주소를 지오코딩하지 못함: {address}", "geocode_raw": geo_data}

        x, y = documents[0]["x"], documents[0]["y"]

        cat_resp = await client.get(
            KAKAO_CATEGORY_SEARCH_URL,
            headers=headers,
            params={
                "category_group_code": category_group_code,
                "x": x,
                "y": y,
                "radius": radius_m,
                "sort": "distance",
            },
        )
        cat_resp.raise_for_status()
        cat_data = cat_resp.json()

    places = [
        {
            "이름": d.get("place_name"),
            "거리_m": d.get("distance"),
            "주소": d.get("road_address_name") or d.get("address_name"),
            "카카오맵URL": d.get("place_url"),
        }
        for d in cat_data.get("documents", [])
    ]
    return {"기준주소": address, "기준좌표": {"x": x, "y": y}, "반경_m": radius_m, "결과": places}


@mcp.tool()
def analyze_price_trend(monthly_deal_amounts: list[dict]) -> dict:
    """여러 달치 실거래가 데이터를 받아 월별 추이(평균/중앙값/거래량/변동률)를 계산한다.

    get_apt_trade_price 등을 여러 계약월(deal_ymd)로 반복 호출한 뒤, 그 결과들을
    이 도구에 넘기면 시세 추이를 계산해준다 — 원본 데이터 수집과 통계 계산을
    분리해서, 이 도구 자체는 어떤 실거래가 API 결과든(아파트/오피스텔/빌라 등) 재사용 가능.

    Args:
        monthly_deal_amounts: [{"year_month": "202506", "amounts_manwon": [29970, 31000, ...]}, ...]
            형태 — 호출자가 실거래가 API 원본 응답(dealAmount 필드, 콤마 포함 문자열일 수
            있음)에서 만원 단위 숫자로 직접 정리해서 넘겨야 함. 이 도구는 원본 XML/JSON
            파싱은 하지 않음(그건 get_apt_trade_price 등의 역할).

    Returns:
        월별 평균가/중앙값/거래량과 전월 대비 변동률이 담긴 dict
    """
    if not monthly_deal_amounts:
        raise ValueError("monthly_deal_amounts가 비어있습니다")

    sorted_months = sorted(monthly_deal_amounts, key=lambda m: m["year_month"])
    monthly_stats = []
    prev_avg = None
    for m in sorted_months:
        amounts = sorted(m["amounts_manwon"])
        if not amounts:
            monthly_stats.append({"year_month": m["year_month"], "거래량": 0})
            continue
        avg = sum(amounts) / len(amounts)
        mid = amounts[len(amounts) // 2]
        change_pct = round((avg - prev_avg) / prev_avg * 100, 2) if prev_avg else None
        monthly_stats.append(
            {
                "year_month": m["year_month"],
                "거래량": len(amounts),
                "평균가_만원": round(avg, 1),
                "중앙값_만원": mid,
                "최저가_만원": amounts[0],
                "최고가_만원": amounts[-1],
                "전월대비_변동률_%": change_pct,
            }
        )
        prev_avg = avg

    return {"월별추이": monthly_stats}


@mcp.tool()
def compare_regions(regions: list[dict]) -> dict:
    """2개 이상 지역의 실거래가 데이터를 받아 평균가·중앙값·㎡당 단가를 비교한다.

    Args:
        regions: [{"region_name": "분당", "amounts_manwon": [...], "areas_sqm": [...]}, ...]
            amounts_manwon과 areas_sqm은 같은 순서로 대응해야 ㎡당 단가 계산이 정확함
            (areas_sqm 생략 시 ㎡당 단가는 계산 안 함)

    Returns:
        지역별 통계 + 평균가 기준 순위가 담긴 dict
    """
    if len(regions) < 2:
        raise ValueError("최소 2개 지역이 필요합니다")

    results = []
    for r in regions:
        amounts = sorted(r["amounts_manwon"])
        if not amounts:
            results.append({"지역": r["region_name"], "거래량": 0})
            continue
        avg = sum(amounts) / len(amounts)
        mid = amounts[len(amounts) // 2]

        price_per_sqm = None
        areas = r.get("areas_sqm")
        if areas and len(areas) == len(r["amounts_manwon"]):
            unit_prices = [a / ar for a, ar in zip(r["amounts_manwon"], areas) if ar > 0]
            if unit_prices:
                price_per_sqm = round(sum(unit_prices) / len(unit_prices), 2)

        results.append(
            {
                "지역": r["region_name"],
                "거래량": len(amounts),
                "평균가_만원": round(avg, 1),
                "중앙값_만원": mid,
                "㎡당_평균_만원": price_per_sqm,
            }
        )

    ranked = sorted(
        [r for r in results if r.get("평균가_만원") is not None],
        key=lambda r: r["평균가_만원"],
        reverse=True,
    )
    return {"지역별통계": results, "평균가_순위": [r["지역"] for r in ranked]}


@mcp.tool()
async def get_auction_bid_result(cltr_mng_no: str, pbct_cdtn_no: Optional[int] = None) -> dict:
    """온비드(캠코) 공매 물건의 입찰결과(낙찰여부·낙찰가 등)를 조회한다.

    get_auction_list/get_auction_detail은 "지금 진행 중"인 물건만 보여주는데, 이 도구는
    이미 끝난 입찰의 결과를 조회한다 — 경매·공매 투자자가 "이 지역·이 유형은 보통
    낙찰가율이 얼마나 되는지" 감을 잡는 데 씀.

    주의: 엔드포인트는 물건목록/상세와 같은 기관(B010003)이라 같은 MOLIT_SERVICE_KEY로
    될 가능성이 높지만, 이 서버에서 실제 호출로 검증한 적은 없음 (2026-08-06 기준).

    Args:
        cltr_mng_no: 물건관리번호
        pbct_cdtn_no: 공매조건번호 (생략 가능)
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 10,
        "resultType": "json",
        "cltrMngNo": cltr_mng_no,
    }
    if pbct_cdtn_no is not None:
        params["pbctCdtnNo"] = pbct_cdtn_no

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_BID_RESULT_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_auction_regional_stats(num_of_rows: int = 100, page_no: int = 1) -> dict:
    """온비드(캠코) 공매 물건의 지역별 낙찰 통계를 조회한다.

    주의: 이 서버에서 실제 호출로 검증한 적 없음 (2026-08-06 기준, GitHub 공개 프로젝트
    소스코드에서 URL만 확인한 상태).
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_REGIONAL_STATS_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_auction_usage_stats(num_of_rows: int = 100, page_no: int = 1) -> dict:
    """온비드(캠코) 공매 물건의 용도별 낙찰 통계를 조회한다.

    주의: 이 서버에서 실제 호출로 검증한 적 없음 (2026-08-06 기준, GitHub 공개 프로젝트
    소스코드에서 URL만 확인한 상태).
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(ONBID_USAGE_STATS_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_jeonse_guarantee_products(region_code: str = "", num_of_rows: int = 100, page_no: int = 1) -> dict:
    """HUG(주택도시보증공사) 전세자금보증상품의 지역별 최대 임차보증금액/추천 상품을 조회한다.

    전세사기 체크리스트(calc_jeonse_ratio, generate_landlord_disclosure_request)와 함께
    쓰면 "이 전세, 보증보험 상품 한도 안에 들어오는지"까지 확인할 수 있음.

    주의: HUG는 온비드(B010003)·국토부(1613000)와 다른 별도 기관(B551408)이라 별도
    활용신청이 필요할 가능성이 높음 — 이 서버에서 실제 호출로 검증한 적 없음
    (2026-08-06 기준, GitHub 공개 프로젝트 소스코드에서 URL만 확인).

    Args:
        region_code: 지역 코드 (정확한 코드 체계 미확인 — 첫 호출 시 빈 값으로 시도해서
            응답 구조부터 확인할 것)
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    if region_code:
        params["regionCode"] = region_code

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(HUG_JNSE_MAX_RENT_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def get_jeonse_guarantee_detail(prod_id: str = "", num_of_rows: int = 100, page_no: int = 1) -> dict:
    """HUG 전세자금보증상품의 상세정보(금리, 조건 등)를 조회한다.

    주의: 이 서버에서 실제 호출로 검증한 적 없음, prod_id 파라미터명·정확한 값 형식도
    미확인 — 첫 호출 시 prod_id 없이 시도해서 응답 구조부터 확인할 것
    (2026-08-06 기준).

    Args:
        prod_id: 상품 ID (정확한 형식 미확인)
        num_of_rows: 한 페이지 결과 수
        page_no: 페이지 번호
    """
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    params = {
        "serviceKey": MOLIT_SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    if prod_id:
        params["prodId"] = prod_id

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(HUG_JNSE_PROD_DTL_URL, params=params)
        resp.raise_for_status()
        return resp.json()


async def _vworld_geocode(client: httpx.AsyncClient, address: str, addr_type: str = "parcel") -> dict:
    """내부 헬퍼 — vworld_geocode_address 도구와 get_land_use_zoning이 공유해서 씀."""
    if not VWORLD_API_KEY:
        raise RuntimeError("VWORLD_API_KEY가 설정되지 않았습니다 (.env 확인, vworld.kr에서 무료 발급)")

    params = {
        "service": "address",
        "request": "getCoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": address,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "type": addr_type,
        "key": VWORLD_API_KEY,
    }
    resp = await client.get(VWORLD_ADDRESS_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    result = data.get("response", {})
    if result.get("status") != "OK":
        raise RuntimeError(f"브이월드 지오코딩 실패: {address} — {result}")

    point = result["result"]["point"]
    return {
        "입력주소": address,
        "정제주소": result.get("refined", {}).get("text", address),
        "x": float(point["x"]),
        "y": float(point["y"]),
    }


async def _vworld_get_features(
    client: httpx.AsyncClient, layer_id: str, x: float, y: float, size: int = 10
) -> list[dict]:
    """내부 헬퍼 — 좌표 기준 반경(점) 필터로 브이월드 레이어를 조회."""
    params = {
        "service": "data",
        "request": "GetFeature",
        "data": layer_id,
        "key": VWORLD_API_KEY,
        "domain": VWORLD_DOMAIN,
        "format": "json",
        "size": size,
        "geometry": "false",
        "geomFilter": f"POINT({x} {y})",
    }
    resp = await client.get(VWORLD_DATA_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    result = data.get("response", {})
    status = result.get("status")
    if status == "NOT_FOUND":
        return []
    if status != "OK":
        return [{"error": f"레이어 {layer_id} 조회 실패: {result.get('error', status)}"}]

    features = result.get("result", {}).get("featureCollection", {}).get("features", [])
    return [f.get("properties", {}) for f in features]


@mcp.tool()
async def vworld_geocode_address(address: str, addr_type: str = "parcel") -> dict:
    """브이월드 지오코더로 주소를 좌표(WGS84)로 변환한다.

    카카오 지오코딩과 별개 — 브이월드 좌표가 get_land_use_zoning 등 브이월드 레이어
    조회에 그대로 재사용 가능해서 따로 만듦(카카오 좌표를 브이월드에 넘겨도 되지만,
    두 지오코더의 결과가 미묘하게 다를 수 있어 안전하게 분리함).

    Args:
        address: 조회할 주소
        addr_type: "parcel"(지번주소, 기본값) 또는 "road"(도로명주소)
    """
    async with httpx.AsyncClient(timeout=15) as client:
        return await _vworld_geocode(client, address, addr_type)


@mcp.tool()
async def get_land_use_zoning(address: str) -> dict:
    """브이월드로 용도지역·용도지구·용도구역·토지거래허가구역을 조회한다.

    체크리스트 "③ 토지이용계획, 공법상 이용제한 및 거래규제" [수동] 항목을 자동화하는
    도구 — GitHub 공개 프로젝트(korean-land-mcp)의 레이어 구성을 그대로 참고해서 작성함.
    2026-08-06 실제 호출로 검증 완료 (서울 강남구 역삼동 826 → 일반상업지역 정상 반환).

    건폐율/용적률 상한, 지구단위계획, 도시계획시설, 42개 다른 법령 지정사항은 아직
    미구현 — korean-land-mcp는 이걸 다 다루니 필요하면 그쪽 레이어 정의를 추가 이식할 것.

    Args:
        address: 조회할 주소 (지번 또는 도로명)
    """
    async with httpx.AsyncClient(timeout=15) as client:
        geo = await _vworld_geocode(client, address)
        x, y = geo["x"], geo["y"]

        async def collect(layers: dict[str, str]) -> list[dict]:
            out = []
            for layer_id, label in layers.items():
                for props in await _vworld_get_features(client, layer_id, x, y):
                    out.append({"레이어": label, **props})
            return out

        use_zone = await collect(VWORLD_USE_ZONE_LAYERS)
        use_district = await collect(VWORLD_USE_DISTRICT_LAYERS)
        use_area = await collect(VWORLD_USE_AREA_LAYERS)
        land_transaction_permit = await collect(VWORLD_EXTRA_LAYERS)

    return {
        "주소": geo["정제주소"],
        "좌표": {"x": x, "y": y},
        "용도지역": use_zone,
        "용도지구": use_district,
        "용도구역": use_area,
        "토지거래허가구역": land_transaction_permit,
        "참고": "용도지역은 정확히 1개만 나오는 게 정상(도시/관리/농림/자연환경보전 중 하나). "
        "빈 리스트는 '해당 없음'이지 오류가 아님. 건폐율·용적률 상한은 시·군 조례 사항이라 "
        "search_law로 별도 확인 필요.",
    }


@mcp.tool()
def get_broker_offices(region_keyword: str = "", name_keyword: str = "", limit: int = 50) -> dict:
    """전국공인중개사사무소표준데이터 로컬 캐시에서 중개사무소를 검색한다.

    라이브 API(tn_pubr_public_med_office_api)를 매번 호출하지 않고, 미리
    scripts/build_broker_cache.py로 받아둔 data/broker_offices.json을 읽어서 로컬
    필터링한다 — 이 API의 서버 쪽 필드 검색이 실제로는 동작하지 않기 때문(모듈
    docstring 참고). 그래서 region_keyword/name_keyword는 정확한 코드가 아니라
    도로명주소·지번주소·제공기관명(region_keyword) 또는 중개사무소명(name_keyword)에
    대한 단순 부분 문자열 매칭이다 — 오타나 축약 표기는 안 잡힐 수 있음.

    캐시가 없으면 먼저 `python scripts/build_broker_cache.py`를 실행해서 만들 것
    (데이터 갱신주기가 연 1회라 캐시가 며칠~몇 주 묵어도 문제없음).

    Args:
        region_keyword: 소재지 주소나 제공기관명에 포함될 키워드 (예: "노원구", "천안시 서북구")
        name_keyword: 중개사무소명에 포함될 키워드 (예: "믿음")
        limit: 반환할 최대 건수 (매칭 전체 건수는 별도로 함께 반환됨)
    """
    if not region_keyword and not name_keyword:
        raise ValueError(
            "region_keyword 또는 name_keyword 중 최소 하나는 지정해야 합니다 "
            "(전체 6.8만여 건이 반환되는 것을 방지)"
        )

    if not BROKER_CACHE_PATH.exists():
        raise RuntimeError(
            f"로컬 캐시가 없습니다: {BROKER_CACHE_PATH}\n"
            "먼저 `python scripts/build_broker_cache.py`를 실행해서 캐시를 생성할 것."
        )

    cache = json.loads(BROKER_CACHE_PATH.read_text(encoding="utf-8"))
    items = cache.get("items", [])

    def matches(item: dict) -> bool:
        if region_keyword:
            haystack = " ".join(
                [
                    item.get("lctnRoadNmAddr") or "",
                    item.get("lctnLotnoAddr") or "",
                    item.get("insttNm") or "",
                ]
            )
            if region_keyword not in haystack:
                return False
        if name_keyword and name_keyword not in (item.get("medOfficeNm") or ""):
            return False
        return True

    matched = [item for item in items if matches(item)]

    return {
        "캐시_기준시각": cache.get("fetched_at"),
        "캐시_전체건수": cache.get("count"),
        "매칭건수": len(matched),
        "반환건수": min(len(matched), limit),
        "결과": matched[:limit],
    }


if __name__ == "__main__":
    mcp.run()
