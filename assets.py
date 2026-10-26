import os
import pygame
from settings import *

MONO_FONTS = "menlo,couriernew,courier,dejavusansmono,monospace"
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")


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
        self.sound_click = self._load("click", 0.6)
        self.sound_switch = self._load("switch", VOLUME_SWITCH)
        self.sound_static = self._load("static", VOLUME_STATIC)
        self.sound_catch = self._load("catch", 0.5)
        self.sound_error = self._load("error", 0.5)
        self.sound_glitch = self._load("glitch", 0.5)
        self.sound_message = self._load("message", 0.4)
        self.sound_scare = self._load("scare", 0.9)
        self.sound_hum = self._load("hum", 0.0)
        self.sound_tick = self._load("tick", 0.5, aliases=("typewriter_ticks",))

        self._static_channel = None
        self._hum_channel = None
        self._typewriter_channel = None

    def _load(self, name, volume=1.0, aliases=()):
        if not self.audio:
            return _SilentSound()
        for base in (name, *aliases):
            for ext in (".ogg", ".wav"):
                path = os.path.join(SOUNDS_DIR, base + ext)
                if os.path.exists(path):
                    try:
                        sound = pygame.mixer.Sound(path)
                        sound.set_volume(volume)
                        return sound
                    except pygame.error:
                        pass
        return _SilentSound()

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

    def play_typewriter(self):
        if self.audio and self._typewriter_channel is None:
            self._typewriter_channel = self.sound_tick.play(loops=-1)

    def stop_typewriter(self):
        if self._typewriter_channel is not None:
            self._typewriter_channel.stop()
            self._typewriter_channel = None

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
