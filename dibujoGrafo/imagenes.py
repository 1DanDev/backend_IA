import cv2
import numpy as np
from config import imagenes_config, canvas, max_width, imagenes_cargadas

def cargar_imagenes_en_canvas():
    for config in imagenes_config:
        img = cv2.imread(config["nombre"], cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"❌ No se pudo cargar {config['nombre']}")
            continue

        h, w = img.shape[:2]
        scale_factor = max_width / w if w > max_width else 1.0
        new_size = (int(w * scale_factor), int(h * scale_factor))
        img_resized = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

        x_off = (canvas.shape[1] - new_size[0]) // 2
        y_off = (canvas.shape[0] - new_size[1]) // 2

        if img_resized.shape[2] == 4:
            alpha_s = img_resized[:, :, 3] / 255.0
            alpha_l = 1.0 - alpha_s
            for c in range(3):
                canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1], c] = (
                    alpha_s * img_resized[:, :, c] +
                    alpha_l * canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1], c]
                )
        else:
            canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1]] = img_resized

        imagenes_cargadas.append((img_resized, (x_off, y_off)))
