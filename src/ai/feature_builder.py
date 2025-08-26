import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from scipy.sparse import csr_matrix, hstack

# ----- 유틸 함수 -----
def clean(s):
    if pd.isna(s): return ""
    s = str(s)
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\d+\.?\d*\s*(g|kg|mg|ml|l|컵|스푼|큰술|작은술|tsp|tbsp)", " ", s, flags=re.I)
    s = re.sub(r"[\/|·\+\*;]", ",", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def build_keyword_flags(name, desc, ing):
    text = " ".join([name, desc, ing])
    def has_any(words): return int(any(w in text for w in words))
    return {
        "has_soup":   has_any(["국","찌개","탕","스프","전골","수프"]),
        "has_rice":   has_any(["밥","죽","리조또","볶음밥","덮밥","비빔밥","주먹밥"]),
        "has_noodle": has_any(["면","파스타","국수","우동","라면","칼국수","소바","스파게티"]),
        "has_grill":  has_any(["구이","그릴","오븐","훈제","베이크","에어프라이어","카츠","돈가스"]),
        "has_stir":   has_any(["볶음","두루치기","잡채","볶다"]),
        "has_sweet":  has_any(["케이크","쿠키","타르트","머핀","브라우니","빵","라떼","주스","스무디","빙수","젤리",
                               "푸딩","초코","초콜릿","잼","시럽"]),
        "has_meat":   has_any(["닭","소고기","돼지","양고기","베이컨","소시지","목살","삼겹","갈비","불고기","다짐육"]),
        "has_sea":    has_any(["새우","오징어","문어","연어","참치","고등어","조개","홍합","전복","꽃게","쭈꾸미","낙지"]),
        "has_veg":    has_any(["두부","버섯","시금치","가지","브로콜리","콩나물","미역","김","채소","야채","토마토",
                               "오이","단호박","호박","감자","고구마","나물"]),
    }

def flags_to_csr(flags_list, flag_names=None):
    if flag_names is None:
        flag_names = sorted(list(flags_list[0].keys()))
    data = [[int(f[k]) for k in flag_names] for f in flags_list]
    return csr_matrix(np.asarray(data, dtype=np.float32)), flag_names

def zeros_csr(n_rows: int) -> csr_matrix:
    return csr_matrix((n_rows, 0), dtype=np.float32)

# ----- FeatureBuilder 클래스 -----
# TF-IDF 및 기타 수치 파라미터는 필요시 상단에서 따로 정의(지금은 하드코딩)
MAXF_NAME_WORD, MAXF_NAME_CHAR = 5000, 6000
MAXF_ING_WORD,  MAXF_ING_CHAR  = 6000, 6000
MAXF_DESC_WORD, MAXF_DESC_CHAR = 6000, 6000
W_NAME, W_ING, W_DESC = 0.50, 0.30, 0.20

class FeatureBuilder:
    """ingredients/desc가 비어있으면 자동 skip."""
    def __init__(self):
        self.tv_name_w = TfidfVectorizer(max_features=MAXF_NAME_WORD, ngram_range=(1,2),
                                         token_pattern=r"(?u)\b\w{2,}\b", min_df=2)
        self.tv_ing_w  = TfidfVectorizer(max_features=MAXF_ING_WORD,  ngram_range=(1,2),
                                         token_pattern=r"(?u)\b\w{2,}\b", min_df=2)
        self.tv_desc_w = TfidfVectorizer(max_features=MAXF_DESC_WORD, ngram_range=(1,2),
                                         token_pattern=r"(?u)\b\w{2,}\b", min_df=2)

        self.tv_name_c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4),
                                         min_df=2, max_features=MAXF_NAME_CHAR)
        self.tv_ing_c  = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4),
                                         min_df=2, max_features=MAXF_ING_CHAR)
        self.tv_desc_c = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4),
                                         min_df=2, max_features=MAXF_DESC_CHAR)

        try:
            self.ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=True)  # sklearn>=1.2
        except TypeError:
            self.ohe = OneHotEncoder(handle_unknown="ignore", sparse=True)         # 구버전 호환

        self.use_ing  = False
        self.use_desc = False
        self.flag_names_ = None
        self.columns_ = None

    def fit(self, df, name_col, way_col, cat_col, ing_col, desc_col):
        names = df[name_col].fillna("").map(clean)
        self.use_ing  = bool(ing_col)  and df[ing_col].astype(str).str.strip().ne("").any()
        self.use_desc = bool(desc_col) and df[desc_col].astype(str).str.strip().ne("").any()

        ings  = df[ing_col].fillna("").map(clean)  if self.use_ing  else pd.Series([""]*len(df))
        descs = df[desc_col].fillna("").map(clean) if self.use_desc else pd.Series([""]*len(df))

        self.tv_name_w.fit(names); self.tv_name_c.fit(names)
        if self.use_ing:
            self.tv_ing_w.fit(ings);  self.tv_ing_c.fit(ings)
        if self.use_desc:
            self.tv_desc_w.fit(descs); self.tv_desc_c.fit(descs)

        ohe_df = pd.DataFrame({
            "way": df[way_col].fillna("").astype(str) if way_col else "",
            "category": df[cat_col].fillna("").astype(str) if cat_col else ""
        })
        self.ohe.fit(ohe_df)

        flags = [build_keyword_flags(n, d, i) for n, d, i in zip(names, descs, ings)]
        _, self.flag_names_ = flags_to_csr(flags)
        self.columns_ = dict(name=name_col, way=way_col, category=cat_col, ing=ing_col, desc=desc_col)
        return self

    def transform(self, df):
        name_col, way_col, cat_col, ing_col, desc_col = (
            self.columns_["name"], self.columns_["way"], self.columns_["category"],
            self.columns_["ing"], self.columns_["desc"]
        )
        n = len(df)
        names = df[name_col].fillna("").map(clean)
        ings  = df[ing_col].fillna("").map(clean)  if self.use_ing  else pd.Series([""]*n)
        descs = df[desc_col].fillna("").map(clean) if self.use_desc else pd.Series([""]*n)

        Xn = hstack([ self.tv_name_w.transform(names), self.tv_name_c.transform(names) ]) * W_NAME
        Xi = (hstack([ self.tv_ing_w.transform(ings),  self.tv_ing_c.transform(ings) ]) * W_ING) if self.use_ing else zeros_csr(n)
        Xd = (hstack([ self.tv_desc_w.transform(descs), self.tv_desc_c.transform(descs)]) * W_DESC) if self.use_desc else zeros_csr(n)

        ohe_df = pd.DataFrame({
            "way": df[way_col].fillna("").astype(str) if way_col else "",
            "category": df[cat_col].fillna("").astype(str) if cat_col else ""
        })
        XO = self.ohe.transform(ohe_df)

        flags = [build_keyword_flags(n, d, i) for n, d, i in zip(names, descs, ings)]
        XF, _ = flags_to_csr(flags, self.flag_names_)

        return hstack([Xn, Xi, Xd, XO, XF]).tocsr(), flags
