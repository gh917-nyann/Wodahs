"""Định nghĩa quái vật thường và hành vi đơn giản.

Mô tả:
    - Quản lý chuyển động, tấn công, va chạm và trạng thái bị chậm.
    - Hỗ trợ AI đơn giản cho patrol, chase và attack.
Author: DGHuy
"""
import pygame

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
        self.shoot_timer = 0
        self.shoot_cooldown = 1.5
        
        self.on_ground = False
        self.knockback_vx = 0
        self.knockback_timer = 0
        self.is_slowed = False

        self.state = "PATROL"
        self.bounds_calculated = False
        self.patrol_min_x = 0
        self.patrol_max_x = 0
        
        self.projectiles = []

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
        if self.shoot_timer > 0: self.shoot_timer -= dt

        dx = player.rect.centerx - self.rect.centerx if player else 0
        actual_speed = 30 if self.is_slowed else self.speed

        if self.on_ground and not self.bounds_calculated:
            self.patrol_min_x, self.patrol_max_x = self.get_patrol_bounds(tiles)
            self.bounds_calculated = True

        if self.bounds_calculated and player:
            in_patrol = (self.patrol_min_x <= player.rect.centerx <= self.patrol_max_x)
            same_floor = abs(player.rect.bottom - self.rect.bottom) <= 32
            
            if in_patrol and same_floor:
                if self.m_type == "RANGED" and abs(dx) < 250:
                    self.state = "ATTACK"
                else:
                    self.state = "CHASE"
            else:
                self.state = "PATROL"
        else:
            self.state = "PATROL"

        if self.state == "PATROL":
            if self.vx == 0: self.vx = actual_speed
            else: self.vx = actual_speed if self.vx > 0 else -actual_speed
        elif self.state == "CHASE":
            self.vx = actual_speed if dx > 0 else -actual_speed
        elif self.state == "ATTACK":
            self.vx = 0
            if self.shoot_timer <= 0:
                dir_x = 1 if dx > 0 else -1
                p_x = self.rect.right if dir_x > 0 else self.rect.left - 16
                self.projectiles.append({
                    'rect': pygame.Rect(p_x, self.rect.centery - 8, 16, 16),
                    'vx': 300 * dir_x,
                    'timer': 2.0
                })
                self.shoot_timer = self.shoot_cooldown

        current_vx = self.knockback_vx if self.knockback_timer > 0 else self.vx
        if self.knockback_timer > 0: self.knockback_timer -= dt

        for p in self.projectiles[:]:
            p['timer'] -= dt
            p['rect'].x += p['vx'] * dt
            if player and p['rect'].colliderect(player.rect):
                player.health -= self.damage
                self.projectiles.remove(p)
                continue
            if p['timer'] <= 0:
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
            
            if self.current_cooldown <= 0:
                player.health -= self.damage
                self.current_cooldown = self.attack_cooldown

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
        color = (150, 0, 0) if self.m_type == "MELEE" else (0, 100, 150)
        pygame.draw.rect(surface, color, self.rect) 
        
        for p in self.projectiles:
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
        color = (80, 0, 0) if self.m_type == "MELEE" else (0, 50, 80)
        pygame.draw.rect(surface, color, self.rect, 2) 
        for p in self.projectiles:
            pygame.draw.circle(surface, (150, 80, 0), p['rect'].center, 8, 1)