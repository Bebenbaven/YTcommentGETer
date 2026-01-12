import os
import re
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, confusion_matrix

DATA_PATH = "labeled_comments.csv"
OUT_DIR = "models_youtube"
RANDOM_STATE = 42

def preprocess(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.replace("\r", "\n")
    s = re.sub(r"\n+", " ", s)
    s = re.sub(r"http\S+|www\.\S+", "<URL>", s)
    return s.strip()

def main():
    df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")

    # 必須列チェック
    for col in ["text", "label"]:
        if col not in df.columns:
            raise ValueError(f"CSVに '{col}' 列がありません")

    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str).map(preprocess)
    df["label"] = df["label"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df["label"]
    )

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        min_df=2,
        max_df=0.95
    )

    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LinearSVC(class_weight="balanced")
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)

    print("=== classification_report ===")
    print(classification_report(y_test, y_pred, digits=3))
    print("=== confusion_matrix ===")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(OUT_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(OUT_DIR, "youtube_toxic_model.pkl"))
    joblib.dump(vectorizer, os.path.join(OUT_DIR, "youtube_tfidf_vectorizer.pkl"))

    print("モデル保存完了:")
    print(f" - {OUT_DIR}/youtube_toxic_model.pkl")
    print(f" - {OUT_DIR}/youtube_tfidf_vectorizer.pkl")

if __name__ == "__main__":
    main()
