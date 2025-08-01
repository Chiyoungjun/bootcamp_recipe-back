from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Recipe(Base):
    __tablename__ = 'recipes'
    id = Column(Integer, primary_key=True)  # 외부 API의 RCP_SEQ

    # 기본 정보
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(String(255))

    # 뷰/별점
    view_count = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3,2), default=0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ----------- 추가 필드 START -----------
    category      = Column("category", String(50))
    ingredients   = Column("ingredients", Text)
    INFO_ENG      = Column("INFO_ENG", String(20))
    INFO_CAR      = Column("INFO_CAR", String(20))
    INFO_PRO      = Column("INFO_PRO", String(20))
    INFO_FAT      = Column("INFO_FAT", String(20))
    INFO_NA       = Column("INFO_NA", String(20))
    RCP_NA_TIP    = Column("RCP_NA_TIP", Text)
    # ----------- 추가 필드 END -----------

    MANUAL01     = Column("MANUAL01", Text)
    MANUAL02     = Column("MANUAL02", Text)
    MANUAL03     = Column("MANUAL03", Text)
    MANUAL04     = Column("MANUAL04", Text)
    MANUAL05     = Column("MANUAL05", Text)
    MANUAL06     = Column("MANUAL06", Text)
    MANUAL07     = Column("MANUAL07", Text)
    MANUAL08     = Column("MANUAL08", Text)
    MANUAL09     = Column("MANUAL09", Text)
    MANUAL10     = Column("MANUAL10", Text)
    MANUAL11     = Column("MANUAL11", Text)
    MANUAL12     = Column("MANUAL12", Text)
    MANUAL13     = Column("MANUAL13", Text)
    MANUAL14     = Column("MANUAL14", Text)
    MANUAL15     = Column("MANUAL15", Text)
    MANUAL16     = Column("MANUAL16", Text)
    MANUAL17     = Column("MANUAL17", Text)
    MANUAL18     = Column("MANUAL18", Text)
    MANUAL19     = Column("MANUAL19", Text)
    MANUAL20     = Column("MANUAL20", Text)
    MANUAL_IMG01 = Column("MANUAL_IMG01", String(255))
    MANUAL_IMG02 = Column("MANUAL_IMG02", String(255))
    MANUAL_IMG03 = Column("MANUAL_IMG03", String(255))
    MANUAL_IMG04 = Column("MANUAL_IMG04", String(255))
    MANUAL_IMG05 = Column("MANUAL_IMG05", String(255))
    MANUAL_IMG06 = Column("MANUAL_IMG06", String(255))
    MANUAL_IMG07 = Column("MANUAL_IMG07", String(255))
    MANUAL_IMG08 = Column("MANUAL_IMG08", String(255))
    MANUAL_IMG09 = Column("MANUAL_IMG09", String(255))
    MANUAL_IMG10 = Column("MANUAL_IMG10", String(255))
    MANUAL_IMG11 = Column("MANUAL_IMG11", String(255))
    MANUAL_IMG12 = Column("MANUAL_IMG12", String(255))
    MANUAL_IMG13 = Column("MANUAL_IMG13", String(255))
    MANUAL_IMG14 = Column("MANUAL_IMG14", String(255))
    MANUAL_IMG15 = Column("MANUAL_IMG15", String(255))
    MANUAL_IMG16 = Column("MANUAL_IMG16", String(255))
    MANUAL_IMG17 = Column("MANUAL_IMG17", String(255))
    MANUAL_IMG18 = Column("MANUAL_IMG18", String(255))
    MANUAL_IMG19 = Column("MANUAL_IMG19", String(255))
    MANUAL_IMG20 = Column("MANUAL_IMG20", String(255))

    ratings = relationship("Rating", back_populates="recipe")

class Rating(Base):
    __tablename__ = 'ratings'
    id        = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    user_id   = Column(Integer, nullable=False)
    rating    = Column(Integer, nullable=False)
    created_at   = Column(DateTime, default=datetime.now)
    updated_at   = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    recipe   = relationship("Recipe", back_populates="ratings")

