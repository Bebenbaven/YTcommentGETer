from youtube_auth import get_service

def get_comments(video_id):
    service = get_service()

    comments = []
    request = service.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )
    response = request.execute()

    for item in response["items"]:
        top = item["snippet"]["topLevelComment"]["snippet"]
        comments.append(top["textDisplay"])

    return comments


if __name__ == "__main__":
    # テスト用の動画ID
    video_id = "B2D3lGOrdVQ"
    data = get_comments(video_id)

    print("=== コメント一覧 ===")
    for c in data:
        print(c)
