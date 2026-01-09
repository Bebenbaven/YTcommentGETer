from youtube_auth import get_service
import csv
from datetime import datetime
import os

OUTPUT_DIR = "outputs"

FIELDS = [
    "video_id",
    "comment_id",
    "parent_id",
    "thread_id",
    "is_reply",
    "author",
    "published_at",
    "updated_at",
    "like_count",
    "text",
    "toxicity_label",
    "toxicity_score",
]

def fetch_all_threads_with_replies(video_id, limit=None, order="time"):
    """
    トップコメント + 返信コメント（リプライ）を全取得して、1つのリストにまとめて返す。
    limit: Noneなら全件、数値ならその件数で打ち切り（トップ+返信の合計件数）
    order: "time" or "relevance"
    """
    service = get_service()
    rows = []
    page_token = None

    while True:
        # 1) コメントスレッド（トップコメント）をページングで取得
        req = service.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            order=order,
            pageToken=page_token,
        )
        res = req.execute()

        for thread in res.get("items", []):
            top = thread["snippet"]["topLevelComment"]
            top_s = top["snippet"]
            thread_id = top["id"]  # スレッドIDはトップコメントIDに統一

            # --- トップコメント行 ---
            rows.append({
                "video_id": video_id,
                "comment_id": top["id"],
                "parent_id": "",
                "thread_id": thread_id,
                "is_reply": 0,
                "author": top_s.get("authorDisplayName", ""),
                "published_at": top_s.get("publishedAt", ""),
                "updated_at": top_s.get("updatedAt", ""),
                "like_count": top_s.get("likeCount", 0),
                "text": top_s.get("textDisplay", ""),
                "toxicity_label": "",
                "toxicity_score": "",
            })
            if limit is not None and len(rows) >= limit:
                return rows

            # 2) replies が付いてきた分を追加（最大5件くらいまでしか付かないことが多い）
            replies = thread.get("replies", {}).get("comments", [])
            for rep in replies:
                rep_s = rep["snippet"]
                rows.append({
                    "video_id": video_id,
                    "comment_id": rep["id"],
                    "parent_id": rep_s.get("parentId", thread_id) or thread_id,
                    "thread_id": thread_id,
                    "is_reply": 1,
                    "author": rep_s.get("authorDisplayName", ""),
                    "published_at": rep_s.get("publishedAt", ""),
                    "updated_at": rep_s.get("updatedAt", ""),
                    "like_count": rep_s.get("likeCount", 0),
                    "text": rep_s.get("textDisplay", ""),
                    "toxicity_label": "",
                    "toxicity_score": "",
                })
                if limit is not None and len(rows) >= limit:
                    return rows

            # 3) 返信総数が多いスレッドは、comments.list で残りを追加取得
            total_reply_count = thread["snippet"].get("totalReplyCount", 0)
            if total_reply_count > len(replies):
                rows.extend(fetch_remaining_replies(service, parent_id=thread_id, video_id=video_id, thread_id=thread_id, limit=limit, current_count=len(rows)))
                if limit is not None and len(rows) >= limit:
                    return rows[:limit]

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return rows


def fetch_remaining_replies(service, parent_id, video_id, thread_id, limit=None, current_count=0):
    """
    comments.list(parentId=...) で、スレッドの返信コメントをページング取得。
    注意：commentThreads の replies に入ってきた分と重複する可能性があるので、
          呼び出し側で「repliesに入ってた分より多い場合」だけ呼ぶ想定。
    """
    out = []
    page_token = None

    while True:
        req = service.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=page_token,
        )
        res = req.execute()

        for rep in res.get("items", []):
            rep_s = rep["snippet"]
            out.append({
                "video_id": video_id,
                "comment_id": rep["id"],
                "parent_id": rep_s.get("parentId", parent_id) or parent_id,
                "thread_id": thread_id,
                "is_reply": 1,
                "author": rep_s.get("authorDisplayName", ""),
                "published_at": rep_s.get("publishedAt", ""),
                "updated_at": rep_s.get("updatedAt", ""),
                "like_count": rep_s.get("likeCount", 0),
                "text": rep_s.get("textDisplay", ""),
                "toxicity_label": "",
                "toxicity_score": "",
            })

            if limit is not None and (current_count + len(out)) >= limit:
                return out[: max(0, limit - current_count)]

        page_token = res.get("nextPageToken")
        if not page_token:
            break

    return out


def dedupe_rows(rows):
    """comment_id で重複除去（thread.replies と comments.list が重なる場合に備える）"""
    seen = set()
    uniq = []
    for r in rows:
        cid = r["comment_id"]
        if cid in seen:
            continue
        seen.add(cid)
        uniq.append(r)
    return uniq


def save_csv(rows, out_path):
    # Excelで文字化けしない UTF-8 with BOM
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    import argparse
    import os
    from datetime import datetime

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--video-ids", nargs="*", default=None,
                        help="動画IDをスペース区切りで複数指定（例: --video-ids id1 id2 id3）")
    parser.add_argument("--outdir", default="outputs")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # 動画IDの受け取り：引数があればそれ、なければ対話入力（複数行）
    if args.video_ids and len(args.video_ids) > 0:
        video_ids = [v.strip() for v in args.video_ids if v.strip()]
    else:
        print("取得したいYouTube動画IDを入力してください（1行=1ID）。終わったら空行で確定：")
        video_ids = []
        while True:
            v = input().strip()
            if not v:
                break
            video_ids.append(v)

    if not video_ids:
        print("動画IDが入力されていません。終了します。")
        raise SystemExit(1)

    for i, video_id in enumerate(video_ids, start=1):
        print(f"\n[{i}/{len(video_ids)}] 取得開始: {video_id} (limit={args.limit})")

        rows = fetch_all_threads_with_replies(video_id, limit=args.limit)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        limit_tag = f"limit{args.limit}" if args.limit is not None else "all"
        out_path = os.path.join(
            args.outdir,
            f"comments_with_replies_{video_id}_{limit_tag}_{ts}.csv"
        )
        save_csv(rows, out_path)

        top_count = sum(1 for r in rows if r["is_reply"] == 0)
        rep_count = sum(1 for r in rows if r["is_reply"] == 1)

        print(f"保存しました: {out_path}")
        print(f"トップ: {top_count} / 返信: {rep_count} / 合計: {len(rows)}")

    print("\n!!!!!完了!!!!!")
