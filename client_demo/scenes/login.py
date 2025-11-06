import pygame
from .scene import BaseScene


class LoginScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.input_active = True
        self.username = ''
        self.input_rect = pygame.Rect(250, 250, 300, 40)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                # go to menu
                if self.manager:
                    self.manager.goto('menu', username=self.username)
            elif event.key == pygame.K_BACKSPACE:
                self.username = self.username[:-1]
            else:
                if len(self.username) < 24:
                    self.username += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_rect.collidepoint(event.pos):
                self.input_active = True
            else:
                self.input_active = False

    def render(self, surface):
        surface.fill((20, 24, 32))
        self.draw_text(surface, 'Login', (400, 120), center=True)
        # input box
        pygame.draw.rect(surface, (255, 255, 255), self.input_rect, 2)
        txt = self.font.render(self.username or 'Enter username (or press Enter for guest)', True, (220, 220, 220))
        surface.blit(txt, (self.input_rect.x + 8, self.input_rect.y + 8))
        self.draw_text(surface, 'Press Enter to continue', (400, 340), center=True)
