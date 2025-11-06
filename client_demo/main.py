import sys
import os
import pygame

from scenes.login import LoginScene
from scenes.menu import MenuScene
from scenes.game import GameScene
from scenes.saves import SavesScene
from save_manager import SaveManager


class SceneManager:
	def __init__(self, screen, fps=60):
		self.screen = screen
		self.clock = pygame.time.Clock()
		self.fps = fps
		self.scenes = {}
		self.current = None

	def register(self, name, scene):
		self.scenes[name] = scene
		scene.manager = self

	def goto(self, name, **kwargs):
		# simple fade transition: fade out current, switch, fade in next
		next_scene = self.scenes.get(name)
		if next_scene is None:
			return

		fade_surf = pygame.Surface(self.screen.get_size()).convert_alpha()
		# fade out
		for a in range(0, 255, 30):
			if self.current:
				try:
					self.current.render(self.screen)
				except Exception:
					self.screen.fill((0, 0, 0))
			fade_surf.fill((0, 0, 0, a))
			self.screen.blit(fade_surf, (0, 0))
			pygame.display.flip()
			self.clock.tick(self.fps)

		if self.current:
			try:
				self.current.on_exit()
			except Exception:
				pass

		self.current = next_scene
		if self.current:
			self.current.on_enter(**kwargs)

		# fade in
		for a in range(255, -1, -30):
			try:
				self.current.render(self.screen)
			except Exception:
				self.screen.fill((0, 0, 0))
			fade_surf.fill((0, 0, 0, a))
			self.screen.blit(fade_surf, (0, 0))
			pygame.display.flip()
			self.clock.tick(self.fps)

	def run(self):
		while True:
			dt = self.clock.tick(self.fps) / 1000.0
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if self.current:
					self.current.handle_event(event)

			if self.current:
				self.current.update(dt)
				self.current.render(self.screen)
				# render modal if present
				if getattr(self.current, 'modal', None):
					try:
						self.current.modal.render(self.screen)
					except Exception:
						pass

			pygame.display.flip()


def main():
	os.environ.setdefault('SDL_VIDEO_CENTERED', '1')
	pygame.init()
	WIDTH, HEIGHT = 800, 600
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption('Pygame Client Framework')

	save_mgr = SaveManager(os.path.join(os.path.dirname(__file__), 'saves'))

	manager = SceneManager(screen)

	# create scenes
	login = LoginScene(screen, save_mgr)
	menu = MenuScene(screen, save_mgr)
	game = GameScene(screen, save_mgr)
	saves = SavesScene(screen, save_mgr)

	manager.register('login', login)
	manager.register('menu', menu)
	manager.register('game', game)
	manager.register('saves', saves)

	manager.goto('login')
	manager.run()


if __name__ == '__main__':
	main()

