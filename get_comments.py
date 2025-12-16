from youtube_auth import get_service
import csv
from datetime import datetime

FIELDS = ["video_id", "comment_id", "author", "published_at", "like_count", "text"]

def fetch_all_comments(video_id, limit=None):
    service = get_service()

    rows = []
    page_token = None

    while True:
        req = service.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            order="time",
            pageToken=page_token
        )
        res = req.execute()

        for item in res.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            rows.append({
                "video_id": video_id,
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "author": snippet.get("authorDisplayName", ""),
                "published_at": snippet.get("publishedAt", ""),
                "like_count": snippet.get("likeCount", 0),
                "text": snippet.get("textDisplay", "")
            })
            if limit is not None and len(rows) >= limit:
                return rows

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return rows


def save_csv(rows, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    video_id = "BaW_jenozKc"  # ←ここを対象の動画IDに
    rows = fetch_all_comments(video_id)  # 例: limit=500 で上限つけてもOK

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"comments_all_{video_id}_{ts}.csv"
    save_csv(rows, out_path)

    print(f"保存しました: {out_path}（{len(rows)}件）")
