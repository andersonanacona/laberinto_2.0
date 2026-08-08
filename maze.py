from pygame import *
from collections import deque

CELL = 36
MAZE_GRID = [
    "1111111111111111111",
    "0010000010000000001",
    "1010101011111011101",
    "1010101000001010101",
    "1010101111101010101",
    "1010100000101000101",
    "1011111110101111101",
    "1000000010100010001",
    "1111111010111010101",
    "1000100010101010101",
    "1011101110101010101",
    "1000000000100000101",
    "1111111111111111111",
]
MAZE_ROWS = len(MAZE_GRID)
MAZE_COLS = len(MAZE_GRID[0])
WIDTH, HEIGHT = MAZE_COLS * CELL, MAZE_ROWS * CELL

WEAPON_SIZE = 26
WEAPON_RESPAWN_FRAMES = 360  # 6 segundos a 60 fps


def cell_at(x, y, w, h):
    """Convierte una posicion en pixeles a celda (fila, col)."""
    col = (x + w // 2) // CELL
    row = (y + h // 2) // CELL
    return int(row), int(col)


def cell_center_px(cell, w, h):
    row, col = cell
    x = col * CELL + (CELL - w) // 2
    y = row * CELL + (CELL - h) // 2
    return x, y


def bfs_next_step(start, goal, grid):
    """Devuelve la siguiente celda del camino mas corto de start a goal."""
    if start == goal:
        return start
    rows, cols = len(grid), len(grid[0])
    visited = [[False] * cols for _ in range(rows)]
    prev = {}
    q = deque([start])
    visited[start[0]][start[1]] = True
    found = False
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            found = True
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "0" and not visited[nr][nc]:
                visited[nr][nc] = True
                prev[(nr, nc)] = (r, c)
                q.append((nr, nc))
    if not found:
        return start
    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path[1] if len(path) > 1 else start


class GameSprite(sprite.Sprite):
    def __init__(self, player_image, player_x, player_y, player_speed, w, h):
        super().__init__()
        self.image = transform.scale(image.load(player_image), (w, h))
        self.speed = player_speed
        self.rect = self.image.get_rect()
        self.rect.x = player_x
        self.rect.y = player_y

    def reset(self):
        window.blit(self.image, (self.rect.x, self.rect.y))


class Player(GameSprite):
    def update(self):
        key_press = key.get_pressed()
        if key_press[K_UP]:
            self.rect.y -= self.speed
        if key_press[K_DOWN]:
            self.rect.y += self.speed
        if key_press[K_LEFT]:
            self.rect.x -= self.speed
        if key_press[K_RIGHT]:
            self.rect.x += self.speed
        self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))


class Enemy(GameSprite):
    """El cyborg persigue al heroe todo el tiempo (sin patrulla, sin bucle)."""

    def __init__(self, player_image, player_x, player_y, player_speed, w, h, grid):
        super().__init__(player_image, player_x, player_y, player_speed, w, h)
        self.grid = grid
        self.start_x = player_x
        self.start_y = player_y

    def respawn(self):
        """Vuelve a su posicion inicial para retomar la persecucion."""
        self.rect.x = self.start_x
        self.rect.y = self.start_y

    def update(self, hero_rect):
        my_cell = cell_at(self.rect.x, self.rect.y, self.rect.width, self.rect.height)
        target_cell = cell_at(hero_rect.x, hero_rect.y, hero_rect.width, hero_rect.height)

        next_cell = bfs_next_step(my_cell, target_cell, self.grid)
        tx, ty = cell_center_px(next_cell, self.rect.width, self.rect.height)

        dx = tx - self.rect.x
        dy = ty - self.rect.y
        if dx > 0:
            self.rect.x += min(self.speed, dx)
        elif dx < 0:
            self.rect.x -= min(self.speed, -dx)
        if dy > 0:
            self.rect.y += min(self.speed, dy)
        elif dy < 0:
            self.rect.y -= min(self.speed, -dy)


class Wall(sprite.Sprite):
    def __init__(self, x, y, size, group):
        super().__init__(group)
        self.image = Surface((size, size))
        self.image.fill((34, 120, 20))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw_wall(self):
        window.blit(self.image, (self.rect.x, self.rect.y))


def build_walls(grid):
    """Genera el grupo de paredes a partir de la cuadricula (1 = seto)."""
    group = sprite.Group()
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if grid[row][col] == "1":
                Wall(col * CELL, row * CELL, CELL, group)
    return group


def draw_weapon(x, y):
    """Dibuja un icono de daga (no requiere ninguna imagen nueva)."""
    draw.polygon(window, (225, 225, 230), [(x + 13, y), (x + 19, y + 16), (x + 7, y + 16)])
    draw.rect(window, (95, 60, 20), (x + 9, y + 16, 8, 9))
    draw.rect(window, (110, 110, 115), (x + 4, y + 14, 18, 4))


# ---- Definicion de niveles ----
# "weapons" son celdas (fila, col) del laberinto donde aparece una daga para recoger.
LEVELS = [
    {
        "grid": MAZE_GRID,
        "hero_start": (8, 42),
        "treasure_pos": (544, 112),
        "enemies": [
            {"start": (547, 151), "speed": 2},
        ],
        "weapons": [(1, 4), (7, 3), (11, 9)],
    },
    {
        "grid": MAZE_GRID,
        "hero_start": (8, 42),
        "treasure_pos": (544, 112),
        "enemies": [
            {"start": (547, 151), "speed": 3},
        ],
        "weapons": [(1, 4), (7, 3), (11, 9)],
    },
    {
        "grid": MAZE_GRID,
        "hero_start": (8, 42),
        "treasure_pos": (544, 112),
        "enemies": [
            {"start": (547, 151), "speed": 3},
            {"start": (43, 331), "speed": 2},
        ],
        "weapons": [(1, 4), (7, 3), (11, 9), (9, 12)],
    },
]

exit_zone = Rect(0, 36, 36, 36)

window = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Laberinto")

background = transform.scale(image.load("background.jpg"), (WIDTH, HEIGHT))

mixer.init()
mixer.music.load("jungles.ogg")
money = mixer.Sound("money.ogg")
kick = mixer.Sound("kick.ogg")

font.init()
title_font = font.Font(None, 90)
game_font = font.Font(None, 60)
small_font = font.Font(None, 30)
hud_font = font.Font(None, 26)


def center_text(surf, y):
    window.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))


MENU, PLAYING, LEVEL_COMPLETE, LOSE, WIN = range(5)
state = MENU
current_level = 0

hero = None
walls = None
treasure = None
enemies = []
weapons = []
treasure_collected = False
has_weapon = False
kills = 0


def load_level(idx):
    global hero, walls, treasure, enemies, weapons, treasure_collected, has_weapon, kills
    level = LEVELS[idx]
    walls = build_walls(level["grid"])

    hx, hy = level["hero_start"]
    hero = Player("hero.png", hx, hy, 4, 24, 24)

    tx, ty = level["treasure_pos"]
    treasure = GameSprite("treasure.png", tx, ty, 0, 28, 28)

    enemies = []
    for e in level["enemies"]:
        ex, ey = e["start"]
        enemies.append(Enemy("cyborg.png", ex, ey, e["speed"], 22, 22, level["grid"]))

    weapons = []
    for (r, c) in level.get("weapons", []):
        wx, wy = cell_center_px((r, c), WEAPON_SIZE, WEAPON_SIZE)
        weapons.append({"rect": Rect(wx, wy, WEAPON_SIZE, WEAPON_SIZE), "active": True, "timer": 0})

    treasure_collected = False
    has_weapon = False
    kills = 0


game = True
clock = time.Clock()
fps = 60

while game:
    for e in event.get():
        if e.type == QUIT:
            game = False
        if e.type == KEYDOWN:
            if state == MENU and e.key == K_RETURN:
                current_level = 0
                load_level(current_level)
                mixer.music.play(-1)
                state = PLAYING
            elif state == LEVEL_COMPLETE and e.key == K_RETURN:
                current_level += 1
                load_level(current_level)
                state = PLAYING
            elif state == LOSE:
                if e.key == K_r:
                    load_level(current_level)
                    mixer.music.play(-1)
                    state = PLAYING
                elif e.key == K_ESCAPE:
                    mixer.music.stop()
                    state = MENU
            elif state == WIN and e.key == K_RETURN:
                current_level = 0
                state = MENU

    if state == MENU:
        window.blit(background, (0, 0))
        title = title_font.render("LABERINTO", True, (255, 255, 255))
        center_text(title, HEIGHT // 2 - 130)
        info1 = small_font.render("Recoge el tesoro y escapa del cyborg", True, (255, 255, 0))
        center_text(info1, HEIGHT // 2 - 40)
        info2 = small_font.render("Busca dagas en el mapa para defenderte", True, (255, 255, 0))
        center_text(info2, HEIGHT // 2 - 10)
        info3 = small_font.render("Flechas para moverte  -  ENTER para comenzar", True, (255, 255, 255))
        center_text(info3, HEIGHT // 2 + 30)

    elif state == PLAYING:
        window.blit(background, (0, 0))
        for w in walls:
            w.draw_wall()

        for wpn in weapons:
            if wpn["active"]:
                draw_weapon(wpn["rect"].x, wpn["rect"].y)

        hero.reset()
        for en in enemies:
            en.reset()
        if not treasure_collected:
            treasure.reset()

        hero.update()
        for en in enemies:
            en.update(hero.rect)

        # Recoger dagas
        for wpn in weapons:
            if wpn["active"]:
                if hero.rect.colliderect(wpn["rect"]):
                    has_weapon = True
                    wpn["active"] = False
                    wpn["timer"] = WEAPON_RESPAWN_FRAMES
                    money.play()
            else:
                wpn["timer"] -= 1
                if wpn["timer"] <= 0:
                    wpn["active"] = True

        # Recoger el tesoro
        if not treasure_collected and sprite.collide_rect(hero, treasure):
            treasure_collected = True
            money.play()

        if treasure_collected:
            run_text = small_font.render("¡Corre a la salida!", True, (255, 255, 0))
            window.blit(run_text, (WIDTH // 2 - 90, 6))
            if hero.rect.colliderect(exit_zone):
                if current_level + 1 < len(LEVELS):
                    state = LEVEL_COMPLETE
                else:
                    state = WIN
                    mixer.music.stop()

        # Contacto con el cyborg: con daga lo elimina y reaparece, sin daga pierdes
        if state == PLAYING:
            for en in enemies:
                if hero.rect.colliderect(en.rect):
                    if has_weapon:
                        has_weapon = False
                        kills += 1
                        en.respawn()
                        kick.play()
                    else:
                        state = LOSE
                        kick.play()
                        mixer.music.stop()
                    break

        if state == PLAYING and sprite.spritecollide(hero, walls, False):
            state = LOSE
            kick.play()
            mixer.music.stop()

        if state == PLAYING:
            weapon_txt = "Daga: SI" if has_weapon else "Daga: NO"
            hud1 = hud_font.render(weapon_txt, True, (255, 255, 255))
            window.blit(hud1, (8, HEIGHT - 28))
            hud2 = hud_font.render("Cyborgs eliminados: " + str(kills), True, (255, 255, 255))
            window.blit(hud2, (WIDTH - hud2.get_width() - 8, HEIGHT - 28))

    elif state == LEVEL_COMPLETE:
        window.blit(background, (0, 0))
        msg = game_font.render("¡Nivel " + str(current_level + 1) + " completado!", True, (110, 215, 0))
        center_text(msg, HEIGHT // 2 - 30)
        info = small_font.render("Presiona ENTER para continuar", True, (255, 255, 255))
        center_text(info, HEIGHT // 2 + 30)

    elif state == LOSE:
        window.blit(background, (0, 0))
        msg = game_font.render("YOU LOSE!", True, (250, 0, 0))
        center_text(msg, HEIGHT // 2 - 30)
        info = small_font.render("R para reintentar  -  ESC para el menu", True, (255, 255, 255))
        center_text(info, HEIGHT // 2 + 30)

    elif state == WIN:
        window.blit(background, (0, 0))
        msg = game_font.render("¡GANASTE EL JUEGO!", True, (110, 215, 0))
        center_text(msg, HEIGHT // 2 - 30)
        info = small_font.render("Presiona ENTER para volver al menu", True, (255, 255, 255))
        center_text(info, HEIGHT // 2 + 30)

    display.update()
    clock.tick(fps)