import math
import random
import pygame
from .scene import BaseScene


class GameScene(BaseScene):
    def __init__(self, screen, save_mgr):
        super().__init__(screen, save_mgr)
        self.state = {'progress': 0}

        # lobby / running
        self.player_count = 1
        self.running = False

        # player controlled entity
        # support for one or two players
        self.players = [
            {'pos': [400.0, 300.0], 'speed': 220.0, 'fire_cooldown': 0.4, 'fire_timer': 0.0, 'hp': 100, 'max_hp': 100, 'weapon_power': 1.0, 'name': 'Player1', 'ult_charge': 0, 'ult_max': 100, 'ult_active': False, 'ult_timer': 0.0},
        ]
        self._move = [
            {'left': False, 'right': False, 'up': False, 'down': False},
        ]

        # enemies (simple moving targets)
        self.enemies = []

        # bullets list: dicts with pos, vel, speed, target (enemy)
        self.bullets = []

        # enemy bullets (purple) fired by enemies toward player
        self.enemy_bullets = []
        # boss/flow control
        self._boss_slain_display = None
        self._post_boss_pause = None
        self._awaiting_next_wave = False

        # limits
        self.max_bullets = 20
        # player firing cooldown (seconds) - controls player's fire rate
        self.player_fire_cooldown = 0.4
        self._player_fire_timer = 0.0
        # visual/effect list (explosions etc.)
        self._effects = []

    def on_enter(self, **kwargs):
        # allow passing player_count from outside
        self.player_count = int(kwargs.get('player_count', self.state.get('player_count', 1)))
        # if a save provided, use it
        if kwargs.get('save'):
            self.state = kwargs['save']

        # start running immediately when entering the game (no waiting screen)
        self.running = True
        # character data
        self.character = kwargs.get('character')
        self.character_label = kwargs.get('character_label', getattr(self, 'character', 'Player'))
        # player display name (from login/menu) — show above player
        self.player_name = kwargs.get('username', getattr(self, 'player_name', 'Player'))
        # 2-player data
        self.players = kwargs.get('players', None) or self.players
        # if players passed as list, initialize their positions and names
        if isinstance(self.players, list) and len(self.players) > 0 and isinstance(self.players[0], dict) and 'character' in self.players[0]:
            # convert incoming players format to internal player dicts
            new_players = []
            new_moves = []
            for i, p in enumerate(self.players):
                pos = [200.0 + i * 400.0, 300.0]
                new_players.append({'pos': pos, 'speed': 220.0, 'fire_cooldown': 0.4, 'fire_timer': 0.0, 'hp': p.get('hp', 100), 'max_hp': p.get('max_hp', 100), 'weapon_power': p.get('weapon_power', 1.0), 'name': p.get('username', f'Player{i+1}'), 'character': p.get('character')} )
                # add ultimate fields
                new_players[-1].update({'ult_charge': 0, 'ult_max': 100, 'ult_active': False, 'ult_timer': 0.0})
                new_moves.append({'left': False, 'right': False, 'up': False, 'down': False})
            self.players = new_players
            self._move = new_moves
        # ensure a convenient reference to the primary player (player 0)
        if isinstance(self.players, list) and len(self.players) > 0:
            self.player = self.players[0]
        else:
            # fallback single-player structure
            self.player = {'pos': [400.0, 300.0], 'hp': 100, 'max_hp': 100}
        # health
        # prefer incoming kwargs, otherwise use primary player's stats
        self.max_hp = int(kwargs.get('max_hp', self.player.get('max_hp', 100)))
        self.hp = int(kwargs.get('hp', self.player.get('hp', self.max_hp)))
        # hurt cooldown (seconds) to avoid instant repeated damage
        self._hurt_cooldown = 0.0
        # death timer after hp <= 0
        self._death_timer = None
        # wave management
        self.wave = int(kwargs.get('wave', 1))
        self._respawn_timer = None
        if self.running:
            self._start_game()

    def _start_game(self):
        # (re)initialize game entities
        self.enemies = []
        self.enemy_bullets = []
        # spawn ~8-12 enemies per wave (keep moderate) and place them in a looser cluster
        # if this wave is a boss wave (every 5th), spawn only the boss
        if self.wave % 5 == 0:
            # create boss
            bx = random.choice([80, 720])
            by = random.uniform(80, 520)
            boss = {
                'pos': [bx, by],
                'vel': [random.uniform(-40.0, 40.0), random.uniform(-40.0, 40.0)],
                'speed': 0.0,
                'is_boss': True,
                'hp': 40 + (self.wave - 1) * 5,  # boss HP increases per wave
                'max_hp': 40 + (self.wave - 1) * 5,
                'phase': 1,
                'fire_timer': 0.8,  # boss fires every 0.8s
                'summon_timer': 20.0,  # boss summons minions every 20s
                'special_timer': 5.0,
            }
            self.enemies.append(boss)
            # if in 2-player mode, spawn a second boss to make encounters harder
            if self.player_count > 1:
                bx2 = random.choice([80, 720])
                by2 = random.uniform(80, 520)
                boss2 = {
                    'pos': [bx2, by2],
                    'vel': [random.uniform(-40.0, 40.0), random.uniform(-40.0, 40.0)],
                    'speed': 0.0,
                    'is_boss': True,
                    'hp': 36 + (self.wave - 1) * 5,
                    'max_hp': 36 + (self.wave - 1) * 5,
                    'phase': 1,
                    'fire_timer': 1.0,
                    'summon_timer': 20.0,
                    'special_timer': 6.0,
                }
                self.enemies.append(boss2)
            # clear player bullets when boss wave starts
            self.bullets = []
            return

        enemy_count = random.randint(8, 12)
        enemy_count += max(0, (self.wave - 1) // 4)

        # spawn as a cluster away from player but with larger spacing so they are not tightly packed
        px, py = self.player['pos']
        cluster_center = None
        for _ in range(16):
            cx = random.uniform(80, 720)
            cy = random.uniform(80, 520)
            if math.hypot(cx - px, cy - py) > 160:
                cluster_center = (cx, cy)
                break
        if cluster_center is None:
            cluster_center = (random.choice([80, 720]), random.uniform(80, 520))

        for i in range(enemy_count):
            # larger offset around center to form a spread-out group
            angle = random.uniform(0, math.pi * 2)
            radius = random.uniform(20, 100)
            cx = cluster_center[0] + math.cos(angle) * radius
            cy = cluster_center[1] + math.sin(angle) * radius
            speed_scale = 1.0 + (self.wave - 1) * 0.03
            e = {
                'pos': [cx, cy],
                'vel': [random.uniform(-24, 24) * speed_scale, random.uniform(-24, 24) * speed_scale],
                'speed': random.uniform(24, 48) * speed_scale,
                # enemy firing cooldown (seconds)
                'fire_timer': random.uniform(1.0, 3.0),
                'hp': 1 + (self.wave - 1) // 3,  # scale enemy HP slowly by wave
            }
            self.enemies.append(e)
        # clear player bullets when new wave starts
        self.bullets = []

    def handle_event(self, event):
        # route modal first
        if getattr(self, 'modal', None):
            if self.modal.result is not None:
                # no special modal handling here
                self.modal = None
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.goto('menu')
            if event.key == pygame.K_a:
                # add simulated player (for testing)
                self.player_count += 1
                if not self.running and self.player_count >= 30:
                    self.running = True
                    self._start_game()
            # single-player fire and movement mapped to player 0
            if event.key == pygame.K_SPACE:
                # fire for player 0
                self._fire_bullet(0)
            # ultimate activation for player 0 (R)
            if event.key == pygame.K_r:
                self._activate_ult(0)
            # movement keys for player 0 (WASD)
            if event.key in (pygame.K_a,):
                self._move[0]['left'] = True
            if event.key in (pygame.K_d,):
                self._move[0]['right'] = True
            if event.key in (pygame.K_w,):
                self._move[0]['up'] = True
            if event.key in (pygame.K_s,):
                self._move[0]['down'] = True
            # second player controls - arrows and RCTRL for fire
            if len(self.players) > 1:
                if event.key == pygame.K_KP_ENTER or event.key == pygame.K_RETURN:
                    # treat Enter as player2 fire
                    self._fire_bullet(1)
                # player2 ultimate activation (Right Ctrl)
                if event.key == pygame.K_RCTRL:
                    self._activate_ult(1)
                if event.key in (pygame.K_LEFT,):
                    self._move[1]['left'] = True
                if event.key in (pygame.K_RIGHT,):
                    self._move[1]['right'] = True
                if event.key in (pygame.K_UP,):
                    self._move[1]['up'] = True
                if event.key in (pygame.K_DOWN,):
                    self._move[1]['down'] = True

        if event.type == pygame.KEYUP:
            # player 0 keys
            if event.key in (pygame.K_a,):
                self._move[0]['left'] = False
            if event.key in (pygame.K_d,):
                self._move[0]['right'] = False
            if event.key in (pygame.K_w,):
                self._move[0]['up'] = False
            if event.key in (pygame.K_s,):
                self._move[0]['down'] = False
            # player 1 keys
            if len(self.players) > 1:
                if event.key in (pygame.K_LEFT,):
                    self._move[1]['left'] = False
                if event.key in (pygame.K_RIGHT,):
                    self._move[1]['right'] = False
                if event.key in (pygame.K_UP,):
                    self._move[1]['up'] = False
                if event.key in (pygame.K_DOWN,):
                    self._move[1]['down'] = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._fire_bullet()

    def _fire_bullet(self, player_idx=0):
        # fire for specific player index
        if player_idx < 0 or player_idx >= len(self.players):
            return
        player = self.players[player_idx]
        # respect per-player fire timer
        if player.get('fire_timer', 0.0) > 0.0:
            return
        # limit bullets
        if len(self.bullets) >= self.max_bullets:
            return
        # create bullet at player position
        bx, by = player['pos']
        b = {
            'pos': [bx, by],
            'vel': [0.0, -1.0],
            'speed': 200.0,  # moderate speed
            'target': self._find_nearest_enemy((bx, by)),
            'owner': player_idx,
        }
        # initialize velocity towards target if exists
        if b['target']:
            tx, ty = b['target']['pos']
            dx, dy = tx - bx, ty - by
            dist = math.hypot(dx, dy) or 1.0
            b['vel'] = [dx / dist, dy / dist]
        else:
            # shoot upward if no target
            b['vel'] = [0.0, -1.0]
        self.bullets.append(b)
        # set cooldown (respect penalty from debuffs if present)
        penalty = player.get('fire_cooldown_penalty', 0.0) if player.get('fire_cooldown_penalty_timer', 0.0) > 0.0 else 0.0
        player['fire_timer'] = player.get('fire_cooldown', 0.4) + penalty

    def _activate_ult(self, player_idx=0):
        # Activate ultimate for a player: spawn radial high-damage bullets
        if player_idx < 0 or player_idx >= len(self.players):
            return
        p = self.players[player_idx]
        if p.get('ult_active'):
            return
        if p.get('ult_charge', 0) < p.get('ult_max', 100):
            return
        # consume charge and activate
        p['ult_charge'] = 0
        p['ult_active'] = True
        p['ult_timer'] = 3.0
        # spawn a radial burst of ult bullets
        px, py = p['pos']
        n = 12
        for i in range(n):
            ang = 2 * math.pi * i / n
            b = {
                'pos': [px, py],
                'vel': [math.cos(ang), math.sin(ang)],
                'speed': 320.0,
                'ult': True,
                'owner': player_idx,
                'target': None,
            }
            self.bullets.append(b)

    def _find_nearest_enemy(self, pos):
        if not self.enemies:
            return None
        bx, by = pos
        best = None
        bestd = float('inf')
        for e in self.enemies:
            ex, ey = e['pos']
            d = (ex - bx) ** 2 + (ey - by) ** 2
            if d < bestd:
                bestd = d
                best = e
        return best

    def _find_nearest_player(self, pos):
        if not self.players:
            return None
        bx, by = pos
        best = None
        bestd = float('inf')
        best_idx = 0
        for i, p in enumerate(self.players):
            px, py = p['pos']
            d = (px - bx) ** 2 + (py - by) ** 2
            if d < bestd:
                bestd = d
                best = p
                best_idx = i
        return best, best_idx

    def update(self, dt):
        # lobby waiting
        if not self.running:
            # small auto-increment for demo (can be removed)
            # self.player_count += dt * 0  # keep stable unless user presses A
            return

        # update player movements for all players
        for idx, p in enumerate(self.players):
            mv = self._move[idx]
            dx = 0
            dy = 0
            if mv.get('left'):
                dx -= 1
            if mv.get('right'):
                dx += 1
            if mv.get('up'):
                dy -= 1
            if mv.get('down'):
                dy += 1
            if dx != 0 or dy != 0:
                mag = math.hypot(dx, dy)
                dx /= mag
                dy /= mag
                p['pos'][0] += dx * p.get('speed', 220.0) * dt
                p['pos'][1] += dy * p.get('speed', 220.0) * dt
                # clamp
                p['pos'][0] = max(8, min(792, p['pos'][0]))
                p['pos'][1] = max(8, min(592, p['pos'][1]))

        # update enemies
        for e in self.enemies:
            e['pos'][0] += e['vel'][0] * dt
            e['pos'][1] += e['vel'][1] * dt
            # bounce on edges
            if e['pos'][0] < 20 or e['pos'][0] > 780:
                e['vel'][0] *= -1
            if e['pos'][1] < 20 or e['pos'][1] > 580:
                e['vel'][1] *= -1
            # enemy firing logic: decrement timer and fire toward player when ready
            if hasattr(self, 'player'):
                e['fire_timer'] = e.get('fire_timer', random.uniform(1.0, 3.0)) - dt
                if e['fire_timer'] <= 0:
                    # boss has different attack behavior
                    if e.get('is_boss'):
                                # boss fires a light-blue larger homing bullet that deals heavy damage
                                bx, by = e['pos']
                                # target nearest player
                                tgt, _ = self._find_nearest_player((bx, by)) or (None, None)
                                if tgt:
                                    px, py = tgt['pos']
                                else:
                                    px, py = self.player['pos']
                                dx = px - bx
                                dy = py - by
                                dist = math.hypot(dx, dy) or 1.0
                                vel = [dx / dist, dy / dist]
                                eb = {
                                    'pos': [bx, by],
                                    'vel': vel,
                                    'speed': 160.0,
                                    'boss_bullet': True,
                                    'homing_time': 1.0,
                                    'size': 8,
                                }
                                self.enemy_bullets.append(eb)
                                e['fire_timer'] = 0.5
                    else:
                        # regular enemy fires a purple bullet toward player
                        bx, by = e['pos']
                        tgt, _ = self._find_nearest_player((bx, by)) or (None, None)
                        if tgt:
                            px, py = tgt['pos']
                        else:
                            px, py = self.player['pos']
                        dx = px - bx
                        dy = py - by
                        dist = math.hypot(dx, dy) or 1.0
                        vel = [dx / dist, dy / dist]
                        eb = {
                            'pos': [bx, by],
                            'vel': vel,
                            'speed': 140.0,
                        }
                        self.enemy_bullets.append(eb)
                        # reset fire timer (slightly randomized)
                        e['fire_timer'] = random.uniform(1.0, 3.0)
                # boss summon handling and special attack
                if e.get('is_boss'):
                    e['summon_timer'] = e.get('summon_timer', 20.0) - dt
                    if e['summon_timer'] <= 0:
                        # summon 5 minions around boss
                        bx, by = e['pos']
                        for i in range(5):
                            angle = random.uniform(0, math.pi * 2)
                            radius = random.uniform(24, 64)
                            mx = bx + math.cos(angle) * radius
                            my = by + math.sin(angle) * radius
                            me = {
                                'pos': [mx, my],
                                'vel': [random.uniform(-24, 24), random.uniform(-24, 24)],
                                'speed': random.uniform(24, 48),
                                'fire_timer': random.uniform(1.0, 3.0),
                                'hp': 1,
                            }
                            self.enemies.append(me)
                        # reset boss summon timer
                        e['summon_timer'] = 20.0
                    # special radial attack every 5 seconds
                    e['special_timer'] = e.get('special_timer', 5.0) - dt
                    if e['special_timer'] <= 0:
                        bx, by = e['pos']
                        tgt, _ = self._find_nearest_player((bx, by)) or (None, None)
                        if tgt:
                            px, py = tgt['pos']
                        else:
                            px, py = self.player['pos']
                        base_ang = math.atan2(py - by, px - bx)
                        n = 8
                        step = 2 * math.pi / n
                        for i in range(n):
                            ang = base_ang + (i - (n - 1) / 2.0) * step
                            vel = [math.cos(ang), math.sin(ang)]
                            # special boss bullet: applies bleed and firing-penalty debuff on hit
                            eb = {
                                'pos': [bx, by],
                                'vel': vel,
                                'speed': 180.0,
                                'boss_bullet': True,
                                'homing_time': 0.0,
                                'size': 10,
                                'special': True,
                                'special_effect': {'bleed_dps': 3.0, 'bleed_time': 3.0, 'cooldown_penalty': 0.25, 'penalty_time': 5.0},
                            }
                            self.enemy_bullets.append(eb)
                        e['special_timer'] = max(3.0, 5.0 - (self.wave - 1) * 0.1)

        # update bullets (homing)
        to_remove = []
        # track enemies removed by collisions to avoid double-processing
        enemies_removed = []
        for bi, b in enumerate(self.bullets):
            target = b.get('target')
            if target and target not in self.enemies:
                # target died or was removed
                b['target'] = self._find_nearest_enemy(b['pos'])
                target = b.get('target')

            if target:
                # homing: steer towards target direction with capped turn
                tx, ty = target['pos']
                bx, by = b['pos']
                desired_dx = tx - bx
                desired_dy = ty - by
                dist = math.hypot(desired_dx, desired_dy) or 1.0
                desired = [desired_dx / dist, desired_dy / dist]
                # current direction
                cvx, cvy = b['vel']
                cmag = math.hypot(cvx, cvy) or 1.0
                cur = [cvx / cmag, cvy / cmag]
                # interpolate direction (simple smoothing)
                steer_strength = 6.0 * dt  # how fast it turns
                new_dir = [cur[0] + (desired[0] - cur[0]) * steer_strength, cur[1] + (desired[1] - cur[1]) * steer_strength]
                nmag = math.hypot(new_dir[0], new_dir[1]) or 1.0
                new_dir = [new_dir[0] / nmag, new_dir[1] / nmag]
                b['vel'] = [new_dir[0], new_dir[1]]
            # advance
            b['pos'][0] += b['vel'][0] * b['speed'] * dt
            b['pos'][1] += b['vel'][1] * b['speed'] * dt

            # check collisions with enemies (player bullets now reduce enemy hp)
            for e in list(self.enemies):
                ex, ey = e['pos']
                bx, by = b['pos']
                if math.hypot(ex - bx, ey - by) < 14:
                    # apply damage to enemy (ult bullets do more damage)
                    owner_idx = b.get('owner')
                    owner_power = 1.0
                    if owner_idx is not None and 0 <= owner_idx < len(self.players):
                        owner_power = self.players[owner_idx].get('weapon_power', 1.0)
                    base_dmg = 5 if b.get('ult') else 1
                    dmg = int(base_dmg * owner_power)
                    e['hp'] = e.get('hp', 1) - dmg
                    if e['hp'] <= 0:
                        # if this was a boss, handle phase transition or killed
                        if e.get('is_boss'):
                            if e.get('phase', 1) == 1:
                                # transition to phase 2
                                e['phase'] = 2
                                # set new (lower) max hp and refill
                                new_max = max(8, int(e.get('max_hp', 40) - 10))
                                e['max_hp'] = new_max
                                e['hp'] = new_max
                                # stop summoning minions
                                e['summon_timer'] = None
                                # special attack now every 3 seconds
                                e['special_timer'] = 3.0
                                # show top-right phase 2 message for 3s
                                self._phase2_msg_timer = 3.0
                                # ensure boss continues alive
                                self._awaiting_next_wave = False
                            else:
                                # boss killed in phase 2 -> slain sequence
                                try:
                                    self.enemies.remove(e)
                                except ValueError:
                                    pass
                                # clear phase message if any
                                self._phase2_msg_timer = None
                                # show slain message for 3s, then pause 5s, then next wave
                                self._boss_slain_display = 3.0
                                self._post_boss_pause = None
                                self.running = False
                                # clear all bullets and enemy bullets
                                self.bullets = []
                                self.enemy_bullets = []
                                # do not spawn next wave until post-boss timers complete
                                self._awaiting_next_wave = True
                                # apply boss-death rewards/effects: restore half hp and boost weapon
                                for p in self.players:
                                    maxhp = p.get('max_hp', 100)
                                    heal = maxhp // 2
                                    p['hp'] = min(maxhp, p.get('hp', 0) + heal)
                                    # boost weapon power
                                    p['weapon_power'] = p.get('weapon_power', 1.0) + 0.5
                                # add a brief explosion effect at boss position
                                self._effects.append({'type': 'explosion', 'pos': list(e['pos']), 'timer': 0.6, 'radius': 8})
                        else:
                            try:
                                self.enemies.remove(e)
                                # award ult charge to the owner of the bullet
                                owner_idx = b.get('owner')
                                if owner_idx is not None and 0 <= owner_idx < len(self.players):
                                    p_owner = self.players[owner_idx]
                                    gain = 20
                                    p_owner['ult_charge'] = min(p_owner.get('ult_max', 100), p_owner.get('ult_charge', 0) + gain)
                            except ValueError:
                                pass
                    # remove bullet on hit
                    to_remove.append(b)
                    break

            # remove bullets out of bounds
            if b['pos'][0] < -10 or b['pos'][0] > 810 or b['pos'][1] < -10 or b['pos'][1] > 610:
                to_remove.append(b)

        # cleanup bullets
        for b in to_remove:
            if b in self.bullets:
                self.bullets.remove(b)

        # update enemy bullets (purple) and check collision with player
        eb_remove = []
        for eb in list(self.enemy_bullets):
            # homing behavior for a short time after spawn
            if eb.get('homing_time', 0.0) > 0.0:
                # steer toward player
                px, py = self.player['pos']
                bx, by = eb['pos']
                desired_dx = px - bx
                desired_dy = py - by
                dist = math.hypot(desired_dx, desired_dy) or 1.0
                desired = [desired_dx / dist, desired_dy / dist]
                cvx, cvy = eb['vel']
                cmag = math.hypot(cvx, cvy) or 1.0
                cur = [cvx / cmag, cvy / cmag]
                steer_strength = 4.0 * dt
                new_dir = [cur[0] + (desired[0] - cur[0]) * steer_strength, cur[1] + (desired[1] - cur[1]) * steer_strength]
                nmag = math.hypot(new_dir[0], new_dir[1]) or 1.0
                new_dir = [new_dir[0] / nmag, new_dir[1] / nmag]
                eb['vel'] = [new_dir[0], new_dir[1]]
                eb['homing_time'] = max(0.0, eb.get('homing_time', 0.0) - dt)

            eb['pos'][0] += eb['vel'][0] * eb['speed'] * dt
            eb['pos'][1] += eb['vel'][1] * eb['speed'] * dt
            bx, by = eb['pos']
            # out of bounds
            if bx < -20 or bx > 820 or by < -20 or by > 620:
                eb_remove.append(eb)
                continue
            # collision with players (support multi-player)
            hit = False
            for i, p in enumerate(self.players):
                px, py = p['pos']
                if math.hypot(px - bx, py - by) < 12:
                    # boss bullets deal heavy damage, regular enemy bullets deal 2 HP
                    dmg = 20 if eb.get('boss_bullet') else 2
                    p['hp'] = max(0, p.get('hp', 0) - dmg)
                    # apply special effect debuff (bleed + fire cooldown penalty)
                    if eb.get('special') and eb.get('special_effect'):
                        eff = eb['special_effect']
                        p['bleed_timer'] = max(p.get('bleed_timer', 0.0), eff.get('bleed_time', 0.0))
                        p['bleed_dps'] = eff.get('bleed_dps', p.get('bleed_dps', 0.0))
                        p['fire_cooldown_penalty_timer'] = max(p.get('fire_cooldown_penalty_timer', 0.0), eff.get('penalty_time', 0.0))
                        p['fire_cooldown_penalty'] = eff.get('cooldown_penalty', p.get('fire_cooldown_penalty', 0.0))
                    # if primary player got hit, keep compatibility fields
                    if i == 0:
                        self.hp = p['hp']
                    eb_remove.append(eb)
                    hit = True
                    break
            if hit:
                continue

        for eb in eb_remove:
            if eb in self.enemy_bullets:
                self.enemy_bullets.remove(eb)

        # update per-player fire timers and debuffs
        for p in self.players:
            if p.get('fire_timer', 0.0) > 0.0:
                p['fire_timer'] = max(0.0, p['fire_timer'] - dt)
            # update ult timers
            if p.get('ult_active'):
                p['ult_timer'] = max(0.0, p.get('ult_timer', 0.0) - dt)
                if p['ult_timer'] <= 0.0:
                    p['ult_active'] = False
            # bleed damage over time
            if p.get('bleed_timer', 0.0) > 0.0:
                bleed_dps = p.get('bleed_dps', 0.0)
                if bleed_dps:
                    p['hp'] = max(0, p.get('hp', 0) - bleed_dps * dt)
                    if p is self.player:
                        self.hp = p['hp']
                p['bleed_timer'] = max(0.0, p.get('bleed_timer', 0.0) - dt)
            # cooldown penalty timer
            if p.get('fire_cooldown_penalty_timer', 0.0) > 0.0:
                p['fire_cooldown_penalty_timer'] = max(0.0, p.get('fire_cooldown_penalty_timer', 0.0) - dt)
                if p['fire_cooldown_penalty_timer'] <= 0.0:
                    p['fire_cooldown_penalty'] = 0.0

        # update hurt cooldown
        if self._hurt_cooldown > 0:
            self._hurt_cooldown = max(0.0, self._hurt_cooldown - dt)

        # check collisions between enemies and players (support multi-player)
        if self.running:
            for i, p in enumerate(self.players):
                if p.get('hp', 0) <= 0:
                    continue
                px, py = p['pos']
                for e in list(self.enemies):
                    ex, ey = e['pos']
                    if math.hypot(ex - px, ey - py) < 20:
                        # collision
                        if self._hurt_cooldown <= 0.0:
                            dmg = 10
                            p['hp'] = max(0, p.get('hp', 0) - dmg)
                            self._hurt_cooldown = 1.0
                            # remove the enemy on collision to avoid repeated hits
                            try:
                                self.enemies.remove(e)
                            except ValueError:
                                pass
                            # simple knockback applied to the collided player
                            dx = px - ex
                            dy = py - ey
                            mag = math.hypot(dx, dy) or 1.0
                            p['pos'][0] += (dx / mag) * 10
                            p['pos'][1] += (dy / mag) * 10
                            # clamp
                            p['pos'][0] = max(8, min(792, p['pos'][0]))
                            p['pos'][1] = max(8, min(592, p['pos'][1]))
                            # keep primary player hp in sync
                            if i == 0:
                                self.hp = p['hp']
                        # break so we process one collision per frame for this player
                        break

        # if player died, start death timer and stop running
        if self.hp <= 0 and self._death_timer is None:
            self._death_timer = 1.5
            self.running = False

        # if boss was slain earlier and awaiting pause, handle timers
        if self._boss_slain_display is not None:
            # still showing slain message
            self._boss_slain_display -= dt
            if self._boss_slain_display <= 0:
                # start post-boss pause
                self._post_boss_pause = 5.0
                self._boss_slain_display = None
            return
        if self._post_boss_pause is not None:
            self._post_boss_pause -= dt
            if self._post_boss_pause <= 0:
                # resume next wave
                self._post_boss_pause = None
                self.wave += 1
                self._start_game()
                self.running = True
            return

        # phase 2 message timer handling (show top-right message)
        if getattr(self, '_phase2_msg_timer', None) is not None:
            self._phase2_msg_timer = max(0.0, self._phase2_msg_timer - dt)

        # if all enemies dead and not in boss pause, immediately spawn next wave
        if not self.enemies and not self._awaiting_next_wave:
            self.wave += 1
            self._start_game()

        # update effect timers
        for eff in list(self._effects):
            eff['timer'] = max(0.0, eff['timer'] - dt)
            if eff['timer'] <= 0:
                self._effects.remove(eff)

    def render(self, surface):
        if not self.running:
            surface.fill((30, 30, 40))
            # if death timer active, show death message
            if self._death_timer is not None:
                self.draw_text(surface, 'You Died! Returning to menu...', (400, 240), center=True)
            else:
                self.draw_text(surface, 'Waiting for players to join...', (400, 220), center=True)
                self.draw_text(surface, f'Players: {self.player_count}/30  (press A to add simulated player)', (400, 260), center=True)
                self.draw_text(surface, 'Esc: Back to Menu', (400, 520), center=True)
            return

        surface.fill((10, 40, 10))
        # draw players (support split-screen players list)
        for idx, p in enumerate(self.players):
            px, py = p['pos']
            color = (50, 160, 220) if idx == 0 else (80, 200, 120)
            pygame.draw.circle(surface, color, (int(px), int(py)), 12)
            # draw player name and hp bar above player
            name = p.get('name', f'Player{idx+1}')
            name_surf = self.font.render(name, True, (255, 255, 255))
            nsr = name_surf.get_rect(center=(int(px), int(py) - 26))
            surface.blit(name_surf, nsr)
            # hp bar
            bar_w = 60
            bar_h = 8
            hp = p.get('hp', 100)
            maxhp = p.get('max_hp', 100)
            hp_frac = max(0.0, min(1.0, float(hp) / float(maxhp)))
            bar_x = int(px - bar_w/2)
            bar_y = int(py - 16)
            pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (180, 30, 30), (bar_x + 1, bar_y + 1, int((bar_w - 2) * hp_frac), bar_h - 2))
            # ult meter under hp bar
            ult_w = 60
            ult_h = 6
            ult_frac = max(0.0, min(1.0, float(p.get('ult_charge', 0)) / float(p.get('ult_max', 100))))
            ult_x = int(px - ult_w/2)
            ult_y = int(py - 6)
            pygame.draw.rect(surface, (30, 30, 30), (ult_x, ult_y, ult_w, ult_h))
            pygame.draw.rect(surface, (60, 200, 220), (ult_x + 1, ult_y + 1, int((ult_w - 2) * ult_frac), ult_h - 2))
            if p.get('ult_active'):
                self.draw_text(surface, 'ULT!', (px, py - 36))

        # draw enemies
        for e in self.enemies:
            ex, ey = int(e['pos'][0]), int(e['pos'][1])
            if e.get('is_boss'):
                # draw boss as a larger purple ball
                pygame.draw.circle(surface, (140, 40, 160), (ex, ey), 26)
                # draw 'BOSS' text above boss
                boss_label = self.font.render('BOSS', True, (255, 40, 40))
                blr = boss_label.get_rect(center=(ex, ey - 52))
                surface.blit(boss_label, blr)
                # boss hp bar above boss
                boss_hp = e.get('hp', 0)
                boss_max = e.get('max_hp', e.get('hp', 1))
                frac = max(0.0, min(1.0, float(boss_hp) / float(boss_max)))
                bw = 100
                bh = 10
                bx = ex - bw // 2
                by = ey - 36
                pygame.draw.rect(surface, (40, 40, 40), (bx, by, bw, bh))
                pygame.draw.rect(surface, (200, 50, 200), (bx + 2, by + 2, int((bw - 4) * frac), bh - 4))
            else:
                pygame.draw.circle(surface, (200, 60, 60), (ex, ey), 10)

        # draw enemy bullets (purple)
        for eb in self.enemy_bullets:
            ebx, eby = int(eb['pos'][0]), int(eb['pos'][1])
            # boss bullets are larger and light-blue, regular enemy bullets are purple
            if eb.get('boss_bullet'):
                pygame.draw.circle(surface, (160, 200, 255), (ebx, eby), 8)
            else:
                pygame.draw.circle(surface, (160, 40, 200), (ebx, eby), 4)

        # draw bullets
        for b in self.bullets:
            bx, by = int(b['pos'][0]), int(b['pos'][1])
            pygame.draw.circle(surface, (240, 220, 80), (bx, by), 5)

        # draw effects (explosions)
        for eff in self._effects:
            if eff['type'] == 'explosion':
                ex, ey = int(eff['pos'][0]), int(eff['pos'][1])
                # simple radial blast visual with fading
                alpha_frac = max(0.0, eff['timer'] / 0.6)
                # draw expanding rings
                for ring_idx in range(1, 6):
                    ring_size = ring_idx * 10
                    pygame.draw.circle(surface, (255, max(0, 200 - ring_idx * 40), 0), (ex, ey), ring_size, 2)

        # HUD - top left
        self.draw_text(surface, f'Player: {self.player_name}  HP: {self.hp}/{self.max_hp}', (14, 8))
        self.draw_text(surface, f'Wave: {self.wave}  Players: {self.player_count}  Enemies: {len(self.enemies)}  Bullets: {len(self.bullets)}', (14, 28))
        self.draw_text(surface, 'Move: WASD/Arrows  Fire: Space / Mouse Click', (400, 560), center=True)
