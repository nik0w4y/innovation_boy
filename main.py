###########################
#        main.py          #
###########################

import os
import sys
import pygame

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TILE_SIZE,
    # Vier Richtungs-Geschwindigkeiten für Overworld:
    OVERWORLD_PLAYER_SPEED_UP,
    OVERWORLD_PLAYER_SPEED_DOWN,
    OVERWORLD_PLAYER_SPEED_LEFT,
    OVERWORLD_PLAYER_SPEED_RIGHT,

    LEVEL_PLAYER_SPEED, LEVEL_JUMP_STRENGTH,
    LEVEL_PLAYER_SPAWN,
    LEVEL_HITBOXES,
    INTERACTION_HITBOXES,
    PLAYER_WIDTH, PLAYER_HEIGHT, GRAVITY, MAX_FALL_SPEED, RESPAWN_Y_LIMIT,
    RED, WHITE, COIN_GOLD,
    BASE_DIR,
    COIN_ANIMATION_SPEED,
    PAUSE_BACKGROUND_PATH,
    PAUSE_BUTTON_SPRITE_PATH,
    PAUSE_BUTTON_WIDTH,
    PAUSE_BUTTON_HEIGHT,
    PAUSE_BUTTON_FONT_SIZE,
    PAUSE_BUTTON_POS_RESUME,
    PAUSE_BUTTON_POS_SETTINGS,
    PAUSE_BUTTON_POS_QUIT,
    PAUSE_BUTTON_TEXT,
    COIN_AMOUNT,
    get_tmx_path, get_level_path, get_interaction_txt_path
)

MOVE_SPEED = LEVEL_PLAYER_SPEED
JUMP_SPEED = -LEVEL_JUMP_STRENGTH

# Global Variables (Coin-System)
coin_count = 0
COLLECTED_COINS = set()

###########################
#   FADE FUNCTIONS        #
###########################
def fade_out_current_scene(screen, clock, duration=1.0):
    old_scene = screen.copy()
    black_surface = pygame.Surface(screen.get_size())
    black_surface.fill((0, 0, 0))

    alpha = 0
    alpha_increase_per_second = 255 / duration
    fading = True

    while fading:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        alpha += alpha_increase_per_second * dt
        if alpha >= 255:
            alpha = 255
            fading = False

        faded_frame = old_scene.copy()
        black_surface.set_alpha(int(alpha))
        faded_frame.blit(black_surface, (0, 0))
        screen.blit(faded_frame, (0, 0))
        pygame.display.flip()

def fade_in_new_scene(screen, clock, draw_scene, duration=1.0):
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))
    alpha = 255
    alpha_decrease_per_second = 255 / duration
    fading = True

    while fading:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        draw_scene()
        alpha -= alpha_decrease_per_second * dt
        if alpha <= 0:
            alpha = 0
            fading = False

        overlay.set_alpha(int(alpha))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()

def fade_in_black_screen(screen, clock, duration=1.0):
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))

    alpha = 255
    alpha_decrease_per_second = 255 / duration
    fading = True

    while fading:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((0, 0, 0))
        alpha -= alpha_decrease_per_second * dt
        if alpha <= 0:
            alpha = 0
            fading = False

        overlay.set_alpha(int(alpha))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()

###########################
#      OVERWORLD          #
###########################
class CameraOverworld:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2
        x = max(-(self.width - SCREEN_WIDTH), min(0, x))
        y = max(-(self.height - SCREEN_HEIGHT), min(0, y))
        self.camera = pygame.Rect(x, y, self.width, self.height)

class PlayerOverworld(pygame.sprite.Sprite):
    def __init__(self, x, y, animations, map_width, map_height):
        super().__init__()
        self.animations = animations
        # Use the sprite size as-is (no manual width override)
        self.image = animations["standing"][0]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.direction = "down"
        self.animation_frame = 0
        self.animation_timer = 0

        # Vier separate Geschwindigkeiten (aus settings.py)
        self.speed_up = OVERWORLD_PLAYER_SPEED_UP
        self.speed_down = OVERWORLD_PLAYER_SPEED_DOWN
        self.speed_left = OVERWORLD_PLAYER_SPEED_LEFT
        self.speed_right = OVERWORLD_PLAYER_SPEED_RIGHT

        self.is_moving = False
        self.map_width = map_width
        self.map_height = map_height
        self.can_move = True  # Lock movement if a textbox is open

    def update(self, dt, keys, terrain_layer_index, tmx_data, collision_rects):
        # Lock movement if interacting
        if not self.can_move:
            return

        self.is_moving = False
        dx, dy = 0, 0

        # Determine desired movement with directional speeds
        if keys[pygame.K_w]:
            dy -= self.speed_up * dt
            self.direction = "up"
            self.is_moving = True
        if keys[pygame.K_s]:
            dy += self.speed_down * dt
            self.direction = "down"
            self.is_moving = True
        if keys[pygame.K_a]:
            dx -= self.speed_left * dt
            self.direction = "left"
            self.is_moving = True
        if keys[pygame.K_d]:
            dx += self.speed_right * dt
            self.direction = "right"
            self.is_moving = True

        # Move in X first (for better "wall sliding")
        next_rect = self.rect.copy()
        next_rect.x += dx
        if not self.check_collision(next_rect, terrain_layer_index, tmx_data, collision_rects):
            self.rect.x = next_rect.x

        # Move in Y
        next_rect = self.rect.copy()
        next_rect.y += dy
        if not self.check_collision(next_rect, terrain_layer_index, tmx_data, collision_rects):
            self.rect.y = next_rect.y

        # Animation handling
        if self.is_moving:
            self.animation_timer += dt
            if self.animation_timer >= 0.15:
                anim_list = self.animations[self.direction]
                self.animation_frame = (self.animation_frame + 1) % len(anim_list)
                self.animation_timer = 0
            self.image = self.animations[self.direction][self.animation_frame]
        else:
            dirs = ["down", "left", "right", "up"]
            if self.direction in dirs:
                idx = dirs.index(self.direction)
                self.image = self.animations["standing"][idx]
                self.animation_frame = 0
                self.animation_timer = 0

    def check_collision(self, test_rect, terrain_layer_index, tmx_data, collision_rects):
        """Return True if there's a collision with terrain or collidable object."""
        # Check map boundaries
        if test_rect.left < 0 or test_rect.right > self.map_width:
            return True
        if test_rect.top < 0 or test_rect.bottom > self.map_height:
            return True

        # Tile-based collision (using terrain_layer)
        if terrain_layer_index is not None:
            corners = [
                (test_rect.left, test_rect.top),
                (test_rect.right - 1, test_rect.top),
                (test_rect.left, test_rect.bottom - 1),
                (test_rect.right - 1, test_rect.bottom - 1),
            ]
            for corner_x, corner_y in corners:
                tile_x = int(corner_x // TILE_SIZE)
                tile_y = int(corner_y // TILE_SIZE)
                if 0 <= tile_x < tmx_data.width and 0 <= tile_y < tmx_data.height:
                    gid = tmx_data.get_tile_gid(tile_x, tile_y, terrain_layer_index)
                    # If gid == 0, we treat it as collision in your code
                    if gid == 0:
                        return True

        # Object-based collision
        if collision_rects:
            for c_rect in collision_rects:
                if test_rect.colliderect(c_rect):
                    return True

        return False

def get_object_by_name(tmx_data, name):
    for obj in tmx_data.objects:
        if obj.name == name:
            return obj
    return None

###########################
#   DRAW OVERWORLD SCENE  #
###########################
def draw_overworld_scene(
    screen, camera_ow, tmx_data, terrain_layer_index,
    walls_layer, design_layer, shading_layer, all_sprites,
    mark_removed=False
):
    """Draws the overworld. 
       If mark_removed=True, then skip drawing 'mark' object from the map."""
    screen.fill((0, 0, 0))

    # Terrain
    if terrain_layer_index is not None:
        terrain_layer = tmx_data.layers[terrain_layer_index]
        for x, y, tile in terrain_layer.tiles():
            screen.blit(tile, (x*TILE_SIZE + camera_ow.camera.x, y*TILE_SIZE + camera_ow.camera.y))

    # Sprites (player, etc.)
    for spr in all_sprites:
        screen.blit(spr.image, camera_ow.apply(spr))

    # Walls
    if walls_layer:
        for x, y, tile in walls_layer.tiles():
            screen.blit(tile, (x*TILE_SIZE + camera_ow.camera.x, y*TILE_SIZE + camera_ow.camera.y))

    # Design
    if design_layer:
        for x, y, tile in design_layer.tiles():
            screen.blit(tile, (x*TILE_SIZE + camera_ow.camera.x, y*TILE_SIZE + camera_ow.camera.y))

    # Shading
    if shading_layer:
        for x, y, tile in shading_layer.tiles():
            screen.blit(tile, (x*TILE_SIZE + camera_ow.camera.x, y*TILE_SIZE + camera_ow.camera.y))

    # Object layers
    for obj_layer in tmx_data.objectgroups:
        for obj in obj_layer:
            # If user wants 'mark' hidden, skip it
            if mark_removed and hasattr(obj, "name") and obj.name == "mark":
                continue

            # GID-based object (tile object)
            if getattr(obj, 'gid', None):
                tile_img = tmx_data.get_tile_image_by_gid(obj.gid)
                if tile_img:
                    screen.blit(tile_img, (obj.x + camera_ow.camera.x, obj.y + camera_ow.camera.y))
            # Image-based object
            elif getattr(obj, 'image', None):
                image = pygame.image.load(obj.image).convert_alpha()
                screen.blit(image, (obj.x + camera_ow.camera.x, obj.y + camera_ow.camera.y))

    # Coin counter
    draw_coin_counter(screen)

############################
#   PAUSE MENU LOGIC       #
############################
class Button:
    """A button with three states: normal, hover, click, and selected via keyboard."""
    def __init__(self, text, x, y):
        self.sprite_sheet = pygame.image.load(PAUSE_BUTTON_SPRITE_PATH).convert_alpha()

        # Extract 3 frames (horizontal)
        self.frames = []
        for i in range(3):
            frame_rect = pygame.Rect(i * PAUSE_BUTTON_WIDTH, 0, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
            if frame_rect.right > self.sprite_sheet.get_width() or frame_rect.bottom > self.sprite_sheet.get_height():
                frame_rect.width = min(PAUSE_BUTTON_WIDTH, self.sprite_sheet.get_width() - frame_rect.x)
                frame_rect.height = min(PAUSE_BUTTON_HEIGHT, self.sprite_sheet.get_height() - frame_rect.y)
            frame_surf = self.sprite_sheet.subsurface(frame_rect)
            self.frames.append(frame_surf)

        self.current_frame = 0
        self.rect = pygame.Rect(0, 0, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
        self.rect.center = (x, y)

        font = pygame.font.SysFont(None, PAUSE_BUTTON_FONT_SIZE)
        self.text_surface = font.render(text, True, WHITE)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def set_selected(self, selected):
        self.current_frame = 1 if selected else 0

    def set_clicked(self, clicked):
        self.current_frame = 2 if clicked else 0

    def draw(self, screen):
        screen.blit(self.frames[self.current_frame], self.rect)
        self.text_rect.center = self.rect.center
        screen.blit(self.text_surface, self.text_rect)

    def is_clicked(self, mouse_pos, mouse_up_event):
        return self.rect.collidepoint(mouse_pos) and mouse_up_event

class PauseMenu:
    def __init__(self):
        self.bg_image = pygame.image.load(PAUSE_BACKGROUND_PATH).convert_alpha()
        self.bg_rect = self.bg_image.get_rect(topleft=(0, 0))

        self.buttons = [
            Button(PAUSE_BUTTON_TEXT[0], *PAUSE_BUTTON_POS_RESUME),
            Button(PAUSE_BUTTON_TEXT[1], *PAUSE_BUTTON_POS_SETTINGS),
            Button(PAUSE_BUTTON_TEXT[2], *PAUSE_BUTTON_POS_QUIT)
        ]
        self.selected_button_index = 0
        self.buttons[self.selected_button_index].set_selected(True)

        self.just_clicked_button = None

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_w, pygame.K_UP):
                    self.buttons[self.selected_button_index].set_selected(False)
                    self.selected_button_index = (self.selected_button_index - 1) % len(self.buttons)
                    self.buttons[self.selected_button_index].set_selected(True)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.buttons[self.selected_button_index].set_selected(False)
                    self.selected_button_index = (self.selected_button_index + 1) % len(self.buttons)
                    self.buttons[self.selected_button_index].set_selected(True)
                elif event.key == pygame.K_RETURN:
                    selected_button = self.buttons[self.selected_button_index]
                    if selected_button == self.buttons[0]:
                        self.just_clicked_button = "resume"
                    elif selected_button == self.buttons[1]:
                        self.just_clicked_button = "settings"
                    elif selected_button == self.buttons[2]:
                        self.just_clicked_button = "quit"

    def draw(self, screen):
        screen.blit(self.bg_image, self.bg_rect)
        for button in self.buttons:
            button.draw(screen)

###########################
#  COIN-Funktionen        #
###########################
class Coin(pygame.sprite.Sprite):
    def __init__(self, object_id, x, y):
        super().__init__()
        self.object_id = object_id
        self.sheet = pygame.image.load(
            os.path.join(BASE_DIR, "graphics", "Objects", "htl_coin.png")
        ).convert_alpha()

        # htl_coin.png = 16 px high, 64 px wide => 4 frames horizontally
        self.frames = self.extract_coin_frames(self.sheet, 16, 16, 1, 4)
        self.frame_index = 0
        self.animation_timer = 0.0

        self.rect = pygame.Rect(x, y, 16, 16)
        self.image = self.frames[0]

    def extract_coin_frames(self, sheet, width, height, rows, cols):
        frames_ = []
        for row in range(rows):
            for col in range(cols):
                x = col * width
                y = row * height
                if x + width > sheet.get_width() or y + height > sheet.get_height():
                    continue
                frame_surf = sheet.subsurface((x, y, width, height))
                frames_.append(frame_surf)
        return frames_

    def update(self, dt):
        global COIN_ANIMATION_SPEED
        self.animation_timer += dt
        if self.animation_timer >= COIN_ANIMATION_SPEED:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]
            self.animation_timer = 0

def load_coins_from_tmx(tmx_data):
    coins_group = pygame.sprite.Group()
    box_layer = None
    for obj_layer in tmx_data.objectgroups:
        if obj_layer.name == "Boxes":
            box_layer = obj_layer
            break
    if not box_layer:
        return coins_group

    for coin_obj in box_layer:
        if coin_obj.name == "coin":
            if coin_obj.id not in COLLECTED_COINS:
                coin_sprite = Coin(coin_obj.id, coin_obj.x, coin_obj.y)
                coins_group.add(coin_sprite)

    return coins_group

def check_coin_collisions(player_rect, coins_group):
    global coin_count, COLLECTED_COINS

    collided_coins = []
    for coin in coins_group:
        if player_rect.colliderect(coin.rect):
            coin_count += 1
            COLLECTED_COINS.add(coin.object_id)
            collided_coins.append(coin)

    for c in collided_coins:
        coins_group.remove(c)

def draw_coin_counter(screen):
    coin_sheet_path = os.path.join(BASE_DIR, "graphics", "Objects", "htl_coin.png")
    if not os.path.exists(coin_sheet_path):
        print(f"ERROR: Coin sprite '{coin_sheet_path}' not found!")
        return

    coin_sheet = pygame.image.load(coin_sheet_path).convert_alpha()
    if coin_sheet.get_width() < 16 or coin_sheet.get_height() < 16:
        print("ERROR: Coin sprite is too small.")
        return

    coin_icon = coin_sheet.subsurface((0, 0, 16, 16))
    screen.blit(coin_icon, (10, 10))

    font = pygame.font.SysFont(None, 24)
    count_surf = font.render(str(coin_count), True, COIN_GOLD)
    screen.blit(count_surf, (30, 12))

def get_collidable_tiles(tmx_data, layer_name="Terrain"):
    tiles = []
    terrain_layer = tmx_data.get_layer_by_name(layer_name)
    for x, y, gid in terrain_layer:
        if gid:
            tile_rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            tiles.append(tile_rect)
    return tiles

def draw_platformer_scene(screen, camera_level, tmx_data, terrain_layer, player_level_sprite, coin_group):
    screen.fill(WHITE)
    for x, y, gid in terrain_layer:
        if gid:
            tile_img = tmx_data.get_tile_image_by_gid(gid)
            if tile_img:
                tile_rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                screen.blit(tile_img, camera_level.apply(tile_rect))

    for coin in coin_group:
        screen.blit(coin.image, camera_level.apply(coin.rect))

    screen.blit(player_level_sprite.image, camera_level.apply(player_level_sprite.rect))

    draw_coin_counter(screen)

############################
#  LEVEL CLASSES & SETUP   #
############################
class CameraLevel:
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, rect):
        return rect.move(-self.camera_rect.x, -self.camera_rect.y)

    def update(self, target):
        x = target.rect.centerx - SCREEN_WIDTH // 2
        y = target.rect.centery - SCREEN_HEIGHT // 2
        x = max(0, min(x, self.width - SCREEN_WIDTH))
        y = max(0, min(y, self.height - SCREEN_HEIGHT))
        self.camera_rect = pygame.Rect(x, y, SCREEN_WIDTH, SCREEN_HEIGHT)

class PlayerLevel(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.spawn_x = x
        self.spawn_y = y
        self.sheet = pygame.image.load(
            os.path.join(BASE_DIR, "graphics", "player_level.png")
        ).convert_alpha()

        self.frames = self.extract_frames(self.sheet, 32, 64, 3, 2)
        self.animations = {
            "front_idle": self.frames[0],
            "back_idle": self.frames[1],
            "front_run": [self.frames[2], self.frames[4]],
            "back_run": [self.frames[3], self.frames[5]],
        }

        self.direction = "front"
        self.is_running = False
        self.frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.15

        # Use a fixed bounding box for platformer
        self.image = self.animations["front_idle"]
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)

        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False

    def extract_frames(self, sheet, width, height, rows, cols):
        frames_ = []
        for row in range(rows):
            for col in range(cols):
                x = col * width
                y = row * height
                if x + width > sheet.get_width() or y + height > sheet.get_height():
                    continue
                frame_surf = sheet.subsurface((x, y, width, height))
                frames_.append(frame_surf)
        return frames_

    def respawn(self):
        print("Respawning player (fell below map).")
        self.rect.x = self.spawn_x
        self.rect.y = self.spawn_y
        self.velocity = pygame.Vector2(0, 0)

    def update(self, dt, tiles, keys):
        # Horizontal
        if keys[pygame.K_a]:
            self.velocity.x = -MOVE_SPEED
            self.direction = "back"
            self.is_running = True
        elif keys[pygame.K_d]:
            self.velocity.x = MOVE_SPEED
            self.direction = "front"
            self.is_running = True
        else:
            self.velocity.x = 0
            self.is_running = False

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity.y = JUMP_SPEED
            self.on_ground = False

        # Gravity
        self.velocity.y += GRAVITY * dt
        if self.velocity.y > MAX_FALL_SPEED:
            self.velocity.y = MAX_FALL_SPEED

        # Move X
        self.rect.x += self.velocity.x * dt
        self.check_collisions_x(tiles)

        # Move Y
        self.rect.y += self.velocity.y * dt
        self.check_collisions_y(tiles)

        # Check respawn if fell out of world
        if self.rect.top > RESPAWN_Y_LIMIT:
            self.respawn()

        self.animate(dt)

    def check_collisions_x(self, tiles):
        for t_rect in tiles:
            if self.rect.colliderect(t_rect):
                if self.velocity.x > 0:
                    self.rect.right = t_rect.left
                elif self.velocity.x < 0:
                    self.rect.left = t_rect.right
                self.velocity.x = 0

    def check_collisions_y(self, tiles):
        self.on_ground = False
        for t_rect in tiles:
            if self.rect.colliderect(t_rect):
                if self.velocity.y > 0:
                    self.rect.bottom = t_rect.top
                    self.velocity.y = 0
                    self.on_ground = True
                elif self.velocity.y < 0:
                    self.rect.top = t_rect.bottom
                    self.velocity.y = 0

    def animate(self, dt):
        if self.is_running:
            if self.direction == "front":
                anim_frames = self.animations["front_run"]
            else:
                anim_frames = self.animations["back_run"]

            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.frame_index = (self.frame_index + 1) % len(anim_frames)
                self.animation_timer = 0
            self.image = anim_frames[self.frame_index]
        else:
            if self.direction == "front":
                self.image = self.animations["front_idle"]
            else:
                self.image = self.animations["back_idle"]
            self.frame_index = 0
            self.animation_timer = 0

def play_platformer(level_name):
    global COLLECTED_COINS, coin_count

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    pause_menu = PauseMenu()
    level_paused = False

    fade_in_black_screen(screen, clock, duration=1.0)

    from pytmx.util_pygame import load_pygame
    tmx_path = get_level_path(level_name)
    print(f"Loading level: {tmx_path}")
    try:
        tmx_data = load_pygame(tmx_path)
    except FileNotFoundError:
        print(f"ERROR: File '{tmx_path}' not found!")
        return

    terrain_layer = tmx_data.get_layer_by_name("Terrain")
    map_width = tmx_data.width * TILE_SIZE
    map_height = tmx_data.height * TILE_SIZE

    spawn_x, spawn_y = LEVEL_PLAYER_SPAWN
    player_level_sprite = PlayerLevel(spawn_x, spawn_y)

    tiles = get_collidable_tiles(tmx_data, "Terrain")
    camera_level = CameraLevel(map_width, map_height)

    coin_group = load_coins_from_tmx(tmx_data)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    level_paused = not level_paused

        if level_paused:
            pause_menu.update(events)
            if pause_menu.just_clicked_button == "resume":
                level_paused = False
                pause_menu.just_clicked_button = None
            elif pause_menu.just_clicked_button == "quit":
                pygame.quit()
                sys.exit()
            elif pause_menu.just_clicked_button == "settings":
                print("Settings not implemented!")
                pause_menu.just_clicked_button = None

            camera_level.update(player_level_sprite)
            draw_platformer_scene(screen, camera_level, tmx_data, terrain_layer, player_level_sprite, coin_group)
            pause_menu.draw(screen)

        else:
            keys = pygame.key.get_pressed()
            player_level_sprite.update(dt, tiles, keys)
            camera_level.update(player_level_sprite)

            coin_group.update(dt)
            check_coin_collisions(player_level_sprite.rect, coin_group)

            # If the player reaches the far east edge, we return to overworld
            if player_level_sprite.rect.right >= map_width:
                print("Reached east edge; returning to Overworld.")
                fade_out_current_scene(screen, clock, duration=1.0)
                running = False
                break
            else:
                draw_platformer_scene(screen, camera_level, tmx_data, terrain_layer, player_level_sprite, coin_group)

        pygame.display.flip()

############################
#  ENTER LEVEL PROMPT CLASS#
############################
class EnterLevelPrompt:
    def __init__(self, image_path, position):
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Failed to load enter_level image: {e}")
            sys.exit()

        self.rect = self.image.get_rect(center=position)

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)

###########################
# INTERACTION SYSTEM      #
###########################
class InteractionPrompt:
    """Displays a 'Press E to interact' prompt image in the center of the screen."""
    def __init__(self, image_path, position):
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Failed to load interaction image: {e}")
            sys.exit()

        self.rect = self.image.get_rect(center=position)

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Textbox:
    """A textbox that slides in from the bottom and displays text from a .txt file."""
    def __init__(self, image_path, text_lines, width=320, height=64):
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except pygame.error as e:
            print(f"Failed to load textbox image: {e}")
            sys.exit()

        self.width = width
        self.height = height

        self.x = (SCREEN_WIDTH - self.width) // 2
        self.y = SCREEN_HEIGHT
        self.final_y = SCREEN_HEIGHT - self.height
        self.slide_speed = 300
        self.is_sliding_in = True

        self.text_lines = text_lines
        print("[Textbox] Loaded lines:", text_lines)

        self.text_color = (255, 255, 255)  
        self.font = pygame.font.SysFont(None, 20)
        self.line_spacing = 5

    def update(self, dt):
        if self.is_sliding_in:
            self.y -= self.slide_speed * dt
            if self.y <= self.final_y:
                self.y = self.final_y
                self.is_sliding_in = False

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        # Render text lines
        text_area_x = self.x + 10
        text_area_y = self.y + 10
        for line in self.text_lines:
            line_surf = self.font.render(line, True, self.text_color)
            screen.blit(line_surf, (text_area_x, text_area_y))
            text_area_y += line_surf.get_height() + self.line_spacing

def load_interaction_text(interaction_name):
    """
    For 'interaction2', we treat the entire file as two blocks split by the FIRST semicolon.
    - If coin_count > 30 => show ONLY the after-semicolon part.
    - Otherwise => show ONLY the before-semicolon part.
    For any other interaction, just return the whole file as-is.
    """
    global coin_count
    txt_path = get_interaction_txt_path(interaction_name)
    if not os.path.exists(txt_path):
        print(f"WARNING: Interaction text file '{txt_path}' not found!")
        return ["No text found!"]

    with open(txt_path, "r", encoding="utf-8") as f:
        file_contents = f.read()

    # By default, split into lines as-is
    lines = file_contents.splitlines()

    # Special case for interaction2:
    if interaction_name == "interaction2":
        # Check if there's a semicolon in the entire file
        if ";" in file_contents:
            # Split by the FIRST semicolon
            before, after = file_contents.split(";", 1)
            if coin_count > COIN_AMOUNT:
                # Show only the after block
                lines = after.strip().splitlines()
            else:
                # Show only the before block
                lines = before.strip().splitlines()
        else:
            # No semicolon => entire file
            lines = file_contents.splitlines()

    return lines

###########################
#  LOAD COLLISION RECTANGLES
###########################
def load_collision_rects(tmx_data, object_layer_name="Boxes", object_name="collision"):
    collision_rects = []
    for obj_layer in tmx_data.objectgroups:
        if obj_layer.name == object_layer_name:
            for obj in obj_layer:
                if obj.name == object_name:
                    rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    collision_rects.append(rect)
    return collision_rects

###########################
#        MAIN()           #
###########################
def run_overworld():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Overworld")
    clock = pygame.time.Clock()

    pause_menu = PauseMenu()
    overworld_paused = False

    # Convert INTERACTION_HITBOXES list -> dict: {"interaction1":"UP", ...}
    interaction_directions = {}
    for i in range(0, len(INTERACTION_HITBOXES), 2):
        key_name = INTERACTION_HITBOXES[i]
        key_dir = INTERACTION_HITBOXES[i+1]
        interaction_directions[key_name] = key_dir

    from pytmx.util_pygame import load_pygame
    overworld_path = get_tmx_path("overworld.tmx")
    print("Loading TMX:", overworld_path)
    try:
        tmx_data = load_pygame(overworld_path)
    except FileNotFoundError:
        print(f"ERROR: Overworld file '{overworld_path}' not found!")
        return

    map_width = tmx_data.width * TILE_SIZE
    map_height = tmx_data.height * TILE_SIZE

    # Player
    player_sheet_path = os.path.join(BASE_DIR, "graphics", "player.png")
    try:
        player_sheet = pygame.image.load(player_sheet_path).convert_alpha()
    except pygame.error as e:
        print(f"Failed to load player sprite sheet: {e}")
        sys.exit()

    def extract_frames(sheet, width, height, rows, cols):
        frames_ = []
        for row in range(rows):
            for col in range(cols):
                frame = sheet.subsurface((col*width, row*height, width, height))
                frames_.append(frame)
        return frames_

    frames = extract_frames(player_sheet, TILE_SIZE, TILE_SIZE, 4, 3)
    animations = {
        "down": [frames[0], frames[2]],
        "left": [frames[3], frames[5]],
        "right": [frames[6], frames[8]],
        "up": [frames[9], frames[11]],
        "standing": [frames[1], frames[4], frames[7], frames[10]],
    }

    player_obj = get_object_by_name(tmx_data, "player")
    if not player_obj:
        raise ValueError("No object named 'player' found in overworld.tmx!")
    player_ow = PlayerOverworld(player_obj.x, player_obj.y, animations, map_width, map_height)
    camera_ow = CameraOverworld(map_width, map_height)
    all_sprites = pygame.sprite.Group(player_ow)

    # We will need this to remove 'mark' after the second text of interaction2
    mark_removed = False

    # Layers
    terrain_layer_index = None
    walls_layer = None
    design_layer = None
    shading_layer = None

    for i, layer in enumerate(tmx_data.layers):
        if layer.name == "Terrain":
            terrain_layer_index = i
        elif layer.name == "Walls":
            walls_layer = layer
        elif layer.name == "Design":
            design_layer = layer
        elif layer.name == "Shading":
            shading_layer = layer

    def check_box_collision(player_sprite, tmx):
        box_layer = None
        for obj_layer in tmx.objectgroups:
            if obj_layer.name == "Boxes":
                box_layer = obj_layer
                break
        if not box_layer:
            return None

        p_rect = player_sprite.rect
        for box in box_layer:
            box_rect = pygame.Rect(box.x, box.y, box.width, box.height)
            if p_rect.colliderect(box_rect):
                return box.name
        return None

    def draw_overworld_once():
        camera_ow.update(player_ow)
        draw_overworld_scene(
            screen, camera_ow, tmx_data, terrain_layer_index,
            walls_layer, design_layer, shading_layer, all_sprites,
            mark_removed=mark_removed
        )

    # Enter-Level prompt
    enter_level_sheet_path = os.path.join(BASE_DIR, "graphics", "Background", "enter_level.png")
    if not os.path.exists(enter_level_sheet_path):
        print(f"ERROR: Enter level image '{enter_level_sheet_path}' not found!")
        sys.exit()
    enter_level_prompt = EnterLevelPrompt(
        image_path=enter_level_sheet_path,
        position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    )

    # Interaction prompt
    interaction_prompt_path = os.path.join(BASE_DIR, "graphics", "Background", "interaction.png")
    if not os.path.exists(interaction_prompt_path):
        print(f"ERROR: Interaction image '{interaction_prompt_path}' not found!")
        sys.exit()
    interaction_prompt = InteractionPrompt(
        image_path=interaction_prompt_path,
        position=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    )

    # Textbox image
    textbox_img_path = os.path.join(BASE_DIR, "graphics", "Background", "textbox.png")
    if not os.path.exists(textbox_img_path):
        print(f"ERROR: Textbox image '{textbox_img_path}' not found!")
        sys.exit()

    fade_in_new_scene(screen, clock, draw_overworld_once, duration=1.0)

    collision_rects = load_collision_rects(tmx_data, object_layer_name="Boxes", object_name="collision")
    print(f"Loaded {len(collision_rects)} collision rectangles.")

    running = True
    current_hitbox = None
    showing_textbox = None
    just_interacted_hitbox = None

    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    overworld_paused = not overworld_paused

                if event.key == pygame.K_e:
                    # If textbox is open, close it
                    if showing_textbox:
                        showing_textbox = None
                        player_ow.can_move = True

                        # If that was the "second text" from interaction2 (i.e. coin_count > 30)
                        # => Remove 'mark'
                        if just_interacted_hitbox == "interaction2" and coin_count > 30:
                            print("Hiding 'mark' because we used the second text from interaction2.")
                            mark_removed = True

                    else:
                        if current_hitbox:
                            # Level?
                            if current_hitbox in LEVEL_HITBOXES:
                                print(f"Entering level: {current_hitbox}")
                                # 1) Store current position
                                overworld_pos_before_level = player_ow.rect.topleft

                                fade_out_current_scene(screen, clock, duration=1.0)
                                play_platformer(current_hitbox)

                                # 2) Restore position
                                player_ow.rect.topleft = overworld_pos_before_level
                                fade_in_new_scene(screen, clock, draw_overworld_once, duration=1.0)

                            # Interaction?
                            elif current_hitbox in interaction_directions:
                                forced_dir = interaction_directions[current_hitbox].lower()
                                player_ow.direction = forced_dir
                                player_ow.is_moving = False
                                dirs = ["down", "left", "right", "up"]
                                if forced_dir in dirs:
                                    idx = dirs.index(forced_dir)
                                    player_ow.image = animations["standing"][idx]

                                lines = load_interaction_text(current_hitbox)
                                showing_textbox = Textbox(textbox_img_path, lines, width=320, height=64)
                                player_ow.can_move = False
                                just_interacted_hitbox = current_hitbox

        if overworld_paused:
            pause_menu.update(events)
            if pause_menu.just_clicked_button == "resume":
                overworld_paused = False
                pause_menu.just_clicked_button = None
            elif pause_menu.just_clicked_button == "quit":
                pygame.quit()
                sys.exit()
            elif pause_menu.just_clicked_button == "settings":
                print("Settings not implemented (Overworld)!")
                pause_menu.just_clicked_button = None

            draw_overworld_once()
            pause_menu.draw(screen)

        else:
            # Normal Overworld
            keys = pygame.key.get_pressed()
            player_ow.update(dt, keys, terrain_layer_index, tmx_data, collision_rects)
            camera_ow.update(player_ow)

            hitbox_name = check_box_collision(player_ow, tmx_data)
            if hitbox_name:
                current_hitbox = hitbox_name
            else:
                current_hitbox = None
                just_interacted_hitbox = None  # reset if we left the hitbox

            draw_overworld_once()

            # Show prompts if appropriate
            if current_hitbox:
                if current_hitbox in LEVEL_HITBOXES:
                    enter_level_prompt.draw(screen)
                elif current_hitbox in interaction_directions:
                    # Only show the 'Press E' prompt if we haven't just interacted
                    if current_hitbox != just_interacted_hitbox:
                        interaction_prompt.draw(screen)

            # Textbox
            if showing_textbox:
                showing_textbox.update(dt)
                showing_textbox.draw(screen)

        pygame.display.flip()

def main():
    run_overworld()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
