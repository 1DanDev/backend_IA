import cv2
import json
import numpy as np

# === CONFIGURACIÓN DE IMÁGENES Y OFFSETS ===
imagenes_config = [
    {"nombre": "casa.png", "offset": (0, 0)},
    {"nombre": "cafeteria.png", "offset": (1000, 0)}  # separada a la derecha
]

# === CARGA DE IMÁGENES Y POSICIONAMIENTO ===
canvas = np.ones((800, 2000, 3), dtype=np.uint8) * 255  # fondo blanco grande
nodos = []
aristas = []
nodo_seleccionado = None

for config in imagenes_config:
    img = cv2.imread(config["nombre"])
    if img is None:
        print(f"❌ No se pudo cargar {config['nombre']}")
        continue
    x_off, y_off = config["offset"]
    h, w = img.shape[:2]
    canvas[y_off:y_off + h, x_off:x_off + w] = img
    config["tamaño"] = (w, h)

# === EVENTO DE MOUSE PARA CREAR NODOS Y ARISTAS ===
def click_event(event, x, y, flags, param):
    global nodo_seleccionado

    if event == cv2.EVENT_LBUTTONDOWN:
        # ¿Clic sobre un nodo existente?
        for (nx, ny) in nodos:
            if abs(x - nx) < 10 and abs(y - ny) < 10:
                nodo_seleccionado = (nx, ny)
                print(f"🟢 Nodo seleccionado: {nodo_seleccionado}")
                return
        # Si no, crear un nuevo nodo
        nodos.append((x, y))
        nodo_seleccionado = (x, y)
        print(f"🟢 Nodo nuevo añadido y seleccionado: ({x}, {y})")

    elif event == cv2.EVENT_RBUTTONDOWN and nodo_seleccionado:
        # Buscar un nodo existente cerca del clic derecho
        for (nx, ny) in nodos:
            if abs(x - nx) < 10 and abs(y - ny) < 10 and (nx, ny) != nodo_seleccionado:
                aristas.append((nodo_seleccionado, (nx, ny)))
                print(f"🔵 Arista añadida entre: {nodo_seleccionado} ↔ ({nx}, {ny})")
                # Seguimos con el nodo seleccionado por si quieres seguir conectando
                return
        print("⚠️ No se encontró nodo cercano para conectar.")



# === VENTANA INTERACTIVA ===
cv2.namedWindow("Editor Global")
cv2.setMouseCallback("Editor Global", click_event)

print("🖱️ Clic izquierdo = añadir nodo")
print("🖱️ Clic derecho = conectar al último nodo")
print("💾 Presiona 's' para guardar")
print("🔙 Presiona 'e' para eliminar último nodo/arista")
print("🔙 Presiona 'a' para eliminar última arista")
print("🧹 Presiona 'c' para limpiar todo")
print("❌ Presiona 'q' para salir sin guardar")

while True:
    vis = canvas.copy()

    # Dibujar nodos (verde por defecto)
    for (x, y) in nodos:
        color = (0, 200, 0)  # verde
        if nodo_seleccionado and (x, y) == nodo_seleccionado:
            color = (0, 0, 255)  # rojo
        cv2.circle(vis, (x, y), 6, color, -1)

    # Dibujar aristas
    for (p1, p2) in aristas:
        cv2.line(vis, p1, p2, (255, 0, 0), 2)

    cv2.imshow("Editor Global", vis)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        salida = {
            "nodos": nodos,
            "aristas": aristas
        }
        with open("grafo_global.json", "w") as f:
            json.dump(salida, f, indent=4)
        print("✅ Grafo global guardado en grafo_global.json")
        break

    elif key == ord("q"):
        print("❌ Saliste sin guardar.")
        break

    elif key == ord("e") and nodos:
        nodo_eliminado = nodos.pop()
        aristas = [a for a in aristas if nodo_eliminado not in a]
        nodo_seleccionado = None
        print(f"🔙 Nodo eliminado: {nodo_eliminado} y sus aristas")

    elif key == ord("a") and aristas:
        ultima_arista = aristas.pop()
        print(f"🔙 Última arista eliminada: {ultima_arista}")

    elif key == ord("c"):
        nodos.clear()
        aristas.clear()
        nodo_seleccionado = None
        print("🧹 Todo el grafo fue borrado")

cv2.destroyAllWindows()
