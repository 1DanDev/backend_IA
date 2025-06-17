import pygame
import sys
import subprocess

# Inicializar pygame
pygame.init()

# Dimensiones más amplias
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Menú Principal - Pygame")

# Colores
BG_COLOR = (29, 29, 47)
WHITE = (255, 255, 255)
GRAY = (58, 58, 90)
GREEN = (60, 176, 67)
RED = (198, 64, 64)
LIGHT_GRAY = (100, 100, 140)
DISABLED_GRAY = (80, 80, 110)
HOVER_GRAY = (75, 75, 110)
HOVER_GREEN = (80, 200, 90)
HOVER_RED = (210, 80, 80)

# Fuente
font = pygame.font.SysFont("arial", 16)

# Layout ajustado al nuevo ancho
btn_width = 170
btn_height = 40
GAP_X = 40
TOP_MARGIN = 45

# Calcular posición inicial para centrar grupo de botones
group_width = btn_width * 4 + GAP_X * 3 + 120  # 120 extra por combo ancho
start_x = (WIDTH - group_width) // 2

# Rects centrados
btn_back = pygame.Rect(start_x, TOP_MARGIN, btn_width, btn_height)
combo_box = pygame.Rect(btn_back.right + GAP_X, TOP_MARGIN, btn_width + 120, btn_height)
btn_start = pygame.Rect(combo_box.right + GAP_X, TOP_MARGIN, btn_width, btn_height)
btn_exit = pygame.Rect(btn_start.right + GAP_X, TOP_MARGIN, btn_width, btn_height)

# Opciones
algoritmos = ["Algoritmo A*", "Búsqueda en Anchura", "Búsqueda en Profundidad"]
selected_index = -1
combo_open = False

def get_combo_items_rects():
    return [pygame.Rect(combo_box.x, combo_box.bottom + 5 + i * 30, combo_box.width, 30)
            for i in range(len(algoritmos))]

running = True
while running:
    screen.fill(BG_COLOR)
    mouse_pos = pygame.mouse.get_pos()
    combo_items_rects = get_combo_items_rects()

    # Botón Editar entorno
    back_hover = btn_back.collidepoint(mouse_pos)
    pygame.draw.rect(screen, HOVER_GRAY if back_hover else GRAY, btn_back)
    text_back = font.render("← Editar entorno", True, WHITE)
    screen.blit(text_back, text_back.get_rect(center=btn_back.center))

    # ComboBox
    pygame.draw.rect(screen, GRAY, combo_box)
    texto = "Selecciona el algoritmo de búsqueda" if selected_index == -1 else algoritmos[selected_index]
    text_combo = font.render(texto, True, WHITE)
    screen.blit(text_combo, text_combo.get_rect(center=combo_box.center))

    # Botón Iniciar
    start_hover = btn_start.collidepoint(mouse_pos)
    if selected_index != -1:
        color_start = HOVER_GREEN if start_hover else GREEN
    else:
        color_start = DISABLED_GRAY
    pygame.draw.rect(screen, color_start, btn_start)
    text_start = font.render("Iniciar", True, WHITE)
    screen.blit(text_start, text_start.get_rect(center=btn_start.center))

    # Botón Salir
    exit_hover = btn_exit.collidepoint(mouse_pos)
    pygame.draw.rect(screen, HOVER_RED if exit_hover else RED, btn_exit)
    text_exit = font.render("Salir", True, WHITE)
    screen.blit(text_exit, text_exit.get_rect(center=btn_exit.center))

    # Desplegable
    if combo_open:
        for i, rect in enumerate(combo_items_rects):
            item_hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, HOVER_GRAY if item_hover else LIGHT_GRAY, rect)
            text_item = font.render(algoritmos[i], True, WHITE)
            screen.blit(text_item, (rect.x + 10, rect.y + 6))

    # Área de visualización del escenario (con imagen fondo)
    try:
        fondo_imagen = pygame.image.load("fondo.PNG").convert()
        juego_area = pygame.Rect(60, 120, WIDTH - 120, HEIGHT - 160)  # más grande
        fondo_ajustado = pygame.transform.scale(fondo_imagen, (juego_area.width, juego_area.height))
        pygame.draw.rect(screen, (20, 20, 30), juego_area)  # fondo oscuro
        screen.blit(fondo_ajustado, juego_area.topleft)
    except Exception as e:
        print("⚠ No se pudo cargar fondo.PNG:", e)

    # Eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            if btn_exit.collidepoint(mx, my):
                running = False
            elif btn_back.collidepoint(mx, my):
                try:
                    subprocess.Popen(["python", "editorEscenarios.py"])
                    pygame.quit()
                    sys.exit()

                except Exception as e:
                    print("Error al abrir editorEscenarios.py:", e)
            elif btn_start.collidepoint(mx, my) and selected_index != -1:
                print(f"Iniciando algoritmo: {algoritmos[selected_index]}")
            elif combo_box.collidepoint(mx, my):
                combo_open = not combo_open
            elif combo_open:
                for i, rect in enumerate(combo_items_rects):
                    if rect.collidepoint(mx, my):
                        selected_index = i
                        combo_open = False
                        break
                else:
                    combo_open = False

    pygame.display.flip()

pygame.quit()
sys.exit()
