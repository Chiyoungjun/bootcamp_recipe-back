# src/ai/ai_model.py

from ultralytics import YOLO
import joblib
from pathlib import Path

# YOLO 모델 (이미지 음식추론)
model = YOLO("C:/Users/user/Desktop/bootcamp_recipe/project_recipe-back/src/ai/best.pt")

# BMI 머신러닝 모델 및 성별 인코더
BMI_MODEL_PATH = Path("C:/Users/user/Desktop/bootcamp_recipe/project_recipe-back/src/ai/bmi_rf_model.pkl")
ENCODER_PATH = Path("C:/Users/user/Desktop/bootcamp_recipe/project_recipe-back/src/ai/gender_encoder.pkl")

bmi_model = joblib.load(BMI_MODEL_PATH)
gender_encoder = joblib.load(ENCODER_PATH)

# ===== 레시피 카테고리 머신러닝 모델 및 벡터라이저 추가 =====
CATEGORY_MODEL_PATH = Path("C:/Users/user/Desktop/bootcamp_recipe/project_recipe-back/src/ai/auto_recipe_kmeans_mapped.pkl")

loaded = joblib.load(CATEGORY_MODEL_PATH)

category_model = loaded['model']
vectorizer = loaded['vectorizer']
manual_map = loaded['manual_map']