import pygame
from .scene import BaseScene


class GameScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.state = {'progress': 0}

    def on_enter(self, **kwargs):
        # kwargs: new (bool) or save (dict)
        if kwargs.get('save'):
            self.state = kwargs['save']
        else:
            if kwargs.get('new'):
                self.state = {'progress': 0}

    def handle_event(self, event):
        # if a modal is active, let BaseScene route events first
        if getattr(self, 'modal', None):
            # if modal has result, handle it
            if self.modal.result is not None:
                res = self.modal.result
                # handle prompt result (save name)
                if isinstance(self.modal, object) and hasattr(self.modal, 'text'):
                    # PromptDialog returned text or None
                    name = res
                    if name:
                        try:
                            self.save_mgr.save_game(self.state, name, overwrite=False)
                            # dismiss modal
                            self.modal = None
                        except FileExistsError:
                            # ask to overwrite
                            dlg = self.show_confirm('Overwrite?', f"Save '{name}' exists. Overwrite?", 'Overwrite', 'Cancel')
                            # wait for that dialog to resolve in subsequent events
                            # store pending name
                            self._pending_save_name = name
                    else:
                        self.modal = None
                else:
                    # Confirm dialogs return True/False
                    if res is True and hasattr(self, '_pending_save_name'):
                        try:
                            self.save_mgr.save_game(self.state, self._pending_save_name, overwrite=True)
                        except Exception:
                            pass
                        self._pending_save_name = None
                        self.modal = None
                    else:
                        # cancel
                        self._pending_save_name = None
                        self.modal = None
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.goto('menu')
            if event.key == pygame.K_s:
                # Ask for a save name via prompt
                self.show_prompt('Save Game', 'Enter save name:', default_text=f'save_{int(pygame.time.get_ticks()/1000)}')

    def update(self, dt):
        # simple progress increment for demo
        self.state['progress'] = self.state.get('progress', 0) + dt * 5

    def render(self, surface):
        surface.fill((10, 40, 10))
        self.draw_text(surface, 'Game Placeholder', (400, 80), center=True)
        self.draw_text(surface, f"Progress: {int(self.state.get('progress',0))}", (400, 140), center=True)
        self.draw_text(surface, 'Press S to save, Esc to return to menu', (400, 520), center=True)
