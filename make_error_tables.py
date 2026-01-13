import os
import pandas as pd
import joblib
import numpy as np

LABELED = "labeled_comments.csv"
MODEL = os.path.join("models_youtube", "youtube_toxic_model.pkl")
VEC   = os.path.join("models_youtube", "youtube_tfidf_vectorizer.pkl")

OUTDIR = os.path.join("tables")
TOPK = 8  # 表に載せる件数

def tex_escape(s: str) -> str:
    if not isinstance(s, str):
        s = ""
    # LaTeXの特殊文字を最低限エスケープ
    return (s.replace("\\", "\\textbackslash{}")
             .replace("&", "\\&")
             .replace("%", "\\%")
             .replace("$", "\\$")
             .replace("#", "\\#")
             .replace("_", "\\_")
             .replace("{", "\\{")
             .replace("}", "\\}")
             .replace("~", "\\textasciitilde{}")
             .replace("^", "\\textasciicircum{}"))

def truncate(s: str, n=60) -> str:
    s = s.strip().replace("\n", " ")
    return s if len(s) <= n else s[:n] + "..."

def to_latex_table(df, path):
    # 表本体だけ出す（\begin{tabular}... をここで生成）
    lines = []
    lines.append("\\begin{tabular}{r c c c l}")
    lines.append("\\hline")
    lines.append("No. & True & Pred & Score & Comment \\\\")
    lines.append("\\hline")
    for i, row in enumerate(df.itertuples(index=False), start=1):
        c = truncate(tex_escape(row.text), 70)
        lines.append(f"{i} & {row.true} & {row.pred} & {row.score:.3f} & {c} \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    df = pd.read_csv(LABELED, encoding="utf-8-sig")
    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(int)

    model = joblib.load(MODEL)
    vec = joblib.load(VEC)

    X = vec.transform(df["text"].values)

    # LinearSVC: decision_function がスコア（大きいほど有害側）
    if hasattr(model, "decision_function"):
        score = model.decision_function(X)
    else:
        # 念のため（確率モデルの場合）
        proba = model.predict_proba(X)[:, 1]
        score = proba

    pred = model.predict(X).astype(int)

    df2 = pd.DataFrame({
        "text": df["text"].values,
        "true": df["label"].values,
        "pred": pred,
        "score": score
    })

    # False Positive: true=0, pred=1（スコアが高い順）
    fp = df2[(df2.true == 0) & (df2.pred == 1)].sort_values("score", ascending=False).head(TOPK)

    # False Negative: true=1, pred=0（スコアが低い順＝有害側に寄れてない）
    fn = df2[(df2.true == 1) & (df2.pred == 0)].sort_values("score", ascending=True).head(TOPK)

    os.makedirs(OUTDIR, exist_ok=True)
    to_latex_table(fp, os.path.join(OUTDIR, "fp_examples.tex"))
    to_latex_table(fn, os.path.join(OUTDIR, "fn_examples.tex"))

    print("Generated:")
    print(" - tables/fp_examples.tex")
    print(" - tables/fn_examples.tex")
    print(f"FP={len(fp)}  FN={len(fn)}")

if __name__ == "__main__":
    main()
