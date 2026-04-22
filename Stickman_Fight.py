import pygame
import sys
import math
import random

pygame.init()

# Fenster
W, H = 900, 550
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Samurai vs Ninja - Stickman Kampf")
clock = pygame.time.Clock()

# Farben
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

# Fonts
