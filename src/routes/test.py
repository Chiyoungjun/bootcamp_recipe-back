from fastapi import APIRouter, HTTPException
from service.test_service import test_service

router = APIRouter()

@router.get("/")
async def get_test():
    try:
        data = await test_service()
        return {"status": 200, "message": "Backend 연결 테스트 성공!", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
