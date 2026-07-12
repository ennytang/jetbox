"""
JETBOX v3 â€” LUT Tuner
Interactive parameter tuner with real-time preview.
Tkinter + Pillow + NumPy

Usage:
    python lut_tuner.py                    â†’ Opens with default test image
    python lut_tuner.py path/to/image.jpg  â†’ Opens with specific image
    python lut_tuner.py --preset rage      â†’ Start from RAGE preset values
    python lut_tuner.py --preset melodic   â†’ Start from MELODIC preset values

Controls:
    - Sliders for all LUT parameters
    - Real-time preview (updates on slider release)
    - "Export" button â†’ prints Python dict to terminal + copies to clipboard
    - "Reset" button â†’ revert to initial preset values
    - "Load Image" button â†’ pick a different source image
"""

import sys
import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import numpy as np
from copy import deepcopy


# â”€â”€â”€ DEFAULT PRESETS (mirrors lut_engine.py) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

PRESETS = {
    "rage": {
        "name": "RAGE â€” Night Vision",
        "matrix_r": [0.08, 0.08, 0.03],
        "matrix_g": [0.12, 0.70, 0.10],
        "matrix_b": [0.03, 0.12, 0.06],
        "brightness": -20,
        "contrast": 1.20,
        "saturation": 1.0,
        "grain_intensity": 0.035,
        "vignette_strength": 0.20,
        "tint_r": 0, "tint_g": 180, "tint_b": 60,
        "tint_opacity": 0.10,
        "glow_radius": 0,
        "glow_intensity": 0.0,
    },
    "melodic": {
        "name": "MELODIC â€” Pink Haze",
        "matrix_r": [0.75, 0.20, 0.20],
        "matrix_g": [0.10, 0.40, 0.10],
        "matrix_b": [0.15, 0.15, 0.55],
        "brightness": 10,
        "contrast": 1.10,
        "saturation": 1.0,
        "grain_intensity": 0.03,
        "vignette_strength": 0.40,
        "tint_r": 255, "tint_g": 105, "tint_b": 180,
        "tint_opacity": 0.10,
        "glow_radius": 0,
        "glow_intensity": 0.0,
    },
}

# â”€â”€â”€ LUT PROCESSING FUNCTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def apply_color_matrix(arr, matrix):
    mat = np.array(matrix, dtype=np.float32)
    h, w, c = arr.shape
    flat = arr.reshape(-1, 3).astype(np.float32)
    out = flat @ mat.T
    return np.clip(out, 0, 255).astype(np.uint8).reshape(h, w, c)


def apply_brightness_contrast(arr, brightness, contrast):
    a = arr.astype(np.float32)
    a = (a - 128) * contrast + 128 + brightness
    return np.clip(a, 0, 255).astype(np.uint8)


def apply_saturation(arr, saturation):
    if abs(saturation - 1.0) < 0.01:
        return arr
    a = arr.astype(np.float32)
    gray = 0.299 * a[:,:,0] + 0.587 * a[:,:,1] + 0.114 * a[:,:,2]
    gray = gray[:,:,np.newaxis]
    out = gray + saturation * (a - gray)
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_grain(arr, intensity):
    if intensity < 0.001:
        return arr
    noise = np.random.normal(0, intensity * 255, arr.shape).astype(np.float32)
    return np.clip(arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)


def apply_tint_overlay(arr, tint_color, opacity):
    if opacity < 0.001:
        return arr
    tint = np.array(tint_color, dtype=np.float32)
    out = arr.astype(np.float32) * (1 - opacity) + tint * opacity
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_vignette(img, strength):
    if strength < 0.01:
        return img
    w, h = img.size
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = w // 2, h // 2
    max_r = int((w**2 + h**2) ** 0.5 / 2)
    steps = 60
    for i in range(steps, 0, -1):
        r = int(max_r * i / steps)
        val = int(255 * (1 - strength * (1 - (i / steps) ** 1.5)))
        val = max(0, min(255, val))
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=val)
    arr = np.array(img).astype(np.float32)
    m = np.array(mask).astype(np.float32) / 255.0
    m3 = np.stack([m]*3, axis=-1)
    return Image.fromarray(np.clip(arr * m3, 0, 255).astype(np.uint8))


def apply_glow(img, radius, intensity):
    if radius < 1 or intensity < 0.01:
        return img
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    arr_orig = np.array(img).astype(np.float32)
    arr_blur = np.array(blurred).astype(np.float32)
    out = arr_orig + arr_blur * intensity
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def process_full(source_arr, params):
    matrix = [params["matrix_r"], params["matrix_g"], params["matrix_b"]]
    arr = apply_color_matrix(source_arr, matrix)
    arr = apply_brightness_contrast(arr, params["brightness"], params["contrast"])
    arr = apply_saturation(arr, params["saturation"])
    arr = apply_tint_overlay(arr, (params["tint_r"], params["tint_g"], params["tint_b"]), params["tint_opacity"])
    arr = apply_grain(arr, params["grain_intensity"])
    img = Image.fromarray(arr)
    img = apply_vignette(img, params["vignette_strength"])
    img = apply_glow(img, params["glow_radius"], params["glow_intensity"])
    return img


# â”€â”€â”€ TUNER GUI â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class LUTTuner:
    PREVIEW_MAX = 600

    def __init__(self, root, image_path=None, preset_name="rage"):
        self.root = root
        self.root.title("JETBOX LUT Tuner")
        self.root.configure(bg="#1a1a1a")

        self.preset_name = preset_name
        self.params = deepcopy(PRESETS.get(preset_name, PRESETS["rage"]))
        self.initial_params = deepcopy(self.params)

        self.source_img = None
        self.source_arr = None
        self.preview_scale = 1.0

        if image_path and os.path.exists(image_path):
            self._load_image(image_path)
        else:
            self._create_test_image()

        self._build_ui()
        self._update_preview()

    def _load_image(self, path):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        scale = min(self.PREVIEW_MAX / w, self.PREVIEW_MAX / h, 1.0)
        if scale < 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        self.preview_scale = scale
        self.source_img = img
        self.source_arr = np.array(img)
        self.root.title(f"JETBOX LUT Tuner â€” {os.path.basename(path)}")

    def _create_test_image(self):
        w, h = 400, 300
        arr = np.zeros((h, w, 3), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                arr[y, x] = [
                    int(255 * x / w),
                    int(255 * y / h),
                    int(128 + 127 * np.sin(x * 0.05) * np.cos(y * 0.05))
                ]
        self.source_img = Image.fromarray(arr)
        self.source_arr = arr

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Dark.TFrame", background="#1a1a1a")
        style.configure("Dark.TLabel", background="#1a1a1a", foreground="#e0e0e0", font=("Segoe UI", 9))
        style.configure("Header.TLabel", background="#1a1a1a", foreground="#00ff88", font=("Segoe UI", 11, "bold"))
        style.configure("Section.TLabel", background="#1a1a1a", foreground="#88ffaa", font=("Segoe UI", 9, "bold"))
        style.configure("Val.TLabel", background="#1a1a1a", foreground="#aaaaaa", font=("Consolas", 9), width=8)

        main = ttk.Frame(self.root, style="Dark.TFrame")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # LEFT: Preview
        left = ttk.Frame(main, style="Dark.TFrame")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left, text="PREVIEW", style="Header.TLabel").pack(pady=(0,4))

        self.canvas = tk.Canvas(left, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(left, style="Dark.TFrame")
        btn_frame.pack(fill=tk.X, pady=(6,0))

        tk.Button(btn_frame, text="ğŸ“‚ Load Image", command=self._load_new_image,
                  bg="#2a2a2a", fg="#e0e0e0", relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="ğŸ”„ Reset", command=self._reset,
                  bg="#2a2a2a", fg="#e0e0e0", relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="ğŸ“‹ Export", command=self._export,
                  bg="#00aa55", fg="#ffffff", relief=tk.FLAT, padx=8, pady=4,
                  font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="ğŸ’¾ Save Preview", command=self._save_preview,
                  bg="#2a2a2a", fg="#e0e0e0", relief=tk.FLAT, padx=8, pady=4).pack(side=tk.LEFT, padx=2)

        preset_frame = ttk.Frame(btn_frame, style="Dark.TFrame")
        preset_frame.pack(side=tk.RIGHT, padx=2)
        ttk.Label(preset_frame, text="Preset:", style="Dark.TLabel").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar(value=self.preset_name)
        preset_menu = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                    values=list(PRESETS.keys()), state="readonly", width=10)
        preset_menu.pack(side=tk.LEFT, padx=4)
        preset_menu.bind("<<ComboboxSelected>>", self._on_preset_change)

        # RIGHT: Scrollable controls
        right = ttk.Frame(main, style="Dark.TFrame", width=380)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(8,0))
        right.pack_propagate(False)

        ctrl_canvas = tk.Canvas(right, bg="#1a1a1a", highlightthickness=0, width=360)
        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=ctrl_canvas.yview)
        self.ctrl_frame = ttk.Frame(ctrl_canvas, style="Dark.TFrame")

        self.ctrl_frame.bind("<Configure>",
            lambda e: ctrl_canvas.configure(scrollregion=ctrl_canvas.bbox("all")))
        ctrl_canvas.create_window((0,0), window=self.ctrl_frame, anchor=tk.NW)
        ctrl_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        ctrl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        def _on_mousewheel(event):
            ctrl_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        ctrl_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.sliders = {}
        self.value_labels = {}

        self._add_section("â”€â”€ COLOR MATRIX â”€â”€")
        self._add_matrix_row("R out â† (R,G,B)", "matrix_r", 0.0, 1.0, 0.01)
        self._add_matrix_row("G out â† (R,G,B)", "matrix_g", 0.0, 1.0, 0.01)
        self._add_matrix_row("B out â† (R,G,B)", "matrix_b", 0.0, 1.0, 0.01)

        self._add_section("â”€â”€ TONE â”€â”€")
        self._add_slider("Brightness", "brightness", -100, 100, 1)
        self._add_slider("Contrast", "contrast", 0.5, 2.5, 0.05)
        self._add_slider("Saturation", "saturation", 0.0, 2.0, 0.05)

        self._add_section("â”€â”€ TINT OVERLAY â”€â”€")
        self._add_slider("Tint R", "tint_r", 0, 255, 1)
        self._add_slider("Tint G", "tint_g", 0, 255, 1)
        self._add_slider("Tint B", "tint_b", 0, 255, 1)
        self._add_slider("Tint Opacity", "tint_opacity", 0.0, 0.5, 0.01)

        self._add_section("â”€â”€ EFFECTS â”€â”€")
        self._add_slider("Grain", "grain_intensity", 0.0, 0.15, 0.005)
        self._add_slider("Vignette", "vignette_strength", 0.0, 1.0, 0.05)
        self._add_slider("Glow Radius", "glow_radius", 0, 30, 1)
        self._add_slider("Glow Intensity", "glow_intensity", 0.0, 1.0, 0.05)

    def _add_section(self, title):
        ttk.Label(self.ctrl_frame, text=title, style="Section.TLabel").pack(
            anchor=tk.W, padx=4, pady=(10, 2))

    def _add_slider(self, label, key, from_, to, resolution):
        frame = ttk.Frame(self.ctrl_frame, style="Dark.TFrame")
        frame.pack(fill=tk.X, padx=4, pady=1)

        ttk.Label(frame, text=label, style="Dark.TLabel", width=14).pack(side=tk.LEFT)

        var = tk.DoubleVar(value=self.params[key])

        fmt = f"{self.params[key]:.3f}" if isinstance(self.params[key], float) else str(int(self.params[key]))
        val_label = ttk.Label(frame, text=fmt, style="Val.TLabel")
        val_label.pack(side=tk.RIGHT)
        self.value_labels[key] = val_label

        slider = tk.Scale(frame, from_=from_, to=to, resolution=resolution,
                         orient=tk.HORIZONTAL, variable=var,
                         bg="#2a2a2a", fg="#00ff88", troughcolor="#333333",
                         highlightthickness=0, sliderrelief=tk.FLAT,
                         length=180, showvalue=False,
                         command=lambda val, k=key, v=var: self._on_slider(k, v))
        slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4,4))

        self.sliders[key] = (var, slider)

    def _add_matrix_row(self, label, key, from_, to, resolution):
        frame = ttk.Frame(self.ctrl_frame, style="Dark.TFrame")
        frame.pack(fill=tk.X, padx=4, pady=1)

        ttk.Label(frame, text=label, style="Dark.TLabel").pack(anchor=tk.W)

        sub = ttk.Frame(frame, style="Dark.TFrame")
        sub.pack(fill=tk.X)

        channels = ["R", "G", "B"]
        for i, ch in enumerate(channels):
            sf = ttk.Frame(sub, style="Dark.TFrame")
            sf.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=1)

            sub_key = f"{key}_{i}"
            var = tk.DoubleVar(value=self.params[key][i])

            ttk.Label(sf, text=ch, style="Dark.TLabel", width=2).pack(side=tk.LEFT)

            val_label = ttk.Label(sf, text=f"{self.params[key][i]:.2f}", style="Val.TLabel")
            val_label.pack(side=tk.RIGHT)
            self.value_labels[sub_key] = val_label

            slider = tk.Scale(sf, from_=from_, to=to, resolution=resolution,
                             orient=tk.HORIZONTAL, variable=var,
                             bg="#2a2a2a", fg="#00ff88", troughcolor="#333333",
                             highlightthickness=0, sliderrelief=tk.FLAT,
                             length=80, showvalue=False,
                             command=lambda val, k=key, idx=i, v=var: self._on_matrix_slider(k, idx, v))
            slider.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=1)

            self.sliders[sub_key] = (var, slider)

    def _on_slider(self, key, var):
        val = var.get()
        self.params[key] = val
        lbl = self.value_labels.get(key)
        if lbl:
            lbl.config(text=f"{val:.3f}" if isinstance(val, float) else str(int(val)))
        self._schedule_update()

    def _on_matrix_slider(self, key, idx, var):
        val = var.get()
        self.params[key][idx] = val
        sub_key = f"{key}_{idx}"
        lbl = self.value_labels.get(sub_key)
        if lbl:
            lbl.config(text=f"{val:.2f}")
        self._schedule_update()

    _update_id = None
    def _schedule_update(self):
        if self._update_id:
            self.root.after_cancel(self._update_id)
        self._update_id = self.root.after(150, self._update_preview)

    def _update_preview(self):
        try:
            result = process_full(self.source_arr, self.params)
            cw = self.canvas.winfo_width() or 600
            ch = self.canvas.winfo_height() or 500
            rw, rh = result.size
            scale = min(cw / rw, ch / rh, 1.0)
            if scale < 1.0:
                result = result.resize((int(rw*scale), int(rh*scale)), Image.LANCZOS)

            self._photo = ImageTk.PhotoImage(result)
            self.canvas.delete("all")
            self.canvas.create_image(cw//2, ch//2, image=self._photo, anchor=tk.CENTER)
        except Exception as e:
            print(f"Preview error: {e}")

    def _load_new_image(self):
        path = filedialog.askopenfilename(
            title="Select Artwork",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.webp *.bmp"), ("All", "*.*")]
        )
        if path:
            self._load_image(path)
            self._update_preview()

    def _reset(self):
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
                        lbl = self.value_labels.get(sub_key)
                        if lbl:
                            lbl.config(text=f"{val[i]:.2f}")
            elif key in self.sliders:
                self.sliders[key][0].set(val)
                lbl = self.value_labels.get(key)
                if lbl:
                    lbl.config(text=f"{val:.3f}" if isinstance(val, float) else str(int(val)))

    def _on_preset_change(self, event=None):
        name = self.preset_var.get()
        if name in PRESETS:
            self.preset_name = name
            self.params = deepcopy(PRESETS[name])
            self.initial_params = deepcopy(self.params)
            self._sync_sliders()
            self._update_preview()

    def _export(self):
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

        print("\n" + "=" * 60)
        print(f"  JETBOX LUT EXPORT â€” {self.preset_name.upper()}")
        print("=" * 60)
        print()
        print("# Paste into lut_engine.py â†’ LUT_PRESETS dict:")
        
        # Pretty print as Python dict
        print(f'    "{self.preset_name}": {{')
        print(f'        "name": "{out["name"]}",')
        print(f'        "color_matrix": [')
        for row in out["color_matrix"]:
            print(f'            {row},')
        print(f'        ],')
        print(f'        "brightness": {out["brightness"]},')
        print(f'        "contrast": {out["contrast"]},')
        print(f'        "grain_intensity": {out["grain_intensity"]},')
        print(f'        "vignette_strength": {out["vignette_strength"]},')
        print(f'        "tint": {out["tint"]},')
        print(f'        "tint_opacity": {out["tint_opacity"]},')
        for k, v in extras.items():
            print(f'        "{k}": {v},')
        print(f'    }},')
        
        print()
        print("=" * 60)

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(json.dumps(out, indent=4))
            messagebox.showinfo("Export",
                "Parameters exported!\n\n"
                "âœ… Copied to clipboard (JSON)\n"
                "âœ… Printed to terminal (Python dict)\n\n"
                "Paste the terminal output into lut_engine.py")
        except Exception:
            messagebox.showinfo("Export", "Parameters printed to terminal.")

    def _save_preview(self):
        path = filedialog.asksaveasfilename(
            title="Save LUT Preview",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")]
        )
        if path:
            result = process_full(self.source_arr, self.params)
            result.save(path, quality=95)
            print(f"âœ… Saved: {path}")
            messagebox.showinfo("Saved", f"Preview saved to:\n{path}")


# â”€â”€â”€ MAIN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    image_path = None
    preset = "rage"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--preset" and i+1 < len(args):
            preset = args[i+1].lower()
            i += 2
        elif not args[i].startswith("--"):
            image_path = args[i]
            i += 1
        else:
            i += 1

    root = tk.Tk()
    root.geometry("1050x650")
    root.minsize(800, 500)

    app = LUTTuner(root, image_path=image_path, preset_name=preset)
    root.mainloop()


if __name__ == "__main__":
    main()

