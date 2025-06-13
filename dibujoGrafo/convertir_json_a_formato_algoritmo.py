import json
import math
import string

# === Cargar archivo JSON ===
with open("grafo_global.json", "r") as f:
    data = json.load(f)

nodos = data["nodos"]
aristas = data["aristas"]

# === Asignar etiquetas (A, B, C, ...)
etiquetas = list(string.ascii_uppercase)
etiquetas_nodos = {tuple(coord): etiquetas[i] for i, coord in enumerate(nodos)}

# === Crear grafo con pesos euclidianos
grafo_con_pesos = {etiquetas_nodos[tuple(n)]: [] for n in nodos}
coordenadas = {}

for coord, etiqueta in etiquetas_nodos.items():
    coordenadas[etiqueta] = coord

for a, b in aristas:
    a_t = tuple(a)
    b_t = tuple(b)
    dist = round(math.dist(a_t, b_t), 2)
    na, nb = etiquetas_nodos[a_t], etiquetas_nodos[b_t]
    grafo_con_pesos[na].append((nb, dist))
    grafo_con_pesos[nb].append((na, dist))  # si es no dirigido

# === Mostrar resultados
print("=== Grafo con Pesos ===")
for nodo, vecinos in grafo_con_pesos.items():
    print(f"{nodo}: {', '.join([f'{v}:{w}' for v, w in vecinos])}")

print("\n=== Coordenadas ===")
for nodo, coord in coordenadas.items():
    print(f"{nodo} = {coord}")

# === Selección de inicio y meta
print("\n=== Selección de nodos ===")
for i, (coord, etiqueta) in enumerate(etiquetas_nodos.items()):
    print(f"{etiqueta} ({i}) -> {coord}")

inicio = input("Letra del nodo de inicio: ").strip().upper()
meta = input("Letra del nodo meta: ").strip().upper()

print(f"\nInicio = {inicio}")
print(f"Meta = {meta}")
