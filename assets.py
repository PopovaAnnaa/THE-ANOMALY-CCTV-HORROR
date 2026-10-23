import pygame
import array
from settings import *

class AssetManager:
    def __init__(self):
        self.font_main = pygame.font.SysFont("Courier", 20, bold=True)
        self.font_large = pygame.font.SysFont("Courier", 28, bold=True)
        
        # Генерація процедурних звуків (щоб гра працювала навіть без зовнішніх .wav)
        self.sound_click = self._generate_beep(FREQ=440, DURATION_MS=50)
        self.sound_catch = self._generate_beep(FREQ=880, DURATION_MS=120)
        self.sound_error = self._generate_beep(FREQ=150, DURATION_MS=200)

    def _generate_beep(self, FREQ=440, DURATION_MS=100):
        """Процедурна генерація простих звуків через Pygame Sound."""
        SAMPLE_RATE = 22050
        NUM_SAMPLES = int(SAMPLE_RATE * (DURATION_MS / 1000.0))
        BUF = array.array('h', [0] * NUM_SAMPLES)
        for i in range(NUM_SAMPLES):
            t = i / SAMPLE_RATE
            # Проста синусоїда
            import math
            value = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * FREQ * t))
            BUF[i] = value
        return pygame.mixer.Sound(BUF)

    def draw_vhs_overlay(self, surface):
        """Ефект CRT/VHS монітора спостереження."""
        for y in range(0, SCREEN_HEIGHT, 4):
            pygame.draw.line(surface, (0, 20, 0), (0, y), (SCREEN_WIDTH, y))