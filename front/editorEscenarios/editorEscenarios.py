import pygame
import json
import math
import os

# --- 1. Inicialización y Constantes ---
pygame.init()

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MENU_WIDTH = 280
EDITOR_WIDTH = SCREEN_WIDTH - MENU_WIDTH

COLOR_FONDO_ESCENARIO = "#87E79E"
COLOR_MENU = (50, 50, 50)
COLOR_TEXTO = (255, 255, 255)
COLOR_ADVERTENCIA = (255, 100, 100)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Editor de Escenarios Avanzado")
font = pygame.font.Font(None, 24)
font_bold = pygame.font.Font(None, 28)

# --- 2. Carga de Assets (Imágenes) ---

ASSET_PATHS = {
    'obs1': 'obstaculo1.png', 'obs2': 'obstaculo2.png', 'obs3': 'obstaculo3.png',
    'obs4': 'obstaculo4.png', 'obs5': 'obstaculo5.png', 'obs6': 'obstaculo6.png',
    'obs7': 'obstaculo7.png', 'obs8': 'obstaculo8.png', 'robot': 'robot.png',
    'flag': 'bandera.png',
    'background': 'fondo.png' # <-- NUEVO: Ruta para la imagen de fondo
}

IMAGES = {}
try:
    for key, path in ASSET_PATHS.items():
        IMAGES[key] = pygame.image.load(path).convert_alpha()
except FileNotFoundError as e:
    print(f"Error: No se encontró el archivo de imagen: {e}. Se usarán placeholders.")
    for key in ASSET_PATHS:
        if key not in IMAGES:
            size = (128, 64) if 'icon' in key else (64, 64)
            IMAGES[key] = pygame.Surface(size)
            IMAGES[key].fill((100, 100, 100))

# <-- NUEVO: Preparar la imagen de fondo -->
background_image = IMAGES.get('background')
if background_image and background_image.get_size() != (EDITOR_WIDTH, SCREEN_HEIGHT):
    try:
        # Escalar la imagen para que llene el área del editor
        background_image = pygame.transform.scale(background_image, (EDITOR_WIDTH, SCREEN_HEIGHT))
        print("Imagen de fondo cargada y escalada con éxito.")
    except Exception as e:
        print(f"No se pudo escalar la imagen de fondo: {e}")
        background_image = None # Volver al color sólido si hay error

# --- 3. Definición de Clases ---
# (El código de las clases no cambia)
class ObjetoDelJuego:
    def __init__(self, x, y, image, obj_id, path):
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.obj_id = obj_id 
        self.path = path
        self.angle = 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def move(self, dx, dy):
        self.rect.move_ip(dx, dy)

    def set_rotation(self, angle):
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def rotate_with_mouse(self, mouse_pos):
        if 'obs' not in self.obj_id:
             return
        rel_x, rel_y = mouse_pos[0] - self.rect.centerx, mouse_pos[1] - self.rect.centery
        new_angle = -math.degrees(math.atan2(rel_y, rel_x))
        self.set_rotation(new_angle)
        
class Button:
    def __init__(self, x, y, image, action_id, tooltip):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.action_id = action_id
        self.tooltip = tooltip

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# --- 4. Funciones Auxiliares ---
# (El código de las funciones no cambia)
def guardar_escenario(objetos):
    escenario_data = []
    for obj in objetos:
        data = { 'path': obj.path, 'pos': (obj.rect.centerx, obj.rect.centery), 'angle': round(obj.angle, 2) }
        escenario_data.append(data)
    try:
        with open('escenario.json', 'w') as f:
            json.dump(escenario_data, f, indent=4)
        print("¡Escenario guardado con éxito en 'escenario.json'!")
        return True
    except IOError as e:
        print(f"Error al guardar el archivo: {e}")
        return False

def cargar_escenario():
    objetos = []
    player_found = False
    goal_found = False
    if os.path.exists('escenario.json'):
        print("Cargando escenario desde 'escenario.json'...")
        with open('escenario.json', 'r') as f:
            escenario_data = json.load(f)
        path_to_key = {v: k for k, v in ASSET_PATHS.items()}
        for data in escenario_data:
            path = data['path']
            if path in path_to_key:
                obj_id = path_to_key[path]
                image = IMAGES.get(obj_id)
                if image:
                    x, y = data['pos']
                    angle = data['angle']
                    new_obj = ObjetoDelJuego(x, y, image, obj_id, path)
                    new_obj.set_rotation(angle)
                    objetos.append(new_obj)
                    if obj_id == 'robot': player_found = True
                    elif obj_id == 'flag': goal_found = True
            else:
                print(f"Advertencia: El path '{path}' no se reconoce y será omitido.")
    return objetos, player_found, goal_found

# --- 5. Configuración del Editor ---
objetos_en_escenario, player_exists, goal_exists = cargar_escenario()
botones_menu = []
objeto_seleccionado_menu = None
objeto_arrastrado = None
feedback_message = ""
feedback_timer = 0

# --- 6. Crear Botones del Menú ---
# (El código de creación de botones no cambia)
item_buttons = [key for key in ASSET_PATHS if 'obs' in key or key in ['robot', 'flag']]
item_buttons.sort()
button_size = (64, 64)
start_x, start_y = EDITOR_WIDTH + 20, 50
cols = 2
col_width = 90
row_height = 80
for i, obj_id in enumerate(item_buttons):
    row = i // cols
    col = i % cols
    x = start_x + col * col_width
    y = start_y + row * row_height
    img = pygame.transform.scale(IMAGES[obj_id], button_size)
    tooltip = obj_id.replace('_', ' ').title()
    btn = Button(x, y, img, obj_id, tooltip)
    botones_menu.append(btn)

options_y_start = 500
separator_line = (EDITOR_WIDTH + 10, options_y_start - 10, SCREEN_WIDTH - 10, options_y_start - 10)
clear_button_img = pygame.Surface((128, 40)); clear_button_img.fill((200, 50, 50))
clear_text = font_bold.render("Limpiar", True, COLOR_TEXTO)
clear_button_img.blit(clear_text, (clear_button_img.get_width()/2 - clear_text.get_width()/2, clear_button_img.get_height()/2 - clear_text.get_height()/2))
clear_button = Button(EDITOR_WIDTH + 70, options_y_start, clear_button_img, 'clear', "Limpiar Escenario")
# <-- MODIFICACIÓN: El botón de guardar ahora se genera como los demás -->
save_button_img = pygame.Surface((128, 40)); save_button_img.fill((50, 180, 50))
save_text = font_bold.render("Guardar", True, COLOR_TEXTO)
save_button_img.blit(save_text, (save_button_img.get_width()/2 - save_text.get_width()/2, save_button_img.get_height()/2 - save_text.get_height()/2))
save_button = Button(EDITOR_WIDTH + 70, options_y_start + 60, save_button_img, 'save', "Guardar Escenario")

exit_button_img = pygame.Surface((128, 40)); exit_button_img.fill((80, 80, 100))
exit_text = font_bold.render("Salir", True, COLOR_TEXTO)
exit_button_img.blit(exit_text, (exit_button_img.get_width()/2 - exit_text.get_width()/2, exit_button_img.get_height()/2 - exit_text.get_height()/2))
exit_button = Button(EDITOR_WIDTH + 70, options_y_start + 120, exit_button_img, 'exit', "Borra JSON y Sale")

# --- 7. Bucle Principal del Editor ---
running = True
clock = pygame.time.Clock()

while running:
    # --- Manejo de Eventos ---
    # (El código de manejo de eventos no cambia)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            
            if event.button == 1:
                clicked_on_button = False
                for btn in botones_menu:
                    if btn.is_clicked(pos):
                        objeto_seleccionado_menu = btn.action_id
                        clicked_on_button = True
                        break
                
                if not clicked_on_button:
                    if save_button.is_clicked(pos):
                        if player_exists and goal_exists:
                            if guardar_escenario(objetos_en_escenario):
                                feedback_message = "¡Escenario guardado!"
                                feedback_timer = 180
                        else:
                            feedback_message = "Falta el robot y/o la bandera"
                            feedback_timer = 180
                        clicked_on_button = True
                    
                    elif clear_button.is_clicked(pos):
                        objetos_en_escenario.clear()
                        player_exists = False
                        goal_exists = False
                        feedback_message = "Escenario limpiado."
                        feedback_timer = 120
                        clicked_on_button = True

                    elif exit_button.is_clicked(pos):
                        try:
                            if os.path.exists('escenario.json'):
                                os.remove('escenario.json')
                                print("Archivo 'escenario.json' eliminado.")
                        except OSError as e:
                            print(f"Error al eliminar el archivo: {e}")
                        running = False

                if not clicked_on_button and pos[0] < EDITOR_WIDTH:
                    clicked_on_object = False
                    for obj in reversed(objetos_en_escenario):
                        if obj.rect.collidepoint(pos):
                            objeto_arrastrado = obj
                            clicked_on_object = True
                            break
                    
                    if not clicked_on_object and objeto_seleccionado_menu:
                        obj_id = objeto_seleccionado_menu
                        path = ASSET_PATHS[obj_id]
                        if obj_id == 'robot':
                            if not player_exists:
                                new_obj = ObjetoDelJuego(pos[0], pos[1], IMAGES[obj_id], obj_id, path)
                                objetos_en_escenario.append(new_obj)
                                player_exists = True
                            else: print("El personaje ya existe.")
                        elif obj_id == 'flag':
                            if not goal_exists:
                                new_obj = ObjetoDelJuego(pos[0], pos[1], IMAGES[obj_id], obj_id, path)
                                objetos_en_escenario.append(new_obj)
                                goal_exists = True
                            else: print("La meta ya existe.")
                        else:
                            new_obj = ObjetoDelJuego(pos[0], pos[1], IMAGES[obj_id], obj_id, path)
                            objetos_en_escenario.append(new_obj)
                        objeto_seleccionado_menu = None
            
            elif event.button == 3:
                if pos[0] < EDITOR_WIDTH:
                    for obj in reversed(objetos_en_escenario):
                        if obj.rect.collidepoint(pos):
                            if obj.obj_id == 'robot': player_exists = False
                            elif obj.obj_id == 'flag': goal_exists = False
                            objetos_en_escenario.remove(obj)
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: objeto_arrastrado = None

        elif event.type == pygame.MOUSEMOTION:
            if objeto_arrastrado:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_r]: objeto_arrastrado.rotate_with_mouse(event.pos)
                else: objeto_arrastrado.move(event.rel[0], event.rel[1])

    # --- 8. Lógica de Dibujado ---
    screen.fill(COLOR_MENU) # Rellenar toda la pantalla con el color del menú como base

    # <-- MODIFICACIÓN: Dibujar la imagen de fondo o el color de respaldo -->
    if background_image:
        screen.blit(background_image, (0, 0))
    else:
        # Si no hay imagen, dibujar un rectángulo verde solo en el área del editor
        pygame.draw.rect(screen, COLOR_FONDO_ESCENARIO, (0, 0, EDITOR_WIDTH, SCREEN_HEIGHT))

    # Dibujar el resto de los elementos sobre el fondo
    for obj in objetos_en_escenario: obj.draw(screen)
    
    # Dibujar el menú
    info_text = font.render("Objetos:", True, COLOR_TEXTO)
    screen.blit(info_text, (EDITOR_WIDTH + 15, 20))
    for btn in botones_menu: btn.draw(screen)

    pygame.draw.line(screen, (100, 100, 100), separator_line[:2], separator_line[2:], 2)
    options_text = font.render("Opciones:", True, COLOR_TEXTO)
    screen.blit(options_text, (EDITOR_WIDTH + 15, options_y_start - 40))
    clear_button.draw(screen)
    save_button.draw(screen)
    exit_button.draw(screen)
    
    if objeto_seleccionado_menu:
        sel_text = font.render(f"Plantar: {objeto_seleccionado_menu}", True, (200, 200, 0))
        screen.blit(sel_text, (EDITOR_WIDTH + 10, SCREEN_HEIGHT - 30))

    if feedback_timer > 0:
        color = COLOR_ADVERTENCIA if "Falta" in feedback_message else (200, 255, 200)
        feedback_surf = font.render(feedback_message, True, color)
        pos_x = EDITOR_WIDTH + (MENU_WIDTH / 2) - (feedback_surf.get_width() / 2)
        screen.blit(feedback_surf, (pos_x, options_y_start - 70))
        feedback_timer -= 1
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()