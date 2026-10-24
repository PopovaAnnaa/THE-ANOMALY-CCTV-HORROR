import math
import os
import random
import pygame
from settings import *


class CCTVRenderer:
    def __init__(self):
        size = (LOW_WIDTH, LOW_HEIGHT)
        self.feed = pygame.Surface(size).convert()
        self.mask = pygame.Surface(size).convert()
        self._chroma_out = pygame.Surface(size).convert()
        self._big = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()

        self._gradients = {}
        self._lights = {}
        self._glows = {}

        self.grain = [self._noise_frame(LOW_WIDTH, LOW_HEIGHT, 0, 255, GRAIN_ALPHA) for _ in range(8)]
        self.static = [self._static_frame() for _ in range(8)]
        self.scanlines = self._make_scanlines()
        self.vignette = self._make_vignette()

        self.glitch_until = 0
        self.glitch_power = 0.0
        self.band_y = None
        self.next_band = pygame.time.get_ticks() + random.randint(3000, 7000)


    @staticmethod
    def _noise_frame(w, h, lo, hi, alpha=None):
        surf = pygame.image.frombytes(os.urandom(w * h), (w, h), "P")
        surf.set_palette([(lo + (hi - lo) * i // 255,) * 3 for i in range(256)])
        surf = surf.convert()
        if alpha is not None:
            surf.set_alpha(alpha)
        return surf

    def _static_frame(self):
        small = self._noise_frame(LOW_WIDTH // 2, LOW_HEIGHT // 2, 8, 210)
        frame = pygame.transform.scale(small, (LOW_WIDTH, LOW_HEIGHT))
        for _ in range(4):
            y = random.randint(0, LOW_HEIGHT - 1)
            frame.fill((235, 240, 235), (0, y, LOW_WIDTH, 1))
        return frame

    def _gradient(self, r):
        if r not in self._gradients:
            g = pygame.Surface((r * 2, r * 2)).convert()
            g.fill((0, 0, 0))
            for i in range(r, 0, -1):
                v = int(255 * (1 - i / r) ** 1.25)
                pygame.draw.circle(g, (v, v, v), (r, r), i)
            self._gradients[r] = g
        return self._gradients[r]

    def _light(self, r, level):
        key = (r, level)
        if key not in self._lights:
            g = self._gradient(r).copy()
            c = int(255 * level / 16)
            g.fill((c, c, c), special_flags=pygame.BLEND_MULT)
            self._lights[key] = g
        return self._lights[key]

    def _make_scanlines(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCALE - 1, SCREEN_HEIGHT, SCALE):
            pygame.draw.line(s, (0, 0, 0, 85), (0, y), (SCREEN_WIDTH, y))
        return s

    def _make_vignette(self):
        small = pygame.Surface((LOW_WIDTH, LOW_HEIGHT), pygame.SRCALPHA)
        small.fill((0, 0, 0, 235))
        steps = 48
        for k in range(steps):
            sc = 1.45 - k * (0.85 / steps)
            a = int(235 * (1 - k / (steps - 1)) ** 1.7)
            w, h = LOW_WIDTH * sc, LOW_HEIGHT * sc
            pygame.draw.ellipse(small, (0, 0, 0, a),
                                (LOW_WIDTH / 2 - w / 2, LOW_HEIGHT / 2 - h / 2, w, h))
        return pygame.transform.smoothscale(small, (SCREEN_WIDTH, SCREEN_HEIGHT))


    def glow(self, surf, x, y, r, color):
        r = max(4, int(r))
        key = (r, color)
        if key not in self._glows:
            g = self._gradient(r).copy()
            g.fill(color, special_flags=pygame.BLEND_MULT)
            self._glows[key] = g
        surf.blit(self._glows[key], (int(x) - r, int(y) - r), special_flags=pygame.BLEND_ADD)

    def kick(self, power, duration_ms):
        now = pygame.time.get_ticks()
        if now >= self.glitch_until or power > self.glitch_power:
            self.glitch_power = power
        self.glitch_until = max(self.glitch_until, now + duration_ms)
        if power > 0.5 and self.band_y is None:
            self.band_y = random.randint(0, LOW_HEIGHT // 2)

    def render_room(self, room, state, t, ambient_scale=1.0):
        f = self.feed
        room.draw_albedo(f, state, t)

        self.mask.fill((int(room.ambient * ambient_scale),) * 3)
        for x, y, r, intensity in room.lights(state, t):
            level = max(0, min(16, int(round(intensity * 16))))
            if level == 0:
                continue
            r = max(8, int(r) // 4 * 4)
            self.mask.blit(self._light(r, level), (int(x) - r, int(y) - r), special_flags=pygame.BLEND_ADD)
        f.blit(self.mask, (0, 0), special_flags=pygame.BLEND_MULT)

        gray = pygame.transform.grayscale(f)
        gray.fill(room.tint, special_flags=pygame.BLEND_MULT)
        f.blit(gray, (0, 0))

        room.emissive(f, state, t, self)

    def render_static(self, darkness=1.0):
        f = self.feed
        f.blit(random.choice(self.static), (0, 0))
        y = (pygame.time.get_ticks() // 6) % (LOW_HEIGHT + 60) - 60
        f.fill((120, 120, 120), (0, y, LOW_WIDTH, 40), special_flags=pygame.BLEND_MULT)
        if darkness < 1.0:
            c = int(255 * darkness)
            f.fill((c, c, c), special_flags=pygame.BLEND_MULT)

    def present(self, screen, extra_glitch=0.0, static=False):
        now = pygame.time.get_ticks()
        g = self.glitch_power if now < self.glitch_until else 0.0
        g = max(g, extra_glitch)
        f = self.feed

        if self.band_y is None and now >= self.next_band:
            self.band_y = -12
        if self.band_y is not None:
            self._apply_band(f, int(self.band_y), g)
            self.band_y += 2.5 + g * 5
            if self.band_y > LOW_HEIGHT:
                self.band_y = None
                self.next_band = now + random.randint(5000, 13000)

        if g > 0.4:
            for _ in range(int(g * 4)):
                y = random.randint(0, LOW_HEIGHT - 8)
                h = random.randint(2, 8)
                strip = f.subsurface((0, y, LOW_WIDTH, h)).copy()
                f.blit(strip, (random.randint(-12, 12), y))

        if not static:
            f.blit(random.choice(self.grain), (0, 0))

        out = self._chroma(f, 1 if static else 1 + int(g * 3))

        jx = jy = 0
        if random.random() < 0.015 + g * 0.3:
            jx = random.choice((-1, 1))
        if g > 0.3 and random.random() < g * 0.25:
            jy = random.randint(-3, 3)

        pygame.transform.scale(out, (SCREEN_WIDTH, SCREEN_HEIGHT), self._big)
        if jx or jy:
            screen.fill((0, 0, 0))
        screen.blit(self._big, (jx * SCALE, jy * SCALE))

    def overlay(self, screen):
        screen.blit(self.scanlines, (0, 0))
        screen.blit(self.vignette, (0, 0))


    def _chroma(self, src, offset):
        red = src.copy()
        red.fill((255, 0, 0), special_flags=pygame.BLEND_MULT)
        cyan = src.copy()
        cyan.fill((0, 255, 255), special_flags=pygame.BLEND_MULT)
        out = self._chroma_out
        out.blit(cyan, (0, 0))
        out.blit(red, (offset, 0), special_flags=pygame.BLEND_ADD)
        out.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MAX)
        return out

    @staticmethod
    def _apply_band(f, y, g):
        h = 10
        for row in range(max(0, y), min(LOW_HEIGHT, y + h)):
            dx = random.randint(-2, 3) + int(g * 8 * random.random())
            if dx:
                strip = f.subsurface((0, row, LOW_WIDTH, 1)).copy()
                f.blit(strip, (dx, row))
        line_y = y + h // 2
        if 0 <= line_y < LOW_HEIGHT:
            x = 0
            while x < LOW_WIDTH:
                w = random.randint(3, 20)
                if random.random() < 0.6:
                    c = random.randint(140, 230)
                    f.fill((c, c, c), (x, line_y, w, 1))
                x += w
