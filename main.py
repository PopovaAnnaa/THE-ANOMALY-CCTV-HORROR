import sys
import pygame
from settings import *
from assets import AssetManager
from postfx import CCTVRenderer
from scenes import MenuScene


class App:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        if pygame.mixer.get_init() is None:
            try:
                pygame.mixer.init(22050, -16, 1, 512)
            except pygame.error:
                pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("The Anomaly: CCTV Horror")
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()

        self.assets = AssetManager()
        self.fx = CCTVRenderer()
        self.mouse = (0, 0)
        self.running = True
        self.scene = MenuScene(self)

    def change(self, scene):
        self.scene = scene

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update()
            self.scene.draw(self.screen)
            if pygame.mouse.get_focused():
                self.assets.draw_cursor(self.screen, self.mouse)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    App().run()
