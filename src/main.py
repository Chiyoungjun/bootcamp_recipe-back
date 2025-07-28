from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.user import router as user_router  # 있다면
from routes.recipe import router as recipe_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router, prefix="/api/users")
app.include_router(recipe_router, prefix="/api")  # 중요! prefix="/api" 유지
