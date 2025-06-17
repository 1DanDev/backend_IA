import cv2
import numpy as np
from shapely.geometry import Polygon, LineString, Point
import json

# === CONFIGURACIÓN DE IMÁGENES ===
# Asegúrate de que 'casa.png' esté en el mismo directorio que tu script.
imagenes_config = [
    {"nombre": "casa.png"},
    # {"nombre": "edificio.png"},
    # {"nombre": "arbol.png"},
    # {"nombre": "roca.png"},
    # {"nombre": "coche.png"}
]

canvas = np.ones((800, 1200, 3), dtype=np.uint8) * 255 # Crea un lienzo blanco
nodos = [] # Lista para almacenar los nodos del grafo
aristas = [] # Lista para almacenar las aristas del grafo
obstaculos_shapely = [] # Lista para almacenar los objetos Shapely Polygon de los obstáculos inflados
imagenes_cargadas = [] # Guarda las imágenes redimensionadas y sus offsets

robot_radio = 50  # Radio de inflación para el robot, determina el "margen" alrededor de los obstáculos
max_width = 200   # Ancho máximo para escalar las imágenes cargadas

# Variables para los nodos de inicio y meta
start_node = None
end_node = None
node_labels = {} # Para mapear coordenadas de nodo a etiquetas (ej. "N0", "N1")

# === CARGAR IMÁGENES AL CANVAS (ESCALADAS Y CENTRADAS) ===
# Itera sobre la configuración de imágenes para cargarlas y superponerlas en el canvas.
for config in imagenes_config:
    img = cv2.imread(config["nombre"], cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"❌ No se pudo cargar {config['nombre']}. Asegúrate de que el archivo exista.")
        continue

    h, w = img.shape[:2] # Obtiene alto y ancho de la imagen

    # Escalar imagen si es muy grande para ajustarse al canvas
    scale_factor = max_width / w if w > max_width else 1.0
    new_size = (int(w * scale_factor), int(h * scale_factor))
    img_resized = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

    # Calcular offset para centrar la imagen en el canvas
    x_off = (canvas.shape[1] - new_size[0]) // 2
    y_off = (canvas.shape[0] - new_size[1]) // 2

    # Superponer la imagen en el canvas, manejando el canal alfa para transparencia
    if img_resized.shape[2] == 4: # Si la imagen tiene un canal alfa (transparencia)
        alpha_s = img_resized[:, :, 3] / 255.0 # Extrae el canal alfa y normaliza a 0-1
        alpha_l = 1.0 - alpha_s # Calcula el complemento del alfa

        for c in range(0, 3): # Itera sobre los canales de color (BGR)
            # Mezcla los píxeles de la imagen con los del canvas usando el canal alfa
            canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1], c] = (
                alpha_s * img_resized[:, :, c] + alpha_l * canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1], c]
            )
    else: # Si la imagen no tiene canal alfa (es opaca)
        canvas[y_off:y_off + img_resized.shape[0], x_off:x_off + img_resized.shape[1]] = img_resized

    imagenes_cargadas.append((img_resized, (x_off, y_off)))

print(imagenes_cargadas)

# === FUNCIONES ===
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

def generar_nodos_y_aristas_optimizadas():
    """
    Genera nodos en los bordes de los obstáculos inflados.
    Luego, genera aristas entre los nodos que son visibles entre sí.
    """
    global nodos, aristas, obstaculos_shapely, start_node, end_node, node_labels

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
        node_labels[node_coord] = f"N{i}"

    print(f"🔧 Se generaron {len(nodos)} nodos en los contornos inflados.")

    # 3. Generar aristas: Conecta cada nodo con todos los demás si son "visibles"
    # Una arista es visible si no cruza el interior de ningún obstáculo.
    for i in range(len(nodos)):
        for j in range(i + 1, len(nodos)): # Evita duplicados (A-B es igual a B-A) y auto-conexiones
            if es_visible(nodos[i], nodos[j], obstaculos_shapely):
                aristas.append((nodos[i], nodos[j]))

    print(f"🔧 Se generaron {len(aristas)} aristas.")

def mouse_event_handler(event, x, y, flags, param):
    """
    Maneja los eventos del ratón para seleccionar los nodos de inicio y meta.
    """
    global start_node, end_node, nodos, node_labels

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)
        # Encuentra el nodo existente más cercano al punto clickeado
        min_dist = float('inf')
        closest_node = None
        for node_coord in nodos:
            dist = np.sqrt((node_coord[0] - clicked_point[0])**2 + (node_coord[1] - clicked_point[1])**2)
            if dist < min_dist:
                min_dist = dist
                closest_node = node_coord

        # Un umbral para considerar que se hizo clic en un nodo (ajusta si es necesario)
        if closest_node and min_dist < 15:
            if start_node is None:
                start_node = closest_node
                print(f"Inicio seleccionado: {node_labels.get(start_node, str(start_node))}")
            elif end_node is None:
                end_node = closest_node
                print(f"Meta seleccionada: {node_labels.get(end_node, str(end_node))}")
            elif start_node == closest_node: # Si se vuelve a clickear el nodo de inicio, lo deselecciona
                start_node = None
                print("Inicio deseleccionado.")
            elif end_node == closest_node: # Si se vuelve a clickear el nodo de meta, lo deselecciona
                end_node = None
                print("Meta deseleccionada.")
            else: # Si ambos están seleccionados y se clickea un nuevo nodo, reinicia y selecciona el nuevo como inicio
                start_node = closest_node
                end_node = None
                print(f"Inicio actualizado: {node_labels.get(start_node, str(start_node))}. Meta deseleccionada.")


# === VENTANA INTERACTIVA ===
cv2.namedWindow("Editor Global") # Crea una ventana para mostrar el canvas
cv2.setMouseCallback("Editor Global", mouse_event_handler) # Registra el manejador de eventos del ratón

print("\n--- Controles ---")
print("⚙️ Presiona 'a' para generar nodos y aristas automáticamente desde la imagen")
print("🖱️ Haz clic izquierdo para seleccionar los nodos de inicio y meta (alternativamente)")
print("💾 Presiona 's' para guardar el grafo en 'grafo_global.json'")
print("🧹 Presiona 'c' para limpiar todos los nodos y aristas del grafo")
print("❌ Presiona 'q' para salir de la aplicación sin guardar")
print("-----------------\n")

while True:
    vis = canvas.copy() # Crea una copia del canvas para dibujar (evita dibujar sobre el original cada vez)

    # Dibujar aristas en el canvas
    for (p1, p2) in aristas:
        cv2.line(vis, p1, p2, (255, 0, 0), 2) # Color azul para las aristas, grosor 2

    # Dibujar nodos
    for (x, y) in nodos:
        cv2.circle(vis, (x, y), 6, (0, 200, 0), -1) # Color verde para los nodos, radio 6, relleno

    # Dibujar los nodos de inicio y meta con colores diferentes
    if start_node:
        cv2.circle(vis, start_node, 10, (0, 0, 255), -1) # Rojo para el nodo de inicio
        # Opcional: Dibujar la etiqueta del nodo de inicio
        cv2.putText(vis, node_labels.get(start_node, ''), (start_node[0] + 15, start_node[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    if end_node:
        cv2.circle(vis, end_node, 10, (255, 0, 255), -1) # Morado para el nodo de meta
        # Opcional: Dibujar la etiqueta del nodo de meta
        cv2.putText(vis, node_labels.get(end_node, ''), (end_node[0] + 15, end_node[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

    # Dibujar los contornos de los obstáculos inflados (para visualización de las áreas prohibidas)
    for obst_poly in obstaculos_shapely:
        if obst_poly.geom_type == 'Polygon':
            # Dibuja el contorno exterior del polígono inflado
            exterior_coords = list(obst_poly.exterior.coords)
            if len(exterior_coords) > 1:
                pts = np.array(exterior_coords, np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis, [pts], isClosed=True, color=(0, 0, 0), thickness=2) # Contorno negro
            # Dibuja los anillos interiores (agujeros) si existen
            for interior_ring in obst_poly.interiors:
                interior_coords = list(interior_ring.coords)
                if len(interior_coords) > 1:
                    pts_interior = np.array(interior_coords, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis, [pts_interior], isClosed=True, color=(0, 0, 0), thickness=1)
        elif obst_poly.geom_type == 'MultiPolygon': # Maneja si la inflación resulta en múltiples polígonos
            for poly in obst_poly.geoms:
                exterior_coords = list(poly.exterior.coords)
                if len(exterior_coords) > 1:
                    pts = np.array(exterior_coords, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis, [pts], isClosed=True, color=(0, 0, 0), thickness=2)
                for interior_ring in poly.interiors:
                    interior_coords = list(interior_ring.coords)
                    if len(interior_coords) > 1:
                        pts_interior = np.array(interior_coords, np.int32).reshape((-1, 1, 2))
                        cv2.polylines(vis, [pts_interior], isClosed=True, color=(0, 0, 0), thickness=1)


    cv2.imshow("Editor Global", vis) # Muestra la imagen actualizada en la ventana
    key = cv2.waitKey(1) & 0xFF # Espera una tecla (1 ms)

    # Manejo de eventos de teclado
    if key == ord("a"):
        generar_nodos_y_aristas_optimizadas() # Llama a la función para generar el grafo

    elif key == ord("s"):
        # Convertir la lista de nodos a un diccionario para la lista de adyacencia
        grafo_final = {}
        for node_coord in nodos:
            label = node_labels.get(node_coord, str(node_coord))
            grafo_final[label] = []

        for p1, p2 in aristas:
            label1 = node_labels.get(p1, str(p1))
            label2 = node_labels.get(p2, str(p2))
            grafo_final[label1].append(label2)
            grafo_final[label2].append(label1) # Asume un grafo no dirigido

        salida = {
            "grafo": grafo_final,
            "inicio": node_labels.get(start_node, None) if start_node else None,
            "meta": node_labels.get(end_node, None) if end_node else None
        }
        with open("grafo_global.json", "w") as f:
            json.dump(salida, f, indent=4) # Guarda el grafo en un archivo JSON
        print("✅ Grafo global guardado en grafo_global.json")
        break # Sale del bucle y cierra la aplicación

    elif key == ord("c"):
        nodos.clear()
        aristas.clear()
        obstaculos_shapely.clear() # Asegúrate de limpiar también los objetos Shapely
        start_node = None # Limpia el nodo de inicio
        end_node = None # Limpia el nodo de meta
        node_labels.clear() # Limpia las etiquetas de los nodos
        print("🧹 Todo el grafo fue borrado.")

    elif key == ord("q"):
        print("❌ Saliste sin guardar.")
        break # Sale del bucle sin guardar

cv2.destroyAllWindows() # Cierra todas las ventanas de OpenCV al salir