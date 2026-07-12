"""
JETBOX v5 - Visual Processor Plugin
Fisheye: tam daire barrel distortion + siyah background
"""
import cv2, numpy as np, os, time, requests
from PIL import Image

def apply_fisheye(image_input, strength=1.0, output_size=1500, circle_margin=0.02):
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None: raise ValueError(f"Image not found: {image_input}")
    elif isinstance(image_input, bytes):
        img = cv2.imdecode(np.frombuffer(image_input, np.uint8), cv2.IMREAD_COLOR)
    elif isinstance(image_input, np.ndarray):
        img = image_input.copy()
    elif isinstance(image_input, Image.Image):
        img = cv2.cvtColor(np.array(image_input.convert("RGB")), cv2.COLOR_RGB2BGR)
    else:
        raise TypeError(f"Unsupported: {type(image_input)}")
    h, w = img.shape[:2]
    side = min(h, w)
    img = img[(h-side)//2:(h-side)//2+side, (w-side)//2:(w-side)//2+side]
    img = cv2.resize(img, (output_size, output_size), interpolation=cv2.INTER_LANCZOS4)
    cx = cy = output_size / 2.0
    radius = (output_size / 2.0) * (1.0 - circle_margin)
    ys, xs = np.mgrid[0:output_size, 0:output_size].astype(np.float32)
    nx = (xs - cx) / radius
    ny = (ys - cy) / radius
    r  = np.sqrt(nx**2 + ny**2)
    circle_mask = (r <= 1.0).astype(np.float32)
    k = strength * 0.35
    r_src = np.where(r <= 1.0, r * (1.0 + k * r * r), 1.0)
    src_x = np.clip((r_src * nx * radius + cx).astype(np.float32), 0, output_size-1)
    src_y = np.clip((r_src * ny * radius + cy).astype(np.float32), 0, output_size-1)
    distorted = cv2.remap(img, src_x, src_y, cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    edge_w = max(1, int(output_size * 0.008))
    kernel = np.ones((edge_w*2+1, edge_w*2+1), np.float32); kernel /= kernel.sum()
    soft_mask = cv2.filter2D(circle_mask, -1, kernel)
    soft3 = np.stack([soft_mask]*3, axis=-1)
    result = (distorted * soft3).astype(np.uint8)
    _, buf = cv2.imencode('.jpg', result, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return buf.tobytes()

def fisheye_from_url(url, strength=1.0, output_size=1500):
    resp = requests.get(url, timeout=15); resp.raise_for_status()
    return apply_fisheye(resp.content, strength=strength, output_size=output_size)

def save_fisheye(image_bytes, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{filename}_{int(time.time())}_fisheye.jpg")
    with open(path, 'wb') as f: f.write(image_bytes)
    return path
