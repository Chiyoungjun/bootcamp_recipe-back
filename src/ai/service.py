import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile
from collections import Counter
from ai.ai_model import model, bmi_model, gender_encoder, category_model  # ai_model.py에서 직접 import!
from sqlalchemy.orm import Session
from recipe.service import get_recipe, predict_recipe_category  # predict_recipe_category 추가!
import numpy as np

UPLOAD_DIR = "temp_uploads"

# ------------------------------------------
# 이미지 파일 저장 (고유 파일명 생성: UUID 기반)
# ------------------------------------------
async def save_image_file(image: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename)[1]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {str(e)}")
    return file_path

# ------------------------------------------
# YOLO 추론: 음식명 리스트 반환
# ------------------------------------------
def run_yolo_inference(file_path: str) -> list:
    try:
        results = model(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(500, f"YOLO 추론 실패: {str(e)}")
    food_names = []
    names = model.names
    for r in results:
        if hasattr(r, "boxes"):
            for box in r.boxes:
                class_id = int(box.cls[0])
                label = names[class_id]
                food_names.append(label)
    if os.path.exists(file_path):
        os.remove(file_path)
    if not food_names:
        raise HTTPException(404, "이미지에서 음식을 인식하지 못했습니다.")
    return food_names

# ------------------------------------------
# 대표 음식명 추출 (YOLO 결과 for DB 검색)
# ------------------------------------------
def get_representative_food_name(food_names: list) -> str:
    common_food_name = Counter(food_names).most_common(1)[0][0]
    if "_" in common_food_name:
        _, search_name = common_food_name.split("_", 1)
    else:
        search_name = common_food_name
    return search_name

# ------------------------------------------
# 이미지 분석 + 레시피 추천 (ML 분류까지 반영)
# ------------------------------------------
async def analyze_image_and_search_recipes(image: UploadFile, db: Session):
    file_path = await save_image_file(image)
    food_names = run_yolo_inference(file_path)
    search_name = get_representative_food_name(food_names)
    recipes = get_recipe(search_name, db)
    # ML 분류 결과도 함께 포함해 반환 (예: 첫 번째 레시피 대상)
    if not recipes:
        raise HTTPException(404, f"{search_name} 기반 검색 결과가 없습니다.")
    for recipe in recipes:
        # 머신러닝 카테고리 예측해서 ai_category에 반영 (수정)
        recipe.category = predict_recipe_category(recipe.name, recipe.description)
    return [{
        "id": r.id,
        "name": r.name,
        "image_url": r.image_url,
        "ai_category": r.category,
        "avg_rating": float(r.avg_rating or 0),
        "rating_count": r.rating_count or 0,
        "view_count": r.view_count or 0,
        "description": r.description,
    } for r in recipes]

# ------------------------------------------
# BMI 머신러닝 예측 (AI 기반 추천)
# ------------------------------------------
def predict_bmi_category(height: float, weight: float, gender: str) -> str:
    try:
        gender_code = gender_encoder.transform([gender])[0]
    except Exception as e:
        raise HTTPException(400, f"잘못된 성별 값: {gender} ({str(e)})")
    X_input = np.array([[height, weight, gender_code]])
    return bmi_model.predict(X_input)[0]
