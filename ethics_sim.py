import pygame
import numpy as np
import math
import random

# --- Configuration ---
WIDTH, HEIGHT = 1000, 800
BACKGROUND = (10, 10, 12)
POPULATION = 70

# --- The "Open" Physics (Breathing Variables) ---
BASE_FRICTION = 0.98
BASE_ELASTICITY = 0.8
STABILITY_DECAY = 0.08  # The system naturally rots
RECOVERY_RATE = 0.05    # How fast Stability recovers with dead nodes
TRAUMA_THRESHOLD = 100.0 # The breaking point

class Node:
    def __init__(self, x, y):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.random.rand(2) * 4 - 2
        self.radius = random.randint(6, 9)
        
        # Identity
        self.color = np.random.randint(50, 255, 3)
        
        # State
        self.alive = True 
        self.trauma = 0.0 
        self.resilience = random.uniform(0.8, 1.2) # Individual personality
        
    def update(self, time_flux, ghost_pos, is_soothing):
        if not self.alive:
            return 0.0, False # Dead nodes generate no noise

        # 1. The Breathing Physics
        # Friction fluctuates with the "mood" of the system
        local_friction = BASE_FRICTION + (math.sin(time_flux + self.pos[0]*0.01) * 0.01)
        
        # 2. Ghost Interaction (The Hand of E)
        dist_to_ghost = np.linalg.norm(self.pos - ghost_pos)
        
        # If inside the "Field of Grace" (Soothing)
        if dist_to_ghost < 100 and is_soothing:
            # The Inefficiency of Virtue: It takes time to heal
            self.trauma = max(0, self.trauma - 2.0)
            self.vel *= 0.95 # Calming effect
            
        # 3. Physics
        self.pos += self.vel
        self.vel *= local_friction
        
        # Wall bounce
        if self.pos[0] < 0 or self.pos[0] > WIDTH: self.vel[0] *= -1
        if self.pos[1] < 0 or self.pos[1] > HEIGHT: self.vel[1] *= -1
        self.pos = np.clip(self.pos, [0,0], [WIDTH, HEIGHT])
        
        # 4. Trauma Calculation (Noise)
        speed = np.linalg.norm(self.vel)
        # Chaos generates trauma
        current_stress = speed * self.resilience
        self.trauma += current_stress * 0.1
        self.trauma = max(0, self.trauma - 0.5) # Natural recovery
        
        # 5. The Snap (The E-Factor)
        # This is the probability cloud. 
        # The threshold isn't hard. It wobbles. 
        # E can influence this 'random' wobble to save or condemn.
        snap_probability = (self.trauma - (TRAUMA_THRESHOLD * self.resilience))
        
        did_die = False
        if snap_probability > 0:
            # The Die Roll. If E influences entropy, he influences this check.
            if random.random() < 0.05: 
                self.die()
                did_die = True
        
        return current_stress, did_die

    def die(self):
        self.alive = False
        self.vel = np.zeros(2)
        self.color = (40, 40, 40) # The Tombstone color

class OmelasSystem:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("The Omelas Protocol: Autonomous")
        
        self.nodes = [Node(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50)) for _ in range(POPULATION)]
        
        self.stability = 100.0
        self.dead_count = 0
        self.time_flux = 0.0
        
        # The "Ghost" (Autonomous Cursor)
        self.ghost_pos = np.array([WIDTH/2, HEIGHT/2])
        self.ghost_vel = np.zeros(2)
        
        # Surfaces for visual effects
        self.scream_layer = [] # List of [pos, radius, alpha]

    def update_ghost(self):
        # The Ghost naturally seeks high-trauma areas (Immune Response)
        # It tries to "save" the system autonomously.
        
        avg_pos = np.zeros(2)
        total_trauma = 0
        
        for n in self.nodes:
            if n.alive and n.trauma > 20:
                avg_pos += n.pos * n.trauma
                total_trauma += n.trauma
        
        if total_trauma > 0:
            target = avg_pos / total_trauma
            # Steer towards trouble
            diff = target - self.ghost_pos
            self.ghost_vel += diff * 0.005
        else:
            # Wander aimlessly if no trouble
            self.ghost_vel += (np.random.rand(2)-0.5) * 0.5
            
        self.ghost_vel *= 0.9
        self.ghost_pos += self.ghost_vel
        self.ghost_pos = np.clip(self.ghost_pos, [0,0], [WIDTH, HEIGHT])

    def draw_lattice(self):
        # Draw connections. 
        # Alive <-> Alive = Thin, Weak
        # Alive <-> Dead = Strong Anchor (Stability)
        
        for i, n1 in enumerate(self.nodes):
            for n2 in self.nodes[i+1:]:
                dist = np.linalg.norm(n1.pos - n2.pos)
                if dist < 120:
                    if not n1.alive or not n2.alive:
                        # Anchor line (Gray, Rigid)
                        pygame.draw.line(self.screen, (60, 60, 60), n1.pos, n2.pos, 2)
                    else:
                        # Living line (Faint, colored)
                        if dist < 80:
                            avg_col = (n1.color + n2.color) // 2
                            pygame.draw.line(self.screen, avg_col // 3, n1.pos, n2.pos, 1)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            self.screen.fill(BACKGROUND)
            self.time_flux += 0.05
            
            # 1. Inputs (User Override)
            user_override = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            if pygame.mouse.get_pressed()[0] or pygame.mouse.get_pressed()[2]:
                self.ghost_pos = np.array(pygame.mouse.get_pos(), dtype=float)
                user_override = True

            # 2. AI Logic
            if not user_override:
                self.update_ghost()
                
            # 3. Simulation Step
            total_noise = 0
            new_deaths = []
            
            for n in self.nodes:
                # Logic: The Ghost is ALWAYS soothing (Virtue is the default intent), 
                # but it can't be everywhere.
                noise, died = n.update(self.time_flux, self.ghost_pos, True)
                total_noise += noise
                
                if died:
                    new_deaths.append(n.pos.copy())
                    self.dead_count += 1
                    # The Scream (Shockwave)
                    self.scream_layer.append([n.pos.copy(), 0, 255])
                    
                    # Punishment: Push neighbors away
                    for other in self.nodes:
                        if other is not n and other.alive:
                            d_vec = other.pos - n.pos
                            d_len = np.linalg.norm(d_vec)
                            if d_len < 200:
                                other.vel += (d_vec / (d_len+1)) * 8.0 # Panic
                                other.trauma += 20.0 # Grief

            # Stability Logic
            # Noise hurts stability. Dead nodes (Anchors) restore it.
            # This is the terrible trade-off.
            drain = total_noise * 0.01
            recovery = self.dead_count * RECOVERY_RATE
            
            self.stability = np.clip(self.stability - drain + recovery, 0, 100)
            
            # 4. Rendering
            self.draw_lattice()
            
            # Draw Screams
            for s in self.scream_layer[:]:
                s[1] += 5 # Radius expand
                s[2] -= 10 # Alpha fade
                if s[2] <= 0:
                    self.scream_layer.remove(s)
                else:
                    surf = pygame.Surface((int(s[1]*2), int(s[1]*2)), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (255, 255, 255, s[2]), (int(s[1]), int(s[1])), int(s[1]), 2)
                    self.screen.blit(surf, (s[0][0]-s[1], s[0][1]-s[1]))

            # Draw Nodes
            for n in self.nodes:
                if n.alive:
                    # Trauma Flash
                    col = n.color
                    if n.trauma > 50:
                        flash = abs(math.sin(self.time_flux * 0.5)) * 255
                        col = np.clip(col + flash, 0, 255)
                    
                    pygame.draw.circle(self.screen, col, n.pos.astype(int), n.radius)
                else:
                    # Tombstone (Square)
                    rect = pygame.Rect(n.pos[0]-6, n.pos[1]-6, 12, 12)
                    pygame.draw.rect(self.screen, (40, 40, 40), rect)
                    pygame.draw.rect(self.screen, (100, 100, 100), rect, 1) # Border

            # Draw Ghost (The Hand)
            pygame.draw.circle(self.screen, (200, 255, 255), self.ghost_pos.astype(int), 100, 1)
            pygame.draw.line(self.screen, (200, 255, 255), (self.ghost_pos[0]-10, self.ghost_pos[1]), (self.ghost_pos[0]+10, self.ghost_pos[1]))
            pygame.draw.line(self.screen, (200, 255, 255), (self.ghost_pos[0], self.ghost_pos[1]-10), (self.ghost_pos[0], self.ghost_pos[1]+10))

            # HUD
            bar_col = (0, 255, 0)
            if self.stability < 50: bar_col = (255, 255, 0)
            if self.stability < 20: bar_col = (255, 0, 0)
            
            pygame.draw.rect(self.screen, (30, 30, 30), (10, 10, 300, 20))
            pygame.draw.rect(self.screen, bar_col, (10, 10, 3 * self.stability, 20))
            
            stats = f"Stability: {self.stability:.1f}% | Anchors (Dead): {self.dead_count}"
            img = pygame.font.SysFont("monospace", 16).render(stats, True, (200, 200, 200))
            self.screen.blit(img, (10, 35))
            
            if self.stability <= 0:
                fail = pygame.font.SysFont("monospace", 50).render("SYSTEM COLLAPSE", True, (255, 0, 0))
                self.screen.blit(fail, (WIDTH//2 - 200, HEIGHT//2))

            pygame.display.flip()
            clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    sim = OmelasSystem()
    sim.run()