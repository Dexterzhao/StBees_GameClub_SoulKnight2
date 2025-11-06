import pygame
from typing import List, Optional


class Button:
    def __init__(self, rect: pygame.Rect, text: str, callback=None, font=None):
        self.rect = rect
        self.text = text
        self.callback = callback
        self.font = font or pygame.font.SysFont(None, 24)

    def render(self, surface, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        color = (110, 110, 110) if hover else (80, 80, 80)
        shadow = self.rect.move(3, 3)
        pygame.draw.rect(surface, (20, 20, 20), shadow, border_radius=6)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=6)
        txt = self.font.render(self.text, True, (240, 240, 240))
        tr = txt.get_rect(center=self.rect.center)
        surface.blit(txt, tr)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                if callable(self.callback):
                    self.callback()
                return True
        return False


class Modal:
    def __init__(self, surface_size):
        self.surface_size = surface_size
        self.result = None

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def render(self, surface):
        pass


class ConfirmDialog(Modal):
    def __init__(self, surface_size, title: str, message: str, yes_label='Yes', no_label='No'):
        super().__init__(surface_size)
        self.title = title
        self.message = message
        self.yes_label = yes_label
        self.no_label = no_label
        self.font = pygame.font.SysFont(None, 22)
        w, h = surface_size
        self.rect = pygame.Rect(w // 2 - 200, h // 2 - 80, 400, 160)
        self.btn_yes = Button(pygame.Rect(self.rect.x + 40, self.rect.y + 100, 120, 36), yes_label, callback=self._yes, font=self.font)
        self.btn_no = Button(pygame.Rect(self.rect.x + 240, self.rect.y + 100, 120, 36), no_label, callback=self._no, font=self.font)

    def _yes(self):
        self.result = True

    def _no(self):
        self.result = False

    def handle_event(self, event):
        mouse = pygame.mouse.get_pos()
        if self.btn_yes.handle_event(event, mouse):
            return
        if self.btn_no.handle_event(event, mouse):
            return

    def render(self, surface):
        # darken background
        overlay = pygame.Surface(self.surface_size).convert_alpha()
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, (40, 40, 40), self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
        title_s = self.font.render(self.title, True, (255, 255, 255))
        surface.blit(title_s, (self.rect.x + 16, self.rect.y + 12))
        msg_s = self.font.render(self.message, True, (220, 220, 220))
        surface.blit(msg_s, (self.rect.x + 16, self.rect.y + 46))
        mouse = pygame.mouse.get_pos()
        self.btn_yes.render(surface, mouse)
        self.btn_no.render(surface, mouse)


class PromptDialog(Modal):
    def __init__(self, surface_size, title: str, prompt: str, default_text=''):
        super().__init__(surface_size)
        self.title = title
        self.prompt = prompt
        self.font = pygame.font.SysFont(None, 22)
        w, h = surface_size
        self.rect = pygame.Rect(w // 2 - 260, h // 2 - 80, 520, 180)
        self.input_rect = pygame.Rect(self.rect.x + 20, self.rect.y + 64, self.rect.w - 40, 36)
        self.text = default_text
        self.active = True
        self.btn_ok = Button(pygame.Rect(self.rect.x + 140, self.rect.y + 116, 100, 36), 'OK', callback=self._ok, font=self.font)
        self.btn_cancel = Button(pygame.Rect(self.rect.x + 280, self.rect.y + 116, 100, 36), 'Cancel', callback=self._cancel, font=self.font)

    def _ok(self):
        self.result = self.text

    def _cancel(self):
        self.result = None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self._ok()
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(event.unicode) and len(self.text) < 64:
                    self.text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse = pygame.mouse.get_pos()
            if self.btn_ok.handle_event(event, mouse) or self.btn_cancel.handle_event(event, mouse):
                return
            # toggle active if clicked input
            self.active = self.input_rect.collidepoint(pygame.mouse.get_pos())

    def render(self, surface):
        overlay = pygame.Surface(self.surface_size).convert_alpha()
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, (36, 36, 36), self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), self.rect, 2, border_radius=6)
        title_s = self.font.render(self.title, True, (255, 255, 255))
        surface.blit(title_s, (self.rect.x + 12, self.rect.y + 8))
        prompt_s = self.font.render(self.prompt, True, (220, 220, 220))
        surface.blit(prompt_s, (self.rect.x + 12, self.rect.y + 40))
        # input box
        pygame.draw.rect(surface, (255, 255, 255), self.input_rect, 2)
        txt = self.font.render(self.text, True, (240, 240, 240))
        surface.blit(txt, (self.input_rect.x + 8, self.input_rect.y + 6))
        mouse = pygame.mouse.get_pos()
        self.btn_ok.render(surface, mouse)
        self.btn_cancel.render(surface, mouse)


class OptionDialog(Modal):
    def __init__(self, surface_size, title: str, options: List[str]):
        super().__init__(surface_size)
        self.title = title
        self.options = options
        self.font = pygame.font.SysFont(None, 22)
        w, h = surface_size
        wbox = 360
        hbox = 80 + 48 * len(options)
        self.rect = pygame.Rect(w // 2 - wbox // 2, h // 2 - hbox // 2, wbox, hbox)
        self.buttons = []
        for i, opt in enumerate(options):
            btn = Button(pygame.Rect(self.rect.x + 20, self.rect.y + 48 + i * 48, self.rect.w - 40, 36), opt, callback=(lambda o=opt: self._choose(o)), font=self.font)
            self.buttons.append(btn)

    def _choose(self, opt):
        self.result = opt

    def handle_event(self, event):
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            if b.handle_event(event, mouse):
                return

    def render(self, surface):
        overlay = pygame.Surface(self.surface_size).convert_alpha()
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        pygame.draw.rect(surface, (40, 40, 40), self.rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=8)
        title_s = self.font.render(self.title, True, (255, 255, 255))
        surface.blit(title_s, (self.rect.x + 12, self.rect.y + 8))
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            b.render(surface, mouse)
