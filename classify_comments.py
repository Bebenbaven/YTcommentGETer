import os
import re
import sys
import pandas as pd
import joblib

MODEL_PATH = os.path.join("models_youtube", "youtube_toxic_model.pkl")
VEC_PATH   = os.path.join("models_youtube", "youtube_tfidf_vectorizer.pkl")


def preprocess_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("\r", "\n")
    s = re.sub(r"\n+", " ", s)                    # 改行を1つの空白へ
    s = re.sub(r"http\S+|www\.\S+", "<URL>", s)  # URLを置換
    return s.strip()

def load_model_and_vectorizer():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"モデルが見つかりません: {MODEL_PATH}")
    if not os.path.exists(VEC_PATH):
        raise FileNotFoundError(f"ベクトライザが見つかりません: {VEC_PATH}")
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VEC_PATH)
    return model, vectorizer

def main():
    if len(sys.argv) < 2:
        print("使い方: python classify_comments.py <input_csv_path>")
        print("例: python classify_comments.py outputs/comments_with_replies_xxx.csv")
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print(f"入力CSVが見つかりません: {in_path}")
        sys.exit(1)

    df = pd.read_csv(in_path, encoding="utf-8-sig")

    if "text" not in df.columns:
        print("CSVに 'text' 列がありません。列名を確認してください。")
        sys.exit(1)

    model, vectorizer = load_model_and_vectorizer()

    texts = df["text"].fillna("").map(preprocess_text).tolist()
    X = vectorizer.transform(texts)
    empty = (X.getnnz(axis=1) == 0).sum()
    print(f"空ベクトル: {empty}/{X.shape[0]} 件（{empty/X.shape[0]*100:.1f}%）")
    print("平均特徴数:", X.getnnz(axis=1).mean())


    # ラベル
    y = model.predict(X)
    df["toxicity_label"] = y

    # スコア（取れれば入れる）
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        df["toxicity_score"] = proba[:, 1] if proba.shape[1] >= 2 else proba[:, 0]
    elif hasattr(model, "decision_function"):
        df["toxicity_score"] = model.decision_function(X)
    else:
        df["toxicity_score"] = ""

    base, ext = os.path.splitext(in_path)
    out_path = f"{base}_scored{ext}"
    df.to_csv(out_path, index=False, encoding="utf-8-sig")

    total = len(df)
    toxic = int((df["toxicity_label"] == 1).sum())
    print(f"出力: {out_path}")
    print(f"合計 {total} 件 / toxic=1 が {toxic} 件（{(toxic/total*100 if total else 0):.1f}%）")

if __name__ == "__main__":
    main()