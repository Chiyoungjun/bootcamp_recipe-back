from fastapi import APIRouter, HTTPException, Query
from service.recipe_service import RecipeService

router = APIRouter()
service = RecipeService()

@router.get("/")
async def get_recipes():
    try:
        data = await service.get_recipes()
        return {"status": 200, "message": "success", "data": data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve recipes")

@router.get("/{recipe_id}")
async def get_recipe(recipe_id: int):
    try:
        data = await service.get_recipe(recipe_id)
        if not data:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return {"status": 200, "message": "success", "data": data}
    except HTTPException as he:
        raise he
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to retrieve recipe")

@router.get("/external/search")
async def search_external_recipes(q: str = Query(..., description="검색어")):
    try:
        data = await service.get_external_recipes(q)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve external recipes: {str(e)}")
