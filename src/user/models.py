from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, Integer, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from base import Base  # src/base.py 또는 공용 Base import


# ----------- User 테이블 ----------
class User(Base):
    __tablename__ = 'user'

    user_id = Column(String(50), primary_key=True)
    pw = Column(String(255), nullable=False)
    ko_name = Column(String(30))
    email = Column(String(100))

    user_detail = relationship("UserDetail", uselist=False, back_populates="user", cascade="all, delete-orphan")
    bmi_recommendations = relationship("UserBmiRecommendation", back_populates="user", cascade="all, delete-orphan")
    search_histories = relationship("UserSearchHistory", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorites", back_populates="user", cascade="all, delete-orphan")
    user_recipes = relationship("UserRecipe", back_populates="user", cascade="all, delete-orphan")  # ← 추가됨


# ----------- UserDetail ----------
class UserDetail(Base):
    __tablename__ = 'user_detail'
    user_id = Column(String(50), ForeignKey('user.user_id', ondelete='CASCADE'), primary_key=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    gender = Column(String(20), nullable=True)
    preferred_food = Column(String(100), nullable=True)
    preferred_tags = Column(String(200), nullable=True)
    birth_date = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="user_detail")


# ----------- UserSearchHistory ----------
class UserSearchHistory(Base):
    __tablename__ = 'user_search_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=True)
    search_word = Column(String(255), nullable=False)
    search_time = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="search_histories")


# ----------- UserBmiRecommendation ----------
class UserBmiRecommendation(Base):
    __tablename__ = 'user_bmi_recommendation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    bmi_value = Column(Float, nullable=False)
    recommended_at = Column(DateTime, default=datetime.now, nullable=False)
    recommended_recipes = Column(Text, nullable=True)

    user = relationship("User", back_populates="bmi_recommendations")


# ----------- UserFavorites ----------
class UserFavorites(Base):
    __tablename__ = 'user_favorites'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorited_by")

    __table_args__ = (
        UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe_favorite'),
    )


# ---------- UserRecipe(유저작성 레시피) ----------
class UserRecipe(Base):
    __tablename__ = 'user_recipes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    view_count = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3, 2), default=0.00)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 단계별 내용 필드들
    MANUAL01 = Column(Text)
    MANUAL02 = Column(Text)
    MANUAL03 = Column(Text)
    MANUAL04 = Column(Text)
    MANUAL05 = Column(Text)
    MANUAL06 = Column(Text)
    MANUAL07 = Column(Text)
    MANUAL08 = Column(Text)
    MANUAL09 = Column(Text)
    MANUAL10 = Column(Text)
    MANUAL11 = Column(Text)
    MANUAL12 = Column(Text)
    MANUAL13 = Column(Text)
    MANUAL14 = Column(Text)
    MANUAL15 = Column(Text)
    MANUAL16 = Column(Text)
    MANUAL17 = Column(Text)
    MANUAL18 = Column(Text)
    MANUAL19 = Column(Text)
    MANUAL20 = Column(Text)

    MANUAL_IMG01 = Column(String(255))
    MANUAL_IMG02 = Column(String(255))
    MANUAL_IMG03 = Column(String(255))
    MANUAL_IMG04 = Column(String(255))
    MANUAL_IMG05 = Column(String(255))
    MANUAL_IMG06 = Column(String(255))
    MANUAL_IMG07 = Column(String(255))
    MANUAL_IMG08 = Column(String(255))
    MANUAL_IMG09 = Column(String(255))
    MANUAL_IMG10 = Column(String(255))
    MANUAL_IMG11 = Column(String(255))
    MANUAL_IMG12 = Column(String(255))
    MANUAL_IMG13 = Column(String(255))
    MANUAL_IMG14 = Column(String(255))
    MANUAL_IMG15 = Column(String(255))
    MANUAL_IMG16 = Column(String(255))
    MANUAL_IMG17 = Column(String(255))
    MANUAL_IMG18 = Column(String(255))
    MANUAL_IMG19 = Column(String(255))
    MANUAL_IMG20 = Column(String(255))

    category = Column(String(50))
    ingredients = Column(Text)

    INFO_ENG = Column(String(20))
    INFO_CAR = Column(String(20))
    INFO_PRO = Column(String(20))
    INFO_FAT = Column(String(20))
    INFO_NA = Column(String(20))

    RCP_NA_TIP = Column(Text)

    user = relationship("User", back_populates="user_recipes")
