import pygame
from .scene import BaseScene


class SavesScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.items = []

    def on_enter(self, **kwargs):
        self.refresh()

    def refresh(self):
        self.items = self.save_mgr.list_saves()

    def handle_event(self, event):
        if self.modal:
            # modal handling occurs in BaseScene
            if self.modal.result is not None:
                choice = self.modal.result
                # process result from OptionDialog or Confirm/Prompt
                if isinstance(choice, str) and self.selected:
                    if choice == 'Load':
                        data = self.save_mgr.load_save(self.selected['filename'])
                        self.manager.goto('game', save=data)
                    elif choice == 'Rename':
                        # show prompt
                        dlg = self.show_prompt('Rename Save', 'Enter new name (no extension):', default_text=self.selected.get('display',''))
                        # store that we're renaming
                        self._renaming = self.selected
                    elif choice == 'Delete':
                        dlg = self.show_confirm('Delete Save', f"Delete '{self.selected.get('display')}'?", 'Delete', 'Cancel')
                        self._deleting = self.selected
                else:
                    # results from prompt/confirm
                    if hasattr(self, '_renaming') and self.modal.result is not None:
                        newname = self.modal.result
                        if newname:
                            try:
                                new_fn = self.save_mgr.rename_save(self._renaming['filename'], newname)
                            except FileExistsError:
                                # ask to overwrite
                                self.show_confirm('Overwrite?', f"Save '{newname}' exists. Overwrite?", 'Overwrite', 'Cancel')
                                self._overwrite_rename_target = (self._renaming, newname)
                            except Exception:
                                pass
                        self._renaming = None
                        self.modal = None
                    elif hasattr(self, '_overwrite_rename_target') and self.modal.result is not None:
                        # user responded to overwrite prompt
                        ren_info, targetname = self._overwrite_rename_target
                        if self.modal.result is True:
                            # delete existing and rename
                            try:
                                # delete existing target
                                self.save_mgr.delete_save(f"{targetname}.json")
                                # perform rename
                                self.save_mgr.rename_save(ren_info['filename'], targetname)
                                self.refresh()
                            except Exception:
                                pass
                        self._overwrite_rename_target = None
                        self.modal = None
                    elif hasattr(self, '_deleting'):
                        if self.modal.result is True:
                            try:
                                self.save_mgr.delete_save(self._deleting['filename'])
                                self.refresh()
                            except Exception:
                                pass
                        self._deleting = None
                        self.modal = None
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for idx, item in enumerate(self.items):
                rect = pygame.Rect(150, 120 + idx * 48, 500, 40)
                if rect.collidepoint((mx, my)):
                    self.selected = item
                    # show options dialog
                    self.show_options('Save Actions', ['Load', 'Rename', 'Delete', 'Cancel'])
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.goto('menu')

    def render(self, surface):
        surface.fill((40, 20, 20))
        self.draw_text(surface, 'Saves', (400, 48), center=True)
        mx, my = pygame.mouse.get_pos()
        if not self.items:
            self.draw_text(surface, 'No saves found', (400, 300), center=True)
            return
        for idx, item in enumerate(self.items):
            rect = pygame.Rect(150, 120 + idx * 48, 500, 40)
            self.draw_button(surface, rect, f"{item.get('display', item['filename'])} - {item.get('mtime')}", (mx, my))
