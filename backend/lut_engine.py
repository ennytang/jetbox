"""
JETBOX v3 â€” Night Vision LUT Engine
Pillow + NumPy color matrix transforms
Presets: RAGE (military green) / MELODIC (pink haze)
"""

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import os
import json

# â”€â”€â”€ LUT PRESETS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

LUT_PRESETS = {
    "rage": {
        "name": "RAGE â€” Emerald Night",
        "color_matrix": [
            # Emerald/zÃ¼mrÃ¼t green â€” deeper, darker green than neon
            # R_out = 0.08*R + 0.08*G + 0.03*B  (red heavily suppressed)
            # G_out = 0.12*R + 0.70*G + 0.10*B  (green dominant but not neon)
            # B_out = 0.03*R + 0.12*G + 0.06*B  (slight teal undertone)
            [0.08, 0.08, 0.03],
            [0.12, 0.70, 0.10],
            [0.03, 0.12, 0.06],
        ],
        "brightness": -20,
        "contrast": 1.20,
        "grain_intensity": 0.035,
        "vignette_strength": 0.20,
        "tint": (0, 180, 60),  # Emerald tint overlay (darker green)
        "tint_opacity": 0.10,
    },
    "melodic": {
        "name": "MELODIC â€” Pink Haze",
        "color_matrix": [
            # R_out = 0.75*R + 0.20*G + 0.20*B  (red/pink boosted)
            # G_out = 0.10*R + 0.40*G + 0.10*B  (green suppressed)
            # B_out = 0.15*R + 0.15*G + 0.55*B  (blue tint)
            [0.75, 0.20, 0.20],
            [0.10, 0.40, 0.10],
            [0.15, 0.15, 0.55],
        ],
        "brightness": 10,
        "contrast": 1.10,
        "grain_intensity": 0.03,
        "vignette_strength": 0.4,
        "tint": (255, 105, 180),  # Pink tint overlay
        "tint_opacity": 0.10,
    },
}

# â”€â”€â”€ 4K UPSCALE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def upscale_to_4k(img: Image.Image, target_long_edge: int = 3840) -> Image.Image:
    """
    Upscale image to 4K (3840px long edge) if smaller.
    Uses LANCZOS for high-quality interpolation.
    Improves crop/fit quality for final output sizes.
    """
    w, h = img.size
    if max(w, h) >= target_long_edge:
        return img
    scale = target_long_edge / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


# â”€â”€â”€ TARGET RESOLUTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

VIDEO_SIZE = (1920, 1080)      # YouTube video frame
THUMBNAIL_SIZE = (1280, 720)   # YouTube thumbnail


# â”€â”€â”€ CORE LUT FUNCTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def apply_color_matrix(img_array: np.ndarray, matrix: list) -> np.ndarray:
    """Apply 3x3 color transformation matrix to image array."""
    mat = np.array(matrix, dtype=np.float32)
    # img_array shape: (H, W, 3)
    h, w, c = img_array.shape
    flat = img_array.reshape(-1, 3).astype(np.float32)
    transformed = flat @ mat.T
    transformed = np.clip(transformed, 0, 255).astype(np.uint8)
    return transformed.reshape(h, w, c)


def apply_brightness_contrast(img_array: np.ndarray, brightness: int, contrast: float) -> np.ndarray:
    """Adjust brightness and contrast."""
    arr = img_array.astype(np.float32)
    # Contrast: scale around midpoint
    arr = (arr - 128) * contrast + 128
    # Brightness
    arr = arr + brightness
    return np.clip(arr, 0, 255).astype(np.uint8)


def apply_grain(img_array: np.ndarray, intensity: float) -> np.ndarray:
    """Add film grain noise overlay."""
    noise = np.random.normal(0, intensity * 255, img_array.shape).astype(np.float32)
    result = img_array.astype(np.float32) + noise
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_vignette(img: Image.Image, strength: float) -> Image.Image:
    """Apply radial vignette darkening effect."""
    w, h = img.size
    # Create radial gradient mask
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    
    cx, cy = w // 2, h // 2
    max_radius = int((w**2 + h**2) ** 0.5 / 2)
    
    steps = 80
    for i in range(steps, 0, -1):
        radius = int(max_radius * i / steps)
        # Outer = dark (low value), inner = bright (high value)
        val = int(255 * (1 - strength * (i / steps) ** 1.5))
        val = max(0, min(255, val))
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=val
        )
    
    # Apply mask: darken image where mask is dark
    img_array = np.array(img).astype(np.float32)
    mask_array = np.array(mask).astype(np.float32) / 255.0
    mask_3d = np.stack([mask_array] * 3, axis=-1)
    
    result = img_array * mask_3d
    return Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))


def apply_tint_overlay(img_array: np.ndarray, tint_color: tuple, opacity: float) -> np.ndarray:
    """Apply solid color tint overlay with opacity."""
    tint = np.array(tint_color, dtype=np.float32)
    result = img_array.astype(np.float32) * (1 - opacity) + tint * opacity
    return np.clip(result, 0, 255).astype(np.uint8)


def fit_to_size(img: Image.Image, target_size: tuple) -> Image.Image:
    """
    Center-crop/pad image to target size.
    Strategy: resize to cover target, then center-crop.
    """
    tw, th = target_size
    iw, ih = img.size
    
    # Calculate scale to cover entire target
    scale = max(tw / iw, th / ih)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Center crop
    left = (new_w - tw) // 2
    top = (new_h - th) // 2
    img_cropped = img_resized.crop((left, top, left + tw, top + th))
    
    return img_cropped


def crop_and_compose(
    img: Image.Image,
    crop_x: float,
    crop_y: float,
    crop_size: float,
) -> Image.Image:
    """
    Crop a square region from artwork and compose onto 1920x1080 black frame.
    
    Args:
        img: Source artwork (any size)
        crop_x: Left edge of crop box as fraction (0.0 - 1.0) of image width
        crop_y: Top edge of crop box as fraction (0.0 - 1.0) of image height
        crop_size: Size of crop box as fraction of image's smaller dimension
    
    Returns:
        1920x1080 image with cropped square (1080x1080) centered on black background
    """
    iw, ih = img.size
    
    # Calculate crop box in pixels
    base_dim = min(iw, ih)
    box_px = int(base_dim * crop_size)
    box_px = max(50, min(box_px, min(iw, ih)))  # Clamp
    
    left = int(iw * crop_x)
    top = int(ih * crop_y)
    
    # Clamp to image bounds
    left = max(0, min(left, iw - box_px))
    top = max(0, min(top, ih - box_px))
    
    # Crop square
    cropped = img.crop((left, top, left + box_px, top + box_px))
    
    # Resize to 1080x1080
    square = cropped.resize((1080, 1080), Image.LANCZOS)
    
    # Compose onto 1920x1080 black frame (centered)
    frame = Image.new('RGB', (1920, 1080), (0, 0, 0))
    paste_x = (1920 - 1080) // 2  # 420px from left
    frame.paste(square, (paste_x, 0))
    
    return frame


def crop_and_compose_thumbnail(
    img: Image.Image,
    crop_x: float,
    crop_y: float,
    crop_size: float,
) -> Image.Image:
    """Same as crop_and_compose but for 1280x720 thumbnail."""
    iw, ih = img.size
    
    base_dim = min(iw, ih)
    box_px = int(base_dim * crop_size)
    box_px = max(50, min(box_px, min(iw, ih)))
    
    left = int(iw * crop_x)
    top = int(ih * crop_y)
    left = max(0, min(left, iw - box_px))
    top = max(0, min(top, ih - box_px))
    
    cropped = img.crop((left, top, left + box_px, top + box_px))
    square = cropped.resize((720, 720), Image.LANCZOS)
    
    frame = Image.new('RGB', (1280, 720), (0, 0, 0))
    paste_x = (1280 - 720) // 2  # 280px from left
    frame.paste(square, (paste_x, 0))
    
    return frame


# â”€â”€â”€ LUT-ONLY (NO CROP/RESIZE) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def apply_lut_only(input_path: str, preset_name: str, output_dir: str) -> str:
    """
    Apply LUT to image WITHOUT any cropping or resizing.
    Returns the original image dimensions with LUT applied.
    Used for crop tool preview.
    """
    preset_name = preset_name.lower()
    if preset_name not in LUT_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}")
    
    preset = LUT_PRESETS[preset_name]
    img = Image.open(input_path).convert('RGB')
    
    # Auto 4K upscale for better quality
    img = upscale_to_4k(img)
    
    arr = np.array(img)
    arr = apply_color_matrix(arr, preset["color_matrix"])
    arr = apply_brightness_contrast(arr, preset["brightness"], preset["contrast"])
    arr = apply_tint_overlay(arr, preset["tint"], preset["tint_opacity"])
    arr = apply_grain(arr, preset["grain_intensity"])
    
    processed = Image.fromarray(arr)
    processed = apply_vignette(processed, preset["vignette_strength"])
    
    import time
    filename = f"lut_preview_{int(time.time())}.jpg"
    output_path = os.path.join(output_dir, filename)
    processed.save(output_path, "JPEG", quality=85)
    
    return output_path


# â”€â”€â”€ MAIN LUT PIPELINE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def process_artwork(
    input_path: str,
    preset_name: str,
    output_dir: str,
    beat_name: str = "output",
    crop: dict = None
) -> dict:
    """
    Full LUT pipeline:
    1. Load artwork
    2. If crop provided: crop square + compose onto black 1920x1080
       If no crop: fit to 1920x1080 (legacy mode)
    3. Apply color matrix
    4. Apply brightness/contrast
    5. Apply tint overlay
    6. Apply grain
    7. Apply vignette
    8. Save video frame + thumbnail
    
    crop dict: {"x": 0.0-1.0, "y": 0.0-1.0, "size": 0.0-1.0}
    """
    preset_name = preset_name.lower()
    if preset_name not in LUT_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. Use 'rage' or 'melodic'.")
    
    preset = LUT_PRESETS[preset_name]
    
    # Load image
    img = Image.open(input_path).convert('RGB')
    
    # Auto 4K upscale for better quality
    img = upscale_to_4k(img)
    original_size = img.size
    
    results = {}
    
    for label, target_size in [("video", VIDEO_SIZE), ("thumbnail", THUMBNAIL_SIZE)]:
        # Step 1: Compose frame
        if crop:
            if label == "video":
                fitted = crop_and_compose(img, crop["x"], crop["y"], crop["size"])
            else:
                fitted = crop_and_compose_thumbnail(img, crop["x"], crop["y"], crop["size"])
        else:
            fitted = fit_to_size(img, target_size)
        
        # Step 2: Color matrix
        arr = np.array(fitted)
        arr = apply_color_matrix(arr, preset["color_matrix"])
        
        # Step 3: Brightness / contrast
        arr = apply_brightness_contrast(arr, preset["brightness"], preset["contrast"])
        
        # Step 4: Tint overlay
        arr = apply_tint_overlay(arr, preset["tint"], preset["tint_opacity"])
        
        # Step 5: Grain
        arr = apply_grain(arr, preset["grain_intensity"])
        
        # Step 6: Vignette (needs PIL Image)
        processed = Image.fromarray(arr)
        processed = apply_vignette(processed, preset["vignette_strength"])
        
        # Save
        safe_name = beat_name.replace(" ", "_").replace('"', '').replace("'", "")
        filename = f"{safe_name}_{preset_name}_{label}.jpg"
        output_path = os.path.join(output_dir, filename)
        
        processed.save(output_path, "JPEG", quality=95)
        results[label] = {
            "path": output_path,
            "size": target_size,
            "filename": filename
        }
    
    return {
        "preset": preset_name,
        "preset_display": preset["name"],
        "original_size": original_size,
        "outputs": results,
        "input_path": input_path
    }


def get_available_presets() -> dict:
    """Return available LUT presets with display info."""
    return {
        key: {
            "name": val["name"],
            "tint_hex": "#{:02x}{:02x}{:02x}".format(*val["tint"]),
            "contrast": val["contrast"],
            "grain": val["grain_intensity"],
            "vignette": val["vignette_strength"],
        }
        for key, val in LUT_PRESETS.items()
    }


def list_artworks(artworks_dir: str) -> dict:
    """
    Scan ARTWORKS/ directory for available images.
    Expected structure:
        ARTWORKS/
            RAGE/
                img1.jpg
            MELODIC/
                img2.png
    """
    result = {}
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    if not os.path.exists(artworks_dir):
        return result
    
    for vibe_folder in os.listdir(artworks_dir):
        vibe_path = os.path.join(artworks_dir, vibe_folder)
        if not os.path.isdir(vibe_path):
            continue
        
        vibe_key = vibe_folder.upper()
        images = []
        
        for fname in sorted(os.listdir(vibe_path)):
            ext = os.path.splitext(fname)[1].lower()
            if ext in valid_extensions:
                fpath = os.path.join(vibe_path, fname)
                try:
                    with Image.open(fpath) as im:
                        w, h = im.size
                except Exception:
                    w, h = 0, 0
                
                images.append({
                    "filename": fname,
                    "path": fpath,
                    "width": w,
                    "height": h,
                    "size_kb": round(os.path.getsize(fpath) / 1024, 1)
                })
        
        result[vibe_key] = {
            "count": len(images),
            "images": images
        }
    
    return result


# â”€â”€â”€ CLI TESTING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

if __name__ == "__main__":
    print("ğŸ”¬ Night Vision LUT Engine")
    print("=" * 40)
    
    presets = get_available_presets()
    for key, info in presets.items():
        print(f"  [{key.upper()}] {info['name']}")
        print(f"    Tint: {info['tint_hex']} | Contrast: {info['contrast']} | Grain: {info['grain']}")
    
    print()
    print("Usage: process_artwork('input.jpg', 'rage', './output/', 'my_beat')")

