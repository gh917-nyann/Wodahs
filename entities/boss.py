"""Quản lý boss chính và hành vi tấn công trong game.

Mô tả:
    - Điều khiển AI boss, trạng thái giận dữ, và đòn tấn công.
    - Tạo đạn, triệu hồi quái và vẽ boss lên màn hình bằng ảnh tĩnh.
    - Cảnh báo chớp đỏ màn hình khi chuyển pha giận dữ.
Author: DGHuy
"""
import pygame
import random
import math
from entities.monster import Monster

class Boss:
    """Thực thể boss với cơ chế di chuyển, tấn công và kích hoạt giận dữ."""
    def __init__(self, x, y):
        """Khởi tạo boss tại vị trí chỉ định.

        Input:
        - x (float): Tọa độ X ban đầu.
        - y (float): Tọa độ Y ban đầu.
        Output:
        - Tạo boss với máu, sát thương, hitbox và hình ảnh tĩnh.
        """
        self.x = x
        self.y = y
        self.world_id = -1 
        self.is_boss = True
        self.is_global = True
        
        self.max_health = 5000
        self.health = self.max_health
        self.damage = 25
        self.speed = 150
        
        self.rect = pygame.Rect(self.x, self.y, 80, 80)
        
        self.state = "IDLE"
        self.is_enraged = False
        self.state_timer = 2.0
        
        self.projectiles = []
        self.dash_vx = 0
        self.dash_vy = 0
        self.is_dashing = False
        
        self.touch_damage_cooldown = 0
        self.touch_damage_delay = 0.5
        
        self.enrage_flash_timer = 0
        
        self.image = None
        self.load_image()

    def load_image(self):
        """Tải ảnh tĩnh cho Boss từ thư mục assets."""
        try:
            img = pygame.image.load("assets/monsters/boss.png").convert_alpha()
            self.image = pygame.transform.scale(img, (self.rect.width, self.rect.height))
        except Exception as e:
            print(f"Lỗi tải ảnh Boss: {e}")
            self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            self.image.fill((0, 0, 0))
            pygame.draw.rect(self.image, (255, 0, 0), self.image.get_rect(), 2)

    def take_damage(self, amount, knockback_force=0, knockback_dir=1):
        """Boss nhận sát thương và kích hoạt trạng thái giận dữ nếu thấp máu.

        Input:
        - amount (int): Số lượng sát thương.
        - knockback_force (int): Lực đẩy lùi khi bị đánh.
        - knockback_dir (int): Hướng đẩy lùi (1 hoặc -1).
        Output:
        - Cập nhật máu boss, tốc độ và trạng thái enraged.
        """
        self.health -= amount
        if self.health < self.max_health * 0.4 and not self.is_enraged:
            self.is_enraged = True
            self.speed *= 1.4
            self.enrage_flash_timer = 1.5

    def spawn_monsters(self, player, all_monsters, current_world):
        """Triệu hồi quái vật hỗ trợ khi boss giận dữ."""
        num_to_spawn = 3 if self.is_enraged else 1
        for _ in range(num_to_spawn):
            spawn_x = player.x + random.randint(-200, 200)
            spawn_y = player.y - 100
            m_type = random.choice(["MELEE", "RANGED"])
            new_m = Monster(spawn_x, spawn_y, m_type=m_type)
            new_m.world_id = current_world
            all_monsters.append(new_m)

    def attack_circle(self):
        """Tạo một vòng đạn quây quanh boss."""
        num_bullets = 16 if self.is_enraged else 8
        for i in range(num_bullets):
            angle = (360 / num_bullets) * i
            rad = math.radians(angle)
            vx = math.cos(rad) * 400
            vy = math.sin(rad) * 400
            self.projectiles.append({
                'rect': pygame.Rect(self.rect.centerx, self.rect.centery, 20, 20),
                'vx': vx,
                'vy': vy,
                'timer': 3.0
            })

    def update(self, dt, player, all_monsters, current_world):
        """Cập nhật hành vi boss, đạn và va chạm với player."""
        if self.touch_damage_cooldown > 0:
            self.touch_damage_cooldown -= dt
            
        # Cập nhật thời gian chớp đỏ
        if self.enrage_flash_timer > 0:
            self.enrage_flash_timer -= dt

        for p in self.projectiles[:]:
            p['timer'] -= dt
            p['rect'].x += p['vx'] * dt
            p['rect'].y += p['vy'] * dt
            if player and p['rect'].colliderect(player.rect):
                player.health -= self.damage
                self.projectiles.remove(p)
                continue
            if p['timer'] <= 0:
                self.projectiles.remove(p)

        self.state_timer -= dt
        
        if self.state == "IDLE":
            if player:
                dx = player.rect.centerx - 40 - self.x
                dy = player.rect.centery - 80 - self.y
                dist = math.hypot(dx, dy)
                if dist > 5:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt

            if self.state_timer <= 0:
                pool = ["CIRCLE", "DASH"]
                if self.is_enraged: pool.append("SUMMON")
                self.state = random.choice(pool)
                self.state_timer = 2.0 if not self.is_enraged else 1.2

        elif self.state == "CIRCLE":
            self.attack_circle()
            self.state = "IDLE"

        elif self.state == "DASH":
            if not self.is_dashing:
                if player:
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        dash_speed = 800 if self.is_enraged else 500
                        self.dash_vx = (dx / dist) * dash_speed
                        self.dash_vy = (dy / dist) * dash_speed
                    else:
                        self.dash_vx = 0
                        self.dash_vy = 0
                self.is_dashing = True
                self.state_timer = 0.8
            else:
                self.x += self.dash_vx * dt
                self.y += self.dash_vy * dt
                if player and self.rect.colliderect(player.rect) and self.touch_damage_cooldown <= 0:
                    player.health -= self.damage * 1.5
                    self.touch_damage_cooldown = self.touch_damage_delay
                    self.is_dashing = False
                    self.state = "IDLE"
                
                if self.state_timer <= 0:
                    self.is_dashing = False
                    self.state = "IDLE"

        elif self.state == "SUMMON":
            if player:
                self.spawn_monsters(player, all_monsters, current_world)
            self.state = "IDLE"

        if self.x < 0: self.x = 0
        if self.x > 880: self.x = 880
        if self.y < 0: self.y = 0
        if self.y > 560: self.y = 560

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if player and self.rect.colliderect(player.rect) and self.touch_damage_cooldown <= 0:
            player.health -= self.damage
            self.touch_damage_cooldown = self.touch_damage_delay

    def draw(self, surface):
        """Vẽ boss, đạn, thanh máu và hiệu ứng toàn màn hình."""
        
        if self.image:
            surface.blit(self.image, self.rect)
        
        for p in self.projectiles:
            p_color = (0, 255, 255) if self.is_enraged else (0, 100, 255)
            pygame.draw.circle(surface, p_color, p['rect'].center, 10)

        health_ratio = max(0, self.health / self.max_health)
        pygame.draw.rect(surface, (50, 50, 50), (280, 20, 400, 20))
        pygame.draw.rect(surface, (255, 0, 0), (280, 20, 400 * health_ratio, 20))

        if self.enrage_flash_timer > 0:
            if int(self.enrage_flash_timer / 0.15) % 2 == 0:
                flash_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
                flash_surface.fill((255, 0, 0, 70)) 
                surface.blit(flash_surface, (0, 0))