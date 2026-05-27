#!/usr/bin/env python3
"""
2D Minecraft Clone - Vollständiger Klon in einer einzigen Python-Datei
Steuerung:
  WASD / Pfeiltasten - Bewegen & Springen
  Mausrad            - Zoom
  Linke Maustaste    - Block abbauen
  Rechte Maustaste   - Block setzen
  1-9                - Inventarslot wählen
  C                  - Portal-Teile craften
  E                  - Inventar öffnen/schließen
  F                  - Fliegen umschalten
  ESC                - Beenden
"""

import pygame
import sys
import random
import math
import json
import os
from collections import defaultdict

# ─── Konstanten ───────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
TILE   = 32          # Pixelgröße eines Blocks auf Bildschirm
CHUNK  = 16          # Blöcke pro Chunk
GRAVITY     = 0.6
JUMP_FORCE  = -13
PLAYER_SPEED = 4
FLY_SPEED    = 7
WORLD_HEIGHT = 128   # Blöcke hoch
SEA_LEVEL    = 64

FPS = 60

# Biom-Farben & Namen
BIOMES = {
    "plains":  {"color": (144, 238, 144), "base": 64, "amp": 6},
    "hills":   {"color": (100, 180, 100), "base": 60, "amp": 18},
    "desert":  {"color": (255, 213, 128), "base": 62, "amp": 5},
    "ocean":   {"color": (100, 160, 230), "base": 55, "amp": 3},
    "forest":  {"color": (34, 120, 34),   "base": 63, "amp": 8},
    "stonefields": {"color": (90, 90, 100), "base": 58, "amp": 12},
}

# Block-IDs
AIR    = 0
GRASS  = 1
DIRT   = 2
STONE  = 3
SAND   = 4
WATER  = 5
WOOD   = 6
LEAVES = 7
COAL   = 8
IRON   = 9
GOLD   = 10
DIAMOND= 11
BEDROCK= 12
GRAVEL = 13
GLASS  = 14
PLANK  = 15
TORCH  = 16
SNOW   = 17
ICE    = 18
CACTUS = 19
CLAY   = 20
PORTAL_FRAME = 21
PORTAL_ACTIVATOR = 22
PORTAL_ENERGY = 23
MOSSY_STONE = 24

BLOCK_NAMES = {
    AIR:"Luft", GRASS:"Gras", DIRT:"Erde", STONE:"Stein",
    SAND:"Sand", WATER:"Wasser", WOOD:"Holz", LEAVES:"Blätter",
    COAL:"Kohle", IRON:"Eisen", GOLD:"Gold", DIAMOND:"Diamant",
    BEDROCK:"Grundstein", GRAVEL:"Kies", GLASS:"Glas",
    PLANK:"Holzplanke", TORCH:"Fackel", SNOW:"Schnee",
    ICE:"Eis", CACTUS:"Kaktus", CLAY:"Ton",
    PORTAL_FRAME:"Portalrahmen", PORTAL_ACTIVATOR:"Portalaktivator",
    PORTAL_ENERGY:"Portalenergie", MOSSY_STONE:"Moosstein",
}

# Wie viel Schaden jeder Block beim Abbauen aussteht (Ticks bis zerstört)
BLOCK_HARDNESS = {
    AIR:0, GRASS:10, DIRT:8, STONE:20, SAND:8, WATER:0,
    WOOD:15, LEAVES:3, COAL:22, IRON:28, GOLD:25, DIAMOND:35,
    BEDROCK:9999, GRAVEL:8, GLASS:5, PLANK:10, TORCH:1,
    SNOW:4, ICE:6, CACTUS:5, CLAY:10,
    PORTAL_FRAME:35, PORTAL_ACTIVATOR:0, PORTAL_ENERGY:9999, MOSSY_STONE:22,
}

# ─── Farben ───────────────────────────────────────────────────────────────────
BLOCK_COLORS = {
    AIR:    None,
    GRASS:  [(106,176,76),(88,148,62),(120,190,85)],
    DIRT:   [(121,85,58),(101,65,45)],
    STONE:  [(128,128,128),(110,110,110),(145,145,145)],
    SAND:   [(237,201,100),(220,185,90)],
    WATER:  [(64,164,223,160)],
    WOOD:   [(101,67,33),(85,55,25)],
    LEAVES: [(34,139,34,200),(45,160,45,200)],
    COAL:   [(50,50,50),(35,35,35)],
    IRON:   [(140,120,100),(160,140,120)],
    GOLD:   [(255,215,0),(235,195,0)],
    DIAMOND:[(0,200,220),(0,180,200)],
    BEDROCK:[(40,40,40),(30,30,30)],
    GRAVEL: [(150,140,130),(130,125,118)],
    GLASS:  [(200,230,255,100)],
    PLANK:  [(180,140,80),(160,120,65)],
    TORCH:  [(255,180,50)],
    SNOW:   [(240,240,255),(250,250,255)],
    ICE:    [(180,210,255,180)],
    CACTUS: [(60,130,60),(40,110,40)],
    CLAY:   [(160,155,170),(140,136,150)],
    PORTAL_FRAME: [(75,75,90),(35,35,50)],
    PORTAL_ACTIVATOR: [(90,210,255),(40,100,180)],
    PORTAL_ENERGY: [(80,230,255,180),(150,80,255,180)],
    MOSSY_STONE: [(95,120,92),(65,85,68)],
}

# Blöcke die man nicht abbauen kann / Flüssig sind
UNBREAKABLE = {BEDROCK, WATER, PORTAL_ENERGY}
LIQUID      = {WATER}
TRANSPARENT = {AIR, WATER, LEAVES, GLASS, ICE, TORCH, PORTAL_ENERGY}
ITEM_ONLY = {PORTAL_ACTIVATOR}

# ─── Textur-Renderer ──────────────────────────────────────────────────────────
_tex_cache = {}

def make_texture(block_id, size=TILE):
    key = (block_id, size)
    if key in _tex_cache:
        return _tex_cache[key]

    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cols = BLOCK_COLORS.get(block_id)
    if not cols:
        _tex_cache[key] = surf
        return surf

    c1 = cols[0]
    c2 = cols[1] if len(cols) > 1 else cols[0]

    # Farbverlauf (einfach)
    for y in range(size):
        t = y / size
        r = int(c1[0]*(1-t) + c2[0]*t)
        g = int(c1[1]*(1-t) + c2[1]*t)
        b = int(c1[2]*(1-t) + c2[2]*t)
        a = c1[3] if len(c1) > 3 else 255
        pygame.draw.line(surf, (r,g,b,a), (0,y),(size-1,y))

    # Pixel-Noise für Textur-Feeling
    rng = random.Random(block_id * 1337)
    for _ in range(size*size//8):
        px = rng.randint(0, size-1)
        py = rng.randint(0, size-1)
        cc = surf.get_at((px,py))
        delta = rng.randint(-18, 18)
        surf.set_at((px,py), (
            max(0,min(255, cc[0]+delta)),
            max(0,min(255, cc[1]+delta)),
            max(0,min(255, cc[2]+delta)),
            cc[3]
        ))

    # Rand (Highlight oben, Schatten unten)
    hl = (min(255,c1[0]+60), min(255,c1[1]+60), min(255,c1[2]+60))
    sh = (max(0,c2[0]-40),   max(0,c2[1]-40),   max(0,c2[2]-40))
    pygame.draw.line(surf, hl, (0,0),(size-1,0))
    pygame.draw.line(surf, hl, (0,0),(0,size-1))
    pygame.draw.line(surf, sh, (0,size-1),(size-1,size-1))
    pygame.draw.line(surf, sh, (size-1,0),(size-1,size-1))

    # Sonder-Render für bestimmte Blöcke
    if block_id == GRASS:
        pygame.draw.rect(surf, (72,160,50), (0,0,size, size//5))
    elif block_id == TORCH:
        surf.fill((0,0,0,0))
        pygame.draw.rect(surf, (120,80,30), (size//2-2, size//3, 4, size//2))
        pygame.draw.circle(surf,(255,200,50),(size//2, size//3),4)
    elif block_id == CACTUS:
        pygame.draw.rect(surf,(80,150,60),(size//4,0,size//2,size))
        pygame.draw.rect(surf,(60,130,40),(size//4-3,size//3,3,6))
        pygame.draw.rect(surf,(60,130,40),(size//2+1,size//2,3,6))
    elif block_id == WOOD:
        pygame.draw.rect(surf,(70,45,20),(size//3,0,size//3,size))
    elif block_id == PORTAL_FRAME:
        pygame.draw.rect(surf, (25,25,40), (size//5, size//5, size*3//5, size*3//5), 2)
        for i in range(4):
            ox = (i % 2) * (size - size//4)
            oy = (i // 2) * (size - size//4)
            pygame.draw.circle(surf, (90,210,255), (ox + size//8, oy + size//8), max(2, size//14))
    elif block_id == PORTAL_ACTIVATOR:
        surf.fill((0,0,0,0))
        pygame.draw.circle(surf, (35,50,75), (size//2, size//2), size//3)
        pygame.draw.circle(surf, (90,220,255), (size//2, size//2), size//4)
        pygame.draw.circle(surf, (245,255,255), (size//2, size//2), max(2, size//12))
    elif block_id == PORTAL_ENERGY:
        surf.fill((0,0,0,0))
        for x in range(0, size, max(3, size//6)):
            pygame.draw.line(surf, (80,230,255,130), (x, 0), (size-x//2, size), max(1, size//16))
        pygame.draw.rect(surf, (140,80,255,90), (0, 0, size, size))
    elif block_id == MOSSY_STONE:
        pygame.draw.rect(surf, (45,95,50), (0, 0, size, size//5))
        pygame.draw.rect(surf, (55,110,55), (size//5, size//2, size//3, size//5))

    _tex_cache[key] = surf
    return surf


# ─── Welt-Generierung ─────────────────────────────────────────────────────────

def smooth_noise(x, seed=0):
    """Einfaches 1D-Rauschen mit Interpolation."""
    def noise1(n):
        n = (n + seed*57) & 0xFFFFFFFF
        n = ((n >> 13) ^ n)
        n = (n * (n * n * 60493 + 19990303) + 1376312589) & 0x7FFFFFFF
        return n / 0x7FFFFFFF

    xi = int(x)
    xf = x - xi
    xf = xf*xf*(3 - 2*xf)   # smoothstep
    return noise1(xi)*(1-xf) + noise1(xi+1)*xf

def fbm(x, octaves=4, seed=0):
    val = 0.0
    amp = 1.0
    freq = 1.0
    mx = 0.0
    for _ in range(octaves):
        val += smooth_noise(x*freq, seed)*amp
        mx  += amp
        amp  *= 0.5
        freq *= 2.0
    return val / mx


class World:
    def __init__(self, seed=None, dimension="grass"):
        self.seed = seed or random.randint(0, 999999)
        self.dimension = dimension
        self.chunks: dict[int, dict] = {}   # chunk_x -> {(x,y): block_id}
        self.modified = set()

    def get_biome(self, chunk_x):
        if self.dimension == "stone":
            return "stonefields"
        v = fbm(chunk_x * 0.3, octaves=3, seed=self.seed+7)
        if v < 0.25:   return "ocean"
        if v < 0.42:   return "plains"
        if v < 0.58:   return "desert"
        if v < 0.74:   return "forest"
        return "hills"

    def gen_chunk(self, chunk_x):
        if self.dimension == "stone":
            return self.gen_stone_chunk(chunk_x)

        data = {}
        biome = self.get_biome(chunk_x)
        binfo = BIOMES[biome]

        for lx in range(CHUNK):
            wx = chunk_x * CHUNK + lx
            # Geländehöhe
            h = int(binfo["base"] + fbm(wx * 0.05, 5, self.seed) * binfo["amp"])
            h = max(2, min(WORLD_HEIGHT-2, h))

            for ly in range(WORLD_HEIGHT):
                y = ly
                if y >= WORLD_HEIGHT - 1:
                    data[(wx, y)] = BEDROCK
                elif y > h:
                    if y <= SEA_LEVEL and biome == "ocean":
                        data[(wx, y)] = WATER
                    else:
                        data[(wx, y)] = AIR
                elif y == h:
                    if biome == "desert":
                        data[(wx, y)] = SAND
                    elif biome == "ocean":
                        data[(wx, y)] = SAND if h >= SEA_LEVEL-2 else GRAVEL
                    else:
                        data[(wx, y)] = GRASS
                elif y >= h - 4:
                    if biome == "desert":
                        data[(wx, y)] = SAND
                    else:
                        data[(wx, y)] = DIRT
                else:
                    # Stein mit Adern
                    rv = fbm(wx*0.2 + y*0.3, 2, self.seed+13)
                    if rv > 0.82:
                        depth = WORLD_HEIGHT - y
                        if depth > 90 and random.random() < 0.05:
                            data[(wx, y)] = DIAMOND
                        elif depth > 60 and random.random() < 0.08:
                            data[(wx, y)] = GOLD
                        elif depth > 30 and random.random() < 0.12:
                            data[(wx, y)] = IRON
                        elif random.random() < 0.18:
                            data[(wx, y)] = COAL
                        else:
                            data[(wx, y)] = GRAVEL
                    else:
                        data[(wx, y)] = STONE

        # Bäume / Kakteen
        rng = random.Random(self.seed ^ (chunk_x * 2654435761))
        for lx in range(CHUNK):
            wx = chunk_x * CHUNK + lx
            # Finde Oberfläche
            for y in range(WORLD_HEIGHT):
                if data.get((wx, y), AIR) not in (AIR, WATER):
                    surf_y = y - 1
                    break
            else:
                continue

            top_block = data.get((wx, surf_y+1), AIR)

            if biome == "desert" and top_block == SAND and rng.random() < 0.04:
                # Kaktus
                ch = rng.randint(2, 4)
                for i in range(ch):
                    if surf_y - i >= 0:
                        data[(wx, surf_y - i)] = CACTUS

            elif biome in ("forest","plains","hills") and top_block == GRASS and rng.random() < (0.08 if biome=="forest" else 0.04):
                # Baum
                th = rng.randint(4, 7)
                # Stamm
                for i in range(th):
                    if surf_y - i >= 0:
                        data[(wx, surf_y - i)] = WOOD
                # Blätter
                cr = 2
                ty = surf_y - th
                for dy in range(-cr, cr+1):
                    for dx in range(-cr, cr+1):
                        if abs(dx)+abs(dy) <= cr+1:
                            bx = wx+dx
                            by = ty+dy
                            if data.get((bx,by), AIR) == AIR:
                                data[(bx,by)] = LEAVES

        self.chunks[chunk_x] = data
        return data

    def gen_stone_chunk(self, chunk_x):
        data = {}
        rng = random.Random((self.seed + 404) ^ (chunk_x * 1103515245))
        binfo = BIOMES["stonefields"]

        for lx in range(CHUNK):
            wx = chunk_x * CHUNK + lx
            h = int(binfo["base"] + fbm(wx * 0.045, 5, self.seed+99) * binfo["amp"])
            h = max(10, min(WORLD_HEIGHT-3, h))

            for y in range(WORLD_HEIGHT):
                if y >= WORLD_HEIGHT - 1:
                    data[(wx, y)] = BEDROCK
                elif y > h:
                    data[(wx, y)] = AIR
                elif y == h:
                    data[(wx, y)] = MOSSY_STONE if rng.random() < 0.18 else STONE
                elif y >= h - 3:
                    data[(wx, y)] = GRAVEL if rng.random() < 0.25 else STONE
                else:
                    cave = fbm(wx * 0.12 + y * 0.05, 3, self.seed+222)
                    if cave > 0.78 and y < h - 7:
                        data[(wx, y)] = AIR
                    else:
                        ore = fbm(wx*0.23 + y*0.37, 2, self.seed+313)
                        depth = WORLD_HEIGHT - y
                        if ore > 0.86 and depth > 80:
                            data[(wx, y)] = DIAMOND if rng.random() < 0.25 else GOLD
                        elif ore > 0.82 and depth > 45:
                            data[(wx, y)] = IRON
                        elif ore > 0.78:
                            data[(wx, y)] = COAL
                        else:
                            data[(wx, y)] = STONE

        # Basaltartige Säulen und seltene fertige Rahmenreste
        for lx in range(CHUNK):
            wx = chunk_x * CHUNK + lx
            if rng.random() < 0.05:
                for y in range(15, WORLD_HEIGHT-1):
                    if data.get((wx, y), AIR) != AIR:
                        for i in range(rng.randint(3, 8)):
                            data[(wx, y-i)] = MOSSY_STONE
                        break

        self.chunks[chunk_x] = data
        return data

    def get_chunk(self, chunk_x):
        if chunk_x not in self.chunks:
            self.gen_chunk(chunk_x)
        return self.chunks[chunk_x]

    def get_block(self, x, y):
        if y < 0: return AIR
        if y >= WORLD_HEIGHT: return BEDROCK
        cx = x // CHUNK
        chunk = self.get_chunk(cx)
        return chunk.get((x, y), AIR)

    def set_block(self, x, y, block_id):
        if y < 0 or y >= WORLD_HEIGHT: return
        cx = x // CHUNK
        chunk = self.get_chunk(cx)
        chunk[(x, y)] = block_id
        self.modified.add(cx)

    def preload(self, center_cx, radius=6):
        for cx in range(center_cx - radius, center_cx + radius + 1):
            self.get_chunk(cx)


# ─── Spieler ──────────────────────────────────────────────────────────────────

class Player:
    W = 0.8
    H = 1.8

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.flying = False
        self.health = 20
        self.max_health = 20
        self.hunger = 20
        self.max_hunger = 20

        # Inventar: Slot -> (block_id, count)
        self.inventory = {
            1: (DIRT,  64),
            2: (STONE, 64),
            3: (WOOD,  64),
            4: (PLANK, 64),
            5: (GLASS, 64),
            6: (TORCH, 64),
            7: (SAND,  64),
            8: (GRAVEL,64),
            9: (LEAVES,64),
        }
        self.selected_slot = 1

    def selected_block(self):
        return self.inventory.get(self.selected_slot, (AIR, 0))[0]

    def add_item(self, block_id, count=1):
        # Fügt Block dem ersten freien Slot hinzu
        for slot in range(1, 37):
            if slot in self.inventory:
                if self.inventory[slot][0] == block_id:
                    bid, cnt = self.inventory[slot]
                    self.inventory[slot] = (bid, min(64, cnt+count))
                    return
            else:
                self.inventory[slot] = (block_id, count)
                return

    def count_item(self, block_id):
        total = 0
        for bid, cnt in self.inventory.values():
            if bid == block_id:
                total += cnt
        return total

    def consume_item(self, block_id, count=1):
        if self.count_item(block_id) < count:
            return False
        remaining = count
        for slot in sorted(list(self.inventory.keys())):
            bid, cnt = self.inventory[slot]
            if bid != block_id:
                continue
            take = min(cnt, remaining)
            cnt -= take
            remaining -= take
            if cnt <= 0:
                del self.inventory[slot]
            else:
                self.inventory[slot] = (bid, cnt)
            if remaining <= 0:
                return True
        return True

    def remove_selected(self, count=1):
        s = self.selected_slot
        if s in self.inventory:
            bid, cnt = self.inventory[s]
            cnt -= count
            if cnt <= 0:
                del self.inventory[s]
            else:
                self.inventory[s] = (bid, cnt)

    def rect_px(self, tile_size):
        """Gibt pygame.Rect in Pixel-Koordinaten zurück (Weltkoordinaten→Pixel)."""
        return pygame.Rect(
            self.x * tile_size,
            self.y * tile_size,
            self.W * tile_size,
            self.H * tile_size,
        )

    def update(self, world, dt):
        if self.flying:
            # Keine Physik
            self.on_ground = False
            return

        self.vy += GRAVITY
        self.vy = min(self.vy, 20)

        # Horizontale Bewegung
        new_x = self.x + self.vx
        if not self._collides(world, new_x, self.y):
            self.x = new_x
        else:
            self.vx = 0

        # Vertikale Bewegung
        new_y = self.y + self.vy
        if not self._collides(world, self.x, new_y):
            self.y = new_y
            self.on_ground = False
        else:
            if self.vy > 0:
                self.on_ground = True
            self.vy = 0

        # Reibung
        self.vx *= 0.8

    def _collides(self, world, px, py):
        """AABB-Kollision mit Welt-Blöcken."""
        x0 = int(math.floor(px))
        x1 = int(math.floor(px + self.W - 0.01))
        y0 = int(math.floor(py))
        y1 = int(math.floor(py + self.H - 0.01))
        for bx in range(x0, x1+1):
            for by in range(y0, y1+1):
                b = world.get_block(bx, by)
                if b not in TRANSPARENT and b != AIR:
                    return True
        return False

    def jump(self):
        if self.on_ground and not self.flying:
            self.vy = JUMP_FORCE
            self.on_ground = False


# ─── Kamera ───────────────────────────────────────────────────────────────────

class Camera:
    def __init__(self, screen_w, screen_h):
        self.sw = screen_w
        self.sh = screen_h
        self.x  = 0.0  # Weltkoordinate (Blöcke) der Kamera-Mitte
        self.y  = 0.0
        self.tile = TILE
        self.min_tile = 12
        self.max_tile = 64

    def follow(self, player):
        self.x = player.x + player.W / 2
        self.y = player.y + player.H / 2

    def world_to_screen(self, wx, wy):
        sx = (wx - self.x) * self.tile + self.sw // 2
        sy = (wy - self.y) * self.tile + self.sh // 2
        return int(sx), int(sy)

    def screen_to_world(self, sx, sy):
        wx = (sx - self.sw // 2) / self.tile + self.x
        wy = (sy - self.sh // 2) / self.tile + self.y
        return wx, wy

    def zoom(self, delta):
        self.tile = max(self.min_tile, min(self.max_tile, self.tile + delta))
        _tex_cache.clear()

    def visible_range(self):
        half_w = self.sw / 2 / self.tile
        half_h = self.sh / 2 / self.tile
        x0 = int(math.floor(self.x - half_w)) - 1
        x1 = int(math.ceil (self.x + half_w)) + 1
        y0 = int(math.floor(self.y - half_h)) - 1
        y1 = int(math.ceil (self.y + half_h)) + 1
        return x0, x1, y0, y1


# ─── Partikel ─────────────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -1)
        self.color = color
        self.life = random.randint(20, 40)
        self.max_life = self.life

    def update(self):
        self.vy += 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam):
        alpha = int(255 * self.life / self.max_life)
        size = max(1, int(3 * self.life / self.max_life))
        sx, sy = cam.world_to_screen(self.x / cam.tile, self.y / cam.tile)
        # Verwende Pixel-Koordinaten direkt
        sx = int((self.x - cam.x * cam.tile) + cam.sw // 2)
        sy = int((self.y - cam.y * cam.tile) + cam.sh // 2)
        c = (*self.color[:3], alpha)
        ps = pygame.Surface((size*2,size*2), pygame.SRCALPHA)
        ps.fill(c)
        surf.blit(ps, (sx-size, sy-size))


# ─── HUD ──────────────────────────────────────────────────────────────────────

def draw_hud(surf, player, font, small_font, show_inventory):
    sw, sh = surf.get_size()

    # ── Hotbar ──────────────────────────────────────────
    slots = 9
    slot_size = 52
    total_w = slots * slot_size + (slots-1)*4
    hx = (sw - total_w) // 2
    hy = sh - slot_size - 10

    bar_surf = pygame.Surface((total_w + 8, slot_size + 8), pygame.SRCALPHA)
    bar_surf.fill((0,0,0,120))
    surf.blit(bar_surf, (hx-4, hy-4))

    for i in range(1, slots+1):
        sx = hx + (i-1)*(slot_size+4)
        selected = (i == player.selected_slot)
        col = (255,255,255,200) if selected else (180,180,180,160)
        border_surf = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
        border_surf.fill((0,0,0,80))
        surf.blit(border_surf, (sx, hy))
        pygame.draw.rect(surf, col, (sx, hy, slot_size, slot_size), 2 if not selected else 3)

        if i in player.inventory:
            bid, cnt = player.inventory[i]
            tex = make_texture(bid, slot_size-8)
            surf.blit(tex, (sx+4, hy+4))
            cnt_surf = small_font.render(str(cnt), True, (255,255,255))
            surf.blit(cnt_surf, (sx + slot_size - cnt_surf.get_width() - 3,
                                  hy + slot_size - cnt_surf.get_height() - 2))
        # Slot-Nummer
        num = small_font.render(str(i), True, (200,200,200))
        surf.blit(num, (sx+3, hy+3))

    # Gewählter Block Name
    sel_bid = player.selected_block()
    name = BLOCK_NAMES.get(sel_bid, "Unbekannt")
    ns = font.render(name, True, (255,255,255))
    surf.blit(ns, ((sw - ns.get_width())//2, hy - 28))

    # ── Leben & Hunger ───────────────────────────────────
    heart_x = hx
    heart_y = hy - 56
    for i in range(player.max_health // 2):
        filled = player.health >= (i+1)*2
        half   = player.health == i*2+1
        col = (220,30,30) if filled else ((220,30,30) if half else (80,80,80))
        pygame.draw.circle(surf, col, (heart_x + i*22 + 8, heart_y+8), 7)
        pygame.draw.circle(surf, col, (heart_x + i*22 + 15, heart_y+8), 7)
        pygame.draw.polygon(surf, col, [
            (heart_x + i*22, heart_y+10),
            (heart_x + i*22 + 12, heart_y+22),
            (heart_x + i*22 + 22, heart_y+10)
        ])
        if not filled:
            pygame.draw.circle(surf, (200,200,200,100), (heart_x + i*22 + 8, heart_y+8), 6, 2)

    # Hunger
    for i in range(player.max_hunger // 2):
        col = (180,100,20) if player.hunger >= (i+1)*2 else (80,80,80)
        fx = sw - hx - (i+1)*22
        pygame.draw.polygon(surf, col, [
            (fx+5,  heart_y),
            (fx+11, heart_y),
            (fx+17, heart_y+8),
            (fx+11, heart_y+16),
            (fx+5,  heart_y+16),
            (fx-1,  heart_y+8),
        ])

    # ── Inventar ────────────────────────────────────────
    if show_inventory:
        inv_w, inv_h = 9*56+20, 4*56+60
        inv_x = (sw-inv_w)//2
        inv_y = (sh-inv_h)//2 - 40

        inv_bg = pygame.Surface((inv_w, inv_h), pygame.SRCALPHA)
        inv_bg.fill((30,30,30,210))
        surf.blit(inv_bg, (inv_x, inv_y))
        pygame.draw.rect(surf,(200,200,200),(inv_x,inv_y,inv_w,inv_h),2)

        title = font.render("Inventar", True, (255,255,255))
        surf.blit(title, (inv_x+10, inv_y+10))

        for slot_i, (bid, cnt) in sorted(player.inventory.items()):
            col_i = (slot_i-1) % 9
            row_i = (slot_i-1) // 9
            bx = inv_x + 10 + col_i*56
            by = inv_y + 40 + row_i*56
            pygame.draw.rect(surf,(100,100,100),(bx,by,52,52))
            pygame.draw.rect(surf,(200,200,200),(bx,by,52,52),1)
            tex = make_texture(bid, 44)
            surf.blit(tex,(bx+4,by+4))
            cs = small_font.render(str(cnt),True,(255,255,255))
            surf.blit(cs,(bx+52-cs.get_width()-2,by+52-cs.get_height()-2))

    # ── Fly-Indikator ────────────────────────────────────
    if player.flying:
        fly_s = small_font.render("Flugmodus", True, (100,200,255))
        surf.blit(fly_s, (10, 10))


def draw_message(surf, font, text, color=(255,255,255)):
    if not text:
        return
    sw, sh = surf.get_size()
    msg = font.render(text, True, color)
    bg = pygame.Surface((msg.get_width()+24, msg.get_height()+16), pygame.SRCALPHA)
    bg.fill((0,0,0,150))
    x = (sw - bg.get_width()) // 2
    y = 82
    surf.blit(bg, (x, y))
    surf.blit(msg, (x+12, y+8))


def try_craft_portal_part(player):
    """Craftet erst Rahmen, danach den Aktivator. Gibt eine HUD-Meldung zurück."""
    if player.count_item(PORTAL_FRAME) < 14:
        if player.count_item(STONE) >= 12 and player.count_item(GLASS) >= 4:
            player.consume_item(STONE, 12)
            player.consume_item(GLASS, 4)
            player.add_item(PORTAL_FRAME, 4)
            return "4 Portalrahmen gecraftet"
        return "Portalrahmen brauchen 12 Stein + 4 Glas"

    if player.count_item(PORTAL_ACTIVATOR) < 1:
        if (player.count_item(STONE) >= 8 and player.count_item(GLASS) >= 6
                and player.count_item(TORCH) >= 1):
            player.consume_item(STONE, 8)
            player.consume_item(GLASS, 6)
            player.consume_item(TORCH, 1)
            player.add_item(PORTAL_ACTIVATOR, 1)
            return "Portalaktivator gecraftet"
        return "Aktivator braucht 8 Stein + 6 Glas + 1 Fackel"

    return "Du hast genug Portalteile"


def find_portal_origin(world, bx, by):
    """Sucht einen 4x5-Rahmen um den angeklickten Block."""
    for ox in range(bx - 3, bx + 1):
        for oy in range(by - 4, by + 1):
            ok = True
            for dx in range(4):
                for dy in range(5):
                    block = world.get_block(ox+dx, oy+dy)
                    edge = dx in (0, 3) or dy in (0, 4)
                    if edge and block != PORTAL_FRAME:
                        ok = False
                    if not edge and block not in (AIR, PORTAL_ENERGY):
                        ok = False
            if ok:
                return ox, oy
    return None


def activate_portal(world, bx, by):
    origin = find_portal_origin(world, bx, by)
    if not origin:
        return False
    ox, oy = origin
    for dx in range(1, 3):
        for dy in range(1, 4):
            world.set_block(ox+dx, oy+dy, PORTAL_ENERGY)
    return True


def create_portal_at(world, ox, oy):
    for dx in range(4):
        for dy in range(5):
            edge = dx in (0, 3) or dy in (0, 4)
            world.set_block(ox+dx, oy+dy, PORTAL_FRAME if edge else PORTAL_ENERGY)


def standing_in_portal(world, player):
    x0 = int(math.floor(player.x))
    x1 = int(math.floor(player.x + player.W))
    y0 = int(math.floor(player.y))
    y1 = int(math.floor(player.y + player.H))
    for bx in range(x0, x1+1):
        for by in range(y0, y1+1):
            if world.get_block(bx, by) == PORTAL_ENERGY:
                return True
    return False


# ─── Skybox & Hintergrund ─────────────────────────────────────────────────────

def draw_sky(surf, camera, dimension="grass"):
    """Einfacher Himmel-Farbverlauf je nach Y-Position der Kamera."""
    t = max(0.0, min(1.0, (camera.y - 20) / 60.0))
    if dimension == "stone":
        sky_top  = (22, 22, 28)
        sky_bot  = (82, 84, 96)
    else:
        sky_top  = (25,  25,  80)
        sky_bot  = (120, 180, 255)
    cave_col = (8,   8,   20)
    sw, sh = surf.get_size()

    if camera.y > 80:
        surf.fill(cave_col)
        return

    for y in range(sh):
        pct = y / sh
        r = int(sky_top[0]*(1-pct) + sky_bot[0]*pct)
        g = int(sky_top[1]*(1-pct) + sky_bot[1]*pct)
        b = int(sky_top[2]*(1-pct) + sky_bot[2]*pct)
        r = int(r*(1-t) + cave_col[0]*t)
        g = int(g*(1-t) + cave_col[1]*t)
        b = int(b*(1-t) + cave_col[2]*t)
        pygame.draw.line(surf,(r,g,b),(0,y),(sw-1,y))

    if dimension == "stone":
        for i in range(18):
            rx = (i * 173) % sw
            ry = 25 + (i * 47) % max(1, sh//2)
            pygame.draw.circle(surf, (120,130,160), (rx, ry), 1 + i % 3)
    else:
        # Sonne / Mond
        sun_wx = 200.0
        sun_wy = 15.0
        sx, sy = camera.world_to_screen(sun_wx, sun_wy)
        pygame.draw.circle(surf,(255,240,100),(sx,sy),28)
        pygame.draw.circle(surf,(255,250,180),(sx,sy),22)


# ─── Haupt-Spielschleife ──────────────────────────────────────────────────────

def spawn_player(world):
    """Findet eine gute Spawn-Position."""
    x = 8
    for y in range(WORLD_HEIGHT):
        b = world.get_block(x, y)
        if b not in (AIR, WATER) and world.get_block(x, y-1) == AIR:
            return float(x), float(y-2)
    return float(x), 60.0


def main():
    pygame.init()
    pygame.display.set_caption("2D Minecraft Clone")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    clock  = pygame.time.Clock()

    font       = pygame.font.SysFont("monospace", 18, bold=True)
    small_font = pygame.font.SysFont("monospace", 13)
    big_font   = pygame.font.SysFont("monospace", 48, bold=True)

    # ── Titelbildschirm ──
    showing_menu = True
    menu_seed_input = ""
    menu_input_active = False

    while showing_menu:
        sw, sh = screen.get_size()
        screen.fill((20, 30, 50))

        # Minecraft-artiger Titel
        t1 = big_font.render("2D MINECRAFT", True, (255, 220, 50))
        t2 = font.render("CLONE", True, (200, 170, 30))
        screen.blit(t1, ((sw-t1.get_width())//2, sh//4))
        screen.blit(t2, ((sw-t2.get_width())//2, sh//4+60))

        play_rect = pygame.Rect((sw-200)//2, sh//2, 200, 50)
        seed_rect  = pygame.Rect((sw-300)//2, sh//2+80, 300, 40)

        # Spiel starten Button
        pygame.draw.rect(screen, (60,160,60), play_rect, border_radius=8)
        pygame.draw.rect(screen, (100,220,100), play_rect, 2, border_radius=8)
        pb = font.render("SPIEL STARTEN", True, (255,255,255))
        screen.blit(pb, (play_rect.x+(play_rect.w-pb.get_width())//2,
                          play_rect.y+(play_rect.h-pb.get_height())//2))

        # Seed-Eingabe
        pygame.draw.rect(screen, (40,40,60) if not menu_input_active else (60,60,90), seed_rect, border_radius=6)
        pygame.draw.rect(screen, (120,120,160), seed_rect, 2, border_radius=6)
        seed_display = menu_seed_input if menu_seed_input else "Seed (leer = zufällig)"
        sd = small_font.render(seed_display, True, (200,200,255))
        screen.blit(sd, (seed_rect.x+8, seed_rect.y+(seed_rect.h-sd.get_height())//2))
        sl = small_font.render("Seed:", True, (180,180,220))
        screen.blit(sl, (seed_rect.x, seed_rect.y-22))

        controls = [
            "WASD / Pfeiltasten - Bewegen & Springen",
            "Linke Maus - Block abbauen",
            "Rechte Maus - Block setzen",
            "1-9 - Inventarslot wählen",
            "C - Portal craften   E - Inventar   F - Fliegen   ESC - Beenden",
        ]
        for i, line in enumerate(controls):
            cs = small_font.render(line, True, (150,180,220))
            screen.blit(cs, ((sw-cs.get_width())//2, sh*3//4 + i*22))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_RETURN:
                    showing_menu = False
                if menu_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        menu_seed_input = menu_seed_input[:-1]
                    elif event.unicode.isdigit() and len(menu_seed_input) < 10:
                        menu_seed_input += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    showing_menu = False
                if seed_rect.collidepoint(event.pos):
                    menu_input_active = True
                else:
                    menu_input_active = False

        clock.tick(60)

    # ── Welt initialisieren ──
    seed = int(menu_seed_input) if menu_seed_input else None
    grass_world = World(seed, "grass")
    stone_world = World(grass_world.seed + 424242, "stone")
    worlds = {"grass": grass_world, "stone": stone_world}
    dimension_names = {"grass": "Graswelt", "stone": "Steinwelt"}
    current_dimension = "grass"
    world = worlds[current_dimension]
    world.preload(0, 5)

    px, py = spawn_player(world)
    player = Player(px, py)
    camera = Camera(SCREEN_W, SCREEN_H)
    camera.follow(player)

    particles = []
    show_inventory = False
    breaking_block = None   # (bx, by, progress)
    keys_held = set()
    message = "Ziel: 14 Portalrahmen + Aktivator craften, 4x5-Portal bauen"
    message_timer = 240
    portal_cooldown = 0
    saved_positions = {}

    # Preload in Kamera-Nähe
    def preload_nearby():
        cx = int(player.x // CHUNK)
        world.preload(cx, 6)

    preload_nearby()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        sw, sh = screen.get_size()
        camera.sw = sw
        camera.sh = sh

        mx, my = pygame.mouse.get_pos()
        mouse_buttons = pygame.mouse.get_pressed()

        # Maus → Welt-Block
        wm_x, wm_y = camera.screen_to_world(mx, my)
        target_bx = int(math.floor(wm_x))
        target_by = int(math.floor(wm_y))
        in_range = abs(wm_x - (player.x+player.W/2)) < 6 and \
                   abs(wm_y - (player.y+player.H/2)) < 6

        # ── Events ───────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                keys_held.add(event.key)
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                    player.jump()
                if event.key == pygame.K_f:
                    player.flying = not player.flying
                    player.vy = 0
                if event.key == pygame.K_e:
                    show_inventory = not show_inventory
                if event.key == pygame.K_c:
                    message = try_craft_portal_part(player)
                    message_timer = 180
                for i, k in enumerate([pygame.K_1,pygame.K_2,pygame.K_3,
                                        pygame.K_4,pygame.K_5,pygame.K_6,
                                        pygame.K_7,pygame.K_8,pygame.K_9]):
                    if event.key == k:
                        player.selected_slot = i+1

            if event.type == pygame.KEYUP:
                keys_held.discard(event.key)

            if event.type == pygame.MOUSEWHEEL:
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    camera.zoom(event.y * 3)
                else:
                    player.selected_slot = (player.selected_slot - 1 - event.y) % 9 + 1

            # Rechtsklick: Block setzen
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if in_range and not show_inventory:
                    bid = player.selected_block()
                    if bid == PORTAL_ACTIVATOR:
                        if activate_portal(world, target_bx, target_by):
                            message = "Portal aktiviert! Spring hinein."
                            message_timer = 180
                        else:
                            message = "Baue einen 4x5-Rahmen aus Portalrahmen."
                            message_timer = 180
                    elif bid != AIR and bid not in ITEM_ONLY and world.get_block(target_bx, target_by) == AIR:
                        # Kein Block auf Spieler setzen
                        player_blocks_x = range(int(math.floor(player.x)), int(math.floor(player.x + player.W)) + 1)
                        player_blocks_y = range(int(math.floor(player.y)), int(math.floor(player.y + player.H)) + 1)
                        if not (target_bx in player_blocks_x and target_by in player_blocks_y):
                            world.set_block(target_bx, target_by, bid)
                            player.remove_selected()
                            # Partikel
                            for _ in range(5):
                                col = BLOCK_COLORS.get(bid, [(128,128,128)])[0]
                                particles.append(Particle(
                                    (target_bx+0.5)*camera.tile,
                                    (target_by+0.5)*camera.tile,
                                    col
                                ))

        # ── Spieler-Bewegung ─────────────────────────────
        move_left  = (pygame.K_a in keys_held or pygame.K_LEFT  in keys_held)
        move_right = (pygame.K_d in keys_held or pygame.K_RIGHT in keys_held)
        move_up    = (pygame.K_w in keys_held or pygame.K_UP    in keys_held or
                      pygame.K_SPACE in keys_held)
        move_down  = (pygame.K_s in keys_held or pygame.K_DOWN  in keys_held)

        speed = FLY_SPEED if player.flying else PLAYER_SPEED

        if player.flying:
            if move_left:  player.x -= speed * dt * FPS / 30
            if move_right: player.x += speed * dt * FPS / 30
            if move_up:    player.y -= speed * dt * FPS / 30
            if move_down:  player.y += speed * dt * FPS / 30
            player.vx = 0
            player.vy = 0
        else:
            if move_left:  player.vx = -speed
            if move_right: player.vx =  speed
            if move_up:    player.jump()

        player.update(world, dt)
        camera.follow(player)

        if portal_cooldown > 0:
            portal_cooldown -= 1

        if portal_cooldown <= 0 and standing_in_portal(world, player):
            saved_positions[current_dimension] = (player.x, player.y)
            current_dimension = "stone" if current_dimension == "grass" else "grass"
            world = worlds[current_dimension]
            world.preload(int(player.x // CHUNK), 5)
            if current_dimension in saved_positions:
                player.x, player.y = saved_positions[current_dimension]
            else:
                player.x, player.y = spawn_player(world)
                create_portal_at(world, int(player.x)-1, int(player.y)-1)
            player.vx = 0
            player.vy = 0
            camera.follow(player)
            portal_cooldown = 120
            message = f"Willkommen in der {dimension_names[current_dimension]}"
            message_timer = 180

        # Spieler nicht unter Bedrock fallen lassen
        if player.y > WORLD_HEIGHT - 3:
            player.y = float(WORLD_HEIGHT - 3)
            player.vy = 0

        # ── Block abbauen (Linksklick gehalten) ──────────
        if mouse_buttons[0] and in_range and not show_inventory:
            b = world.get_block(target_bx, target_by)
            if b not in UNBREAKABLE and b != AIR:
                if (breaking_block is None or
                        breaking_block[0] != target_bx or
                        breaking_block[1] != target_by):
                    breaking_block = [target_bx, target_by, 0]
                else:
                    breaking_block[2] += 1
                    hardness = BLOCK_HARDNESS.get(b, 10)
                    if breaking_block[2] >= hardness:
                        world.set_block(target_bx, target_by, AIR)
                        player.add_item(b)
                        col = BLOCK_COLORS.get(b,[(128,128,128)])[0]
                        for _ in range(12):
                            particles.append(Particle(
                                (target_bx+0.5)*camera.tile,
                                (target_by+0.5)*camera.tile,
                                col
                            ))
                        breaking_block = None
        else:
            breaking_block = None

        # ── Chunks nachladen ─────────────────────────────
        cx = int(player.x // CHUNK)
        world.preload(cx, 5)

        # ── Partikel updaten ─────────────────────────────
        particles = [p for p in particles if p.update()]

        # ── Zeichnen ─────────────────────────────────────
        draw_sky(screen, camera, current_dimension)

        # Sichtbarer Bereich
        x0, x1, y0, y1 = camera.visible_range()
        y0 = max(0, y0)
        y1 = min(WORLD_HEIGHT-1, y1)

        # Blöcke rendern
        ts = camera.tile
        for bx in range(x0, x1+1):
            for by in range(y0, y1+1):
                bid = world.get_block(bx, by)
                if bid == AIR:
                    continue
                sx, sy = camera.world_to_screen(bx, by)
                if sx > sw+ts or sx < -ts or sy > sh+ts or sy < -ts:
                    continue
                tex = make_texture(bid, ts)
                screen.blit(tex, (sx, sy))

                # Schatten (unter Blöcken)
                if world.get_block(bx, by-1) != AIR:
                    shadow = pygame.Surface((ts, 6), pygame.SRCALPHA)
                    shadow.fill((0,0,0,80))
                    screen.blit(shadow, (sx, sy))

        # Breaking-Animation
        if breaking_block:
            bx, by, prog = breaking_block
            b = world.get_block(bx, by)
            hardness = BLOCK_HARDNESS.get(b, 10)
            pct = prog / hardness
            sx, sy = camera.world_to_screen(bx, by)
            crack = pygame.Surface((ts, ts), pygame.SRCALPHA)
            crack.fill((0,0,0, int(180*pct)))
            # Riss-Linien
            for i in range(int(pct*5)+1):
                cx_ = ts//4 + i*ts//8
                cy_ = ts//4 + i*ts//8
                pygame.draw.line(crack,(255,255,255,100),(cx_,0),(0,cy_),2)
            screen.blit(crack,(sx,sy))
            pygame.draw.rect(screen,(255,255,255),(sx,sy,ts,ts),2)

        # Partikel
        for p in particles:
            p.draw(screen, camera)

        # Spieler
        p_sx, p_sy = camera.world_to_screen(player.x, player.y)
        p_pw = int(player.W * ts)
        p_ph = int(player.H * ts)

        # Körper
        pygame.draw.rect(screen,(210,160,100),(p_sx, p_sy+p_ph//3, p_pw, p_ph*2//3))
        # Kopf
        pygame.draw.rect(screen,(240,190,130),(p_sx, p_sy, p_pw, p_ph//3))
        # Augen
        eye_y = p_sy + p_ph//6
        pygame.draw.rect(screen,(50,50,50),(p_sx+2, eye_y, 3, 4))
        pygame.draw.rect(screen,(50,50,50),(p_sx+p_pw-5, eye_y, 3, 4))
        # Shirt
        pygame.draw.rect(screen,(70,130,220),(p_sx, p_sy+p_ph//3, p_pw, p_ph*2//5))

        # Cursor / Ziel-Block
        if in_range:
            tsx, tsy = camera.world_to_screen(target_bx, target_by)
            pygame.draw.rect(screen,(255,255,255),(tsx,tsy,ts,ts),2)

        # HUD
        draw_hud(screen, player, font, small_font, show_inventory)
        if message_timer > 0:
            draw_message(screen, font, message)
            message_timer -= 1

        # Debug-Info
        debug_lines = [
            f"X:{player.x:.1f} Y:{player.y:.1f}",
            f"Welt:{dimension_names[current_dimension]}  Chunk:{int(player.x//CHUNK)}  Seed:{world.seed}",
            f"Biom:{world.get_biome(int(player.x//CHUNK))}",
            f"Portal: Rahmen {player.count_item(PORTAL_FRAME)}/14  Aktivator {player.count_item(PORTAL_ACTIVATOR)}/1",
            f"Zoom:{ts}px  FPS:{clock.get_fps():.0f}",
            f"[C=Craft | Strg+Scroll=Zoom | F=Fliegen | E=Inv]",
        ]
        for i, line in enumerate(debug_lines):
            ds = small_font.render(line, True, (200,230,255))
            ds_bg = pygame.Surface((ds.get_width()+6, ds.get_height()+2), pygame.SRCALPHA)
            ds_bg.fill((0,0,0,100))
            screen.blit(ds_bg, (8, 30 + i*18))
            screen.blit(ds, (11, 31 + i*18))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
