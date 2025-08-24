from sqlalchemy import func, cast, Float, desc

alpha = 0.3  # 평점 참여자 가중치
beta = 0.1   # 조회수 가중치
#score=평균 평점+0.3×log(1+평점 참여자 수)+0.1×log(1+조회수)

def score_expression_recipe(Recipe):
    return (
        Recipe.avg_rating +
        alpha * func.log(1 + Recipe.rating_count) +
        beta * func.log(1 + cast(Recipe.view_count, Float))
    )

def score_expression_user_recipe(UserRecipe):
    return (
        UserRecipe.avg_rating +
        alpha * func.log(1 + UserRecipe.rating_count) +
        beta * func.log(1 + cast(UserRecipe.view_count, Float))
    )

def get_basic_rankings(db, Recipe, RecipeRatingHistories, period_enum, period_start_date):
    score_expr = (
        (RecipeRatingHistories.rating_sum / RecipeRatingHistories.rating_count) +
        alpha * func.log(1 + RecipeRatingHistories.rating_count) +
        beta * func.log(1 + cast(Recipe.view_count, Float))
    ).label("score")

    return (
        db.query(Recipe, score_expr)
        .join(RecipeRatingHistories, Recipe.id == RecipeRatingHistories.recipe_id)
        .filter(
            RecipeRatingHistories.period_type == period_enum,
            RecipeRatingHistories.period_start_date == period_start_date,
            RecipeRatingHistories.rating_count > 0,
        )
        .order_by(desc("score"))
        .all()
    )

def get_user_rankings(db, UserRecipe):
    score_expr = score_expression_user_recipe(UserRecipe).label("score")
    return (
        db.query(UserRecipe, score_expr)
        .filter(UserRecipe.rating_count > 0)
        .order_by(desc("score"))
        .all()
    )
