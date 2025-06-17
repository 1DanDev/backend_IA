import json
import cv2
import numpy
import utlis
max_width = 200

#Leemos en Json del lienzo
def leerEscenarioJson(path):
    datos = []
    imgs = []
    # Abre el archivo en modo lectura
    with open('escenario.json', 'r') as archivo:
        datos = json.load(archivo)
    if datos!=[]:
        for elemento in datos:
            ruta = elemento["path"]
            posicion = elemento["pos"]    
            angulo = elemento["angle"]
            imgs.append([ruta,posicion,angulo])
    # print(imgs)
    return imgs

def cargarImagenes(imgs):
    imagenes_cargadas = []
    #indice 0: nombre imagen, id1 :cordenadas, id2 rotacion
    for imagen in imgs:
        img = cv2.imread(imagen[0], cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"❌ No se pudo cargar {imagen[0]}. Asegúrate de que el archivo exista.")
            continue
        h, w = img.shape[:2] # Obtiene alto y ancho de la imagen
        # Escalar imagen si es muy grande para ajustarse al canvas
        scale_factor = max_width / w if w > max_width else 1.0
        new_size = (int(w * scale_factor), int(h * scale_factor))
        img_resized = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        # Calcular offset para centrar la imagen en el canvas
        x_off = imagen[1][0]
        y_off = imagen[1][1]

        imagenes_cargadas.append((img_resized, (x_off, y_off)))
    return imagenes_cargadas

def NodosJson(nodos, node_labels, aristas, start_node, end_node):
    grafo_final = {}
    coordenadas = {}
    for node_coord in nodos:
        label = node_labels.get(node_coord, str(node_coord))
        grafo_final[label] = []
        coordenadas[label] = []

    for p1, p2 in aristas:
        label1 = node_labels.get(p1, str(p1))
        label2 = node_labels.get(p2, str(p2))
        grafo_final[label1].append(label2)
        grafo_final[label2].append(label1) # Asume un grafo no dirigido
    
    for nodo in nodos:
        print(nodo, node_labels.get(nodo,str(nodo)))
        coordenadas[node_labels.get(nodo,str(nodo))] =nodo



    salida = {
        "inicio": node_labels.get(start_node, None) if start_node else None,
        "meta": node_labels.get(end_node, None) if end_node else None,
        "grafo": grafo_final,
        "coordenadas": coordenadas
    }
    with open("grafo_coords.json", "w") as f:
            json.dump(salida, f, indent=4) # Guarda el grafo en un archivo JSON
    print("✅ Grafo global guardado en grafo_global.json")
        
    return salida
    


#Leemos en Json
datosJson = leerEscenarioJson("escenario.json")
imagenes = cargarImagenes(datosJson)
nodos, node_labels, aristas,start_node, end_node = utlis.generar_nodos_y_aristas_optimizadas(imagenes)
a = NodosJson(nodos, node_labels, aristas, start_node, end_node)
print(a)
# print(cargarImagenes(leerEscenarioJson("escenario.json")))
