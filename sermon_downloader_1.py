#!/usr/bin/env python3
"""
Sermon Downloader
=================
Watches a YouTube playlist for new videos, downloads audio as MP3,
and saves it to your Google Drive folder for Make to pick up.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Missing yt-dlp. Run: pip3 install yt-dlp")
    sys.exit(1)

# ─── CONFIGURATION ───────────────────────────────────────────────────────────

PLAYLIST_ID   = "PLj27fIVHl5JHvhcHr__kGWYyYAeVqw2_p"
OUTPUT_FOLDER = "/Users/production-graphics/Google Drive Public/My Drive/AUDIO"
STATE_FILE    = str(Path.home() / "sermon_pipeline" / "seen_videos.json")

# ─────────────────────────────────────────────────────────────────────────────

def load_seen():
    p = Path(STATE_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        with open(p) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen), f, indent=2)

def get_playlist_videos():
    print(f"📋  Checking playlist for new videos...")
    url = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    videos = [
        {"id": e["id"], "title": e.get("title", "Untitled")}
        for e in info.get("entries", []) if e
    ]
    print(f"    Found {len(videos)} video(s) in playlist.")
    return videos

def download_audio(video_id, title):
    url = f"https://www.youtube.com/watch?v={video_id}"
    safe_title = "".join(c if c.isalnum() or c in " -_()" else "" for c in title).strip()
    output_template = str(Path(OUTPUT_FOLDER) / f"{safe_title}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
    }

    print(f"⬇️   Downloading: {title}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"✅  Saved: {safe_title}.mp3")

def mark_all_seen():
    """Mark all current playlist videos as seen without downloading."""
    print("\n" + "═"*50)
    print(f"  Marking all videos as seen (no download)")
    print("═"*50 + "\n")
    seen   = load_seen()
    videos = get_playlist_videos()
    new    = [v for v in videos if v["id"] not in seen]
    if not new:
        print("✅  All videos already marked as seen.\n")
        return
    for v in new:
        seen.add(v["id"])
        print(f"    Marked: {v['title']}")
    save_seen(seen)
    print(f"\n✅  {len(new)} video(s) marked as seen.")
    print("    From now on, only NEW videos added to the playlist will be downloaded.\n")

def run():
    print("\n" + "═"*50)
    print(f"  Sermon Downloader  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("═"*50 + "\n")

    Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

    seen   = load_seen()
    videos = get_playlist_videos()
    new    = [v for v in videos if v["id"] not in seen]

    if not new:
        print("✅  No new videos. Nothing to do.\n")
        return

    print(f"\n🆕  {len(new)} new video(s) to download.\n")

    for video in new:
        try:
            download_audio(video["id"], video["title"])
            seen.add(video["id"])
            save_seen(seen)
        except Exception as e:
            print(f"❌  Failed: {video['title']} — {e}")

    print(f"\n🎉  Done! Check your Google Drive AUDIO folder.\n")

if __name__ == "__main__":
    if "--mark-seen" in sys.argv:
        mark_all_seen()
    else:
        run()
