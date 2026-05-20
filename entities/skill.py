"""
Chức năng chính: Xử lý toàn bộ kỹ năng chiến đấu của player.
Author: DGHuy

Chi tiết:
    - Quản lý kỹ năng cận chiến, phân thân, kiếm bay và vùng hiệu ứng.
    - Theo dõi cooldown, thời gian tồn tại và trạng thái kích hoạt.
    - Xử lý hitbox, va chạm và sát thương lên quái vật.
    - Cập nhật hiệu ứng buff/debuff và render kỹ năng lên màn hình.
"""
import pygame
import math

class BasicAttack:
    """
    Chức năng: Đòn đánh cận chiến cơ bản của player.

    Chi tiết:
        - Tạo hitbox phía trước player.
        - Kiểm tra va chạm với quái vật.
        - Gây sát thương và knockback.
        - Ngăn một quái nhận damage nhiều lần trong cùng đòn đánh.
    """
    def __init__(self, cooldown, damage, range_x, range_y):
        """
        Chức năng: Khởi tạo đòn đánh cơ bản.

        Input:
        - cooldown (float): Thời gian hồi chiêu.
        - damage (int): Sát thương gây ra.
        - range_x (int): Độ rộng hitbox.
        - range_y (int): Độ cao hitbox.
        """
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.damage = damage
        self.range_x = range_x
        self.range_y = range_y
        self.active_timer = 0
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.monsters_hit = []
        self.current_knockback = 0

    def use(self, player_x, player_y, facing_right, monsters, knockback=0):
        """
        Chức năng: Kích hoạt đòn đánh nếu đã hết cooldown.

        Input:
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        - facing_right (bool): Hướng nhìn của player.
        - monsters (list): Danh sách quái vật.
        - knockback (int): Lực đẩy lùi.
        """
        if self.current_cooldown <= 0:
            self.active_timer = 0.1
            self.current_cooldown = self.cooldown
            self.monsters_hit.clear()
            self.current_knockback = knockback
            self.update_hitbox(player_x, player_y, facing_right)
            self.check_hit(monsters, facing_right)

    def update_hitbox(self, px, py, facing_right):
        """
        Chức năng: Cập nhật vị trí hitbox theo player.

        Input:
        - px (float): Tọa độ X của player.
        - py (float): Tọa độ Y của player.
        - facing_right (bool): Hướng nhìn hiện tại.
        """
        if facing_right:
            self.hitbox = pygame.Rect(px + 32, py - (self.range_y - 32) // 2, self.range_x, self.range_y)
        else:
            self.hitbox = pygame.Rect(px - self.range_x, py - (self.range_y - 32) // 2, self.range_x, self.range_y)

    def check_hit(self, monsters, facing_right):
        """
        Chức năng: Kiểm tra va chạm và gây sát thương.

        Input:
        - monsters (list): Danh sách quái vật.
        - facing_right (bool): Hướng nhìn để tính knockback.
        """
        knockback_dir = 1 if facing_right else -1
        
        for monster in monsters:
            if monster not in self.monsters_hit and hasattr(monster, 'rect'):
                if self.hitbox.colliderect(monster.rect):
                    if hasattr(monster, 'take_damage'):
                        monster.take_damage(self.damage, self.current_knockback, knockback_dir)
                    self.monsters_hit.append(monster)

    def update(self, dt, px, py, facing_right, monsters):
        """
        Chức năng: Cập nhật cooldown và hitbox đòn đánh.

        Input:
        - dt (float): Delta time.
        - px (float): Tọa độ X của player.
        - py (float): Tọa độ Y của player.
        - facing_right (bool): Hướng nhìn hiện tại.
        - monsters (list): Danh sách quái vật.
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt
            
        if self.active_timer > 0:
            self.active_timer -= dt
            self.update_hitbox(px, py, facing_right)
            self.check_hit(monsters, facing_right)


class ShadowClone:
    """
    Chức năng: Kỹ năng tạo phân thân bóng tối.

    Chi tiết:
        - Tạo ảo ảnh tại vị trí hiện tại để thu hút quái (nếu có logic aggro).
        - Tái kích hoạt để lướt ngay lập tức về phía ảo ảnh.
        - Gây sát thương toàn bộ quái vật trên đường bay về.
    """
    def __init__(self, cooldown, duration, damage):
        """
        Chức năng: Khởi tạo kỹ năng phân thân.

        Input:
        - cooldown (float): Thời gian hồi chiêu.
        - duration (float): Thời gian tồn tại tối đa của ảo ảnh.
        - damage (int): Sát thương gây ra khi lướt.
        """
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.duration = duration
        self.active_timer = 0
        self.damage = damage
        
        self.is_active = False
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.dash_hitbox = None
        self.monsters_hit = []
        self.silhouette = None
        self.facing_right = True

    def use(self, player_x, player_y, player_surface, facing_right):
        """
        Chức năng: Kích hoạt tạo ảo ảnh hoặc lướt về ảo ảnh đang có.

        Input:
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        - player_surface (pygame.Surface): Hình ảnh hiện tại của player.
        - facing_right (bool): Hướng nhìn hiện tại của player.
        """
        if not self.is_active and self.current_cooldown <= 0:
            self.is_active = True
            self.active_timer = self.duration
            self.rect.x = player_x
            self.rect.y = player_y
            self.facing_right = facing_right
            
            # Tạo silhouette
            sil = player_surface.copy()
            # Tô đen hoàn toàn (RGB: 0,0,0) nhưng giữ lại độ trong suốt gốc
            # Lấy vùng phủ (color key/alpha), lấp đầy bằng màu đen, 
            # chỉ giữ lại vùng có pixel, kết hợp độ trong suốt
            temp_surface = pygame.Surface(sil.get_size()).convert_alpha()
            temp_surface.fill((0, 0, 0, 200)) # Màu đen, mờ 200/255
            sil.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self.silhouette = sil
            
        elif self.is_active:
            min_x = min(player_x, self.rect.x)
            max_x = max(player_x, self.rect.x) + 32
            min_y = min(player_y, self.rect.y)
            max_y = max(player_y, self.rect.y) + 32
            
            self.dash_hitbox = pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)
            self.monsters_hit.clear()
                        
            self.is_active = False
            self.active_timer = 0
            self.current_cooldown = self.cooldown
            self.silhouette = None

    def update(self, dt, monsters):
        """
        Chức năng: Cập nhật thời gian tồn tại và xử lý sát thương lướt.

        Input:
        - dt (float): Delta time.
        - monsters (list): Danh sách quái vật.
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt
            
        if self.is_active:
            self.active_timer -= dt
            if self.active_timer <= 0:
                self.is_active = False
                self.silhouette = None
                self.current_cooldown = self.cooldown
                
        if self.dash_hitbox:
            for monster in monsters:
                if hasattr(monster, 'rect') and self.dash_hitbox.colliderect(monster.rect):
                    if monster not in self.monsters_hit:
                        if hasattr(monster, 'take_damage'):
                            monster.take_damage(self.damage)
                        self.monsters_hit.append(monster)
            self.dash_hitbox = None

    def draw(self, surface, offset_x=0, offset_y=0):
        """
        Chức năng: Vẽ hình ảnh phân thân dạng bóng đen.

        Input:
        - surface (pygame.Surface): Surface dùng để render.
        - offset_x (int): Độ lệch X (dùng cho canvas to/hitbox bé).
        - offset_y (int): Độ lệch Y (dùng cho canvas to/hitbox bé).
        """
        if self.is_active and self.silhouette:
            img = self.silhouette
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
                
            surface.blit(img, (self.rect.x + offset_x, self.rect.y + offset_y))


class ShadowSword:
    """
    Chức năng: Kỹ năng bắn kiếm ảnh xuyên thấu.

    Chi tiết:
        - Triệu hồi 3 thanh kiếm lơ lửng quanh player.
        - Bắn từng thanh kiếm theo hướng trỏ chuột.
        - Kiếm bay xuyên thấu quái và địa hình, giảm dần sát thương và tốc độ.
        - Tự hủy khi xuyên quá giới hạn hoặc bay ra ngoài map.
    """
    def __init__(self, cooldown, duration, damage, speed):
        """
        Chức năng: Khởi tạo kỹ năng kiếm ảnh.

        Input:
        - cooldown (float): Thời gian hồi chiêu.
        - duration (float): Thời gian tồn tại của kiếm khi chưa bắn.
        - damage (int): Sát thương gốc của mỗi thanh kiếm.
        - speed (float): Tốc độ bay của kiếm.
        """
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.duration = duration
        self.active_timer = 0
        self.damage = damage
        self.speed = speed
        
        self.swords = []
        self.max_swords = 3

    def use(self, player_x, player_y, target_x, target_y):
        """
        Chức năng: Triệu hồi kiếm hoặc bắn kiếm về vị trí chỉ định.

        Input:
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        - target_x (float): Tọa độ X của mục tiêu (chuột).
        - target_y (float): Tọa độ Y của mục tiêu (chuột).
        """
        if len(self.swords) == 0 and self.current_cooldown <= 0:
            self.active_timer = self.duration
            for _ in range(self.max_swords):
                self.swords.append({
                    'rect': pygame.Rect(player_x, player_y, 16, 16),
                    'fired': False,
                    'vx': 0, 'vy': 0,
                    'exact_x': 0.0,
                    'exact_y': 0.0,
                    'monsters_hit': [],
                    'tiles_hit': [],
                    'current_damage': self.damage,
                    'pierce_left': 4
                })
                
        elif len(self.swords) > 0:
            for sword in self.swords:
                if not sword['fired']:
                    sword['fired'] = True
                    dx = target_x - sword['rect'].centerx
                    dy = target_y - sword['rect'].centery
                    angle = math.atan2(dy, dx)
                    
                    sword['vx'] = math.cos(angle) * self.speed
                    sword['vy'] = math.sin(angle) * self.speed
                    
                    sword['exact_x'] = float(sword['rect'].x)
                    sword['exact_y'] = float(sword['rect'].y)
                    break

    def update(self, dt, player_x, player_y, solid_rects, monsters):
        """
        Chức năng: Cập nhật vị trí, xử lý va chạm xuyên thấu và giảm trừ chỉ số kiếm.

        Input:
        - dt (float): Delta time.
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        - solid_rects (list): Danh sách gạch địa hình.
        - monsters (list): Danh sách quái vật.
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt

        if len(self.swords) > 0:
            self.active_timer -= dt
            
            for sword in self.swords[:]:
                if not sword['fired']:
                    sword['rect'].centerx = player_x + 16
                    sword['rect'].centery = player_y - 30 
                else:
                    sword['exact_x'] += sword['vx'] * dt
                    sword['exact_y'] += sword['vy'] * dt
                    
                    sword['rect'].x = int(sword['exact_x'])
                    sword['rect'].y = int(sword['exact_y'])
                    
                    for monster in monsters:
                        if hasattr(monster, 'rect') and sword['rect'].colliderect(monster.rect):
                            if monster not in sword['monsters_hit']:
                                if hasattr(monster, 'take_damage'):
                                    monster.take_damage(sword['current_damage'])
                                sword['monsters_hit'].append(monster)
                                
                                sword['current_damage'] = int(sword['current_damage'] * 0.7)
                                sword['vx'] *= 0.8
                                sword['vy'] *= 0.8
                                sword['pierce_left'] -= 1
                                
                    for tile in solid_rects:
                        if getattr(tile, 'is_solid', False) and sword['rect'].colliderect(tile.rect):
                            if tile not in sword['tiles_hit']:
                                sword['tiles_hit'].append(tile)
                                
                                sword['current_damage'] = int(sword['current_damage'] * 0.7)
                                sword['vx'] *= 0.8
                                sword['vy'] *= 0.8
                                sword['pierce_left'] -= 1
                    
                    out_of_bounds = (sword['rect'].x < -1000 or sword['rect'].x > 3000 or 
                                     sword['rect'].y < -1000 or sword['rect'].y > 2000)
                                     
                    if sword['pierce_left'] <= 0 or out_of_bounds:
                        self.swords.remove(sword)
                        
            if self.active_timer <= 0 or (all(s['fired'] for s in self.swords) and len(self.swords) == 0):
                self.swords.clear()
                self.current_cooldown = self.cooldown

    def draw(self, surface):
        """
        Chức năng: Vẽ các thanh kiếm lên màn hình.

        Input:
        - surface (pygame.Surface): Surface dùng để render.
        """
        for sword in self.swords:
            pygame.draw.rect(surface, (0, 255, 255), sword['rect'])


class ShadowArea:
    """
    Chức năng: Kỹ năng tạo lãnh địa bóng tối (AoE).

    Chi tiết:
        - Tạo vùng ma thuật tĩnh tại vị trí thi triển.
        - Buff cho player: Tăng sát thương và phòng thủ khi đứng trong vùng.
        - Debuff cho quái vật: Làm chậm tốc độ di chuyển khi bước vào.
    """
    def __init__(self, cooldown, duration, radius):
        """
        Chức năng: Khởi tạo lãnh địa bóng tối.

        Input:
        - cooldown (float): Thời gian hồi chiêu.
        - duration (float): Thời gian tồn tại của vùng lãnh địa.
        - radius (int): Bán kính vùng hiệu ứng.
        """
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.duration = duration
        self.active_timer = 0
        
        self.radius = radius
        self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        self.is_active = False

    def use(self, player_x, player_y):
        """
        Chức năng: Kích hoạt lãnh địa tại vị trí hiện tại của player.

        Input:
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        """
        if self.current_cooldown <= 0:
            self.is_active = True
            self.active_timer = self.duration
            self.current_cooldown = self.cooldown
            self.rect.centerx = player_x + 16 
            self.rect.centery = player_y + 16

    def update(self, dt, player, monsters):
        """
        Chức năng: Cập nhật thời gian tồn tại, áp dụng buff và debuff.

        Input:
        - dt (float): Delta time.
        - player (Player): Đối tượng player (để xét buff).
        - monsters (list): Danh sách quái vật (để xét debuff).
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt
        
        if self.active_timer > 0:
            self.active_timer -= dt
            if self.active_timer <= 0:
                self.is_active = False
            
        if self.is_active and self.rect.colliderect(player.rect):
            player.in_shadow_area = True
        else:
            player.in_shadow_area = False

        for monster in monsters:
            if hasattr(monster, 'rect'):
                if self.is_active and self.rect.colliderect(monster.rect):
                    monster.is_slowed = True 
                else:
                    monster.is_slowed = False

    def draw(self, surface):
        """
        Chức năng: Vẽ vùng lãnh địa bán trong suốt.

        Input:
        - surface (pygame.Surface): Surface dùng để render.
        """
        if self.is_active:
            s = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 0, 100, 100), (self.radius, self.radius), self.radius)
            surface.blit(s, (self.rect.x, self.rect.y))