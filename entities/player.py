"""Định nghĩa hành vi và trạng thái của nhân vật người chơi.

Mô tả:
    - Quản lý điều khiển, tấn công, kỹ năng và các vật phẩm.
    - Xử lý va chạm, cập nhật vật lý và giao diện người chơi.
Author: DGHuy
"""
import pygame
import os
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
        
        self.hitbox_w = 32
        self.hitbox_h = 32
        self.rect = pygame.Rect(self.x, self.y, self.hitbox_w, self.hitbox_h)
        
        self.draw_width = 72
        self.draw_height = 72
        
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
        
        self.width = self.hitbox_w
        self.height = self.hitbox_h
        self.animations = {'idle': [], 'walk': [], 'jump': [], 'attack': []}
        self.current_state = 'idle'
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speeds = {
            'idle': 0.2,
            'walk': 0.08,
            'jump': 0.06,
            'attack': 0.04
        }
        self.load_animations()

    def load_animations(self):
        """Tải ảnh sprite sheet, cắt frame, scale to và lưu vào dictionary.

        Mô tả:
        - Tải các file dải ảnh dài uncropped từ image_0.png... image_3.png.
        - Cắt frame, scale tất cả uncropped frames lên self.draw_width x self.draw_height.
        """
        base_path = "assets/player/"
        anim_steps = {'idle': 8, 'walk': 8, 'jump': 13, 'attack': 5}
        
        for state, steps in anim_steps.items():
            file_path = f"{base_path}{state}.png"
            if os.path.exists(file_path):
                sheet = pygame.image.load(file_path).convert_alpha()
                sheet_w, sheet_h = sheet.get_size()
                frame_w = sheet_w // steps
                frame_h = sheet_h
                
                for i in range(steps):
                    frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                    frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                    frame = pygame.transform.scale(frame, (self.draw_width, self.draw_height))
                    self.animations[state].append(frame)

    def update_animation(self, dt):
        if self.attack_freeze > 0:
            new_state = 'attack'
        elif not self.on_ground:
            new_state = 'jump'
        elif self.vx != 0:
            new_state = 'walk'
        else:
            new_state = 'idle'

        if new_state != self.current_state:
            self.current_state = new_state
            self.frame_index = 0
            self.anim_timer = 0

        if len(self.animations[self.current_state]) > 0:
            self.anim_timer += dt
            current_speed = self.anim_speeds.get(self.current_state, 0.1)
            if self.anim_timer >= current_speed:
                self.anim_timer = 0
                self.frame_index += 1
                if self.frame_index >= len(self.animations[self.current_state]):
                    self.frame_index = 0

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
                    if len(self.animations[self.current_state]) > 0:
                        current_img = self.animations[self.current_state][self.frame_index]
                    else:
                        current_img = pygame.Surface((self.draw_width, self.draw_height))                
                    if self.mana >= 50 and not self.shadow_clone.is_active and self.shadow_clone.current_cooldown <= 0:
                        self.shadow_clone.use(self.x, self.y, current_img, self.facing_right)
                        self.mana -= 50
                    elif self.shadow_clone.is_active:
                        self.shadow_clone.use(self.x, self.y, current_img, self.facing_right)
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
                # elif event.key == pygame.K_k:
                #     for monster in monsters:
                #         monster.health = 0

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
        self.update_animation(dt)

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
        
        self.rect.y += 1
        for tile in tiles:
            if getattr(tile, 'is_solid', False) and self.rect.colliderect(tile.rect):
                if not getattr(tile, 'is_one_way', False) or (self.vy >= 0 and self.old_rect.bottom <= tile.rect.top + 10):
                    self.on_ground = True
                    break
        self.rect.y -= 1

    def draw(self, surface):
        """Vẽ player và các hiệu ứng liên quan.

        Input:
        - surface (pygame.Surface): Surface để render player.
        Output:
        - Không trả về, vẽ player, kỹ năng và UI.
        """
        self.shadow_area.draw(surface)

        offset_x = - (self.draw_width - self.hitbox_w) // 2
        offset_y = self.hitbox_h - self.draw_height
        self.shadow_clone.draw(surface, offset_x, offset_y)
        
        current_anim_list = self.animations[self.current_state]
        if len(current_anim_list) > 0:
            img = current_anim_list[self.frame_index]
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            
            draw_x = self.rect.x - (self.draw_width - self.hitbox_w) // 2
            draw_y = self.rect.bottom - self.draw_height
            surface.blit(img, (draw_x, draw_y))
            
        else:
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

        font_key = pygame.font.SysFont(None, 18) 
        font_cd = pygame.font.SysFont(None, 22)
        
        slots = [
            ("Q", "Clone", self.shadow_clone.current_cooldown, self.shadow_clone.cooldown),
            ("E", "Sword", self.shadow_sword.current_cooldown, self.shadow_sword.cooldown),
            ("R", "Area", self.shadow_area.current_cooldown, self.shadow_area.cooldown),
            ("1", "HP", self.health_potion.current_cooldown, self.health_potion.cooldown),
            ("2", "MP", self.mana_potion.current_cooldown, self.mana_potion.cooldown),
            ("3", "Bomb", self.bomb_item.current_cooldown, self.bomb_item.cooldown)
        ]
        
        slot_size = 40  
        spacing = 8     
        
        total_height = len(slots) * (slot_size + spacing) - spacing
        
        start_x = 0 
        start_y = (surface.get_height() - total_height) // 2 
        
        for i, (key, name, cd_current, cd_max) in enumerate(slots):
            x = start_x
            y = start_y + i * (slot_size + spacing)
            
            pygame.draw.rect(surface, (30, 30, 30), (x, y, slot_size, slot_size))
            pygame.draw.rect(surface, (150, 150, 150), (x, y, slot_size, slot_size), 2)
            
            key_text = font_key.render(key, True, (255, 215, 0))
            surface.blit(key_text, (x + 3, y + 3))
            
            name_text = font_key.render(name, True, (200, 200, 200))
            surface.blit(name_text, (x + 3, y + slot_size - 15))
            
            if cd_current > 0:
                cd_ratio = cd_current / cd_max
                overlay_height = int(slot_size * cd_ratio)
                
                s = pygame.Surface((slot_size, overlay_height), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                surface.blit(s, (x, y + (slot_size - overlay_height)))
                
                cd_text = font_cd.render(f"{cd_current:.1f}", True, (255, 100, 100))
                text_rect = cd_text.get_rect(center=(x + slot_size // 2, y + slot_size // 2))
                surface.blit(cd_text, text_rect)

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
