import pygame


class BaseScene:
    def __init__(self, screen, save_mgr):
        self.screen = screen
        self.save_mgr = save_mgr
        self.manager = None
        self.font = pygame.font.SysFont(None, 28)
        self.modal = None

    def on_enter(self, **kwargs):
        pass

    def on_exit(self):
        pass

    def handle_event(self, event):
        # route events to modal if present
        if self.modal:
            self.modal.handle_event(event)
            return

    def update(self, dt):
        pass

    def render(self, surface):
        surface.fill((30, 30, 30))
        # if a modal is active, the scene should render underneath and modal will be drawn by manager/scene

    def draw_text(self, surface, text, pos, color=(255, 255, 255), center=False):
        surf = self.font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(surf, rect)

    def draw_button(self, surface, rect, text, mouse_pos):
        # nicer button with subtle shadow and hover
        color = (70, 70, 70)
        hover = rect.collidepoint(mouse_pos)
        if hover:
            color = (120, 120, 120)
        # shadow
        shadow = rect.move(3, 3)
        pygame.draw.rect(surface, (20, 20, 20), shadow, border_radius=6)
        pygame.draw.rect(surface, color, rect, border_radius=6)
        pygame.draw.rect(surface, (200, 200, 200), rect, 2, border_radius=6)
        self.draw_text(surface, text, rect.center, center=True)

    def show_confirm(self, title, message, yes_label='Yes', no_label='No'):
        from ui import ConfirmDialog
        self.modal = ConfirmDialog(self.screen.get_size(), title, message, yes_label, no_label)
        return self.modal

    def show_prompt(self, title, prompt, default_text=''):
        from ui import PromptDialog
        self.modal = PromptDialog(self.screen.get_size(), title, prompt, default_text)
        return self.modal

    def show_options(self, title, options):
        from ui import OptionDialog
        self.modal = OptionDialog(self.screen.get_size(), title, options)
        return self.modal
