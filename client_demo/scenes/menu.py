import pygame
from .scene import BaseScene


class MenuScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.buttons = [
            ('Start New Game', 'start'),
            ('Continue', 'continue'),
            ('View Saves', 'saves'),
            ('Exit', 'exit'),
        ]

    def on_enter(self, **kwargs):
        self.username = kwargs.get('username', 'Guest')

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for idx, (_, name) in enumerate(self.buttons):
                rect = pygame.Rect(300, 200 + idx * 60, 200, 44)
                if rect.collidepoint((mx, my)):
                    if name == 'start':
                        self.manager.goto('game', new=True)
                    elif name == 'continue':
                        latest = self.save_mgr.get_latest_save()
                        if latest:
                            data = self.save_mgr.load_save(latest['filename'])
                            self.manager.goto('game', save=data)
                        else:
                            # no saves: start new
                            self.manager.goto('game', new=True)
                    elif name == 'saves':
                        self.manager.goto('saves')
                    elif name == 'exit':
                        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def render(self, surface):
        surface.fill((18, 18, 40))
        self.draw_text(surface, f'Welcome, {getattr(self, "username", "Guest")}', (400, 120), center=True)
        mx, my = pygame.mouse.get_pos()
        for idx, (label, _) in enumerate(self.buttons):
            rect = pygame.Rect(300, 200 + idx * 60, 200, 44)
            self.draw_button(surface, rect, label, (mx, my))
