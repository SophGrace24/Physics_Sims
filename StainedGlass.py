import pygame
import math
import random
import numpy as np

# --- Configuration ---
WIDTH, HEIGHT = 1200, 900
BACKGROUND = (5, 5, 10)

# Physics Settings
WAVELENGTHS = [1.0, 1.02, 1.05] # Dispersion multipliers
MAX_BOUNCES = 8 
RAYS_PER_SOURCE = 150 # Slightly reduced per source to keep FPS smooth

class OrganicShard:
    def __init__(self, points):
        self.points = points 
        self.hue = random.randint(0, 360)
        self.saturation = 100
        self.base_ior = random.uniform(1.1, 2.4) 
        self.volatility = random.uniform(0.001, 0.005) 
        self.energy = 0.0 
        self.current_ior = self.base_ior

    def update(self):
        # The "Breathing" 
        drift = math.sin(pygame.time.get_ticks() * self.volatility * 0.1) * 0.05
        self.energy = max(0, self.energy - 0.01) 
        self.current_ior = self.base_ior + drift + (self.energy * 0.1)
        self.current_ior = max(1.01, self.current_ior) 

    def get_color(self):
        c = pygame.Color(0)
        c.hsva = (self.hue, self.saturation, 100, 100)
        return (c.r, c.g, c.b)

# --- Vector Math Helpers ---
def intersect(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if denom == 0: return None
    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
    if 0 < ua < 1 and 0 < ub < 1:
        return ua 
    return None

def get_normal(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return (-dy, dx)

def normalize(v):
    l = math.sqrt(v[0]**2 + v[1]**2)
    if l == 0: return (0,1)
    return (v[0]/l, v[1]/l)

def reflect(d, n):
    dot = d[0]*n[0] + d[1]*n[1]
    return (d[0] - 2*dot*n[0], d[1] - 2*dot*n[1])

def refract(d, n, ior_ratio):
    dot = -(d[0]*n[0] + d[1]*n[1])
    term = 1.0 - ior_ratio**2 * (1.0 - dot**2)
    if term < 0: return None 
    term = math.sqrt(term)
    return (ior_ratio * d[0] + (ior_ratio * dot - term) * n[0],
            ior_ratio * d[1] + (ior_ratio * dot - term) * n[1])

def dist_sq(p1, p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Lumina Naturae: Binary Source")
    
    light_surface = pygame.Surface((WIDTH, HEIGHT))
    light_surface.set_colorkey((0,0,0))
    
    shards = []
    current_draw = []
    
    # --- The Lights ---
    # 0: Cyan (Green + Blue)
    # 1: Magenta (Red + Blue)
    lights = [
        {'pos': [WIDTH//3, HEIGHT//2], 'color': (0, 255, 255)},   
        {'pos': [2*WIDTH//3, HEIGHT//2], 'color': (255, 0, 255)}
    ]
    selected_light_idx = -1
    
    running = True
    while running:
        # 1. Update Environment
        for shard in shards:
            shard.update()
            
        # 2. Handle Inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click Draw
                    current_draw.append(list(event.pos))
                if event.button == 3: # Right Click - Grab closest light
                    mx, my = event.pos
                    d0 = dist_sq([mx, my], lights[0]['pos'])
                    d1 = dist_sq([mx, my], lights[1]['pos'])
                    selected_light_idx = 0 if d0 < d1 else 1

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3:
                    selected_light_idx = -1

            if event.type == pygame.MOUSEMOTION:
                if selected_light_idx != -1:
                    lights[selected_light_idx]['pos'] = list(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(current_draw) > 2:
                        shards.append(OrganicShard(current_draw))
                        current_draw = []
                if event.key == pygame.K_SPACE:
                    shards = []
                    current_draw = []

        # 3. Render Base
        screen.fill(BACKGROUND)
        light_surface.fill((0,0,0))
        
        # Draw Shards
        for shard in shards:
            poly = shard.points
            color = shard.get_color()
            pygame.draw.polygon(screen, (*color, 50), poly, 1)
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*color, 20), poly)
            screen.blit(s, (0,0))

        # 4. The Physics of Light
        # R, G, B Channels for Dispersion
        base_channels = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        
        for light in lights:
            lx, ly = light['pos']
            l_col = light['color']
            
            for i, wave_mod in enumerate(WAVELENGTHS): 
                # Determine if this light emits this wavelength
                # Cyan (0,255,255) has no Red component, so Red rays are skipped
                if l_col[i] == 0: 
                    continue
                    
                channel_color = [0, 0, 0]
                channel_color[i] = 255 # Pure primary color
                
                # Cast rays
                for angle in range(0, 360, int(360/RAYS_PER_SOURCE)):
                    # Add slight rotation drift
                    rad = math.radians(angle + (pygame.time.get_ticks()*0.01)) 
                    dx = math.cos(rad)
                    dy = math.sin(rad)
                    
                    rx, ry = lx, ly
                    rdx, rdy = dx, dy
                    
                    path = [(rx, ry)]
                    
                    for _ in range(MAX_BOUNCES):
                        closest_t = 2000
                        hit_normal = None
                        hit_shard = None
                        
                        # Find intersection
                        for shard in shards:
                            pts = shard.points
                            for j in range(len(pts)):
                                p1 = pts[j]
                                p2 = pts[(j+1)%len(pts)]
                                
                                ray_end = (rx + rdx * 2000, ry + rdy * 2000)
                                t = intersect((rx, ry), ray_end, p1, p2)
                                
                                if t and t * 2000 < closest_t:
                                    closest_t = t * 2000
                                    n = get_normal(p1, p2)
                                    n = normalize(n)
                                    hit_normal = n
                                    hit_shard = shard

                        if hit_shard:
                            rx += rdx * closest_t
                            ry += rdy * closest_t
                            path.append((rx, ry))
                            
                            # Interaction Heat
                            hit_shard.energy = min(1.0, hit_shard.energy + 0.005)
                            
                            dot_prod = rdx * hit_normal[0] + rdy * hit_normal[1]
                            entering = dot_prod < 0
                            
                            normal = hit_normal
                            if not entering:
                                normal = (-hit_normal[0], -hit_normal[1])
                            
                            # Snell's Law with Dispersion
                            eff_ior = hit_shard.current_ior * wave_mod
                            eta = 1.0 / eff_ior if entering else eff_ior / 1.0
                            
                            new_dir = refract((rdx, rdy), normal, eta)
                            
                            if new_dir:
                                rdx, rdy = new_dir
                            else:
                                ref = reflect((rdx, rdy), normal)
                                rdx, rdy = ref       
                        else:
                            path.append((rx + rdx * 2000, ry + rdy * 2000))
                            break
                    
                    if len(path) > 1:
                        pygame.draw.lines(light_surface, channel_color, False, path, 1)

        # 5. Composite
        screen.blit(light_surface, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # Draw Suns
        pygame.draw.circle(screen, lights[0]['color'], (int(lights[0]['pos'][0]), int(lights[0]['pos'][1])), 12)
        pygame.draw.circle(screen, lights[1]['color'], (int(lights[1]['pos'][0]), int(lights[1]['pos'][1])), 12)
        
        # Draw drawing line
        if len(current_draw) > 0:
             pygame.draw.lines(screen, (200, 200, 200), False, current_draw + [pygame.mouse.get_pos()], 1)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()