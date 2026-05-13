"""Định nghĩa hành vi và trạng thái của nhân vật người chơi.

Mô tả:
    - Quản lý điều khiển, tấn công, kỹ năng và các vật phẩm.
    - Xử lý va chạm, cập nhật vật lý và giao diện người chơi.
Author: DGHuy
"""
import pygame
from entities.skill import *
from entities.item import *

class Player:
    """Đối tượng player với di chuyển, kỹ năng và giao diện hiển thị."""
    def __init__(self, x, y):
        """Khởi tạo đối tượng player và các kỹ năng, vật phẩm.

        Input:
        - x (float): Vị trí spawn X.
        - y (float): Vị trí spawn Y.
        Output:
        - Tạo player với máu, mana, tốc độ và kỹ năng ban đầu.
        """
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        self.vx = 0
        self.vy = 0
        self.max_health = 1000
        self.health = 1000
        self.max_mana = 500
        self.mana = 500
        self.jump_times = 0
        self.speed = 280
        self.jump_force = -450
        self.dash_speed = 800
        self.gravity = 1500
        self.facing_right = True
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_duration = 0.15
        self.rect = pygame.Rect(self.x, self.y, 32, 32)
        self.on_ground = False
        self.attack_freeze = 0 
        self.can_dash = True
        
        self.basic_attack = BasicAttack(0.25, 100, 45, 40)
        self.combo_count = 0
        self.combo_timer = 0
        
        self.shadow_clone = ShadowClone(cooldown=8, duration=5, damage=100)
        self.shadow_sword = ShadowSword(cooldown=10, duration=8, damage=60, speed=600)
        self.shadow_area = ShadowArea(cooldown=15, duration=6, radius=150)
        self.in_shadow_area = False

        self.health_potion = HealthPotion(heal_amount=300, cooldown=5)
        self.mana_potion = ManaPotion(restore_amount=200, cooldown=5)
        self.bomb_item = BombItem(cooldown=3, fuse_time=2.0, damage=200, radius=80)

    def inp(self, events, tiles, monsters):
        """Xử lý đầu vào phím và chuột cho player.

        Input:
        - events (list): Danh sách sự kiện Pygame.
        - tiles (list): Danh sách tile để kiểm tra.
        - monsters (list): Danh sách quái vật để tấn công.
        Output:
        - Không trả về, cập nhật trạng thái điều khiển và kỹ năng.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.jump_times < 2:
                        self.move("jump")
                        self.jump_times += 1
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    if self.can_dash:
                        self.move("dash")
                        self.can_dash = False
                elif event.key == pygame.K_q:
                    if self.mana >= 50 and not self.shadow_clone.is_active and self.shadow_clone.current_cooldown <= 0:
                        self.shadow_clone.use(self.x, self.y)
                        self.mana -= 50
                    elif self.shadow_clone.is_active:
                        self.shadow_clone.use(self.x, self.y)
                        self.x = self.shadow_clone.rect.x
                        self.y = self.shadow_clone.rect.y
                elif event.key == pygame.K_e:
                    if self.mana >= 60 and len(self.shadow_sword.swords) == 0 and self.shadow_sword.current_cooldown <= 0:
                        self.shadow_sword.use(self.x, self.y, 0, 0)
                        self.mana -= 60
                elif event.key == pygame.K_r:
                    if self.mana >= 80 and self.shadow_area.current_cooldown <= 0:
                        self.shadow_area.use(self.x, self.y)
                        self.mana -= 80
                elif event.key == pygame.K_1:
                    self.health_potion.use(self)
                elif event.key == pygame.K_2:
                    self.mana_potion.use(self)
                elif event.key == pygame.K_3:
                    self.bomb_item.use(self.x, self.y, self.facing_right)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if len(self.shadow_sword.swords) > 0 and not all(s['fired'] for s in self.shadow_sword.swords):
                        self.shadow_sword.use(self.x, self.y, mouse_x, mouse_y)
                    else:
                        self.perform_attack(monsters)
        
        if not self.is_dashing and self.attack_freeze <= 0:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_d]:
                self.move("right")
            elif keys[pygame.K_a]:
                self.move("left")
            else:
                self.vx = 0

    def perform_attack(self, monsters):
        """Thực hiện đòn đánh cơ bản và tính damage combo.

        Input:
        - monsters (list): Danh sách quái vật để gây sát thương.
        Output:
        - Không trả về, kích hoạt basic attack và cập nhật combo.
        """
        if self.basic_attack.current_cooldown > 0:
            return

        self.attack_freeze = 0.15
        self.combo_timer = 1.5
        
        base_dmg = 100
        if self.in_shadow_area:
            base_dmg = int(base_dmg * 1.5)
            
        if not self.on_ground:
            base_dmg = int(base_dmg * 1.2)
        elif self.is_dashing:
            base_dmg = int(base_dmg * 1.5)
            
        knockback = 0
        self.combo_count += 1
        
        if self.combo_count == 4:
            base_dmg *= 3 
            self.basic_attack.range_x = 100 
            self.combo_count = 0            
            knockback = 600                 
        else:
            self.basic_attack.range_x = 45  
            
        self.basic_attack.damage = base_dmg
        self.basic_attack.use(self.x, self.y, self.facing_right, monsters, knockback)

    def move(self, input_type):
        """Cập nhật vận tốc player theo kiểu di chuyển.

        Input:
        - input_type (str): "left", "right", "jump" hoặc "dash".
        Output:
        - Không trả về, chỉ thay đổi vx, vy và trạng thái di chuyển.
        """
        if input_type == "left":
            self.vx = -self.speed
            self.facing_right = False
        elif input_type == "right":
            self.vx = self.speed
            self.facing_right = True
        elif input_type == "jump":
            self.vy = self.jump_force
            self.on_ground = False
        elif input_type == "dash":
            if not self.is_dashing:
                self.is_dashing = True
                self.dash_timer = self.dash_duration
                self.vx = self.dash_speed if self.facing_right else -self.dash_speed

    def update(self, dt, solid_rects, monsters):
        """Cập nhật vật lý, kỹ năng và va chạm cho player.

        Input:
        - dt (float): Delta time.
        - solid_rects (list): Danh sách tile cứng để kiểm tra va chạm.
        - monsters (list): Danh sách quái vật.
        Output:
        - Không trả về, cập nhật vị trí, trạng thái và kỹ năng.
        """
        self.old_rect = self.rect.copy() 
        if self.y > 690 or self.x < -100 or self.x > 1060:
            self.x = self.spawn_x
            self.y = self.spawn_y
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
            self.vx = 0
            self.vy = 0
            self.clear_active_states()
            
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
                
        self.shadow_clone.update(dt, monsters)
        self.shadow_sword.update(dt, self.x, self.y, solid_rects, monsters)
        self.shadow_area.update(dt, self, monsters)

        if self.mana < self.max_mana:
            self.mana += 10 * dt 

        if self.attack_freeze > 0:
            self.attack_freeze -= dt
            self.vy = 0
        elif self.is_dashing:
            self.dash_timer -= dt
            self.vy = 0
            if self.dash_timer <= 0:
                self.is_dashing = False
        else:
            self.vy += self.gravity * dt

        self.check_collision_x(solid_rects, dt, monsters)
        self.check_collision_y(solid_rects, dt, monsters)
        self.basic_attack.update(dt, self.x, self.y, self.facing_right, monsters)
        self.health_potion.update(dt)
        self.mana_potion.update(dt)
        self.bomb_item.update(dt, monsters, solid_rects)

    def check_collision_x(self, tiles, dt, monsters):
        """Kiểm tra và xử lý va chạm theo trục X.

        Input:
        - tiles (list): Danh sách tile để kiểm tra va chạm.
        - dt (float): Delta time.
        - monsters (list): Danh sách quái vật để xử lý chạm trục X.
        Output:
        - Không trả về, điều chỉnh vị trí x và vx khi va chạm.
        """
        self.x += self.vx * dt
        self.rect.x = int(self.x)
        
        for tile in tiles:
            if hasattr(tile, 'rect') and self.rect.colliderect(tile.rect):
                if getattr(tile, 'is_trap', False):
                    self.health = 0
                    continue

                if getattr(tile, 'is_solid', False):
                    if getattr(tile, 'is_one_way', False):
                        if self.old_rect.right > tile.rect.left and self.old_rect.left < tile.rect.right:
                            continue 

                    if self.vx > 0:
                        self.rect.right = tile.rect.left
                    elif self.vx < 0:
                        self.rect.left = tile.rect.right
                    self.x = self.rect.x
                    self.vx = 0
                
        for monster in monsters:
            if getattr(monster, 'is_boss', False): 
                continue
            if hasattr(monster, 'rect') and self.rect.colliderect(monster.rect):
                if self.vx > 0:
                    self.rect.right = monster.rect.left
                elif self.vx < 0:
                    self.rect.left = monster.rect.right
                self.x = self.rect.x
                self.vx = 0

    def check_collision_y(self, tiles, dt, monsters):
        """Kiểm tra và xử lý va chạm theo trục Y.

        Input:
        - tiles (list): Danh sách tile để kiểm tra va chạm.
        - dt (float): Delta time.
        - monsters (list): Danh sách quái vật để xử lý chạm trục Y.
        Output:
        - Không trả về, điều chỉnh vị trí y và vy khi va chạm.
        """
        self.y += self.vy * dt
        self.rect.y = int(self.y)
        self.on_ground = False
        
        for tile in tiles:
            if hasattr(tile, 'rect') and self.rect.colliderect(tile.rect):
                if getattr(tile, 'is_trap', False):
                    self.health = 0
                    continue

                if getattr(tile, 'is_solid', False):
                    if getattr(tile, 'is_one_way', False):
                        if self.vy > 0 and self.old_rect.bottom <= tile.rect.top + 10:
                            self.rect.bottom = tile.rect.top
                            self.on_ground = True
                            self.jump_times = 0
                            self.can_dash = True
                            if hasattr(tile, 'step_on'): tile.step_on()
                            self.y = self.rect.y
                            self.vy = 0
                    else:
                        if self.vy > 0:
                            self.rect.bottom = tile.rect.top
                            self.on_ground = True
                            self.jump_times = 0
                            self.can_dash = True
                            if hasattr(tile, 'step_on'): tile.step_on()
                        elif self.vy < 0:
                            self.rect.top = tile.rect.bottom
                        self.y = self.rect.y
                        self.vy = 0
                
        for monster in monsters:
            if getattr(monster, 'is_boss', False): 
                continue
            if hasattr(monster, 'rect') and self.rect.colliderect(monster.rect):
                if self.vy > 0:
                    self.rect.bottom = monster.rect.top
                    self.on_ground = True
                    self.jump_times = 0
                    self.can_dash = True
                elif self.vy < 0:
                    self.rect.top = monster.rect.bottom
                self.y = self.rect.y
                self.vy = 0

    def draw(self, surface):
        """Vẽ player và các hiệu ứng liên quan.

        Input:
        - surface (pygame.Surface): Surface để render player.
        Output:
        - Không trả về, vẽ player, kỹ năng và UI.
        """
        self.shadow_area.draw(surface)
        self.shadow_clone.draw(surface)
        
        pygame.draw.rect(surface, (255, 255, 255), self.rect)
        if self.facing_right:
            pygame.draw.circle(surface, (255, 0, 0), (self.rect.right - 8, self.rect.centery), 4)
        else:
            pygame.draw.circle(surface, (255, 0, 0), (self.rect.left + 8, self.rect.centery), 4)
            
        self.shadow_sword.draw(surface)
        if hasattr(self.basic_attack, 'draw'):
            self.basic_attack.draw(surface)
            
        self.draw_ui(surface)
        
    def draw_ui(self, surface):
        """Vẽ thanh HP, MP và combo của player.

        Input:
        - surface (pygame.Surface): Surface để render giao diện.
        Output:
        - Không trả về, vẽ các thanh chỉ số và bom.
        """
        health_ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(surface, (100, 100, 100), (20, 20, 200, 20)) 
        pygame.draw.rect(surface, (255, 0, 0), (20, 20, 200 * health_ratio, 20))
        
        mana_ratio = max(0, self.mana / self.max_mana)
        pygame.draw.rect(surface, (100, 100, 100), (20, 45, 150, 15)) 
        pygame.draw.rect(surface, (0, 100, 255), (20, 45, 150 * mana_ratio, 15))
        
        if self.combo_count > 0:
            font = pygame.font.SysFont(None, 36)
            text = font.render(f"Combo: {self.combo_count}", True, (255, 200, 0))
            surface.blit(text, (20, 70))
        self.bomb_item.draw(surface)

    def clear_active_states(self):
        """Xóa trạng thái kỹ năng đang hoạt động và reset cooldown.

        Input:
        - Không có.
        Output:
        - Không trả về, chỉ reset trạng thái kỹ năng và effect.
        """
        self.basic_attack.active_timer = 0
        self.attack_freeze = 0
        self.combo_count = 0
        self.combo_timer = 0

        if self.shadow_clone.is_active:
            self.shadow_clone.is_active = False
            self.shadow_clone.active_timer = 0
            self.shadow_clone.dash_hitbox = None
            self.shadow_clone.current_cooldown = self.shadow_clone.cooldown

        if len(self.shadow_sword.swords) > 0:
            self.shadow_sword.swords.clear()
            self.shadow_sword.active_timer = 0
            self.shadow_sword.current_cooldown = self.shadow_sword.cooldown

        if self.shadow_area.is_active:
            self.shadow_area.is_active = False
            self.shadow_area.active_timer = 0
            self.shadow_area.current_cooldown = self.shadow_area.cooldown
        self.in_shadow_area = False

        self.bomb_item.active_bombs.clear()