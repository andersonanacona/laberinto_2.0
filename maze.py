from pygame import *
from collections import deque

# ---- Cuadricula logica del laberinto: 1 = seto, 0 = pasillo (celdas de 36px) ----
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


def cell_at(x, y, w, h):
    """Convierte una posicion en pixeles (esquina superior izq de un sprite) a celda (fila, col)."""
    col = (x + w // 2) // CELL
    row = (y + h // 2) // CELL
    return int(row), int(col)


def bfs_next_step(start, goal):
    """Devuelve la siguiente celda del camino mas corto de start a goal, respetando los setos."""
    if start == goal:
        return start
    visited = [[False] * MAZE_COLS for _ in range(MAZE_ROWS)]
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
            if 0 <= nr < MAZE_ROWS and 0 <= nc < MAZE_COLS and MAZE_GRID[nr][nc] == "0" and not visited[nr][nc]:
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
    def update(self, walls):
        key_press = key.get_pressed()

        if key_press[K_UP]:
            self.rect.y -= self.speed
        if key_press[K_DOWN]:
            self.rect.y += self.speed
        if key_press[K_LEFT]:
            self.rect.x -= self.speed
        if key_press[K_RIGHT]:
            self.rect.x += self.speed

        # Limites de la ventana
        self.rect.x = max(0, min(self.rect.x, WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, HEIGHT - self.rect.height))


class Enemy(GameSprite):
    def __init__(self, player_image, player_x, player_y, player_speed, w, h, patrol_cells):
        super().__init__(player_image, player_x, player_y, player_speed, w, h)
        self.patrol_cells = patrol_cells
        self.patrol_index = 0
        self.chasing = False
        self.chase_speed = player_speed + 2

    def start_chase(self):
        self.chasing = True

    def _cell_center_px(self, cell):
        row, col = cell
        x = col * CELL + (CELL - self.rect.width) // 2
        y = row * CELL + (CELL - self.rect.height) // 2
        return x, y

    def update(self, hero_rect=None):
        my_cell = cell_at(self.rect.x, self.rect.y, self.rect.width, self.rect.height)

        if self.chasing and hero_rect is not None:
            target_cell = cell_at(hero_rect.x, hero_rect.y, hero_rect.width, hero_rect.height)
            speed = self.chase_speed
        else:
            target_cell = self.patrol_cells[self.patrol_index]
            if my_cell == target_cell:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_cells)
                target_cell = self.patrol_cells[self.patrol_index]
            speed = self.speed

        next_cell = bfs_next_step(my_cell, target_cell)
        tx, ty = self._cell_center_px(next_cell)

        dx = tx - self.rect.x
        dy = ty - self.rect.y
        if dx > 0:
            self.rect.x += min(speed, dx)
        elif dx < 0:
            self.rect.x -= min(speed, -dx)
        if dy > 0:
            self.rect.y += min(speed, dy)
        elif dy < 0:
            self.rect.y -= min(speed, -dy)


walls = sprite.Group()


class Wall(sprite.Sprite):
    def __init__(self, x, y, width, height, color_r, color_g, color_b):
        super().__init__(walls)
        self.width = width
        self.height = height
        self.image = Surface((self.width, self.height))
        self.image.fill((color_r, color_g, color_b))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def draw_wall(self):
        window.blit(self.image, (self.rect.x, self.rect.y))


# ---- Dimensiones basadas en el laberinto (19x13 celdas de 36px) ----
WIDTH, HEIGHT = 684, 468

# ---- Paredes: laberinto generado por DFS (garantizado resoluble) ----
wall_list = [
    Wall(0, 0, 684, 36, 34, 120, 20),
    Wall(72, 36, 36, 36, 34, 120, 20),
    Wall(288, 36, 36, 36, 34, 120, 20),
    Wall(648, 36, 36, 36, 34, 120, 20),
    Wall(0, 72, 36, 36, 34, 120, 20),
    Wall(72, 72, 36, 36, 34, 120, 20),
    Wall(144, 72, 36, 36, 34, 120, 20),
    Wall(216, 72, 36, 36, 34, 120, 20),
    Wall(288, 72, 180, 36, 34, 120, 20),
    Wall(504, 72, 108, 36, 34, 120, 20),
    Wall(648, 72, 36, 36, 34, 120, 20),
    Wall(0, 108, 36, 36, 34, 120, 20),
    Wall(72, 108, 36, 36, 34, 120, 20),
    Wall(144, 108, 36, 36, 34, 120, 20),
    Wall(216, 108, 36, 36, 34, 120, 20),
    Wall(432, 108, 36, 36, 34, 120, 20),
    Wall(504, 108, 36, 36, 34, 120, 20),
    Wall(576, 108, 36, 36, 34, 120, 20),
    Wall(648, 108, 36, 36, 34, 120, 20),
    Wall(0, 144, 36, 36, 34, 120, 20),
    Wall(72, 144, 36, 36, 34, 120, 20),
    Wall(144, 144, 36, 36, 34, 120, 20),
    Wall(216, 144, 180, 36, 34, 120, 20),
    Wall(432, 144, 36, 36, 34, 120, 20),
    Wall(504, 144, 36, 36, 34, 120, 20),
    Wall(576, 144, 36, 36, 34, 120, 20),
    Wall(648, 144, 36, 36, 34, 120, 20),
    Wall(0, 180, 36, 36, 34, 120, 20),
    Wall(72, 180, 36, 36, 34, 120, 20),
    Wall(144, 180, 36, 36, 34, 120, 20),
    Wall(360, 180, 36, 36, 34, 120, 20),
    Wall(432, 180, 36, 36, 34, 120, 20),
    Wall(576, 180, 36, 36, 34, 120, 20),
    Wall(648, 180, 36, 36, 34, 120, 20),
    Wall(0, 216, 36, 36, 34, 120, 20),
    Wall(72, 216, 252, 36, 34, 120, 20),
    Wall(360, 216, 36, 36, 34, 120, 20),
    Wall(432, 216, 180, 36, 34, 120, 20),
    Wall(648, 216, 36, 36, 34, 120, 20),
    Wall(0, 252, 36, 36, 34, 120, 20),
    Wall(288, 252, 36, 36, 34, 120, 20),
    Wall(360, 252, 36, 36, 34, 120, 20),
    Wall(504, 252, 36, 36, 34, 120, 20),
    Wall(648, 252, 36, 36, 34, 120, 20),
    Wall(0, 288, 252, 36, 34, 120, 20),
    Wall(288, 288, 36, 36, 34, 120, 20),
    Wall(360, 288, 108, 36, 34, 120, 20),
    Wall(504, 288, 36, 36, 34, 120, 20),
    Wall(576, 288, 36, 36, 34, 120, 20),
    Wall(648, 288, 36, 36, 34, 120, 20),
    Wall(0, 324, 36, 36, 34, 120, 20),
    Wall(144, 324, 36, 36, 34, 120, 20),
    Wall(288, 324, 36, 36, 34, 120, 20),
    Wall(360, 324, 36, 36, 34, 120, 20),
    Wall(432, 324, 36, 36, 34, 120, 20),
    Wall(504, 324, 36, 36, 34, 120, 20),
    Wall(576, 324, 36, 36, 34, 120, 20),
    Wall(648, 324, 36, 36, 34, 120, 20),
    Wall(0, 360, 36, 36, 34, 120, 20),
    Wall(72, 360, 108, 36, 34, 120, 20),
    Wall(216, 360, 108, 36, 34, 120, 20),
    Wall(360, 360, 36, 36, 34, 120, 20),
    Wall(432, 360, 36, 36, 34, 120, 20),
    Wall(504, 360, 36, 36, 34, 120, 20),
    Wall(576, 360, 36, 36, 34, 120, 20),
    Wall(648, 360, 36, 36, 34, 120, 20),
    Wall(0, 396, 36, 36, 34, 120, 20),
    Wall(360, 396, 36, 36, 34, 120, 20),
    Wall(576, 396, 36, 36, 34, 120, 20),
    Wall(648, 396, 36, 36, 34, 120, 20),
    Wall(0, 432, 684, 36, 34, 120, 20),
]

hero = Player("hero.png", 8, 42, 4, 24, 24)
# Cyborg en la celda (4,15), justo debajo del tesoro (la unica celda conectada a la meta).
# Patrulla yendo y viniendo entre esa celda y la siguiente, ambas dentro del pasillo real.
cyborg = Enemy("cyborg.png", 547, 151, 2, 22, 22, patrol_cells=[(4, 15), (5, 15)])
tesoro = GameSprite("treasure.png", 544, 112, 0, 28, 28)

# Zona de escape: la misma entrada del laberinto. Llegar aqui con el tesoro = victoria
exit_zone = Rect(0, 36, 36, 36)
treasure_collected = False

window = display.set_mode((WIDTH, HEIGHT))
display.set_caption("Laberinto")

background = transform.scale(image.load("background.jpg"), (WIDTH, HEIGHT))

game = True
clock = time.Clock()
fps = 60

mixer.init()
mixer.music.load("jungles.ogg")
mixer.music.play()
money = mixer.Sound("money.ogg")
kick = mixer.Sound("kick.ogg")

font.init()
game_font = font.Font(None, 60)
small_font = font.Font(None, 34)
win_text = game_font.render("YOU WIN!", True, (110, 215, 0))
lose_text = game_font.render("YOU LOSE!", True, (250, 0, 0))
run_text = small_font.render("¡Corre a la salida!", True, (255, 255, 0))

finished = False

while game:
    for e in event.get():
        if e.type == QUIT:
            game = False

    if not finished:
        window.blit(background, (0, 0))

        for w in walls:
            w.draw_wall()

        hero.reset()
        cyborg.reset()
        if not treasure_collected:
            tesoro.reset()

        hero.update(walls)
        cyborg.update(hero.rect)

        # El heroe agarra el tesoro -> el cyborg empieza a perseguirlo
        if not treasure_collected and sprite.collide_rect(hero, tesoro):
            treasure_collected = True
            money.play()
            cyborg.start_chase()

        if treasure_collected:
            window.blit(run_text, (WIDTH // 2 - 100, 10))
            # Si el heroe llega a la salida con el tesoro -> victoria
            if hero.rect.colliderect(exit_zone):
                finished = True
                window.blit(win_text, (WIDTH // 2 - 110, HEIGHT // 2 - 30))
                mixer.music.stop()

        # El cyborg atrapa al heroe, o el heroe toca una pared -> derrota
        if sprite.collide_rect(hero, cyborg) or sprite.spritecollide(hero, walls, False):
            finished = True
            kick.play()
            window.blit(lose_text, (WIDTH // 2 - 120, HEIGHT // 2 - 30))
            mixer.music.stop()

    display.update()
    clock.tick(fps)