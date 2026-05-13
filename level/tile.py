"""
Chức năng chính: Quản lý khối địa hình (Tile) được load từ TMX.
Author: DGHuy
"""
import pygame

class Tile:
    def __init__(self, x, y, layer_name, image=None):
        self.x = x
        self.y = y
        self.image = image
        self.layer_name = layer_name
        self.silhouette_img = None
        
        if self.image:
            img_w, img_h = self.image.get_size()
            self.rect = pygame.Rect(self.x, self.y, img_w, img_h)
            self.silhouette_img = self.image.copy()
            self.silhouette_img.fill((0, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
            
        else:
            self.rect = pygame.Rect(self.x, self.y, 32, 32)
            
        self.is_solid = False
        self.is_fragile = False 
        self.is_broken = False
        self.is_one_way = False 
        self.is_trap = False 
        
        self.stand_timer = 0.5   
        self.respawn_timer = 3.0 
        self.is_stepped = False

        if layer_name == 'solid':
            self.is_solid = True
        elif layer_name == 'cracked':
            self.is_solid = True
            self.is_fragile = True
        elif layer_name == 'oneway':
            self.is_solid = True
            self.is_one_way = True
        elif layer_name == 'traps':
            self.is_trap = True

    def step_on(self):
        """Đánh dấu tile giòn khi player bước lên.

        Input:
        - Không có.
        Output:
        - Cập nhật self.is_stepped nếu tile có thể vỡ.
        """
        if self.is_fragile and not self.is_broken:
            self.is_stepped = True

    def update(self, dt):
        """Cập nhật trạng thái gạch giòn và hồi phục.

        Input:
        - dt (float): Delta time.
        Output:
        - Không trả về, điều khiển thời gian vỡ và hồi sinh.
        """
        if self.is_fragile:
            if self.is_broken:
                self.respawn_timer -= dt
                if self.respawn_timer <= 0:
                    self.is_broken = False
                    self.is_solid = True
                    self.is_stepped = False
                    self.stand_timer = 0.5
                    self.respawn_timer = 3.0
            elif self.is_stepped:
                self.stand_timer -= dt
                if self.stand_timer <= 0:
                    self.is_broken = True
                    self.is_solid = False

    def draw(self, surface):
        """Vẽ tile lên màn hình nếu chưa bị vỡ.

        Input:
        - surface (pygame.Surface): Surface để render tile.
        Output:
        - Không trả về, vẽ hình ảnh hoặc màu tile.
        """
        if self.is_broken: return
            
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            color = (100, 100, 100)
            if self.layer_name == 'traps': color = (255, 0, 0)
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, (0, 0, 0), self.rect, 1)

        if self.is_fragile and self.is_stepped:
            overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            overlay.fill((255, 100, 100, 128))
            surface.blit(overlay, self.rect)

    def draw_silhouette(self, surface):
        """Vẽ bóng mờ của tile khi tile nằm ngoài thế giới hiện tại.

        Input:
        - surface (pygame.Surface): Surface để render silhouette.
        Output:
        - Không trả về, vẽ bóng mờ hoặc viền xám.
        """
        if self.is_broken: return
        
        if self.silhouette_img:
            surface.blit(self.silhouette_img, self.rect)
        else:
            pygame.draw.rect(surface, (30, 30, 30), self.rect, 1)