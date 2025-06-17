from shapely.geometry import LineString

def es_visible(p1, p2, obstaculos_shapely):
    linea = LineString([p1, p2])
    for obstaculo in obstaculos_shapely:
        if obstaculo.intersects(linea):
            if not obstaculo.boundary.contains(obstaculo.intersection(linea)):
                return False
    return True
