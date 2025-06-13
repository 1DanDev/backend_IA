import json
import matplotlib.pyplot as plt
import networkx as nx

# === Cargar el archivo JSON ===
with open("grafo_global.json", "r") as f:
    data = json.load(f)

nodos = data["nodos"]
aristas = data["aristas"]

# === Crear el grafo ===
G = nx.Graph()

# Agregar nodos
for i, (x, y) in enumerate(nodos):
    G.add_node(i, pos=(x, -y))  # invertimos Y para que el gráfico coincida visualmente

# Agregar aristas
for a, b in aristas:
    i = nodos.index(a)
    j = nodos.index(b)
    G.add_edge(i, j)

# === Dibujar el grafo ===
pos = nx.get_node_attributes(G, 'pos')

plt.figure(figsize=(10, 6))
nx.draw(G, pos, with_labels=True, node_size=400, node_color='lightblue', font_size=8, edge_color='gray')
plt.title("Visualización del Grafo Global")
plt.axis("equal")
plt.show()
