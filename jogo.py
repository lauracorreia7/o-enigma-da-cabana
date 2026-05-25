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
