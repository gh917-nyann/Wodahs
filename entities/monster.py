"""Định nghĩa quái vật thường và hành vi đơn giản.

Mô tả:
    - Quản lý chuyển động, tấn công, va chạm và trạng thái bị chậm.
    - Hỗ trợ AI đơn giản cho patrol, chase và attack.
Author: DGHuy
"""
import pygame
import os
import math

class Monster:
    """Thực thể quái vật với trạng thái patrol, chase và attack."""
    def __init__(self, x, y, m_type="MELEE"):
        """Khởi tạo quái vật cơ bản.

        Input:
        - x (float): Tọa độ X ban đầu.
        - y (float): Tọa độ Y ban đầu.
        - m_type (str): Loại quái "MELEE" hoặc "RANGED".
        Output:
        - Tạo quái với thuộc tính di chuyển, máu, sát thương và hitbox.
        """
        self.x = x
        self.y = y
        self.m_type = m_type 
        self.world_id = 0 
        
        self.speed = 100 
        self.max_health = 300
        self.health = self.max_health
        self.damage = 10
        self.gravity = 1200
        self.vx = self.speed
        self.vy = 0
        
        self.rect = pygame.Rect(self.x, self.y, 32, 32)
        
        self.attack_cooldown = 0.5
        self.current_cooldown = 0
        
        self.on_ground = False
        self.knockback_vx = 0
        self.knockback_timer = 0
        self.is_slowed = False

        self.state = "PATROL"
        self.bounds_calculated = False
        self.patrol_min_x = 0
        self.patrol_max_x = 0
        self.is_attack_locked = False
        
        self.projectiles = []

        self.visual_size = 80
        self.anim_state = "walk"
        self.frame_index = 0
        self.anim_timer = 0
        self.facing_right = True
        self.animations = {'walk': [], 'attack': []}
        self.projectile_image = None
        self.load_animations()

    def load_animations(self):
        """Tải các khung hình animation cho quái vật từ sprite sheet (ảnh dài).

        Input:
        - Không có.
        Output:
        - Khởi tạo danh sách hình ảnh cho các trạng thái walk và attack bằng cách cắt ảnh.
        """
        if self.m_type == "MELEE":
            w_count, a_count = 7, 14
            path_w = "assets/monsters/melee_walk.png"
            path_a = "assets/monsters/melee_attack.png"
        else:
            w_count, a_count = 8, 15
            path_w = "assets/monsters/ranged_walk.png"
            path_a = "assets/monsters/ranged_attack.png"
            
        try:
            sheet_w = pygame.image.load(path_w).convert_alpha()
            frame_w = sheet_w.get_width() // w_count
            frame_h = sheet_w.get_height()
            for i in range(w_count):
                img = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                img.blit(sheet_w, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                self.animations['walk'].append(img)
        except:
            for i in range(w_count):
                img = pygame.Surface((self.visual_size, self.visual_size), pygame.SRCALPHA)
                img.fill((255, 0, 0))
                self.animations['walk'].append(img)
                
        try:
            sheet_a = pygame.image.load(path_a).convert_alpha()
            frame_w = sheet_a.get_width() // a_count
            frame_h = sheet_a.get_height()
            for i in range(a_count):
                img = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                img.blit(sheet_a, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                img = pygame.transform.scale(img, (self.visual_size, self.visual_size))
                self.animations['attack'].append(img)
        except:
            for i in range(a_count):
                img = pygame.Surface((self.visual_size, self.visual_size), pygame.SRCALPHA)
                img.fill((0, 0, 255))
                self.animations['attack'].append(img)
            
        if self.m_type == "RANGED":
            try:
                p_img = pygame.image.load("assets/monsters/arrow.png").convert_alpha()
                self.projectile_image = pygame.transform.scale(p_img, (48, 48))
            except:
                self.projectile_image = pygame.Surface((48, 48), pygame.SRCALPHA)
                pygame.draw.circle(self.projectile_image, (255, 150, 0), (24, 24), 24)

    def take_damage(self, amount, knockback_force=0, knockback_dir=1):
        self.health -= amount
        if knockback_force > 0:
            self.knockback_vx = knockback_force * knockback_dir
            self.knockback_timer = 0.2

    def get_patrol_bounds(self, tiles):
        min_x = self.rect.left
        max_x = self.rect.right
        for step in range(16, 2000, 16):
            check_x = self.rect.left - step
            if any(t.rect.collidepoint(check_x, self.rect.y + 16) for t in tiles if getattr(t, 'is_solid', False)): break
            if not any(t.rect.collidepoint(check_x, self.rect.bottom + 2) for t in tiles if getattr(t, 'is_solid', False)): break
            min_x = check_x
        for step in range(16, 2000, 16):
            check_x = self.rect.right + step
            if any(t.rect.collidepoint(check_x, self.rect.y + 16) for t in tiles if getattr(t, 'is_solid', False)): break
            if not any(t.rect.collidepoint(check_x, self.rect.bottom + 2) for t in tiles if getattr(t, 'is_solid', False)): break
            max_x = check_x
        return min_x, max_x

    def update(self, dt, tiles, player):
        """Cập nhật hành vi, di chuyển và va chạm của quái.

        Input:
        - dt (float): Delta time.
        - tiles (list): Danh sách tile để kiểm tra va chạm.
        - player (Player): Đối tượng player để quyết định hành vi.
        Output:
        - Cập nhật vị trí quái, trạng thái và đạn bắn.
        """
        if self.current_cooldown > 0: self.current_cooldown -= dt

        dx = player.rect.centerx - self.rect.centerx if player else 0
        actual_speed = 30 if self.is_slowed else self.speed

        if self.on_ground and not self.bounds_calculated:
            self.patrol_min_x, self.patrol_max_x = self.get_patrol_bounds(tiles)
            self.bounds_calculated = True

        if not getattr(self, 'is_attack_locked', False):
            if self.bounds_calculated and player:
                in_patrol = (self.patrol_min_x <= player.rect.centerx <= self.patrol_max_x)
                same_floor = abs(player.rect.bottom - self.rect.bottom) <= 32
                
                if in_patrol and same_floor:
                    if self.m_type == "RANGED" and abs(dx) < 250:
                        self.state = "ATTACK"
                        self.is_attack_locked = True
                    elif self.m_type == "MELEE" and (abs(dx) < 45 or self.rect.colliderect(player.rect)):
                        self.state = "ATTACK"
                        self.is_attack_locked = True
                    else:
                        self.state = "CHASE"
                else:
                    self.state = "PATROL"
            else:
                self.state = "PATROL"

        if self.state == "PATROL":
            if self.vx == 0: self.vx = actual_speed
            else: self.vx = actual_speed if self.vx > 0 else -actual_speed
            new_anim = "walk"
        elif self.state == "CHASE":
            self.vx = actual_speed if dx > 0 else -actual_speed
            new_anim = "walk"
        elif self.state == "ATTACK":
            self.vx = 0
            new_anim = "attack"

        if new_anim != self.anim_state:
            self.anim_state = new_anim
            self.frame_index = 0
            self.anim_timer = 0

        if self.vx > 0:
            self.facing_right = True
        elif self.vx < 0:
            self.facing_right = False
        elif self.state == "ATTACK" and player and self.frame_index == 0:
            self.facing_right = player.rect.centerx > self.rect.centerx

        if len(self.animations[self.anim_state]) > 0:
            self.anim_timer += dt
            if self.anim_timer >= 0.1:
                self.anim_timer = 0
                self.frame_index += 1
                
                if self.anim_state == "attack":
                    if self.m_type == "RANGED" and self.frame_index == 9:
                        dir_x = 1 if self.facing_right else -1
                        p_x = self.rect.right if dir_x > 0 else self.rect.left - 16
                        p_y = self.rect.top - 4
                        
                        # LOGIC BẮN THẲNG MỤC TIÊU
                        shoot_vx = 400 * dir_x
                        shoot_vy = 0
                        
                        if player:
                            target_x = player.rect.centerx
                            target_y = player.rect.centery
                            
                            start_x = p_x + 8
                            start_y = p_y + 8
                            
                            angle = math.atan2(target_y - start_y, target_x - start_x)
                            shoot_vx = math.cos(angle) * 450 # 450 là tốc độ bay
                            shoot_vy = math.sin(angle) * 450
                        
                        self.projectiles.append({
                            'rect': pygame.Rect(p_x, p_y, 16, 16),
                            'exact_x': float(p_x), 
                            'exact_y': float(p_y),
                            'vx': shoot_vx,     
                            'vy': shoot_vy,            
                            'timer': 2.0
                        })
                    elif self.m_type == "MELEE" and self.frame_index == 7:
                        if player and self.rect.inflate(40, 0).colliderect(player.rect):
                            player.health -= self.damage
                
                if self.frame_index >= len(self.animations[self.anim_state]):
                    self.frame_index = 0
                    if self.anim_state == "attack":
                        self.is_attack_locked = False
                        self.state = "IDLE"

        current_vx = self.knockback_vx if self.knockback_timer > 0 else self.vx
        if self.knockback_timer > 0: self.knockback_timer -= dt

        for p in self.projectiles[:]:
            p['timer'] -= dt
                        
            p['exact_x'] += p['vx'] * dt
            p['exact_y'] += p['vy'] * dt
            
            p['rect'].x = int(p['exact_x'])
            p['rect'].y = int(p['exact_y'])
            
            if player and p['rect'].colliderect(player.rect):
                player.health -= self.damage
                self.projectiles.remove(p)
                continue
                
            hit_ground = False
            for tile in tiles:
                if getattr(tile, 'is_solid', False) and p['rect'].colliderect(tile.rect):
                    hit_ground = True
                    break
                    
            if hit_ground or p['timer'] <= 0:
                self.projectiles.remove(p)

        if self.on_ground and self.knockback_timer <= 0:
            probe_x = self.rect.right + 2 if current_vx > 0 else self.rect.left - 2
            probe_rect = pygame.Rect(probe_x, self.rect.bottom, 2, 2)
            if not any(probe_rect.colliderect(t.rect) for t in tiles if getattr(t, 'is_solid', False)):
                if self.state == "PATROL": 
                    self.vx *= -1; current_vx = self.vx
                elif self.state in ["CHASE", "ATTACK"]: 
                    self.vx = 0; current_vx = 0

        self.vy += self.gravity * dt
        self.x += current_vx * dt
        self.rect.x = int(self.x)
        
        for tile in tiles:
            if getattr(tile, 'is_solid', False) and self.rect.colliderect(tile.rect):
                if getattr(tile, 'is_one_way', False): continue 
                if current_vx > 0: self.rect.right = tile.rect.left
                elif current_vx < 0: self.rect.left = tile.rect.right
                self.x = self.rect.x
                self.vx *= -1 if self.knockback_timer<=0 else 1
                current_vx = self.vx

        if player and self.rect.colliderect(player.rect):
            if current_vx > 0: self.rect.right = player.rect.left
            elif current_vx < 0: self.rect.left = player.rect.right
            self.x = self.rect.x
            self.vx *= -1 if self.knockback_timer<=0 else 1
            current_vx = self.vx

        self.y += self.vy * dt
        self.rect.y = int(self.y)
        self.on_ground = False
        
        for tile in tiles:
            if getattr(tile, 'is_solid', False) and self.rect.colliderect(tile.rect):
                if getattr(tile, 'is_one_way', False): 
                    if self.vy > 0 and self.rect.bottom - self.vy*dt <= tile.rect.top + 10:
                        self.rect.bottom = tile.rect.top
                        self.on_ground = True; self.y = self.rect.y; self.vy = 0
                else:
                    if self.vy > 0: self.rect.bottom = tile.rect.top; self.on_ground = True
                    elif self.vy < 0: self.rect.top = tile.rect.bottom
                    self.y = self.rect.y; self.vy = 0

        if player and self.rect.colliderect(player.rect):
            if self.vy > 0: self.rect.bottom = player.rect.top; self.on_ground = True
            elif self.vy < 0: self.rect.top = player.rect.bottom
            self.y = self.rect.y; self.vy = 0

    def draw(self, surface):
        """Vẽ quái vật và thanh máu.

        Input:
        - surface (pygame.Surface): Surface để render monster.
        Output:
        - Không trả về, hiển thị hình quái và thanh HP.
        """
        if len(self.animations[self.anim_state]) > 0:
            img = self.animations[self.anim_state][self.frame_index]
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            draw_x = self.rect.x - (self.visual_size - self.rect.width) // 2
            draw_y = self.rect.bottom - self.visual_size
            surface.blit(img, (draw_x, draw_y))
        else:
            color = (150, 0, 0) if self.m_type == "MELEE" else (0, 100, 150)
            pygame.draw.rect(surface, color, self.rect)
        
        for p in self.projectiles:
            if self.projectile_image:
                angle = math.degrees(math.atan2(-p['vy'], p['vx']))
                rotated_img = pygame.transform.rotate(self.projectile_image, angle)
                new_rect = rotated_img.get_rect(center=p['rect'].center)
                surface.blit(rotated_img, new_rect.topleft)
            else:
                pygame.draw.circle(surface, (255, 150, 0), p['rect'].center, 8)
        
        if self.health < self.max_health:
            health_ratio = max(0, self.health / self.max_health)
            bar_width = self.rect.width
            pygame.draw.rect(surface, (100, 100, 100), (self.rect.x, self.rect.y - 10, bar_width, 5))
            pygame.draw.rect(surface, (255, 0, 0), (self.rect.x, self.rect.y - 10, bar_width * health_ratio, 5))

    def draw_silhouette(self, surface):
        """Vẽ phiên bản bóng tối của quái khi ở thế giới khác.

        Input:
        - surface (pygame.Surface): Surface để render silhouette.
        Output:
        - Không trả về, vẽ hình dạng đơn giản của quái.
        """
        if len(self.animations[self.anim_state]) > 0:
            img = self.animations[self.anim_state][self.frame_index].copy()
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            img.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
            draw_x = self.rect.x - (self.visual_size - self.rect.width) // 2
            draw_y = self.rect.bottom - self.visual_size
            surface.blit(img, (draw_x, draw_y))
        else:
            color = (80, 0, 0) if self.m_type == "MELEE" else (0, 50, 80)
            pygame.draw.rect(surface, color, self.rect, 2)
            
        for p in self.projectiles:
            if self.projectile_image:
                angle = math.degrees(math.atan2(-p['vy'], p['vx']))
                p_img = self.projectile_image.copy()
                p_img.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
                rotated_img = pygame.transform.rotate(p_img, angle)
                new_rect = rotated_img.get_rect(center=p['rect'].center)
                surface.blit(rotated_img, new_rect.topleft)
            else:
                pygame.draw.circle(surface, (150, 80, 0), p['rect'].center, 8, 1)