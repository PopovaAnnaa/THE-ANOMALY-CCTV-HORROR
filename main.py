import pygame
import sys
import math
import random
from settings import *
from assets import AssetManager
from game_logic import AnomalyManager

def draw_menu(screen, assets, mouse_pos):
    """Рендеринг головного меню."""
    time_ms = pygame.time.get_ticks()

    # Заголовок
    title_flicker = random.randint(200, 255) if time_ms % 400 > 350 else 255
    title_text = assets.font_large.render("THE ANOMALY: CCTV HORROR", True, (0, title_flicker, 60))
    subtitle_text = assets.font_main.render("BUNKER CONTAINMENT PROTOCOL v4.02", True, COLOR_GRAY)

    screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 120))
    screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 165))

    # Кнопка START
    start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, 260, 280, 50)
    is_start_hover = start_rect.collidepoint(mouse_pos)
    start_color = COLOR_GREEN if is_start_hover else COLOR_GRAY
    pygame.draw.rect(screen, start_color, start_rect, 2)
    start_txt = assets.font_large.render("> START SYSTEM", True, start_color)
    screen.blit(start_txt, (start_rect.x + 20, start_rect.y + 12))

    # Кнопка EXIT
    exit_rect = pygame.Rect(SCREEN_WIDTH // 2 - 140, 330, 280, 50)
    is_exit_hover = exit_rect.collidepoint(mouse_pos)
    exit_color = COLOR_RED if is_exit_hover else COLOR_GRAY
    pygame.draw.rect(screen, exit_color, exit_rect, 2)
    exit_txt = assets.font_large.render("> SHUTDOWN", True, exit_color)
    screen.blit(exit_txt, (exit_rect.x + 40, exit_rect.y + 12))

    # Інструкція
    info_lines = [
        "CONTROLS:",
        "[LEFT / RIGHT] - Switch Cameras (1-8)",
        "[L-CLICK] - Report Anomaly",
        "GOAL: Contain 5 anomalies before containment fails."
    ]
    for i, line in enumerate(info_lines):
        info_txt = assets.font_main.render(line, True, COLOR_LIGHT_GRAY if i == 0 else COLOR_GRAY)
        screen.blit(info_txt, (SCREEN_WIDTH // 2 - info_txt.get_width() // 2, 430 + i * 24))

    return start_rect, exit_rect

def draw_story(screen, assets):
    """Рендеринг екрана передісторії (білий текст на чорному тлі)."""
    time_ms = pygame.time.get_ticks()

    story_lines = [
        "LOCATION: DEEP CONTAINMENT BUNKER - SECTOR 7",
        "DATE: OCTOBER 24, 2026 / 03:14 AM",
        "",
        "During Quantum Containment Experiment #88, an unidentified",
        "spatial entity breached containment within the subterranean complex.",
        "",
        "The entity lacks physical body, yet distorts reality and alters",
        "surrounding matter whenever it is NOT directly observed.",
        "",
        "You are the sole operator remaining in the control room.",
        "Your task: Monitor all 8 CCTV sectors, report 5 anomalies,",
        "and prevent reality collapse until automated locks engage.",
        "",
        "WARNING: If 3 anomalies accumulate simultaneously, the entity",
        "will notice your observation and break into your station.",
        "",
        "",
        "PRESS [SPACE] OR [ENTER] TO INITIATE MONITORING..."
    ]

    for i, line in enumerate(story_lines):
        # Заголовок робимо світлішим, підказку — миготливою
        if i < 2:
            color = COLOR_GREEN
        elif i == len(story_lines) - 1:
            blink = (time_ms % 800) > 400
            color = COLOR_WHITE if blink else COLOR_GRAY
        else:
            color = COLOR_WHITE

        txt_surf = assets.font_main.render(line, True, color)
        screen.blit(txt_surf, (SCREEN_WIDTH // 2 - txt_surf.get_width() // 2, 50 + i * 26))

def draw_anomaly_sprite(screen, rect):
    """Процедурне малювання паранормальної аномалії."""
    time_ms = pygame.time.get_ticks()
    center_x, center_y = rect.center
    radius = max(rect.width, rect.height) // 2

    # Червона аномальна аура
    pulse = math.sin(time_ms / 120) * 6
    aura_surf = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, (255, 30, 30, 70), (aura_surf.get_width()//2, aura_surf.get_height()//2), int(radius + 10 + pulse))
    screen.blit(aura_surf, (center_x - aura_surf.get_width()//2, center_y - aura_surf.get_height()//2))

    # Темний розрив матерії
    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)
    pygame.draw.ellipse(screen, (5, 5, 10), (rect.x + offset_x, rect.y + offset_y, rect.width, rect.height))

    # Сяюче ядро
    eye_flicker = random.randint(180, 255)
    pygame.draw.circle(screen, (eye_flicker, 20, 20), (center_x + offset_x, center_y + offset_y), max(4, radius // 3))



def draw_enhanced_room(screen, cam_id):
    time_ms = pygame.time.get_ticks()

    # Палітра бункера
    palettes = {
        1: ((12, 20, 28), (20, 28, 38), (80, 180, 255, 18)),  # CAM 01: Mainframe
        2: ((20, 28, 22), (28, 38, 30), (100, 255, 140, 15)),  # CAM 02: Bio-Lab
        3: ((32, 22, 12), (42, 30, 18), (255, 160, 60, 18)),  # CAM 03: Decon
        4: ((28, 12, 12), (38, 18, 18), (255, 40, 40, 25)),  # CAM 04: Gate
        5: ((12, 22, 32), (18, 30, 45), (120, 190, 255, 18)),  # CAM 05: Cryo
        6: ((22, 12, 32), (30, 18, 45), (200, 100, 255, 18)),  # CAM 06: Quantum
        7: ((32, 28, 12), (42, 38, 18), (255, 200, 60, 20)),  # CAM 07: Power
        8: ((8, 12, 18), (12, 18, 28), (90, 140, 200, 12)),  # CAM 08: Deep Post
    }
    wall_color, floor_color, light_color = palettes.get(cam_id, palettes[1])

    # 1. СТІНИ ТА ПІДЛОГА (3D Перспектива)
    pygame.draw.rect(screen, wall_color, (120, 120, 560, 320))
    pygame.draw.polygon(
        screen,
        (wall_color[0] // 1.5, wall_color[1] // 1.5, wall_color[2] // 1.5),
        [(80, 100), (120, 120), (120, 440), (80, 500)],
    )
    pygame.draw.polygon(
        screen,
        (wall_color[0] // 1.5, wall_color[1] // 1.5, wall_color[2] // 1.5),
        [(720, 100), (680, 120), (680, 440), (720, 500)],
    )
    pygame.draw.polygon(
        screen, floor_color, [(120, 440), (680, 440), (720, 500), (80, 500)]
    )

    # 2. ЗАГАЛЬНІ ІНЖЕНЕРНІ ДЕТАЛІ (Написи, кабелі, тріщини)
    # Кабельні траси під стелею
    pygame.draw.line(screen, (15, 15, 20), (80, 115), (720, 115), 4)
    pygame.draw.line(screen, (30, 30, 35), (80, 118), (720, 118), 2)

    # Плитка на підлозі
    for x in range(160, 680, 60):
        pygame.draw.line(
            screen, (10, 15, 15, 100), (x, 440), (x - 25, 500), 1
        )

    # Тріщина на бетоні (декоративна)
    pygame.draw.lines(
        screen,
        (10, 10, 10),
        False,
        [(200, 450), (215, 465), (210, 480), (225, 490)],
        1,
    )

    # 3. ПОСЕКТОРНА ДЕТАЛІЗАЦІЯ
    if cam_id == 1:  # CAM 01: MAINFRAME SECTOR
        # Серверні стійки із захисними решітками
        pygame.draw.rect(screen, (18, 22, 28), (140, 150, 110, 240))
        pygame.draw.rect(screen, (35, 45, 55), (145, 155, 100, 230), 2)
        for y in range(165, 370, 16):
            pygame.draw.line(screen, (45, 55, 70), (150, y), (240, y), 2)
            blink = (time_ms + y * 130) % 400 > 200
            pygame.draw.circle(
                screen,
                (0, 255, 120) if blink else (255, 40, 40),
                (156, y - 2),
                2,
            )

        # Робоча станція з анімованими моніторами
        pygame.draw.rect(screen, (35, 40, 48), (400, 310, 180, 50))  # Стіл
        # Монітор 1 (Анімований текстовий код)
        pygame.draw.rect(screen, (20, 25, 30), (420, 250, 65, 55))
        pygame.draw.rect(screen, (0, 180, 220), (425, 255, 55, 45))
        for line_y in range(260, 295, 6):
            line_w = (time_ms // 100 + line_y * 5) % 40 + 10
            pygame.draw.line(
                screen, (255, 255, 255), (428, line_y), (428 + line_w, line_y), 2
            )

        # Монітор 2 (Графік осцилографа)
        pygame.draw.rect(screen, (20, 25, 30), (495, 250, 65, 55))
        pygame.draw.rect(screen, (0, 200, 100), (500, 255, 55, 45))
        pts = [
            (
                505 + i * 8,
                278 + int(math.sin((time_ms / 150) + i) * 12),
            )
            for i in range(6)
        ]
        pygame.draw.lines(screen, (0, 50, 20), False, pts, 2)

    elif cam_id == 2:  # CAM 02: BIO-LABORATORY
        # Баки з біомасою та анімованими бульбашками
        for bx in (460, 560):
            pygame.draw.rect(screen, (50, 65, 55), (bx, 180, 80, 210))
            pygame.draw.rect(screen, (20, 30, 25), (bx + 8, 195, 64, 180))
            pygame.draw.rect(
                screen, (80, 220, 130, 180), (bx + 12, 210, 56, 160)
            )

            # Бульбашки в рідині
            for i in range(3):
                b_y = 360 - ((time_ms // 10 + i * 50) % 140)
                b_x = bx + 25 + int(math.sin(b_y / 10) * 8)
                pygame.draw.circle(screen, (180, 255, 200), (b_x, b_y), 3, 1)

        # Дослідницький стіл з колбами
        pygame.draw.rect(screen, (60, 70, 65), (150, 310, 140, 50))
        pygame.draw.polygon(
            screen, (0, 200, 255), [(180, 310), (170, 290), (190, 290)]
        )  # Колба
        pygame.draw.rect(screen, (200, 220, 210), (220, 285, 35, 25))  # Мікроскоп

    elif cam_id == 3:  # CAM 03: DECONTAMINATION VAULT
        # Душова система дезактивації
        pygame.draw.rect(screen, (70, 60, 45), (120, 140, 560, 22))
        for fx in range(180, 600, 100):
            pygame.draw.rect(screen, (90, 80, 60), (fx, 162, 30, 18))
            # Пар / Струмінь дезактивації
            if (time_ms + fx) % 800 > 400:
                steam_surf = pygame.Surface((30, 80), pygame.SRCALPHA)
                pygame.draw.polygon(
                    steam_surf,
                    (255, 200, 150, 30),
                    [(15, 0), (0, 80), (30, 80)],
                )
                screen.blit(steam_surf, (fx, 180))

        # Станція захисту
        pygame.draw.rect(screen, (35, 30, 25), (160, 270, 90, 140))
        pygame.draw.circle(screen, (255, 170, 30), (205, 295), 16)  # Шолом
        pygame.draw.rect(screen, (200, 200, 180), (185, 315, 40, 70))

    elif cam_id == 4:  # CAM 04: CONTAINMENT GATE
        # Масивні залізобетонні гермодвері
        pygame.draw.rect(screen, (35, 35, 40), (270, 150, 260, 290))
        pygame.draw.rect(screen, (18, 18, 20), (285, 165, 230, 260))

        # Сигнальні смуги
        for i in range(0, 230, 25):
            pygame.draw.polygon(
                screen,
                (220, 170, 20),
                [(285 + i, 165), (298 + i, 165), (285 + i, 190)],
            )

        # Гідравлічні засуви та масивна шестірня
        pygame.draw.circle(screen, (60, 60, 65), (400, 295), 45)
        pygame.draw.circle(screen, (30, 30, 35), (400, 295), 25)
        # Аварійний маяк на стіні
        beacon_on = (time_ms % 600) < 300
        pygame.draw.circle(
            screen, (255, 30, 30) if beacon_on else (80, 10, 10), (230, 180), 12
        )

    elif cam_id == 5:  # CAM 05: CRYO-STASIS CHAMBER
        # Кріогенні капсули з густим замороженим туманом
        for x_pos in (180, 340, 500):
            pygame.draw.rect(screen, (45, 60, 75), (x_pos, 180, 85, 210))
            pygame.draw.rect(
                screen, (90, 180, 240, 150), (x_pos + 10, 200, 65, 170)
            )

            # Тінь силуету всередині капсули
            pygame.draw.ellipse(
                screen, (20, 35, 45), (x_pos + 25, 230, 35, 100)
            )

            # Індикатор температури (-196°C)
            pygame.draw.rect(screen, (0, 255, 200), (x_pos + 20, 185, 45, 8))

    elif cam_id == 6:  # CAM 06: QUANTUM REACTOR
        # Квантовий прискорювач з обертовими кільцями
        center = (400, 270)
        pygame.draw.circle(screen, (50, 40, 70), center, 100, 18)

        # Обертові елементи
        for angle_offset in (0, 120, 240):
            rad = math.radians((time_ms / 8) + angle_offset)
            rx = center[0] + int(math.cos(rad) * 85)
            ry = center[1] + int(math.sin(rad) * 85)
            pygame.draw.circle(screen, (220, 120, 255), (rx, ry), 10)

        # Сяюче плазмове ядро
        pulse_core = int(math.sin(time_ms / 60) * 10)
        pygame.draw.circle(screen, (240, 180, 255), center, 32 + pulse_core)

    elif cam_id == 7:  # CAM 07: SUBSTATION & GENERATOR
        # Трансформатор високої напруги
        pygame.draw.rect(screen, (65, 60, 35), (260, 190, 220, 200))
        # Вольтметр зі стрелкою, що коливається
        pygame.draw.circle(screen, (220, 220, 200), (370, 240), 22)
        v_angle = math.radians(-45 + math.sin(time_ms / 50) * 30)
        vx = 370 + int(math.cos(v_angle) * 16)
        vy = 240 + int(math.sin(v_angle) * 16)
        pygame.draw.line(screen, (255, 0, 0), (370, 240), (vx, vy), 2)

        # Високовольтні іскри
        if random.randint(0, 10) > 5:
            spk_x = random.randint(280, 420)
            pygame.draw.line(
                screen,
                (255, 255, 180),
                (spk_x, 190),
                (spk_x + random.randint(-15, 15), 160),
                2,
            )

    elif cam_id == 8:  # CAM 08: DEEP OBSERVATION POST
        # Броньоване вікно у безодню
        pygame.draw.rect(screen, (25, 30, 40), (240, 150, 320, 200))
        pygame.draw.rect(screen, (4, 6, 10), (252, 162, 296, 176))

        # Обертовий червоний прожектор у безодні
        light_angle = (time_ms / 20) % 360
        lx = 400 + int(math.cos(math.radians(light_angle)) * 100)
        ly = 250 + int(math.sin(math.radians(light_angle)) * 50)
        pygame.draw.circle(screen, (180, 20, 20), (lx, ly), 6)

    # 4. ДИНАМІЧНЕ ОСВІТЛЕННЯ
    lamp_overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    pygame.draw.polygon(
        lamp_overlay,
        light_color,
        [(400, 100), (90, 500), (710, 500)],
    )
    screen.blit(lamp_overlay, (0, 0))

    # Рамка камери спостереження
    pygame.draw.rect(screen, (0, 255, 60), (80, 100, 640, 400), 2)

def draw_round_anomaly(screen, rect):
    """Повернутий круглий спрайт тіньової аномалії з пульсуючою аурою та ядром."""
    time_ms = pygame.time.get_ticks()
    center_x, center_y = rect.center
    radius = max(rect.width, rect.height) // 2

    # 1. Пульсуюче червоне сяйво (Аура)
    pulse = math.sin(time_ms / 120) * 5
    aura_surf = pygame.Surface((rect.width + 30, rect.height + 30), pygame.SRCALPHA)
    pygame.draw.circle(aura_surf, (255, 30, 30, 75), (aura_surf.get_width() // 2, aura_surf.get_height() // 2), int(radius + 8 + pulse))
    screen.blit(aura_surf, (center_x - aura_surf.get_width() // 2, center_y - aura_surf.get_height() // 2))

    # 2. Тіньове кругле тіло з ефектом легкого тремтіння
    offset_x = random.randint(-1, 1)
    offset_y = random.randint(-1, 1)
    pygame.draw.circle(screen, (5, 5, 10), (center_x + offset_x, center_y + offset_y), radius)

    # 3. Сяюче червоне ядро в центрі
    eye_flicker = random.randint(180, 255)
    pygame.draw.circle(screen, (eye_flicker, 20, 20), (center_x + offset_x, center_y + offset_y), max(3, radius // 2.5))

def draw_static_noise(screen, assets):
    """Ефект білого шуму / поміх при блокуванні системи на 3 секунди."""
    noise_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    noise_surf.fill((10, 15, 10))
    for _ in range(1200):
        nx = random.randint(0, SCREEN_WIDTH)
        ny = random.randint(0, SCREEN_HEIGHT)
        bw = random.randint(100, 255)
        noise_surf.set_at((nx, ny), (bw, bw, bw))
    screen.blit(noise_surf, (0, 0))

    # Напис блокування
    msg = assets.font_large.render("SYSTEM LOCKOUT - REBOOTING SIGNAL...", True, COLOR_RED)
    sub = assets.font_main.render("CAMERA FEED OFFLINE FOR 3 SECONDS", True, COLOR_WHITE)
    screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
    screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 25))

def main():
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("The Anomaly: CCTV Horror")
    clock = pygame.time.Clock()

    assets = AssetManager()
    game = AnomalyManager()

    SPAWN_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL_MS)

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        # Перевірка наведення для механіки ухилення
        if game.state == "PLAYING":
            game.check_hover_evade(mouse_pos, assets)

        # --- ОБРОБКА ПОДІЙ ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game.state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    start_btn, exit_btn = draw_menu(screen, assets, mouse_pos)
                    if start_btn.collidepoint(mouse_pos):
                        assets.sound_catch.play()
                        game.show_story()
                    elif exit_btn.collidepoint(mouse_pos):
                        running = False

            elif game.state == "STORY":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        assets.sound_catch.play()
                        game.start_game()

            elif game.state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_a, pygame.K_LEFT):
                        game.switch_cam(-1, assets)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        game.switch_cam(1, assets)

                if event.type == SPAWN_EVENT:
                    game.spawn_random_anomaly()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    game.handle_click(mouse_pos, assets)

            elif game.state in ("GAMEOVER", "WIN"):
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    game.state = "MENU"

        game.update_status()

        # --- РЕНДЕРИНГ ---
        screen.fill(COLOR_BLACK)

        if game.state == "MENU":
            draw_menu(screen, assets, mouse_pos)
        elif game.state == "STORY":
            draw_story(screen, assets)
        else:
            if game.is_locked:
                # Малювання шуму при блокуванні камери на 3 сек
                draw_static_noise(screen, assets)
            else:
                # Нормальний ігровий процес
                draw_enhanced_room(screen, game.current_cam)

                for a in game.anomalies:
                    if a["cam"] == game.current_cam and a["active"]:
                        draw_round_anomaly(screen, a["rect"])

                # UI
                active_cnt = sum(1 for a in game.anomalies if a["active"])
                txt_cam = assets.font_main.render(f"CAMERA 0{game.current_cam}/0{game.max_cams} [A/D - Switch]", True, COLOR_GREEN)
                txt_stats = assets.font_main.render(f"Reported: {game.caught_count}/{REQUIRED_WIN_CATCHES} | Sanity: {game.sanity}%", True, COLOR_GREEN)
                
                warn_color = COLOR_RED if active_cnt > 1 else COLOR_GREEN
                txt_warn = assets.font_main.render(f"Active Anomalies: {active_cnt}/{MAX_ACTIVE_ANOMALIES}", True, warn_color)

                screen.blit(txt_cam, (20, 20))
                screen.blit(txt_stats, (20, 45))
                screen.blit(txt_warn, (20, 70))

            # Фінальні екрани
            if game.state == "GAMEOVER":
                msg = assets.font_large.render("SUBJECT NOTICED YOU. SIGNAL LOST.", True, COLOR_RED)
                sub_msg = assets.font_main.render("Press any key to return to Main Menu", True, COLOR_WHITE)
                screen.blit(msg, (SCREEN_WIDTH // 2 - 270, SCREEN_HEIGHT // 2 - 20))
                screen.blit(sub_msg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 30))
            elif game.state == "WIN":
                msg = assets.font_large.render("PROTOCOL SUCCESSFUL. ALL ANOMALIES CONTAINED.", True, COLOR_GREEN)
                sub_msg = assets.font_main.render("Press any key to return to Main Menu", True, COLOR_WHITE)
                screen.blit(msg, (SCREEN_WIDTH // 2 - 340, SCREEN_HEIGHT // 2 - 20))
                screen.blit(sub_msg, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 30))

        assets.draw_vhs_overlay(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()