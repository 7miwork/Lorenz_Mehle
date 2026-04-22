import pygame
import sys
import math
import random

pygame.init()

# ── Fenster ──────────────────────────────────────────────────────────────────
W, H = 900, 550
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Samurai vs Ninja – Stickman Kampf")
clock = pygame.time.Clock()

# ── Farben ───────────────────────────────────────────────────────────────────
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
RED     = (220, 40, 40)
DARK_RED= (140, 10, 10)
BLUE    = (40, 80, 200)
DARK_BLU= (10, 30, 120)
GOLD    = (255, 200, 40)
SILVER  = (180, 190, 210)
GRAY    = (100, 100, 110)
DARK_GR = (30, 30, 35)
SKY     = (20, 20, 30)
GROUND  = (50, 40, 30)
GREEN   = (40, 200, 80)
YELLOW  = (255, 230, 0)
PURPLE  = (140, 0, 200)
ORANGE  = (255, 140, 0)
TRANS   = (0, 0, 0, 0)

# ── Fonts ─────────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 52, bold=True)
font_med   = pygame.font.SysFont("consolas", 28, bold=True)
font_small = pygame.font.SysFont("consolas", 18)
font_tiny  = pygame.font.SysFont("consolas", 14)

GROUND_Y = 420  # Boden-Y-Koordinate

# ═══════════════════════════════════════════════════════════════════════════════
#  STICKMAN ZEICHNUNG
# ═══════════════════════════════════════════════════════════════════════════════

def draw_samurai(surf, cx, cy, color, facing, anim, attacking, blocking, special, hurt):
    """Zeichnet einen Samurai-Stickman."""
    if hurt:
        color = (255, 100, 100)

    scale = 1.0
    # Kopf-Y schwingt beim Gehen
    head_bob = math.sin(anim * 0.3) * 3 if not attacking else 0

    head_r = 18
    head_y = cy - 80 + head_bob
    # Kopf
    pygame.draw.circle(surf, color, (cx, int(head_y)), head_r, 3)

    # Helm (Kabuto)
    helm_pts = [
        (cx - head_r, int(head_y) - 4),
        (cx - head_r + 4, int(head_y) - head_r - 10),
        (cx, int(head_y) - head_r - 18),
        (cx + head_r - 4, int(head_y) - head_r - 10),
        (cx + head_r, int(head_y) - 4),
    ]
    pygame.draw.polygon(surf, GOLD, helm_pts)
    pygame.draw.polygon(surf, color, helm_pts, 2)
    # Helm-Deko (Maedate)
    pygame.draw.line(surf, GOLD, (cx, int(head_y) - head_r - 18), (cx, int(head_y) - head_r - 28), 3)

    # Augen
    eye_x = cx + (8 if facing == 1 else -8)
    pygame.draw.circle(surf, color, (eye_x, int(head_y) - 2), 3, 2)

    # Körper
    body_top = int(head_y) + head_r
    body_bot = cy - 10
    pygame.draw.line(surf, color, (cx, body_top), (cx, body_bot), 4)

    # Kimono-Linie (diagonal)
    pygame.draw.line(surf, GOLD, (cx - 8, body_top + 5), (cx + 5, body_top + 18), 2)

    # Beine
    leg_swing = math.sin(anim * 0.3) * 20
    if attacking:
        leg_swing = 15 * facing
    # linkes Bein
    lk = (cx - 12, body_bot + 25)
    lf = (cx - 16, cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), lk, 3)
    pygame.draw.line(surf, color, lk, lf, 3)
    # rechtes Bein
    rk = (cx + 12, body_bot + 25 - int(leg_swing * 0.3))
    rf = (cx + 16 + int(leg_swing * 0.3), cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), rk, 3)
    pygame.draw.line(surf, color, rk, rf, 3)

    # Arme & Katana
    arm_top = body_top + 12
    if blocking:
        # Block: Schild aus Schwert
        ax = cx + facing * 30
        pygame.draw.line(surf, color, (cx - 8, arm_top), (ax, arm_top + 10), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (ax, arm_top - 10), 3)
        pygame.draw.line(surf, SILVER, (ax - 5, arm_top - 22), (ax + 5, arm_top + 22), 4)
    elif attacking:
        # Angriff: Schwert nach vorne
        swing = math.sin(anim * 0.8) * 30
        ax = cx + facing * 35
        ay = arm_top + int(swing * 0.4)
        pygame.draw.line(surf, color, (cx - 8, arm_top + 5), (ax, ay + 5), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top + 5), (ax, ay - 5), 3)
        # Klinge
        sword_end_x = ax + facing * 52
        sword_end_y = ay - 10
        pygame.draw.line(surf, SILVER, (ax, ay), (sword_end_x, sword_end_y), 4)
        pygame.draw.line(surf, WHITE,  (ax, ay), (ax + facing * 20, ay - 4), 2)
        # Tsuba (Parierstange)
        pygame.draw.line(surf, GOLD, (ax, ay - 8), (ax, ay + 8), 3)
    elif special:
        # Spezial: beide Arme hoch + Schwert oben
        pygame.draw.line(surf, color, (cx - 8, arm_top), (cx - 25, arm_top - 28), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (cx + 25, arm_top - 28), 3)
        pygame.draw.line(surf, SILVER, (cx + 10, arm_top - 28), (cx + 10, arm_top - 70), 4)
        pygame.draw.line(surf, GOLD,   (cx + 4,  arm_top - 28), (cx + 18, arm_top - 28), 3)
    else:
        # Idle: Schwert an der Seite
        sx = cx + facing * 12
        pygame.draw.line(surf, color, (cx - 8, arm_top), (sx - 5, arm_top + 22), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (sx + 5, arm_top + 22), 3)
        pygame.draw.line(surf, SILVER, (sx, arm_top + 22), (sx + facing * 10, arm_top + 58), 3)

    # Effekt bei Spezial
    if special:
        for i in range(6):
            angle = anim * 0.2 + i * (math.pi / 3)
            ex = cx + int(math.cos(angle) * 55)
            ey = head_y - 10 + int(math.sin(angle) * 35)
            pygame.draw.circle(surf, GOLD, (int(ex), int(ey)), 5)


def draw_ninja(surf, cx, cy, color, facing, anim, attacking, blocking, special, hurt):
    """Zeichnet einen Ninja-Stickman."""
    if hurt:
        color = (255, 100, 100)

    head_bob = math.sin(anim * 0.35) * 4 if not attacking else 0
    head_r = 17
    head_y = cy - 82 + head_bob

    # Kopf (Maske)
    pygame.draw.circle(surf, color, (cx, int(head_y)), head_r, 3)
    # Stirnband
    pygame.draw.line(surf, RED, (cx - head_r, int(head_y) - 4),
                                (cx + head_r, int(head_y) - 4), 4)
    # Augen (schmal)
    eye_x = cx + (7 if facing == 1 else -7)
    pygame.draw.line(surf, WHITE, (eye_x - 4, int(head_y) - 2),
                                  (eye_x + 4, int(head_y) - 2), 2)

    # Körper
    body_top = int(head_y) + head_r
    body_bot = cy - 12
    pygame.draw.line(surf, color, (cx, body_top), (cx, body_bot), 4)

    # Gürtel
    pygame.draw.line(surf, RED, (cx - 10, body_top + 20),
                                (cx + 10, body_top + 20), 3)

    # Beine (schnell)
    leg_swing = math.sin(anim * 0.45) * 22
    if attacking:
        leg_swing = 18 * facing
    lk = (cx - 13, body_bot + 22)
    lf = (cx - 18, cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), lk, 3)
    pygame.draw.line(surf, color, lk, lf, 3)
    rk = (cx + 13, body_bot + 22 - int(leg_swing * 0.3))
    rf = (cx + 18 + int(leg_swing * 0.3), cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), rk, 3)
    pygame.draw.line(surf, color, rk, rf, 3)

    arm_top = body_top + 10

    if blocking:
        # Ninja Block: Kunai vor sich
        ax = cx + facing * 28
        pygame.draw.line(surf, color, (cx - 7, arm_top), (ax, arm_top + 8), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (ax, arm_top - 8), 3)
        pygame.draw.line(surf, SILVER, (ax, arm_top - 18), (ax, arm_top + 18), 3)
        # Kunai Blatt
        kunai_tip = (ax + facing * 12, arm_top)
        pygame.draw.polygon(surf, SILVER, [
            (ax, arm_top - 6), (ax, arm_top + 6), kunai_tip])
    elif attacking:
        # Angriff: Kunai-Wurf
        swing = math.sin(anim * 1.0) * 25
        ax = cx + facing * 32
        ay = arm_top + int(swing * 0.3)
        pygame.draw.line(surf, color, (cx - 7, arm_top + 4), (ax, ay + 4), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top + 4), (ax, ay - 4), 3)
        # Kunai
        tip = (ax + facing * 38, ay - 8)
        pygame.draw.line(surf, SILVER, (ax, ay), tip, 3)
        # Kunai Blatt
        pygame.draw.polygon(surf, SILVER, [
            (tip[0], tip[1] - 5), (tip[0], tip[1] + 5),
            (tip[0] + facing * 12, tip[1])])
        # Seil
        pygame.draw.line(surf, GRAY, (ax, ay), (ax - facing * 8, ay + 10), 1)
    elif special:
        # Spezial: Shuriken-Sturm
        pygame.draw.line(surf, color, (cx - 7, arm_top), (cx - 30, arm_top - 22), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (cx + 30, arm_top - 22), 3)
        for i in range(3):
            angle = anim * 0.5 + i * (2 * math.pi / 3)
            sx = cx + int(math.cos(angle) * (30 + i * 18))
            sy = int(head_y) - 10 + int(math.sin(angle) * 20)
            # Shuriken
            for j in range(4):
                a2 = angle + j * (math.pi / 2)
                pygame.draw.line(surf, SILVER,
                    (sx, sy),
                    (sx + int(math.cos(a2) * 8), sy + int(math.sin(a2) * 8)), 2)
    else:
        # Idle
        sx = cx + facing * 10
        pygame.draw.line(surf, color, (cx - 7, arm_top), (sx - 5, arm_top + 20), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (sx + 5, arm_top + 20), 3)
        # Kunai in der Hand
        pygame.draw.line(surf, SILVER, (sx, arm_top + 20),
                         (sx + facing * 8, arm_top + 32), 2)

    if special:
        for i in range(8):
            angle = anim * 0.4 + i * (math.pi / 4)
            ex = cx + int(math.cos(angle) * 60)
            ey = int(head_y) + int(math.sin(angle) * 40)
            for j in range(4):
                a2 = angle + j * (math.pi / 2)
                pygame.draw.line(surf, PURPLE,
                    (int(ex), int(ey)),
                    (int(ex + math.cos(a2) * 6), int(ey + math.sin(a2) * 6)), 2)


# ═══════════════════════════════════════════════════════════════════════════════
#  HINTERGRUND
# ═══════════════════════════════════════════════════════════════════════════════

def draw_background(surf, tick):
    # Himmel
    surf.fill(SKY)

    # Mond
    pygame.draw.circle(surf, (200, 200, 180), (720, 70), 45)
    pygame.draw.circle(surf, SKY, (735, 60), 38)

    # Sterne
    random.seed(42)
    for _ in range(60):
        sx = random.randint(0, W)
        sy = random.randint(0, 180)
        bright = 120 + int(math.sin(tick * 0.03 + sx) * 60)
        pygame.draw.circle(surf, (bright, bright, bright), (sx, sy), 1)

    # Berge (Silhouette)
    mountain_pts = [
        (0, 300), (80, 200), (160, 280), (260, 160), (370, 260),
        (460, 180), (560, 270), (650, 200), (760, 280), (860, 190),
        (900, 240), (900, 300), (0, 300)
    ]
    pygame.draw.polygon(surf, (25, 25, 35), mountain_pts)

    # Boden
    pygame.draw.rect(surf, (40, 32, 22), (0, GROUND_Y, W, H - GROUND_Y))
    pygame.draw.rect(surf, (60, 48, 30), (0, GROUND_Y, W, 6))

    # Dojo-Gitter
    for i in range(0, W, 40):
        pygame.draw.line(surf, (55, 43, 28), (i, GROUND_Y + 6), (i, H), 1)

    # Bambus links & rechts
    for bx, count in [(60, 3), (820, 3)]:
        for bi in range(count):
            x = bx + bi * 20
            pygame.draw.rect(surf, (30, 80, 30), (x, GROUND_Y - 120, 8, 120))
            for seg in range(0, 120, 22):
                pygame.draw.line(surf, (20, 60, 20), (x, GROUND_Y - 120 + seg),
                                 (x + 8, GROUND_Y - 120 + seg), 2)
            # Blätter
            lx = x + 4 + int(math.sin(tick * 0.04 + bi) * 5)
            pygame.draw.line(surf, (40, 110, 40), (lx, GROUND_Y - 125), (lx - 18, GROUND_Y - 135), 3)
            pygame.draw.line(surf, (40, 110, 40), (lx, GROUND_Y - 125), (lx + 18, GROUND_Y - 140), 3)


# ═══════════════════════════════════════════════════════════════════════════════
#  KAMPF-PARTIKEL
# ═══════════════════════════════════════════════════════════════════════════════

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2
        self.life = random.randint(15, 35)
        self.max_life = self.life
        self.color = color
        self.r = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.25
        self.life -= 1

    def draw(self, surf):
        alpha = self.life / self.max_life
        r = int(self.color[0] * alpha)
        g = int(self.color[1] * alpha)
        b = int(self.color[2] * alpha)
        if self.life > 0:
            pygame.draw.circle(surf, (r, g, b), (int(self.x), int(self.y)), self.r)


# ═══════════════════════════════════════════════════════════════════════════════
#  KÄMPFER KLASSE
# ═══════════════════════════════════════════════════════════════════════════════

class Fighter:
    SPEED = 4
    JUMP_POWER = -14
    GRAVITY = 0.6

    def __init__(self, char_type, x, facing):
        self.char_type = char_type  # "samurai" oder "ninja"
        self.x = float(x)
        self.y = float(GROUND_Y)
        self.facing = facing
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = True

        if char_type == "samurai":
            self.max_hp  = 120
            self.attack  = 18
            self.defense = 0.25
            self.sp_dmg  = 35
            self.color   = BLUE
            self.name    = "SAMURAI"
        else:
            self.max_hp  = 100
            self.attack  = 14
            self.defense = 0.15
            self.sp_dmg  = 28
            self.color   = RED
            self.name    = "NINJA"

        self.hp = self.max_hp
        self.anim_tick = 0
        self.attacking = False
        self.blocking  = False
        self.special   = False
        self.hurt      = False

        self.attack_timer   = 0
        self.block_timer    = 0
        self.special_timer  = 0
        self.hurt_timer     = 0
        self.special_cd     = 0
        self.attack_cd      = 0
        self.hit_registered = False

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - 28, int(self.y) - 110, 56, 110)

    def move(self, left, right, jump):
        if left:  self.vx = -self.SPEED
        elif right: self.vx = self.SPEED
        else: self.vx = 0

        if jump and self.on_ground:
            self.vy = self.JUMP_POWER
            self.on_ground = False

        self.x += self.vx
        self.y += self.vy
        self.vy += self.GRAVITY

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True

        # Grenzen
        self.x = max(50, min(W - 50, self.x))

    def do_attack(self):
        if self.attack_cd <= 0 and not self.attacking:
            self.attacking = True
            self.attack_timer = 25
            self.hit_registered = False
            self.attack_cd = 30

    def do_block(self):
        self.blocking = True
        self.block_timer = 5

    def do_special(self):
        if self.special_cd <= 0 and not self.special:
            self.special = True
            self.special_timer = 40
            self.hit_registered = False
            self.special_cd = 180

    def take_damage(self, dmg, particles, px, py):
        if self.blocking:
            dmg = int(dmg * (1 - self.defense) * 0.4)
        else:
            dmg = int(dmg * (1 - self.defense))
        self.hp = max(0, self.hp - dmg)
        self.hurt = True
        self.hurt_timer = 12
        # Partikel
        color = GOLD if self.blocking else RED
        for _ in range(12):
            particles.append(Particle(px, py, color))

    def update(self, particles):
        self.anim_tick += 1
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.attacking = False
        if self.block_timer > 0:
            self.block_timer -= 1
            if self.block_timer == 0:
                self.blocking = False
        if self.special_timer > 0:
            self.special_timer -= 1
            if self.special_timer == 0:
                self.special = False
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            if self.hurt_timer == 0:
                self.hurt = False
        if self.special_cd > 0:
            self.special_cd -= 1
        if self.attack_cd > 0:
            self.attack_cd -= 1

    def draw(self, surf):
        if self.char_type == "samurai":
            draw_samurai(surf, int(self.x), int(self.y), self.color, self.facing,
                         self.anim_tick, self.attacking, self.blocking, self.special, self.hurt)
        else:
            draw_ninja(surf, int(self.x), int(self.y), self.color, self.facing,
                       self.anim_tick, self.attacking, self.blocking, self.special, self.hurt)


# ═══════════════════════════════════════════════════════════════════════════════
#  EINFACHE KI
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleAI:
    def __init__(self, fighter, target):
        self.fighter = fighter
        self.target = target
        self.think_timer = 0
        self.action = "approach"
        self.retreat_timer = 0

    def update(self):
        f = self.fighter
        t = self.target
        dist = abs(f.x - t.x)

        self.think_timer -= 1
        if self.think_timer <= 0:
            self.think_timer = random.randint(15, 40)
            roll = random.random()
            if dist < 100:
                if roll < 0.35:   self.action = "attack"
                elif roll < 0.55: self.action = "block"
                elif roll < 0.65: self.action = "special"
                elif roll < 0.80: self.action = "retreat"
                else:             self.action = "approach"
            else:
                if roll < 0.65:   self.action = "approach"
                elif roll < 0.80: self.action = "attack"
                else:             self.action = "idle"

        left = right = jump = False
        atk = blk = spc = False

        if self.action == "approach":
            if f.x < t.x: right = True
            else:          left = True
        elif self.action == "retreat":
            if f.x < t.x: left = True
            else:          right = True
        elif self.action == "attack":
            if dist < 120: atk = True
            else:
                if f.x < t.x: right = True
                else:          left = True
        elif self.action == "block":
            blk = True
        elif self.action == "special":
            if dist < 150: spc = True

        # Sprung ab und zu
        if random.random() < 0.008 and f.on_ground:
            jump = True

        # Richtung zum Feind
        f.facing = 1 if t.x > f.x else -1

        f.move(left, right, jump)
        if atk: f.do_attack()
        if blk: f.do_block()
        if spc: f.do_special()


# ═══════════════════════════════════════════════════════════════════════════════
#  HUD ZEICHNEN
# ═══════════════════════════════════════════════════════════════════════════════

def draw_hud(surf, p1, p2, tick):
    # ── Spieler 1 ────────────────────────────────────────────────────────────
    label1 = font_small.render(p1.name, True, p1.color)
    surf.blit(label1, (20, 14))
    # HP-Bar
    bar_w = 280
    hp_w1 = int(bar_w * p1.hp / p1.max_hp)
    pygame.draw.rect(surf, DARK_RED, (20, 38, bar_w, 20), border_radius=5)
    if hp_w1 > 0:
        col = GREEN if p1.hp > p1.max_hp * 0.5 else (YELLOW if p1.hp > p1.max_hp * 0.25 else RED)
        pygame.draw.rect(surf, col, (20, 38, hp_w1, 20), border_radius=5)
    pygame.draw.rect(surf, WHITE, (20, 38, bar_w, 20), 2, border_radius=5)
    hp_txt1 = font_tiny.render(f"{p1.hp}/{p1.max_hp}", True, WHITE)
    surf.blit(hp_txt1, (24, 41))
    # Special-CD
    sp_pct = 1.0 - (p1.special_cd / 180) if p1.special_cd > 0 else 1.0
    sp_w1 = int(bar_w * sp_pct)
    pygame.draw.rect(surf, DARK_GR, (20, 64, bar_w, 10), border_radius=3)
    if sp_w1 > 0:
        pygame.draw.rect(surf, PURPLE, (20, 64, sp_w1, 10), border_radius=3)
    sp_lbl = font_tiny.render("SPEZIAL", True, PURPLE)
    surf.blit(sp_lbl, (24, 65))

    # ── Spieler 2 ────────────────────────────────────────────────────────────
    label2 = font_small.render(p2.name, True, p2.color)
    surf.blit(label2, (W - 20 - label2.get_width(), 14))
    bar_w = 280
    hp_w2 = int(bar_w * p2.hp / p2.max_hp)
    pygame.draw.rect(surf, DARK_RED, (W - 20 - bar_w, 38, bar_w, 20), border_radius=5)
    if hp_w2 > 0:
        col = GREEN if p2.hp > p2.max_hp * 0.5 else (YELLOW if p2.hp > p2.max_hp * 0.25 else RED)
        pygame.draw.rect(surf, col, (W - 20 - bar_w, 38, hp_w2, 20), border_radius=5)
    pygame.draw.rect(surf, WHITE, (W - 20 - bar_w, 38, bar_w, 20), 2, border_radius=5)
    hp_txt2 = font_tiny.render(f"{p2.hp}/{p2.max_hp}", True, WHITE)
    surf.blit(hp_txt2, (W - 20 - bar_w + 4, 41))
    sp_pct2 = 1.0 - (p2.special_cd / 180) if p2.special_cd > 0 else 1.0
    sp_w2 = int(bar_w * sp_pct2)
    pygame.draw.rect(surf, DARK_GR, (W - 20 - bar_w, 64, bar_w, 10), border_radius=3)
    if sp_w2 > 0:
        pygame.draw.rect(surf, PURPLE, (W - 20 - bar_w, sp_w2, sp_w2, 10), border_radius=3)
        pygame.draw.rect(surf, PURPLE, (W - 20 - bar_w, 64, sp_w2, 10), border_radius=3)
    sp_lbl2 = font_tiny.render("SPEZIAL", True, PURPLE)
    surf.blit(sp_lbl2, (W - 20 - bar_w + 4, 65))

    # ── Mitte: VS ────────────────────────────────────────────────────────────
    vs = font_big.render("VS", True, GOLD)
    surf.blit(vs, (W // 2 - vs.get_width() // 2, 22))

    # ── Steuerung ────────────────────────────────────────────────────────────
    ctrl = font_tiny.render("WASD:Bewegung  F:Angriff  G:Block  H:Spezial", True, (120, 120, 140))
    surf.blit(ctrl, (W // 2 - ctrl.get_width() // 2, H - 22))


# ═══════════════════════════════════════════════════════════════════════════════
#  CHARAKTER-AUSWAHL
# ═══════════════════════════════════════════════════════════════════════════════

def char_select_screen():
    chars = ["samurai", "ninja"]
    selected = 0
    tick = 0

    while True:
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                    selected = 1 - selected
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return chars[selected]
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        draw_background(screen, tick)

        # Titel
        title = font_big.render("⚔  STICKMAN KAMPF  ⚔", True, GOLD)
        screen.blit(title, (W // 2 - title.get_width() // 2, 40))
        sub = font_small.render("Wähle deinen Kämpfer!", True, WHITE)
        screen.blit(sub, (W // 2 - sub.get_width() // 2, 105))

        # Karten
        card_w, card_h = 240, 280
        positions = [W // 2 - 160 - card_w // 2, W // 2 + 160 - card_w // 2]
        names_d = {"samurai": ("SAMURAI", "HP: 120  ATK: 18\nDEF: 25%  SP: 35\nSchweres Schwert\nStarke Verteidigung"),
                   "ninja":   ("NINJA",   "HP: 100  ATK: 14\nDEF: 15%  SP: 28\nSchnelle Kunai\nGeschmeidiger Stil")}

        for i, ch in enumerate(chars):
            cx = positions[i] + card_w // 2
            cy = 300
            is_sel = (i == selected)
            border_col = GOLD if is_sel else GRAY
            bob = int(math.sin(tick * 0.05) * 6) if is_sel else 0

            card_rect = pygame.Rect(positions[i], 150 - bob, card_w, card_h)
            pygame.draw.rect(screen, (20, 20, 30), card_rect, border_radius=12)
            pygame.draw.rect(screen, border_col, card_rect, 3, border_radius=12)

            # Figur vorschau
            preview_y = cy - bob
            if ch == "samurai":
                draw_samurai(screen, cx, preview_y, BLUE, 1, tick, False, False, False, False)
            else:
                draw_ninja(screen, cx, preview_y, RED, 1, tick, False, False, False, False)

            # Name
            nm, desc = names_d[ch]
            nm_surf = font_med.render(nm, True, border_col)
            screen.blit(nm_surf, (cx - nm_surf.get_width() // 2, 155 - bob))

            # Stats
            for li, line in enumerate(desc.split("\n")):
                ls = font_tiny.render(line, True, WHITE if is_sel else GRAY)
                screen.blit(ls, (positions[i] + 10, 335 + li * 18 - bob))

            # Selektion-Pfeil
            if is_sel:
                arrow = font_med.render("▼ AUSWAHL ▼", True, GOLD)
                screen.blit(arrow, (cx - arrow.get_width() // 2, 445 - bob))

        hint = font_tiny.render("← → wechseln   ENTER bestätigen", True, (100, 100, 120))
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 45))

        pygame.display.flip()
        clock.tick(60)


# ═══════════════════════════════════════════════════════════════════════════════
#  KAMPF-SCHLEIFE
# ═══════════════════════════════════════════════════════════════════════════════

def fight(player_char):
    ai_char = "ninja" if player_char == "samurai" else "samurai"

    p1 = Fighter(player_char, 200, 1)
    p2 = Fighter(ai_char,     700, -1)
    ai = SimpleAI(p2, p1)

    particles = []
    tick = 0
    round_over = False
    winner = ""
    result_timer = 0

    # Countdown
    for cd in range(3, 0, -1):
        for _ in range(60):
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            draw_background(screen, tick)
            p1.draw(screen); p2.draw(screen)
            draw_hud(screen, p1, p2, tick)
            cd_surf = font_big.render(str(cd), True, GOLD)
            screen.blit(cd_surf, (W // 2 - cd_surf.get_width() // 2, H // 2 - 40))
            pygame.display.flip(); clock.tick(60); tick += 1

    fight_surf = font_big.render("KÄMPFT!", True, RED)
    for _ in range(40):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        draw_background(screen, tick)
        p1.draw(screen); p2.draw(screen)
        draw_hud(screen, p1, p2, tick)
        screen.blit(fight_surf, (W // 2 - fight_surf.get_width() // 2, H // 2 - 40))
        pygame.display.flip(); clock.tick(60); tick += 1

    while True:
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and round_over:
                return  # zurück zur Auswahl

        keys = pygame.key.get_pressed()

        if not round_over:
            # Spieler-Input
            left  = keys[pygame.K_a] or keys[pygame.K_LEFT]
            right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
            jump  = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]
            p1.facing = 1 if p2.x > p1.x else -1
            p1.move(left, right, jump)
            if keys[pygame.K_f]: p1.do_attack()
            if keys[pygame.K_g]: p1.do_block()
            if keys[pygame.K_h]: p1.do_special()

            # KI
            ai.update()

            # Treffer prüfen
            for attacker, defender in [(p1, p2), (p2, p1)]:
                if (attacker.attacking or attacker.special) and not attacker.hit_registered:
                    reach = 110 if attacker.special else 90
                    dist = abs(attacker.x - defender.x)
                    if dist < reach:
                        dmg = attacker.sp_dmg if attacker.special else attacker.attack
                        mid_x = int((attacker.x + defender.x) / 2)
                        mid_y = int(defender.y - 60)
                        defender.take_damage(dmg, particles, mid_x, mid_y)
                        attacker.hit_registered = True

            p1.update(particles); p2.update(particles)

            # Partikel
            for pt in particles[:]:
                pt.update()
                if pt.life <= 0: particles.remove(pt)

            if p1.hp <= 0 or p2.hp <= 0:
                round_over = True
                result_timer = 180
                winner = p1.name if p2.hp <= 0 else p2.name

        # ── Zeichnen ─────────────────────────────────────────────────────────
        draw_background(screen, tick)

        for pt in particles: pt.draw(screen)

        p1.draw(screen); p2.draw(screen)
        draw_hud(screen, p1, p2, tick)

        if round_over:
            # Ergebnis
            result_timer -= 1
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            win_txt = font_big.render(f"{winner} GEWINNT!", True, GOLD)
            screen.blit(win_txt, (W // 2 - win_txt.get_width() // 2, H // 2 - 50))
            hint = font_med.render("Beliebige Taste zum Fortfahren", True, WHITE)
            screen.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 20))

        pygame.display.flip()
        clock.tick(60)


# ═══════════════════════════════════════════════════════════════════════════════
#  HAUPTPROGRAMM
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    while True:
        player_char = char_select_screen()
        fight(player_char)

if __name__ == "__main__":
    main()
