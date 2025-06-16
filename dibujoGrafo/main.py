import cv2
import json
import numpy as np
from config import canvas, nodos, aristas, obstaculos_shapely, start_node, end_node, node_labels
from imagenes import cargar_imagenes_en_canvas
from grafo import generar_nodos_y_aristas_optimizadas
from interaccion import mouse_event_handler

# === Cargar imágenes desde la carpeta recursos/ ===
cargar_imagenes_en_canvas()

# === Ventana interactiva ===
cv2.namedWindow("Editor Global")
cv2.setMouseCallback("Editor Global", mouse_event_handler)

print("\n--- Controles ---")
print("⚙️  Presiona 'a' para generar nodos y aristas automáticamente desde la imagen")
print("🖱️  Haz clic izquierdo para seleccionar los nodos de inicio y meta")
print("💾 Presiona 's' para guardar el grafo en 'grafo_global.json'")
print("🧹 Presiona 'c' para limpiar todos los nodos y aristas del grafo")
print("❌ Presiona 'q' para salir de la aplicación sin guardar")
print("-----------------\n")

while True:
    vis = canvas.copy()

    # Dibujar aristas
    for p1, p2 in aristas:
        cv2.line(vis, p1, p2, (255, 0, 0), 2)

    # Dibujar nodos
    for (x, y) in nodos:
        cv2.circle(vis, (x, y), 6, (0, 200, 0), -1)

    # Nodo inicio
    if start_node:
        cv2.circle(vis, start_node, 10, (0, 0, 255), -1)
        cv2.putText(vis, node_labels.get(start_node, ''), (start_node[0] + 15, start_node[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Nodo meta
    if end_node:
        cv2.circle(vis, end_node, 10, (255, 0, 255), -1)
        cv2.putText(vis, node_labels.get(end_node, ''), (end_node[0] + 15, end_node[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

    # Dibujar contornos inflados
    for obst in obstaculos_shapely:
        if obst.geom_type == 'Polygon':
            exterior_coords = list(obst.exterior.coords)
            if len(exterior_coords) > 1:
                pts = np.array(exterior_coords, np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis, [pts], True, (0, 0, 0), 2)
            for ring in obst.interiors:
                interior_coords = list(ring.coords)
                if len(interior_coords) > 1:
                    pts_interior = np.array(interior_coords, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis, [pts_interior], True, (0, 0, 0), 1)
        elif obst.geom_type == 'MultiPolygon':
            for poly in obst.geoms:
                exterior_coords = list(poly.exterior.coords)
                if len(exterior_coords) > 1:
                    pts = np.array(exterior_coords, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis, [pts], True, (0, 0, 0), 2)
                for ring in poly.interiors:
                    interior_coords = list(ring.coords)
                    if len(interior_coords) > 1:
                        pts_interior = np.array(interior_coords, np.int32).reshape((-1, 1, 2))
                        cv2.polylines(vis, [pts_interior], True, (0, 0, 0), 1)

    cv2.imshow("Editor Global", vis)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("a"):
        generar_nodos_y_aristas_optimizadas()

    elif key == ord("s"):
        grafo_final = {}
        for node_coord in nodos:
            label = node_labels.get(node_coord, str(node_coord))
            grafo_final[label] = []

        for p1, p2 in aristas:
            l1 = node_labels.get(p1, str(p1))
            l2 = node_labels.get(p2, str(p2))
            grafo_final[l1].append(l2)
            grafo_final[l2].append(l1)

        salida = {
            "grafo": grafo_final,
            "inicio": node_labels.get(start_node) if start_node else None,
            "meta": node_labels.get(end_node) if end_node else None
        }

        with open("grafo_global.json", "w") as f:
            json.dump(salida, f, indent=4)
        print("✅ Grafo guardado en grafo_global.json")
        break

    elif key == ord("c"):
        nodos.clear()
        aristas.clear()
        obstaculos_shapely.clear()
        start_node = None
        end_node = None
        node_labels.clear()
        print("🧹 Grafo limpiado.")

    elif key == ord("q"):
        print("❌ Saliste sin guardar.")
        break

cv2.destroyAllWindows()
