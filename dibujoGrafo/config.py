import numpy as np

# Canvas blanco
canvas = np.ones((800, 1200, 3), dtype=np.uint8) * 255

# Parámetros globales
robot_radio = 50
max_width = 200

# Variables globales
imagenes_config = [
    {"nombre": "recursos/casa.png"},
    #{"nombre": "recursos/edificio.png"},
    #{"nombre": "recursos/arbol.png"},
    #{"nombre": "recursos/roca.png"},
    #{"nombre": "recursos/coche.png"},
]

imagenes_cargadas = []
nodos = []
aristas = []
obstaculos_shapely = []
start_node = None
end_node = None
node_labels = {}
