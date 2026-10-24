import math
import random
import pygame
from settings import LOW_WIDTH as LW, LOW_HEIGHT as LH, FEED_TINT

_FONT = None


def tiny_font():
    global _FONT
    if _FONT is None:
        _FONT = pygame.font.SysFont("menlo,couriernew,courier,monospace", 9, bold=True)
    return _FONT


def h01(n):
    n = int(n) & 0xFFFFFFFF
    n = (((n >> 16) ^ n) * 0x45D9F3B) & 0xFFFFFFFF
    n = (((n >> 16) ^ n) * 0x45D9F3B) & 0xFFFFFFFF
    n = (n >> 16) ^ n
    return n / 0xFFFFFFFF


def flicker(t, seed, rate=12, chance=0.06, low=0.35):
    if h01(int(t * rate) * 7919 + seed) < chance:
        return low
    return 0.96 + 0.04 * math.sin(t * 47 + seed)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def lerp(a, b, f):
    return a + (b - a) * f


def stencil(s, text, pos, color):
    s.blit(tiny_font().render(text, False, color), pos)


def anomaly(key, name, kind, changes, hitbox, tier=1):
    return {"key": key, "name": name, "kind": kind, "changes": changes, "hitbox": hitbox, "tier": tier}


def draw_box(s, back, wall, floor, ceil):
    x0, y0, x1, y1 = back
    pygame.draw.polygon(s, ceil, [(0, 0), (LW, 0), (x1, y0), (x0, y0)])
    pygame.draw.polygon(s, floor, [(0, LH), (LW, LH), (x1, y1), (x0, y1)])
    pygame.draw.polygon(s, shade(wall, 0.72), [(0, 0), (x0, y0), (x0, y1), (0, LH)])
    pygame.draw.polygon(s, shade(wall, 0.82), [(LW, 0), (x1, y0), (x1, y1), (LW, LH)])
    pygame.draw.rect(s, wall, (x0, y0, x1 - x0, y1 - y0))

    line = shade(floor, 0.8)
    for i in range(1, 8):
        f = i / 8
        pygame.draw.line(s, line, (lerp(x0, x1, f), y1), (lerp(0, LW, f), LH))
    for d in (0.1, 0.26, 0.5, 0.85):
        y = lerp(y1, LH, d)
        pygame.draw.line(s, line, (lerp(x0, 0, d), y), (lerp(x1, LW, d), y))

    beam = shade(ceil, 0.7)
    for d in (0.3, 0.65):
        y = lerp(y0, 0, d)
        pygame.draw.line(s, beam, (lerp(x0, 0, d), y), (lerp(x1, LW, d), y), 2)

    seam = shade(wall, 0.86)
    for x in range(x0 + 30, x1 - 5, 30):
        pygame.draw.line(s, seam, (x, y0), (x, y1))
    pygame.draw.line(s, seam, (x0, lerp(y0, y1, 0.55)), (x1, lerp(y0, y1, 0.55)))
    for f in (0.35, 0.7):
        pygame.draw.line(s, shade(wall, 0.64), (lerp(0, x0, f), lerp(0, y0, f)), (lerp(0, x0, f), lerp(LH, y1, f)))
        pygame.draw.line(s, shade(wall, 0.74), (lerp(LW, x1, f), lerp(0, y0, f)), (lerp(LW, x1, f), lerp(LH, y1, f)))

    edge = shade(wall, 0.55)
    pygame.draw.rect(s, edge, (x0, y0, x1 - x0, y1 - y0), 1)
    for a, b in (((0, 0), (x0, y0)), ((LW, 0), (x1, y0)), ((0, LH), (x0, y1)), ((LW, LH), (x1, y1))):
        pygame.draw.line(s, edge, a, b)
    pygame.draw.line(s, shade(wall, 0.65), (x0, y1 - 3), (x1, y1 - 3))


def draw_figure(s, x, foot, h, color):
    hr = max(2, h * 0.065)
    top = foot - h
    pygame.draw.ellipse(s, color, (x - hr, top, hr * 2, hr * 2.4))
    neck_y = top + hr * 2.2
    sy = foot - h * 0.80
    pygame.draw.rect(s, color, (x - hr * 0.5, neck_y, hr, sy - neck_y + 1))
    sw, hw = h * 0.13, h * 0.085
    hip = foot - h * 0.47
    pygame.draw.polygon(s, color, [(x - sw, sy), (x + sw, sy), (x + hw, hip), (x - hw, hip)])
    aw = max(1, h * 0.045)
    hand_y = foot - h * 0.27
    for side in (-1, 1):
        sx = x + side * sw
        pygame.draw.circle(s, color, (sx - side * aw * 0.5, sy + aw * 0.5), aw * 0.8)
        pygame.draw.polygon(s, color, [(sx - side * aw, sy), (sx + side * 0.5, sy),
                                       (sx + side * h * 0.03, hand_y), (sx + side * h * 0.03 - side * aw, hand_y)])
        pygame.draw.polygon(s, color, [(x + side * hw, hip), (x + side * 0.5, hip),
                                       (x + side * 1.5, foot), (x + side * hw * 0.95, foot)])


def figure_head(x, foot, h):
    hr = max(2, h * 0.065)
    ey = foot - h + hr * 1.05
    return (x - hr * 0.45, ey), (x + hr * 0.45, ey)


def draw_lying_figure(s, cx, cy, length, color):
    w = int(length * 0.4)
    tmp = pygame.Surface((w, int(length) + 2), pygame.SRCALPHA)
    draw_figure(tmp, w / 2, length, length, color)
    tmp = pygame.transform.rotate(tmp, 90)
    tmp = pygame.transform.scale(tmp, (tmp.get_width(), max(2, tmp.get_height() // 2)))
    s.blit(tmp, (cx - tmp.get_width() // 2, cy - tmp.get_height() // 2))


def draw_chair(s, x, y, facing_camera, color):
    back = shade(color, 0.8)
    if facing_camera:
        pygame.draw.rect(s, back, (x - 7, y - 26, 14, 13))
    pygame.draw.rect(s, color, (x - 8, y - 13, 16, 4))
    pygame.draw.line(s, back, (x, y - 9), (x, y - 3), 2)
    for dx in (-7, 0, 7):
        pygame.draw.line(s, back, (x, y - 3), (x + dx, y))
    if not facing_camera:
        pygame.draw.rect(s, color, (x - 8, y - 28, 16, 15))


def hazard_stripes(s, rect, light=(150, 140, 70), dark=(40, 38, 30)):
    x, y, w, h = rect
    s.fill(light, rect)
    clip = s.get_clip()
    s.set_clip(rect)
    for sx in range(x - h, x + w + h, 12):
        pygame.draw.polygon(s, dark, [(sx, y), (sx + 6, y), (sx + 6 - h, y + h), (sx - h, y + h)])
    s.set_clip(clip)


def draw_entity(s, cx, cy, r, t, fx=None, core_ratio=0.22):
    pts = []
    for k in range(40):
        a = k / 40 * math.tau
        rr = r * (1 + 0.07 * math.sin(a * 5 + t * 6) + 0.06 * (h01(k + int(t * 24) * 40) - 0.5))
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    pygame.draw.polygon(s, (2, 2, 3), pts)
    pulse = 0.5 + 0.5 * math.sin(t * 9)
    core = max(2, int(r * core_ratio))
    if fx:
        fx.glow(s, cx, cy, int(r * 0.75), (int(60 + 50 * pulse), 6, 4))
    pygame.draw.circle(s, (int(170 + 80 * pulse), 25, 15), (int(cx), int(cy)), core)
    pygame.draw.circle(s, (255, 190, 150), (int(cx), int(cy)), max(1, core // 3))


class Room:
    cam_id = 0
    name = ""
    back = (70, 40, 250, 160)
    wall = (120, 120, 120)
    floor = (100, 100, 100)
    ceil = (80, 80, 80)
    ambient = 50
    tint = FEED_TINT
    base_state = {}
    anomalies = []

    def draw_albedo(self, s, st, t):
        draw_box(s, self.back, self.wall, self.floor, self.ceil)
        self.draw(s, st, t)

    def draw(self, s, st, t):
        pass

    def lights(self, st, t):
        return []

    def emissive(self, s, st, t, fx):
        pass


class Mainframe(Room):
    cam_id = 1
    name = "MAINFRAME"
    back = (70, 40, 250, 160)
    wall, floor, ceil = (130, 134, 140), (105, 105, 110), (80, 82, 88)
    ambient = 54
    base_state = {"dead_rack": -1, "monitor_face": False, "chair": "desk"}
    anomalies = [
        anomaly("dead_rack", "Server rack offline", "LIGHT", {"dead_rack": 1}, (106, 64, 30, 100), tier=1),
        anomaly("monitor_face", "Figure on workstation monitor", "INTRUDER", {"monitor_face": True}, (178, 120, 32, 28), tier=2),
        anomaly("chair_moved", "Operator chair displaced", "DISPLACEMENT", {"chair": "center"}, (116, 162, 32, 40), tier=1),
    ]
    RACKS = (82, 110, 138)

    def draw(self, s, st, t):
        pygame.draw.polygon(s, (62, 64, 70), [(0, 20), (46, 44), (46, 196), (0, 240)])
        for k in range(1, 12):
            f = k / 12
            pygame.draw.line(s, (44, 45, 50), (0, lerp(20, 240, f)), (46, lerp(44, 196, f)))
        for rx in self.RACKS:
            pygame.draw.rect(s, (70, 72, 80), (rx, 68, 24, 92))
            pygame.draw.rect(s, (115, 118, 126), (rx, 68, 24, 92), 1)
            for gy in range(74, 156, 6):
                pygame.draw.line(s, (52, 54, 60), (rx + 8, gy), (rx + 21, gy))
        pygame.draw.lines(s, (40, 40, 45), False, [(150, 160), (165, 168), (185, 170), (200, 166)], 2)
        pygame.draw.polygon(s, (110, 110, 116), [(172, 146), (246, 146), (252, 154), (166, 154)])
        pygame.draw.rect(s, (80, 80, 86), (166, 154, 86, 4))
        for lx in (170, 248):
            pygame.draw.line(s, (70, 70, 76), (lx, 158), (lx, 176), 2)
        for mx in (182, 212):
            pygame.draw.rect(s, (50, 52, 56), (mx, 124, 24, 20))
            pygame.draw.rect(s, (60, 62, 66), (mx + 10, 144, 4, 3))
        pygame.draw.rect(s, (150, 150, 150), (140, 16, 44, 6))
        stencil(s, "NODE-01", (196, 58), shade(self.wall, 0.55))
        stencil(s, "DATA CORE", (190, 70), shade(self.wall, 0.65))
        if st["chair"] == "desk":
            draw_chair(s, 209, 186, False, (42, 42, 48))
        else:
            draw_chair(s, 132, 200, True, (42, 42, 48))

    def lights(self, st, t):
        return [(162, 110, 190, 0.9 * flicker(t, 1)), (194, 136, 36, 0.45), (224, 136, 36, 0.45)]

    def emissive(self, s, st, t, fx):
        c = int(225 * flicker(t, 1))
        s.fill((c, min(255, c + 12), c), (142, 18, 40, 2))

        for i, rx in enumerate(self.RACKS):
            if i == st["dead_rack"]:
                continue
            for j, gy in enumerate(range(74, 156, 6)):
                v = h01(i * 131 + j * 17 + int(t * (2 + j % 3)) * 977)
                if v > 0.3:
                    s.fill((70, 255, 130), (rx + 3, gy, 2, 1))
                elif v > 0.15:
                    s.fill((255, 170, 50), (rx + 3, gy, 2, 1))
        for k in range(2, 11, 2):
            if h01(k * 7 + int(t * 3) * 31) > 0.4:
                s.fill((70, 255, 130), (40, int(lerp(44, 196, k / 12)) + 3, 2, 1))

        if st["monitor_face"]:
            s.fill((150, 172, 172), (184, 126, 20, 16))
            pygame.draw.ellipse(s, (8, 12, 12), (190, 128, 8, 9))
            pygame.draw.polygon(s, (8, 12, 12), [(186, 142), (202, 142), (199, 136), (189, 136)])
            fx.glow(s, 194, 134, 20, (40, 60, 60))
        else:
            s.fill((40, 120, 150), (184, 126, 20, 16))
            for k in range(5):
                w = 4 + int(h01(k * 13 + int(t * 6) * 101) * 14)
                s.fill((170, 230, 240), (185, 127 + k * 3, w, 1))
            fx.glow(s, 194, 134, 18, (25, 55, 65))
        s.fill((30, 105, 60), (214, 126, 20, 16))
        pts = [(214 + k * 2.2, 134 + math.sin(t * 6 + k * 0.7) * 4) for k in range(10)]
        pygame.draw.lines(s, (160, 255, 180), False, pts)
        fx.glow(s, 224, 134, 18, (20, 55, 30))


class BioLab(Room):
    cam_id = 2
    name = "BIO-LAB"
    back = (60, 45, 260, 165)
    wall, floor, ceil = (118, 132, 120), (96, 104, 98), (74, 82, 76)
    ambient = 48
    base_state = {"tank_shape": False, "bubbles": True, "flasks": (1, 1, 1)}
    anomalies = [
        anomaly("tank_shape", "Shape inside tank A", "INTRUDER", {"tank_shape": True}, (172, 60, 36, 104), tier=2),
        anomaly("bubbles", "Tank B circulation frozen", "DISTORTION", {"bubbles": False}, (212, 60, 36, 104), tier=1),
        anomaly("flask", "Sample flask missing", "MISSING", {"flasks": (1, 0, 1)}, (84, 130, 16, 22), tier=1),
    ]
    TANKS = (175, 215)

    def draw(self, s, st, t):
        pygame.draw.polygon(s, (175, 172, 150), [(100, 60), (113, 82), (87, 82)])
        pygame.draw.polygon(s, (60, 60, 55), [(100, 64), (109, 79), (91, 79)], 1)
        s.fill((60, 60, 55), (99, 68, 2, 6))
        s.fill((60, 60, 55), (99, 76, 2, 2))
        stencil(s, "BIO-LAB 02", (66, 50), shade(self.wall, 0.55))
        stencil(s, "LEVEL 3 BIOHAZARD", (66, 92), shade(self.wall, 0.65))
        for tx in self.TANKS:
            pygame.draw.line(s, (90, 95, 92), (tx + 15, 0), (tx + 15, 52), 3)
            s.fill((80, 86, 82), (tx - 2, 160, 34, 14))
            s.fill((88, 94, 90), (tx - 2, 52, 34, 10))
            s.fill((40, 50, 44), (tx + 1, 63, 28, 96))
            pygame.draw.rect(s, (140, 160, 150), (tx, 62, 30, 98), 1)
        pygame.draw.polygon(s, (115, 120, 116), [(66, 148), (140, 148), (148, 157), (58, 157)])
        s.fill((85, 90, 86), (58, 157, 90, 4))
        for lx in (62, 144):
            pygame.draw.line(s, (75, 80, 76), (lx, 161), (lx, 182), 2)
        for i, x in enumerate((80, 92, 106)):
            if st["flasks"][i]:
                pygame.draw.polygon(s, (150, 168, 160), [(x - 4, 147), (x + 4, 147), (x + 1, 139),
                                                         (x + 1, 135), (x - 1, 135), (x - 1, 139)])
        s.fill((140, 140, 140), (122, 136, 4, 11))
        s.fill((140, 140, 140), (118, 145, 12, 3))
        s.fill((140, 140, 140), (124, 133, 7, 3))
        pygame.draw.ellipse(s, shade(self.floor, 0.7), (150, 196, 22, 7))
        s.fill((150, 150, 145), (94, 36, 14, 4))

    def lights(self, st, t):
        pulse = 0.72 + 0.06 * math.sin(t * 1.3)
        return [(190, 110, 60, pulse), (230, 110, 60, pulse),
                (100, 115, 100, 0.85 * flicker(t, 22, chance=0.12, low=0.15)), (160, 170, 170, 0.3)]

    def emissive(self, s, st, t, fx):
        c = int(220 * flicker(t, 22, chance=0.12, low=0.15))
        s.fill((c, c, int(c * 0.9)), (96, 39, 10, 1))
        for idx, tx in enumerate(self.TANKS):
            s.fill((60, 155, 100), (tx + 3, 70, 24, 88))
            s.fill((90, 190, 130), (tx + 3, 70, 24, 3))
            frozen = idx == 1 and not st["bubbles"]
            bt = 12.3 if frozen else t
            for k in range(4):
                by = 154 - ((bt * 22 + k * 23) % 82)
                bx = tx + 8 + k * 4 + int(math.sin(by / 6 + k) * 2)
                pygame.draw.circle(s, (190, 255, 215), (bx, int(by)), 1)
            if idx == 0 and st["tank_shape"]:
                bob = math.sin(t * 0.8) * 1.5
                draw_figure(s, tx + 15, 156 + bob, 80, (14, 38, 24))
            pygame.draw.line(s, (170, 235, 200), (tx + 5, 66), (tx + 5, 156))
            fx.glow(s, tx + 15, 110, 40, (22, 55, 32))


class DeconVault(Room):
    cam_id = 3
    name = "DECON VAULT"
    back = (105, 55, 215, 150)
    wall, floor, ceil = (140, 130, 108), (108, 102, 90), (86, 82, 72)
    ambient = 50
    tint = (195, 205, 165)
    base_state = {"helmet": True, "suit": "rack", "window_face": False}
    anomalies = [
        anomaly("helmet", "Hazmat helmet missing", "MISSING", {"helmet": False}, (28, 42, 26, 24), tier=1),
        anomaly("suit", "Hazmat suit standing", "DISPLACEMENT", {"suit": "center"}, (146, 116, 30, 92), tier=2),
        anomaly("window_face", "Face in door window", "INTRUDER", {"window_face": True}, (146, 88, 28, 24), tier=3),
    ]
    NOZZLES = (0.18, 0.42, 0.66, 0.86)
    SUIT = (165, 155, 110)

    def draw(self, s, st, t):
        pygame.draw.line(s, (90, 85, 75), (0, 28), (105, 60), 3)
        pygame.draw.line(s, (90, 85, 75), (LW, 28), (215, 60), 3)
        for f in self.NOZZLES:
            sz = int(6 * (1 - f * 0.6)) + 2
            for x in (lerp(0, 105, f), lerp(LW, 215, f)):
                s.fill((120, 112, 95), (x - sz // 2, lerp(28, 60, f) + 2, sz, sz // 2 + 1))
        pygame.draw.rect(s, (100, 95, 85), (138, 82, 44, 68))
        s.fill((125, 118, 100), (142, 86, 36, 64))
        s.fill((30, 30, 30), (152, 94, 16, 12))
        s.fill((80, 76, 66), (172, 118, 3, 8))
        stencil(s, "DECON 03", (138, 70), shade(self.wall, 0.55))
        hazard_stripes(s, (0, 198, LW, 10))

        pygame.draw.line(s, (80, 76, 66), (24, 64), (56, 72), 2)
        if st["helmet"]:
            pygame.draw.circle(s, (175, 165, 120), (40, 56), 6)
            pygame.draw.ellipse(s, (40, 40, 35), (35, 53, 9, 5))
        pygame.draw.line(s, (80, 76, 66), (22, 80), (58, 88), 2)
        if st["suit"] == "rack":
            draw_figure(s, 40, 178, 92, self.SUIT)
        else:
            draw_figure(s, 161, 206, 84, self.SUIT)
            pygame.draw.ellipse(s, (38, 38, 34), (157, 124, 9, 6))

    def lights(self, st, t):
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        return [(70, 100, 120, 0.7 * flicker(t, 3)), (250, 100, 120, 0.6), (160, 160, 150, 0.5),
                (160, 78, 60, 0.25 + 0.4 * pulse), (160, 100, 18, 0.3)]

    def emissive(self, s, st, t, fx):
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        s.fill((int(255 * pulse), int(150 * pulse), 40), (156, 77, 8, 3))
        fx.glow(s, 160, 78, 16, (int(70 * pulse), int(40 * pulse), 8))

        for i, f in enumerate(self.NOZZLES):
            if int(t * 1.2 + i * 0.8) % 3 == 0:
                for x in (lerp(0, 105, f), lerp(LW, 215, f)):
                    y = lerp(28, 60, f) + 10 + 12 * (1 - f)
                    fx.glow(s, x, y, 14 * (1 - f * 0.5), (55, 50, 40))

        s.fill((52, 60, 52), (152, 94, 16, 12))
        if st["window_face"]:
            pygame.draw.ellipse(s, (5, 6, 5), (156, 95, 8, 11))
            s.fill((5, 6, 5), (153, 103, 14, 3))
            s.fill((210, 210, 195), (158, 99, 1, 1))
            s.fill((210, 210, 195), (161, 99, 1, 1))


class ContainmentGate(Room):
    cam_id = 4
    name = "CONTAINMENT GATE"
    back = (60, 40, 260, 170)
    wall, floor, ceil = (116, 112, 110), (94, 92, 90), (68, 66, 66)
    ambient = 46
    tint = (215, 188, 175)
    base_state = {"beacon": True, "gap": 0, "corner_figure": False}
    anomalies = [
        anomaly("beacon", "Warning beacon dead", "LIGHT", {"beacon": False}, (78, 48, 24, 22), tier=1),
        anomaly("gap", "Containment gate ajar", "DISPLACEMENT", {"gap": 6}, (146, 62, 28, 110), tier=2),
        anomaly("corner_figure", "Figure by the gate", "INTRUDER", {"corner_figure": True}, (232, 90, 30, 96), tier=3),
    ]

    def draw(self, s, st, t):
        pygame.draw.rect(s, (145, 142, 138), (108, 58, 104, 112))
        s.fill((14, 14, 15), (114, 64, 92, 106))
        g = st["gap"]
        leaf = (105, 102, 98)
        s.fill(leaf, (114, 64, 46 - g // 2, 106))
        s.fill(leaf, (160 + g // 2, 64, 46 - g // 2, 106))
        hazard_stripes(s, (114, 66, 46 - g // 2, 9))
        hazard_stripes(s, (160 + g // 2, 66, 46 - g // 2, 9))
        for x in (118, 200):
            for y in range(84, 166, 14):
                pygame.draw.circle(s, (80, 78, 75), (x, y), 1)
        wx, wy = 180 + g // 2, 120
        pygame.draw.circle(s, (85, 82, 78), (wx, wy), 13, 3)
        for a in range(0, 360, 60):
            r = math.radians(a)
            pygame.draw.line(s, (85, 82, 78), (wx, wy), (wx + math.cos(r) * 12, wy + math.sin(r) * 12), 2)
        stencil(s, "CONTAINMENT GATE 04", (112, 46), shade(self.wall, 0.55))
        stencil(s, "AUTHORIZED PERSONNEL ONLY", (66, 150), shade(self.wall, 0.62))
        s.fill((80, 80, 80), (86, 56, 10, 7))
        s.fill((60, 60, 62), (222, 106, 10, 16))
        if st["corner_figure"]:
            draw_figure(s, 246, 184, 88, (14, 13, 13))

    def lights(self, st, t):
        L = [(160, 115, 175, 0.62 * flicker(t, 4))]
        if st["beacon"]:
            pulse = max(0.0, math.sin(t * 1.6 * math.tau)) ** 2
            L.append((91, 60, 120, 0.2 + 0.75 * pulse))
        return L

    def emissive(self, s, st, t, fx):
        if st["beacon"]:
            pulse = max(0.0, math.sin(t * 1.6 * math.tau)) ** 2
            s.fill((int(90 + 165 * pulse), int(20 + 30 * pulse), 20), (87, 57, 8, 5))
            fx.glow(s, 91, 59, 26, (int(130 * pulse), 10, 5))
        else:
            s.fill((45, 10, 10), (87, 57, 8, 5))
        led = (60, 255, 120) if st["gap"] else (255, 50, 40)
        s.fill(led, (226, 109, 2, 2))
        fx.glow(s, 227, 110, 6, shade(led, 0.35))


class CryoVault(Room):
    cam_id = 5
    name = "CRYO VAULT"
    back = (50, 50, 270, 160)
    wall, floor, ceil = (118, 126, 136), (92, 96, 106), (72, 76, 86)
    ambient = 42
    tint = (160, 202, 228)
    base_state = {"bodies": (1, 1, 1), "eyes": -1, "floor_figure": False}
    anomalies = [
        anomaly("pod_empty", "Observer pod 02 empty", "MISSING", {"bodies": (1, 0, 1)}, (138, 66, 44, 104), tier=2),
        anomaly("pod_eyes", "Observer 03 eyes open", "INTRUDER", {"eyes": 2}, (206, 72, 32, 40), tier=2),
        anomaly("floor_figure", "Unidentified figure in vault", "INTRUDER", {"floor_figure": True}, (108, 108, 38, 110), tier=3),
    ]
    PODS = (78, 140, 202)

    def draw(self, s, st, t):
        for px in self.PODS:
            pygame.draw.line(s, (85, 92, 102), (px + 20, 0), (px + 20, 60), 2)
            s.fill((110, 118, 128), (px, 66, 40, 104))
            s.fill((125, 132, 142), (px - 3, 60, 46, 10))
            s.fill((105, 112, 122), (px - 3, 166, 46, 10))
            s.fill((35, 42, 50), (px + 5, 74, 30, 88))
            s.fill((150, 156, 162), (px + 2, 168, 36, 8))
        for i, px in enumerate(self.PODS):
            stencil(s, f"OBS-0{i + 1}", (px + 4, 167), (40, 44, 48))
        stencil(s, "CRYO VAULT 05", (56, 54), shade(self.wall, 0.55))
        stencil(s, "-196 C", (234, 54), shade(self.wall, 0.6))
        if st["floor_figure"]:
            draw_figure(s, 127, 216, 104, (10, 11, 13))

    def lights(self, st, t):
        return [(px + 20, 125, 60, 0.6) for px in self.PODS] + [(160, 165, 170, 0.38)]

    def emissive(self, s, st, t, fx):
        for i, px in enumerate(self.PODS):
            for yy in range(75, 161, 2):
                c = 70 + int(40 * (yy - 75) / 86)
                s.fill((c - 15, c + 55, c + 85), (px + 6, yy, 28, 2))
            if st["bodies"][i]:
                draw_figure(s, px + 20, 158, 78, (18, 32, 42))
                if st["eyes"] == i:
                    for ex, ey in figure_head(px + 20, 158, 78):
                        s.fill((240, 240, 220), (int(ex), int(ey), 1, 1))
            pygame.draw.line(s, (170, 230, 250), (px + 8, 76), (px + 8, 158))
            on = int(t * 1.5 + i) % 4 != 0
            if st["bodies"][i]:
                led = (60, 255, 200) if on else (20, 90, 70)
            else:
                led = (255, 170, 40) if on else (90, 60, 15)
            s.fill(led, (px + 15, 62, 10, 3))
            fx.glow(s, px + 20, 118, 34, (18, 42, 58))
        for k in range(6):
            x = (k * 60 + t * 8) % 360 - 20
            fx.glow(s, x, 198 + (k % 2) * 14, 28, (12, 18, 22))


class QuantumLab(Room):
    cam_id = 6
    name = "QUANTUM LAB"
    back = (70, 35, 250, 165)
    wall, floor, ceil = (118, 112, 128), (90, 86, 98), (70, 66, 78)
    ambient = 46
    tint = (192, 182, 228)
    base_state = {"spin": 1, "core_dark": False, "shadow": False}
    anomalies = [
        anomaly("spin", "Accelerator spinning in reverse", "DISTORTION", {"spin": -1}, (104, 48, 112, 112), tier=1),
        anomaly("core_dark", "Plasma core extinguished", "LIGHT", {"core_dark": True}, (140, 85, 40, 40), tier=1),
        anomaly("shadow", "Shadow on the wall", "INTRUDER", {"shadow": True}, (200, 38, 44, 128), tier=3),
    ]
    C = (160, 105)

    def draw(self, s, st, t):
        if st["shadow"]:
            draw_figure(s, 222, 166, 126, shade(self.wall, 0.42))
        cx, cy = self.C
        pygame.draw.line(s, (60, 58, 70), (135, 150), (124, 186), 4)
        pygame.draw.line(s, (60, 58, 70), (185, 150), (196, 186), 4)
        pygame.draw.circle(s, (66, 62, 76), self.C, 53, 10)
        pygame.draw.circle(s, (150, 145, 165), self.C, 43, 1)
        for k in range(12):
            a = k / 12 * math.tau
            pygame.draw.line(s, (40, 38, 48), (cx + math.cos(a) * 43, cy + math.sin(a) * 43),
                             (cx + math.cos(a) * 53, cy + math.sin(a) * 53))
        pygame.draw.lines(s, (40, 38, 46), False, [(124, 186), (110, 192), (98, 176)], 2)
        pygame.draw.polygon(s, (105, 100, 112), [(78, 150), (118, 150), (122, 162), (74, 162)])
        s.fill((80, 76, 88), (74, 162, 48, 16))
        s.fill((55, 52, 60), (84, 136, 26, 14))
        stencil(s, "Q-ACCELERATOR // EXP-88", (76, 40), shade(self.wall, 0.55))

    def lights(self, st, t):
        L = [(97, 143, 36, 0.5), (160, 165, 170, 0.3)]
        if not st["core_dark"]:
            L.append((160, 105, 150, 0.75 + 0.15 * math.sin(t * 6)))
        return L

    def emissive(self, s, st, t, fx):
        cx, cy = self.C
        for k in range(3):
            a = st["spin"] * t * 1.4 + k * math.tau / 3
            x, y = cx + math.cos(a) * 48, cy + math.sin(a) * 48
            pygame.draw.circle(s, (215, 150, 255), (x, y), 2)
            fx.glow(s, x, y, 10, (40, 20, 60))
        if not st["core_dark"]:
            r = 12 + int(math.sin(t * 5) * 2)
            fx.glow(s, cx, cy, 42, (70, 40, 90))
            pygame.draw.circle(s, (230, 190, 255), self.C, r)
            pygame.draw.circle(s, (255, 245, 255), self.C, r // 2)
        else:
            pygame.draw.circle(s, (3, 2, 5), self.C, 13)
            pygame.draw.circle(s, (90, 12, 18), self.C, 13, 1)
            pygame.draw.circle(s, (int(80 + 60 * math.sin(t * 3)), 10, 10), self.C, 2)
        s.fill((70, 45, 110), (86, 138, 22, 10))
        for k in range(3):
            w = 4 + int(h01(k * 3 + int(t * 4) * 17) * 14)
            s.fill((190, 150, 240), (87, 139 + k * 3, w, 1))


class Substation(Room):
    cam_id = 7
    name = "SUBSTATION"
    back = (80, 45, 240, 160)
    wall, floor, ceil = (126, 120, 100), (98, 95, 84), (74, 72, 62)
    ambient = 48
    tint = (208, 200, 160)
    base_state = {"needle_frozen": False, "sparks_frozen": False, "body": False}
    anomalies = [
        anomaly("needle", "Voltmeter needle frozen", "DISTORTION", {"needle_frozen": True}, (198, 88, 32, 30), tier=1),
        anomaly("sparks", "Discharge suspended in air", "DISTORTION", {"sparks_frozen": True}, (100, 52, 76, 40), tier=2),
        anomaly("body", "Body on the floor", "INTRUDER", {"body": True}, (114, 188, 72, 30), tier=3),
    ]
    INSULATORS = (110, 138, 166)

    def _spark(self, st, t):
        if st["sparks_frozen"]:
            return 77
        k = int(t * 9)
        return k if h01(k * 31 + 5) > 0.72 else None

    def draw(self, s, st, t):
        s.fill((100, 98, 86), (96, 92, 84, 72))
        for x in range(100, 178, 6):
            pygame.draw.line(s, (80, 78, 68), (x, 96), (x, 160))
        s.fill((115, 112, 98), (92, 86, 92, 8))
        for ix in self.INSULATORS:
            for k in range(3):
                s.fill((150, 145, 130), (ix - 3, 74 + k * 4, 6, 3))
            pygame.draw.line(s, (40, 40, 38), (ix, 74), (ix + (ix - 138) // 2, 45))
        pygame.draw.polygon(s, (175, 170, 120), [(206, 56), (217, 74), (195, 74)])
        pygame.draw.line(s, (60, 58, 40), (207, 61), (204, 67), 2)
        pygame.draw.line(s, (60, 58, 40), (204, 67), (208, 70), 2)
        s.fill((95, 92, 84), (196, 88, 36, 44))
        pygame.draw.circle(s, (175, 172, 160), (214, 104), 10)
        for a in range(-140, -30, 22):
            r = math.radians(a)
            pygame.draw.line(s, (70, 68, 60), (214 + math.cos(r) * 8, 104 + math.sin(r) * 8),
                             (214 + math.cos(r) * 10, 104 + math.sin(r) * 10))
        s.fill((90, 88, 78), (196, 136, 36, 20))
        stencil(s, "SUBSTATION 07 // 10kV", (86, 50), shade(self.wall, 0.55))
        s.fill((140, 135, 115), (150, 18, 20, 5))
        if st["body"]:
            draw_lying_figure(s, 150, 204, 74, (14, 13, 12))

    def lights(self, st, t):
        L = [(160, 110, 180, 0.85 * flicker(t, 7, rate=15, chance=0.1, low=0.2))]
        if self._spark(st, t) is not None:
            L.append((138, 72, 70, 0.9))
        return L

    def emissive(self, s, st, t, fx):
        f = flicker(t, 7, rate=15, chance=0.1, low=0.2)
        s.fill((int(255 * f), int(190 * f), int(110 * f)), (152, 20, 16, 2))

        if st["needle_frozen"]:
            a = -1.5
        else:
            a = -1.5 + 0.3 * math.sin(t * 7) + 0.08 * math.sin(t * 31)
        pygame.draw.line(s, (210, 40, 30), (214, 104), (214 + math.cos(a) * 8, 104 + math.sin(a) * 8))

        seed = self._spark(st, t)
        if seed is not None:
            x = 110 + h01(seed * 3) * 56
            pts, y = [], 74
            for k in range(5):
                pts.append((x + (h01(seed * 7 + k) - 0.5) * 10, y))
                y -= 4
            pygame.draw.lines(s, (230, 235, 255), False, pts)
            fx.glow(s, x, 66, 16, (60, 65, 80))
        for k, c in enumerate(((255, 40, 30), (60, 255, 100))):
            if (int(t * 2) + k) % 2:
                s.fill(c, (202 + k * 6, 142, 2, 2))


class DeepPost(Room):
    cam_id = 8
    name = "DEEP POST"
    back = (60, 30, 260, 150)
    wall, floor, ceil = (104, 108, 116), (84, 86, 92), (62, 64, 70)
    ambient = 38
    tint = (165, 186, 218)
    base_state = {"search": True, "hand": False, "sphere": False}
    anomalies = [
        anomaly("search", "Shaft searchlight stopped", "LIGHT", {"search": False}, (90, 52, 140, 76), tier=1),
        anomaly("hand", "Handprint on the glass", "EXTRA", {"hand": True}, (106, 66, 28, 36), tier=2),
        anomaly("sphere", "Mass behind the glass", "INTRUDER", {"sphere": True}, (166, 64, 60, 64), tier=3),
    ]
    PANES = ((90, 52, 68, 76), (162, 52, 68, 76))

    def __init__(self):
        rnd = random.Random(8)
        self.specks = [(rnd.randint(90, 229), rnd.randint(52, 127), rnd.uniform(0.4, 1.0)) for _ in range(170)]

    def _beam(self, st, t):
        a = t * 0.5 if st["search"] else 1.1
        return 160 + math.cos(a) * 55, 90 + math.sin(a * 1.3) * 22

    def draw(self, s, st, t):
        s.fill((120, 124, 132), (82, 44, 156, 92))
        s.fill((0, 0, 0), (90, 52, 140, 76))
        for x in range(86, 236, 12):
            pygame.draw.circle(s, (90, 94, 102), (x, 47), 1)
            pygame.draw.circle(s, (90, 94, 102), (x, 132), 1)
        stencil(s, "DEEP POST 08 // SHAFT -310m", (86, 33), shade(self.wall, 0.55))
        pygame.draw.line(s, (90, 92, 98), (0, 186), (LW, 180), 4)
        pygame.draw.line(s, (90, 92, 98), (0, 207), (LW, 201), 3)
        for x in (30, 120, 210, 300):
            pygame.draw.line(s, (80, 82, 88), (x, 180), (x, LH), 4)

    def lights(self, st, t):
        bx, by = self._beam(st, t)
        return [(160, 120, 175, 0.5 * flicker(t, 8, chance=0.04)), (bx, by, 60, 0.35)]

    def emissive(self, s, st, t, fx):
        for pane in self.PANES:
            s.fill((9, 11, 15), pane)
        fx.glow(s, 125, 112, 30, (6, 8, 10))
        fx.glow(s, 200, 70, 34, (6, 8, 10))
        bx, by = self._beam(st, t)
        for x, y, b in self.specks:
            d = math.hypot(x - bx, y - by)
            if d < 28:
                v = b * (1 - d / 28)
                s.fill((int(120 * v), int(130 * v), int(140 * v)), (x, y, 1, 1))
        fx.glow(s, bx, by, 22, (65, 75, 85))
        pygame.draw.circle(s, (230, 235, 240), (bx, by), 1)

        if st["sphere"]:
            s.set_clip((90, 52, 140, 76))
            draw_entity(s, 196, 96, 27, t * 0.4)
            fx.glow(s, 196, 96, 14, (40, 6, 4))
            s.set_clip(None)
        if st["hand"]:
            col = (58, 66, 72)
            pygame.draw.ellipse(s, col, (114, 82, 12, 13))
            for k, (dx, ln) in enumerate(((-4, 7), (-1, 10), (2, 10), (5, 8))):
                pygame.draw.line(s, col, (120 + dx, 83), (120 + dx * 1.4, 83 - ln))
            pygame.draw.line(s, col, (114, 90), (109, 84))
            for dx in (-3, 0, 3):
                pygame.draw.line(s, (42, 48, 52), (120 + dx, 95), (120 + dx, 104 + abs(dx)))
        s.fill((28, 30, 34), (158, 52, 4, 76))


ROOMS = {room.cam_id: room for room in (Mainframe(), BioLab(), DeconVault(), ContainmentGate(),
                                       CryoVault(), QuantumLab(), Substation(), DeepPost())}
