from recipe.models import Recipe
from recipe.service import predict_recipe_category
from database import SessionLocal

if __name__ == "__main__":
    with SessionLocal() as db:
        recipes = db.query(Recipe).all()
        for recipe in recipes:
            # 머신러닝 카테고리 예측해서 기존 category 컬럼에 덮어쓰기
            recipe.category = predict_recipe_category(recipe.name, recipe.description)
        db.commit()
    print("모든 레시피 category 값을 AI 결과로 덮어썼음!")
