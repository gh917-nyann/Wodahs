"""
Chức năng chính: Quản lý hệ thống vật phẩm.
Author: DGHuy

Chi tiết:
    - Định nghĩa và xử lý logic cho các vật phẩm tiêu hao (Bình máu, Bình Mana, Bom nổ).
    - Quản lý số lượng giới hạn và thời gian chờ (Cooldown).
    - Phục hồi chỉ số cho người chơi.
    - Xử lý đếm ngược phát nổ, gây sát thương diện rộng và phá gạch nứt.
"""
import pygame

class HealthPotion:
    """
    Chức năng: Vật phẩm Bình Máu.
    
    Chi tiết:
        - Phục hồi lượng máu nhất định cho player.
        - Quản lý số lượng mang theo và cooldown giữa các lần uống.
    """
    def __init__(self, heal_amount, cooldown):
        """
        Chức năng: Khởi tạo bình máu.
        
        Input:
        - heal_amount (int): Lượng HP phục hồi mỗi lần uống.
        - cooldown (float): Thời gian hồi sau khi uống.
        """
        self.heal_amount = heal_amount
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.quantity = 3
        
    def use(self, player):
        """
        Chức năng: Sử dụng bình máu để hồi HP.
        
        Input:
        - player (Player): Đối tượng player được hồi máu.
        """
        if self.quantity > 0 and self.current_cooldown <= 0:
            if player.health < player.max_health:
                player.health = min(player.health + self.heal_amount, player.max_health)
                self.quantity -= 1
                self.current_cooldown = self.cooldown

    def update(self, dt):
        """
        Chức năng: Cập nhật thời gian hồi của bình máu.

        Input:
        - dt (float): Delta time.
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt


class ManaPotion:
    """
    Chức năng: Vật phẩm Bình Năng lượng.
    
    Chi tiết:
        - Phục hồi năng lượng (Mana) cho player.
        - Quản lý số lượng và cooldown tương tự bình máu.
    """
    def __init__(self, restore_amount, cooldown):
        """
        Chức năng: Khởi tạo bình năng lượng.
        
        Input:
        - restore_amount (int): Lượng Mana phục hồi mỗi lần uống.
        - cooldown (float): Thời gian hồi sau khi uống.
        """
        self.restore_amount = restore_amount
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.quantity = 3 
        
    def use(self, player):
        """
        Chức năng: Sử dụng bình mana để hồi năng lượng.
        
        Input:
        - player (Player): Đối tượng player được hồi mana.
        """
        if self.quantity > 0 and self.current_cooldown <= 0:
            if player.mana < player.max_mana:
                player.mana = min(player.mana + self.restore_amount, player.max_mana)
                self.quantity -= 1
                self.current_cooldown = self.cooldown

    def update(self, dt):
        """
        Chức năng: Cập nhật thời gian hồi của bình mana.

        Input:
        - dt (float): Delta time.
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt


class BombItem:
    """
    Chức năng: Vật phẩm Bom nổ (AoE).
    
    Chi tiết:
        - Đặt bom tại vị trí hiện tại của player.
        - Đếm ngược và phát nổ gây sát thương diện rộng.
        - Phá hủy các khối gạch nứt trong bán kính nổ.
    """
    def __init__(self, cooldown, fuse_time, damage, radius):
        """
        Chức năng: Khởi tạo hệ thống bom.
        
        Input:
        - cooldown (float): Thời gian chờ giữa 2 lần đặt bom.
        - fuse_time (float): Thời gian đếm ngược trước khi nổ.
        - damage (int): Sát thương gây ra cho quái.
        - radius (int): Bán kính vụ nổ.
        """
        self.cooldown = cooldown
        self.current_cooldown = 0
        self.fuse_time = fuse_time
        self.damage = damage
        self.radius = radius
        self.quantity = 5
        
        self.active_bombs = []

    def use(self, player_x, player_y, facing_right):
        """
        Chức năng: Đặt bom xuống map.
        
        Input:
        - player_x (float): Tọa độ X của player.
        - player_y (float): Tọa độ Y của player.
        - facing_right (bool): Hướng nhìn để thả bom lệch ra trước mặt.
        """
        if self.quantity > 0 and self.current_cooldown <= 0:
            drop_x = player_x + 32 if facing_right else player_x - 16
            
            self.active_bombs.append({
                'rect': pygame.Rect(drop_x, player_y + 16, 16, 16),
                'timer': self.fuse_time,
                'exploded': False,
                'explosion_timer': 0
            })
            
            self.quantity -= 1
            self.current_cooldown = self.cooldown

    def update(self, dt, monsters, tiles):
        """
        Chức năng: Cập nhật đếm ngược bom, xử lý nổ và phá gạch.
        
        Input:
        - dt (float): Delta time.
        - monsters (list): Danh sách quái vật.
        - tiles (list): Danh sách khối địa hình (gạch).
        """
        if self.current_cooldown > 0:
            self.current_cooldown -= dt

        for bomb in self.active_bombs[:]:
            if not bomb['exploded']:
                bomb['timer'] -= dt
                if bomb['timer'] <= 0:
                    bomb['exploded'] = True
                    bomb['explosion_timer'] = 0.2
                    
                    explosion_rect = pygame.Rect(
                        bomb['rect'].centerx - self.radius,
                        bomb['rect'].centery - self.radius,
                        self.radius * 2,
                        self.radius * 2
                    )
                    
                    for monster in monsters:
                        if hasattr(monster, 'rect') and explosion_rect.colliderect(monster.rect):
                            if hasattr(monster, 'take_damage'):
                                monster.take_damage(self.damage)

                    for tile in tiles[:]:
                        if hasattr(tile, 'rect') and explosion_rect.colliderect(tile.rect):
                            if getattr(tile, 'is_cracked', False):
                                tiles.remove(tile)

            else:
                bomb['explosion_timer'] -= dt
                if bomb['explosion_timer'] <= 0:
                    self.active_bombs.remove(bomb)

    def draw(self, surface):
        """
        Chức năng: Vẽ bom và hiệu ứng nổ.
        
        Input:
        - surface (pygame.Surface): Surface dùng để render.
        """
        for bomb in self.active_bombs:
            if not bomb['exploded']:
                pygame.draw.circle(surface, (50, 50, 50), bomb['rect'].center, 8)
                pygame.draw.circle(surface, (255, 150, 0), (bomb['rect'].centerx, bomb['rect'].top), 3)
            else:
                pygame.draw.circle(surface, (255, 100, 0), bomb['rect'].center, self.radius)