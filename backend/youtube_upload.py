"""
JETBOX v3 â€” YouTube Direct Upload Module
Replaces n8n. Uses google-api-python-client + OAuth2.
Resumable upload with progress tracking, retry logic.

First-time setup:
    1. Go to console.cloud.google.com
    2. Create project, enable YouTube Data API v3
    3. Create OAuth2 credentials (Desktop app)
    4. Download client_secrets.json into JETBOX root
    5. Run: python youtube_upload.py --setup
       (opens browser for one-time Google auth)
"""

import os
import sys
import json
import time
import random
import http.client
import httplib2
from datetime import datetime

# Google API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


# â”€â”€â”€ CONSTANTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

YOUTUBE_API_SERVICE = "youtube"
YOUTUBE_API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtube.readonly"]

# Retry config
MAX_RETRIES = 5
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError,
                        http.client.NotConnected, http.client.IncompleteRead,
                        http.client.ImproperConnectionState, http.client.CannotSendRequest,
                        http.client.CannotSendHeader, http.client.ResponseNotReady,
                        http.client.BadStatusLine)

# Paths (relative to project root)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRETS_FILE = os.path.join(PROJECT_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(PROJECT_DIR, "youtube_token.json")


# â”€â”€â”€ AUTH â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def check_dependencies() -> dict:
    """Check if required packages are installed."""
    return {
        "google_api_available": GOOGLE_API_AVAILABLE,
        "client_secrets_exists": os.path.exists(CLIENT_SECRETS_FILE),
        "token_exists": os.path.exists(TOKEN_FILE),
        "install_command": "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
    }


def authenticate(force_new: bool = False) -> object:
    """
    Authenticate with YouTube API using OAuth2.
    
    First run: Opens browser for Google sign-in. Saves token to youtube_token.json.
    Subsequent runs: Uses saved token, auto-refreshes if expired.
    
    Returns:
        YouTube API service object, or None if auth fails.
    """
    if not GOOGLE_API_AVAILABLE:
        raise ImportError(
            "Google API libraries not installed. Run:\n"
            "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
    
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise FileNotFoundError(
            f"client_secrets.json not found at: {CLIENT_SECRETS_FILE}\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials"
        )
    
    credentials = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE) and not force_new:
        try:
            credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            credentials = None
    
    # Refresh or get new credentials
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except Exception:
            credentials = None
    
    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        credentials = flow.run_local_server(
            port=0,
            prompt="consent",
            success_message="JETBOX: YouTube auth complete! You can close this tab."
        )
        
        # Save token for future use
        with open(TOKEN_FILE, 'w') as f:
            f.write(credentials.to_json())
        print(f"âœ… Token saved to {TOKEN_FILE}")
    
    # Build YouTube service
    youtube = build(YOUTUBE_API_SERVICE, YOUTUBE_API_VERSION, credentials=credentials)
    return youtube


def revoke_auth() -> dict:
    """Kayıtlı token'ı siler (arayüzden 'Disconnect')."""
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
            return {"success": True, "removed": True}
        except OSError as e:
            return {"success": False, "error": str(e)}
    return {"success": True, "removed": False}


def get_auth_status() -> dict:
    """Check current authentication status without triggering auth flow."""
    status = {
        "dependencies_installed": GOOGLE_API_AVAILABLE,
        "client_secrets_exists": os.path.exists(CLIENT_SECRETS_FILE),
        "token_exists": os.path.exists(TOKEN_FILE),
        "authenticated": False,
        "needs_setup": True,
    }
    
    if not GOOGLE_API_AVAILABLE or not os.path.exists(CLIENT_SECRETS_FILE):
        return status
    
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and (creds.valid or creds.refresh_token):
                status["authenticated"] = True
                status["needs_setup"] = False
                if creds.expiry:
                    status["token_expiry"] = creds.expiry.isoformat()
        except Exception:
            pass
    
    return status


# â”€â”€â”€ UPLOAD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def upload_video(
    mp4_path: str,
    title: str,
    description: str,
    tags: list,
    category_id: str = "10",
    privacy_status: str = "public",
    thumbnail_path: str = None,
    on_progress: callable = None,
    publish_at: str = None,
    default_language: str = "en",
) -> dict:
    """
    Upload a video to YouTube with resumable upload + retry logic.
    
    Args:
        mp4_path: Path to MP4 file
        title: Video title
        description: Video description
        tags: List of tags
        category_id: YouTube category (10 = Music)
        privacy_status: public / private / unlisted
        thumbnail_path: Optional thumbnail JPG path
        on_progress: Optional callback(percent) for progress updates
    
    Returns:
        dict with video_id, url, and upload details
    """
    if not os.path.exists(mp4_path):
        return {"success": False, "error": f"MP4 not found: {mp4_path}"}
    
    # Authenticate
    try:
        youtube = authenticate()
    except Exception as e:
        return {"success": False, "error": f"Auth failed: {str(e)}"}
    
    status_block = {
        "privacyStatus": privacy_status,
        "embeddable": True,
        "publicStatsViewable": True,
        "selfDeclaredMadeForKids": False,
    }

    if publish_at:
        status_block["publishAt"] = publish_at
        status_block["privacyStatus"] = "private" # API Requirement for scheduling
    
    # Build video resource
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags if isinstance(tags, list) else json.loads(tags),
            "categoryId": category_id,
            "defaultLanguage": default_language or "en",
        },
        "status": status_block,
    }
    
    # Create upload request
    media = MediaFileUpload(
        mp4_path,
        mimetype="video/quicktime" if mp4_path.lower().endswith(".mov") else "video/mp4",
        chunksize=10 * 1024 * 1024,  # 10MB chunks
        resumable=True
    )
    
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    # Execute with retry
    response = None
    error = None
    retry = 0
    start_time = time.time()
    
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            
            if status and on_progress:
                percent = int(status.progress() * 100)
                on_progress(percent)
            
            if status:
                print(f"  â³ Upload progress: {int(status.progress() * 100)}%")
                
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: retryable error"
            else:
                return {
                    "success": False,
                    "error": f"YouTube API error {e.resp.status}: {e.content.decode()[:300]}"
                }
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retryable error: {str(e)}"
        
        if error:
            retry += 1
            if retry > MAX_RETRIES:
                return {"success": False, "error": f"Max retries exceeded. Last error: {error}"}
            
            sleep_time = random.random() * (2 ** retry)
            print(f"  âš ï¸ {error}. Retrying in {sleep_time:.1f}s... (attempt {retry}/{MAX_RETRIES})")
            time.sleep(sleep_time)
            error = None
    
    elapsed = time.time() - start_time
    video_id = response.get("id", "")
    video_url = f"https://youtube.com/watch?v={video_id}"
    
    result = {
        "success": True,
        "video_id": video_id,
        "video_url": video_url,
        "title": response.get("snippet", {}).get("title", title),
        "privacy": privacy_status,
        "upload_time_seconds": round(elapsed, 1),
        "uploaded_at": datetime.now().isoformat(),
    }
    
    # Set thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path) and video_id:
        try:
            thumb_result = youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            result["thumbnail_set"] = True
        except HttpError as e:
            # Thumbnail upload requires channel verification â€” common failure
            result["thumbnail_set"] = False
            result["thumbnail_note"] = "Custom thumbnails require YouTube channel verification"
    
    return result


# â”€â”€â”€ PLAYLISTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_playlists() -> dict:
    """
    Fetch all playlists from the authenticated YouTube channel.
    Returns list of {id, title, item_count, privacy} dicts.
    """
    if not GOOGLE_API_AVAILABLE:
        return {"success": False, "error": "Google API not available", "playlists": []}
    try:
        youtube = authenticate()
        playlists = []
        next_page = None
        while True:
            kwargs = dict(part="snippet,contentDetails,status", mine=True, maxResults=50)
            if next_page:
                kwargs["pageToken"] = next_page
            response = youtube.playlists().list(**kwargs).execute()
            for item in response.get("items", []):
                playlists.append({
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "item_count": item["contentDetails"]["itemCount"],
                    "privacy": item["status"]["privacyStatus"],
                    "thumbnail": (item["snippet"].get("thumbnails", {}).get("default", {}).get("url", "")),
                })
            next_page = response.get("nextPageToken")
            if not next_page:
                break
        return {"success": True, "playlists": playlists, "count": len(playlists)}
    except Exception as e:
        return {"success": False, "error": str(e), "playlists": []}


def add_video_to_playlist(video_id: str, playlist_id: str) -> dict:
    """
    Add an already-uploaded video to a YouTube playlist.
    Call this AFTER upload_video returns a video_id.
    """
    if not GOOGLE_API_AVAILABLE:
        return {"success": False, "error": "Google API not available"}
    try:
        youtube = authenticate()
        response = youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            }
        ).execute()
        return {
            "success": True,
            "playlist_item_id": response.get("id"),
            "video_id": video_id,
            "playlist_id": playlist_id,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_channel_info() -> dict:
    """Get basic info about the authenticated YouTube channel."""
    try:
        youtube = authenticate()
        request = youtube.channels().list(part="snippet,statistics", mine=True)
        response = request.execute()
        
        if response.get("items"):
            channel = response["items"][0]
            return {
                "success": True,
                "channel_id": channel["id"],
                "title": channel["snippet"]["title"],
                "subscriber_count": channel["statistics"].get("subscriberCount", "hidden"),
                "video_count": channel["statistics"].get("videoCount", "0"),
            }
        return {"success": False, "error": "No channel found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_channel_videos(max_results: int = 50) -> dict:
    """
    KanalÄ±n videolarÄ±nÄ± istatistiklerle birlikte getirir.
    Her video iÃ§in: id, title, thumbnail (maxres), viewCount,
    likeCount, commentCount, publishedAt dÃ¶ndÃ¼rÃ¼r.
    Performans skoru: view Ã- 0.5 + like Ã- 0.3 + comment Ã- 0.2 (normalize)
    """
    try:
        youtube = authenticate()

        # 1) Channel'in uploads playlist ID'sini al
        ch = youtube.channels().list(part="contentDetails", mine=True).execute()
        if not ch.get("items"):
            return {"success": False, "error": "No channel found"}
        uploads_id = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # 2) Playlist'teki videolarÄ± getir
        videos = []
        next_page = None
        while len(videos) < max_results:
            pl_req = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_id,
                maxResults=min(50, max_results - len(videos)),
                pageToken=next_page
            ).execute()
            for item in pl_req.get("items", []):
                vid_id = item["snippet"]["resourceId"]["videoId"]
                thumb  = item["snippet"].get("thumbnails", {})
                # En yÃ¼ksek kaliteli thumbnail
                thumb_url = (
                    thumb.get("maxres", {}).get("url") or
                    thumb.get("standard", {}).get("url") or
                    thumb.get("high", {}).get("url") or
                    thumb.get("medium", {}).get("url") or ""
                )
                videos.append({
                    "video_id": vid_id,
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                    "thumbnail_url": thumb_url,
                })
            next_page = pl_req.get("nextPageToken")
            if not next_page:
                break

        if not videos:
            return {"success": True, "videos": []}

        # 3) Ä°statistiklerÄ± al (50'lik batch'ler)
        stats_map = {}
        ids_all = [v["video_id"] for v in videos]
        for i in range(0, len(ids_all), 50):
            batch = ids_all[i:i+50]
            st = youtube.videos().list(
                part="statistics",
                id=",".join(batch)
            ).execute()
            for item in st.get("items", []):
                s = item.get("statistics", {})
                stats_map[item["id"]] = {
                    "view_count":    int(s.get("viewCount",    0)),
                    "like_count":    int(s.get("likeCount",    0)),
                    "comment_count": int(s.get("commentCount", 0)),
                }

        # 4) Skoru hesapla ve sÄ±rala
        for v in videos:
            s = stats_map.get(v["video_id"], {})
            views    = s.get("view_count",    0)
            likes    = s.get("like_count",    0)
            comments = s.get("comment_count", 0)
            v["view_count"]    = views
            v["like_count"]    = likes
            v["comment_count"] = comments
            # Ham skor (normalize ileride yapÄ±lacak)
            v["raw_score"] = views * 0.5 + likes * 300 + comments * 150

        # Normalize 0-100
        max_score = max((v["raw_score"] for v in videos), default=1) or 1
        for v in videos:
            v["sales_score"] = round((v["raw_score"] / max_score) * 100, 1)
            del v["raw_score"]

        videos.sort(key=lambda x: x["sales_score"], reverse=True)
        return {"success": True, "videos": videos, "total": len(videos)}

    except Exception as e:
        return {"success": False, "error": str(e)}


# â”€â”€â”€ CLI INTERFACE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def setup_wizard():
    """Interactive setup wizard for first-time configuration."""
    print()
    print("=" * 55)
    print("  ğŸ” JETBOX v3 â€” YouTube API Setup Wizard")
    print("=" * 55)
    print()
    
    deps = check_dependencies()
    
    # Step 1: Check dependencies
    if not deps["google_api_available"]:
        print("âŒ Google API libraries not installed.")
        print(f"   Run: {deps['install_command']}")
        return
    print("âœ… Google API libraries installed")
    
    # Step 2: Check client_secrets.json
    if not deps["client_secrets_exists"]:
        print()
        print("âŒ client_secrets.json not found!")
        print()
        print("   Follow these steps:")
        print("   1. Open: https://console.cloud.google.com")
        print("   2. Create a new project (or select existing)")
        print("   3. Go to: APIs & Services → Library")
        print("   4. Search 'YouTube Data API v3' → Enable it")
        print("   5. Go to: APIs & Services → Credentials")
        print("   6. Click '+ CREATE CREDENTIALS' → 'OAuth client ID'")
        print("   7. Application type: 'Desktop app'")
        print("   8. Name it: 'JETBOX'")
        print("   9. Click 'Download JSON' (â¬‡ï¸ icon)")
        print(f"  10. Save as: {CLIENT_SECRETS_FILE}")
        print()
        print("   Then run this setup again!")
        return
    print("âœ… client_secrets.json found")
    
    # Step 3: Authenticate
    print()
    print("ğŸŒ Opening browser for Google sign-in...")
    print("   (Sign in with the Google account that owns your YouTube channel)")
    print()
    
    try:
        youtube = authenticate(force_new=True)
        print()
        print("âœ… Authentication successful!")
        
        # Verify channel access
        info = get_channel_info()
        if info.get("success"):
            print(f"   Channel: {info['title']}")
            print(f"   Videos: {info['video_count']}")
            print(f"   Subscribers: {info['subscriber_count']}")
        
        print()
        print("=" * 55)
        print("  ğŸ‰ Setup complete! JETBOX can now upload to YouTube.")
        print("=" * 55)
        
    except Exception as e:
        print(f"âŒ Authentication failed: {e}")


if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_wizard()
    elif "--status" in sys.argv:
        status = get_auth_status()
        for k, v in status.items():
            print(f"  {k}: {v}")
    elif "--channel" in sys.argv:
        info = get_channel_info()
        for k, v in info.items():
            print(f"  {k}: {v}")
    else:
        print("JETBOX v3 â€” YouTube Upload Module")
        print()
        print("Commands:")
        print("  python youtube_upload.py --setup    First-time auth setup")
        print("  python youtube_upload.py --status   Check auth status")
        print("  python youtube_upload.py --channel  Show channel info")

