from youtube_auth import get_service
import csv
from datetime import datetime

def get_comments(video_id, max_results=100):
    service = get_service()

    rows = []
    request = service.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText",
        order="time"  # 新しい順（必要なら "relevance"）
    )
    response = request.execute()

    for item in response.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        rows.append({
            "video_id": video_id,
            "comment_id": item["snippet"]["topLevelComment"]["id"],
            "author": snippet.get("authorDisplayName", ""),
            "published_at": snippet.get("publishedAt", ""),
            "like_count": snippet.get("likeCount", 0),
            "text": snippet.get("textDisplay", "")
        })

    return rows


def save_to_csv(rows, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video_id", "comment_id", "author", "published_at", "like_count", "text"]
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    video_id = "B2D3lGOrdVQ"  #動画ID
    rows = get_comments(video_id)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"comments_{video_id}_{ts}.csv"
    save_to_csv(rows, out_path)

    print(f"保存しました: {out_path}（{len(rows)}件）")
