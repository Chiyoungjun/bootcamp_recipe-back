from fastapi import APIRouter, HTTPException, Request
from service.user_service import UserService

router = APIRouter()
service = UserService()

@router.get("/")
async def get_users():
    try:
        data = await service.get_users()
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}")
async def get_one_user(user_id: int):
    try:
        data = await service.get_one_user(user_id)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signin")
async def sign_in(request: Request):
    user_info = await request.json()
    try:
        data = await service.sign_in(user_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/signup")
async def sign_up(request: Request):
    user_info = await request.json()
    try:
        data = await service.sign_up(user_info)
        return {"status": 200, "message": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
