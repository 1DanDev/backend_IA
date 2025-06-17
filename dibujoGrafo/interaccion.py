import numpy as np
from config import nodos, node_labels, start_node, end_node

def mouse_event_handler(event, x, y, flags, param):
    global start_node, end_node
    if event != 1: return
    click = (x, y)
    min_dist = float('inf')
    closest = None
    for n in nodos:
        dist = np.hypot(n[0]-x, n[1]-y)
        if dist < min_dist:
            min_dist, closest = dist, n
    if closest and min_dist < 15:
        if not start_node:
            start_node = closest
        elif not end_node:
            end_node = closest
        elif closest == start_node:
            start_node = None
        elif closest == end_node:
            end_node = None
        else:
            start_node, end_node = closest, None
