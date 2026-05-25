import pygame
import sys
import random
from pathlib import Path
from io import BytesIO
import zipfile

pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
W, H = 1000, 666
FPS = 60

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("O Enigma da Cabana")
clock = pygame.time.Clock()

# ---------------------------------------------------
# CORES
# ---------------------------------------------------
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GOLD = (255, 220, 120)
GREEN = (80, 220, 120)
RED = (220, 70, 70)

# ---------------------------------------------------
# FONTS
# ---------------------------------------------------
font = pygame.font.SysFont("arial", 28)
font_big = pygame.font.SysFont("arial", 42, bold=True)
font_small = pygame.font.SysFont("arial", 18)

# ---------------------------------------------------
# IMAGENS
# ---------------------------------------------------
ASSET_DIR = Path("cenarios")
BACKGROUND_PATH = ASSET_DIR / "quarto.png"
BACKGROUND_POEM_PATH = ASSET_DIR / "quarto_papel.png"
START_PATH = ASSET_DIR / "inicio.png"

ASSET_DIR_SONS = Path("sons")

background = pygame.image.load(str(BACKGROUND_PATH)).convert()
background = pygame.transform.scale(background, (W, H))

background_poem = pygame.image.load(str(BACKGROUND_POEM_PATH)).convert()
background_poem = pygame.transform.scale(background_poem, (W, H))

start_bg = pygame.image.load(str(START_PATH)).convert()
start_bg = pygame.transform.scale(start_bg, (W, H))

# ---------------------------------------------------
# SOM DO ALARME
# ---------------------------------------------------
def load_first_sound(paths):
    for p in paths:
        if p.exists():
            try:
                return pygame.mixer.Sound(str(p))
            except Exception:
                pass
    return None


ALARM_SOUND = load_first_sound([
    ASSET_DIR_SONS / "alarme.mp3",
    ASSET_DIR_SONS / "alarme.wav",
])

alarm_channel = None
alarm_on = False

if ALARM_SOUND:
    try:
        ALARM_SOUND.set_volume(0.35)
    except Exception:
        pass


def start_alarm():
    global alarm_channel, alarm_on
    alarm_on = True
    if ALARM_SOUND and pygame.mixer.get_init():
        try:
            if alarm_channel:
                alarm_channel.stop()
            alarm_channel = ALARM_SOUND.play(-1)
        except Exception:
            alarm_channel = None


def stop_alarm():
    global alarm_channel, alarm_on
    alarm_on = False
    try:
        if alarm_channel:
            alarm_channel.stop()
    except Exception:
        pass
    alarm_channel = None


# ---------------------------------------------------
# SOM DE FUNDO
# ---------------------------------------------------
BACKGROUND_SOUND = load_first_sound([ASSET_DIR_SONS / "tempestade.mp3"])
background_channel = None

if BACKGROUND_SOUND:
    try:
        BACKGROUND_SOUND.set_volume(0.18)
        background_channel = BACKGROUND_SOUND.play(-1)
    except Exception:
        background_channel = None