"""
JETBOX v3 â€” Video Effects Engine
FFmpeg filter chain builder for periodic video effects.
Zoom, glitch, flash, shake, etc. applied at timed intervals.

Usage:
    from video_effects import EFFECTS_LIBRARY, build_filter_chain
    
    chain = build_filter_chain(
        total_duration=180,
        interval=10,
        effect_duration=0.5,
        effects=["zoom_pulse", "rgb_glitch"],
        order="sequential"
    )
    # → Returns FFmpeg -filter_complex string
"""

import math

# Aktif video kare boyutu â€” build_filter_chain() cagrisinda guncellenir.
# zoom_pulse ve shake efektleri cozunurluk-bagimsiz calismak icin bunu kullanir.
_FRAME_W = 1920
_FRAME_H = 1080


# ═══════════════════════════════════════════════════════════════
# EFFECTS LIBRARY
# ═══════════════════════════════════════════════════════════════

EFFECTS_LIBRARY = {
    "zoom_pulse": {
        "name": "Zoom Pulse",
        "icon": "ğŸ”",
        "description": "Smooth zoom in and snap back",
        "category": "motion",
        "intensity": "medium",
    },
    "rgb_glitch": {
        "name": "RGB Glitch",
        "icon": "ğŸ“º",
        "description": "RGB channel split and shift",
        "category": "glitch",
        "intensity": "high",
    },
    "brightness_flash": {
        "name": "Brightness Flash",
        "icon": "⚡",
        "description": "Quick white brightness flash",
        "category": "color",
        "intensity": "medium",
    },
    "shake": {
        "name": "Camera Shake",
        "icon": "ğŸ“³",
        "description": "Rapid camera vibration",
        "category": "motion",
        "intensity": "high",
    },
    "color_invert": {
        "name": "Color Invert",
        "icon": "ğŸ”„",
        "description": "Brief negative/inverted flash",
        "category": "color",
        "intensity": "medium",
    },
    "hue_rotate": {
        "name": "Hue Rotate",
        "icon": "ğŸŒˆ",
        "description": "Rapid hue spin through spectrum",
        "category": "color",
        "intensity": "medium",
    },
    "blur_pulse": {
        "name": "Blur Pulse",
        "icon": "ğŸ’«",
        "description": "Blur out and sharpen back",
        "category": "distortion",
        "intensity": "low",
    },
    "scanline_sweep": {
        "name": "Scanline Sweep",
        "icon": "ğŸ“¡",
        "description": "Horizontal scanline bar sweep",
        "category": "glitch",
        "intensity": "low",
    },
}


# ═══════════════════════════════════════════════════════════════
# EFFECT FILTER GENERATORS
# ═══════════════════════════════════════════════════════════════

def _zoom_pulse_filter(t_start: float, duration: float, idx: int) -> str:
    """Zoom in smoothly then snap back.

    NOT: scale/setpts filtreleri timeline (enable=) desteklemez; eski surum
    bu yuzden FFmpeg'i dusuruyordu. Zoom carpani pencere disinda 1.0'a
    dondugu icin enable'a gerek yok. Cikti boyutu _FRAME_W x _FRAME_H'e
    sabitlenir (2K dahil her cozunurlukte calisir).
    """
    t_end = t_start + duration
    mid = t_start + duration / 2
    # z(t): pencere icinde 0..0.15..0 ucgen rampasi, disinda 0
    z = (
        f"(1+0.15*if(between(t\\,{t_start}\\,{t_end})\\,"
        f"1-abs((t-{mid})/{duration/2})\\,0))"
    )
    return (
        f"[v{idx}]scale=w='trunc(iw*{z}/2)*2':h='trunc(ih*{z}/2)*2':eval=frame,"
        f"crop={_FRAME_W}:{_FRAME_H}[v{idx+1}]"
    )


def _rgb_glitch_filter(t_start: float, duration: float, idx: int) -> str:
    """RGB channel shift for glitch effect."""
    t_end = t_start + duration
    return (
        f"[v{idx}]rgbashift=rh=-12:rv=4:gh=0:gv=0:bh=10:bv=-3"
        f":enable='between(t,{t_start},{t_end})'[v{idx+1}]"
    )


def _brightness_flash_filter(t_start: float, duration: float, idx: int) -> str:
    """Quick brightness flash â€” ramp up then down."""
    t_end = t_start + duration
    mid = t_start + duration / 2
    return (
        f"[v{idx}]eq=brightness="
        f"if(between(t\\,{t_start}\\,{mid})\\,"
        f"0.4*(t-{t_start})/{duration/2}\\,"
        f"if(between(t\\,{mid}\\,{t_end})\\,"
        f"0.4*(1-(t-{mid})/{duration/2})\\,0))"
        f":eval=frame[v{idx+1}]"
    )


def _shake_filter(t_start: float, duration: float, idx: int) -> str:
    """Camera shake â€” random-ish crop offset.

    NOT: scale filtresi timeline (enable=) desteklemez; sarsinti offset'i
    pencere disinda 0'a sabitlenerek ayni etki elde edilir.
    Cozunurluk-bagimsiz: _FRAME_W/_FRAME_H kullanilir.
    """
    t_end = t_start + duration
    cw, ch = _FRAME_W - 20, _FRAME_H - 12
    return (
        f"[v{idx}]crop=w={cw}:h={ch}:"
        f"x='10+if(between(t\\,{t_start}\\,{t_end})\\,10*sin(t*45)\\,0)':"
        f"y='6+if(between(t\\,{t_start}\\,{t_end})\\,8*cos(t*37)\\,0)',"
        f"scale={_FRAME_W}:{_FRAME_H}[v{idx+1}]"
    )


def _color_invert_filter(t_start: float, duration: float, idx: int) -> str:
    """Brief color inversion."""
    t_end = t_start + duration
    return (
        f"[v{idx}]negate"
        f":enable='between(t,{t_start},{t_end})'[v{idx+1}]"
    )


def _hue_rotate_filter(t_start: float, duration: float, idx: int) -> str:
    """Rapid hue rotation through spectrum."""
    t_end = t_start + duration
    return (
        f"[v{idx}]hue=h=360*(t-{t_start})/{duration}"
        f":enable='between(t,{t_start},{t_end})'[v{idx+1}]"
    )


def _blur_pulse_filter(t_start: float, duration: float, idx: int) -> str:
    """Blur out then sharpen back."""
    t_end = t_start + duration
    mid = t_start + duration / 2
    return (
        f"[v{idx}]boxblur="
        f"lr=if(lt(t-{t_start},{duration/2}),"
        f"15*(t-{t_start})/{duration/2},"
        f"15*(1-(t-{mid})/{duration/2}))"
        f":enable='between(t,{t_start},{t_end})'[v{idx+1}]"
    )


def _scanline_sweep_filter(t_start: float, duration: float, idx: int) -> str:
    """Horizontal bright scanline bar sweeping down."""
    t_end = t_start + duration
    return (
        f"[v{idx}]drawbox=x=0:y=(t-{t_start})/{duration}*ih:"
        f"w=iw:h=4:color=white@0.6:t=fill"
        f":enable='between(t,{t_start},{t_end})'[v{idx+1}]"
    )


# Map effect keys to generator functions
_EFFECT_GENERATORS = {
    "zoom_pulse": _zoom_pulse_filter,
    "rgb_glitch": _rgb_glitch_filter,
    "brightness_flash": _brightness_flash_filter,
    "shake": _shake_filter,
    "color_invert": _color_invert_filter,
    "hue_rotate": _hue_rotate_filter,
    "blur_pulse": _blur_pulse_filter,
    "scanline_sweep": _scanline_sweep_filter,
}


# ═══════════════════════════════════════════════════════════════
# FILTER CHAIN BUILDER
# ═══════════════════════════════════════════════════════════════

def build_filter_chain(
    total_duration: float,
    interval: float = 10.0,
    effect_duration: float = 0.5,
    effects: list = None,
    order: str = "sequential",
    frame_width: int = 1920,
    frame_height: int = 1080,
) -> str:
    """
    Build FFmpeg -filter_complex string for periodic video effects.
    
    Args:
        total_duration: Video length in seconds
        interval: Seconds between effects
        effect_duration: Duration of each effect in seconds
        effects: List of effect keys (from EFFECTS_LIBRARY)
        order: "sequential" (cycle through) or "random"
    
    Returns:
        FFmpeg filter_complex string, or empty string if no effects
    """
    global _FRAME_W, _FRAME_H
    _FRAME_W = int(frame_width) if frame_width else 1920
    _FRAME_H = int(frame_height) if frame_height else 1080

    if not effects:
        return ""

    # Guard: total_duration must be a positive number
    if not total_duration or total_duration <= 0:
        return ""

    # Normalize effects â€” accept both string keys and dicts with a "key" field
    normalized = []
    for e in effects:
        if isinstance(e, str):
            normalized.append(e)
        elif isinstance(e, dict) and e.get("key"):
            normalized.append(e["key"])
    if not normalized:
        return ""

    # Validate against known generators
    valid_effects = [e for e in normalized if e in _EFFECT_GENERATORS]
    if not valid_effects:
        return ""

    # Calculate trigger points
    triggers = []
    t = interval  # First effect at interval, not at 0
    while t + effect_duration < total_duration:
        triggers.append(t)
        t += interval
    
    if not triggers:
        return ""
    
    # Build filter chain
    filters = []
    
    # Start: label input as [v0]
    # Each effect takes [vN] and outputs [vN+1]
    idx = 0
    
    for i, trigger_time in enumerate(triggers):
        if order == "sequential":
            effect_key = valid_effects[i % len(valid_effects)]
        else:
            # "random" â€” pseudo-random based on index
            effect_key = valid_effects[hash(str(i)) % len(valid_effects)]
        
        gen = _EFFECT_GENERATORS[effect_key]
        filt = gen(trigger_time, effect_duration, idx)
        filters.append(filt)
        idx += 1
    
    if not filters:
        return ""
    
    # Build full chain: [0:v] → [v0] → effect → [v1] → effect → [v2] → ... → [vN]
    chain = f"[0:v]copy[v0];{';'.join(filters)}"
    final_label = f"v{idx}"
    
    return chain, final_label


def get_effects_list() -> list:
    """Return effects library as a list for API response."""
    return [
        {"key": key, **info}
        for key, info in EFFECTS_LIBRARY.items()
    ]


def get_effect_timeline(
    total_duration: float,
    interval: float,
    effect_duration: float,
    effects: list,
    order: str = "sequential",
) -> list:
    """
    Generate a timeline showing when each effect will trigger.
    Used for preview in the UI.
    """
    if not effects:
        return []
    
    valid = [e for e in effects if e in EFFECTS_LIBRARY]
    if not valid:
        return []
    
    timeline = []
    t = interval
    i = 0
    while t + effect_duration < total_duration:
        if order == "sequential":
            effect_key = valid[i % len(valid)]
        else:
            effect_key = valid[hash(str(i)) % len(valid)]
        
        timeline.append({
            "time": round(t, 1),
            "effect": effect_key,
            "name": EFFECTS_LIBRARY[effect_key]["name"],
            "icon": EFFECTS_LIBRARY[effect_key]["icon"],
            "end": round(t + effect_duration, 1),
        })
        t += interval
        i += 1
    
    return timeline

