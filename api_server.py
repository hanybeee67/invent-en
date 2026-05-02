"""
Everest Inventory API Server
============================
POS ↔ 재고관리 앱 연동을 위한 FastAPI REST API 서버
파일 위치: 재고관리 앱 루트 (app-en.py 와 같은 폴더)

Render.com 실행: uvicorn api_server:app --host 0.0.0.0 --port $PORT
로컬 테스트:     uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys

# core/logic.py 및 config.py 임포트를 위해 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

import config
from core.logic import (
    deduct_by_menu,
    get_menu_cost_breakdown,
    get_low_stock_items,
    get_available_menus,
)

# ── 앱 초기화 ─────────────────────────────────────────────────
app = FastAPI(
    title="Everest Inventory API",
    description="Everest POS ↔ 재고관리 앱 연동 REST API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 내부 API 키 (POS의 INTERNAL_API_KEY 와 동일 값으로 설정)
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

# ── branch_id(정수) → branch_name(한국어) 변환 ────────────────
# POS DB의 branches 테이블 순서와 맞춰야 합니다.
BRANCH_MAP: dict[int, str] = {
    1: "동탄",
    2: "동대문",
    3: "굿모닝시티",
    4: "양재",
    5: "수원영통",
    6: "영등포",
    7: "룸비니",
}

def get_branch_name(branch_id: int) -> str:
    name = BRANCH_MAP.get(branch_id)
    if name:
        return name
    # 매핑 없을 경우 config.BRANCHES 첫 번째 값 사용
    return config.BRANCHES[0] if config.BRANCHES else "동탄"


# ── 인증 헬퍼 ─────────────────────────────────────────────────
def verify_api_key(x_api_key: Optional[str]) -> None:
    """INTERNAL_API_KEY 검증. 키가 설정된 경우에만 강제."""
    if INTERNAL_API_KEY and x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="인증 실패: 유효하지 않은 API Key")


# ── 요청/응답 모델 ────────────────────────────────────────────

class DeductItem(BaseModel):
    item_id: str            # POS 메뉴명 (name_ko)
    qty: int                # 판매 수량 (인분)
    note: Optional[str] = "POS 판매 자동차감"


class DeductRequest(BaseModel):
    branch_id: int          # POS branches.id
    items: List[DeductItem] # 판매된 메뉴 목록
    source: Optional[str] = "pos"


# ─────────────────────────────────────────────────────────────
# 엔드포인트 1: 헬스체크
# GET /api/health
# ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
def health_check():
    """서버 상태 확인 — 인증 불필요"""
    return {
        "status":       "ok",
        "service":      "Everest Inventory API",
        "version":      "1.0.0",
        "storage_mode": config.STORAGE_MODE,
        "base_dir":     config.BASE_DIR,
    }


# ─────────────────────────────────────────────────────────────
# 엔드포인트 2: 레시피 조회
# GET /api/recipe/ingredients?menuId={menu_name}
# ─────────────────────────────────────────────────────────────
@app.get("/api/recipe/ingredients", tags=["recipe"])
def get_recipe_ingredients(
    menuId: str = Query(..., description="POS 메뉴명 (name_ko)"),
    x_api_key: Optional[str] = Header(None),
):
    """
    POS가 결제 완료 후 식재료 목록을 조회하는 API.
    core/logic.py의 get_menu_cost_breakdown() 사용.
    """
    verify_api_key(x_api_key)

    items, result = get_menu_cost_breakdown(menuId, servings=1)
    if items is None:
        raise HTTPException(
            status_code=404,
            detail=f"메뉴 '{menuId}'를 레시피에서 찾을 수 없습니다. 오류: {result}"
        )

    ingredient_list = [
        {
            "item_id": i["mapped"],
            "name":    i["ingredient"],
            "qty":     i["qty_g"],
            "unit":    "g",
        }
        for i in items if i.get("type") not in ("skip", "zero")
    ]

    total_cost = result if isinstance(result, (int, float)) else 0

    return {
        "menu_id":    menuId,
        "menu_name":  menuId,
        "items":      ingredient_list,
        "total_cost": total_cost,
    }


# ─────────────────────────────────────────────────────────────
# 엔드포인트 3: 재고 자동 차감  ← POS 결제 완료 시 호출
# POST /api/inventory/out
# ─────────────────────────────────────────────────────────────
@app.post("/api/inventory/out", tags=["inventory"])
def deduct_inventory(
    request: DeductRequest,
    x_api_key: Optional[str] = Header(None),
):
    """
    POS 결제 완료 후 판매된 메뉴 목록으로 재고를 자동 차감.
    core/logic.py의 deduct_by_menu() 사용.

    요청 예시:
    {
        "branch_id": 1,
        "items": [
            { "item_id": "치킨마살라", "qty": 2 },
            { "item_id": "갈릭난",     "qty": 3 }
        ],
        "source": "pos"
    }
    """
    verify_api_key(x_api_key)

    branch_name = get_branch_name(request.branch_id)
    all_alerts: List[str] = []
    deducted = 0
    errors:   List[str] = []

    for item in request.items:
        try:
            success, message, alerts = deduct_by_menu(
                menu_name=item.item_id,
                servings=item.qty,
                branch=branch_name,
                sale_price=0,      # 판매가는 POS DB에서 관리
            )
            if success:
                deducted += 1
                all_alerts.extend(alerts)
            else:
                errors.append(f"{item.item_id}: {message}")
        except Exception as e:
            errors.append(f"{item.item_id}: {str(e)}")

    return {
        "success":  len(errors) == 0,
        "deducted": deducted,
        "alerts":   all_alerts,        # 재고 부족 품목 목록
        "errors":   errors,
        "message":  (
            f"재고 차감 완료 | 지점: {branch_name} | {deducted}개 메뉴 처리"
            if not errors
            else f"일부 오류: {'; '.join(errors)}"
        ),
    }


# ─────────────────────────────────────────────────────────────
# 엔드포인트 4: 재고 부족 알림 조회
# GET /api/inventory/alerts?branch_id=1
# ─────────────────────────────────────────────────────────────
@app.get("/api/inventory/alerts", tags=["inventory"])
def get_inventory_alerts(
    branch_id: int = Query(..., description="POS branch_id"),
    x_api_key: Optional[str] = Header(None),
):
    """지점별 최소 수량 미달 품목 목록 반환"""
    verify_api_key(x_api_key)
    branch_name = get_branch_name(branch_id)
    low_items = get_low_stock_items(branch_name)
    return {
        "branch":          branch_name,
        "low_stock_count": len(low_items),
        "items":           low_items,
    }


# ─────────────────────────────────────────────────────────────
# 엔드포인트 5: 등록된 메뉴 목록 (디버깅용)
# GET /api/menus
# ─────────────────────────────────────────────────────────────
@app.get("/api/menus", tags=["recipe"])
def list_menus(x_api_key: Optional[str] = Header(None)):
    """레시피북에 등록된 메뉴 전체 목록"""
    verify_api_key(x_api_key)
    menus = get_available_menus()
    return {"count": len(menus), "menus": menus}


# ─────────────────────────────────────────────────────────────
# 로컬 개발 실행
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
