"""
JETBOX v3 â€” Flask API Backend
React frontend + Flask API architecture
Endpoints for beats, artists, artworks, LUT processing, rendering, upload
"""

from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
import os
import io
import json
import time
import requests
from datetime import datetime, timedelta

from lut_engine import (
    process_artwork, get_available_presets, list_artworks, LUT_PRESETS,
    apply_lut_only
)
from lut_tuner import (
    load_custom_presets,
    save_custom_presets,
    MAX_CUSTOM_PRESETS,
    process_full as lut_process_full,
    apply_master_blend,
)
from mp4_render import render_mp4, render_mp4_with_effects, check_ffmpeg, get_audio_duration
from video_effects import get_effects_list, get_effect_timeline
from seo_engine import (
    get_all_artists, get_artists_by_tier, search_artists,
    generate_title, generate_publish_package,
)
from file_watcher import BeatWatcher
from youtube_upload import (
    upload_video, get_auth_status, get_channel_info,
    setup_wizard, check_dependencies, GOOGLE_API_AVAILABLE,
    get_playlists, add_video_to_playlist, get_channel_videos,
)
from plugins.visual_processor import apply_fisheye, fisheye_from_url, save_fisheye

# â”€â”€â”€ CONFIG â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# These directories should exist at project root
BEATS_DIR = os.path.join(PROJECT_DIR, "BEATS")
ARTWORKS_DIR = os.path.join(PROJECT_DIR, "ARTWORKS")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "OUTPUT")
CONFIG_PATH = os.path.join(PROJECT_DIR, "config.json")

# Create directories if not exist
for d in [BEATS_DIR, ARTWORKS_DIR, OUTPUT_DIR,
          os.path.join(ARTWORKS_DIR, "RAGE"),
          os.path.join(ARTWORKS_DIR, "MELODIC")]:
    os.makedirs(d, exist_ok=True)

# â”€â”€â”€ APP INIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

app = Flask(__name__)
CORS(app)  # Allow React frontend requests

# Initialize file watcher
watcher = BeatWatcher(BEATS_DIR)
watcher.start()
# Load existing WAV files into pending queue on startup
watcher.add_existing_as_pending()


def load_config() -> dict:
    """Load config.json or return defaults."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {
        "n8n_webhook_url": "",
        "youtube_region": "US",
        "youtube_category": "10",
        "channel_name": "ENNY TANG",
        "channel_handle": "@enny-tang",
        "contact_email": "",
        "social_links": [],
        "default_license": (
            "FREE FOR NON-PROFIT USE â€” credit the producer in the title or description. "
            "Commercial use requires a lease."
        ),
        "lease_url": "",
        "default_language": "en",
        "producer_credit": "ENNY TANG",
    }


def get_seo_channel_config() -> dict:
    """Subset of config.json passed into SEO / publish package generation."""
    c = load_config()
    keys = (
        "channel_name", "channel_handle", "contact_email", "social_links",
        "default_license", "lease_url", "default_language", "producer_credit",
        "youtube_region", "youtube_category",
    )
    return {k: c[k] for k in keys if k in c}


# ═══════════════════════════════════════════════════════════════
# HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    ffmpeg = check_ffmpeg()
    yt_status = get_auth_status()
    return jsonify({
        "status": "ok",
        "version": "3.1.0",
        "ffmpeg": ffmpeg,
        "youtube": yt_status,
        "watcher_running": watcher._running,
        "beats_dir": BEATS_DIR,
        "artworks_dir": ARTWORKS_DIR,
        "output_dir": OUTPUT_DIR,
        "timestamp": datetime.now().isoformat()
    })


# ═══════════════════════════════════════════════════════════════
# BEATS â€” File watcher endpoints
# ═══════════════════════════════════════════════════════════════

@app.route('/api/beats', methods=['GET'])
def get_beats():
    """Get all beats as a flat list â€” frontend expects {beats:[...]}."""
    data = watcher.get_all_beats()
    # Combine pending + processed into single list, pending first
    all_beats = data.get("pending", []) + data.get("processed", [])
    return jsonify({
        "beats": all_beats,
        "watching": data.get("watching"),
        "is_running": data.get("is_running"),
        "total": len(all_beats),
    })


@app.route('/api/beats/pending', methods=['GET'])
def get_pending_beats():
    """Get only pending beats."""
    return jsonify({"beats": watcher.get_pending()})


@app.route('/api/beats/scan', methods=['POST'])
def scan_beats():
    """Manually trigger scan and add existing files as pending."""
    count = watcher.add_existing_as_pending()
    return jsonify({"added": count, "pending": watcher.get_pending()})


@app.route('/api/beats/<beat_id>', methods=['GET'])
def get_beat(beat_id):
    """Get specific beat by ID."""
    beat = watcher.get_beat_by_id(beat_id)
    if not beat:
        return jsonify({"error": "Beat not found"}), 404
    return jsonify(beat)


@app.route('/api/beats/<beat_id>/status', methods=['PUT'])
def update_beat_status(beat_id):
    """Update beat status."""
    data = request.json
    status = data.get("status", "configuring")
    watcher.update_status(beat_id, status)
    return jsonify({"ok": True, "beat_id": beat_id, "status": status})


# ═══════════════════════════════════════════════════════════════
# ARTISTS â€” Database endpoints
# ═══════════════════════════════════════════════════════════════

@app.route('/api/artists', methods=['GET'])
def get_artists():
    """Get all artists (flat list)."""
    artists = get_all_artists()
    return jsonify({
        "artists": artists,
        "total": len(artists)
    })


@app.route('/api/artists/tiers', methods=['GET'])
def get_artists_tiers():
    """Get artists organized by tier."""
    return jsonify(get_artists_by_tier())


@app.route('/api/artists/search', methods=['GET'])
def search_artists_endpoint():
    """Search artists by name."""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"results": [], "query": ""})
    results = search_artists(query)
    return jsonify({"results": results, "query": query})


# ═══════════════════════════════════════════════════════════════
# ARTWORKS â€” Browse & select
# ═══════════════════════════════════════════════════════════════

@app.route('/api/artworks', methods=['GET'])
def get_artworks():
    """List all artworks organized by vibe folder."""
    artworks = list_artworks(ARTWORKS_DIR)
    return jsonify(artworks)


@app.route('/api/artworks/image/<vibe>/<filename>', methods=['GET'])
def serve_artwork(vibe, filename):
    """Serve an artwork image file."""
    vibe_dir = os.path.join(ARTWORKS_DIR, vibe.upper())
    if not os.path.exists(os.path.join(vibe_dir, filename)):
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(vibe_dir, filename)


# ═══════════════════════════════════════════════════════════════
# LUT â€” Preview & process
# ═══════════════════════════════════════════════════════════════

@app.route('/api/lut/presets', methods=['GET'])
def get_lut_presets():
    """Get available LUT presets (built-in + custom)."""
    built_in = get_available_presets()
    custom = load_custom_presets()
    custom_info = {
        f"⚡{k}": {
            "name": v.get("name", k),
            "custom": True,
        }
        for k, v in custom.items()
    }
    return jsonify({**built_in, **custom_info})


@app.route('/api/lut/custom-presets', methods=['GET'])
def get_custom_presets():
    """Get saved custom LUT presets."""
    custom = load_custom_presets()
    return jsonify({
        "presets": custom,
        "count": len(custom),
        "max": MAX_CUSTOM_PRESETS,
    })


@app.route('/api/lut/custom-presets', methods=['POST'])
def save_custom_preset():
    """Save a custom LUT preset."""
    data = request.json
    name = data.get("name", "").strip().lower().replace(" ", "_")
    params = data.get("params", {})
    if not name or not params:
        return jsonify({"error": "Name and params required"}), 400
    if name in ("rage", "melodic"):
        return jsonify({"error": "Cannot overwrite built-in presets"}), 400
    custom = load_custom_presets()
    if len(custom) >= MAX_CUSTOM_PRESETS and name not in custom:
        return jsonify({"error": f"Max {MAX_CUSTOM_PRESETS} presets"}), 400
    custom[name] = params
    save_custom_presets(custom)
    return jsonify({"ok": True, "name": name, "count": len(custom)})


@app.route('/api/lut/custom-presets/<name>', methods=['DELETE'])
def delete_custom_preset(name):
    """Delete a custom LUT preset."""
    custom = load_custom_presets()
    if name not in custom:
        return jsonify({"error": "Preset not found"}), 404
    del custom[name]
    save_custom_presets(custom)
    return jsonify({"ok": True, "remaining": len(custom)})


@app.route('/api/lut/preview', methods=['POST'])
def lut_preview():
    """
    Generate LUT preview for selected artwork.
    Expects: { "artwork_path", "preset", "crop"?, "params"? }
    - If "params" is provided (from Spectral Tuner sliders), uses lut_process_full directly.
    - Otherwise uses the stored preset (custom or built-in).
    """
    data = request.json or {}
    artwork_rel   = data.get("artwork_path", "")
    preset_raw    = data.get("preset", "rage")
    # Strip leading ⚡ emoji (or any corrupted encoding variant) safely via regex
    import re as _re
    preset        = _re.sub(r'^[\u26a1\xc3\xa2\xc5\xa1\xc2\xa1\u00e2\u009a\u00a1]+', '', preset_raw).strip()
    if not preset:
        preset = preset_raw.strip()   # fallback: use as-is if strip removed everything
    crop          = data.get("crop", None)
    tuner_params  = data.get("params", None)  # live Spectral Tuner params

    full_path = os.path.normpath(os.path.join(ARTWORKS_DIR, artwork_rel))
    if not os.path.exists(full_path):
        return jsonify({"error": f"Artwork not found: {artwork_rel}"}), 404

    try:
        from PIL import Image
        import numpy as np

        img = Image.open(full_path).convert('RGB')

        # 1. Apply 1:1 crop if requested
        if crop:
            cx  = float(crop.get("x",    0))
            cy  = float(crop.get("y",    0))
            csz = float(crop.get("size", 1))
            iw, ih = img.size
            base_dim = min(iw, ih)
            box_px   = max(50, min(int(base_dim * csz), base_dim))
            left     = max(0, min(int(iw * cx), iw - box_px))
            top      = max(0, min(int(ih * cy), ih - box_px))
            img = img.crop((left, top, left + box_px, top + box_px))
            img = img.resize((1080, 1080), Image.LANCZOS)

        # 2. Resize for preview speed
        w, h = img.size
        scale = min(1000 / w, 1000 / h, 1.0)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # 3. Apply LUT
        arr = np.array(img)

        if tuner_params and isinstance(tuner_params, dict) and len(tuner_params) > 0:
            # Live Spectral Tuner params â€” use directly
            processed = lut_process_full(arr, tuner_params)
        else:
            # Preset lookup (custom or built-in)
            custom_presets = load_custom_presets()
            if preset in custom_presets:
                params = custom_presets[preset]
                processed = lut_process_full(arr, params)
            else:
                # Built-in (rage / melodic) â€” write to temp then apply
                tmp_path = os.path.join(OUTPUT_DIR, f"_preview_tmp_{preset}.jpg")
                img.save(tmp_path, "JPEG", quality=92)
                preview_path = apply_lut_only(
                    input_path=tmp_path,
                    preset_name=preset,
                    output_dir=OUTPUT_DIR
                )
                from PIL import Image as PILImage
                result_img = PILImage.open(preview_path)
                buf = io.BytesIO()
                result_img.save(buf, format='JPEG', quality=88)
                buf.seek(0)
                return send_file(buf, mimetype='image/jpeg')

        buf = io.BytesIO()
        processed.save(buf, format='JPEG', quality=88)
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lut/preview-with-params', methods=['POST'])
def lut_preview_with_params():
    """
    Generate LUT preview with custom parameters.
    Multipart form: image file + params JSON string.
    Returns: processed JPEG preview.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    params_str = request.form.get("params", "{}")
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid params JSON"}), 400
    
    image_file = request.files['image']

    # Query string is reliable with multipart; form field kept as fallback
    master_raw = request.args.get("master") or request.form.get("master") or "1"
    try:
        master = float(master_raw)
    except (TypeError, ValueError):
        master = 1.0
    if master != master or master < 0 or master > 1:  # NaN or out of range
        master = 1.0
    master = max(0.0, min(1.0, master))

    try:
        from PIL import Image
        import numpy as np
        import io

        img = Image.open(image_file.stream).convert('RGB')

        # Downscale for fast preview (max 800px)
        w, h = img.size
        scale = min(800 / w, 800 / h, 1.0)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        original_pil = img.copy()
        arr = np.array(img)
        processed = lut_process_full(arr, params)
        result = apply_master_blend(original_pil, processed, master)

        # Save to buffer
        buf = io.BytesIO()
        result.save(buf, format='JPEG', quality=85)
        buf.seek(0)
        
        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lut/save-with-params', methods=['POST'])
def lut_save_with_params():
    """
    Apply full LUT pipeline at original resolution and write JPEG to OUTPUT/.
    Multipart form: image file + params JSON string.
    Optional: basename (sanitized) used in the filename prefix.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    params_str = request.form.get("params", "{}")
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid params JSON"}), 400

    raw_base = request.form.get("basename", "").strip()
    safe_base = "".join(c for c in raw_base if c.isalnum() or c in ("_", "-"))[:80] or "export"

    master_raw = request.args.get("master") or request.form.get("master") or "1"
    try:
        master = float(master_raw)
    except (TypeError, ValueError):
        master = 1.0
    if master != master or master < 0 or master > 1:
        master = 1.0
    master = max(0.0, min(1.0, master))

    try:
        from PIL import Image
        import numpy as np

        image_file = request.files['image']
        img = Image.open(image_file.stream).convert('RGB')
        original_pil = img.copy()
        arr = np.array(img)
        processed = lut_process_full(arr, params)
        result = apply_master_blend(original_pil, processed, master)

        ts = int(time.time() * 1000) % 1_000_000_000_000
        filename = f"lut_tuner_{safe_base}_{ts}.jpg"
        out_path = os.path.join(OUTPUT_DIR, filename)
        result.save(out_path, "JPEG", quality=95)

        return jsonify({
            "success": True,
            "filename": filename,
            "url": f"/api/output/{filename}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/lut/tuner-defaults', methods=['GET'])
def lut_tuner_defaults():
    """
    Return the built-in PRESETS from lut_tuner.py so the frontend
    can populate slider defaults without hardcoding.
    """
    from lut_tuner import PRESETS as TUNER_PRESETS
    return jsonify(TUNER_PRESETS)


@app.route('/api/lut/process', methods=['POST'])
def lut_process():
    """
    Full LUT processing for final render.
    Expects: { "artwork_path": "RAGE/img.jpg", "preset": "rage", "beat_name": "Night Vision" }
    Returns: JSON with output paths
    """
    data = request.json
    artwork_rel = data.get("artwork_path", "")
    preset = data.get("preset", "rage")
    beat_name = data.get("beat_name", "output")
    
    full_path = os.path.join(ARTWORKS_DIR, artwork_rel)
    if not os.path.exists(full_path):
        return jsonify({"error": f"Artwork not found: {artwork_rel}"}), 404
    
    try:
        result = process_artwork(
            input_path=full_path,
            preset_name=preset,
            output_dir=OUTPUT_DIR,
            beat_name=beat_name
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# SEO â€” Title & metadata generation
# ═══════════════════════════════════════════════════════════════

@app.route('/api/seo/preview-title', methods=['POST'])
def preview_title():
    """
    Live title preview as user selects artists.
    Expects: { "artist1": "...", "artist2": "...", "beat_name": "..." }
    """
    data = request.json
    artist1 = data.get("artist1", "")
    artist2 = data.get("artist2", "")
    beat_name = data.get("beat_name", "")
    
    if not all([artist1, artist2, beat_name]):
        return jsonify({"title": "[FREE] _____ x _____ Type Beat - \"_____\"", "complete": False})
    
    title = generate_title(artist1, artist2, beat_name)
    return jsonify({"title": title, "complete": True, "length": len(title)})


@app.route('/api/seo/generate', methods=['POST'])
def generate_seo():
    """
    Generate full SEO package (uses config.json for channel, license, links).
    Expects: { "artist1", "artist2", "beat_name", "bpm", "key", "drop", "vibe" }
    """
    data = request.json or {}

    required = ["artist1", "beat_name", "bpm", "key", "drop"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    result = generate_publish_package(
        artist1=data["artist1"],
        artist2=data.get("artist2") or None,   # optional
        beat_name=data["beat_name"],
        bpm=int(data["bpm"]),
        key=data["key"],
        drop_timestamp=data.get("drop") or data.get("drop_ts", "0:25"),
        vibe=data.get("vibe", "trap"),
        channel_config=get_seo_channel_config(),
        outro_timestamp=data.get("outro") or data.get("outro_ts"),
        duration_seconds=data.get("duration_seconds"),
    )

    return jsonify(result)


@app.route('/api/seo/generate-full', methods=['POST'])
def generate_seo_full():
    """
    Same as generate publish package; body may override channel fields inline.
    Expects: beat fields + optional channel_name, channel_handle, contact_email, social_links, etc.
    """
    data = request.json or {}

    required = ["artist1", "beat_name", "bpm", "key", "drop"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    base = get_seo_channel_config()
    override_keys = (
        "channel_name", "channel_handle", "contact_email", "social_links",
        "default_license", "lease_url", "default_language", "producer_credit",
        "youtube_region", "youtube_category",
    )
    for k in override_keys:
        if k in data and data[k] is not None:
            base[k] = data[k]

    result = generate_publish_package(
        artist1=data["artist1"],
        artist2=data.get("artist2") or None,    # optional â€” same as /generate
        beat_name=data["beat_name"],
        bpm=int(data["bpm"]),
        key=data["key"],
        drop_timestamp=data.get("drop") or data.get("drop_ts", "0:25"),
        vibe=data.get("vibe", "trap"),
        channel_config=base,
        outro_timestamp=data.get("outro") or data.get("outro_ts"),
        duration_seconds=data.get("duration_seconds"),
    )
    return jsonify(result)


@app.route('/api/channel-meta', methods=['GET'])
def channel_meta():
    """Safe fields for YouTube preview UI (no secrets)."""
    c = load_config()
    return jsonify({
        "channel_name": c.get("channel_name", "ENNY TANG"),
        "channel_handle": c.get("channel_handle", "@enny-tang"),
        "youtube_region": c.get("youtube_region", "US"),
        "youtube_category": c.get("youtube_category", "10"),
        "default_language": c.get("default_language", "en"),
        "has_contact": bool(c.get("contact_email") or c.get("social_links")),
    })


# ═══════════════════════════════════════════════════════════════
# RENDER â€” MP4 generation
# ═══════════════════════════════════════════════════════════════

@app.route('/api/render/mp4', methods=['POST'])
def render_video():
    """
    Render final MP4 from LUT-processed image + WAV audio.
    Expects: {
        "beat_id": "beat_xxx",
        "artwork_path": "RAGE/img.jpg",
        "preset": "rage",
        "beat_name": "Night Vision",
        "quality": "2K" | "HD"   â† NEW: upscale quality selection
    }
    """
    data = request.json
    beat_id = data.get("beat_id")
    
    # Get beat info
    beat = watcher.get_beat_by_id(beat_id)
    if not beat:
        return jsonify({"error": "Beat not found"}), 404
    
    watcher.update_status(beat_id, "rendering")
    
    # Step 1: Process artwork with LUT + Upscale
    artwork_rel = data.get("artwork_path", "")
    artwork_full = os.path.join(ARTWORKS_DIR, artwork_rel)
    preset    = data.get("preset", "rage")
    beat_name = data.get("beat_name", "output")
    crop      = data.get("crop", None)
    quality   = data.get("quality", "HD")  # "2K" or "HD"
    
    if not os.path.exists(artwork_full):
        return jsonify({"error": "Artwork not found"}), 404
    
    try:
        lut_preset_name = data.get("lut_preset_name")
        custom_presets = load_custom_presets()
        
        if lut_preset_name and lut_preset_name in custom_presets:
            # Use full tuner pipeline + smart upscaler
            from upscaler import upscale_for_render, QUALITY_SPECS
            from PIL import Image
            import numpy as np

            # Get the video frame dimensions for this quality
            spec = QUALITY_SPECS.get(quality, QUALITY_SPECS["HD"])
            fw, fh = spec["frame"]

            # Load and upscale artwork to square
            from upscaler import upscale_artwork
            img_raw = Image.open(artwork_full).convert("RGB")
            img_upscaled = upscale_artwork(img_raw, quality=quality, square_crop=True)

            # Apply LUT processing  (lut_process_full already imported at top from lut_tuner)
            tuner_params = custom_presets[lut_preset_name]
            arr = np.array(img_upscaled)
            processed_pil = lut_process_full(arr, tuner_params)

            # Compose into video frame
            from upscaler import compose_video_frame
            video_frame_img = compose_video_frame(processed_pil, quality=quality)

            # Save video frame and thumbnail
            safe_name = beat_name.replace(" ", "_").replace('"', '').replace("'", "")
            video_filename = f"{safe_name}_{lut_preset_name}_video.jpg"
            thumb_filename = f"{safe_name}_{lut_preset_name}_thumbnail.jpg"
            video_path_out = os.path.join(OUTPUT_DIR, video_filename)
            thumb_path_out = os.path.join(OUTPUT_DIR, thumb_filename)

            video_frame_img.save(video_path_out, "JPEG", quality=95)
            # Thumbnail = video frame scaled down
            thumb = video_frame_img.resize((1280, 720), Image.LANCZOS)
            thumb.save(thumb_path_out, "JPEG", quality=90)

            lut_result = {
                "preset": lut_preset_name,
                "preset_display": f"Custom: {lut_preset_name}",
                "quality": quality,
                "outputs": {
                    "video":     {"path": video_path_out, "size": spec["frame"], "filename": video_filename},
                    "thumbnail": {"path": thumb_path_out, "size": (1280, 720),   "filename": thumb_filename},
                },
                "input_path": artwork_full,
            }
        else:
            # Use basic built-in preset (RAGE / MELODIC)
            lut_result = process_artwork(
                input_path=artwork_full,
                preset_name=preset,
                output_dir=OUTPUT_DIR,
                beat_name=beat_name,
                crop=crop
            )
    except Exception as e:
        return jsonify({"error": f"LUT processing failed: {e}"}), 500
    
    # Step 2: Render MP4 (with optional VFX)
    video_frame = lut_result["outputs"]["video"]["path"]
    audio_path = beat["filepath"]

    # Get actual audio duration to pass as hard cap â€” prevents longer-than-beat renders
    audio_duration = get_audio_duration(audio_path)

    safe_name = beat_name.replace(" ", "_").replace('"', '').replace("'", "")
    mp4_filename = f"{safe_name}_{preset}_final.mp4"  # .mp4 not .mov
    mp4_path = os.path.join(OUTPUT_DIR, mp4_filename)

    vfx_config = data.get("vfx_config", None)

    render_result = render_mp4_with_effects(
        image_path=video_frame,
        audio_path=audio_path,
        output_path=mp4_path,
        vfx_config=vfx_config,
        duration=audio_duration if audio_duration > 0 else None,  # exact audio length cap
    )
    
    if not render_result.get("success"):
        watcher.update_status(beat_id, "render_failed")
        return jsonify({"error": render_result.get("error", "Render failed")}), 500
    
    watcher.update_status(beat_id, "rendered")
    
    return jsonify({
        "lut": lut_result,
        "render": render_result,
        "mp4_path": mp4_path,
        "thumbnail_path": lut_result["outputs"]["thumbnail"]["path"],
        "beat_id": beat_id,
        "audio_duration_seconds": round(audio_duration, 2) if audio_duration > 0 else None,
    })


# ═══════════════════════════════════════════════════════════════
# VFX â€” Video Effects
# ═══════════════════════════════════════════════════════════════

@app.route('/api/vfx/effects', methods=['GET'])
def vfx_list_effects():
    """List all available video effects."""
    return jsonify({"effects": get_effects_list()})


@app.route('/api/vfx/timeline', methods=['POST'])
def vfx_timeline():
    """
    Compute effect timeline for preview.
    Expects: { duration, interval, effect_duration, effects[], order }
    """
    data = request.json
    timeline = get_effect_timeline(
        total_duration=data.get("duration", 180),
        interval=data.get("interval", 10),
        effect_duration=data.get("effect_duration", 0.5),
        effects=data.get("effects", []),
        order=data.get("order", "sequential"),
    )
    return jsonify({"timeline": timeline, "total_effects": len(timeline)})


VFX_PRESETS_FILE = os.path.join(os.path.dirname(__file__), "vfx_presets.json")

def _load_vfx_presets():
    if os.path.exists(VFX_PRESETS_FILE):
        with open(VFX_PRESETS_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_vfx_presets(presets):
    with open(VFX_PRESETS_FILE, "w") as f:
        json.dump(presets, f, indent=2)


@app.route('/api/vfx/presets', methods=['GET'])
def vfx_get_presets():
    """List saved VFX presets."""
    return jsonify({"presets": _load_vfx_presets()})


@app.route('/api/vfx/presets', methods=['POST'])
def vfx_save_preset():
    """Save a VFX preset."""
    data = request.json
    name = data.get("name", "").strip().lower().replace(" ", "_")
    config = data.get("config", {})
    if not name:
        return jsonify({"error": "Name required"}), 400
    presets = _load_vfx_presets()
    if len(presets) >= 20 and name not in presets:
        return jsonify({"error": "Max 20 VFX presets"}), 400
    presets[name] = config
    _save_vfx_presets(presets)
    return jsonify({"ok": True, "name": name})


@app.route('/api/vfx/presets/<name>', methods=['DELETE'])
def vfx_delete_preset(name):
    """Delete a VFX preset."""
    presets = _load_vfx_presets()
    if name in presets:
        del presets[name]
        _save_vfx_presets(presets)
    return jsonify({"ok": True})


@app.route('/api/output/<path:filename>', methods=['GET'])
def serve_output_file(filename):
    """Serve rendered MP4/thumbnail files from OUTPUT/ directory."""
    safe_path = os.path.normpath(os.path.join(OUTPUT_DIR, filename))
    if not safe_path.startswith(os.path.normpath(OUTPUT_DIR)):
        return jsonify({"error": "Invalid path"}), 403
    if not os.path.exists(safe_path):
        return jsonify({"error": "File not found"}), 404
    return send_file(safe_path)


@app.route('/api/vfx/preview', methods=['POST'])
def vfx_preview_render():
    """
    Render a short VFX preview clip (10s) from an image + vfx_config.
    Expects multipart form: image file + vfx_config JSON string.
    Returns JSON with preview file URL.
    """
    import uuid
    from mp4_render import render_mp4_with_effects

    if 'image' not in request.files:
        return jsonify({"error": "Image file required"}), 400

    image_file = request.files['image']
    vfx_config_str = request.form.get('vfx_config', '{}')
    try:
        vfx_config = json.loads(vfx_config_str)
    except (json.JSONDecodeError, TypeError):
        vfx_config = {}

    # Save temp image
    preview_id = str(uuid.uuid4())[:8]
    temp_dir = os.path.join(OUTPUT_DIR, "_vfx_previews")
    os.makedirs(temp_dir, exist_ok=True)
    temp_img = os.path.join(temp_dir, f"preview_{preview_id}.jpg")
    image_file.save(temp_img)

    # Create a silent audio track (10s)
    silent_audio = os.path.join(temp_dir, f"silent_{preview_id}.wav")
    import subprocess
    from mp4_render import get_ffmpeg_cmd
    subprocess.run([
        get_ffmpeg_cmd(), "-y", "-f", "lavfi", "-i",
        "anullsrc=r=44100:cl=stereo", "-t", "10",
        silent_audio
    ], capture_output=True, timeout=30)

    # Render preview â€” clamp interval for 10s preview so effects are always visible
    output_mp4 = os.path.join(temp_dir, f"vfx_preview_{preview_id}.mp4")
    preview_duration = 10.0
    preview_config = dict(vfx_config)
    # Ensure at least 2 effects trigger in the preview
    max_interval = (preview_duration - preview_config.get("effect_duration", 0.5)) / 2
    if preview_config.get("interval_seconds", 10) > max_interval:
        preview_config["interval_seconds"] = max(1, max_interval)
    try:
        result = render_mp4_with_effects(
            image_path=temp_img,
            audio_path=silent_audio,
            output_path=output_mp4,
            vfx_config=preview_config,
            duration=preview_duration,
        )
        # Clean up temp files
        for f in [temp_img, silent_audio]:
            if os.path.exists(f):
                os.remove(f)

        return jsonify({
            "preview_url": f"/api/output/_vfx_previews/vfx_preview_{preview_id}.mp4",
            "render": result,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# YOUTUBE â€” Direct API upload (replaces n8n)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/youtube/status', methods=['GET'])
def youtube_status():
    """Get YouTube API authentication status."""
    status = get_auth_status()
    deps = check_dependencies()
    return jsonify({**status, **deps})


@app.route('/api/youtube/channel', methods=['GET'])
def youtube_channel():
    """Get authenticated YouTube channel info."""
    info = get_channel_info()
    return jsonify(info)


@app.route('/api/youtube/playlists', methods=['GET'])
def youtube_playlists():
    """Fetch all playlists from the authenticated channel."""
    result = get_playlists()
    return jsonify(result)


@app.route('/api/youtube/playlists/add', methods=['POST'])
def youtube_add_to_playlist():
    """
    Add an uploaded video to a playlist.
    Expects: { "video_id": "...", "playlist_id": "..." }
    """
    data = request.json or {}
    video_id = data.get("video_id")
    playlist_id = data.get("playlist_id")
    if not video_id or not playlist_id:
        return jsonify({"error": "video_id and playlist_id required"}), 400
    result = add_video_to_playlist(video_id, playlist_id)
    return jsonify(result)


@app.route('/api/upload/youtube', methods=['POST'])
def upload_to_youtube():
    """
    Upload video directly to YouTube via API.
    Expects: {
        "mp4_path": "/path/to/video.mp4",
        "thumbnail_path": "/path/to/thumb.jpg",  (optional)
        "title": "[FREE] ...",
        "description": "...",
        "tags": [...],
        "category_id": "10",
        "privacy_status": "public"
    }
    """
    yt_auth = get_auth_status()
    if not yt_auth.get("authenticated"):
        return jsonify({
            "error": "YouTube not authenticated. Run: python youtube_upload.py --setup",
            "auth_status": yt_auth
        }), 400

    data = request.json or {}
    beat_id = data.get("beat_id")  # optional
    mp4_path = data.get("mp4_path") or data.get("video_path")  # accept both keys

    if not mp4_path:
        return jsonify({"error": "mp4_path is required"}), 400
    if not os.path.exists(mp4_path):
        return jsonify({"error": f"MP4 file not found: {mp4_path}"}), 404

    if beat_id:
        watcher.update_status(beat_id, "uploading")

    # Direct YouTube upload
    result = upload_video(
        mp4_path=mp4_path,
        title=data.get("title", ""),
        description=data.get("description", ""),
        tags=data.get("tags", []),
        category_id=data.get("category_id", "10"),
        privacy_status=data.get("privacy_status", "public"),
        thumbnail_path=data.get("thumbnail_path"),
    )

    if result.get("success"):
        if beat_id:
            watcher.mark_processed(beat_id, {
                "video_id": result.get("video_id"),
                "video_url": result.get("video_url"),
                "uploaded_at": result.get("uploaded_at"),
            })
        return jsonify(result)
    else:
        if beat_id:
            watcher.update_status(beat_id, "upload_failed")
        return jsonify(result), 500



@app.route('/api/schedule/youtube', methods=['POST'])
def schedule_youtube():
    """
    Upload video to YouTube scheduled (private until publishAt).
    Expects: { mp4_path, title, description, tags, category_id,
               schedule_date (YYYY-MM-DD), schedule_hour (TRT), schedule_min }
    """
    yt_auth = get_auth_status()
    if not yt_auth.get("authenticated"):
        return jsonify({
            "error": "YouTube not authenticated",
            "auth_status": yt_auth
        }), 400

    data = request.json or {}
    beat_id = data.get("beat_id")  # optional
    mp4_path = data.get("mp4_path") or data.get("video_path")  # accept both keys

    if not mp4_path:
        return jsonify({"error": "mp4_path is required"}), 400
    if not os.path.exists(mp4_path):
        return jsonify({"error": f"MP4 file not found: {mp4_path}"}), 404

    schedule_hour = int(data.get("schedule_hour", 22))
    schedule_min  = int(data.get("schedule_min", 0))
    schedule_date_str = data.get("schedule_date")

    # TRT is UTC+3. Convert TRT HH:MM -> UTC HH:MM using total minutes
    trt_total_minutes = schedule_hour * 60 + schedule_min
    utc_total_minutes = trt_total_minutes - 180  # subtract UTC+3 offset
    day_offset = 0
    if utc_total_minutes < 0:
        utc_total_minutes += 1440  # wrap around midnight
        day_offset = -1            # previous calendar day in UTC
    target_utc_hour = utc_total_minutes // 60
    target_utc_min  = utc_total_minutes % 60

    if schedule_date_str:
        from datetime import date as _date
        chosen_date = _date.fromisoformat(schedule_date_str)
        # Use exactly the chosen date â€” no day-offset adjustment.
        # day_offset only matters when crossing UTC midnight (e.g. TRT 01:00 = UTC 22:00 prev day)
        target_utc = datetime(chosen_date.year, chosen_date.month, chosen_date.day,
                              target_utc_hour, target_utc_min, 0)
        if day_offset:
            target_utc += timedelta(days=day_offset)
        # Warn if the resulting UTC time is more than 10 minutes in the past
        if target_utc < datetime.utcnow() - timedelta(minutes=10):
            return jsonify({"error": "SeÃ§ilen saat geÃ§miÅŸte kaldÄ±. LÃ¼tfen ileride bir saat seÃ§in."}), 400
    else:
        # No date given: use today, auto-advance to tomorrow if time has passed
        now_utc = datetime.utcnow()
        target_utc = now_utc.replace(hour=target_utc_hour, minute=target_utc_min, second=0, microsecond=0)
        if now_utc >= target_utc:
            target_utc += timedelta(days=1)

    publish_at = target_utc.isoformat() + "Z"

    if beat_id:
        watcher.update_status(beat_id, "uploading to cloud schedule")

    result = upload_video(
        mp4_path=mp4_path,
        title=data.get("title", ""),
        description=data.get("description", ""),
        tags=data.get("tags", []),
        category_id=data.get("category_id", "10"),
        privacy_status="private",  # required for publishAt
        thumbnail_path=data.get("thumbnail_path"),
        publish_at=publish_at
    )

    if result.get("success"):
        if beat_id:
            watcher.mark_processed(beat_id, {
                "video_id": result.get("video_id"),
                "video_url": result.get("video_url"),
                "scheduled_at": publish_at,
            })
        result["scheduled_at"] = publish_at
        result["scheduled_trt"] = f"{schedule_date_str} {schedule_hour:02d}:{schedule_min:02d} TRT"
        return jsonify(result)
    else:
        if beat_id:
            watcher.update_status(beat_id, "schedule_failed")
        return jsonify(result), 500



# ═══════════════════════════════════════════════════════════════
# FULL PIPELINE â€” One-click process
# ═══════════════════════════════════════════════════════════════

@app.route('/api/pipeline/preview', methods=['POST'])
def pipeline_preview():
    """
    Generate full preview (title + thumbnail + SEO) without rendering MP4.
    Fast preview for dashboard display.
    """
    data = request.json
    
    # Generate title preview
    title = generate_title(
        data.get("artist1", ""),
        data.get("artist2", ""),
        data.get("beat_name", "")
    )
    
    # Generate SEO
    seo = generate_publish_package(
        artist1=data.get("artist1", ""),
        artist2=data.get("artist2", ""),
        beat_name=data.get("beat_name", ""),
        bpm=int(data.get("bpm", 140)),
        key=data.get("key", "Fm"),
        drop_timestamp=data.get("drop", "0:25"),
        vibe=data.get("vibe", "trap"),
        channel_config=get_seo_channel_config(),
    )
    
    return jsonify({
        "title": title,
        "seo": seo,
        "ready_to_render": all([
            data.get("artist1"),
            data.get("artist2"),
            data.get("beat_name"),
            data.get("artwork_path"),
            data.get("beat_id"),
        ])
    })





# ═══════════════════════════════════════════════════════════════
# INSTAGRAM ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/instagram/status', methods=['GET'])
def instagram_status():
    """Check Instagram connection status."""
    try:
        from instagram_upload import get_status
        return jsonify(get_status())
    except Exception as e:
        return jsonify({
            "connected": False,
            "authenticated": False,
            "status": "ERROR",
            "error": str(e),
            "message": "instagram_upload.py error"
        })

@app.route('/api/instagram/connect', methods=['POST'])
def instagram_connect():
    """
    Trigger Instagram OAuth flow.
    Opens browser - user authorizes - token saved locally.
    """
    try:
        from instagram_upload import authenticate
        data = request.json or {}
        port = data.get("port", 8891)
        token = authenticate(redirect_port=int(port))
        return jsonify({
            "success": True,
            "user_id": token.get("user_id"),
            "message": "Instagram connected successfully"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/instagram/account', methods=['GET'])
def instagram_account():
    """Return connected IG account info."""
    try:
        from instagram_upload import get_account_info
        return jsonify(get_account_info())
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/instagram/refresh', methods=['POST'])
def instagram_refresh():
    """Refresh Instagram long-lived token."""
    try:
        from instagram_upload import refresh_token
        result = refresh_token()
        return jsonify({"success": True, "expires_in": result.get("expires_in")})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ffmpeg/version', methods=['GET'])
def ffmpeg_version():
    """Return FFmpeg version string."""
    try:
        import subprocess
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        first_line = result.stdout.split("\n")[0] if result.stdout else ""
        version = first_line.replace("ffmpeg version ", "").split(" ")[0]
        return jsonify({"version": version, "available": True})
    except Exception:
        return jsonify({"version": None, "available": False})


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def _run_server():
    # NOT: Bu blok eskiden `if __name__ == '__main__':` idi ve dosyanin
    # ortasindaydi; app.run() blokladigi icin altindaki v5 plugin
    # endpoint'leri hic kayit edilmiyordu. Artik dosyanin en sonundan cagriliyor.
    print()
    print("=" * 55)
    print("  JETBOX v3 â€” API Backend")
    print("  by ENNYTANG")
    print("=" * 55)
    print(f"  BEATS:    {BEATS_DIR}")
    print(f"  ARTWORKS: {ARTWORKS_DIR}")
    print(f"  OUTPUT:   {OUTPUT_DIR}")
    print(f"  Artists:  {len(get_all_artists())} loaded")
    print(f"  LUT:      {', '.join(LUT_PRESETS.keys())}")
    print(f"  FFmpeg:   {check_ffmpeg().get('version', 'NOT FOUND')}")
    print(f"  Watcher:  {'Running' if watcher._running else 'Stopped'}")
    yt = get_auth_status()
    yt_ok = "Authenticated" if yt.get("authenticated") else "Run: python youtube_upload.py --setup"
    print(f"  YouTube:  {yt_ok}")
    print("=" * 55)
    print(f"  API:      http://localhost:5001")
    print(f"  Health:   http://localhost:5001/api/health")
    print(f"  YT Auth:  python youtube_upload.py --setup")
    print("=" * 55)
    print()
    
    app.run(debug=True, host='127.0.0.1', port=5001, threaded=True)


# ═══════════════════════════════════════════════════
# JETBOX v5 PLUGIN ENDPOINTS
# ═══════════════════════════════════════════════════

@app.route('/api/youtube/my-videos', methods=['GET'])
def youtube_my_videos():
    """
    KanalÄ±n tÃ¼m videolarÄ±nÄ± satÄ±ÅŸ skoru (view+like+comment)
    yÃ¼ksek olandan dÃ¼ÅŸÃ¼ÄŸe sÄ±ralayarak dÃ¶ndÃ¼rÃ¼r.
    Query params: ?max=50
    """
    yt_auth = get_auth_status()
    if not yt_auth.get('authenticated'):
        return jsonify({'error': 'YouTube not authenticated'}), 400
    max_results = min(int(request.args.get('max', 50)), 200)
    result = get_channel_videos(max_results=max_results)
    return jsonify(result)


@app.route('/api/beatstars/fisheye', methods=['POST'])
def beatstars_fisheye():
    """
    Thumbnail URL veya lokal dosya yolundan fisheye efekti uygular.
    Expects JSON: {
        "thumbnail_url": "https://...",   # URL'den Ã§ek
        "image_path": "/path/to/img.jpg", # VEYA lokal dosya
        "strength": 1.0,                  # 0.5=hafif, 1.0=tam, 1.5=aÅŸÄ±rÄ±
        "output_size": 1500,              # px
        "save_to_disk": false,            # true = OUTPUT/klasÃ¶rÃ¼ne kaydet
        "filename": "beat_name"           # kaydetme iÃ§in isim (opsiyonel)
    }
    Response: JPEG binary (Content-Disposition: attachment) veya {saved_path}
    """
    data = request.json or {}
    thumbnail_url = data.get('thumbnail_url')
    image_path    = data.get('image_path')
    strength      = float(data.get('strength', 1.0))
    output_size   = int(data.get('output_size', 1500))
    save_to_disk  = bool(data.get('save_to_disk', False))
    filename      = data.get('filename', 'fisheye')

    try:
        if thumbnail_url:
            img_bytes = fisheye_from_url(thumbnail_url, strength=strength, output_size=output_size)
        elif image_path:
            img_bytes = apply_fisheye(image_path, strength=strength, output_size=output_size)
        else:
            return jsonify({'error': 'thumbnail_url or image_path required'}), 400

        if save_to_disk:
            output_dir = os.path.join(os.path.dirname(__file__), '..', 'OUTPUT')
            saved = save_fisheye(img_bytes, output_dir, filename)
            return jsonify({'success': True, 'saved_path': os.path.abspath(saved)})
        else:
            # Direkt binary dÃ¶ndÃ¼r â€” browser indirir
            from flask import Response
            safe_name = filename.replace(' ', '_')
            return Response(
                img_bytes,
                mimetype='image/jpeg',
                headers={'Content-Disposition': f'attachment; filename="{safe_name}_fisheye.jpg"'}
            )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══ MAIN ENTRY — tum route'lar kayit edildikten sonra calisir ═══
if __name__ == '__main__':
    _run_server()

