"""Quản lý phòng, map và chuyển thế giới cho game.

Mô tả:
    - Tải dữ liệu TMX cho các phòng trong từng level.
    - Quản lý tile, monster, cửa và spawn player.
    - Xử lý chuyển room/level và cập nhật render.
Author: DGHuy
"""

import pygame
import pytmx
import os
import random
from level.tile import Tile
from entities.monster import Monster
from entities.boss import Boss

class LevelManager:
    """Quản lý trạng thái level và phòng của game.

    Input:
    - rooms_per_level (list): Số lượng phòng cho mỗi level.
    Output:
    - Tạo đối tượng quản lý các tile, quái, cửa và spawn point.
    """
    def __init__(self, rooms_per_level):
        self.rooms_per_level = rooms_per_level
        self.max_levels = len(rooms_per_level)
        self.current_level = 0
        self.current_room = 0
        self.current_world = 0
        
        self.highest_level = 0
        self.highest_room = 0
        
        self.tiles = []
        self.monsters = []
        self.doors = []
        
        try:
            bg = pygame.image.load("sth/background.png").convert() 
            self.global_bg = pygame.transform.scale(bg, (960, 640))
        except Exception:
            self.global_bg = None
        
        self.player_spawn_x = 0
        self.player_spawn_y = 0

        self.spawn_points = []
        self.monsters_left_to_spawn = 0
        self.spawn_timer = 0
        self.max_active_monsters = 5
        self.spawn_amount_per_wave = 3
        
        self.load_room()

    def flip_world(self):
        """Đổi thế giới hiện tại giữa 0 và 1.

        Input:
        - Không có.
        Output:
        - Không trả về, chỉ cập nhật current_world.
        """
        self.current_world = 1 - self.current_world

    def resolve_overlap(self, player):
        """Di chuyển player ra khỏi tile chồng nhau sau khi flip world.

        Input:
        - player (Player): Player có thể bị chồng lên tile.
        Output:
        - Không trả về, chỉ điều chỉnh vị trí player.
        """
        overlapped = True
        active_tiles = [t for t in self.tiles if getattr(t, 'world_id', 0) == self.current_world]
        while overlapped:
            overlapped = False
            for tile in active_tiles:
                if getattr(tile, 'is_solid', False) and player.rect.colliderect(tile.rect):
                    player.y -= 1
                    player.rect.y = int(player.y)
                    overlapped = True
                    break

    def load_room(self):
        """Tải lại dữ liệu TMX cho phòng hiện tại.

        Input:
        - Không có.
        Output:
        - Cập nhật self.tiles, self.monsters và self.doors từ file TMX.
        """
        self.tiles.clear()
        self.monsters.clear()
        self.doors.clear()
        self.spawn_points.clear()
        self.monsters_left_to_spawn = 0
        
        room_num = self.current_room + 1
        level_num = self.current_level + 1
        
        for w_idx, suffix in enumerate(['O', 'S']):
            tmx_file = f"sth/room{room_num}_level{level_num}_{suffix}.tmx" 
            
            if not os.path.exists(tmx_file):
                if w_idx == 1: 
                    tmx_file = f"sth/room{room_num}_level{level_num}_O.tmx"
                else:
                    continue

            tmx_data = pytmx.load_pygame(tmx_file)

            for layer in tmx_data.visible_layers:
                layer_name = layer.name.lower()

                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        if gid == 0: continue
                        
                        pixel_x = x * tmx_data.tilewidth
                        pixel_y = y * tmx_data.tileheight
                        
                        if layer_name == 'player':
                            self.player_spawn_x = pixel_x
                            self.player_spawn_y = pixel_y
                            
                        tile_img = tmx_data.get_tile_image_by_gid(gid)
                        if tile_img:
                            img_w, img_h = tile_img.get_size()
                            adjusted_y = pixel_y + tmx_data.tileheight - img_h
                            
                            if layer_name in ['solid', 'cracked', 'oneway', 'traps']:
                                t = Tile(pixel_x, adjusted_y, layer_name, tile_img)
                                t.world_id = w_idx
                                self.tiles.append(t)
                                
                            elif layer_name == 'portal':
                                self.doors.append({
                                    'rect': pygame.Rect(pixel_x, adjusted_y, img_w, img_h),
                                    'image': tile_img,
                                    'world_id': w_idx 
                                })
                                
                            elif layer_name == 'boss':
                                b = Boss(pixel_x, pixel_y)
                                self.monsters.append(b)
                                
                            elif layer_name == 'monsters':
                                self.spawn_points.append({'x': pixel_x, 'y': pixel_y, 'world_id': w_idx})
                                self.monsters_left_to_spawn += 1

                elif isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        if layer_name == 'player':
                            self.player_spawn_x, self.player_spawn_y = obj.x, obj.y
                        elif layer_name == 'portal':
                            self.doors.append({
                                'rect': pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                                'image': getattr(obj, 'image', None),
                                'world_id': w_idx
                            })
                        elif layer_name == 'boss':
                            b = Boss(obj.x, obj.y)
                            self.monsters.append(b)
                        elif layer_name == 'monsters':
                            self.spawn_points.append({'x': obj.x, 'y': obj.y, 'world_id': w_idx})
                            self.monsters_left_to_spawn += 1

    def check_room_transition(self, player):
        """Kiểm tra điều kiện chuyển phòng hoặc chiến thắng.

        Input:
        - player (Player): Đối tượng player để kiểm tra va chạm cửa.
        Output:
        - Trả về False, True, "LEVEL_UP" hoặc "WIN" tùy trạng thái.
        """
        if len(self.monsters) > 0 or self.monsters_left_to_spawn > 0:
            return False

        for door in self.doors:
            if door['world_id'] == self.current_world:
                if player.rect.colliderect(door['rect']):
                    self.current_room += 1

                    if self.current_room >= self.rooms_per_level[self.current_level]:
                        self.current_level += 1
                        self.current_room = 0

                        if self.current_level > self.highest_level:
                            self.highest_level = self.current_level
                            self.highest_room = 0

                        if self.current_level >= self.max_levels:
                            return "WIN"

                        player.clear_active_states()
                        return "LEVEL_UP"

                    self.current_world = 0
                    player.clear_active_states()
                    self.load_room()
                    player.spawn_x = self.player_spawn_x
                    player.spawn_y = self.player_spawn_y
                    player.x = self.player_spawn_x
                    player.y = self.player_spawn_y
                    player.rect.x = int(player.x)
                    player.rect.y = int(player.y)
                    player.vx = 0
                    player.vy = 0
                    return True
        return False

    def update(self, dt, player):
        """Cập nhật trạng thái tile và quái trong phòng.

        Input:
        - dt (float): Delta time.
        - player (Player): Player để truyền cho quái.
        Output:
        - Không trả về, cập nhật tile, quái và loại bỏ quái chết.
        """
        if len(self.monsters) < self.max_active_monsters and self.monsters_left_to_spawn > 0 and len(self.spawn_points) > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                for _ in range(self.spawn_amount_per_wave):
                    if len(self.monsters) >= self.max_active_monsters or self.monsters_left_to_spawn <= 0:
                        break
                        
                    sp = random.choice(self.spawn_points)
                    monster_type = random.choice(["MELEE", "RANGED"])
                    new_m = Monster(sp['x'], sp['y'], m_type=monster_type)
                    new_m.world_id = sp['world_id']
                    
                    self.monsters.append(new_m)
                    self.monsters_left_to_spawn -= 1
                self.spawn_timer = 1.5

        for tile in self.tiles:
            if hasattr(tile, 'update'): 
                tile.update(dt)

        for monster in self.monsters[:]:
            is_global = getattr(monster, 'is_global', False)
            target_player = player if (monster.world_id == self.current_world or is_global) else None
            
            if isinstance(monster, Boss):
                if target_player:
                    monster.update(dt, target_player, self.monsters, self.current_world)
            else:
                m_tiles = [t for t in self.tiles if t.world_id == monster.world_id]
                monster.update(dt, m_tiles, target_player)
                
            if hasattr(monster, 'health') and monster.health <= 0:
                self.monsters.remove(monster)

    def draw(self, surface):
        """Vẽ phòng, nền và quái vật theo thế giới hiện tại.

        Input:
        - surface (pygame.Surface): Surface để render.
        Output:
        - Không trả về, vẽ nền, tile và quái.
        """
        if self.global_bg:
            surface.blit(self.global_bg, (0, 0))
            if self.current_world == 1:
                dark_overlay = pygame.Surface((960, 640), pygame.SRCALPHA)
                dark_overlay.fill((20, 25, 35, 45)) 
                surface.blit(dark_overlay, (0, 0))

        for tile in self.tiles:
            if tile.world_id != self.current_world:
                tile.draw_silhouette(surface)
                
        for monster in self.monsters:
            if not getattr(monster, 'is_global', False) and monster.world_id != self.current_world:
                monster.draw_silhouette(surface)

        for tile in self.tiles:
            if tile.world_id == self.current_world:
                tile.draw(surface)
        
        if len(self.monsters) == 0 and self.monsters_left_to_spawn == 0:
            for door in self.doors:
                if door['world_id'] == self.current_world:
                    if door['image']:
                        surface.blit(door['image'], door['rect'])
                    else:
                        pygame.draw.rect(surface, (100, 50, 200), door['rect'])
        
        for monster in self.monsters:
            if getattr(monster, 'is_global', False) or monster.world_id == self.current_world:
                monster.draw(surface)
