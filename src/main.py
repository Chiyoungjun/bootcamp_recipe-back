from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from recipe.router import router as recipe_router
from user.router import router as user_router, public_router as user_public_router
from ai.router import router as ai_router        # ✅ 챗봇 라우터는 여기(ai)
from maps.router import router as maps_router

from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",  # 로컬 두 형태 모두 허용
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# http://localhost:8000/uploads/파일명  ← 이렇게 접근 가능
# app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
# 라우터 등록 — 각자 한 번만
app.include_router(recipe_router, prefix="/api")          # /api/...
app.include_router(user_router, prefix="/api/users")      # /api/users/...
app.include_router(user_public_router, prefix="/api")     # /api/userrecipedetail
app.include_router(ai_router, prefix="/api")              # ✅ ai.router가 prefix="/chatbot"이면 /api/chatbot/...
app.include_router(maps_router)                           # 내부에서 prefix 정의했다면 유지
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ❌ 아래 두 줄은 삭제(중복/혼선의 원인)
# from recipe.router import router as chatbot_router
# app.include_router(chatbot_router)
