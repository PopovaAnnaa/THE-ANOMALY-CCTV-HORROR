import array
import math
import random
import pygame
from settings import *

MONO_FONTS = "menlo,couriernew,courier,dejavusansmono,monospace"
SAMPLE_RATE = 22050


class _SilentSound:
    def play(self, *args, **kwargs):
        return None

    def stop(self):
        pass

    def set_volume(self, v):
        pass


class AssetManager:
    def __init__(self):
        self.font_small = pygame.font.SysFont(MONO_FONTS, 14, bold=True)
        self.font_main = pygame.font.SysFont(MONO_FONTS, 18, bold=True)
        self.font_large = pygame.font.SysFont(MONO_FONTS, 30, bold=True)
        self.font_title = pygame.font.SysFont(MONO_FONTS, 64, bold=True)

        self.audio = pygame.mixer.get_init() is not None
        self.sound_click = self._make(self._click)
        self.sound_switch = self._make(lambda: self._noise(160, 0.5, smooth=0.3, decay=5), VOLUME_SWITCH)
        self.sound_static = self._make(lambda: self._noise(1000, 0.35, smooth=0.3, decay=0), VOLUME_STATIC)
        self.sound_catch = self._make(self._confirm, 0.45)
        self.sound_error = self._make(self._buzz, 0.45)
        self.sound_glitch = self._make(self._glitch, 0.5)
        self.sound_tick = self._make(lambda: self._noise(6, 0.5, smooth=0.2, decay=8), 0.12)
        self.sound_message = self._make(self._chime, 0.3)
        self.sound_scare = self._make(self._scare, 0.9)
        self.sound_hum = self._make(self._hum, 0.0)
        self._static_channel = None
        self._hum_channel = None


    def _make(self, generator, volume=1.0):
        if not self.audio:
            return _SilentSound()
        samples = generator()
        buf = array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in samples))
        snd = pygame.mixer.Sound(buffer=buf)
        snd.set_volume(volume)
        return snd

    @staticmethod
    def _env(i, n, attack=0.004, decay=3.0):
        t = i / SAMPLE_RATE
        a = min(1.0, t / attack) if attack > 0 else 1.0
        tail = min(1.0, (n - i) / (SAMPLE_RATE * 0.01))
        return a * tail * (math.exp(-decay * i / n) if decay else 1.0)

    def _noise(self, ms, vol, smooth=0.5, decay=3.0):
        n = int(SAMPLE_RATE * ms / 1000)
        out, y = [], 0.0
        for i in range(n):
            y += smooth * (random.uniform(-1, 1) - y)
            out.append(y * vol * 1.8 * self._env(i, n, decay=decay))
        return out

    def _click(self):
        n = int(SAMPLE_RATE * 0.03)
        return [(random.uniform(-1, 1) * 0.5 + (0.4 if (i // 18) % 2 else -0.4)) * 0.4 * self._env(i, n, decay=9)
                for i in range(n)]

    def _confirm(self):
        out = []
        for freq, ms in ((660, 70), (990, 110)):
            n = int(SAMPLE_RATE * ms / 1000)
            out += [0.3 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * self._env(i, n, decay=2.5)
                    for i in range(n)]
        return out

    def _buzz(self):
        n = int(SAMPLE_RATE * 0.38)
        out = []
        for i in range(n):
            t = i / SAMPLE_RATE
            sq = 1.0 if math.sin(2 * math.pi * 110 * t) > 0 else -1.0
            trem = 0.6 + 0.4 * math.sin(2 * math.pi * 18 * t)
            out.append(sq * 0.22 * trem * self._env(i, n, decay=1.5))
        return out

    def _glitch(self):
        n = int(SAMPLE_RATE * 0.32)
        out, hold, v = [], 0, 0.0
        for i in range(n):
            if hold <= 0:
                v = random.uniform(-1, 1)
                hold = random.choice((3, 6, 12, 24, 48))
            hold -= 1
            out.append(v * 0.4 * self._env(i, n, decay=2.0))
        return out

    def _scare(self):
        n = int(SAMPLE_RATE * 1.3)
        out, y, phase = [], 0.0, 0.0
        for i in range(n):
            t = i / n
            y += 0.7 * (random.uniform(-1, 1) - y)
            phase += (90 - 50 * t) / SAMPLE_RATE
            saw = 2 * (phase % 1.0) - 1
            v = (y * 0.8 + saw * 0.7) * 1.6
            out.append(max(-0.95, min(0.95, v)) * self._env(i, n, attack=0.002, decay=1.8))
        return out

    def _chime(self):
        out = []
        for freq, ms in ((520, 120), (390, 220)):
            n = int(SAMPLE_RATE * ms / 1000)
            out += [0.3 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) * self._env(i, n, attack=0.01, decay=3)
                    for i in range(n)]
        return out

    def _hum(self):
        n = SAMPLE_RATE * 2
        out = []
        for i in range(n):
            t = i / SAMPLE_RATE
            v = (0.5 * math.sin(2 * math.pi * 50 * t) + 0.28 * math.sin(2 * math.pi * 100 * t)
                 + 0.12 * math.sin(2 * math.pi * 150 * t) + 0.06 * math.sin(2 * math.pi * 0.5 * t) * math.sin(2 * math.pi * 75 * t))
            out.append(v * 0.6)
        return out

    def start_hum(self, volume):
        if self.audio and self._hum_channel is None:
            self.sound_hum.set_volume(volume)
            self._hum_channel = self.sound_hum.play(loops=-1)

    def set_hum_volume(self, volume):
        self.sound_hum.set_volume(volume)

    def stop_hum(self):
        if self._hum_channel is not None:
            self._hum_channel.stop()
            self._hum_channel = None

    def play_static_loop(self):
        if self.audio:
            self._static_channel = self.sound_static.play(loops=-1)

    def stop_static_loop(self):
        if self._static_channel is not None:
            self._static_channel.stop()
            self._static_channel = None


    def text(self, surface, font, text, pos, color, center=False, shadow=True):
        img = font.render(text, True, color)
        x, y = pos
        if center:
            x -= img.get_width() // 2
        if shadow:
            surface.blit(font.render(text, True, (0, 0, 0)), (x + 2, y + 2))
        surface.blit(img, (x, y))
        return pygame.Rect(x, y, img.get_width(), img.get_height())

    def draw_cursor(self, surface, pos, color=COLOR_GREEN):
        x, y = pos
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pygame.draw.line(surface, color, (x + dx * 5, y + dy * 5), (x + dx * 13, y + dy * 13), 2)
        pygame.draw.rect(surface, color, (x - 1, y - 1, 3, 3))
