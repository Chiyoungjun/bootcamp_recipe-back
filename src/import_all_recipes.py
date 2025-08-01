from service.recipe_service import fetch_and_save_all_recipes
from database import SessionLocal

if __name__ == "__main__":
    with SessionLocal() as db:
        fetch_and_save_all_recipes(db, total=10000, batch_size=500)
    print("전체 레시피 적재 완료!")
