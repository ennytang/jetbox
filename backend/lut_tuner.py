"""
JETBOX v3 â€” LUT Tuner v2
Interactive parameter tuner with real-time preview.
Tkinter + Pillow + NumPy

Features:
    - 12+ effect sliders across 6 categories
    - 5 new effects: Chromatic Aberration, Duotone, Halation, Scanlines, Hue Shift
    - 4 selectable themes: DARK OPS, NEBULA, COCKPIT RED, PHANTOM GRID
    - Collapsible sections, keyboard shortcuts, status bar

Usage:
    python lut_tuner.py                        → Opens with default test image
    python lut_tuner.py path/to/image.jpg      → Opens with specific image
    python lut_tuner.py --preset rage           → Start from RAGE preset values
    python lut_tuner.py --theme nebula          → Start with NEBULA theme

Shortcuts:
    Ctrl+O  Load image    Ctrl+S  Save preview
    Ctrl+E  Export         Ctrl+R  Reset
"""

import sys
import os
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import numpy as np
from copy import deepcopy


# ═══════════════════════════════════════════════════════════════
# THEMES
# ═══════════════════════════════════════════════════════════════

THEMES = {
    "dark_ops": {
        "name": "⚡ DARK OPS",
        "bg": "#0a0a0f", "panel": "#0d0d14", "canvas": "#050508",
        "accent": "#00ff88", "dim": "#2a3a30", "text": "#d0d0d8",
        "trough": "#151f18", "section": "#44cc77",
        "btn_bg": "#121f18", "btn_accent": "#00aa55",
        "border": "#1a2a1f", "val": "#66aa80",
    },
    "nebula": {
        "name": "ğŸŒŒ NEBULA",
        "bg": "#08050f", "panel": "#0c0818", "canvas": "#060310",
        "accent": "#bf5fff", "dim": "#3a2a55", "text": "#d0c8e0",
        "trough": "#160f28", "section": "#9944dd",
        "btn_bg": "#150e25", "btn_accent": "#8833bb",
        "border": "#251a3a", "val": "#7755aa",
    },
    "cockpit_red": {
        "name": "ğŸ”´ COCKPIT RED",
        "bg": "#0f0808", "panel": "#140a0a", "canvas": "#0a0505",
        "accent": "#ff3344", "dim": "#4a2525", "text": "#e0d0d0",
        "trough": "#281212", "section": "#cc3344",
        "btn_bg": "#1f1010", "btn_accent": "#aa2233",
        "border": "#3a1818", "val": "#aa5050",
    },
    "phantom_grid": {
        "name": "ğŸ”· PHANTOM GRID",
        "bg": "#050a0c", "panel": "#080f12", "canvas": "#030808",
        "accent": "#00ffcc", "dim": "#254540", "text": "#d0e0e0",
        "trough": "#0f2020", "section": "#33ccaa",
        "btn_bg": "#0e1a1a", "btn_accent": "#22aa88",
        "border": "#153030", "val": "#559988",
    },
}


# ═══════════════════════════════════════════════════════════════
# PRESETS
# ═══════════════════════════════════════════════════════════════

PRESETS = {
    "rage": {
        "name": "RAGE â€” Emerald Night",
        "matrix_r": [0.08, 0.08, 0.03],
        "matrix_g": [0.12, 0.70, 0.10],
        "matrix_b": [0.03, 0.12, 0.06],
        "brightness": -20, "contrast": 1.20, "saturation": 1.05,
        "grain_intensity": 0.035, "grain_size": 1,
        "vignette_strength": 0.20,
        "tint_r": 0, "tint_g": 180, "tint_b": 60, "tint_opacity": 0.10,
        "glow_radius": 3, "glow_intensity": 0.15,
        "chromatic_shift": 0, "hue_shift": 0,
        "scanline_intensity": 0.0, "scanline_opacity": 1.0, "scanline_warp": 0.0,
        "halation_strength": 0.0,
        "duotone_intensity": 0.0,
        "duotone_shadow": [10, 30, 5],
        "duotone_highlight": [50, 255, 120],
    },
    "melodic": {
        "name": "MELODIC â€” Pink Haze",
        "matrix_r": [0.75, 0.20, 0.20],
        "matrix_g": [0.10, 0.40, 0.10],
        "matrix_b": [0.15, 0.15, 0.55],
        "brightness": 10, "contrast": 1.10, "saturation": 1.0,
        "grain_intensity": 0.03, "grain_size": 1,
        "vignette_strength": 0.40,
        "tint_r": 255, "tint_g": 105, "tint_b": 180, "tint_opacity": 0.10,
        "glow_radius": 0, "glow_intensity": 0.0,
        "chromatic_shift": 0, "hue_shift": 0,
        "scanline_intensity": 0.0, "scanline_opacity": 1.0, "scanline_warp": 0.0,
        "halation_strength": 0.0,
        "duotone_intensity": 0.0,
        "duotone_shadow": [40, 10, 60],
        "duotone_highlight": [255, 130, 200],
    },
}


# ═══════════════════════════════════════════════════════════════
# LUT PROCESSING FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def apply_color_matrix(arr, matrix):
    mat = np.array(matrix, dtype=np.float32)
    flat = arr.reshape(-1, 3).astype(np.float32)
    out = flat @ mat.T
    return np.clip(out, 0, 255).astype(np.uint8).reshape(arr.shape)


def apply_brightness_contrast(arr, brightness, contrast):
    a = arr.astype(np.float32)
    a = (a - 128) * contrast + 128 + brightness
    return np.clip(a, 0, 255).astype(np.uint8)


def apply_saturation(arr, saturation):
    if abs(saturation - 1.0) < 0.01:
        return arr
    a = arr.astype(np.float32)
    gray = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2])[:, :, np.newaxis]
    return np.clip(gray + saturation * (a - gray), 0, 255).astype(np.uint8)


def apply_hue_shift(arr, degrees):
    degrees = int(degrees)
    if degrees < 1:
        return arr
    img = Image.fromarray(arr).convert("HSV")
    h, s, v = img.split()
    h_arr = (np.array(h, dtype=np.int16) + int(degrees * 255 / 360)) % 256
    img = Image.merge("HSV", (Image.fromarray(h_arr.astype(np.uint8), "L"), s, v))
    return np.array(img.convert("RGB"))


def apply_duotone(arr, intensity, shadow_color, highlight_color):
    if intensity < 0.01:
        return arr
    a = arr.astype(np.float32)
    lum = (0.299 * a[:, :, 0] + 0.587 * a[:, :, 1] + 0.114 * a[:, :, 2]) / 255.0
    shadow = np.array(shadow_color, dtype=np.float32)
    highlight = np.array(highlight_color, dtype=np.float32)
    duo = shadow * (1 - lum[:, :, np.newaxis]) + highlight * lum[:, :, np.newaxis]
    return np.clip(a * (1 - intensity) + duo * intensity, 0, 255).astype(np.uint8)


def apply_tint_overlay(arr, tint_color, opacity):
    if opacity < 0.001:
        return arr
    tint = np.array(tint_color, dtype=np.float32)
    return np.clip(arr.astype(np.float32) * (1 - opacity) + tint * opacity, 0, 255).astype(np.uint8)


def apply_chromatic_aberration(arr, shift):
    shift = int(shift)
    if shift < 1:
        return arr
    result = arr.copy()
    result[:, :, 0] = np.roll(arr[:, :, 0], -shift, axis=1)
    result[:, :, 2] = np.roll(arr[:, :, 2], shift, axis=1)
    return result


def apply_grain(arr, intensity, grain_size=1):
    if intensity < 0.001:
        return arr
    h, w, c = arr.shape
    gs = max(1, int(grain_size))
    if gs > 1:
        sh, sw = max(1, h // gs), max(1, w // gs)
        small = np.random.normal(0, intensity * 255, (sh, sw, c)).astype(np.float32)
        noise = small.repeat(gs, axis=0).repeat(gs, axis=1)[:h, :w, :]
    else:
        noise = np.random.normal(0, intensity * 255, (h, w, c)).astype(np.float32)
    return np.clip(arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_scanlines(arr, value, opacity=1.0, warp=0.0):
    if value < 0.005:
        return arr
    h, w, _ = arr.shape
    step = max(2, int(2 + value * 8))
    darkness = max(0.3, 0.85 - value * 0.5) * max(0.05, opacity)

    # Build scanline mask
    mask = np.ones((h, w), dtype=np.float32)
    mask[::step, :] = 1.0 - darkness

    if warp > 0.01:
        # Barrel distortion warp â€” glitched TV fisheye
        y_idx, x_idx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = w / 2.0, h / 2.0
        nx = (x_idx - cx) / max(cx, 1)
        ny = (y_idx - cy) / max(cy, 1)
        r = np.sqrt(nx ** 2 + ny ** 2)
        warped_y = y_idx + warp * r * 8 * np.sin(x_idx * 0.025 + ny * 2)
        warped_y = np.clip(warped_y, 0, h - 1).astype(np.int32)
        mask = mask[warped_y, x_idx.astype(np.int32)]

    return np.clip(arr.astype(np.float32) * mask[:, :, np.newaxis], 0, 255).astype(np.uint8)


def apply_vignette(img, strength):
    if strength < 0.01:
        return img
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = w // 2, h // 2
    max_r = int((w ** 2 + h ** 2) ** 0.5 / 2)
    for i in range(60, 0, -1):
        r = int(max_r * i / 60)
        val = max(0, min(255, int(255 * (1 - strength * (i / 60) ** 1.5))))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=val)
    m = np.array(mask).astype(np.float32) / 255.0
    return Image.fromarray(np.clip(np.array(img).astype(np.float32) * m[:, :, np.newaxis], 0, 255).astype(np.uint8))


def apply_glow(img, radius, intensity):
    if radius < 1 or intensity < 0.01:
        return img
    blurred = img.filter(ImageFilter.GaussianBlur(radius=int(radius)))
    out = np.array(img).astype(np.float32) + np.array(blurred).astype(np.float32) * intensity
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def apply_halation(img, strength):
    if strength < 0.01:
        return img
    arr = np.array(img).astype(np.float32)
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    mask = np.clip((lum - 180) / 75, 0, 1)
    bright = arr * mask[:, :, np.newaxis]
    bright_img = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8))
    radius = max(5, min(img.size) // 20)
    blur_arr = np.array(bright_img.filter(ImageFilter.GaussianBlur(radius=radius))).astype(np.float32)
    blur_arr[:, :, 0] *= 1.15
    blur_arr[:, :, 2] *= 0.85
    return Image.fromarray(np.clip(arr + blur_arr * strength * 0.8, 0, 255).astype(np.uint8))


def process_full(source_arr, params):
    """Full LUT pipeline â€” all effects applied in order. All params use .get() for safety."""
    # Color matrix â€” use identity if missing
    matrix_r = params.get("matrix_r", [1.0, 0.0, 0.0])
    matrix_g = params.get("matrix_g", [0.0, 1.0, 0.0])
    matrix_b = params.get("matrix_b", [0.0, 0.0, 1.0])
    arr = apply_color_matrix(source_arr, [matrix_r, matrix_g, matrix_b])

    # Tone
    arr = apply_brightness_contrast(
        arr,
        params.get("brightness", 0),
        params.get("contrast", 1.0),
    )
    arr = apply_saturation(arr, params.get("saturation", 1.0))
    arr = apply_hue_shift(arr, params.get("hue_shift", 0))

    # Duotone
    arr = apply_duotone(
        arr,
        params.get("duotone_intensity", 0),
        params.get("duotone_shadow", [0, 0, 0]),
        params.get("duotone_highlight", [255, 255, 255]),
    )

    # Tint overlay
    tint_color = (
        params.get("tint_r", 0),
        params.get("tint_g", 0),
        params.get("tint_b", 0),
    )
    arr = apply_tint_overlay(arr, tint_color, params.get("tint_opacity", 0.0))

    # Character FX
    arr = apply_chromatic_aberration(arr, params.get("chromatic_shift", 0))
    arr = apply_grain(
        arr,
        params.get("grain_intensity", 0.0),
        params.get("grain_size", 1),
    )
    arr = apply_scanlines(
        arr,
        params.get("scanline_intensity", 0),
        opacity=params.get("scanline_opacity", 1.0),
        warp=params.get("scanline_warp", 0.0),
    )

    img = Image.fromarray(arr)
    img = apply_vignette(img, params.get("vignette_strength", 0.0))
    img = apply_glow(
        img,
        params.get("glow_radius", 0),
        params.get("glow_intensity", 0.0),
    )
    img = apply_halation(img, params.get("halation_strength", 0))
    return img


def apply_master_blend(original: Image.Image, processed: Image.Image, master: float) -> Image.Image:
    """
    Crossfade original → full LUT output. master=0 → original, master=1 → processed.
    """
    m = max(0.0, min(1.0, float(master)))
    o = original.convert("RGB")
    p = processed.convert("RGB")
    if m <= 0.0:
        return o.copy()
    if m >= 1.0:
        return p.copy()
    return Image.blend(o, p, m)


# ═══════════════════════════════════════════════════════════════
# CUSTOM PRESET PERSISTENCE
# ═══════════════════════════════════════════════════════════════

CUSTOM_PRESETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_presets.json")
MAX_CUSTOM_PRESETS = 5


def load_custom_presets() -> dict:
    """Load custom presets from JSON file."""
    if os.path.exists(CUSTOM_PRESETS_PATH):
        try:
            with open(CUSTOM_PRESETS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
        except Exception:
            pass
    return {}


def save_custom_presets(presets: dict):
    """Save custom presets to JSON file."""
    with open(CUSTOM_PRESETS_PATH, "w", encoding="utf-8") as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)


def get_all_presets() -> dict:
    """Return merged dict of built-in + custom presets."""
    merged = deepcopy(PRESETS)
    merged.update(load_custom_presets())
    return merged


# ═══════════════════════════════════════════════════════════════
# TUNER GUI
# ═══════════════════════════════════════════════════════════════

class LUTTuner:
    PREVIEW_MAX = 600

    def __init__(self, root, image_path=None, preset_name="rage", theme_name="dark_ops"):
        self.root = root
        self.theme_name = theme_name if theme_name in THEMES else "dark_ops"
        self.theme = THEMES[self.theme_name]
        all_presets = get_all_presets()
        self.preset_name = preset_name if preset_name in all_presets else "rage"
        self.params = deepcopy(all_presets[self.preset_name])
        self.initial_params = deepcopy(self.params)
        self.source_img = None
        self.source_arr = None
        self.full_res_arr = None
        self.preview_scale = 1.0
        self._photo = None
        self._update_id = None
        self._undo_stack = []
        self._undo_gesture_open = False

        if image_path and os.path.exists(image_path):
            self._load_image(image_path)
        else:
            self._create_test_image()

        self._build_ui()
        # Bind keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self._load_new_image())
        self.root.bind("<Control-s>", lambda e: self._save_preview())
        self.root.bind("<Control-e>", lambda e: self._export())
        self.root.bind("<Control-r>", lambda e: self._reset())
        self.root.bind("<Control-z>", lambda e: self._undo())
        # Deferred first preview to avoid sizing issues
        self.root.after(100, self._update_preview)

    # â”€â”€â”€ IMAGE LOADING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _upscale_to_4k(self, img):
        """Upscale image to 4K (3840px long edge) if smaller."""
        w, h = img.size
        target = 3840
        if max(w, h) >= target:
            return img
        scale = target / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        return img.resize((new_w, new_h), Image.LANCZOS)

    def _load_image(self, path):
        img = Image.open(path).convert("RGB")
        # Auto 4K upscale
        img_4k = self._upscale_to_4k(img)
        self.full_res_arr = np.array(img_4k)
        # Downscale for preview
        w, h = img_4k.size
        scale = min(self.PREVIEW_MAX / w, self.PREVIEW_MAX / h, 1.0)
        if scale < 1.0:
            preview = img_4k.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        else:
            preview = img_4k
        self.preview_scale = scale
        self.source_img = preview
        self.source_arr = np.array(preview)
        self.root.title(f"JETBOX LUT Tuner â€” {os.path.basename(path)} [{img_4k.size[0]}Ã-{img_4k.size[1]}]")

    def _create_test_image(self):
        w, h = 500, 400
        x = np.arange(w, dtype=np.float32).reshape(1, w).repeat(h, axis=0)
        y = np.arange(h, dtype=np.float32).reshape(h, 1).repeat(w, axis=1)
        r = (255 * x / w)
        g = (255 * y / h)
        b = (128 + 127 * np.sin(x * 0.05) * np.cos(y * 0.05))
        arr = np.stack([r, g, b], axis=-1).astype(np.uint8)
        self.source_img = Image.fromarray(arr)
        self.source_arr = arr
        self.full_res_arr = arr

    # â”€â”€â”€ UI BUILD â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _build_ui(self):
        t = self.theme
        self.root.title("JETBOX LUT Tuner v2")
        self.root.configure(bg=t["bg"])

        self.sliders = {}
        self.value_labels = {}
        self._section_content = None

        # â”€â”€ Main PanedWindow â”€â”€
        self._paned = tk.PanedWindow(
            self.root, orient=tk.HORIZONTAL, sashwidth=5,
            bg=t["border"], sashrelief=tk.FLAT, opaqueresize=True,
        )
        self._paned.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 0))

        # LEFT: Preview
        left = tk.Frame(self._paned, bg=t["bg"])
        self._paned.add(left, stretch="always", minsize=300)

        # Toolbar
        toolbar = tk.Frame(left, bg=t["panel"])
        toolbar.pack(fill=tk.X, pady=(0, 4))

        tk.Button(toolbar, text="ğŸ“‚ Load", command=self._load_new_image,
                  bg=t["btn_bg"], fg=t["text"], activebackground=t["dim"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="ğŸ”„ Reset", command=self._reset,
                  bg=t["btn_bg"], fg=t["text"], activebackground=t["dim"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="ğŸ“‹ Export", command=self._export,
                  bg=t["btn_accent"], fg="#ffffff", activebackground=t["accent"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="ğŸ’¾ Save IMG", command=self._save_preview,
                  bg=t["btn_bg"], fg=t["text"], activebackground=t["dim"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="⚡ Save Preset", command=self._save_custom_preset,
                  bg=t["btn_bg"], fg=t["accent"], activebackground=t["dim"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="🗑", command=self._delete_custom_preset,
                  bg=t["btn_bg"], fg="#ff4444", activebackground=t["dim"],
                  relief=tk.FLAT, padx=4, pady=3, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="â†© Undo", command=self._undo,
                  bg=t["btn_bg"], fg=t["dim"], activebackground=t["dim"],
                  relief=tk.FLAT, padx=6, pady=3, font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=1)

        # Theme selector
        tk.Label(toolbar, text="  Theme:", bg=t["panel"], fg=t["dim"],
                 font=("Segoe UI", 8)).pack(side=tk.RIGHT)
        self.theme_var = tk.StringVar(value=self.theme_name)
        theme_menu = ttk.Combobox(toolbar, textvariable=self.theme_var,
                                  values=list(THEMES.keys()), state="readonly", width=12)
        theme_menu.pack(side=tk.RIGHT, padx=2)
        theme_menu.bind("<<ComboboxSelected>>", self._on_theme_change)

        # Preset selector (built-in + custom)
        all_preset_names = list(PRESETS.keys()) + [f"⚡{k}" for k in load_custom_presets().keys()]
        tk.Label(toolbar, text="Preset:", bg=t["panel"], fg=t["dim"],
                 font=("Segoe UI", 8)).pack(side=tk.RIGHT)
        self.preset_var = tk.StringVar(value=self.preset_name)
        self._preset_menu = ttk.Combobox(toolbar, textvariable=self.preset_var,
                                   values=all_preset_names, state="readonly", width=14)
        self._preset_menu.pack(side=tk.RIGHT, padx=2)
        self._preset_menu.bind("<<ComboboxSelected>>", self._on_preset_change)

        # Canvas
        self.canvas = tk.Canvas(left, bg=t["canvas"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # RIGHT: Scrollable control panel
        right = tk.Frame(self._paned, bg=t["panel"])
        self._paned.add(right, width=400, minsize=320, stretch="never")

        ctrl_canvas = tk.Canvas(right, bg=t["panel"], highlightthickness=0, width=380)
        scrollbar = tk.Scrollbar(right, orient=tk.VERTICAL, command=ctrl_canvas.yview,
                                 bg=t["border"], troughcolor=t["bg"])
        self.ctrl_frame = tk.Frame(ctrl_canvas, bg=t["panel"])
        self.ctrl_frame.bind("<Configure>",
                             lambda e: ctrl_canvas.configure(scrollregion=ctrl_canvas.bbox("all")))
        ctrl_canvas.create_window((0, 0), window=self.ctrl_frame, anchor=tk.NW)
        ctrl_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ctrl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mousewheel only on control panel
        def _on_mousewheel(event):
            ctrl_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        ctrl_canvas.bind("<Enter>", lambda e: ctrl_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        ctrl_canvas.bind("<Leave>", lambda e: ctrl_canvas.unbind_all("<MouseWheel>"))

        # â”€â”€ Slider Sections â”€â”€
        self._add_section("COLOR MATRIX")
        self._add_matrix_row("R out â† (R,G,B)", "matrix_r", 0.0, 1.0, 0.01)
        self._add_matrix_row("G out â† (R,G,B)", "matrix_g", 0.0, 1.0, 0.01)
        self._add_matrix_row("B out â† (R,G,B)", "matrix_b", 0.0, 1.0, 0.01)

        self._add_section("TONE")
        self._add_slider("Brightness", "brightness", -100, 100, 1)
        self._add_slider("Contrast", "contrast", 0.5, 2.5, 0.05)
        self._add_slider("Saturation", "saturation", 0.0, 2.0, 0.05)

        self._add_section("TINT OVERLAY")
        self._add_slider("Tint R", "tint_r", 0, 255, 1)
        self._add_slider("Tint G", "tint_g", 0, 255, 1)
        self._add_slider("Tint B", "tint_b", 0, 255, 1)
        self._add_slider("Tint Opacity", "tint_opacity", 0.0, 0.5, 0.01)

        self._add_section("EFFECTS")
        self._add_slider("Grain", "grain_intensity", 0.0, 0.15, 0.005)
        self._add_slider("Grain Size", "grain_size", 1, 6, 1)
        self._add_slider("Vignette", "vignette_strength", 0.0, 1.0, 0.05)
        self._add_slider("Glow Radius", "glow_radius", 0, 30, 1)
        self._add_slider("Glow Intensity", "glow_intensity", 0.0, 1.0, 0.05)

        self._add_section("CHARACTER FX")
        self._add_slider("Chromatic", "chromatic_shift", 0, 15, 1)
        self._add_slider("Hue Shift", "hue_shift", 0, 360, 1)
        self._add_slider("Scanlines", "scanline_intensity", 0.0, 1.0, 0.01)
        self._add_slider("Scan Opacity", "scanline_opacity", 0.0, 1.0, 0.05)
        self._add_slider("Scan Warp", "scanline_warp", 0.0, 1.0, 0.05)
        self._add_slider("Halation", "halation_strength", 0.0, 1.0, 0.05)

        self._add_section("DUOTONE", collapsed=True)
        self._add_slider("Intensity", "duotone_intensity", 0.0, 1.0, 0.05)
        self._add_matrix_row("Shadow RGB", "duotone_shadow", 0, 255, 1)
        self._add_matrix_row("Highlight RGB", "duotone_highlight", 0, 255, 1)

        # â”€â”€ Status Bar â”€â”€
        self._status_var = tk.StringVar(value="JETBOX LUT Tuner v2 | Ctrl+O: Load | Ctrl+E: Export")
        status = tk.Label(self.root, textvariable=self._status_var,
                          bg=t["bg"], fg=t["dim"], font=("Consolas", 8), anchor=tk.W)
        status.pack(fill=tk.X, padx=8, pady=(2, 4))

    # â”€â”€â”€ SECTION BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _add_section(self, title, collapsed=False):
        t = self.theme
        header = tk.Frame(self.ctrl_frame, bg=t["panel"], cursor="hand2")
        header.pack(fill=tk.X, padx=2, pady=(10, 0))

        arrow_var = tk.StringVar(value="â–¾" if not collapsed else "â–¸")
        arrow = tk.Label(header, textvariable=arrow_var, bg=t["panel"],
                         fg=t["section"], font=("Consolas", 10, "bold"))
        arrow.pack(side=tk.LEFT)
        lbl = tk.Label(header, text=f" â”€â”€ {title} â”€â”€", bg=t["panel"],
                       fg=t["section"], font=("Segoe UI", 9, "bold"))
        lbl.pack(side=tk.LEFT)

        content = tk.Frame(self.ctrl_frame, bg=t["panel"])
        if not collapsed:
            content.pack(fill=tk.X, padx=2, pady=(2, 0))

        def toggle(event=None):
            if content.winfo_manager():
                content.pack_forget()
                arrow_var.set("â–¸")
            else:
                content.pack(fill=tk.X, padx=2, pady=(2, 0), after=header)
                arrow_var.set("â–¾")

        header.bind("<Button-1>", toggle)
        arrow.bind("<Button-1>", toggle)
        lbl.bind("<Button-1>", toggle)

        self._section_content = content

    # â”€â”€â”€ SLIDER BUILDER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _add_slider(self, label, key, from_, to, resolution):
        t = self.theme
        parent = self._section_content or self.ctrl_frame
        frame = tk.Frame(parent, bg=t["panel"])
        frame.pack(fill=tk.X, padx=4, pady=1)

        tk.Label(frame, text=label, bg=t["panel"], fg=t["text"],
                 font=("Segoe UI", 9), width=14, anchor=tk.W).pack(side=tk.LEFT)

        val = self.params[key]
        var = tk.DoubleVar(value=val)
        fmt = f"{val:.3f}" if isinstance(val, float) and resolution < 1 else str(int(val))
        val_label = tk.Label(frame, text=fmt, bg=t["panel"], fg=t["val"],
                             font=("Consolas", 9), width=7, anchor=tk.E)
        val_label.pack(side=tk.RIGHT)
        self.value_labels[key] = (val_label, resolution)

        slider = tk.Scale(frame, from_=from_, to=to, resolution=resolution,
                          orient=tk.HORIZONTAL, variable=var,
                          bg=t["panel"], fg=t["accent"], troughcolor=t["trough"],
                          highlightthickness=0, sliderrelief=tk.FLAT,
                          activebackground=t["accent"], length=180, showvalue=False,
                          command=lambda v, k=key, vr=var: self._on_slider(k, vr))
        slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 4))
        self.sliders[key] = (var, slider)

    def _add_matrix_row(self, label, key, from_, to, resolution):
        t = self.theme
        parent = self._section_content or self.ctrl_frame
        frame = tk.Frame(parent, bg=t["panel"])
        frame.pack(fill=tk.X, padx=4, pady=1)

        tk.Label(frame, text=label, bg=t["panel"], fg=t["text"],
                 font=("Segoe UI", 8)).pack(anchor=tk.W)

        sub = tk.Frame(frame, bg=t["panel"])
        sub.pack(fill=tk.X)

        is_int = resolution >= 1
        for i, ch in enumerate(["R", "G", "B"]):
            sf = tk.Frame(sub, bg=t["panel"])
            sf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

            sub_key = f"{key}_{i}"
            v = self.params[key][i]
            var = tk.DoubleVar(value=v)

            tk.Label(sf, text=ch, bg=t["panel"], fg=t["dim"],
                     font=("Segoe UI", 8), width=2).pack(side=tk.LEFT)

            val_text = f"{int(v)}" if is_int else f"{v:.2f}"
            val_label = tk.Label(sf, text=val_text, bg=t["panel"], fg=t["val"],
                                 font=("Consolas", 8), width=5, anchor=tk.E)
            val_label.pack(side=tk.RIGHT)
            self.value_labels[sub_key] = (val_label, resolution)

            slider = tk.Scale(sf, from_=from_, to=to, resolution=resolution,
                              orient=tk.HORIZONTAL, variable=var,
                              bg=t["panel"], fg=t["accent"], troughcolor=t["trough"],
                              highlightthickness=0, sliderrelief=tk.FLAT,
                              activebackground=t["accent"], length=80, showvalue=False,
                              command=lambda v, k=key, idx=i, vr=var: self._on_matrix_slider(k, idx, vr))
            slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=1)
            self.sliders[sub_key] = (var, slider)

    # â”€â”€â”€ SLIDER CALLBACKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _on_slider(self, key, var):
        if not self._undo_gesture_open:
            self._undo_stack.append(deepcopy(self.params))
            if len(self._undo_stack) > 30:
                self._undo_stack.pop(0)
            self._undo_gesture_open = True
        val = var.get()
        self.params[key] = val
        entry = self.value_labels.get(key)
        if entry:
            lbl, res = entry
            lbl.config(text=f"{val:.3f}" if isinstance(val, float) and res < 1 else str(int(val)))
        self._schedule_update()

    def _on_matrix_slider(self, key, idx, var):
        if not self._undo_gesture_open:
            self._undo_stack.append(deepcopy(self.params))
            if len(self._undo_stack) > 30:
                self._undo_stack.pop(0)
            self._undo_gesture_open = True
        val = var.get()
        self.params[key][idx] = val
        sub_key = f"{key}_{idx}"
        entry = self.value_labels.get(sub_key)
        if entry:
            lbl, res = entry
            lbl.config(text=f"{int(val)}" if res >= 1 else f"{val:.2f}")
        self._schedule_update()

    def _schedule_update(self):
        if self._update_id:
            self.root.after_cancel(self._update_id)
        self._update_id = self.root.after(120, self._finish_update)

    def _finish_update(self):
        self._update_id = None
        self._undo_gesture_open = False
        self._update_preview()

    def _undo(self, event=None):
        if self._undo_stack:
            self.params = self._undo_stack.pop()
            self._sync_sliders()
            self._update_preview()

    # â”€â”€â”€ PREVIEW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _update_preview(self):
        try:
            self.root.update_idletasks()
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw < 20 or ch < 20:
                self.root.after(50, self._update_preview)
                return

            t0 = time.perf_counter()
            result = process_full(self.source_arr, self.params)
            elapsed = time.perf_counter() - t0

            rw, rh = result.size
            scale = min(cw / rw, ch / rh, 1.0)
            if scale < 0.99:
                nw, nh = max(1, int(rw * scale)), max(1, int(rh * scale))
                result = result.resize((nw, nh), Image.LANCZOS)

            self._photo = ImageTk.PhotoImage(result)
            self.canvas.delete("all")
            self.canvas.create_image(cw // 2, ch // 2, image=self._photo, anchor=tk.CENTER)

            h, w = self.source_arr.shape[:2]
            self._status_var.set(
                f"{w}Ã-{h} | {self.preset_name.upper()} | {elapsed * 1000:.0f}ms | "
                f"{THEMES[self.theme_name]['name']}"
            )
        except Exception as e:
            print(f"Preview error: {e}")

    # â”€â”€â”€ ACTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _load_new_image(self, event=None):
        path = filedialog.askopenfilename(
            title="Select Artwork",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All", "*.*")],
        )
        if path:
            self._load_image(path)
            self._update_preview()

    def _reset(self, event=None):
        self.params = deepcopy(self.initial_params)
        self._sync_sliders()
        self._update_preview()

    def _sync_sliders(self):
        for key, val in self.params.items():
            if isinstance(val, list) and len(val) == 3:
                for i in range(3):
                    sub_key = f"{key}_{i}"
                    if sub_key in self.sliders:
                        self.sliders[sub_key][0].set(val[i])
                        entry = self.value_labels.get(sub_key)
                        if entry:
                            lbl, res = entry
                            lbl.config(text=f"{int(val[i])}" if res >= 1 else f"{val[i]:.2f}")
            elif key in self.sliders:
                self.sliders[key][0].set(val)
                entry = self.value_labels.get(key)
                if entry:
                    lbl, res = entry
                    lbl.config(text=f"{val:.3f}" if isinstance(val, float) and res < 1 else str(int(val)))

    def _on_preset_change(self, event=None):
        raw_name = self.preset_var.get()
        name = raw_name.lstrip("⚡")
        all_presets = get_all_presets()
        if name in all_presets:
            self.preset_name = name
            self.params = deepcopy(all_presets[name])
            self.initial_params = deepcopy(self.params)
            self._sync_sliders()
            self._update_preview()

    def _refresh_preset_dropdown(self):
        """Refresh preset dropdown with built-in + custom presets."""
        all_names = list(PRESETS.keys()) + [f"⚡{k}" for k in load_custom_presets().keys()]
        self._preset_menu["values"] = all_names

    def _save_custom_preset(self, event=None):
        """Save current params as a custom preset (max 5)."""
        custom = load_custom_presets()
        if len(custom) >= MAX_CUSTOM_PRESETS:
            messagebox.showwarning(
                "Limit Reached",
                f"Maximum {MAX_CUSTOM_PRESETS} custom presets.\n"
                "Delete one first with 🗑 button.",
            )
            return

        # Ask for name
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Custom Preset")
        dialog.geometry("350x130")
        dialog.configure(bg=self.theme["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Preset Name:", bg=self.theme["bg"],
                 fg=self.theme["text"], font=("Segoe UI", 10)).pack(pady=(15, 5))
        name_var = tk.StringVar(value=f"custom_{len(custom)+1}")
        entry = tk.Entry(dialog, textvariable=name_var, font=("Segoe UI", 11),
                         bg=self.theme["panel"], fg=self.theme["accent"],
                         insertbackground=self.theme["accent"], width=25)
        entry.pack(pady=5)
        entry.select_range(0, tk.END)
        entry.focus_set()

        def do_save():
            pname = name_var.get().strip().lower().replace(" ", "_")
            if not pname:
                return
            if pname in PRESETS:
                messagebox.showerror("Error", "Cannot overwrite built-in presets.")
                return
            # Save params (skip 'name' key - will add custom name)
            preset_data = deepcopy(self.params)
            preset_data["name"] = f"⚡ {pname.upper()}"
            custom[pname] = preset_data
            save_custom_presets(custom)
            self._refresh_preset_dropdown()
            self.preset_name = pname
            self.preset_var.set(f"⚡{pname}")
            dialog.destroy()
            messagebox.showinfo("Saved", f"Preset '⚡{pname}' saved!\n({len(custom)}/{MAX_CUSTOM_PRESETS} slots used)")

        tk.Button(dialog, text="ğŸ’¾ Save", command=do_save,
                  bg=self.theme["btn_accent"], fg="#ffffff",
                  relief=tk.FLAT, padx=12, pady=4,
                  font=("Segoe UI", 9, "bold")).pack(pady=8)
        dialog.bind("<Return>", lambda e: do_save())

    def _delete_custom_preset(self, event=None):
        """Delete a custom preset."""
        custom = load_custom_presets()
        if not custom:
            messagebox.showinfo("No Custom Presets", "No custom presets to delete.")
            return

        # Ask which to delete
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Custom Preset")
        dialog.geometry("300x130")
        dialog.configure(bg=self.theme["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Select preset to delete:", bg=self.theme["bg"],
                 fg=self.theme["text"], font=("Segoe UI", 10)).pack(pady=(15, 5))
        del_var = tk.StringVar(value=list(custom.keys())[0])
        ttk.Combobox(dialog, textvariable=del_var,
                     values=list(custom.keys()), state="readonly", width=20).pack(pady=5)

        def do_delete():
            name = del_var.get()
            if name in custom:
                del custom[name]
                save_custom_presets(custom)
                self._refresh_preset_dropdown()
                if self.preset_name == name:
                    self.preset_name = "rage"
                    self.preset_var.set("rage")
                    self._on_preset_change()
                dialog.destroy()
                messagebox.showinfo("Deleted", f"Preset '{name}' deleted.")

        tk.Button(dialog, text="🗑 Delete", command=do_delete,
                  bg="#4a1515", fg="#ff4444",
                  relief=tk.FLAT, padx=12, pady=4,
                  font=("Segoe UI", 9, "bold")).pack(pady=8)

    def _on_theme_change(self, event=None):
        name = self.theme_var.get()
        if name in THEMES and name != self.theme_name:
            self.theme_name = name
            self.theme = THEMES[name]
            # Rebuild UI (preserves params)
            for child in self.root.winfo_children():
                child.destroy()
            self._build_ui()
            self.root.after(50, self._update_preview)

    def _export(self, event=None):
        out = {
            "name": self.params.get("name", f"Custom {self.preset_name}"),
            "color_matrix": [
                [round(v, 2) for v in self.params["matrix_r"]],
                [round(v, 2) for v in self.params["matrix_g"]],
                [round(v, 2) for v in self.params["matrix_b"]],
            ],
            "brightness": int(self.params["brightness"]),
            "contrast": round(self.params["contrast"], 2),
            "grain_intensity": round(self.params["grain_intensity"], 3),
            "vignette_strength": round(self.params["vignette_strength"], 2),
            "tint": (int(self.params["tint_r"]), int(self.params["tint_g"]), int(self.params["tint_b"])),
            "tint_opacity": round(self.params["tint_opacity"], 2),
        }

        extras = {}
        if abs(self.params["saturation"] - 1.0) > 0.01:
            extras["saturation"] = round(self.params["saturation"], 2)
        if self.params["glow_radius"] > 0:
            extras["glow_radius"] = int(self.params["glow_radius"])
            extras["glow_intensity"] = round(self.params["glow_intensity"], 2)
        if self.params.get("chromatic_shift", 0) > 0:
            extras["chromatic_shift"] = int(self.params["chromatic_shift"])
        if self.params.get("hue_shift", 0) > 0:
            extras["hue_shift"] = int(self.params["hue_shift"])
        if self.params.get("scanline_intensity", 0) > 0.005:
            extras["scanline_intensity"] = round(self.params["scanline_intensity"], 3)
        if self.params.get("halation_strength", 0) > 0.01:
            extras["halation_strength"] = round(self.params["halation_strength"], 2)
        if self.params.get("duotone_intensity", 0) > 0.01:
            extras["duotone_intensity"] = round(self.params["duotone_intensity"], 2)
            extras["duotone_shadow"] = [int(v) for v in self.params["duotone_shadow"]]
            extras["duotone_highlight"] = [int(v) for v in self.params["duotone_highlight"]]

        print("\n" + "=" * 60)
        print(f"  JETBOX LUT EXPORT â€” {self.preset_name.upper()}")
        print("=" * 60)
        print()
        print("# Paste into lut_engine.py → LUT_PRESETS dict:")
        print(f'    "{self.preset_name}": {{')
        print(f'        "name": "{out["name"]}",')
        print(f'        "color_matrix": [')
        for row in out["color_matrix"]:
            print(f"            {row},")
        print(f"        ],")
        print(f'        "brightness": {out["brightness"]},')
        print(f'        "contrast": {out["contrast"]},')
        print(f'        "grain_intensity": {out["grain_intensity"]},')
        print(f'        "vignette_strength": {out["vignette_strength"]},')
        print(f'        "tint": {out["tint"]},')
        print(f'        "tint_opacity": {out["tint_opacity"]},')
        for k, v in extras.items():
            print(f'        "{k}": {v},')
        print(f"    }},")
        print()
        print("=" * 60)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps({**out, **extras}, indent=4))
            messagebox.showinfo(
                "Export",
                "Parameters exported!\n\n"
                "âœ… Copied to clipboard (JSON)\n"
                "âœ… Printed to terminal (Python dict)\n\n"
                "Paste the terminal output into lut_engine.py",
            )
        except Exception:
            messagebox.showinfo("Export", "Parameters printed to terminal.")

    def _save_preview(self, event=None):
        path = filedialog.asksaveasfilename(
            title="Save LUT Preview (4K)",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
        )
        if path:
            source = self.full_res_arr if self.full_res_arr is not None else self.source_arr
            result = process_full(source, self.params)
            result.save(path, quality=95)
            h, w = source.shape[:2]
            print(f"âœ… Saved: {path} [{w}Ã-{h}]")
            messagebox.showinfo("Saved", f"Preview saved to:\n{path}\n\nResolution: {w}Ã-{h}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    image_path = None
    preset = "rage"
    theme = "dark_ops"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--preset" and i + 1 < len(args):
            preset = args[i + 1].lower()
            i += 2
        elif args[i] == "--theme" and i + 1 < len(args):
            theme = args[i + 1].lower()
            i += 2
        elif not args[i].startswith("--"):
            image_path = args[i]
            i += 1
        else:
            i += 1

    root = tk.Tk()
    root.geometry("1250x700")
    root.minsize(900, 550)

    app = LUTTuner(root, image_path=image_path, preset_name=preset, theme_name=theme)
    root.mainloop()


if __name__ == "__main__":
    main()

