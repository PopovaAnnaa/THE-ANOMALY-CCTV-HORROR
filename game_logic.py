import pygame
import random
from settings import *

class AnomalyManager:
    def __init__(self):
        self.state = "MENU"
        self.current_cam = 1
        self.max_cams = 8
        self.caught_count = 0
        self.sanity = INITIAL_SANITY

        # Блокування при помилці
        self.is_locked = False
        self.lock_start_time = 0

        # Сховані тонкі аномалії (дрібні розміри, приховані місця)
        self.anomalies = [
            # CAM 01: Mainframe
            {"id": 1, "cam": 1, "rect": pygame.Rect(148, 178, 16, 24), "active": False, "name": "Led Displace", "evaded": False},
            {"id": 2, "cam": 1, "rect": pygame.Rect(432, 262, 14, 18), "active": False, "name": "Glitch Pixel", "evaded": False},
            
            # CAM 02: Bio-Lab
            {"id": 3, "cam": 2, "rect": pygame.Rect(485, 330, 22, 18), "active": False, "name": "Tube Crack", "evaded": False},
            {"id": 4, "cam": 2, "rect": pygame.Rect(235, 280, 12, 12), "active": False, "name": "Lens Distortion", "evaded": False},

            # CAM 03: Decon Vault
            {"id": 5, "cam": 3, "rect": pygame.Rect(385, 165, 20, 14), "active": False, "name": "Nozzle Shift", "evaded": False},
            {"id": 6, "cam": 3, "rect": pygame.Rect(228, 300, 18, 18), "active": False, "name": "Visor Stain", "evaded": False},

            # CAM 04: Containment Gate
            {"id": 7, "cam": 4, "rect": pygame.Rect(392, 282, 16, 26), "active": False, "name": "Lock Gap", "evaded": False},

            # CAM 05: Cryo Vault
            {"id": 8, "cam": 5, "rect": pygame.Rect(202, 182, 35, 10), "active": False, "name": "Frost Speck", "evaded": False},
            {"id": 9, "cam": 5, "rect": pygame.Rect(362, 270, 18, 25), "active": False, "name": "Glass Warp", "evaded": False},

            # CAM 06: Quantum Lab
            {"id": 10, "cam": 6, "rect": pygame.Rect(392, 262, 16, 16), "active": False, "name": "Core Flicker", "evaded": False},

            # CAM 07: Substation
            {"id": 11, "cam": 7, "rect": pygame.Rect(362, 222, 16, 16), "active": False, "name": "Gauge Needle Jitter", "evaded": False},
            {"id": 12, "cam": 7, "rect": pygame.Rect(440, 290, 22, 15), "active": False, "name": "Wire Split", "evaded": False},

            # CAM 08: Deep Window
            {"id": 13, "cam": 8, "rect": pygame.Rect(310, 190, 14, 14), "active": False, "name": "Void Pulse", "evaded": False}
        ]

    def show_story(self):
        self.state = "STORY"

    def start_game(self):
        self.state = "PLAYING"
        self.current_cam = 1
        self.caught_count = 0
        self.sanity = INITIAL_SANITY
        self.is_locked = False
        for a in self.anomalies:
            a["active"] = False
            a["evaded"] = False

    def switch_cam(self, direction, assets):
        if self.state != "PLAYING" or self.is_locked:
            return
        new_cam = self.current_cam + direction
        if new_cam < 1:
            new_cam = self.max_cams
        elif new_cam > self.max_cams:
            new_cam = 1

        if self.current_cam != new_cam:
            self.current_cam = new_cam
            assets.sound_click.play()

    def check_hover_evade(self, mouse_pos, assets):
        """Перевірка наведення миші для механіки ухилення аномалії."""
        if self.state != "PLAYING" or self.is_locked:
            return

        for a in self.anomalies:
            if a["cam"] == self.current_cam and a["active"] and not a["evaded"]:
                if a["rect"].collidepoint(mouse_pos):
                    if random.random() < EVADE_CHANCE:
                        # Аномалія помітила погляд і телепортується на іншу камеру!
                        a["evaded"] = True
                        other_cams = [c for c in range(1, self.max_cams + 1) if c != self.current_cam]
                        a["cam"] = random.choice(other_cams)
                        assets.sound_error.play()

    def spawn_random_anomaly(self):
        if self.state != "PLAYING" or self.is_locked:
            return

        hidden = [a for a in self.anomalies if a["cam"] != self.current_cam and not a["active"]]
        if hidden:
            chosen = random.choice(hidden)
            chosen["active"] = True
            chosen["evaded"] = False

    def handle_click(self, pos, assets):
        if self.state != "PLAYING" or self.is_locked:
            return

        hit = False
        for a in self.anomalies:
            if a["cam"] == self.current_cam and a["active"] and a["rect"].collidepoint(pos):
                a["active"] = False
                self.caught_count += 1
                hit = True
                assets.sound_catch.play()
                break

        if not hit:
            # Хибний клік: штраф глузду + блокування на 3 секунди
            self.sanity -= SANITY_PENALTY
            self.is_locked = True
            self.lock_start_time = pygame.time.get_ticks()
            assets.sound_error.play()

    def update_status(self):
        if self.state != "PLAYING":
            return

        # Зняття блокування після 3 секунд
        if self.is_locked:
            if pygame.time.get_ticks() - self.lock_start_time >= LOCKOUT_DURATION_MS:
                self.is_locked = False

        active_count = sum(1 for a in self.anomalies if a["active"])
        if active_count >= MAX_ACTIVE_ANOMALIES or self.sanity <= 0:
            self.state = "GAMEOVER"
        elif self.caught_count >= REQUIRED_WIN_CATCHES:
            self.state = "WIN"