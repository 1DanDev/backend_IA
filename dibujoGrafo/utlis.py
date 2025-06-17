import cv2
import numpy as np
from shapely.geometry import Polygon, LineString, Point
import json

nodos, obstaculos_shapely, aristas = [], [], []
node_labels = {}
def extraer_vertices_desde_imagen(img, offset):
    """
    Extrae los vértices del contorno exterior del objeto en la imagen.
    Aplica el offset para obtener las coordenadas en el canvas global.
    """
    if img.shape[2] == 4: # Si tiene canal alfa, usa el alfa para el umbralizado
        gray = img[:, :, 3]
        # Asegúrate de que el objeto (no transparente) sea blanco (255) y el fondo (transparente) sea negro (0)
        _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    else: # Si no tiene canal alfa, convierte a escala de grises y umbraliza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Asume que el objeto es más oscuro que el fondo o blanco sobre fondo oscuro
        # Ajusta el umbral para aislar el objeto (200 es un valor común para fondos blancos)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Encuentra los contornos externos en la imagen umbralizada
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print(f"⚠️ No se encontraron contornos en la imagen.")
        return []

    # Selecciona el contorno más grande (asumiendo que es el objeto principal)
    contour = max(contours, key=cv2.contourArea)

    # Aproxima el polígono para reducir el número de vértices, simplificando la forma
    epsilon = 0.01 * cv2.arcLength(contour, True) # 1% del perímetro como tolerancia
    approx = cv2.approxPolyDP(contour, epsilon, True)

    vertices = []
    for point in approx:
        x, y = point[0]
        # Aplica el offset de la imagen para obtener coordenadas en el canvas global
        vertices.append((x + offset[0], y + offset[1]))

    return vertices

def inflar_poligono(vertices, distancia):
    """
    Infla un polígono dado por sus vértices usando la librería Shapely.
    """
    if not vertices or len(vertices) < 3:
        return None # Un polígono necesita al menos 3 vértices

    poligono = Polygon(vertices)
    # Infla el polígono. join_style=3 (BEVEL) crea esquinas biseladas (planas),
    # que son útiles para evitar que el robot "se atasque" en esquinas afiladas.
    poligono_inflado = poligono.buffer(distancia, join_style=3)

    return poligono_inflado # Devuelve el objeto Shapely Polygon inflado

def es_visible(p1, p2, obstaculos_shapely):
    """
    Verifica si una línea entre dos puntos es visible, es decir, no cruza el interior de ningún obstáculo inflado.
    Permite que la línea toque el borde del obstáculo.
    """
    linea = LineString([p1, p2])
    for obstaculo_poly in obstaculos_shapely:
        # Si la línea interseca el obstáculo inflado
        if obstaculo_poly.intersects(linea):
            # Obtén la geometría de la intersección
            intersection_geom = obstaculo_poly.intersection(linea)
            # Si la intersección no está completamente contenida en el borde del obstáculo,
            # significa que la línea entró en el interior del obstáculo, por lo tanto, no es visible.
            if not obstaculo_poly.boundary.contains(intersection_geom):
                return False
    return True


def generar_nodos_y_aristas_optimizadas(imagenes_cargadas, robot_radio= 50):
    """
    Genera nodos en los bordes de los obstáculos inflados.
    Luego, genera aristas entre los nodos que son visibles entre sí.
    """
    global nodos, obstaculos_shapely, node_labels, aristas 
    # Limpia las estructuras de datos antes de regenerar el grafo
    nodos.clear() 
    aristas.clear() 
    obstaculos_shapely.clear() 
    start_node = None 
    end_node = None 
    node_labels.clear()

    # 1. Extraer y inflar todos los obstáculos presentes en el canvas
    for (img, offset) in imagenes_cargadas:
        vertices = extraer_vertices_desde_imagen(img, offset)
        if not vertices:
            continue
        # Infla el polígono de cada imagen y lo añade a la lista de obstáculos
        inflated_polygon = inflar_poligono(vertices, robot_radio)
        if inflated_polygon:
            obstaculos_shapely.append(inflated_polygon)

    # 2. Añadir los vértices de los contornos de los obstáculos inflados como nodos
    # Permitir que el robot navegue cerca de las esquinas de los obstáculos.
    obstacle_boundary_nodes = []
    for obst_poly in obstaculos_shapely:
        # Maneja polígonos simples y multipolígonos (si la inflación creara múltiples formas)
        if obst_poly.geom_type == 'Polygon':
            # Añade los puntos del contorno exterior
            for coord in obst_poly.exterior.coords:
                obstacle_boundary_nodes.append((int(coord[0]), int(coord[1])))
            # Añade los puntos de los anillos interiores (agujeros), si existen
            for interior_ring in obst_poly.interiors:
                for coord in interior_ring.coords:
                    obstacle_boundary_nodes.append((int(coord[0]), int(coord[1])))
        elif obst_poly.geom_type == 'MultiPolygon':
            for poly in obst_poly.geoms:
                for coord in poly.exterior.coords:
                    obstacle_boundary_nodes.append((int(coord[0]), int(coord[1])))
                for interior_ring in poly.interiors:
                    for coord in interior_ring.coords:
                        obstacle_boundary_nodes.append((int(coord[0]), int(coord[1])))

    # Elimina duplicados y convierte a lista
    nodos = list(set(obstacle_boundary_nodes))

    # Asigna etiquetas a los nodos
    for i, node_coord in enumerate(nodos):
        # print("NODE CORD ",node_coord)
        node_labels[node_coord] = f"N{i}"

    print(f"🔧 Se generaron {len(nodos)} nodos en los contornos inflados.")

    # 3. Generar aristas: Conecta cada nodo con todos los demás si son "visibles"
    # Una arista es visible si no cruza el interior de ningún obstáculo.
    for i in range(len(nodos)):
        for j in range(i + 1, len(nodos)): # Evita duplicados (A-B es igual a B-A) y auto-conexiones
            if es_visible(nodos[i], nodos[j], obstaculos_shapely):
                aristas.append((nodos[i], nodos[j]))

    print(f"🔧 Se generaron {len(aristas)} aristas.")
    return nodos, node_labels, aristas,start_node, end_node 