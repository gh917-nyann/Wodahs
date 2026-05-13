"""File chính của game Wodahs.

Mô tả:
    - Khởi tạo Pygame, cửa sổ, font và trạng thái menu.
    - Quản lý lựa chọn level, chọn phòng, vòng lặp game và vẽ giao diện.
Author: DGHuy
"""

import pygame
import sys
import random
import math
from entities.player import Player
from level.level_manager import LevelManager

def restart_game(player, level_manager):
    """Đặt lại trạng thái player và tải lại phòng hiện tại.

    Input:
    - player (Player): Đối tượng người chơi cần reset.
    - level_manager (LevelManager): Quản lý phòng level.
    Output:
    - Không trả về, chỉ cập nhật trạng thái player và phòng.
    """
    player.health = player.max_health
    player.mana = player.max_mana
    player.clear_active_states()
    level_manager.load_room()
    player.spawn_x = level_manager.player_spawn_x
    player.spawn_y = level_manager.player_spawn_y
    player.x = player.spawn_x
    player.y = player.spawn_y
    player.rect.x = int(player.x)
    player.rect.y = int(player.y)
    player.vx = 0
    player.vy = 0

pygame.init()
screen = pygame.display.set_mode((960, 640))
pygame.display.set_caption("Wodahs")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 80)
small_font = pygame.font.SysFont(None, 36)

ROOMS_PER_LEVEL = [3, 3, 1]
level_manager = LevelManager(rooms_per_level=ROOMS_PER_LEVEL)
player = Player(level_manager.player_spawn_x, level_manager.player_spawn_y)

game_state = "MAIN_MENU"
selected_lvl_idx = 0

play_btn_rect = pygame.Rect(960 // 2 - 100, 640 // 2 - 40, 200, 50)
htp_btn_rect = pygame.Rect(960 // 2 - 100, 640 // 2 + 30, 200, 50)
quit_btn_rect = pygame.Rect(960 // 2 - 100, 640 // 2 + 100, 200, 50)
menu_btn_rect = pygame.Rect(960 // 2 - 100, 640 // 2 + 120, 200, 50)
back_btn_rect = pygame.Rect(50, 50, 100, 40)

lvl_btn_rects = []
for i in range(len(ROOMS_PER_LEVEL)):
    lvl_btn_rects.append(pygame.Rect(960 // 2 - 100, 200 + i * 70, 200, 50))

instructions = [
    "A / D : Move Left / Right",
    "SPACE : Jump / Double Jump",
    "SHIFT : Dash",
    "LCTRL / RCTRL : Flip World (Change Dimension)",
    "Left Click : Basic Attack / Shoot Hovering Swords",
    "Q : Shadow Clone (Dash to clone position)",
    "E : Summon Shadow Swords (Requires 60 Mana)",
    "R : Shadow Area (Buff/Debuff zone - Requires 80 Mana)",
    "1, 2, 3 : Use Health Potion, Mana Potion, Bomb",
    "~GOOD LUCK~",
    "~~~Nyann~~~"
]

menu_particles = []
LIGHT_RADIUS = 70
light_brush = pygame.Surface((LIGHT_RADIUS * 2, LIGHT_RADIUS * 2))
light_brush.fill((0, 0, 0))
for r in range(LIGHT_RADIUS, 0, -2):
    intensity = int(255 * ((LIGHT_RADIUS - r) / LIGHT_RADIUS))
    pygame.draw.circle(light_brush, (intensity, int(intensity * 0.8), int(intensity * 0.2)), (LIGHT_RADIUS, LIGHT_RADIUS), r)

def draw_firefly_background(surface, dt, background_img):
    """Vẽ nền menu với hiệu ứng đom đóm và ánh sáng.

    Input:
    - surface (pygame.Surface): Surface để vẽ.
    - dt (float): Delta time để cập nhật hoạt ảnh.
    - background_img: Ảnh nền nếu có, hoặc None để dùng màu mặc định.
    Output:
    - Không trả về, vẽ trực tiếp lên surface.
    """
    if background_img:
        surface.blit(background_img, (0, 0))
    else:
        surface.fill((20, 20, 25))

    if len(menu_particles) < 30:
        menu_particles.append({
            'x': random.randint(0, 960),
            'y': random.randint(640, 700),
            'r': random.randint(2, 4),
            'vx': random.uniform(-0.5, 0.5),
            'vy': random.uniform(-1.5, -0.5),
            'life': 255,
            'blink_speed': random.uniform(0.003, 0.01)
        })

    time_ms = pygame.time.get_ticks()
    light_map = pygame.Surface((960, 640))
    light_map.fill((30, 30, 45))

    for p in menu_particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['life'] -= 15 * dt
        
        if p['life'] <= 0 or p['y'] < -50:
            menu_particles.remove(p)
        else:
            blink = abs(math.sin(time_ms * p['blink_speed']))
            current_life = p['life'] * blink
            
            if current_life > 10:
                scale = current_life / 255.0
                s_radius = int(LIGHT_RADIUS * scale)
                if s_radius > 0:
                    scaled_brush = pygame.transform.scale(light_brush, (s_radius * 2, s_radius * 2))
                    light_map.blit(scaled_brush, (int(p['x']) - s_radius, int(p['y']) - s_radius), special_flags=pygame.BLEND_RGB_ADD)

    surface.blit(light_map, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    for p in menu_particles:
        blink = abs(math.sin(time_ms * p['blink_speed']))
        alpha = int(p['life'] * blink)
        if alpha > 50:
            core = pygame.Surface((p['r']*2, p['r']*2), pygame.SRCALPHA)
            pygame.draw.circle(core, (255, 255, 200, alpha), (p['r'], p['r']), p['r'])
            surface.blit(core, (int(p['x']) - p['r'], int(p['y']) - p['r']))

running = True
while running:
    dt = clock.tick(60) / 1000.0
    events = pygame.event.get()
    mouse_pos = pygame.mouse.get_pos()
    
    for event in events:
        if event.type == pygame.QUIT:
            running = False
            
        if game_state == "MAIN_MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_btn_rect.collidepoint(mouse_pos):
                    game_state = "LEVEL_SELECT"
                elif htp_btn_rect.collidepoint(mouse_pos):
                    game_state = "HOW_TO_PLAY"
                elif quit_btn_rect.collidepoint(mouse_pos):
                    running = False

        elif game_state == "HOW_TO_PLAY":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(mouse_pos):
                    game_state = "MAIN_MENU"

        elif game_state == "LEVEL_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(mouse_pos):
                    game_state = "MAIN_MENU"
                for i, btn in enumerate(lvl_btn_rects):
                    if btn.collidepoint(mouse_pos) and i <= level_manager.highest_level:
                        selected_lvl_idx = i
                        game_state = "ROOM_SELECT"

        elif game_state == "ROOM_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn_rect.collidepoint(mouse_pos):
                    game_state = "LEVEL_SELECT"
                for r_idx in range(ROOMS_PER_LEVEL[selected_lvl_idx]):
                    r_btn = pygame.Rect(960 // 2 - 100, 200 + r_idx * 70, 200, 50)
                    is_unlocked = (selected_lvl_idx < level_manager.highest_level) or (selected_lvl_idx == level_manager.highest_level and r_idx <= level_manager.highest_room)
                    if r_btn.collidepoint(mouse_pos) and is_unlocked:
                        level_manager.current_level = selected_lvl_idx
                        level_manager.current_room = r_idx
                        restart_game(player, level_manager)
                        game_state = "PLAYING"

        elif game_state == "PLAYING":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    if hasattr(level_manager, 'flip_world'):
                        level_manager.flip_world()
                        level_manager.resolve_overlap(player)
        
        elif game_state == "GAMEOVER":
            if event.type == pygame.KEYDOWN:
                restart_game(player, level_manager)
                game_state = "PLAYING"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_btn_rect.collidepoint(mouse_pos):
                    game_state = "MAIN_MENU"

        elif game_state == "WIN":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_btn_rect.collidepoint(mouse_pos):
                    game_state = "MAIN_MENU"

        elif game_state == "LEVEL_COMPLETE":
            if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                game_state = "LEVEL_SELECT"

    if game_state == "PLAYING":
        active_tiles = [t for t in level_manager.tiles if getattr(t, 'world_id', 0) == level_manager.current_world]
        active_monsters = [m for m in level_manager.monsters if getattr(m, 'world_id', 0) == level_manager.current_world or getattr(m, 'is_global', False)]
        player.inp(events, active_tiles, active_monsters)
        player.update(dt, active_tiles, active_monsters)
        level_manager.update(dt, player)
        status = level_manager.check_room_transition(player)
        if status == "WIN": 
            game_state = "WIN"
        elif status == "LEVEL_UP":
            game_state = "LEVEL_COMPLETE"
        elif player.health <= 0: 
            game_state = "GAMEOVER"

    screen.fill((20, 20, 25))
    
    if game_state in ["MAIN_MENU", "HOW_TO_PLAY", "LEVEL_SELECT", "ROOM_SELECT", "LEVEL_COMPLETE"]:
        if game_state == "LEVEL_COMPLETE":
            if len(menu_particles) < 60:
                menu_particles.append({
                    'x': random.randint(0, 960),
                    'y': random.randint(640, 700),
                    'r': random.randint(2, 4),
                    'vx': random.uniform(-0.5, 0.5),
                    'vy': random.uniform(-2.5, -1.0),
                    'life': 255,
                    'blink_speed': random.uniform(0.003, 0.01)
                })
        draw_firefly_background(screen, dt, level_manager.global_bg)
    
    if game_state == "MAIN_MENU":
        time_ms = pygame.time.get_ticks()
        float_y = math.sin(time_ms / 500.0) * 10
        title_y = 150 + float_y
        
        title_text = font.render("WODAHS", True, (255, 215, 0))
        for i in range(1, 4):
            glow = font.render("WODAHS", True, (200, 100, 0))
            glow.set_alpha(100 // i)
            screen.blit(glow, glow.get_rect(center=(480, title_y + i*3)))
        screen.blit(title_text, title_text.get_rect(center=(480, title_y)))
        
        for b, txt, clr in [(play_btn_rect, "PLAY", (50, 50, 60)), (htp_btn_rect, "HOW TO PLAY", (50, 50, 60)), (quit_btn_rect, "QUIT", (100, 30, 30))]:
            if b.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 215, 0), b.inflate(6, 6), border_radius=10)
                c = (80, 80, 100) if clr != (100, 30, 30) else (150, 50, 50)
            else:
                c = clr
            pygame.draw.rect(screen, c, b, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), b, 2, border_radius=10)
            msg = small_font.render(txt, True, (255, 255, 255))
            screen.blit(msg, msg.get_rect(center=b.center))

    elif game_state == "HOW_TO_PLAY":
        t = font.render("HOW TO PLAY", True, (255, 215, 0))
        screen.blit(t, t.get_rect(center=(480, 80)))
        
        b_color = (150, 50, 50) if back_btn_rect.collidepoint(mouse_pos) else (100, 30, 30)
        pygame.draw.rect(screen, b_color, back_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), back_btn_rect, 2, border_radius=8)
        b_text = small_font.render("BACK", True, (255, 255, 255))
        screen.blit(b_text, b_text.get_rect(center=back_btn_rect.center))
        
        for i, text in enumerate(instructions):
            msg = small_font.render(text, True, (200, 200, 200))
            screen.blit(msg, msg.get_rect(center=(480, 160 + i * 40)))

    elif game_state == "LEVEL_SELECT":
        t = font.render("SELECT LEVEL", True, (255, 255, 255))
        screen.blit(t, t.get_rect(center=(480, 100)))
        
        b_color = (150, 50, 50) if back_btn_rect.collidepoint(mouse_pos) else (100, 30, 30)
        pygame.draw.rect(screen, b_color, back_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), back_btn_rect, 2, border_radius=8)
        b_t = small_font.render("BACK", True, (255, 255, 255))
        screen.blit(b_t, b_t.get_rect(center=back_btn_rect.center))
        
        for i, b in enumerate(lvl_btn_rects):
            unlocked = i <= level_manager.highest_level
            if unlocked and b.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 255, 255), b.inflate(6, 6), border_radius=10)
                c = (50, 150, 50)
            else:
                c = (30, 100, 30) if unlocked else (40, 40, 40)
            
            pygame.draw.rect(screen, c, b, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), b, 2, border_radius=10)
            msg = small_font.render(f"LEVEL {i+1}" if unlocked else "LOCKED", True, (255, 255, 255) if unlocked else (100, 100, 100))
            screen.blit(msg, msg.get_rect(center=b.center))

    elif game_state == "ROOM_SELECT":
        t = font.render(f"LEVEL {selected_lvl_idx + 1} ROOMS", True, (255, 255, 255))
        screen.blit(t, t.get_rect(center=(480, 100)))
        
        b_color = (150, 50, 50) if back_btn_rect.collidepoint(mouse_pos) else (100, 30, 30)
        pygame.draw.rect(screen, b_color, back_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), back_btn_rect, 2, border_radius=8)
        b_t = small_font.render("BACK", True, (255, 255, 255))
        screen.blit(b_t, b_t.get_rect(center=back_btn_rect.center))
        
        for r_idx in range(ROOMS_PER_LEVEL[selected_lvl_idx]):
            r_btn = pygame.Rect(480 - 100, 200 + r_idx * 70, 200, 50)
            unlocked = (selected_lvl_idx < level_manager.highest_level) or (selected_lvl_idx == level_manager.highest_level and r_idx <= level_manager.highest_room)
            
            if unlocked and r_btn.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (255, 255, 255), r_btn.inflate(6, 6), border_radius=10)
                c = (50, 100, 150)
            else:
                c = (30, 60, 100) if unlocked else (40, 40, 40)
                
            pygame.draw.rect(screen, c, r_btn, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), r_btn, 2, border_radius=10)
            msg = small_font.render(f"ROOM {r_idx+1}" if unlocked else "LOCKED", True, (255, 255, 255) if unlocked else (100, 100, 100))
            screen.blit(msg, msg.get_rect(center=r_btn.center))

    elif game_state == "PLAYING":
        level_manager.draw(screen)
        player.draw(screen)

    elif game_state == "GAMEOVER":
        level_manager.draw(screen)
        player.draw(screen)
        ov = pygame.Surface((960, 640), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        screen.blit(ov, (0, 0))
        t = font.render("GAME OVER", True, (255, 0, 0))
        screen.blit(t, t.get_rect(center=(480, 250)))
        
        time_ms = pygame.time.get_ticks()
        if (time_ms // 500) % 2 == 0:
            msg = small_font.render("Press ANY KEY to Restart", True, (255, 255, 255))
            screen.blit(msg, msg.get_rect(center=(480, 320)))
            
        c = (150, 150, 150) if menu_btn_rect.collidepoint(mouse_pos) else (80, 80, 80)
        pygame.draw.rect(screen, c, menu_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), menu_btn_rect, 2, border_radius=8)
        txt = small_font.render("MAIN MENU", True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=menu_btn_rect.center))

    elif game_state == "WIN":
        level_manager.draw(screen)
        player.draw(screen)
        ov = pygame.Surface((960, 640), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        screen.blit(ov, (0, 0))
        t = font.render("VICTORY!", True, (0, 255, 0))
        screen.blit(t, t.get_rect(center=(480, 250)))
        
        c = (150, 150, 150) if menu_btn_rect.collidepoint(mouse_pos) else (80, 80, 80)
        pygame.draw.rect(screen, c, menu_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255), menu_btn_rect, 2, border_radius=8)
        txt = small_font.render("MAIN MENU", True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=menu_btn_rect.center))

    elif game_state == "LEVEL_COMPLETE":
        ov = pygame.Surface((960, 640), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 100))
        screen.blit(ov, (0, 0))
        
        time_ms = pygame.time.get_ticks()
        float_y = math.sin(time_ms / 300.0) * 15
        
        for i in range(1, 5):
            glow = font.render("LEVEL CLEARED!", True, (0, 150, 80))
            glow.set_alpha(150 // i)
            screen.blit(glow, glow.get_rect(center=(480, int(250 + float_y) + i * 2)))
            screen.blit(glow, glow.get_rect(center=(480, int(250 + float_y) - i * 2)))
            screen.blit(glow, glow.get_rect(center=(480 + i * 2, int(250 + float_y))))
            screen.blit(glow, glow.get_rect(center=(480 - i * 2, int(250 + float_y))))

        msg_title = font.render("LEVEL CLEARED!", True, (0, 255, 150))
        screen.blit(msg_title, msg_title.get_rect(center=(480, int(250 + float_y))))
        
        sub_msg = small_font.render("Congratulations! Press ANY KEY to continue", True, (255, 255, 255))
        screen.blit(sub_msg, sub_msg.get_rect(center=(480, 380)))

    pygame.display.flip()

pygame.quit()
sys.exit()