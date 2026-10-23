import pygame

# Налаштування екрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Кольори (RGB)
COLOR_BLACK = (5, 10, 5)
COLOR_GREEN = (0, 255, 60)
COLOR_RED = (255, 50, 50)
COLOR_GRAY = (50, 60, 50)
COLOR_LIGHT_GRAY = (120, 130, 120)
COLOR_WHITE = (240, 240, 240)

# Механіка гри для 5 хвилин геймплею
MAX_ACTIVE_ANOMALIES = 3     # Ліміт аномалій
REQUIRED_WIN_CATCHES = 10    # Кількість зафіксованих аномалій для перемоги
INITIAL_SANITY = 100         # Початковий глузд
SANITY_PENALTY = 15          # Штраф за помилковий клік
SPAWN_INTERVAL_MS = 10000     # Інтервал появи аномалій (6 сек)
LOCKOUT_DURATION_MS = 3000   # Час блокування камери при помилці (3 сек)
EVADE_CHANCE = 0.30          # 30% шанс втечі аномалії при наведенні