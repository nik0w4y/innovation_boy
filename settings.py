import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_tmx_path(tmx_filename):
    return os.path.join(BASE_DIR, "data", "tmx", tmx_filename)

def get_level_path(level_name):
    return os.path.join(BASE_DIR, "data", "tmx", f"{level_name}.tmx")

def get_interaction_txt_path(interaction_name):
    return os.path.join(BASE_DIR, "data", "txt", f"{interaction_name}.txt")

###########################
#  KONFIGURATIONEN        #
###########################

# Screen-Dimensionen
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320

# Frames per second
FPS = 60

# Tilegröße
TILE_SIZE = 32

# Overworld-Player Speed für jede Richtung
OVERWORLD_PLAYER_SPEED_UP = 200
OVERWORLD_PLAYER_SPEED_DOWN =245
OVERWORLD_PLAYER_SPEED_LEFT = 200
OVERWORLD_PLAYER_SPEED_RIGHT = 245

# Level-Player Speed & Jump
LEVEL_PLAYER_SPEED = 200
LEVEL_JUMP_STRENGTH = 400  # Intern: JUMP_SPEED = -LEVEL_JUMP_STRENGTH

# Level-Player Spawn (x, y in Pixel)
LEVEL_PLAYER_SPAWN = (64, 700)

# Liste der Level-/Hitbox-Namen
LEVEL_HITBOXES = [
    "level_werkstätte",
    "level_klasse",
    "level_klasse2",
    "level_labs",
    "level_turnsaal",
    "sekretariat",
]

# Neue Liste für Interaktionen im Format:
# [hitboxName, direction, hitboxName, direction, ...]
INTERACTION_HITBOXES = [
    "interaction1", "UP",
    "interaction2", "UP",
]

# Player-/Physik-Werte
PLAYER_WIDTH = 28
PLAYER_HEIGHT = 60
GRAVITY = 800
MAX_FALL_SPEED = 1000
RESPAWN_Y_LIMIT = 1000  # Y-Koordinate: darunter => Respawn

# Farben
RED = (255, 0, 0)
WHITE = (255, 255, 255)
COIN_GOLD = (251, 223, 54)

# COIN-Animation
COIN_ANIMATION_SPEED = 0.15

# Pause-Menü / UI
PAUSE_BACKGROUND_PATH = os.path.join(BASE_DIR, "graphics", "Background", "pause_ui.png")
PAUSE_BUTTON_SPRITE_PATH = os.path.join(BASE_DIR, "graphics", "Background", "pause_ui_button.png")
PAUSE_BUTTON_WIDTH = 288
PAUSE_BUTTON_HEIGHT = 48
PAUSE_BUTTON_FONT_SIZE = 20

PAUSE_BUTTON_POS_RESUME = (SCREEN_WIDTH // 2, 150)
PAUSE_BUTTON_POS_SETTINGS = (SCREEN_WIDTH // 2, 210)
PAUSE_BUTTON_POS_QUIT = (SCREEN_WIDTH // 2, 270)
PAUSE_BUTTON_TEXT = ("Weiter", "Einstellungen", "Verlassen")

COIN_AMOUNT = 30
