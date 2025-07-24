from fastapi import FastAPI
from routes.user import router as user_router
from routes.recipe import router as recipe_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(user_router, prefix="/api/users")
app.include_router(recipe_router, prefix="/api/recipes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 필요에 따라 프론트 주소 변경
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
