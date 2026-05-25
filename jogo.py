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

# ---------------------------------------------------
# QUEBRA-CABECA DO QUADRO
# ---------------------------------------------------
PUZZLE_ZIP = ASSET_DIR / "imagens_quebra_cabeca.zip"

PIECE_W = 180
PIECE_H = 180
PIECE_GAP = 10
GRID_COLS = 3
GRID_ROWS = 2

GRID_W = GRID_COLS * PIECE_W + (GRID_COLS - 1) * PIECE_GAP
GRID_H = GRID_ROWS * PIECE_H + (GRID_ROWS - 1) * PIECE_GAP
GRID_X = (W - GRID_W) // 2
GRID_Y = 220


def _sorted_piece_names(names):
    def key_fn(name):
        stem = Path(name).stem
        nums = []
        for part in stem.replace("-", "").split(""):
            if part.isdigit():
                nums.append(int(part))
        return nums if nums else [9999, stem]
    return sorted(names, key=key_fn)


def _load_puzzle_pieces(zip_path: Path):
    pieces = []
    if not zip_path.exists():
        for _ in range(6):
            surf = pygame.Surface((PIECE_W, PIECE_H), pygame.SRCALPHA)
            surf.fill((120, 120, 120))
            pieces.append(surf)
        return pieces

    with zipfile.ZipFile(zip_path, "r") as zf:
        png_names = [n for n in zf.namelist() if n.lower().endswith(".png")]
        png_names = _sorted_piece_names(png_names)[:6]

        for name in png_names:
            data = zf.read(name)
            img = pygame.image.load(BytesIO(data)).convert_alpha()
            img = pygame.transform.smoothscale(img, (PIECE_W, PIECE_H))
            pieces.append(img)

    while len(pieces) < 6:
        surf = pygame.Surface((PIECE_W, PIECE_H), pygame.SRCALPHA)
        surf.fill((120, 120, 120))
        pieces.append(surf)

    return pieces


painting_piece_surfs = _load_puzzle_pieces(PUZZLE_ZIP)

painting_positions = []
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        painting_positions.append(
            pygame.Rect(
                GRID_X + c * (PIECE_W + PIECE_GAP),
                GRID_Y + r * (PIECE_H + PIECE_GAP),
                PIECE_W,
                PIECE_H,
            )
        )

correct_order = [0, 1, 2, 3, 4, 5]
current_order = correct_order[:]
random.shuffle(current_order)
while current_order == correct_order:
    random.shuffle(current_order)

painting_selected = None

# ---------------------------------------------------
# GAME STATE
# ---------------------------------------------------
STATE_START = "start"
STATE_POEM = "poem"
STATE_GAME = "game"
STATE_PAINTING = "painting"
STATE_VICTORY = "victory"
STATE_LOSE = "lose"
STATE_NEXT = "next"

game_state = STATE_START

glasses_done = False
diary_done = False
window_done = False
bed_done = False
safe_done = False
clock_done = False
painting_done = False

popup = None

# ---------------------------------------------------
# BOTÕES
# ---------------------------------------------------
start_button = pygame.Rect(385, 520, 235, 70)
next_button = pygame.Rect(350, 520, 300, 70)
lose_button = pygame.Rect(350, 520, 300, 70)

# ---------------------------------------------------
# BOTÕES DOS ITENS
# ---------------------------------------------------
items = {
    "glasses": {"rect": pygame.Rect(610, 340, 55, 30)},
    "diary": {"rect": pygame.Rect(700, 320, 60, 40)},
    "window": {"rect": pygame.Rect(400, 100, 220, 220)},
    "bed": {"rect": pygame.Rect(100, 300, 250, 250)},
    "safe": {"rect": pygame.Rect(830, 360, 140, 140)},
    "clock": {"rect": pygame.Rect(375, 350, 60, 55)},
    "painting": {"rect": pygame.Rect(130, 150, 80, 130)},
}

# ---------------------------------------------------
# POEMA
# ---------------------------------------------------
poem_lines = [
    "Acorda com o som da chuva a cair,",
    "Lentes nos olhos pra melhor refletir,",
    "O dia cinza se torna mais claro,",
    "Por trás dos óculos, tudo é raro.",
]

# ---------------------------------------------------
# PUZZLE DA CAMA
# ---------------------------------------------------
x = y = a = b = z = w = 0
questions = []
current_question = 0
user_input = ""
puzzle_active = False

safe_active = False
safe_input = ""

code = ""

BED_TIME_LIMIT = 20.0
bed_timer_remaining = BED_TIME_LIMIT

def generate_bed_puzzle():
    global x, y, a, b, z, w, questions, code

    x = random.randint(1, 9)
    y = random.randint(1, 9)

    a = random.randint(100, 999)
    b = random.randint(1, 99)
    while a % b!= 0:
        b = random.randint(1, 99)

    z = random.randint(0, 999)
    w = random.randint(0, 999)

    questions = [
        (f"{x} x {y} =", f"{x * y}"),
        (f"{a} / {b} =", f"{a // b}"),
        (f"{z} + {w} =", f"{z + w}"),
    ]

    code = f"{x * y}{a // b}{z + w}"


generate_bed_puzzle()

# ---------------------------------------------------
# TEXT
# ---------------------------------------------------
def draw_text(text, font_obj, color, x, y):
    img = font_obj.render(text, True, color)
    screen.blit(img, (x, y))


def draw_text_center(text, font_obj, color, centerx, centery):
    img = font_obj.render(text, True, color)
    screen.blit(img, (centerx - img.get_width() // 2, centery - img.get_height() // 2))

# ---------------------------------------------------
# RESET
# ---------------------------------------------------
def reset_game():
    global game_state, glasses_done, diary_done, window_done, bed_done, safe_done, clock_done, painting_done
    global popup, current_question, user_input, puzzle_active, safe_active, safe_input
    global painting_selected, current_order, bed_timer_remaining

    game_state = STATE_START
    glasses_done = False
    diary_done = False
    window_done = False
    bed_done = False
    safe_done = False
    clock_done = False
    painting_done = False

    popup = None

    current_question = 0
    user_input = ""
    puzzle_active = False

    safe_active = False
    safe_input = ""

    painting_selected = None
    current_order = correct_order[:]
    random.shuffle(current_order)
    while current_order == correct_order:
        random.shuffle(current_order)

    bed_timer_remaining = BED_TIME_LIMIT
    generate_bed_puzzle()
    stop_alarm()

# ---------------------------------------------------
# POPUP
# ---------------------------------------------------
def draw_popup(title, text):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(200, 150, 600, 360)

    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=12)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=12)

    draw_text_center(title, font_big, GOLD, box.centerx, box.y + 60)

    lines = text.split("\n")
    yy = box.y + 135

    for line in lines:
        img = font.render(line, True, WHITE)
        screen.blit(img, (box.centerx - img.get_width() // 2, yy))
        yy += 40

    hint = font_small.render("Clique para fechar", True, (180, 180, 180))
    screen.blit(hint, (box.centerx - hint.get_width() // 2, box.bottom - 45))