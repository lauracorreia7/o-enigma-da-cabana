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
YELLOW = (240, 210, 90)
GRAY = (130, 130, 130)
PAPER = (245, 239, 225)

# ---------------------------------------------------
# FONTES
# ---------------------------------------------------

font_small = pygame.font.SysFont("arial", 18)
font = pygame.font.SysFont("arial", 24)
font_mid = pygame.font.SysFont("arial", 28)
font_big = pygame.font.SysFont("arial", 42, bold=True)
font_huge = pygame.font.SysFont("arial", 58, bold=True)

# ---------------------------------------------------
# IMAGENS
# ---------------------------------------------------
ASSET_DIR = Path("cenarios")
BACKGROUND_PATH = ASSET_DIR / "quarto.png"
BACKGROUND_POEM_PATH = ASSET_DIR / "quarto_papel.png"
START_PATH = ASSET_DIR / "inicio.png"
BACKGROUND_PATH_COZINHA = ASSET_DIR / "cozinha.png"

ASSET_DIR_SONS = Path("sons")

background = pygame.image.load(str(BACKGROUND_PATH)).convert()
background = pygame.transform.scale(background, (W, H))

background_poem = pygame.image.load(str(BACKGROUND_POEM_PATH)).convert()
background_poem = pygame.transform.scale(background_poem, (W, H))

start_bg = pygame.image.load(str(START_PATH)).convert()
start_bg = pygame.transform.scale(start_bg, (W, H))

background_cozinha = pygame.image.load(str(BACKGROUND_PATH_COZINHA)).convert()
background_cozinha = pygame.transform.scale(background_cozinha, (W, H))

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
        for part in stem.replace("-", "").split(" "):
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


STATE_INTRO_1 = "intro_1"
STATE_INTRO_2 = "intro_2"
STATE_SCENE = "scene"
STATE_MEMORY = "memory"
STATE_WIN = "win"

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
exit_button = pygame.Rect(385, 540, 230, 60)

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
    "painting": {"rect": pygame.Rect(130, 150, 80, 130)},}
hotspots = {
    "stove": pygame.Rect(20, 370, 250, 250),
    "faucet": pygame.Rect(650, 270, 50, 80),
    "book": pygame.Rect(260, 250, 150, 100),
    "spoon": pygame.Rect(400, 230, 60, 100),
    "cabinet": pygame.Rect(800, 400, 100, 200),
    "plates": pygame.Rect(570, 60, 150, 70),
    "rug": pygame.Rect(290, 520, 420, 140),
    "spices": pygame.Rect(790, 240, 100, 110),
    "light": pygame.Rect(500, 5, 50, 70),}
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

BED_TIME_LIMIT = 25.0
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

def draw_intro_panel(title, subtitle):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 145))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(200, 150, 600, 360)
    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=12)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=12)

    draw_text_center(title, font_big, GOLD, box.centerx, box.y + 90)
    draw_text_center(subtitle, font_huge, WHITE, box.centerx, box.y + 165)
    draw_text_center("clique para continuar", font, WHITE, box.centerx, box.bottom - 42)

def draw_popup(title, text):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 145))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(200, 150, 600, 360)

    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=12)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=12)

    draw_text_center(title, font_big, GOLD, box.centerx, box.y + 60)

    lines = text.split("\n")
    yy = box.y + 135

    for line in lines:
        img = font_mid.render(line, True, WHITE)
        screen.blit(img, (box.centerx - img.get_width() // 2, yy))
        yy += 40

    hint = font_small.render("Clique para fechar", True, (180, 180, 180))
    screen.blit(hint, (box.centerx - hint.get_width() // 2, box.bottom - 45))

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
# PUZZLE SCREEN
# ---------------------------------------------------
def draw_puzzle():
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(W // 2 - 350, H // 2 - 220, 700, 440)

    pygame.draw.rect(screen, (30, 30, 30), box, border_radius=15)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=15)

    draw_text_center("Arrume a cama!", font_big, GOLD, box.centerx, box.y + 50)

    remaining = max(0.0, bed_timer_remaining)
    timer_color = RED if remaining <= 5 else GOLD
    draw_text_center(f"Tempo: {int(remaining)}s", font_small, timer_color, box.right - 70, box.y + 28)

    q = questions[current_question][0]
    draw_text_center(q, font_big, WHITE, box.centerx, box.y + 170)

    input_box = pygame.Rect(box.centerx - 150, box.y + 240, 300, 70)

    pygame.draw.rect(screen, (50, 50, 50), input_box, border_radius=8)
    pygame.draw.rect(screen, GOLD, input_box, 2, border_radius=8)

    display = user_input if user_input else "_"
    draw_text_center(display, font_big, WHITE, input_box.centerx, input_box.centery)

# ---------------------------------------------------
# SAFE SCREEN
# ---------------------------------------------------
def draw_safe():
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(W // 2 - 300, H // 2 - 200, 600, 400)

    pygame.draw.rect(screen, (30, 30, 30), box, border_radius=15)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=15)

    draw_text_center("COFRE", font_big, GOLD, box.centerx, box.y + 50)

    input_box = pygame.Rect(box.centerx - 150, box.y + 170, 300, 80)

    pygame.draw.rect(screen, (50, 50, 50), input_box, border_radius=10)
    pygame.draw.rect(screen, GOLD, input_box, 2, border_radius=10)

    hidden = "•" * len(safe_input)
    display = hidden if hidden else "_"
    draw_text_center(display, font_big, WHITE, input_box.centerx, input_box.centery)

    draw_text_center("Digite a senha e pressione ENTER", font, WHITE, box.centerx, box.y + 320)

    hint = font_small.render("ESC para voltar ao quarto", True, (170, 160, 145))
    screen.blit(hint, (box.centerx - hint.get_width() // 2, box.bottom - 32))

# ---------------------------------------------------
# TELA DO QUEBRA-CABECA
# ---------------------------------------------------
def draw_painting_puzzle():
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(GRID_X - 25, 110, GRID_W + 50, GRID_H + 150)
    pygame.draw.rect(screen, (18, 16, 20), panel, border_radius=18)
    pygame.draw.rect(screen, GOLD, panel, 3, border_radius=18)

    draw_text_center("Organize o quadro", font_big, GOLD, panel.centerx, panel.y + 34)
    draw_text_center("Clique em duas partes para trocar", font_small, WHITE, panel.centerx, panel.y + 68)

    for idx, rect in enumerate(painting_positions):
        piece_idx = current_order[idx]
        screen.blit(painting_piece_surfs[piece_idx], rect.topleft)

        border = GOLD if painting_selected == idx else (120, 105, 80)
        pygame.draw.rect(screen, border, rect, 3)

        if painting_selected == idx:
            pygame.draw.rect(screen, (255, 245, 180), rect.inflate(8, 8), 2)

# ---------------------------------------------------
# TELA DE VITÓRIA
# ---------------------------------------------------
def draw_victory():
    screen.blit(background, (0, 0))

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(180, 80, 640, 500)

    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=20)
    pygame.draw.rect(screen, GOLD, box, 4, border_radius=20)

    draw_text_center("Você achou a chave!", font_big, GOLD, box.centerx, box.y + 60)

    cx = box.centerx
    cy = box.centery - 20

    pygame.draw.circle(screen, GOLD, (cx - 120, cy), 38, 8)
    pygame.draw.rect(screen, GOLD, (cx - 80, cy - 10, 220, 20))
    pygame.draw.rect(screen, GOLD, (cx + 90, cy + 10, 20, 40))
    pygame.draw.rect(screen, GOLD, (cx + 130, cy + 10, 20, 25))
    pygame.draw.line(screen, (255, 245, 180), (cx - 75, cy), (cx + 120, cy), 3)

    pygame.draw.rect(screen, (35, 30, 24), next_button, border_radius=12)
    pygame.draw.rect(screen, GOLD, next_button, 3, border_radius=12)
    draw_text_center("PROXIMA FASE", font, GOLD, next_button.centerx, next_button.centery)

def draw_win():
    screen.blit(background_cozinha, (0, 0))
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(180, 90, 640, 500)
    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=20)
    pygame.draw.rect(screen, GOLD, box, 4, border_radius=20)

    draw_text_center("Parabéns, você escapou!", font_big, GOLD, box.centerx, box.y + 60)

    cx = box.centerx
    cy = box.centery 

    pygame.draw.circle(screen, GOLD, (cx - 120, cy), 38, 8)
    pygame.draw.rect(screen, GOLD, (cx - 80, cy - 10, 220, 20))
    pygame.draw.rect(screen, GOLD, (cx + 90, cy + 10, 20, 40))
    pygame.draw.rect(screen, GOLD, (cx + 130, cy + 10, 20, 25))
    pygame.draw.line(screen, (255, 245, 180), (cx - 75, cy), (cx + 120, cy), 3)

    pygame.draw.rect(screen, (35, 30, 24), exit_button, border_radius=12)
    pygame.draw.rect(screen, GOLD, exit_button, 3, border_radius=12)
    draw_text_center("SAIR", font, GOLD, exit_button.centerx, exit_button.centery)

# ---------------------------------------------------
# TELA DE DERROTA
# ---------------------------------------------------
def draw_lose():
    screen.blit(background, (0, 0))

    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(180, 110, 640, 420)

    pygame.draw.rect(screen, (20, 20, 20), box, border_radius=20)
    pygame.draw.rect(screen, RED, box, 4, border_radius=20)

    draw_text_center("VOCÊ PERDEU", font_big, RED, box.centerx, box.y + 60)
    draw_text_center("O tempo acabou.", font, WHITE, box.centerx, box.y + 150)
    draw_text_center("A cabana engoliu sua chance.", font, WHITE, box.centerx, box.y + 195)

    pygame.draw.rect(screen, (35, 30, 24), lose_button, border_radius=12)
    pygame.draw.rect(screen, RED, lose_button, 3, border_radius=12)
    draw_text_center("TENTAR NOVAMENTE", font, RED, lose_button.centerx, lose_button.centery)

# ---------------------------------------------------
# PROXIMA FASE
# ---------------------------------------------------

def draw_next():
    game_state = STATE_INTRO_1

# ---------------------------------------------------
# GAME
# ---------------------------------------------------

def draw_game1():
    screen.blit(background, (0, 0))

def draw_game2():
    screen.blit(background_cozinha, (0,0))

# ---------------------------------------------------
# START SCREEN
# ---------------------------------------------------
def draw_start():
    screen.blit(start_bg, (0, 0))

def draw_intro():
    screen.blit(background_cozinha, (0, 0))
    draw_intro_panel("Fase 2", "A cozinha")

def draw_intro_burning():
    screen.blit(background_cozinha, (0, 0))
    draw_popup("A cozinha", "Você está sentindo esse cheiro?\nAcho que algo está queimando...")

# ---------------------------------------------------
# POEM SCREEN
# ---------------------------------------------------
def draw_poem():
    screen.blit(background_poem, (0, 0))

    y = 220
    for line in poem_lines:
        text = font.render(line, True, (40, 30, 22))
        screen.blit(text, (305, y))
        y += 55

    hint = font_small.render("Clique ou pressione ENTER para continuar", True, (60, 60, 50))
    screen.blit(hint, (350, 520))

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def start_bed_puzzle():
    global puzzle_active, current_question, user_input, bed_timer_remaining
    puzzle_active = True
    current_question = 0
    user_input = ""
    bed_timer_remaining = BED_TIME_LIMIT

# ---------------------------------------------------
# MEMÓRIA
# ---------------------------------------------------

creatures = ["Vampiro", "Fantasma", "Múmia", "Lobisomem"]
deck = creatures * 2
random.shuffle(deck)

memory_cards = []
start_x = 72
start_y = 180
card_w = 200
card_h = 200
gap_x = 20
gap_y = 20

idx = 0
for row in range(2):
    for col in range(4):
        rect = pygame.Rect(
            start_x + col * (card_w + gap_x),
            start_y + row * (card_h + gap_y),
            card_w,
            card_h,
        )
        memory_cards.append({
            "rect": rect,
            "name": deck[idx],
            "revealed": False,
            "matched": False,
        })
        idx += 1

memory_first = None
memory_second = None
memory_flip_timer = 0
memory_mismatch = False

def complete_memory():
    global memory_complete, step, state, popup_text
    memory_complete = True
    step = 1
    state = STATE_SCENE
    popup_text = "Ufa, você apagou o fogo \n e nem teve que usar água."

def handle_memory_click(pos):
    global memory_first, memory_second, memory_flip_timer, memory_mismatch

    if memory_flip_timer > 0:
        return

    for card in memory_cards:
        if card["rect"].collidepoint(pos) and not card["matched"] and not card["revealed"]:
            card["revealed"] = True

            if memory_first is None:
                memory_first = card

            elif memory_second is None and card is not memory_first:
                memory_second = card

                if memory_first["name"] == memory_second["name"]:
                    memory_first["matched"] = True
                    memory_second["matched"] = True
                    memory_first = None
                    memory_second = None

                    if all(c["matched"] for c in memory_cards):
                        complete_memory()
                else:
                    memory_flip_timer = 45
                    memory_mismatch = True
            break

def draw_memory():
    screen.fill((40, 40, 40))

    panel = pygame.Rect(40, 55, 920, 580)
    pygame.draw.rect(screen, (238, 235, 228), panel, border_radius=20)
    pygame.draw.rect(screen, (70, 70, 70), panel, 3, border_radius=20)

    draw_text("Jogo da Memória", font_huge, BLACK, panel.x + 40, panel.y + 18)
    draw_text("Ache os pares para apagar o fogo.", font, BLACK, panel.x + 45, panel.y + 78)

    for card in memory_cards:
        if card["matched"]:
            color = GREEN
            label = card["name"]
        elif card["revealed"]:
            color = YELLOW
            label = card["name"]
        else:
            color = GRAY
            label = "?"

        pygame.draw.rect(screen, color, card["rect"], border_radius=12)
        pygame.draw.rect(screen, BLACK, card["rect"], 2, border_radius=12)
        txt = font.render(label, True, BLACK)
        screen.blit(txt, txt.get_rect(center=card["rect"].center))

# ---------------------------------------------------
# PROGRESSO / FASE 2
# ---------------------------------------------------

step = 0
book_open = False
memory_complete = False
win_ready = False
phase2_started = False
popup_text = None

# ---------------------------------------------------
# LIVRO DE RECEITAS
# ---------------------------------------------------
def draw_scene():
    screen.blit(background_cozinha, (0, 0))

    if book_open:
        page = pygame.Rect(330, 150, 350, 360)
        pygame.draw.rect(screen, PAPER, page, border_radius=14)
        pygame.draw.rect(screen, (140, 120, 90), page, 3, border_radius=14)

        draw_text_center("Receita", font_big, BLACK, page.centerx, page.y + 34)

        lines = [
            "- 2 xícaras de farinha",
            "- 1 xícara de açúcar",
            "- 3 ovos",
            "- 1 colher de fermento",
            "- Misture até ficar homogêneo",
        ]
        y2 = page.y + 86
        for line in lines:
            draw_text(line, font, BLACK, page.x + 24, y2)
            y2 += 40

        warning = font_mid.render("USE A COLHER DE PAU!", True, RED)
        screen.blit(warning, warning.get_rect(center=(page.centerx, page.bottom - 42)))

    if popup_text is not None:
        draw_popup("Cozinha", popup_text)

#----------------------------------
# FASE 2
#----------------------------------
def handle_scene_click(pos):
    global state, step, book_open, win_ready, popup_text

    if step == 0 and hotspots["stove"].collidepoint(pos):
        state = STATE_MEMORY
        return

    if book_open:
        book_open = False
        return

    if step == 1 and hotspots["faucet"].collidepoint(pos):
        popup_text = "A receita que fiz sujou muita louça."
        step = 2
        return

    if step == 2 and hotspots["book"].collidepoint(pos):
        book_open = True
        step = 3
        return

    if step == 3 and hotspots["spoon"].collidepoint(pos):
        popup_text = "Usei a mesma madeira na \n colher e no armário."
        step = 4
        return

    if step == 4 and hotspots["cabinet"].collidepoint(pos):
        popup_text = "Costumava deixar os pratos guardados \n aqui, até que..."
        step = 5
        return

    if step == 5 and hotspots["plates"].collidepoint(pos):
        popup_text = "O tapete ajudou os pratos \n a não quebrarem tanto."
        step = 6
        return

    if step == 6 and hotspots["rug"].collidepoint(pos):
        popup_text = "Quanta sujeira, acho que deixei \n algum tempero cair enquanto cozinhava."
        step = 7
        return

    if step == 7 and hotspots["spices"].collidepoint(pos):
        popup_text = "Se essa luz não estivesse tão ruim, \n eu não teria confundido os temperos."
        step = 8
        return

    if step == 8 and hotspots["light"].collidepoint(pos):
        win_ready = True
        state = STATE_WIN
        return


# ---------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------
running = True

while running:
    dt = clock.tick(FPS) / 1000.0

    # ---------------------------------------------------
    # UPDATE FASE 1
    # ---------------------------------------------------

    if puzzle_active:
        bed_timer_remaining -= dt

        if bed_timer_remaining <= 0:
            bed_timer_remaining = 0
            puzzle_active = False
            user_input = ""
            stop_alarm()
            game_state = STATE_LOSE
            popup = None

    # ---------------------------------------------------
    # UPDATE FASE 2
    # ---------------------------------------------------

    if phase2_started:

        if state == STATE_MEMORY and memory_flip_timer > 0:
            memory_flip_timer -= 1

            if memory_flip_timer == 0 and memory_mismatch:

                for card in memory_cards:
                    if not card["matched"]:
                        card["revealed"] = False

                memory_first = None
                memory_second = None
                memory_mismatch = False

    # ---------------------------------------------------
    # EVENTOS
    # ---------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        # ---------------------------------------------------
        # FASE 2
        # ---------------------------------------------------

        if phase2_started:

            if state == STATE_INTRO_1:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    state = STATE_INTRO_2

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = STATE_INTRO_2

                continue

            if state == STATE_INTRO_2:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    state = STATE_SCENE

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        state = STATE_SCENE

                continue

            if state == STATE_MEMORY:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    handle_memory_click(event.pos)

                continue

            if state == STATE_SCENE:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    if popup_text is not None:
                        popup_text = None
                        continue

                    if book_open:
                        book_open = False
                        continue

                    handle_scene_click(event.pos)

                continue

            if state == STATE_WIN:

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    if exit_button.collidepoint(event.pos):
                        running = False

                continue


        # ---------------------------------------------------
        # FASE 1
        # ---------------------------------------------------

        if game_state == STATE_START:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if start_button.collidepoint(event.pos):
                    game_state = STATE_POEM

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_state = STATE_POEM

            continue

        if game_state == STATE_POEM:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game_state = STATE_GAME
                continue

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_state = STATE_GAME

            continue

        if game_state == STATE_PAINTING:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                clicked = None

                for i, rect in enumerate(painting_positions):

                    if rect.collidepoint(event.pos):
                        clicked = i
                        break

                if clicked is not None:

                    if painting_selected is None:
                        painting_selected = clicked

                    else:

                        current_order[painting_selected], current_order[clicked] = (
                            current_order[clicked],
                            current_order[painting_selected],
                        )

                        painting_selected = None

                        if current_order == correct_order:

                            painting_done = True
                            painting_selected = None
                            game_state = STATE_GAME

                            start_alarm()

                            popup = (
                                "Quadro",
                                "A pintura foi restaurada.\nO alarme começou a tocar!"
                            )

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                painting_selected = None
                game_state = STATE_GAME

            continue

        if game_state == STATE_VICTORY:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if next_button.collidepoint(event.pos):
                    game_state = STATE_NEXT

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game_state = STATE_NEXT

            continue

        # ---------------------------------------------------
        # COMEÇA FASE 2
        # ---------------------------------------------------

        if game_state == STATE_NEXT:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                phase2_started = True
                state = STATE_INTRO_1

            continue

        if game_state == STATE_LOSE:

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                if lose_button.collidepoint(event.pos):
                    reset_game()

            if event.type == pygame.KEYDOWN:

                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    reset_game()

            continue

        # ---------------------------------------------------
        # CLIQUES FASE 1
        # ---------------------------------------------------

        if event.type == pygame.MOUSEBUTTONDOWN:

            mx, my = event.pos

            if popup:
                popup = None
                continue

            if safe_active:

                if event.button == 1:
                    safe_active = False

                continue

            if not puzzle_active and not safe_active:

                if items["glasses"]["rect"].collidepoint(mx, my):

                    glasses_done = True

                    popup = (
                        "Óculos",
                        "Agora eu consigo enxergar o que escrevo."
                    )

                elif items["diary"]["rect"].collidepoint(mx, my):

                    if not glasses_done:

                        popup = (
                            "Diário",
                            "Você não consegue ler sem os óculos."
                        )

                    else:

                        diary_done = True

                        popup = (
                            "Diário",
                            "Sexta-feira, 13 de setembro de 3029\n"
                            "A poeira no ar estava terrível.\n"
                            "Tive que deixar a janela fechada."
                        )

                elif items["window"]["rect"].collidepoint(mx, my):

                    if not diary_done:

                        popup = (
                            "Janela",
                            "Adoro escrever e desenhar"
                        )

                    else:

                        window_done = True

                        popup = (
                            "Janela",
                            "Ainda me lembro de quando pintei\n"
                            "um quadro olhando para essa vista."
                        )

                elif items["painting"]["rect"].collidepoint(mx, my):

                    if not window_done:

                        popup = (
                            "Quadro",
                            "Que vista linda!"
                        )

                    else:

                        if painting_done:

                            popup = (
                                "Quadro",
                                "A pintura já foi restaurada."
                            )

                        else:

                            game_state = STATE_PAINTING
                            painting_selected = None

                elif items["clock"]["rect"].collidepoint(mx, my):

                    if alarm_on:

                        stop_alarm()
                        clock_done = True

                        popup = (
                            "Relógio",
                            "Você não acha que está na hora de dormir?"
                        )

                    else:

                        if not painting_done:

                            popup = (
                                "Relógio",
                                "Uma pintura demora muito para ser feita"
                            )

                        else:

                            clock_done = True

                            popup = (
                                "Relógio",
                                "Você não acha que está na hora de dormir?"
                            )

                elif items["bed"]["rect"].collidepoint(mx, my):

                    if not clock_done:

                        popup = (
                            "Cama",
                            "Que horas são?"
                        )

                    else:

                        if not bed_done:

                            start_bed_puzzle()

                        else:

                            popup = (
                                "Senha da cama",
                                f"A senha do cofre é:\n{code}"
                            )

                elif items["safe"]["rect"].collidepoint(mx, my):

                    if not bed_done:

                        popup = (
                            "Cofre",
                            "Você precisa da senha."
                        )

                    else:

                        safe_active = True

        # ---------------------------------------------------
        # TECLADO FASE 1
        # ---------------------------------------------------

        if event.type == pygame.KEYDOWN:

            if safe_active and event.key == pygame.K_ESCAPE:
                safe_active = False
                continue

            if puzzle_active:

                if event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]

                elif event.key == pygame.K_RETURN:

                    if user_input == questions[current_question][1]:

                        current_question += 1
                        user_input = ""

                        if current_question >= len(questions):

                            puzzle_active = False
                            bed_done = True

                            popup = (
                                "Senha Encontrada",
                                f"A senha do cofre é:\n{code}"
                            )

                    else:
                        user_input = ""

                elif event.unicode.isdigit():
                    user_input += event.unicode

            elif safe_active:

                if event.key == pygame.K_BACKSPACE:
                    safe_input = safe_input[:-1]

                elif event.key == pygame.K_RETURN:

                    if safe_input == code:

                        safe_done = True
                        safe_active = False
                        game_state = STATE_VICTORY

                    else:

                        safe_input = ""

                        popup = (
                            "Erro",
                            "Senha incorreta."
                        )

                elif event.unicode.isdigit():
                    safe_input += event.unicode

    # ---------------------------------------------------
    # DRAW FASE 2
    # ---------------------------------------------------

    if phase2_started:

        if state == STATE_INTRO_1:
            draw_intro()

        elif state == STATE_INTRO_2:
            draw_intro_burning()

        elif state == STATE_SCENE:
            draw_scene()

        elif state == STATE_MEMORY:
            draw_memory()

        elif state == STATE_WIN:
            draw_win()

    # ---------------------------------------------------
    # DRAW FASE 1
    # ---------------------------------------------------

    else:

        if game_state == STATE_START:
            draw_start()

        elif game_state == STATE_POEM:
            draw_poem()

        elif game_state == STATE_PAINTING:
            draw_painting_puzzle()

        elif game_state == STATE_GAME:

            draw_game1()

            if popup:
                draw_popup(popup[0], popup[1])

            if puzzle_active:
                draw_puzzle()

            if safe_active:
                draw_safe()

        elif game_state == STATE_VICTORY:
            draw_victory()

        elif game_state == STATE_LOSE:
            draw_lose()

        elif game_state == STATE_NEXT:
            draw_next()

    pygame.display.flip()

stop_alarm()
pygame.quit()
sys.exit()