from fastapi import APIRouter, Query
from .service import search_places_by_keyword

router = APIRouter(prefix="/api/maps", tags=["Maps"])

@router.get("/search")
def search_places(
    keyword: str = Query(..., description="검색할 키워드(음식명 등)"),
    x: float = Query(None, description="경도 optional"),
    y: float = Query(None, description="위도 optional"),
    radius: int = Query(2000, description="검색반경(m, 기본 2000)")
):
    """
    카카오맵 장소(음식점 등) 검색 API 프록시: /api/maps/search?keyword=OOO&x=경도&y=위도
    """
    data = search_places_by_keyword(keyword, x, y, radius)
    shops = [
        {
            "name": place.get("place_name"),
            "address": place.get("address_name"),
            "road_address": place.get("road_address_name"),
            "category": place.get("category_group_name") or place.get("category_name"),
            "phone": place.get("phone"),
            "x": place.get("x"),
            "y": place.get("y"),
            "url": place.get("place_url"),
            "distance": place.get("distance"),
        }
        for place in data.get("documents", [])
    ]
    return {"results": shops, "meta": data.get("meta", {})}
