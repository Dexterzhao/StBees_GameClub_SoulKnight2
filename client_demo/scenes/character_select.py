import pygame
from .scene import BaseScene


class CharacterSelectScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        # simple demo characters
        self.characters = [
            ('Warrior', 'warrior'),
            ('Mage', 'mage'),
            ('Rogue', 'rogue'),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for idx, (label, cid) in enumerate(self.characters):
                rect = pygame.Rect(250, 180 + idx * 64, 300, 52)
                if rect.collidepoint((mx, my)):
                    # selected a character, go to map selection
                    if self.manager:
                        self.manager.goto('map_select', character=cid, character_label=label, username=getattr(self, 'username', 'Player'))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # back to menu
                if self.manager:
                    self.manager.goto('menu')

    def on_enter(self, **kwargs):
        # receive forwarded username from menu/login
        self.username = kwargs.get('username', 'Player')

    def render(self, surface):
        surface.fill((28, 18, 24))
        self.draw_text(surface, 'Select Your Character', (400, 80), center=True)
        mx, my = pygame.mouse.get_pos()
        for idx, (label, _) in enumerate(self.characters):
            rect = pygame.Rect(250, 180 + idx * 64, 300, 52)
            self.draw_button(surface, rect, label, (mx, my))
        self.draw_text(surface, 'Esc: Back to Menu', (400, 520), center=True)
