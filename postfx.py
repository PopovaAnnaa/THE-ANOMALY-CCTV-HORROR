import os
import random
import pygame
from settings import *


class CCTVRenderer:
    def __init__(self):
        self.feed = pygame.Surface((LOW_WIDTH, LOW_HEIGHT)).convert()
        self.light = pygame.Surface((LOW_WIDTH, LOW_HEIGHT)).convert()
        self._gradients = {}

        self.static = [self._noise_frame() for _ in range(6)]
        self.grain = [self._noise_frame() for _ in range(6)]
        for g in self.grain:
            g.set_alpha(GRAIN_ALPHA)

        self.scanlines = self._make_scanlines()
        self.vignette = self._make_vignette()

        self.glitch_until = 0
        self.glitch_power = 0.0

    @staticmethod
    def _noise_frame():
        data = os.urandom(LOW_WIDTH * LOW_HEIGHT)
        surf = pygame.image.frombytes(data, (LOW_WIDTH, LOW_HEIGHT), "P")
        surf.set_palette([(g, g, g) for g in range(256)])
        return surf.convert()

    def _gradient(self, r):
        r = max(2, int(r))
        if r not in self._gradients:
            g = pygame.Surface((r * 2, r * 2)).convert()
            for i in range(r, 0, -1):
                v = int(255 * (1 - i / r) ** 1.3)
                pygame.draw.circle(g, (v, v, v), (r, r), i)
            self._gradients[r] = g
        return self._gradients[r]

    @staticmethod
    def _make_scanlines():
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, SCALE):
            pygame.draw.line(surf, (0, 0, 0, 70), (0, y), (SCREEN_WIDTH, y))
        return surf

    @staticmethod
    def _make_vignette():
        small = pygame.Surface((LOW_WIDTH, LOW_HEIGHT), pygame.SRCALPHA)
        small.fill((0, 0, 0, 160))
        cx, cy = LOW_WIDTH // 2, LOW_HEIGHT // 2
        for i in range(32):
            f = i / 32
            alpha = int(160 * (1 - f))
            w = int(LOW_WIDTH * (1 - f * 0.55))
            h = int(LOW_HEIGHT * (1 - f * 0.55))
            pygame.draw.ellipse(small, (0, 0, 0, alpha), (cx - w // 2, cy - h // 2, w, h))
        return pygame.transform.smoothscale(small, (SCREEN_WIDTH, SCREEN_HEIGHT))

    def glow(self, surf, x, y, r, color):
        r = max(2, int(r))
        blob = self._gradient(r).copy()
        blob.fill(color, special_flags=pygame.BLEND_MULT)
        surf.blit(blob, (int(x) - r, int(y) - r), special_flags=pygame.BLEND_ADD)

    def kick(self, power, duration_ms):
        now = pygame.time.get_ticks()
        if now >= self.glitch_until or power > self.glitch_power:
            self.glitch_power = power
        self.glitch_until = max(self.glitch_until, now + duration_ms)

    def render_room(self, room, state, t, ambient_scale=1.0):
        f = self.feed
        room.draw_albedo(f, state, t)

        base = max(0, min(255, int(room.ambient * ambient_scale)))
        self.light.fill((base, base, base))
        for x, y, r, intensity in room.lights(state, t):
            v = max(0, min(255, int(255 * intensity)))
            self.glow(self.light, x, y, r, (v, v, v))
        f.blit(self.light, (0, 0), special_flags=pygame.BLEND_MULT)

        gray = pygame.transform.grayscale(f)
        gray.fill(room.tint, special_flags=pygame.BLEND_MULT)
        f.blit(gray, (0, 0))

        room.emissive(f, state, t, self)

    def render_static(self, darkness=1.0):
        self.feed.blit(random.choice(self.static), (0, 0))
        if darkness < 1.0:
            d = int(255 * darkness)
            self.feed.fill((d, d, d), special_flags=pygame.BLEND_MULT)

    def present(self, screen, extra_glitch=0.0, static=False):
        now = pygame.time.get_ticks()
        glitch = self.glitch_power if now < self.glitch_until else 0.0
        glitch = max(glitch, extra_glitch)
        f = self.feed

        if not static:
            f.blit(random.choice(self.grain), (0, 0))

        if glitch > 0.4:
            for _ in range(int(glitch * 4)):
                y = random.randint(0, LOW_HEIGHT - 6)
                h = random.randint(2, 6)
                strip = f.subsurface((0, y, LOW_WIDTH, h)).copy()
                f.blit(strip, (random.randint(-10, 10), y))

        out = self._chroma(f, 1 if static else 1 + int(glitch * 3))
        big = pygame.transform.scale(out, (SCREEN_WIDTH, SCREEN_HEIGHT))

        shake = int(glitch * 6)
        ox = random.randint(-shake, shake) if shake else 0
        oy = random.randint(-shake, shake) if shake else 0
        if ox or oy:
            screen.fill((0, 0, 0))
        screen.blit(big, (ox, oy))

    def overlay(self, screen):
        screen.blit(self.scanlines, (0, 0))
        screen.blit(self.vignette, (0, 0))

    @staticmethod
    def _chroma(src, offset):
        red = src.copy()
        red.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
        out = src.copy()
        out.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
        out.blit(red, (offset, 0), special_flags=pygame.BLEND_ADD)
        return out
