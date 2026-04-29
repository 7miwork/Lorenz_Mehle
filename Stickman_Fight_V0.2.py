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
STAMINA_COL = (200, 200, 100)

# ── Fonts ─────────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("consolas", 52, bold=True)
font_med   = pygame.font.SysFont("consolas", 28, bold=True)
font_small = pygame.font.SysFont("consolas", 18)
font_tiny  = pygame.font.SysFont("consolas", 14)

GROUND_Y = 420 

# ═══════════════════════════════════════════════════════════════════════════════
#  STICKMAN ZEICHNUNG
# ═══════════════════════════════════════════════════════════════════════════════

def draw_samurai(surf, cx, cy, color, facing, anim, attacking, blocking, special, hurt):
    if hurt: color = (255, 100, 100)
    head_bob = math.sin(anim * 0.3) * 3 if not attacking else 0
    head_r = 18
    head_y = cy - 80 + head_bob
    pygame.draw.circle(surf, color, (cx, int(head_y)), head_r, 3)
    helm_pts = [(cx - head_r, int(head_y) - 4), (cx - head_r + 4, int(head_y) - head_r - 10), (cx, int(head_y) - head_r - 18), (cx + head_r - 4, int(head_y) - head_r - 10), (cx + head_r, int(head_y) - 4)]
    pygame.draw.polygon(surf, GOLD, helm_pts)
    pygame.draw.polygon(surf, color, helm_pts, 2)
    pygame.draw.line(surf, GOLD, (cx, int(head_y) - head_r - 18), (cx, int(head_y) - head_r - 28), 3)
    eye_x = cx + (8 if facing == 1 else -8)
    pygame.draw.circle(surf, color, (eye_x, int(head_y) - 2), 3, 2)
    body_top = int(head_y) + head_r
    body_bot = cy - 10
    pygame.draw.line(surf, color, (cx, body_top), (cx, body_bot), 4)
    pygame.draw.line(surf, GOLD, (cx - 8, body_top + 5), (cx + 5, body_top + 18), 2)
    leg_swing = math.sin(anim * 0.3) * 20
    if attacking: leg_swing = 15 * facing
    lk = (cx - 12, body_bot + 25); lf = (cx - 16, cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), lk, 3); pygame.draw.line(surf, color, lk, lf, 3)
    rk = (cx + 12, body_bot + 25 - int(leg_swing * 0.3)); rf = (cx + 16 + int(leg_swing * 0.3), cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), rk, 3); pygame.draw.line(surf, color, rk, rf, 3)
    arm_top = body_top + 12
    if blocking:
        ax = cx + facing * 30
        pygame.draw.line(surf, color, (cx - 8, arm_top), (ax, arm_top + 10), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (ax, arm_top - 10), 3)
        pygame.draw.line(surf, SILVER, (ax - 5, arm_top - 22), (ax + 5, arm_top + 22), 4)
    elif attacking:
        swing = math.sin(anim * 0.8) * 30
        ax = cx + facing * 35; ay = arm_top + int(swing * 0.4)
        pygame.draw.line(surf, color, (cx - 8, arm_top + 5), (ax, ay + 5), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top + 5), (ax, ay - 5), 3)
        sword_end_x = ax + facing * 52; sword_end_y = ay - 10
        pygame.draw.line(surf, SILVER, (ax, ay), (sword_end_x, sword_end_y), 4)
        pygame.draw.line(surf, WHITE,  (ax, ay), (ax + facing * 20, ay - 4), 2)
        pygame.draw.line(surf, GOLD, (ax, ay - 8), (ax, ay + 8), 3)
    elif special:
        pygame.draw.line(surf, color, (cx - 8, arm_top), (cx - 25, arm_top - 28), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (cx + 25, arm_top - 28), 3)
        pygame.draw.line(surf, SILVER, (cx + 10, arm_top - 28), (cx + 10, arm_top - 70), 4)
        pygame.draw.line(surf, GOLD,   (cx + 4,  arm_top - 28), (cx + 18, arm_top - 28), 3)
    else:
        sx = cx + facing * 12
        pygame.draw.line(surf, color, (cx - 8, arm_top), (sx - 5, arm_top + 22), 3)
        pygame.draw.line(surf, color, (cx + 8, arm_top), (sx + 5, arm_top + 22), 3)
        pygame.draw.line(surf, SILVER, (sx, arm_top + 22), (sx + facing * 10, arm_top + 58), 3)
    if special:
        for i in range(6):
            angle = anim * 0.2 + i * (math.pi / 3)
            ex = cx + int(math.cos(angle) * 55); ey = head_y - 10 + int(math.sin(angle) * 35)
            pygame.draw.circle(surf, GOLD, (int(ex), int(ey)), 5)

def draw_ninja(surf, cx, cy, color, facing, anim, attacking, blocking, special, hurt):
    if hurt: color = (255, 100, 100)
    head_bob = math.sin(anim * 0.35) * 4 if not attacking else 0
    head_r = 17
    head_y = cy - 82 + head_bob
    pygame.draw.circle(surf, color, (cx, int(head_y)), head_r, 3)
    pygame.draw.line(surf, RED, (cx - head_r, int(head_y) - 4), (cx + head_r, int(head_y) - 4), 4)
    eye_x = cx + (7 if facing == 1 else -7)
    pygame.draw.line(surf, WHITE, (eye_x - 4, int(head_y) - 2), (eye_x + 4, int(head_y) - 2), 2)
    body_top = int(head_y) + head_r; body_bot = cy - 12
    pygame.draw.line(surf, color, (cx, body_top), (cx, body_bot), 4)
    pygame.draw.line(surf, RED, (cx - 10, body_top + 20), (cx + 10, body_top + 20), 3)
    leg_swing = math.sin(anim * 0.45) * 22
    if attacking: leg_swing = 18 * facing
    lk = (cx - 13, body_bot + 22); lf = (cx - 18, cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), lk, 3); pygame.draw.line(surf, color, lk, lf, 3)
    rk = (cx + 13, body_bot + 22 - int(leg_swing * 0.3)); rf = (cx + 18 + int(leg_swing * 0.3), cy + 5)
    pygame.draw.line(surf, color, (cx, body_bot), rk, 3); pygame.draw.line(surf, color, rk, rf, 3)
    arm_top = body_top + 10
    if blocking:
        ax = cx + facing * 28
        pygame.draw.line(surf, color, (cx - 7, arm_top), (ax, arm_top + 8), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (ax, arm_top - 8), 3)
        pygame.draw.line(surf, SILVER, (ax, arm_top - 18), (ax, arm_top + 18), 3)
        kunai_tip = (ax + facing * 12, arm_top)
        pygame.draw.polygon(surf, SILVER, [(ax, arm_top - 6), (ax, arm_top + 6), kunai_tip])
    elif attacking:
        swing = math.sin(anim * 1.0) * 25
        ax = cx + facing * 32; ay = arm_top + int(swing * 0.3)
        pygame.draw.line(surf, color, (cx - 7, arm_top + 4), (ax, ay + 4), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top + 4), (ax, ay - 4), 3)
        tip = (ax + facing * 38, ay - 8)
        pygame.draw.line(surf, SILVER, (ax, ay), tip, 3)
        pygame.draw.polygon(surf, SILVER, [(tip[0], tip[1] - 5), (tip[0], tip[1] + 5), (tip[0] + facing * 12, tip[1])])
        pygame.draw.line(surf, GRAY, (ax, ay), (ax - facing * 8, ay + 10), 1)
    elif special:
        pygame.draw.line(surf, color, (cx - 7, arm_top), (cx - 30, arm_top - 22), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (cx + 30, arm_top - 22), 3)
        for i in range(3):
            angle = anim * 0.5 + i * (2 * math.pi / 3)
            sx = cx + int(math.cos(angle) * (30 + i * 18)); sy = int(head_y) - 10 + int(math.sin(angle) * 20)
            for j in range(4):
                a2 = angle + j * (math.pi / 2)
                pygame.draw.line(surf, SILVER, (sx, sy), (sx + int(math.cos(a2) * 8), sy + int(math.sin(a2) * 8)), 2)
    else:
        sx = cx + facing * 10
        pygame.draw.line(surf, color, (cx - 7, arm_top), (sx - 5, arm_top + 20), 3)
        pygame.draw.line(surf, color, (cx + 7, arm_top), (sx + 5, arm_top + 20), 3)
        pygame.draw.line(surf, SILVER, (sx, arm_top + 20), (sx + facing * 8, arm_top + 32), 2)
    if special:
        for i in range(8):
            angle = anim * 0.4 + i * (math.pi / 4)
            ex = cx + int(math.cos(angle) * 60); ey = int(head_y) + int(math.sin(angle) * 40)
            for j in range(4):
                a2 = angle + j * (math.pi / 2)
                pygame.draw.line(surf, PURPLE, (int(ex), int(ey)), (int(ex + math.cos(a2) * 6), int(ey + math.sin(a2) * 6)), 2)

# ═══════════════════════════════════════════════════════════════════════════════
#  HINTERGRUND & PARTIKEL
# ═══════════════════════════════════════════════════════════════════════════════

def draw_background(surf, tick):
    surf.fill(SKY)
    pygame.draw.circle(surf, (200, 200, 180), (720, 70), 45)
    pygame.draw.circle(surf, SKY, (735, 60), 38)
    random.seed(42)
    for _ in range(60):
        sx = random.randint(0, W); sy = random.randint(0, 180)
        bright = 120 + int(math.sin(tick * 0.03 + sx) * 60)
        pygame.draw.circle(surf, (bright, bright, bright), (sx, sy), 1)
    mountain_pts = [(0, 300), (80, 200), (160, 280), (260, 160), (370, 260), (460, 180), (560, 270), (650, 200), (760, 280), (860, 190), (900, 240), (900, 300), (0, 300)]
    pygame.draw.polygon(surf, (25, 25, 35), mountain_pts)
    pygame.draw.rect(surf, (40, 32, 22), (0, GROUND_Y, W, H - GROUND_Y))
    pygame.draw.rect(surf, (60, 48, 30), (0, GROUND_Y, W, 6))
    for i in range(0, W, 40): pygame.draw.line(surf, (55, 43, 28), (i, GROUND_Y + 6), (i, H), 1)
    for bx, count in [(60, 3), (820, 3)]:
        for bi in range(count):
            x = bx + bi * 20
            pygame.draw.rect(surf, (30, 80, 30), (x, GROUND_Y - 120, 8, 120))
            for seg in range(0, 120, 22): pygame.draw.line(surf, (20, 60, 20), (x, GROUND_Y - 120 + seg), (x + 8, GROUND_Y - 120 + seg), 2)
            lx = x + 4 + int(math.sin(tick * 0.04 + bi) * 5)
            pygame.draw.line(surf, (40, 110, 40), (lx, GROUND_Y - 125), (lx - 18, GROUND_Y - 135), 3)
            pygame.draw.line(surf, (40, 110, 40), (lx, GROUND_Y - 125), (lx + 18, GROUND_Y - 140), 3)

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angle = random.uniform(0, 2 * math.pi); speed = random.uniform(2, 7)
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed - 2
        self.life = random.randint(15, 35); self.max_life = self.life
        self.color = color; self.r = random.randint(3, 7)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.25; self.life -= 1
    def draw(self, surf):
        alpha = self.life / self.max_life
        c = [int(x * alpha) for x in self.color]
        if self.life > 0: pygame.draw.circle(surf, c, (int(self.x), int(self.y)), self.r)

# ═══════════════════════════════════════════════════════════════════════════════
#  KÄMPFER KLASSE (Mit Block-Stamina)
# ═══════════════════════════════════════════════════════════════════════════════

class Fighter:
    SPEED = 4; JUMP_POWER = -14; GRAVITY = 0.6

    def __init__(self, char_type, x, facing):
        self.char_type = char_type; self.x = float(x); self.y = float(GROUND_Y); self.facing = facing
        self.vx = 0.0; self.vy = 0.0; self.on_ground = True
        if char_type == "samurai":
            self.max_hp, self.attack, self.defense, self.sp_dmg, self.color, self.name = 110, 16, 0.2, 35, BLUE, "SAMURAI"
        else:
            self.max_hp, self.attack, self.defense, self.sp_dmg, self.color, self.name = 100, 17, 0.2, 28, RED, "NINJA"
        self.hp = self.max_hp
        self.block_stamina = 100.0
        self.max_block_stamina = 100.0
        self.anim_tick = 0; self.attacking = False; self.blocking = False; self.special = False; self.hurt = False
        self.attack_timer = 0; self.block_timer = 0; self.special_timer = 0; self.hurt_timer = 0
        self.special_cd = 0; self.attack_cd = 0; self.hit_registered = False

    def move(self, left, right, jump):
        if left: self.vx = -self.SPEED
        elif right: self.vx = self.SPEED
        else: self.vx = 0
        if jump and self.on_ground: self.vy = self.JUMP_POWER; self.on_ground = False
        self.x += self.vx; self.y += self.vy; self.vy += self.GRAVITY
        if self.y >= GROUND_Y: self.y = GROUND_Y; self.vy = 0; self.on_ground = True
        self.x = max(50, min(W - 50, self.x))

    def do_attack(self):
        if self.attack_cd <= 0 and not self.attacking:
            self.attacking = True; self.attack_timer = 25; self.hit_registered = False; self.attack_cd = 35

    def do_block(self):
        if self.block_stamina > 10: 
            self.blocking = True; self.block_timer = 5

    def do_special(self):
        if self.special_cd <= 0 and not self.special:
            self.special = True; self.special_timer = 40; self.hit_registered = False; self.special_cd = 180

    def take_damage(self, dmg, particles, px, py):
        if self.blocking:
            dmg = int(dmg * (1 - self.defense) * 0.4)
        else:
            dmg = int(dmg * (1 - self.defense))
        self.hp = max(0, self.hp - dmg); self.hurt = True; self.hurt_timer = 12
        color = GOLD if self.blocking else RED
        for _ in range(12): particles.append(Particle(px, py, color))

    def update(self, particles):
        self.anim_tick += 1
        if self.attack_timer > 0: self.attack_timer -= 1
        if self.attack_timer == 0: self.attacking = False
        if self.block_timer > 0: self.block_timer -= 1
        if self.block_timer == 0: self.blocking = False
        if self.special_timer > 0: self.special_timer -= 1
        if self.special_timer == 0: self.special = False
        if self.hurt_timer > 0: self.hurt_timer -= 1
        if self.hurt_timer == 0: self.hurt = False
        if self.special_cd > 0: self.special_cd -= 1
        if self.attack_cd > 0: self.attack_cd -= 1

        if self.blocking:
            self.block_stamina -= 0.8 
            if self.block_stamina <= 0:
                self.block_stamina = 0
                self.blocking = False 
        else:
            self.block_stamina = min(self.max_block_stamina, self.block_stamina + 0.4)

    def draw(self, surf):
        if self.char_type == "samurai": draw_samurai(surf, int(self.x), int(self.y), self.color, self.facing, self.anim_tick, self.attacking, self.blocking, self.special, self.hurt)
        else: draw_ninja(surf, int(self.x), int(self.y), self.color, self.facing, self.anim_tick, self.attacking, self.blocking, self.special, self.hurt)

# ═══════════════════════════════════════════════════════════════════════════════
#  VERBESSERTE KI
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleAI:
    def __init__(self, fighter, target):
        self.fighter = fighter; self.target = target
        self.think_timer = 0; self.action = "approach"

    def update(self):
        f = self.fighter; t = self.target
        dist = abs(f.x - t.x)
        self.think_timer -= 1
        if self.think_timer <= 0:
            self.think_timer = random.randint(15, 40)
            roll = random.random()
            if dist < 100:
                if roll < 0.3: self.action = "attack"
                elif roll < 0.5: self.action = "block"
                elif roll < 0.7: self.action = "special"
                else: self.action = "retreat"
            else:
                self.action = "approach" if roll < 0.8 else "idle"

        left = right = jump = False
        atk = blk = spc = False
        if self.action == "approach":
            if f.x < t.x: right = True
            else: left = True
        elif self.action == "retreat":
            if f.x < t.x: left = True
            else: right = True
        elif self.action == "attack":
            if dist < 90: atk = True
            else: (right if f.x < t.x else None) or (left if f.x > t.x else None) 
        elif self.action == "block": blk = True
        elif self.action == "special":
            if dist < 140: spc = True

        if (t.attacking or t.special) and random.random() < 0.1 and f.on_ground:
            jump = True
        elif random.random() < 0.01 and f.on_ground:
            jump = True

        f.facing = 1 if t.x > f.x else -1
        f.move(left, right, jump)
        if atk: f.do_attack()
        if blk: f.do_block()
        if spc: f.do_special()

# ═══════════════════════════════════════════════════════════════════════════════
#  HUD (Mit Stamina-Balken)
# ═══════════════════════════════════════════════════════════════════════════════

def draw_hud(surf, p1, p2, tick):
    for p, x_off, is_right in [(p1, 20, False), (p2, W - 300, True)]:
        name_lbl = font_small.render(p.name, True, p.color)
        surf.blit(name_lbl, (x_off if not is_right else W - x_off - name_lbl.get_width(), 14))
        hp_w = int(280 * p.hp / p.max_hp)
        pygame.draw.rect(surf, DARK_RED, (x_off, 38, 280, 20), border_radius=5)
        if hp_w > 0:
            col = GREEN if p.hp > p.max_hp * 0.5 else (YELLOW if p.hp > p.max_hp * 0.25 else RED)
            pygame.draw.rect(surf, col, (x_off, 38, hp_w, 20), border_radius=5)
        sp_pct = 1.0 - (p.special_cd / 180) if p.special_cd > 0 else 1.0
        pygame.draw.rect(surf, DARK_GR, (x_off, 64, 280, 10), border_radius=3)
        pygame.draw.rect(surf, PURPLE, (x_off, 64, int(280 * sp_pct), 10), border_radius=3)
        st_pct = p.block_stamina / p.max_block_stamina
        pygame.draw.rect(surf, (40, 40, 40), (x_off, 78, 280, 6), border_radius=3)
        pygame.draw.rect(surf, STAMINA_COL, (x_off, 78, int(280 * st_pct), 6), border_radius=3)

    vs = font_big.render("VS", True, GOLD)
    surf.blit(vs, (W // 2 - vs.get_width() // 2, 22))
    ctrl = font_tiny.render("WASD:Bewegung  F:Angriff  G:Block  H:Spezial", True, (120, 120, 140))
    surf.blit(ctrl, (W // 2 - ctrl.get_width() // 2, H - 22))

# ═══════════════════════════════════════════════════════════════════════════════
#  CHARAKTER-AUSWAHL
# ═══════════════════════════════════════════════════════════════════════════════

def char_select_screen():
    chars = ["samurai", "ninja"]; selected = 0; tick = 0
    while True:
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d): selected = 1 - selected
                if event.key in (pygame.K_RETURN, pygame.K_SPACE): return chars[selected]
        draw_background(screen, tick)
        title = font_big.render("⚔  STICKMAN KAMPF  ⚔", True, GOLD)
        screen.blit(title, (W // 2 - title.get_width() // 2, 40))
        card_w, card_h = 240, 280
        positions = [W // 2 - 160 - card_w // 2, W // 2 + 160 - card_w // 2]
        for i, ch in enumerate(chars):
            cx = positions[i] + card_w // 2; is_sel = (i == selected)
            border_col = GOLD if is_sel else GRAY; bob = int(math.sin(tick * 0.05) * 6) if is_sel else 0
            card_rect = pygame.Rect(positions[i], 150 - bob, card_w, card_h)
            pygame.draw.rect(screen, (20, 20, 30), card_rect, border_radius=12)
            pygame.draw.rect(screen, border_col, card_rect, 3, border_radius=12)
            if ch == "samurai": draw_samurai(screen, cx, 300 - bob, BLUE, 1, tick, False, False, False, False)
            else: draw_ninja(screen, cx, 300 - bob, RED, 1, tick, False, False, False, False)
        pygame.display.flip(); clock.tick(60)

# ═══════════════════════════════════════════════════════════════════════════════
#  KAMPF-SCHLEIFE
# ═══════════════════════════════════════════════════════════════════════════════

def fight(player_char):
    ai_char = "ninja" if player_char == "samurai" else "samurai"
    p1 = Fighter(player_char, 200, 1); p2 = Fighter(ai_char, 700, -1)
    ai = SimpleAI(p2, p1)
    particles = []; tick = 0; round_over = False; winner = ""; result_timer = 0

    while True:
        tick += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and round_over: return
        keys = pygame.key.get_pressed()
        if not round_over:
            p1.facing = 1 if p2.x > p1.x else -1
            p1.move(keys[pygame.K_a] or keys[pygame.K_LEFT], keys[pygame.K_d] or keys[pygame.K_RIGHT], keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE])
            if keys[pygame.K_f]: p1.do_attack()
            if keys[pygame.K_g]: p1.do_block()
            if keys[pygame.K_h]: p1.do_special()
            ai.update()

            min_dist = 60; dist_x = p1.x - p2.x
            if abs(dist_x) < min_dist:
                overlap = min_dist - abs(dist_x)
                if dist_x > 0: p1.x += overlap / 2; p2.x -= overlap / 2
                else: p1.x -= overlap / 2; p2.x += overlap / 2

            for attacker, defender in [(p1, p2), (p2, p1)]:
                if (attacker.attacking or attacker.special) and not attacker.hit_registered:
                    reach = 120 if attacker.special else 95
                    if abs(attacker.x - defender.x) < reach and ((attacker.facing == 1 and defender.x > attacker.x) or (attacker.facing == -1 and defender.x < attacker.x)):
                        defender.take_damage(attacker.sp_dmg if attacker.special else attacker.attack, particles, int((attacker.x + defender.x) / 2), int(defender.y - 60))
                        attacker.hit_registered = True
            p1.update(particles); p2.update(particles)
            
            # FIX: Korrekte Einrückung für Partikel-Update
            for pt in particles[:]:
                pt.update()
                if pt.life <= 0:
                    particles.remove(pt)

            if p1.hp <= 0 or p2.hp <= 0: round_over = True; winner = p1.name if p2.hp <= 0 else p2.name

        draw_background(screen, tick)
        for pt in particles: pt.draw(screen)
        p1.draw(screen); p2.draw(screen); draw_hud(screen, p1, p2, tick)
        if round_over:
            overlay = pygame.Surface((W, H), pygame.SRCALPHA); overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (0, 0))
            win_txt = font_big.render(f"{winner} GEWINNT!", True, GOLD)
            screen.blit(win_txt, (W // 2 - win_txt.get_width() // 2, H // 2 - 50))
        pygame.display.flip(); clock.tick(60)

def main():
    while True: fight(char_select_screen())

if __name__ == "__main__":
    main()
