#!/usr/bin/env python3
"""
Multi-platform video downloader CLI (Bilibili, Douyin, TikTok, YouTube)
Requires: yt-dlp, ffmpeg (for merging & post-processing)
"""

import argparse
import sys
import os
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("[!] yt-dlp is not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


# ---------- Platform-specific option builders ----------
def build_ydl_opts(args) -> dict:
    """Construct yt-dlp options dictionary based on CLI arguments."""
    opts = {
        "outtmpl": os.path.join(args.output_dir, "%(title)s.%(ext)s"),
        "format": args.format,
        "merge_output_format": "mp4",
        "noplaylist": not args.playlist,
        "quiet": args.quiet,
        "no_warnings": args.quiet,
        "write_subs": args.write_subs,
        "write_auto_subs": args.write_auto_subs,
        "subtitleslangs": args.sub_langs.split(",") if args.sub_langs else ["en"],
        "writethumbnail": args.write_thumbnail,
        "embed_thumbnail": args.embed_thumbnail,
        "embed_metadata": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [],
    }

    # Audio extraction
    if args.audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"].append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": args.audio_format,
            "preferredquality": "192",
        })

    # Cookie handling (critical for Bilibili & YouTube high-res)
    if args.cookies_from_browser:
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)
    elif args.cookies_file:
        opts["cookiefile"] = args.cookies_file

    # Platform-specific overrides
    # Bilibili: sometimes requires referer
    # (yt-dlp handles most, but we can add headers if needed)
    if args.referer:
        opts["http_headers"] = {"Referer": args.referer}

    # Proxy
    if args.proxy:
        opts["proxy"] = args.proxy

    # Rate limit
    if args.rate_limit:
        opts["ratelimit"] = args.rate_limit

    return opts


def progress_hook(d):
    """Simple progress display."""
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "?").strip()
        speed = d.get("_speed_str", "?").strip()
        eta = d.get("_eta_str", "?").strip()
        print(f"\r[download] {pct} at {speed}, ETA {eta}", end="")
    elif d["status"] == "finished":
        print("\n[download] Finished, now post-processing...")


# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(
        description="Download videos from Bilibili, Douyin, TikTok, YouTube (and 1000+ other sites) via yt-dlp.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=xxxx"
  %(prog)s -o ./videos -f "bestvideo[height<=1080]+bestaudio/best" "https://www.bilibili.com/video/BVxxxx"
  %(prog)s --cookies-from-browser chrome "https://www.youtube.com/watch?v=xxxx"
  %(prog)s --audio-only --audio-format mp3 "https://www.tiktok.com/@user/video/xxxx"
  %(prog)s -a urls.txt
        """,
    )

    # Positional
    parser.add_argument("urls", nargs="*", help="One or more video URLs to download.")

    # Output
    parser.add_argument("-o", "--output-dir", default="./downloads", help="Output directory (default: ./downloads).")

    # Format / quality
    parser.add_argument("-f", "--format", default="bestvideo+bestaudio/best",
                        help="yt-dlp format selector (default: bestvideo+bestaudio/best).")
    parser.add_argument("--audio-only", action="store_true", help="Extract audio only.")
    parser.add_argument("--audio-format", default="mp3", help="Audio format when using --audio-only (default: mp3).")

    # Subtitles
    parser.add_argument("--write-subs", action="store_true", help="Write subtitles.")
    parser.add_argument("--write-auto-subs", action="store_true", help="Write auto-generated subtitles.")
    parser.add_argument("--sub-langs", default="en", help="Comma-separated subtitle languages (default: en).")

    # Thumbnail / metadata
    parser.add_argument("--write-thumbnail", action="store_true", help="Write thumbnail image.")
    parser.add_argument("--embed-thumbnail", action="store_true", help="Embed thumbnail in the video file.")

    # Playlist
    parser.add_argument("--playlist", action="store_true", help="Download entire playlist (default: single video only).")

    # Batch file
    parser.add_argument("-a", "--batch-file", help="File containing URLs (one per line).")

    # Cookies (critical for Bilibili & YouTube)
    cookie_group = parser.add_mutually_exclusive_group()
    cookie_group.add_argument("--cookies-from-browser", choices=["chrome", "firefox", "safari", "edge", "brave", "opera", "vivaldi"],
                              help="Load cookies directly from a browser profile.")
    cookie_group.add_argument("--cookies-file", help="Path to a Netscape-format cookies.txt file.")

    # Network
    parser.add_argument("--proxy", help="Proxy URL (e.g., socks5://127.0.0.1:1080).")
    parser.add_argument("--rate-limit", help="Max download rate (e.g., 5M for 5 MB/s).")
    parser.add_argument("--referer", help="Custom Referer header (useful for some Bilibili streams).")

    # Misc
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress yt-dlp output (except progress).")

    args = parser.parse_args()

    # Gather URLs
    urls = list(args.urls)
    if args.batch_file:
        try:
            with open(args.batch_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        urls.append(line)
        except FileNotFoundError:
            print(f"[!] Batch file not found: {args.batch_file}")
            sys.exit(1)

    if not urls:
        parser.print_help()
        print("\n[!] No URLs provided. Use positional arguments or -a batch file.")
        sys.exit(1)

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Build options
    ydl_opts = build_ydl_opts(args)

    # Download
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)
        print("\n[✓] All downloads completed successfully.")
    except yt_dlp.DownloadError as e:
        print(f"\n[!] Download error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()