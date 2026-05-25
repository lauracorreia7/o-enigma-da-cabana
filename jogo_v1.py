import pygame
import sys
import math
import random
import time
 

pygame.init()
pygame.mixer.init()
 
# ─── Constants ───────────────────────────────────────
W, H = 1200, 750
FPS = 60
FONT_PATH = None  # will use pygame default
 
# Palette
C_BG        = (18, 16, 22)
C_DARK      = (28, 24, 34)
C_WOOD      = (72, 52, 38)
C_WOOD_LT   = (101, 74, 54)
C_WALL      = (52, 48, 58)
C_WALL_LT   = (68, 62, 74)
C_RAIN      = (140, 170, 210)
C_RAIN2     = (100, 130, 180)
C_FLOOR     = (58, 45, 32)
C_FLOOR_LT  = (78, 60, 42)
C_WINDOW    = (80, 120, 160)
C_FOREST    = (30, 60, 35)
C_FOREST2   = (20, 45, 25)
C_TEXT      = (220, 210, 195)
C_TEXT_DIM  = (140, 128, 110)
C_GOLD      = (200, 160, 60)
C_RED       = (180, 60, 60)
C_GREEN     = (60, 160, 80)
C_HIGHLIGHT = (220, 200, 100)
C_OVERLAY   = (0, 0, 0, 190)
C_PAPER     = (210, 195, 165)
C_PAPER_DK  = (170, 152, 118)
C_INK       = (40, 35, 28)
C_INK2      = (80, 65, 45)
C_GLASS     = (140, 185, 220, 60)
C_SAFE      = (80, 80, 85)
C_SAFE_LT   = (110, 110, 118)
C_DIAL      = (50, 50, 55)
 
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("O Enigma da Cabana")
clock = pygame.time.Clock()
 
# ─── Fonts ───────────────────────────────────────────
def load_font(size, bold=False):
    try:
        return pygame.font.SysFont("Georgia", size, bold=bold)
    except:
        return pygame.font.Font(None, size)
 
def load_mono(size):
    try:
        return pygame.font.SysFont("Courier New", size)
    except:
        return pygame.font.Font(None, size)
 
f_tiny   = load_font(14)
f_small  = load_font(18)
f_med    = load_font(22)
f_body   = load_font(26)
f_title  = load_font(36, bold=True)
f_big    = load_font(52, bold=True)
f_poem   = load_font(20)
f_mono   = load_mono(22)
f_mono_s = load_mono(17)
f_hand   = load_font(19)  # "handwriting" sim
 
# ─── Helpers ─────────────────────────────────────────
def draw_text_wrapped(surf, text, font, color, rect, line_spacing=6, center=False):
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = ' '.join(current + [w])
        if font.size(test)[0] <= rect.width:
            current.append(w)
        else:
            if current:
                lines.append(' '.join(current))
            current = [w]
    if current:
        lines.append(' '.join(current))
    y = rect.top
    for line in lines:
        surf_t = font.render(line, True, color)
        x = rect.centerx - surf_t.get_width()//2 if center else rect.left
        surf.blit(surf_t, (x, y))
        y += font.get_height() + line_spacing
    return y
 
def draw_rect_alpha(surf, color, rect, radius=0):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    if radius:
        pygame.draw.rect(s, color, s.get_rect(), border_radius=radius)
    else:
        s.fill(color)
    surf.blit(s, rect.topleft)
 
def glow_text(surf, text, font, color, pos, glow_color=None, glow_r=3):
    if glow_color:
        for dx in range(-glow_r, glow_r+1, 1):
            for dy in range(-glow_r, glow_r+1, 1):
                if dx*dx + dy*dy <= glow_r*glow_r:
                    g = font.render(text, True, glow_color)
                    surf.blit(g, (pos[0]+dx, pos[1]+dy))
    t = font.render(text, True, color)
    surf.blit(t, pos)
 
def pulse(t, speed=2, lo=180, hi=255):
    v = int(lo + (hi-lo) * (0.5 + 0.5*math.sin(t*speed)))
    return max(lo, min(hi, v))
 
# ─── Rain System ─────────────────────────────────────
class Raindrop:
    def __init__(self, window_rect):
        self.reset(window_rect)
    def reset(self, wr):
        self.x = random.randint(wr.left+5, wr.right-5)
        self.y = random.randint(wr.top+5, wr.top + wr.height//3)
        self.speed = random.uniform(3, 7)
        self.length = random.randint(8, 20)
        self.alpha = random.randint(80, 180)
        self.wr = wr
    def update(self):
        self.y += self.speed
        if self.y > self.wr.bottom - 5:
            self.reset(self.wr)
    def draw(self, surf):
        a = self.alpha
        end_y = min(self.y + self.length, self.wr.bottom - 5)
        s = pygame.Surface((2, int(end_y - self.y + 1)), pygame.SRCALPHA)
        s.fill((*C_RAIN2, a))
        surf.blit(s, (int(self.x), int(self.y)))
 
# ─── Particles ───────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-3, -1)
        self.life = random.randint(40, 80)
        self.max_life = self.life
        self.size = random.randint(2, 5)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= 1
    def draw(self, surf):
        alpha = int(255 * self.life / self.max_life)
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surf.blit(s, (int(self.x - self.size), int(self.y - self.size)))
 
# ─── Game State ──────────────────────────────────────
class GameState:
    INTRO       = "intro"
    ROOM        = "room"
    GLASSES     = "glasses"
    DIARY       = "diary"
    WINDOW_ZOOM = "window_zoom"
    BED_PUZZLE  = "bed_puzzle"
    SAFE        = "safe"
    VICTORY     = "victory"
    NEXT_ROOM   = "next_room"
 
class Game:
    def __init__(self):
        self.state = GameState.INTRO
        self.t = 0.0
 
        # Progress flags
        self.glasses_done  = False
        self.diary_done    = False
        self.window_done   = False
        self.bed_done      = False
        self.safe_done     = False
 
        # Intro poem
        self.poem_lines = [
            "Acorda com o som da chuva a cair,",
            "Lentes nos olhos pra melhor refletir,",
            "O dia cinza se torna mais claro,",
            "Por trás dos óculos, tudo é raro.",
        ]
        self.poem_reveal = 0.0   # 0..len lines
        self.intro_alpha = 0
        self.intro_done  = False
        self.intro_timer = 0
 
        # Rain
        window_rect = pygame.Rect(820, 100, 300, 260)
        self.raindrops = [Raindrop(window_rect) for _ in range(60)]
        self.window_rect = window_rect
 
        # Particles
        self.particles = []
 
        # Clickable objects (defined after drawing coords are set)
        self.objs = self._build_objects()
 
        # Hover
        self.hovered = None
        self.hover_alpha = {}
 
        # Popup
        self.popup_text  = ""
        self.popup_lines = []
        self.popup_active = False
        self.popup_alpha  = 0
        self.popup_type   = "message"  # message | diary | window | victory
 
        # Bed puzzle
        self.puzzle_questions = [
            ("7 × 8 = ?",    56),
            ("144 ÷ 12 = ?", 12),
            ("29 + 37 = ?",  66),
        ]
        self.puzzle_idx     = 0
        self.puzzle_input   = ""
        self.puzzle_start   = 0
        self.puzzle_time    = 40
        self.puzzle_wrong   = False
        self.puzzle_answers = []
        self.puzzle_code    = ""
 
        # Safe
        self.safe_input  = ""
        self.safe_wrong  = False
        self.safe_flash  = 0
 
        # Victory
        self.victory_alpha = 0
        self.key_y = H + 100
 
        # Notification
        self.notif_text  = ""
        self.notif_timer = 0
 
    def _build_objects(self):
        return {
            "glasses": {
                "rect": pygame.Rect(148, 530, 90, 38),
                "label": "Óculos",
                "hint": "Clique nos óculos",
                "done_color": C_GREEN,
            },
            "diary": {
                "rect": pygame.Rect(300, 490, 65, 90),
                "label": "Diário",
                "hint": "Clique no diário",
                "done_color": C_GREEN,
            },
            "window": {
                "rect": pygame.Rect(820, 100, 300, 260),
                "label": "Janela",
                "hint": "Clique na janela",
                "done_color": C_GREEN,
            },
            "bed": {
                "rect": pygame.Rect(60, 360, 380, 230),
                "label": "Cama",
                "hint": "Clique na cama",
                "done_color": C_GREEN,
            },
            "safe": {
                "rect": pygame.Rect(975, 480, 140, 120),
                "label": "Cofre",
                "hint": "Clique no cofre",
                "done_color": C_GREEN,
            },
        }
 
    # ─── Update ──────────────────────────────────────
    def update(self, dt):
        self.t += dt
 
        if self.state == GameState.INTRO:
            self.intro_timer += dt
            # Fade in
            self.intro_alpha = min(255, int(self.intro_alpha + dt*120))
            # Reveal poem lines one by one
            self.poem_reveal = min(len(self.poem_lines), self.poem_reveal + dt * 0.6)
            if self.intro_timer > 9 and not self.intro_done:
                self.intro_done = True
 
        # Rain
        if self.state == GameState.ROOM or self.state == GameState.INTRO:
            for r in self.raindrops:
                r.update()
 
        # Particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update()
 
        # Popup fade
        if self.popup_active:
            self.popup_alpha = min(255, self.popup_alpha + 12)
        else:
            self.popup_alpha = max(0, self.popup_alpha - 15)
 
        # Hover alpha
        for key in self.objs:
            if key not in self.hover_alpha:
                self.hover_alpha[key] = 0
            target = 180 if self.hovered == key else 0
            self.hover_alpha[key] += (target - self.hover_alpha[key]) * 0.2
 
        # Bed puzzle timer
        if self.state == GameState.BED_PUZZLE:
            elapsed = time.time() - self.puzzle_start
            if elapsed >= self.puzzle_time:
                self._puzzle_timeout()
 
        # Notif
        if self.notif_timer > 0:
            self.notif_timer -= dt
 
        # Victory animation
        if self.state == GameState.VICTORY:
            self.victory_alpha = min(255, self.victory_alpha + 3)
            self.key_y = max(H//2 - 40, self.key_y - 3)
 
        if self.state == GameState.NEXT_ROOM:
            pass
 
    # ─── Events ──────────────────────────────────────
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = None
            if self.state == GameState.ROOM and not self.popup_active:
                for key, obj in self.objs.items():
                    if obj["rect"].collidepoint(mx, my):
                        self.hovered = key
                        break
 
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
 
            if self.state == GameState.INTRO:
                if self.intro_done or self.intro_timer > 6:
                    self.state = GameState.ROOM
                return
 
            if self.state == GameState.ROOM and not self.popup_active:
                self._room_click(mx, my)
                return
 
            if self.popup_active:
                self._popup_click(mx, my)
                return
 
            if self.state == GameState.BED_PUZZLE:
                pass  # handled by keydown
 
            if self.state == GameState.SAFE:
                pass
 
            if self.state == GameState.VICTORY:
                if self.victory_alpha > 200:
                    self.state = GameState.NEXT_ROOM
 
        if event.type == pygame.KEYDOWN:
            if self.state == GameState.BED_PUZZLE:
                self._puzzle_key(event)
            elif self.state == GameState.SAFE:
                self._safe_key(event)
            elif self.state == GameState.ROOM and self.popup_active:
                if event.key == pygame.K_ESCAPE:
                    self.popup_active = False
 
    def _room_click(self, mx, my):
        for key, obj in self.objs.items():
            if obj["rect"].collidepoint(mx, my):
                self._on_object_click(key)
                # Spawn particles
                cx, cy = obj["rect"].center
                for _ in range(15):
                    self.particles.append(Particle(cx, cy, C_GOLD))
                return
 
    def _on_object_click(self, key):
        if key == "glasses":
            self._show_popup(
                "message",
                "O antigo morador dessa cabana\ntinha uma letra horrível.",
                title="🔍 Óculos"
            )
            self.glasses_done = True
 
        elif key == "diary":
            if not self.glasses_done:
                self._show_notif("Talvez você precise de algo para ler melhor…")
                return
            self._show_popup(
                "diary",
                "Sexta-feira, 13, 3029\n\nO índice de poluição do ar hoje estava péssimo, tive que deixar a janela fechada o dia inteiro hoje.",
                title="📓 Diário"
            )
            self.diary_done = True
 
        elif key == "window":
            if not self.diary_done:
                self._show_notif("Será que há algo escrito aí? Você mal consegue enxergar…")
                return
            self._show_popup("window", "", title="🪟 Janela")
            self.window_done = True
 
        elif key == "bed":
            if not self.window_done:
                self._show_notif("A mensagem na janela diz para você olhar para a cama…")
                return
            self._start_bed_puzzle()
 
        elif key == "safe":
            if not self.bed_done:
                self._show_notif("Você precisaria de uma senha para abrir o cofre…")
                return
            self._show_safe()
 
    def _show_popup(self, ptype, text, title=""):
        self.popup_type  = ptype
        self.popup_text  = text
        self.popup_title = title
        self.popup_active = True
        self.popup_alpha  = 0
 
    def _popup_click(self, mx, my):
        # Close button area (top-right of popup)
        popup_rect = self._get_popup_rect()
        close = pygame.Rect(popup_rect.right - 44, popup_rect.top + 10, 34, 34)
        if close.collidepoint(mx, my) or not popup_rect.collidepoint(mx, my):
            self.popup_active = False
 
    def _get_popup_rect(self):
        if self.popup_type == "window":
            return pygame.Rect(W//2 - 360, H//2 - 280, 720, 560)
        elif self.popup_type == "diary":
            return pygame.Rect(W//2 - 280, H//2 - 220, 560, 440)
        else:
            return pygame.Rect(W//2 - 260, H//2 - 140, 520, 280)
 
    def _show_notif(self, text):
        self.notif_text  = text
        self.notif_timer = 3.0
 
    def _start_bed_puzzle(self):
        self.state = GameState.BED_PUZZLE
        self.puzzle_idx     = 0
        self.puzzle_input   = ""
        self.puzzle_start   = time.time()
        self.puzzle_answers = []
        self.puzzle_wrong   = False
        self.popup_active   = False
 
    def _puzzle_key(self, event):
        if event.key == pygame.K_RETURN:
            self._puzzle_submit()
        elif event.key == pygame.K_BACKSPACE:
            self.puzzle_input = self.puzzle_input[:-1]
        elif event.unicode.isdigit() and len(self.puzzle_input) < 6:
            self.puzzle_input += event.unicode
            self.puzzle_wrong = False
 
    def _puzzle_submit(self):
        q, ans = self.puzzle_questions[self.puzzle_idx]
        try:
            val = int(self.puzzle_input)
        except:
            val = -1
        if val == ans:
            self.puzzle_answers.append(str(ans))
            self.puzzle_idx += 1
            self.puzzle_input = ""
            self.puzzle_wrong = False
            if self.puzzle_idx >= len(self.puzzle_questions):
                self._puzzle_complete()
        else:
            self.puzzle_wrong = True
            self.puzzle_input = ""
 
    def _puzzle_complete(self):
        self.puzzle_code = "".join(self.puzzle_answers)  # e.g. "561266"
        self.bed_done    = True
        self._show_notif(f"A cama está arrumada! Você notou: {self.puzzle_code}")
        self.state = GameState.ROOM
 
    def _puzzle_timeout(self):
        self.state = GameState.ROOM
        self._show_notif("Tempo esgotado! Tente arrumar a cama novamente.")
        self.bed_done = False
        self.puzzle_idx = 0
        self.puzzle_answers = []
 
    def _show_safe(self):
        self.state = GameState.SAFE
        self.safe_input = ""
        self.safe_wrong = False
        self.popup_active = False
 
    def _safe_key(self, event):
        if event.key == pygame.K_RETURN:
            self._safe_submit()
        elif event.key == pygame.K_BACKSPACE:
            self.safe_input = self.safe_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.state = GameState.ROOM
        elif event.unicode.isdigit() and len(self.safe_input) < len(self.puzzle_code):
            self.safe_input += event.unicode
            self.safe_wrong = False
 
    def _safe_submit(self):
        if self.safe_input == self.puzzle_code:
            self.safe_done = True
            self.state = GameState.VICTORY
        else:
            self.safe_wrong  = True
            self.safe_flash  = 30
            self.safe_input  = ""
 
    # ─── Draw ─────────────────────────────────────────
    def draw(self):
        screen.fill(C_BG)
 
        if self.state == GameState.INTRO:
            self._draw_intro()
        elif self.state in (GameState.ROOM,):
            self._draw_room()
            self._draw_room_ui()
            if self.popup_active:
                self._draw_popup()
        elif self.state == GameState.BED_PUZZLE:
            self._draw_room()
            self._draw_bed_puzzle()
        elif self.state == GameState.SAFE:
            self._draw_room()
            self._draw_safe()
        elif self.state == GameState.VICTORY:
            self._draw_room()
            self._draw_victory()
        elif self.state == GameState.NEXT_ROOM:
            self._draw_next_room()
 
        pygame.display.flip()
 
    # ── Intro ────────────────────────────────────────
    def _draw_intro(self):
        # Dark bg with subtle texture
        screen.fill((10, 9, 14))
        # Vignette
        for i in range(8):
            a = 30 - i*3
            r = pygame.Rect(i*20, i*15, W-i*40, H-i*30)
            draw_rect_alpha(screen, (0,0,0,max(0,a)), r)
 
        # Rain atmosphere in bg
        for rd in self.raindrops:
            rd.draw(screen)
 
        # Title
        title = f_big.render("O Enigma da Cabana", True, (200, 185, 155))
        tx = W//2 - title.get_width()//2
        glow_text(screen, "O Enigma da Cabana", f_big, (200,185,155),
                  (tx, 60), glow_color=(100,80,40), glow_r=4)
 
        sub = f_small.render("— Uma história de escape —", True, (120, 108, 88))
        screen.blit(sub, (W//2 - sub.get_width()//2, 120))
 
        # Poem box
        box = pygame.Rect(W//2 - 320, 180, 640, 240)
        draw_rect_alpha(screen, (30, 26, 22, 200), box, radius=12)
        pygame.draw.rect(screen, (100, 85, 60), box, 1, border_radius=12)
 
        visible = int(self.poem_reveal)
        partial = self.poem_reveal - visible
 
        y = box.top + 30
        for i, line in enumerate(self.poem_lines):
            if i < visible:
                alpha = 255
            elif i == visible:
                alpha = int(partial * 255)
            else:
                alpha = 0
 
            if alpha > 0:
                surf = f_poem.render(line, True, (220, 205, 175))
                s2 = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                s2.blit(surf, (0,0))
                s2.set_alpha(alpha)
                screen.blit(s2, (W//2 - surf.get_width()//2, y))
            y += 44
 
        # Instruction
        if self.intro_done or self.intro_timer > 7:
            blink = pulse(self.t, 3, 120, 220)
            msg = f_small.render("[ Clique para continuar ]", True, (blink, blink-20, blink-40))
            screen.blit(msg, (W//2 - msg.get_width()//2, H - 80))
 
    # ── Room ─────────────────────────────────────────
    def _draw_room(self):
        # Floor
        pygame.draw.rect(screen, C_FLOOR, (0, 580, W, H-580))
        # Floor planks
        for x in range(0, W, 80):
            pygame.draw.line(screen, C_FLOOR_LT, (x, 580), (x, H), 1)
        pygame.draw.line(screen, (40,30,20), (0, 580), (W, 580), 2)
 
        # Walls
        pygame.draw.rect(screen, C_WALL, (0, 0, W, 580))
        # Wall texture lines
        for y in range(40, 580, 60):
            pygame.draw.line(screen, C_WALL_LT, (0, y), (W, y), 1)
        # Baseboard
        pygame.draw.rect(screen, C_WOOD, (0, 560, W, 20))
        pygame.draw.rect(screen, C_WOOD_LT, (0, 560, W, 3))
 
        # ── Window ──
        self._draw_window()
 
        # ── Bed ──
        self._draw_bed()
 
        # ── Nightstand ──
        self._draw_nightstand()
 
        # ── Glasses ──
        self._draw_glasses()
 
        # ── Diary ──
        self._draw_diary()
 
        # ── Safe ──
        self._draw_safe_obj()
 
        # ── Particles ──
        for p in self.particles:
            p.draw(screen)
 
        # Hover highlights
        for key, obj in self.objs.items():
            alpha = int(self.hover_alpha.get(key, 0))
            if alpha > 5:
                s = pygame.Surface((obj["rect"].width, obj["rect"].height), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 240, 140, alpha), s.get_rect(), border_radius=6)
                pygame.draw.rect(s, (255, 220, 60, min(255, alpha+50)), s.get_rect(), 2, border_radius=6)
                screen.blit(s, obj["rect"].topleft)
                # Label
                if alpha > 80:
                    lbl = f_small.render(obj["label"], True, (255, 240, 160))
                    lx = obj["rect"].centerx - lbl.get_width()//2
                    ly = obj["rect"].top - 28
                    draw_rect_alpha(screen, (20,18,14,180), pygame.Rect(lx-6, ly-3, lbl.get_width()+12, lbl.get_height()+6), radius=4)
                    screen.blit(lbl, (lx, ly))
 
        # Vignette
        self._draw_vignette()
 
    def _draw_window(self):
        wr = self.window_rect
        # Window frame
        pygame.draw.rect(screen, C_WOOD_LT, wr.inflate(16, 16), border_radius=4)
        pygame.draw.rect(screen, C_WOOD, wr.inflate(16, 16), 4, border_radius=4)
 
        # Forest outside (dark, rainy)
        forest = pygame.Surface((wr.width, wr.height), pygame.SRCALPHA)
        forest.fill(C_FOREST2)
        # Tree silhouettes
        for tx in range(10, wr.width, 35):
            th = random.randint(100, 220) if not hasattr(self, '_trees') else self._trees[tx % len(self._trees)]
            ph = 40 + (tx % 20)
            pygame.draw.rect(forest, C_FOREST, (tx-5, wr.height-ph, 10, ph))
            # Triangle top
            points = [(tx, wr.height-ph-th//2), (tx-25, wr.height-ph), (tx+25, wr.height-ph)]
            pygame.draw.polygon(forest, C_FOREST, points)
        # Sky gradient
        for y in range(wr.height//2):
            alpha = int(60 * (1 - y/(wr.height//2)))
            pygame.draw.line(forest, (*C_WINDOW, alpha), (0, y), (wr.width, y))
        screen.blit(forest, wr.topleft)
 
        # Rain inside window
        for rd in self.raindrops:
            rd.draw(screen)
 
        # Glass overlay
        glass = pygame.Surface((wr.width, wr.height), pygame.SRCALPHA)
        glass.fill((160, 200, 240, 18))
        screen.blit(glass, wr.topleft)
 
        # Window cross dividers
        mx = wr.left + wr.width//2
        my = wr.top + wr.height//2
        pygame.draw.line(screen, C_WOOD, (mx, wr.top), (mx, wr.bottom), 5)
        pygame.draw.line(screen, C_WOOD, (wr.left, my), (wr.right, my), 5)
        pygame.draw.rect(screen, C_WOOD, wr, 5, border_radius=2)
 
        # "no survivors" inscription (faint, on glass)
        if self.window_done:
            msg = f_tiny.render("no survivors • olha para a cama", True, (220, 210, 200))
            ms = pygame.Surface(msg.get_size(), pygame.SRCALPHA)
            ms.blit(msg, (0,0))
            ms.set_alpha(90)
            screen.blit(ms, (wr.left + 8, wr.bottom - 24))
 
    def _draw_bed(self):
        bed = self.objs["bed"]["rect"]
        # Bed frame
        pygame.draw.rect(screen, C_WOOD, bed, border_radius=8)
        pygame.draw.rect(screen, C_WOOD_LT, bed, 3, border_radius=8)
 
        # Headboard
        hb = pygame.Rect(bed.left, bed.top, bed.width, 60)
        pygame.draw.rect(screen, C_WOOD_LT, hb, border_radius=6)
        pygame.draw.rect(screen, C_WOOD, hb, 3, border_radius=6)
 
        # Mattress
        mat = pygame.Rect(bed.left+8, bed.top+60, bed.width-16, bed.height-75)
        pygame.draw.rect(screen, (90, 82, 75), mat, border_radius=4)
 
        if not self.bed_done:
            # Messy sheets
            colors = [(140, 128, 110), (120, 108, 94), (155, 140, 122)]
            for i, c in enumerate(colors):
                offset_x = random.randint(-5, 5) if not hasattr(self, '_sheet_offsets') else self._sheet_offsets[i][0]
                offset_y = random.randint(-5, 5) if not hasattr(self, '_sheet_offsets') else self._sheet_offsets[i][1]
                sh = pygame.Rect(mat.left+6+offset_x, mat.top+8+i*20+offset_y, mat.width-12, 45)
                pygame.draw.rect(screen, c, sh, border_radius=8)
                # Wrinkle lines
                for wx in range(sh.left+10, sh.right-10, 20):
                    pygame.draw.arc(screen, (max(0,c[0]-20), max(0,c[1]-20), max(0,c[2]-20)),
                                    pygame.Rect(wx, sh.top+5, 18, 14), 0, math.pi, 2)
            # Pillow (messy)
            pil = pygame.Rect(mat.left+15, mat.top+5, 100, 55)
            pygame.draw.ellipse(screen, (175, 165, 148), pil)
            pil2 = pygame.Rect(mat.left+130, mat.top+8, 95, 50)
            pygame.draw.ellipse(screen, (160, 150, 133), pil2)
        else:
            # Neat sheets
            for i, c in enumerate([(150,138,120),(160,148,130),(170,158,140)]):
                sh = pygame.Rect(mat.left+6, mat.top+10+i*38, mat.width-12, 36)
                pygame.draw.rect(screen, c, sh, border_radius=6)
            # Pillows neat
            pil = pygame.Rect(mat.left+15, mat.top+8, 100, 48)
            pygame.draw.ellipse(screen, (195,185,168), pil)
            pygame.draw.ellipse(screen, (175,165,148), pil, 2)
            pil2 = pygame.Rect(mat.left+130, mat.top+8, 95, 48)
            pygame.draw.ellipse(screen, (190,180,163), pil2)
            pygame.draw.ellipse(screen, (170,160,143), pil2, 2)
 
    def _draw_nightstand(self):
        ns = pygame.Rect(430, 480, 80, 100)
        pygame.draw.rect(screen, C_WOOD, ns, border_radius=4)
        pygame.draw.rect(screen, C_WOOD_LT, ns, 2, border_radius=4)
        # Drawer line
        pygame.draw.line(screen, C_WOOD_LT, (ns.left+8, ns.top+45), (ns.right-8, ns.top+45), 1)
        # Handle
        pygame.draw.circle(screen, C_GOLD, (ns.centerx, ns.top+48), 4)
        # Lamp
        lx, ly = ns.centerx, ns.top
        pygame.draw.rect(screen, (60,55,50), (lx-4, ly-50, 8, 50))  # pole
        # Lampshade
        shade_pts = [(lx-30, ly-50), (lx+30, ly-50), (lx+18, ly-90), (lx-18, ly-90)]
        pygame.draw.polygon(screen, (180, 155, 90), shade_pts)
        pygame.draw.polygon(screen, (140, 120, 70), shade_pts, 2)
        # Lamp glow
        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        for r in range(38, 0, -2):
            alpha = int(10 * r / 38)
            pygame.draw.circle(glow, (255, 220, 100, alpha), (40, 40), r)
        screen.blit(glow, (lx-40, ly-90))
 
    def _draw_glasses(self):
        gr = self.objs["glasses"]["rect"]
        cx, cy = gr.centerx, gr.centery
        # Table surface
        pygame.draw.rect(screen, (55, 42, 30), pygame.Rect(120, 545, 160, 10), border_radius=3)
        # Frame
        left_lens = pygame.Rect(cx - 44, cy - 14, 38, 28)
        right_lens = pygame.Rect(cx + 6, cy - 14, 38, 28)
        # Shadow
        for i in range(4, 0, -1):
            pygame.draw.ellipse(screen, (20,16,12), left_lens.inflate(i*2, i), )
            pygame.draw.ellipse(screen, (20,16,12), right_lens.inflate(i*2, i))
        # Lenses
        pygame.draw.ellipse(screen, (80, 110, 140), left_lens)
        pygame.draw.ellipse(screen, (80, 110, 140), right_lens)
        pygame.draw.ellipse(screen, (200,200,210), left_lens, 2)
        pygame.draw.ellipse(screen, (200,200,210), right_lens, 2)
        # Bridge
        pygame.draw.line(screen, (180,180,190), (left_lens.right, cy), (right_lens.left, cy), 2)
        # Arms
        pygame.draw.line(screen, (180,180,190), (left_lens.left, cy), (left_lens.left-20, cy+5), 2)
        pygame.draw.line(screen, (180,180,190), (right_lens.right, cy), (right_lens.right+20, cy+5), 2)
        # Glint
        pygame.draw.circle(screen, (230,235,245), (left_lens.left+8, left_lens.top+6), 4)
 
        if self.glasses_done:
            chk = f_tiny.render("✓", True, C_GREEN)
            screen.blit(chk, (gr.right+4, gr.top))
 
    def _draw_diary(self):
        dr = self.objs["diary"]["rect"]
        # Book body
        pygame.draw.rect(screen, (80, 40, 25), dr, border_radius=3)
        pygame.draw.rect(screen, (100, 55, 35), dr, 2, border_radius=3)
        # Spine
        pygame.draw.rect(screen, (60, 28, 16), pygame.Rect(dr.left, dr.top, 10, dr.height), border_radius=2)
        # Pages edge
        pygame.draw.rect(screen, (195, 180, 155), pygame.Rect(dr.right-8, dr.top+3, 6, dr.height-6), border_radius=2)
        # Title on cover
        t = f_tiny.render("Diário", True, (200, 170, 110))
        screen.blit(t, (dr.left + 12, dr.centery - 8))
        # Lock clasp
        pygame.draw.rect(screen, C_GOLD, pygame.Rect(dr.right-14, dr.centery-6, 10, 12), border_radius=3)
 
        if self.diary_done:
            chk = f_tiny.render("✓", True, C_GREEN)
            screen.blit(chk, (dr.right+4, dr.top))
 
    def _draw_safe_obj(self):
        sr = self.objs["safe"]["rect"]
        # Body
        pygame.draw.rect(screen, C_SAFE, sr, border_radius=6)
        pygame.draw.rect(screen, C_SAFE_LT, sr, 3, border_radius=6)
        # Door
        door = sr.inflate(-20, -20)
        pygame.draw.rect(screen, (65,65,70), door, border_radius=4)
        pygame.draw.rect(screen, (90,90,95), door, 2, border_radius=4)
 
        if self.safe_done:
            # Open safe
            pygame.draw.rect(screen, (40,35,30), door, border_radius=4)
            t = f_tiny.render("ABERTO", True, C_GREEN)
            screen.blit(t, (sr.centerx - t.get_width()//2, sr.centery - 8))
            chk = f_tiny.render("✓", True, C_GREEN)
            screen.blit(chk, (sr.right+4, sr.top))
        else:
            # Dial
            dial_cx, dial_cy = sr.centerx - 15, sr.centery
            pygame.draw.circle(screen, C_DIAL, (dial_cx, dial_cy), 20)
            pygame.draw.circle(screen, (80,80,85), (dial_cx, dial_cy), 20, 2)
            # Notches
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                x1 = dial_cx + int(14 * math.cos(rad))
                y1 = dial_cy + int(14 * math.sin(rad))
                x2 = dial_cx + int(18 * math.cos(rad))
                y2 = dial_cy + int(18 * math.sin(rad))
                pygame.draw.line(screen, (100,100,110), (x1,y1), (x2,y2), 1)
            # Needle
            needle_angle = math.radians(self.t * 30 % 360)
            nx = dial_cx + int(12 * math.cos(needle_angle))
            ny = dial_cy + int(12 * math.sin(needle_angle))
            pygame.draw.line(screen, C_RED, (dial_cx, dial_cy), (nx, ny), 2)
            # Handle
            pygame.draw.rect(screen, C_GOLD, pygame.Rect(sr.right-28, sr.centery-5, 14, 10), border_radius=3)
            # Label
            lbl = f_tiny.render("COFRE", True, (160,160,165))
            screen.blit(lbl, (sr.centerx - lbl.get_width()//2, sr.bottom - 20))
 
    def _draw_vignette(self):
        vign = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(30):
            alpha = i * 3
            r = pygame.Rect(i*5, i*4, W-i*10, H-i*8)
            pygame.draw.rect(vign, (0, 0, 0, alpha), r)
        screen.blit(vign, (0,0))
 
    # ── Room UI ──────────────────────────────────────
    def _draw_room_ui(self):
        # Progress tracker top-left
        panel = pygame.Rect(16, 16, 240, 148)
        draw_rect_alpha(screen, (15, 13, 18, 210), panel, radius=10)
        pygame.draw.rect(screen, (80, 70, 55), panel, 1, border_radius=10)
 
        title = f_small.render("Fase 1 — O Quarto", True, (180, 165, 130))
        screen.blit(title, (panel.left+12, panel.top+10))
 
        steps = [
            ("Óculos",  self.glasses_done),
            ("Diário",  self.diary_done),
            ("Janela",  self.window_done),
            ("Cama",    self.bed_done),
            ("Cofre",   self.safe_done),
        ]
        for i, (label, done) in enumerate(steps):
            y = panel.top + 36 + i*22
            c = C_GREEN if done else (100, 92, 80)
            icon = "●" if done else "○"
            t = f_tiny.render(f"{icon} {label}", True, c)
            screen.blit(t, (panel.left+14, y))
 
        # Notification
        if self.notif_timer > 0:
            alpha = min(255, int(self.notif_timer * 200))
            nb = pygame.Rect(W//2 - 300, H - 70, 600, 44)
            draw_rect_alpha(screen, (30, 26, 20, alpha), nb, radius=8)
            pygame.draw.rect(screen, (*C_GOLD, alpha), nb, 1, border_radius=8)
            nt = f_small.render(self.notif_text, True, (220, 200, 150))
            ns = pygame.Surface(nt.get_size(), pygame.SRCALPHA)
            ns.blit(nt, (0,0))
            ns.set_alpha(alpha)
            screen.blit(ns, (W//2 - nt.get_width()//2, nb.top + 10))
 
        # Hint at bottom
        hint_obj = None
        for key, obj in self.objs.items():
            done_map = {
                "glasses": self.glasses_done,
                "diary": self.diary_done,
                "window": self.window_done,
                "bed": self.bed_done,
                "safe": self.safe_done,
            }
            if not done_map.get(key, False):
                hint_obj = obj
                break
        if hint_obj and not self.popup_active:
            ht = f_tiny.render(f"💡 {hint_obj['hint']}", True, (140, 128, 100))
            screen.blit(ht, (W - ht.get_width() - 20, H - 30))
 
    # ── Popup ────────────────────────────────────────
    def _draw_popup(self):
        if self.popup_alpha <= 5:
            return
 
        # Dim overlay
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(180, self.popup_alpha)))
        screen.blit(dim, (0,0))
 
        pr = self._get_popup_rect()
 
        if self.popup_type == "window":
            self._draw_popup_window(pr)
        elif self.popup_type == "diary":
            self._draw_popup_diary(pr)
        else:
            self._draw_popup_message(pr)
 
    def _draw_popup_message(self, pr):
        # Panel
        draw_rect_alpha(screen, (25, 22, 28, self.popup_alpha), pr, radius=14)
        pygame.draw.rect(screen, (100, 85, 60), pr, 2, border_radius=14)
        # Title
        title = f_med.render(self.popup_title, True, C_GOLD)
        screen.blit(title, (pr.left+20, pr.top+16))
        # Close
        close = f_body.render("✕", True, (160,140,120))
        screen.blit(close, (pr.right-40, pr.top+12))
        # Body
        draw_text_wrapped(screen, self.popup_text, f_body, C_TEXT,
                          pygame.Rect(pr.left+24, pr.top+58, pr.width-48, pr.height-80),
                          center=True)
        # Hint
        h = f_tiny.render("Clique para fechar", True, (100, 90, 72))
        screen.blit(h, (pr.centerx - h.get_width()//2, pr.bottom - 26))
 
    def _draw_popup_diary(self, pr):
        # Paper background
        paper = pygame.Surface((pr.width, pr.height), pygame.SRCALPHA)
        paper.fill((*C_PAPER, self.popup_alpha))
        # Aged spots
        for _ in range(20):
            rx = random.randint(10, pr.width-10) if not hasattr(self, '_diary_spots') else self._diary_spots[_ % len(self._diary_spots)][0]
            ry = random.randint(10, pr.height-10) if not hasattr(self, '_diary_spots') else self._diary_spots[_ % len(self._diary_spots)][1]
            pygame.draw.circle(paper, (*C_PAPER_DK, 40), (rx, ry), random.randint(3,10))
        screen.blit(paper, pr.topleft)
        pygame.draw.rect(screen, C_PAPER_DK, pr, 2, border_radius=8)
 
        # Red margin line
        pygame.draw.line(screen, (180, 80, 70), (pr.left+60, pr.top+20), (pr.left+60, pr.bottom-20), 1)
 
        # Lines
        for y in range(pr.top+55, pr.bottom-30, 28):
            pygame.draw.line(screen, (180, 168, 140), (pr.left+20, y), (pr.right-20, y), 1)
 
        # Title
        title = f_title.render(self.popup_title, True, C_INK2)
        screen.blit(title, (pr.left+20, pr.top+12))
        # Close
        close = f_body.render("✕", True, C_INK2)
        screen.blit(close, (pr.right-40, pr.top+12))
 
        # Handwritten text (simulate messy)
        lines = self.popup_text.split('\n')
        y = pr.top + 60
        for line in lines:
            if not line.strip():
                y += 14
                continue
            # Simulate wobbly handwriting with slight offset
            for i, char in enumerate(line):
                offset_y = int(math.sin(i * 0.8 + y * 0.1) * 1.5)
                ct = f_hand.render(char, True, C_INK)
                cw = f_hand.size(char)[0]
                screen.blit(ct, (pr.left + 70 + i * 10, y + offset_y))
            # Simpler: just render full line with slight skew
            y += 32
 
        # Actually render properly readable but with ink color
        y = pr.top + 60
        for line in lines:
            if not line.strip():
                y += 14
                continue
            # Re-render properly
            screen.blit(pygame.Surface((pr.width-80, 30), pygame.SRCALPHA), (pr.left+65, y))
            lt = f_hand.render(line, True, C_INK)
            screen.blit(lt, (pr.left + 70, y))
            y += 32
 
        h = f_tiny.render("Clique para fechar", True, C_INK2)
        screen.blit(h, (pr.centerx - h.get_width()//2, pr.bottom - 22))
 
    def _draw_popup_window(self, pr):
        # Dark frame
        draw_rect_alpha(screen, (10, 15, 22, self.popup_alpha), pr, radius=10)
        pygame.draw.rect(screen, C_WOOD, pr, 6, border_radius=10)
 
        # Forest view
        forest_rect = pr.inflate(-16, -16)
        forest_surf = pygame.Surface((forest_rect.width, forest_rect.height))
        forest_surf.fill(C_FOREST2)
 
        # Trees
        for tx in range(20, forest_rect.width, 40):
            th = 100 + (tx % 80)
            ph = 30 + (tx % 15)
            pygame.draw.rect(forest_surf, (25,50,28), (tx-6, forest_rect.height-ph, 12, ph))
            pts = [(tx, forest_rect.height-ph-th//2),
                   (tx-30, forest_rect.height-ph),
                   (tx+30, forest_rect.height-ph)]
            pygame.draw.polygon(forest_surf, C_FOREST, pts)
            pts2 = [(tx, forest_rect.height-ph-th//2-30),
                    (tx-20, forest_rect.height-ph-th//3),
                    (tx+20, forest_rect.height-ph-th//3)]
            pygame.draw.polygon(forest_surf, (35,65,38), pts2)
 
        # Sky
        for y in range(forest_rect.height//3):
            g = int(15 + 20 * y / (forest_rect.height//3))
            pygame.draw.line(forest_surf, (g, g+10, g+30), (0, y), (forest_rect.width, y))
 
        screen.blit(forest_surf, forest_rect.topleft)
 
        # Rain on zoomed window
        for _ in range(80):
            rx = random.randint(forest_rect.left, forest_rect.right)
            ry = random.randint(forest_rect.top, forest_rect.bottom)
            rlen = random.randint(10, 25)
            alpha_r = random.randint(60, 150)
            s = pygame.Surface((2, rlen), pygame.SRCALPHA)
            s.fill((*C_RAIN2, alpha_r))
            screen.blit(s, (rx, ry))
 
        # Glass overlay
        glass = pygame.Surface((forest_rect.width, forest_rect.height), pygame.SRCALPHA)
        glass.fill((160, 200, 240, 25))
        # Fog/condensation patches
        for _ in range(5):
            fx = random.randint(20, forest_rect.width-60)
            fy = random.randint(20, forest_rect.height-40)
            fw, fh = random.randint(40,120), random.randint(20,50)
            pygame.draw.ellipse(glass, (200,225,255,15), (fx, fy, fw, fh))
        screen.blit(glass, forest_rect.topleft)
 
        # THE INSCRIPTION — carved into glass
        insc1 = f_title.render("no survivors", True, (240, 235, 228))
        insc2 = f_med.render("olha para a cama", True, (220, 215, 208))
 
        # Shadow/depth effect
        sh1 = f_title.render("no survivors", True, (0,0,0))
        sh2 = f_med.render("olha para a cama", True, (0,0,0))
        screen.blit(sh1, (forest_rect.centerx - insc1.get_width()//2 + 2, forest_rect.centery - 38 + 2))
        screen.blit(sh2, (forest_rect.centerx - insc2.get_width()//2 + 2, forest_rect.centery + 12 + 2))
 
        glow_text(screen, "no survivors", f_title, (240,235,228),
                  (forest_rect.centerx - insc1.get_width()//2, forest_rect.centery - 38),
                  glow_color=(180,220,255), glow_r=3)
        glow_text(screen, "olha para a cama", f_med, (220,215,208),
                  (forest_rect.centerx - insc2.get_width()//2, forest_rect.centery + 12),
                  glow_color=(180,220,255), glow_r=2)
 
        # Frame dividers
        mx = forest_rect.left + forest_rect.width//2
        my = forest_rect.top + forest_rect.height//2
        pygame.draw.line(screen, C_WOOD, (mx, pr.top+5), (mx, pr.bottom-5), 8)
        pygame.draw.line(screen, C_WOOD, (pr.left+5, my), (pr.right-5, my), 8)
 
        # Close
        close = f_body.render("✕", True, (200,185,160))
        screen.blit(close, (pr.right-44, pr.top+10))
        h = f_tiny.render("Clique para fechar", True, (160,148,128))
        screen.blit(h, (pr.centerx - h.get_width()//2, pr.bottom + 8))
 
    # ── Bed Puzzle ───────────────────────────────────
    def _draw_bed_puzzle(self):
        # Dim overlay
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        screen.blit(dim, (0,0))
 
        pr = pygame.Rect(W//2 - 340, H//2 - 260, 680, 520)
        draw_rect_alpha(screen, (20, 18, 24, 255), pr, radius=16)
        pygame.draw.rect(screen, C_WOOD, pr, 3, border_radius=16)
 
        # Timer
        elapsed = time.time() - self.puzzle_start
        remaining = max(0, self.puzzle_time - elapsed)
        t_color = C_RED if remaining < 10 else C_GOLD
        timer_txt = f_title.render(f"⏱ {remaining:.0f}s", True, t_color)
        screen.blit(timer_txt, (pr.right - timer_txt.get_width() - 16, pr.top+14))
 
        # Timer bar
        bar_w = pr.width - 40
        bar_rect = pygame.Rect(pr.left+20, pr.top+60, bar_w, 8)
        pygame.draw.rect(screen, (50,45,40), bar_rect, border_radius=4)
        fill = int(bar_w * remaining / self.puzzle_time)
        fill_color = C_RED if remaining < 10 else C_GREEN
        pygame.draw.rect(screen, fill_color, pygame.Rect(bar_rect.left, bar_rect.top, fill, 8), border_radius=4)
 
        # Title
        t = f_title.render("Arrume a Cama!", True, (200, 185, 155))
        screen.blit(t, (pr.centerx - t.get_width()//2, pr.top+16))
 
        # Sub
        sub = f_small.render("Resolva as contas — as respostas formam a senha do cofre", True, (140,128,108))
        screen.blit(sub, (pr.centerx - sub.get_width()//2, pr.top+78))
 
        # Answered questions
        ay = pr.top + 115
        for i, (q, _) in enumerate(self.puzzle_questions):
            if i < self.puzzle_idx:
                ans_txt = self.puzzle_answers[i]
                c_q = f_med.render(f"{q}", True, (120,110,90))
                c_a = f_med.render(f"= {ans_txt}  ✓", True, C_GREEN)
                screen.blit(c_q, (pr.left+60, ay))
                screen.blit(c_a, (pr.left+60 + c_q.get_width() + 10, ay))
                ay += 40
 
        # Current question
        if self.puzzle_idx < len(self.puzzle_questions):
            q, _ = self.puzzle_questions[self.puzzle_idx]
            qnum = f_small.render(f"Questão {self.puzzle_idx+1} de {len(self.puzzle_questions)}:", True, C_TEXT_DIM)
            screen.blit(qnum, (pr.left+60, ay+10))
            qt = f_big.render(q, True, C_TEXT)
            screen.blit(qt, (pr.centerx - qt.get_width()//2, ay+36))
 
            # Input field
            inp_rect = pygame.Rect(pr.centerx - 120, ay+110, 240, 58)
            border_c = C_RED if self.puzzle_wrong else (120, 108, 90)
            draw_rect_alpha(screen, (35, 30, 25, 255), inp_rect, radius=10)
            pygame.draw.rect(screen, border_c, inp_rect, 2, border_radius=10)
 
            display = self.puzzle_input if self.puzzle_input else "_"
            blink_cur = "|" if int(self.t * 2) % 2 == 0 else ""
            it = f_big.render(display + blink_cur, True, C_TEXT if self.puzzle_input else (80,72,60))
            screen.blit(it, (inp_rect.centerx - it.get_width()//2, inp_rect.top + 10))
 
            if self.puzzle_wrong:
                wt = f_small.render("Resposta incorreta! Tente novamente.", True, C_RED)
                screen.blit(wt, (pr.centerx - wt.get_width()//2, inp_rect.bottom + 10))
 
            # Instruction
            inst = f_tiny.render("Digite a resposta e pressione ENTER", True, (100,90,72))
            screen.blit(inst, (pr.centerx - inst.get_width()//2, pr.bottom - 30))
 
    # ── Safe UI ──────────────────────────────────────
    def _draw_safe(self):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0,0,0,200))
        screen.blit(dim, (0,0))
 
        pr = pygame.Rect(W//2 - 300, H//2 - 240, 600, 480)
        draw_rect_alpha(screen, (25, 22, 28, 255), pr, radius=16)
        pygame.draw.rect(screen, C_SAFE_LT, pr, 4, border_radius=16)
 
        t = f_title.render("🔒 Cofre", True, C_GOLD)
        screen.blit(t, (pr.centerx - t.get_width()//2, pr.top+18))
 
        # Safe door visual
        door = pygame.Rect(pr.centerx - 80, pr.top+70, 160, 160)
        pygame.draw.rect(screen, C_SAFE, door, border_radius=10)
        pygame.draw.rect(screen, C_SAFE_LT, door, 3, border_radius=10)
 
        # Dial
        dial_cx, dial_cy = door.centerx, door.centery
        pygame.draw.circle(screen, C_DIAL, (dial_cx, dial_cy), 45)
        pygame.draw.circle(screen, (100,100,110), (dial_cx, dial_cy), 45, 3)
        for angle in range(0, 360, 20):
            rad = math.radians(angle)
            x1 = dial_cx + int(32 * math.cos(rad))
            y1 = dial_cy + int(32 * math.sin(rad))
            x2 = dial_cx + int(42 * math.cos(rad))
            y2 = dial_cy + int(42 * math.sin(rad))
            pygame.draw.line(screen, (120,120,130), (x1,y1), (x2,y2), 1)
        needle_angle = math.radians(self.t * 40 % 360)
        nx = dial_cx + int(28 * math.cos(needle_angle))
        ny = dial_cy + int(28 * math.sin(needle_angle))
        pygame.draw.line(screen, C_RED, (dial_cx, dial_cy), (nx, ny), 3)
        pygame.draw.circle(screen, C_GOLD, (dial_cx, dial_cy), 6)
 
        sub = f_small.render("Digite a senha e pressione ENTER", True, (140,128,108))
        screen.blit(sub, (pr.centerx - sub.get_width()//2, pr.top+244))
 
        hint = f_tiny.render(f"(Senha: {len(self.puzzle_code)} dígitos)", True, (100,90,72))
        screen.blit(hint, (pr.centerx - hint.get_width()//2, pr.top+272))
 
        # Input
        inp_rect = pygame.Rect(pr.centerx - 150, pr.top+300, 300, 70)
        flash_border = (self.safe_flash > 0 and int(self.t*8) % 2 == 0)
        border_c = C_RED if (self.safe_wrong or flash_border) else (120,108,90)
        if self.safe_flash > 0:
            self.safe_flash -= 1
        draw_rect_alpha(screen, (35,30,25,255), inp_rect, radius=10)
        pygame.draw.rect(screen, border_c, inp_rect, 2, border_radius=10)
 
        display = "•" * len(self.safe_input) if self.safe_input else "_"
        blink_cur = "|" if int(self.t*2)%2==0 else ""
        it = f_big.render(display + blink_cur, True, C_TEXT if self.safe_input else (80,72,60))
        screen.blit(it, (inp_rect.centerx - it.get_width()//2, inp_rect.top + 14))
 
        if self.safe_wrong:
            wt = f_small.render("Senha incorreta!", True, C_RED)
            screen.blit(wt, (pr.centerx - wt.get_width()//2, inp_rect.bottom + 10))
 
        esc = f_tiny.render("ESC para voltar", True, (100,90,72))
        screen.blit(esc, (pr.centerx - esc.get_width()//2, pr.bottom - 28))
 
    # ── Victory ──────────────────────────────────────
    def _draw_victory(self):
        # Flash overlay
        flash = pygame.Surface((W, H), pygame.SRCALPHA)
        flash.fill((255, 240, 180, max(0, 80 - self.victory_alpha)))
        screen.blit(flash, (0,0))
 
        # Dim
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(170, self.victory_alpha)))
        screen.blit(dim, (0,0))
 
        if self.victory_alpha < 50:
            return
 
        # Box
        pr = pygame.Rect(W//2 - 320, H//2 - 240, 640, 420)
        draw_rect_alpha(screen, (20, 18, 14, min(255, self.victory_alpha)), pr, radius=18)
        pygame.draw.rect(screen, C_GOLD, pr, 3, border_radius=18)
 
        t1 = f_big.render("🗝️  Porta Destrancada!", True, C_GOLD)
        screen.blit(t1, (pr.centerx - t1.get_width()//2, pr.top+28))
 
        # Animated key
        key_y = int(self.key_y)
        key_t = f_big.render("🗝️", True, C_GOLD)
        if key_y < H:
            screen.blit(key_t, (pr.centerx - key_t.get_width()//2, key_y))
 
        msg = f_body.render("Você encontrou a chave do quarto!", True, C_TEXT)
        screen.blit(msg, (pr.centerx - msg.get_width()//2, pr.top+120))
 
        msg2 = f_med.render("A porta range ao abrir…", True, C_TEXT_DIM)
        screen.blit(msg2, (pr.centerx - msg2.get_width()//2, pr.top+160))
 
        # Sparkles
        for i in range(12):
            angle = self.t * 60 + i * 30
            rad = math.radians(angle)
            sx = pr.centerx + int(160 * math.cos(rad))
            sy = pr.centery + int(80 * math.sin(rad))
            size = int(3 + 3 * math.sin(self.t * 4 + i))
            pygame.draw.circle(screen, C_GOLD, (sx, sy), size)
 
        if self.victory_alpha > 200:
            cont = f_small.render("[ Clique para ir ao próximo cômodo ]", True, (160, 148, 120))
            blink = pulse(self.t, 3, 130, 200)
            cont = f_small.render("[ Clique para ir ao próximo cômodo ]", True, (blink, blink-20, blink-40))
            screen.blit(cont, (pr.centerx - cont.get_width()//2, pr.bottom - 44))
 
    # ── Next Room ────────────────────────────────────
    def _draw_next_room(self):
        screen.fill((8, 7, 10))
        # Fade in "Em breve..."
        t = f_big.render("Em breve…", True, (140, 128, 108))
        screen.blit(t, (W//2 - t.get_width()//2, H//2 - 60))
        s = f_body.render("Fase 2: A Cozinha", True, (100,90,72))
        screen.blit(s, (W//2 - s.get_width()//2, H//2 + 20))
        s2 = f_small.render("O Enigma da Cabana continua…", True, (80,72,58))
        screen.blit(s2, (W//2 - s2.get_width()//2, H//2 + 70))
 
# ─── Main ─────────────────────────────────────────────
def main():
    game = Game()
    running = True
 
    while running:
        dt = clock.tick(FPS) / 1000.0
 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            game.handle_event(event)
 
        game.update(dt)
        game.draw()
 
    pygame.quit()
    sys.exit()
 
if __name__ == "__main__":
    main()