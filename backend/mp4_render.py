"""
JETBOX v3 â€” MP4 Render Pipeline
FFmpeg: LUT-processed artwork (static) + WAV audio → YouTube-ready MP4
H.264/AAC encoding, 1920Ã-1080
"""

import subprocess
import os
import json

# â”€â”€â”€ CACHED EXECUTABLE PATHS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_FFMPEG_PATH  = None  # Cached FFmpeg executable path
_FFPROBE_PATH = None  # Cached ffprobe executable path


def render_mp4(
    image_path: str,
    audio_path: str,
    output_path: str,
    duration: float = None
) -> dict:
    """
    Render static image + audio into YouTube-ready MP4.
    
    Args:
        image_path: LUT-processed video frame (1920x1080 JPG)
        audio_path: WAV audio file
        output_path: Output MP4 path
        duration: Optional duration override (seconds). If None, uses audio length.
    
    Returns:
        dict with output path, file size, duration, encoding info
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # Always derive duration from audio â€” this is the hard cap.
    # get_audio_duration tries ffprobe then wave/mutagen fallbacks.
    total_duration = get_audio_duration(audio_path)
    if duration and duration > 0:
        # Never exceed actual audio length; use caller's value only if shorter
        total_duration = min(duration, total_duration) if total_duration > 0 else duration

    if total_duration <= 0:
        # Last resort: let FFmpeg handle it with -shortest only (no -t)
        total_duration = None

    # Build FFmpeg command
    # -loop 1         : loop single image
    # -t total_dur    : hard stop at exact audio length (primary duration control)
    # -shortest       : secondary safeguard â€” stop at shortest stream
    # -r 1            : 1 fps static image (saves encode time + file size)
    
    cmd = [
        get_ffmpeg_cmd(),
        "-y",                              # Overwrite output
        "-loop", "1",                      # Loop image
    ]
    if total_duration:
        cmd += ["-t", str(round(total_duration, 4))]  # Hard cap = exact audio length
    cmd += [
        "-i", image_path,                  # Input image
        "-i", audio_path,                  # Input audio
        "-c:v", "libx264",                 # H.264
        "-tune", "stillimage",             # Optimize for static
        # NOT: pcm_s24le MP4 konteynerine mux edilemez (FFmpeg hata verir).
        # AAC 384k YouTube icin fiilen kayipsizdir (YT zaten yeniden encode eder).
        "-c:a", "aac", "-b:a", "384k",
        "-ar", "48000",                    # 48kHz sample rate (YouTube standard)
        "-pix_fmt", "yuv420p",             # YouTube compatible
        "-r", "1",                         # 1 fps for static image
        "-shortest",                       # Always stop at audio end
        "-movflags", "+faststart",         # Web-optimized MP4
    ]
    
    cmd.append(output_path)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr[-500:] if result.stderr else "Unknown FFmpeg error",
                "command": " ".join(cmd)
            }
        
        # Get output file info
        file_size = os.path.getsize(output_path)
        probe_info = probe_media(output_path)
        
        return {
            "success": True,
            "output_path": output_path,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "duration": probe_info.get("duration"),
            "encoding": {
                "video_codec": "H.264",
                "audio_codec": "AAC 384k",
                "resolution": "1920x1080",
                "fps": 1,
                "pixel_format": "yuv420p"
            }
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg timeout (>5 minutes)"}
    except FileNotFoundError:
        return {"success": False, "error": "FFmpeg not installed. Install with: sudo apt install ffmpeg"}


def render_mp4_with_effects(
    image_path: str,
    audio_path: str,
    output_path: str,
    vfx_config: dict = None,
    duration: float = None
) -> dict:
    """
    Render image + audio into MP4 with periodic video effects.
    
    Uses 24fps + FFmpeg filter_complex for animated effects.
    If vfx_config is None or disabled, falls back to static 1fps render.
    
    Args:
        image_path: LUT-processed video frame (1920x1080 JPG)
        audio_path: WAV audio file
        output_path: Output MP4 path
        vfx_config: {
            "enabled": bool,
            "interval_seconds": float,
            "effect_duration": float,
            "effects": list[str],
            "order": "sequential" | "random"
        }
        duration: Optional duration override
    
    Returns:
        dict with output path, file size, duration, encoding info
    """
    # Fall back to static render if VFX disabled or not configured
    if not vfx_config or not vfx_config.get("enabled", False):
        return render_mp4(image_path, audio_path, output_path, duration)
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio not found: {audio_path}")
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # Always derive duration from audio â€” this is the hard cap.
    total_duration = get_audio_duration(audio_path)
    if duration and duration > 0:
        total_duration = min(duration, total_duration) if total_duration > 0 else duration
    # If still unknown, fall back to static render without -t
    if not total_duration or total_duration <= 0:
        return render_mp4(image_path, audio_path, output_path, duration)

    # Build effect filter chain
    from video_effects import build_filter_chain

    interval = vfx_config.get("interval_seconds", 10)
    effect_dur = vfx_config.get("effect_duration", 0.5)
    effects = vfx_config.get("effects", [])
    order = vfx_config.get("order", "sequential")

    # Kare boyutunu gorselden oku â€” zoom/shake efektleri 2K'da da dogru calissin
    frame_w, frame_h = 1920, 1080
    try:
        from PIL import Image
        with Image.open(image_path) as _im:
            frame_w, frame_h = _im.size
    except Exception:
        pass

    result = build_filter_chain(
        total_duration=total_duration,
        interval=interval,
        effect_duration=effect_dur,
        effects=effects,
        order=order,
        frame_width=frame_w,
        frame_height=frame_h,
    )

    # build_filter_chain returns (chain, label) tuple or empty string on no effects
    if not result or not isinstance(result, tuple):
        # No valid effects â€” fall back to static
        return render_mp4(image_path, audio_path, output_path, duration)

    filter_chain, final_label = result

    # Build FFmpeg command with effects at 24fps
    # -t before image input caps the -loop 1 infinite loop at exact audio length
    cmd = [
        get_ffmpeg_cmd(),
        "-y",
        "-loop", "1",
    ]
    if total_duration:
        cmd += ["-t", str(round(total_duration, 4))]  # Hard cap = exact audio length
    cmd += [
        "-i", image_path,
        "-i", audio_path,
        "-filter_complex", f"{filter_chain}",
        "-map", f"[{final_label}]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "aac", "-b:a", "384k",  # pcm_s24le MP4'e mux edilemez
        "-ar", "48000",
        "-pix_fmt", "yuv420p",
        "-r", "24",
        "-shortest",
        "-movflags", "+faststart",
    ]

    cmd.append(output_path)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout for VFX (longer than static)
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr[-500:] if result.stderr else "FFmpeg VFX render error",
                "command": " ".join(cmd)
            }
        
        file_size = os.path.getsize(output_path)
        probe_info = probe_media(output_path)
        
        return {
            "success": True,
            "output_path": output_path,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "duration": probe_info.get("duration"),
            "vfx_enabled": True,
            "vfx_effects": effects,
            "encoding": {
                "video_codec": "H.264",
                "audio_codec": "AAC 384k",
                "resolution": "1920x1080",
                "fps": 24,
                "pixel_format": "yuv420p"
            }
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg VFX timeout (>10 minutes)"}
    except FileNotFoundError:
        return {"success": False, "error": "FFmpeg not installed."}


def _find_ffprobe() -> str:
    """Find ffprobe executable, same logic as _find_ffmpeg."""
    global _FFPROBE_PATH
    if _FFPROBE_PATH:
        return _FFPROBE_PATH

    # Try PATH first
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            _FFPROBE_PATH = "ffprobe"
            return _FFPROBE_PATH
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: same directory as ffmpeg, or common Windows locations
    common_paths = [
        os.path.join("C:\\", "ffmpeg", "bin", "ffprobe.exe"),
        os.path.join("C:\\", "Program Files", "ffmpeg", "bin", "ffprobe.exe"),
        os.path.join("C:\\", "Program Files (x86)", "ffmpeg", "bin", "ffprobe.exe"),
        os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffprobe.exe"),
        os.path.join(os.path.expanduser("~"), "scoop", "shims", "ffprobe.exe"),
    ]
    for path in common_paths:
        if os.path.isfile(path):
            try:
                r = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    _FFPROBE_PATH = path
                    return _FFPROBE_PATH
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
    return None


def probe_media(file_path: str) -> dict:
    """Get media file info using ffprobe."""
    ffprobe = _find_ffprobe() or "ffprobe"
    try:
        cmd = [
            ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        # Use binary capture (not text=True) to avoid cp1254 decode errors
        # on filenames with non-ASCII / Turkish characters on Windows
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )

        if result.returncode == 0:
            raw = result.stdout.decode("utf-8", errors="replace")
            data = json.loads(raw)
            fmt = data.get("format", {})
            return {
                "duration": float(fmt.get("duration", 0)),
                "size_bytes": int(fmt.get("size", 0)),
                "format": fmt.get("format_name", "unknown"),
                "streams": len(data.get("streams", []))
            }
    except Exception:
        pass

    return {}


def get_audio_duration(audio_path: str) -> float:
    """
    Get audio duration in seconds.
    Tries ffprobe first; falls back to Python's wave module for WAV files.
    Falls back to mutagen for MP3/FLAC if available.
    """
    # 1) Try ffprobe
    info = probe_media(audio_path)
    dur = info.get("duration", 0)
    if dur and dur > 0:
        return dur

    # 2) Fallback: Python wave module (WAV only, lossless accurate)
    ext = os.path.splitext(audio_path)[1].lower()
    if ext == ".wav":
        try:
            import wave
            with wave.open(audio_path, "rb") as wf:
                frames = wf.getnframes()
                rate   = wf.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass

    # 3) Fallback: mutagen (handles MP3, FLAC, etc.)
    try:
        from mutagen import File as MutagenFile
        mf = MutagenFile(audio_path)
        if mf and mf.info and hasattr(mf.info, "length") and mf.info.length > 0:
            return mf.info.length
    except Exception:
        pass

    return 0



def _find_ffmpeg() -> str:
    """Find FFmpeg executable, checking PATH and common Windows locations."""
    global _FFMPEG_PATH
    if _FFMPEG_PATH:
        return _FFMPEG_PATH

    # Try PATH first
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            _FFMPEG_PATH = "ffmpeg"
            return _FFMPEG_PATH
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: common Windows install locations
    common_paths = [
        os.path.join("C:\\", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join("C:\\", "Program Files", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join("C:\\", "Program Files (x86)", "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg.exe"),
        os.path.join(os.path.expanduser("~"), "scoop", "shims", "ffmpeg.exe"),
    ]

    for path in common_paths:
        if os.path.isfile(path):
            try:
                result = subprocess.run(
                    [path, "-version"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    _FFMPEG_PATH = path
                    return _FFMPEG_PATH
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

    return None


def get_ffmpeg_cmd() -> str:
    """Get the FFmpeg command/path to use. Returns 'ffmpeg' or full path."""
    return _find_ffmpeg() or "ffmpeg"


def check_ffmpeg() -> dict:
    """Check if FFmpeg is available and return version info."""
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        try:
            result = subprocess.run(
                [ffmpeg, "-version"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return {"available": True, "version": version_line}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return {"available": False, "version": None}


if __name__ == "__main__":
    print("ğŸ¬ MP4 Render Pipeline")
    print("=" * 40)
    
    status = check_ffmpeg()
    if status["available"]:
        print(f"  âœ… FFmpeg: {status['version']}")
    else:
        print("  âŒ FFmpeg not found!")
    
    print()
    print("Usage: render_mp4('frame.jpg', 'beat.wav', 'output.mp4')")

