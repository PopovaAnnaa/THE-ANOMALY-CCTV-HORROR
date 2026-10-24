import random
import pygame
from settings import *
from rooms import ROOMS, draw_entity, h01
from game_logic import AnomalyManager, clock_to_real, fmt_clock, save_archive
from story import (INTRO_LINES, INTERCOM, GLITCH_NAMES, WINDOW_TITLE, WINDOW_TITLE_HAUNTED,
                   ending_lines)


class Scene:
    def __init__(self, app):
        self.app = app
        self.started = pygame.time.get_ticks()

    @property
    def age(self):
        return pygame.time.get_ticks() - self.started

    def handle_event(self, e):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass


class MenuScene(Scene):
    CYCLE_MS = 6500

    def __init__(self, app):
        super().__init__(app)
        pygame.display.set_caption(WINDOW_TITLE)
        app.assets.stop_hum()
        app.assets.stop_static_loop()
        self.cams = list(ROOMS)
        random.shuffle(self.cams)
        self.cam_index = 0
        self.last_cycle = pygame.time.get_ticks()
        self.dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 150))
        cx = SCREEN_WIDTH // 2
        self.buttons = {
            "start": pygame.Rect(cx - 170, 380, 340, 54),
            "exit": pygame.Rect(cx - 170, 450, 340, 54),
        }

    def handle_event(self, e):
        a = self.app.assets
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.buttons["start"].collidepoint(e.pos):
                a.sound_catch.play()
                self.app.change(IntroScene(self.app))
            elif self.buttons["exit"].collidepoint(e.pos):
                self.app.running = False
        elif e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE):
            a.sound_catch.play()
            self.app.change(IntroScene(self.app))

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_cycle > self.CYCLE_MS:
            self.last_cycle = now
            self.cam_index = (self.cam_index + 1) % len(self.cams)
            self.app.fx.kick(0.7, 260)

    def draw(self, screen):
        a, fx = self.app.assets, self.app.fx
        t = pygame.time.get_ticks() / 1000
        room = ROOMS[self.cams[self.cam_index]]
        if pygame.time.get_ticks() - self.last_cycle < 200:
            fx.render_static()
            fx.present(screen, static=True)
        else:
            fx.render_room(room, room.base_state, t)
            fx.present(screen)
        screen.blit(self.dim, (0, 0))

        a.text(screen, a.font_small, f"CAM 0{room.cam_id} - {room.name}", (24, 20), COLOR_DIM_GREEN)

        cx = SCREEN_WIDTH // 2
        glitch = random.random() < 0.04
        off = random.randint(3, 8) if glitch else 2
        title = "THE ANOMALY"
        for color, dx in (((255, 30, 30), -off), ((30, 220, 255), off)):
            img = a.font_title.render(title, True, color)
            img.set_alpha(110)
            screen.blit(img, (cx - img.get_width() // 2 + dx, 170))
        a.text(screen, a.font_title, title, (cx, 170), COLOR_WHITE, center=True)
        a.text(screen, a.font_main, "C C T V   H O R R O R", (cx, 248), COLOR_GREEN, center=True)
        a.text(screen, a.font_small, "SUBTERRANEAN CONTAINMENT FACILITY - SECTOR 07 - TERMINAL 04",
               (cx, 282), COLOR_GRAY, center=True)

        mouse = self.app.mouse
        for key, label, hover_color in (("start", "> START SHIFT", COLOR_GREEN), ("exit", "> SHUTDOWN", COLOR_RED)):
            r = self.buttons[key]
            color = hover_color if r.collidepoint(mouse) else COLOR_LIGHT_GRAY
            pygame.draw.rect(screen, color, r, 2)
            a.text(screen, a.font_large, label, (r.centerx, r.y + 10), color, center=True)

        lines = ["[A/D] [ARROWS] [1-8]  SWITCH CAMERA",
                 "[LEFT CLICK]  REPORT ANOMALY     [ESC]  PAUSE",
                 f"SURVIVE UNTIL {SHIFT_END}. NEVER LET {MAX_ACTIVE_ANOMALIES} STAND UNREPORTED."]
        for i, line in enumerate(lines):
            a.text(screen, a.font_small, line, (cx, 560 + i * 24), COLOR_LIGHT_GRAY if i < 2 else COLOR_AMBER,
                   center=True)
        fx.overlay(screen)


class TypewriterScene(Scene):
    CPS = 60
    lines = []
    top = 70
    line_h = 27

    def __init__(self, app):
        super().__init__(app)
        self.total = sum(len(t) for t, _ in self.lines)
        self.skip = False
        self.last_tick = 0

    @property
    def shown(self):
        return self.total if self.skip else int(self.age / 1000 * self.CPS)

    @property
    def done(self):
        return self.shown >= self.total

    def update(self):
        n = self.shown
        if not self.done and n // 3 != self.last_tick:
            self.last_tick = n // 3
            self.app.assets.sound_tick.play()

    def draw_text(self, screen):
        a = self.app.assets
        left = self.shown
        y = self.top
        for text, color in self.lines:
            if left <= 0:
                break
            part = text[:left]
            left -= len(text)
            if part:
                a.text(screen, a.font_main, part, (110, y), color)
            if 0 < len(part) < len(text) or (left <= 0 and not self.done):
                if (pygame.time.get_ticks() // 250) % 2:
                    w = a.font_main.size(part)[0]
                    screen.fill(COLOR_GREEN, (112 + w, y + 3, 10, 16))
            y += self.line_h


class IntroScene(TypewriterScene):
    lines = INTRO_LINES
    top = 60
    line_h = 28

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            if not self.done and e.key != pygame.K_ESCAPE:
                self.skip = True
            else:
                self.app.assets.sound_catch.play()
                self.app.change(ShiftScene(self.app))
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.done:
            self.skip = True

    def draw(self, screen):
        a = self.app.assets
        screen.fill(COLOR_BLACK)
        self.draw_text(screen)
        if self.done and (pygame.time.get_ticks() // 500) % 2:
            a.text(screen, a.font_main, "[SPACE] BEGIN MONITORING", (SCREEN_WIDTH // 2, 650), COLOR_WHITE, center=True)
        self.app.fx.overlay(screen)


class Intercom:
    CPS = 42
    HOLD_MS = 6500
    FADE_MS = 600
    WIDTH = 640
    GLYPHS = "#%&@/\\|_01"

    def __init__(self, app):
        self.app = app
        self.queue = sorted((clock_to_real(c), sender, text, stamp, corrupt)
                            for c, sender, text, stamp, corrupt in INTERCOM)
        self.msg = None

    def _wrap(self, text):
        font = self.app.assets.font_main
        lines, line = [], ""
        for word in text.split(" "):
            test = f"{line} {word}".strip()
            if font.size(test)[0] > self.WIDTH - 28 and line:
                lines.append(line)
                line = word
            else:
                line = test
        lines.append(line)
        return lines

    def shift_time(self, ms):
        if self.msg:
            self.msg["start"] += ms
            self.msg["end"] += ms

    def update(self, elapsed, now):
        if self.msg is None and self.queue and elapsed >= self.queue[0][0]:
            _, sender, text, stamp, corrupt = self.queue.pop(0)
            lines = self._wrap(text)
            total = sum(len(l) for l in lines)
            done_at = now + total / self.CPS * 1000
            self.msg = {"sender": sender, "stamp": stamp or fmt_clock(elapsed), "lines": lines,
                        "corrupt": corrupt, "start": now, "total": total, "last_tick": -1,
                        "end": done_at + self.HOLD_MS}
            self.app.assets.sound_message.play()
        if self.msg:
            shown = self.shown(now)
            if shown < self.msg["total"] and shown // 3 != self.msg["last_tick"]:
                self.msg["last_tick"] = shown // 3
                self.app.assets.sound_tick.play()
            if now >= self.msg["end"]:
                self.msg = None

    def shown(self, now):
        return int((now - self.msg["start"]) / 1000 * self.CPS)

    def _corrupt(self, text, amount, now, seed):
        if amount <= 0:
            return text
        slot = now // 90
        return "".join(self.GLYPHS[int(h01(slot * 977 + seed + i) * len(self.GLYPHS))]
                       if c != " " and h01(slot * 131 + seed * 7 + i) < amount * 0.35 else c
                       for i, c in enumerate(text))

    def draw(self, screen, now):
        if not self.msg:
            return
        a, m = self.app.assets, self.msg
        h = 40 + 24 * len(m["lines"])
        panel = pygame.Surface((self.WIDTH, h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        pygame.draw.rect(panel, (*COLOR_DIM_GREEN, 255), panel.get_rect(), 1)

        header = f"INTERCOM // {m['sender']} // [{m['stamp']}]"
        a.text(panel, a.font_small, self._corrupt(header, m["corrupt"], now, 999), (14, 8), COLOR_AMBER)
        left = self.shown(now)
        for i, line in enumerate(m["lines"]):
            if left <= 0:
                break
            part = self._corrupt(line[:left], m["corrupt"], now, i * 53)
            left -= len(line)
            a.text(panel, a.font_main, part, (14, 30 + i * 24), COLOR_WHITE)

        fade = min(1.0, (m["end"] - now) / self.FADE_MS)
        panel.set_alpha(int(255 * max(0.0, fade)))
        screen.blit(panel, (16, HUD_TOP + 10))


class ShiftScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        now = pygame.time.get_ticks()
        self.game = AnomalyManager(ROOMS)
        self.game.reset(now)
        self.intercom = Intercom(app)
        self.cam = 1
        self.switch_until = now + 400
        self.was_locked = False
        self.haunt_at = None
        self.paused_at = None
        self.toast = None
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        self.pause_buttons = {
            "resume": pygame.Rect(cx - 160, cy - 10, 320, 50),
            "quit": pygame.Rect(cx - 160, cy + 54, 320, 50),
        }
        self.pause_dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.pause_dim.fill((0, 0, 0, 160))
        self.hud_bands = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.hud_bands.fill((0, 0, 0, 110), (0, 0, SCREEN_WIDTH, HUD_TOP))
        self.hud_bands.fill((0, 0, 0, 110), (0, SCREEN_HEIGHT - HUD_BOTTOM, SCREEN_WIDTH, HUD_BOTTOM))
        bw, gap = 38, 6
        x0 = SCREEN_WIDTH - 8 * (bw + gap) - 18
        self.cam_buttons = {i: pygame.Rect(x0 + (i - 1) * (bw + gap), SCREEN_HEIGHT - 46, bw, 30)
                            for i in range(1, 9)}
        pygame.display.set_caption(WINDOW_TITLE)
        app.assets.sound_switch.play()
        app.assets.start_hum(ACTS[0]["hum"])

    def leave(self):
        if self.paused_at is not None:
            pygame.mixer.unpause()
        self.app.assets.stop_static_loop()
        self.app.assets.stop_hum()


    def pause(self):
        if self.paused_at is None and not self.game.result:
            self.paused_at = pygame.time.get_ticks()
            if self.app.assets.audio:
                pygame.mixer.pause()

    def resume(self):
        if self.paused_at is None:
            return
        dt = pygame.time.get_ticks() - self.paused_at
        self.paused_at = None
        self.game.shift_time(dt)
        self.intercom.shift_time(dt)
        self.switch_until += dt
        if self.haunt_at:
            self.haunt_at += dt
        if self.toast:
            self.toast = (self.toast[0], self.toast[1], self.toast[2] + dt)
        if self.app.assets.audio:
            pygame.mixer.unpause()
        self.app.assets.sound_click.play()

    def handle_pause_event(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self.resume()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.pause_buttons["resume"].collidepoint(e.pos):
                self.resume()
            elif self.pause_buttons["quit"].collidepoint(e.pos):
                self.leave()
                self.app.change(MenuScene(self.app))


    def switch_cam(self, cam):
        now = pygame.time.get_ticks()
        if self.game.is_locked(now) or cam == self.cam:
            return
        self.cam = cam
        self.switch_until = now + CAM_SWITCH_STATIC_MS
        self.app.assets.sound_switch.play()

    def handle_event(self, e):
        if self.paused_at is not None:
            self.handle_pause_event(e)
            return
        if e.type == pygame.WINDOWFOCUSLOST:
            self.pause()
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_a, pygame.K_LEFT):
                self.switch_cam((self.cam - 2) % 8 + 1)
            elif e.key in (pygame.K_d, pygame.K_RIGHT):
                self.switch_cam(self.cam % 8 + 1)
            elif pygame.K_1 <= e.key <= pygame.K_8:
                self.switch_cam(e.key - pygame.K_0)
            elif e.key in (pygame.K_ESCAPE, pygame.K_p):
                self.pause()
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for cam, r in self.cam_buttons.items():
                if r.collidepoint(e.pos):
                    self.switch_cam(cam)
                    return
            if e.pos[1] < HUD_TOP or e.pos[1] > SCREEN_HEIGHT - HUD_BOTTOM:
                return
            self.report(e.pos)

    def report(self, pos):
        now = pygame.time.get_ticks()
        if now < self.switch_until or self.game.is_locked(now):
            return
        low = (pos[0] // SCALE, pos[1] // SCALE)
        kind, anomaly = self.game.report(self.cam, low, now)
        a = self.app.assets
        if kind == "hit":
            a.sound_catch.play()
            self.app.fx.kick(0.35, 180)
            self.show_toast(f"ANOMALY LOGGED: {anomaly['name'].upper()}", COLOR_GREEN)
        elif kind == "miss":
            a.sound_error.play()
            a.play_static_loop()
            self.app.fx.kick(1.0, 400)

    def show_toast(self, text, color, ms=2600):
        self.toast = (text, color, pygame.time.get_ticks() + ms)


    def update(self):
        if self.paused_at is not None:
            return
        now = pygame.time.get_ticks()
        g = self.game
        locked = g.is_locked(now)
        if self.was_locked and not locked:
            self.app.assets.stop_static_loop()
            self.switch_until = now + CAM_SWITCH_STATIC_MS
        self.was_locked = locked

        watching = not locked and now >= self.switch_until
        events = g.update(now, self.cam if watching else None)
        self.intercom.update(g.elapsed(now), now)

        if "act" in events:
            act = ACTS[g.act]
            self.app.fx.kick(0.9, 500)
            self.app.assets.sound_glitch.play()
            self.app.assets.set_hum_volume(act["hum"])
            if g.act == len(ACTS) - 1:
                self.haunt_at = now + 15000
        if self.haunt_at and now >= self.haunt_at:
            pygame.display.set_caption(WINDOW_TITLE_HAUNTED)
            self.haunt_at = None

        if watching:
            m = self.app.mouse
            if g.hover(self.cam, (m[0] // SCALE, m[1] // SCALE), now) == "evade":
                self.app.assets.sound_glitch.play()
                self.app.fx.kick(1.0, 550)
                self.show_toast("SIGNAL INTERFERENCE DETECTED", COLOR_AMBER, 1800)

        if g.result:
            self.leave()
            self.app.change(EndingScene(self.app, g.result, g.reason, g.stats(),
                                        self.cam, g.state_for(self.cam)))


    def draw(self, screen):
        paused = self.paused_at is not None
        now = self.paused_at if paused else pygame.time.get_ticks()
        fx, g = self.app.fx, self.game
        t = now / 1000
        locked = g.is_locked(now)
        room = ROOMS[self.cam]

        if locked or now < self.switch_until:
            fx.render_static()
            fx.present(screen, extra_glitch=0.6 if locked else 0.2, static=True)
        else:
            fx.render_room(room, g.state_for(self.cam), t, ACTS[g.act]["ambient"])
            fx.present(screen)

        self.draw_hud(screen, room, now, locked)
        if paused:
            self.draw_pause(screen, now)
        fx.overlay(screen)

    def draw_pause(self, screen, now):
        a = self.app.assets
        screen.blit(self.pause_dim, (0, 0))
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        box = pygame.Rect(cx - 220, cy - 130, 440, 260)
        screen.fill((0, 0, 0), box)
        pygame.draw.rect(screen, COLOR_DIM_GREEN, box, 2)
        a.text(screen, a.font_large, "FEED ON HOLD", (cx, cy - 108), COLOR_WHITE, center=True)
        a.text(screen, a.font_small, f"SHIFT PAUSED AT {fmt_clock(self.game.elapsed(now))}",
               (cx, cy - 64), COLOR_LIGHT_GRAY, center=True)
        mouse = self.app.mouse
        for key, label, hover_color in (("resume", "> RESUME", COLOR_GREEN), ("quit", "> QUIT TO MENU", COLOR_RED)):
            r = self.pause_buttons[key]
            color = hover_color if r.collidepoint(mouse) else COLOR_LIGHT_GRAY
            pygame.draw.rect(screen, color, r, 2)
            a.text(screen, a.font_main, label, (r.centerx, r.y + 14), color, center=True)

    def draw_hud(self, screen, room, now, locked):
        a, g = self.app.assets, self.game
        screen.blit(self.hud_bands, (0, 0))

        if (now // 600) % 2:
            pygame.draw.circle(screen, COLOR_RED, (30, 26), 7)
        a.text(screen, a.font_main, "REC", (44, 16), COLOR_WHITE)

        name, name_color = room.name, COLOR_WHITE
        if g.act == len(ACTS) - 1 and h01((now // 450) * 13 + self.cam) < 0.07:
            name, name_color = GLITCH_NAMES[self.cam], (220, 80, 70)
        a.text(screen, a.font_main, f"CAM 0{room.cam_id} - {name}", (110, 16), name_color)
        a.text(screen, a.font_main, f"{SHIFT_DATE}  {fmt_clock(g.elapsed(now))}",
               (SCREEN_WIDTH - 250, 16), COLOR_WHITE)

        y = SCREEN_HEIGHT - 42
        a.text(screen, a.font_small, f"LOGGED {g.logged:02d}", (20, y), COLOR_GREEN)
        sanity_color = COLOR_GREEN if g.sanity > 50 else COLOR_AMBER if g.sanity > 25 else COLOR_RED
        a.text(screen, a.font_small, f"SANITY {g.sanity:03d}%", (150, y), sanity_color)
        stable = g.breach_count(now)
        fresh = min(MAX_ACTIVE_ANOMALIES, g.active_count) - stable
        breach_color = COLOR_RED if stable >= MAX_ACTIVE_ANOMALIES - 1 else COLOR_LIGHT_GRAY
        a.text(screen, a.font_small, "BREACH", (290, y), breach_color)
        for i in range(MAX_ACTIVE_ANOMALIES):
            r = pygame.Rect(360 + i * 18, y + 2, 12, 14)
            if i < stable:
                screen.fill(COLOR_RED if stable >= MAX_ACTIVE_ANOMALIES - 1 else COLOR_AMBER, r)
            elif i < stable + fresh:
                screen.fill((70, 60, 40), r)
            else:
                pygame.draw.rect(screen, COLOR_GRAY, r, 1)

        mouse = self.app.mouse
        for cam, r in self.cam_buttons.items():
            current = cam == self.cam
            hover = r.collidepoint(mouse)
            color = COLOR_GREEN if current else COLOR_WHITE if hover else COLOR_GRAY
            if current:
                screen.fill((20, 70, 40), r)
            pygame.draw.rect(screen, color, r, 1)
            a.text(screen, a.font_small, str(cam), (r.centerx, r.y + 6), color, center=True, shadow=False)

        self.intercom.draw(screen, now)

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        if locked:
            left = (g.locked_until - now) / 1000
            box = pygame.Rect(cx - 250, cy - 60, 500, 120)
            screen.fill((0, 0, 0), box)
            pygame.draw.rect(screen, COLOR_RED, box, 2)
            a.text(screen, a.font_large, "FALSE ALARM", (cx, cy - 42), COLOR_RED, center=True)
            a.text(screen, a.font_main, "SIGNAL LOST - REACQUIRING FEED", (cx, cy + 2), COLOR_WHITE, center=True)
            a.text(screen, a.font_main, f"{left:0.1f}s", (cx, cy + 28), COLOR_LIGHT_GRAY, center=True)
        elif now < self.switch_until:
            a.text(screen, a.font_main, "NO SIGNAL", (cx, cy - 10), COLOR_WHITE, center=True)

        if self.toast and now < self.toast[2] and not locked:
            a.text(screen, a.font_main, self.toast[0], (cx, SCREEN_HEIGHT - HUD_BOTTOM - 34), self.toast[1],
                   center=True)


GRADE_COLORS = {"S": COLOR_GREEN, "A": COLOR_GREEN, "B": COLOR_WHITE, "C": COLOR_AMBER,
                "D": COLOR_AMBER, "F": COLOR_RED}


class EndingScene(TypewriterScene):
    CPS = 70
    line_h = 28
    SCARE_MS = 950
    STATIC_MS = 750

    def __init__(self, app, result, reason, stats, last_cam=1, last_state=None):
        archive = save_archive(stats["found"])
        gray = COLOR_LIGHT_GRAY
        who = "OBSERVER 04" if result == "WIN" else "TERMINAL 04"
        row = lambda label, value: f"{label:.<26} {value}"
        self.lines = ending_lines(result, reason) + [
            ("", None),
            (f"SHIFT REPORT - {who}", COLOR_AMBER),
            (row("Survived until", stats["survived"]), gray),
            (row("Anomalies logged", stats["logged"]), gray),
            (row("Unique this shift", f"{stats['unique']}/{stats['total']}"), gray),
            (row("Archive, all shifts", f"{len(archive)}/{stats['total']}"), gray),
            (row("False alarms", stats["false_alarms"]), gray),
            (row("Left unreported", stats["missed"]), gray),
            (row("Rating", f"{stats['grade']} - {stats['label']}"), GRADE_COLORS[stats["grade"]]),
        ]
        self.top = max(40, (SCREEN_HEIGHT - len(self.lines) * self.line_h) // 2 - 30)
        self.intro_ms = 600 if result == "WIN" else self.SCARE_MS + self.STATIC_MS
        super().__init__(app)
        self.result = result
        self.last_room = ROOMS[last_cam]
        self.last_state = last_state or self.last_room.base_state
        pygame.display.set_caption(WINDOW_TITLE)
        if result == "WIN":
            app.assets.sound_message.play()
        else:
            app.assets.sound_scare.play()

    @property
    def shown(self):
        if self.skip:
            return self.total
        return max(0, int((self.age - self.intro_ms) / 1000 * self.CPS))

    def update(self):
        if self.age > self.intro_ms:
            super().update()

    def handle_event(self, e):
        if self.age < self.intro_ms + 600:
            return
        if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if not self.done:
                self.skip = True
            elif e.type == pygame.MOUSEBUTTONDOWN or e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.app.change(MenuScene(self.app))

    def draw(self, screen):
        fx, a = self.app.fx, self.app.assets
        age = self.age
        t = age / 1000

        if self.result == "LOSE" and age < self.SCARE_MS:
            k = age / self.SCARE_MS
            fx.render_room(self.last_room, self.last_state, t)
            draw_entity(fx.feed, LOW_WIDTH / 2 + random.randint(-2, 2), LOW_HEIGHT / 2 + random.randint(-2, 2),
                        8 + 230 * k ** 2.2, t * 3, fx, core_ratio=0.07)
            fx.present(screen, extra_glitch=0.3 + 0.7 * k)
        elif age < self.intro_ms:
            fx.render_static()
            fx.present(screen, extra_glitch=0.8 if self.result == "LOSE" else 0.3, static=True)
        else:
            screen.fill(COLOR_BLACK)
            self.draw_text(screen)
            if self.done and (pygame.time.get_ticks() // 500) % 2:
                a.text(screen, a.font_main, "[ENTER] RETURN TO TERMINAL", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50),
                       COLOR_WHITE, center=True)
        fx.overlay(screen)
