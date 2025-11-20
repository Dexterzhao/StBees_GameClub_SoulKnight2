import pygame
from .scene import BaseScene


class MapSelectScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.maps = [
            ('Forest', 'forest'),
            ('Dungeon', 'dungeon'),
            ('Castle', 'castle'),
        ]
        self.selected_character = None

    def on_enter(self, **kwargs):
        # accept character selection passed from previous scene
        self.selected_character = kwargs.get('character')
        self.selected_character_label = kwargs.get('character_label', self.selected_character)
        # keep username forwarded from previous scenes
        self.username = kwargs.get('username', 'Player')

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for idx, (label, mid) in enumerate(self.maps):
                rect = pygame.Rect(200, 160 + idx * 64, 400, 52)
                if rect.collidepoint((mx, my)):
                    # go to game, pass character and map
                    if self.manager:
                        self.manager.goto('game', new=True, character=self.selected_character, character_label=self.selected_character_label, map=mid, map_label=label, username=getattr(self, 'username', 'Player'))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # back to character selection
                if self.manager:
                    self.manager.goto('character_select')

    def render(self, surface):
        surface.fill((12, 24, 36))
        self.draw_text(surface, 'Select Map', (400, 60), center=True)
        self.draw_text(surface, f'Character: {getattr(self, "selected_character_label", "?")}', (400, 100), center=True)
        mx, my = pygame.mouse.get_pos()
        for idx, (label, _) in enumerate(self.maps):
            rect = pygame.Rect(200, 160 + idx * 64, 400, 52)
            self.draw_button(surface, rect, label, (mx, my))
        self.draw_text(surface, 'Esc: Back to Character Select', (400, 520), center=True)
