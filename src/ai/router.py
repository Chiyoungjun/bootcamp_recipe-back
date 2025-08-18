from fastapi import APIRouter, UploadFile, File, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from ai.service import predict_bmi_category  # AI 예측 함수
from user.models import UserDetail            # UserDetail DB 모델
from recipe.models import Recipe
from database import get_db
from ai import service

router = APIRouter()

@router.post("/recipes/upload")
async def upload_recipe_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return await service.analyze_image_and_search_recipes(image, db)

@router.get("/recommendations/bmi")
def get_bmi_recommendations(user_id: str = Query(...), db: Session = Depends(get_db)):
    # 회원 신체 정보 읽기
    user_profile = db.query(UserDetail).filter_by(user_id=user_id).first()
    if not user_profile or not user_profile.height or not user_profile.weight or not user_profile.gender:
        raise HTTPException(400, "사용자 신체 정보(키, 몸무게, 성별)가 필요합니다.")

    # AI 모델로 BMI 카테고리 예측 (키/몸무게/성별 입력)
    bmi_class = predict_bmi_category(
        float(user_profile.height),
        float(user_profile.weight),
        user_profile.gender
    )

    # 머신러닝 학습된 ai_category 기준 분류명 세분화 매핑 예시
    BMI_CATEGORY_MAP = {
        "Extreme Obesity": ["샐러드", "국, 찌개", "반찬"],    # 고도 비만: 저칼로리, 수분 및 채소 위주 음식 추천
        "Obesity": ["샐러드", "국, 찌개", "반찬"],            # 비만: 저칼로리와 건강식 위주 추천
        "Overweight": ["샐러드", "반찬"],                      # 과체중: 가벼운 식단과 반찬류 추천
        "Normal": [],                                         # 정상: 인기, 조회수 기반 전체 레시피 추천
        "Weak": ["밥", "구이, 찜"],                            # 저체중(약함): 영양가 있는 밥과 고기 구이, 찜류 추천
        "Extremely Weak": ["밥", "구이, 찜"]                   # 극저체중: 고영양 밥과 간단한 고기류 집중 추천
    }

    categories = BMI_CATEGORY_MAP.get(bmi_class, ["샐러드", "반찬"])  # 기본값은 과체중/기타에 맞춘 샐러드, 반찬

    if categories:
        query = db.query(Recipe).filter(Recipe.category.in_(categories)).order_by(Recipe.INFO_ENG.desc())
    else:
        query = db.query(Recipe).order_by(Recipe.view_count.desc())

    recipes = query.limit(10).all()

    return {
        "bmi_category": bmi_class,
        "recipes": [{
            "id": r.id,
            "name": r.name,
            "image_url": r.image_url,
            "category": r.category,  
            "avg_rating": float(r.avg_rating or 0),
            "rating_count": r.rating_count or 0,
            "view_count": r.view_count or 0,
        } for r in recipes]
    }
