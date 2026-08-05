"""
전국공인중개사사무소표준데이터(data.go.kr, tn_pubr_public_med_office_api)를
페이지네이션으로 전량 수집해서 로컬 캐시(data/broker_offices.json)로 저장한다.

이 API는 문서상 필드별 검색 파라미터(instt_nm, RPRSV_NM 등)가 있다고 나오지만
실제로는 동작하지 않는다 (2026-08-06 실호출 확인: 문서에 나온 값 그대로 넘겨도
NODATA_ERROR, camelCase로 바꾸면 SERVICE_ERROR). 그래서 서버 쪽 필터링을 포기하고
pageNo/numOfRows/type만 써서 전체(약 6.8만건)를 받은 뒤 server.py의
get_broker_offices가 로컬에서 필터링한다.

데이터 갱신주기가 연 1회(개별 지자체는 월 1회)라 캐시가 며칠 묵어도 문제없음 —
이 스크립트를 가끔(월 1회 정도) 재실행해서 캐시를 갱신할 것.

실행: python scripts/build_broker_cache.py
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

MOLIT_SERVICE_KEY = os.environ.get("MOLIT_SERVICE_KEY", "")
BROKER_OFFICE_URL = "https://api.data.go.kr/openapi/tn_pubr_public_med_office_api"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "broker_offices.json"
NUM_OF_ROWS = 1000


async def fetch_all() -> list[dict]:
    if not MOLIT_SERVICE_KEY:
        raise RuntimeError("MOLIT_SERVICE_KEY가 설정되지 않았습니다 (.env 확인)")

    items: list[dict] = []
    page_no = 1
    total_count = None

    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            params = {
                "serviceKey": MOLIT_SERVICE_KEY,
                "pageNo": page_no,
                "numOfRows": NUM_OF_ROWS,
                "type": "json",
            }
            resp = await client.get(BROKER_OFFICE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            header = data.get("header", {})
            if header.get("resultCode") != "00":
                raise RuntimeError(f"API 오류 (page {page_no}): {header}")

            body = data.get("body") or {}
            if total_count is None:
                total_count = body.get("totalCount", 0)
                print(f"전체 {total_count}건, {NUM_OF_ROWS}건씩 페이지네이션 시작")

            page_items = (body.get("items") or {}).get("item") or []
            if isinstance(page_items, dict):
                # numOfRows보다 결과가 적게 남으면 리스트 대신 dict 1개로 오는 경우가 있음
                page_items = [page_items]
            items.extend(page_items)

            print(f"  page {page_no}: {len(page_items)}건 (누적 {len(items)}/{total_count})")

            if not page_items or len(items) >= total_count:
                break
            page_no += 1

    return items


async def main() -> None:
    items = await fetch_all()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"저장 완료: {OUT_PATH} ({len(items)}건)")


if __name__ == "__main__":
    asyncio.run(main())
