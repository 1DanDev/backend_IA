import numpy as np
from shapely.geometry import Polygon
from config import *
from imagenes import cargar_imagenes_en_canvas
from utilidades import es_visible
import cv2

def extraer_vertices_desde_imagen(img, offset):
    if img.shape[2] == 4:
        gray = img[:, :, 3]
        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []

    contour = max(contours, key=cv2.contourArea)
    epsilon = 0.01 * cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    return [(p[0][0] + offset[0], p[0][1] + offset[1]) for p in approx]

def inflar_poligono(vertices, distancia):
    if len(vertices) < 3:
        return None
    poligono = Polygon(vertices)
    return poligono.buffer(distancia, join_style=3)

def generar_nodos_y_aristas_optimizadas():
    nodos.clear(); aristas.clear(); obstaculos_shapely.clear()
    global start_node, end_node
    start_node = None; end_node = None
    node_labels.clear()

    for img, offset in imagenes_cargadas:
        vertices = extraer_vertices_desde_imagen(img, offset)
        pol = inflar_poligono(vertices, robot_radio)
        if pol: obstaculos_shapely.append(pol)

    temp_nodos = set()
    for poly in obstaculos_shapely:
        if poly.geom_type == 'Polygon':
            temp_nodos.update(map(lambda c: (int(c[0]), int(c[1])), poly.exterior.coords))
            for ring in poly.interiors:
                temp_nodos.update(map(lambda c: (int(c[0]), int(c[1])), ring.coords))
        elif poly.geom_type == 'MultiPolygon':
            for subpoly in poly.geoms:
                temp_nodos.update(map(lambda c: (int(c[0]), int(c[1])), subpoly.exterior.coords))
                for ring in subpoly.interiors:
                    temp_nodos.update(map(lambda c: (int(c[0]), int(c[1])), ring.coords))

    nodos.extend(temp_nodos)
    for i, n in enumerate(nodos):
        node_labels[n] = f"N{i}"

    for i in range(len(nodos)):
        for j in range(i+1, len(nodos)):
            if es_visible(nodos[i], nodos[j], obstaculos_shapely):
                aristas.append((nodos[i], nodos[j]))
