from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.user import router as user_router  # user 라우터가 있다면
from routes.recipe import router as recipe_router

app = FastAPI()

# 미들웨어 등록은 라우터 등록보다 먼저 하는 것이 깔끔합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 주소 (배포시에는 실제 도메인만 허용 권장)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록 (prefix는 필요에 맞게 설정)
app.include_router(user_router, prefix="/api/users")
app.include_router(recipe_router, prefix="/api")
