# -*- coding: utf-8 -*-
"""
Macro9 ML Trainer (v2, safe, Korean fonts fixed + richer visuals)
- 입력: recipes_with_macro9_v2.csv (필수: macro9, 권장: id,name,way,category,ingredients,desc)
- 출력: z/<ts>_macro9_ml/
    - macro9_ml_model.joblib
    - cls_report.csv
    - confusion_matrix.csv/.png
    - confusion_matrix_norm.png
    - class_metrics.png
    - support_bar.png
    - flag_coeff_heatmap.png
    - sample_predictions.csv
    - run_meta.json (acc, macro_f1, top2_acc 등)
"""
from ai.feature_builder import FeatureBuilder

import os, json, argparse, warnings
from datetime import datetime
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

# ================== Matplotlib (headless + Korean font) ==================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import font_manager, rcParams

def _set_korean_font():
    installed = {f.name for f in font_manager.fontManager.ttflist}
    candidates = ["Malgun Gothic","AppleGothic","NanumGothic","Noto Sans KR","Noto Sans CJK KR"]
    chosen = None
    for name in candidates:
        if name in installed:
            chosen = name; break
    if chosen is None:
        for p in [r"C:\Windows\Fonts\malgun.ttf", r"C:\Windows\Fonts\malgunbd.ttf"]:
            if os.path.exists(p):
                try: font_manager.fontManager.addfont(p)
                except Exception: pass
        installed = {f.name for f in font_manager.fontManager.ttflist}
        if "Malgun Gothic" in installed: chosen = "Malgun Gothic"
    rcParams["font.family"] = chosen or "DejaVu Sans"
    rcParams["axes.unicode_minus"] = False
_set_korean_font()
# ========================================================================

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.utils import Bunch
from scipy.sparse import hstack, csr_matrix
import joblib

# 분리한 모듈에서 임포트
from ai.feature_builder import FeatureBuilder, clean, build_keyword_flags, flags_to_csr, zeros_csr

# --------------------- 설정 ---------------------
SEED = 42
TEST_SIZE = 0.2

MAXF_NAME_WORD = 5000
MAXF_NAME_CHAR = 6000
MAXF_ING_WORD  = 6000
MAXF_ING_CHAR  = 6000
MAXF_DESC_WORD = 6000
MAXF_DESC_CHAR = 6000

W_NAME = 0.50
W_ING  = 0.30
W_DESC = 0.20

# --------------------- 유틸 ---------------------
def nowdir(root="z", suffix="macro9_ml"):
    os.makedirs(root, exist_ok=True)
    d = os.path.join(root, datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + suffix)
    os.makedirs(d, exist_ok=True)
    return d

def detect_columns(cols):
    def pick(keys, default=""):
        for c in cols:
            cl = c.lower()
            if any(k in cl for k in keys): return c
        return default

    idc   = pick(["id"], "id")
    name  = pick(["name","rcp_nm","제목","메뉴"], "name")
    way   = pick(["way","method","조리","방법"], "way")
    cat   = pick(["category","cat","분류"], "category")
    ing   = pick(["ing","ingredient","재료","parts"], "")
    desc  = pick(["desc","설명","요약"], "")
    lab   = pick(["macro9"], "macro9")
    return idc, name, way, cat, ing, desc, lab

# --------------------- 시각화 함수 ---------------------
# (함수 정의들은 원본과 동일하게 이 파일에 모두 포함하세요)

def plot_class_metrics(report_dict, out_path):
    import matplotlib.pyplot as plt
    import pandas as pd; import seaborn as sns
    df = pd.DataFrame(report_dict).T
    df = df.drop(index=[i for i in df.index if i in ["accuracy","macro avg","weighted avg"]])
    df = df[["precision","recall","f1-score"]].astype(float)
    plt.figure(figsize=(max(8, 0.8*len(df)), 5))
    df.plot(kind="bar")
    plt.xticks(rotation=30, ha="right")
    plt.title("클래스별 Precision / Recall / F1")
    plt.ylabel("score")
    plt.ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(out_path, dpi=170)
    plt.close()

def plot_support_bar(report_dict, out_path):
    import matplotlib.pyplot as plt
    import pandas as pd; import seaborn as sns
    df = pd.DataFrame(report_dict).T
    df = df.drop(index=[i for i in df.index if i in ["accuracy","macro avg","weighted avg"]])
    sup = df["support"].astype(int)
    plt.figure(figsize=(max(8, 0.8*len(sup)), 4.5))
    sns.barplot(x=sup.index, y=sup.values, color="#4C78A8")
    plt.xticks(rotation=30, ha="right")
    plt.title("클래스별 샘플 개수 (support)")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(out_path, dpi=170)
    plt.close()

def plot_cm_norm(cm, labels, out_path):
    import matplotlib.pyplot as plt
    import seaborn as sns
    cmn = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    plt.figure(figsize=(10,7))
    sns.heatmap(cmn, annot=True, fmt=".2f", cmap="Blues",
                xticklabels=labels, yticklabels=labels, vmin=0, vmax=1)
    plt.title("Confusion Matrix (row-normalized)")
    plt.xlabel("Predicted"); plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(out_path, dpi=170)
    plt.close()

def slice_flag_coeff_heatmap(clf, fb):
    def vdim(v):
        return len(getattr(v, "vocabulary_", {}) or getattr(v, "get_feature_names_out", lambda:[])())
    name_dim = vdim(fb.tv_name_w) + vdim(fb.tv_name_c)
    ing_dim  = (vdim(fb.tv_ing_w)  + vdim(fb.tv_ing_c))  if fb.use_ing  else 0
    desc_dim = (vdim(fb.tv_desc_w) + vdim(fb.tv_desc_c)) if fb.use_desc else 0
    try:
        ohe_dim = fb.ohe.get_feature_names_out().shape[0]
    except Exception:
        try:
            ohe_dim = fb.ohe.get_feature_names().shape[0]
        except Exception:
            ohe_dim = sum(len(c) for c in getattr(fb.ohe, "categories_", []))
    flags_dim = len(fb.flag_names_ or [])
    start = name_dim + ing_dim + desc_dim + ohe_dim
    end   = start + flags_dim
    if flags_dim <= 0 or end > clf.coef_.shape[1]:
        return None, None
    return clf.coef_[:, start:end], fb.flag_names_

def plot_flag_coeff_heatmap(clf, fb, labels, out_path):
    import matplotlib.pyplot as plt
    import seaborn as sns
    coef_block, flag_names = slice_flag_coeff_heatmap(clf, fb)
    if coef_block is None:
        return
    plt.figure(figsize=(max(8, 0.6*len(flag_names)), 0.6*len(labels)+3))
    sns.heatmap(coef_block, annot=False, cmap="coolwarm", center=0,
                xticklabels=flag_names, yticklabels=labels)
    plt.xticks(rotation=30, ha="right")
    plt.title("로지스틱 회귀 계수 (규칙 플래그 has_*)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=170)
    plt.close()

# --------------------- 학습 파이프라인 ---------------------
def train(csv_path, seed=SEED, test_size=TEST_SIZE, out_root="z"):
    outdir = nowdir(out_root, "macro9_ml")
    print(f"[INFO] 결과 폴더: {outdir}")

    df = pd.read_csv(csv_path)
    id_col, name_col, way_col, cat_col, ing_col, desc_col, lab_col = detect_columns(df.columns)
    if lab_col == "" or lab_col not in df.columns:
        raise ValueError("CSV에 macro9 라벨 컬럼이 필요합니다.")

    for c in [id_col, name_col, way_col, cat_col, ing_col, desc_col, lab_col]:
        if c and c not in df.columns: df[c] = ""

    le = LabelEncoder()
    y = le.fit_transform(df[lab_col].astype(str))

    tr, te = train_test_split(df, test_size=test_size, random_state=seed, stratify=y)
    y_tr = le.transform(tr[lab_col].astype(str))
    y_te = le.transform(te[lab_col].astype(str))

    fb = FeatureBuilder().fit(tr, name_col, way_col, cat_col, ing_col, desc_col)
    print(f"[INFO] use_ing={fb.use_ing} / use_desc={fb.use_desc}")
    X_tr, flags_tr = fb.transform(tr)
    X_te, flags_te = fb.transform(te)

    clf = LogisticRegression(max_iter=2000, solver="saga", multi_class="multinomial",
                             class_weight="balanced", n_jobs=-1, C=3.0)
    clf.fit(X_tr, y_tr)

    y_pred  = clf.predict(X_te)
    y_proba = clf.predict_proba(X_te)
    acc = accuracy_score(y_te, y_pred)
    macro_f1 = f1_score(y_te, y_pred, average="macro")

    # Top-2 accuracy
    top2 = np.argsort(-y_proba, axis=1)[:, :2]
    top2_acc = float(np.mean([yt in top2[i] for i, yt in enumerate(y_te)]))

    print(f"[SCORE] acc={acc:.3f}  macro_f1={macro_f1:.3f}  top2_acc={top2_acc:.3f}")

    labels = list(le.classes_)

    # 리포트/혼동행렬
    report = classification_report(y_te, y_pred, target_names=labels, output_dict=True)
    pd.DataFrame(report).to_csv(os.path.join(outdir, "cls_report.csv"), encoding="utf-8-sig")

    cm = confusion_matrix(y_te, y_pred, labels=range(len(labels)))
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(
        os.path.join(outdir, "confusion_matrix.csv"), encoding="utf-8-sig"
    )
    # 혼동행렬(정수)
    plt.figure(figsize=(10,7))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels)
    plt.title("Confusion Matrix")
    plt.xlabel("Predicted"); plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "confusion_matrix.png"), dpi=170)
    plt.close()
    # 혼동행렬(정규화)
    plot_cm_norm(cm, labels, os.path.join(outdir, "confusion_matrix_norm.png"))

    # 클래스별 메트릭/서포트 그래프
    plot_class_metrics(report, os.path.join(outdir, "class_metrics.png"))
    plot_support_bar(report, os.path.join(outdir, "support_bar.png"))

    # 규칙 플래그 계수 열지도(설명력)
    plot_flag_coeff_heatmap(clf, fb, labels, os.path.join(outdir, "flag_coeff_heatmap.png"))

    # 샘플 예측 (Top-2 + 플래그)
    rows = []
    for i, (idx, p1, p2) in enumerate(zip(te.index, top2[:,0], top2[:,1])):
        row = te.loc[idx]
        rows.append({
            "id": row.get(id_col, idx),
            "name": row.get(name_col, ""),
            "true": row.get(lab_col, ""),
            "pred1": labels[p1], "proba1": float(y_proba[i, p1]),
            "pred2": labels[p2], "proba2": float(y_proba[i, p2]),
            **flags_te[i],
        })
    pd.DataFrame(rows).to_csv(os.path.join(outdir, "sample_predictions.csv"),
                             index=False, encoding="utf-8-sig")

    # 아티팩트 저장(모델+전처리+라벨러+열정보)
    artifact = Bunch(
        model=clf,
        feature_builder=fb,
        label_encoder=le,
        columns=dict(id=id_col, name=name_col, way=way_col,
                    category=cat_col, ingredients=ing_col, desc=desc_col, label=lab_col),
        config=dict(seed=seed, test_size=test_size,
                    weights=dict(name=W_NAME, ing=W_ING, desc=W_DESC)),
        classes=labels
    )
    joblib.dump(artifact, os.path.join(outdir, "macro9_ml_model.joblib"))

    with open(os.path.join(outdir, "run_meta.json"), "w", encoding="utf-8") as f:
        json.dump({
            "csv": os.path.basename(csv_path),
            "outdir": outdir, "n_rows": int(len(df)),
            "labels": labels, "acc": float(acc), "macro_f1": float(macro_f1),
            "top2_acc": float(top2_acc),
            "use_ing": bool(fb.use_ing), "use_desc": bool(fb.use_desc)
        }, f, ensure_ascii=False, indent=2)

    print("\n[DONE]")
    print(f"- 모델: {os.path.join(outdir, 'macro9_ml_model.joblib')}")
    print(f"- 리포트/혼동행렬: cls_report.csv / confusion_matrix.csv/.png / confusion_matrix_norm.png")
    print(f"- 그래프: class_metrics.png / support_bar.png / flag_coeff_heatmap.png")
    print(f"- 샘플예측: sample_predictions.csv")
    return outdir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="recipes_with_macro9_v2.csv 경로")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--test-size", type=float, default=TEST_SIZE)
    ap.add_argument("--outdir", default="z")
    args = ap.parse_args()
    train(args.csv, seed=args.seed, test_size=args.test_size, out_root=args.outdir)


if __name__ == "__main__":
    main()
