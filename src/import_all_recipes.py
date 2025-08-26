from recipe.models import Recipe
from recipe.service import predict_recipe_category
from database import SessionLocal

if __name__ == "__main__":
    with SessionLocal() as db:
        recipes = db.query(Recipe).all()
        for recipe in recipes:
            old_cat = recipe.category
            new_cat = predict_recipe_category(recipe.name, recipe.description, "", recipe.category or "")
            print(f"Recipe ID {recipe.id}: {old_cat} -> {new_cat}")
            
            if old_cat != new_cat:
                recipe.category = new_cat
            else:
                print(f"Recipe ID {recipe.id} 카테고리 변화 없음")
        
        db.commit()
        print("커밋 완료")
