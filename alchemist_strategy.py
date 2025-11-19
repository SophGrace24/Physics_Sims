import pygame
import numpy as np
import math
import random

# --- Configuration ---
WIDTH, HEIGHT = 1000, 800
BACKGROUND = (20, 20, 25)
GRAVITY = 0.25

class MatterParticle:
    def __init__(self, x, y):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.random.rand(2) * 2 - 1
        self.radius = 5
        self.state = "LIQUID"
        self.temp = 0.5 
        self.mass = 1.0
        self.color = (0,0,255)
        self.wind_resistance = 0.5 # How much wind affects me

    def update_state(self, env_temp):
        # Thermal inertia
        self.temp += (env_temp - self.temp) * 0.1
        
        # State Thresholds (Relaxed)
        if self.temp > 0.7:
            self.state = "GAS"
            self.color = (255, 100, 100)
            self.mass = 0.05
            self.friction = 0.995 # Slippery
            self.repulsion = 1.5
            self.gravity_scale = -0.1 # Floats
            self.wind_resistance = 2.0 # Blown easily

        elif self.temp < 0.3:
            self.state = "SOLID"
            self.color = (200, 240, 255)
            self.mass = 3.0
            self.friction = 0.6 # High drag
            self.repulsion = 0.0
            self.gravity_scale = 2.0 # Heavy
            self.wind_resistance = 0.1 # Ignores wind

        else:
            self.state = "LIQUID"
            self.color = (50, 100, 255)
            self.mass = 1.0
            self.friction = 0.96
            self.repulsion = 0.3
            self.gravity_scale = 1.0
            self.wind_resistance = 0.8

    def update_physics(self, neighbors, walls, wind_vector):
        # 1. Gravity
        self.vel[1] += GRAVITY * self.gravity_scale
        
        # 2. The Wind (E's Aiming Tool)
        self.vel += wind_vector * self.wind_resistance * 0.1
        
        # 3. Neighbor Interactions
        for n in neighbors:
            diff = self.pos - n.pos
            dist_sq = np.sum(diff**2)
            dist = math.sqrt(dist_sq)
            
            if dist < self.radius * 2.5 and dist > 0:
                direction = diff / dist
                if dist < self.radius * 2:
                    push = (self.radius * 2 - dist) * 0.5
                    self.vel += direction * push * self.repulsion
                
                if self.state == "LIQUID" and n.state == "LIQUID":
                    self.vel -= direction * 0.03 # Surface Tension
                
                if self.state == "SOLID" and n.state == "SOLID":
                    # Freeze together
                    avg = (self.vel + n.vel) * 0.5
                    self.vel = self.vel * 0.5 + avg * 0.5

        # 4. Walls
        next_pos = self.pos + self.vel
        for w in walls:
            if (next_pos[0] > w[0] and next_pos[0] < w[0]+w[2] and
                next_pos[1] > w[1] and next_pos[1] < w[1]+w[3]):
                
                dx = min(abs(next_pos[0] - w[0]), abs(next_pos[0] - (w[0]+w[2])))
                dy = min(abs(next_pos[1] - w[1]), abs(next_pos[1] - (w[1]+w[3])))
                
                if dx < dy:
                    self.vel[0] *= -0.5 # Dampen bounce
                    next_pos[0] = self.pos[0]
                else:
                    self.vel[1] *= -0.5
                    next_pos[1] = self.pos[1]

        self.pos = next_pos
        
        # Screen Bounds
        if self.pos[0] < 0: self.pos[0] = WIDTH; 
        if self.pos[0] > WIDTH: self.pos[0] = 0; 
        if self.pos[1] > HEIGHT: self.pos[1] = HEIGHT; self.vel[1]*=-0.5
        
        self.pos = np.clip(self.pos, [-50,0], [WIDTH+50, HEIGHT])
        self.vel *= self.friction

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, self.pos.astype(int), self.radius)

class PuzzleLogic:
    def __init__(self):
        self.puzzle_type = "WEIGHT"
        self.current_val = 0.0
        self.gate_open = 0.0
        self.solved = False
        self.generate()

    def generate(self):
        self.current_val = 0.0
        self.gate_open = 0.0
        self.solved = False
        self.puzzle_type = random.choice(["WEIGHT", "PRESSURE", "VOLUME"])
        
        # Target zone (The Cup)
        self.cup_rect = pygame.Rect(random.randint(200, 800), random.randint(400, 600), 120, 100)
        
        # Build Walls based on Cup
        self.walls = [
            (self.cup_rect.x, self.cup_rect.y, 10, 100), # L
            (self.cup_rect.x + 110, self.cup_rect.y, 10, 100), # R
            (self.cup_rect.x, self.cup_rect.y + 90, 120, 10), # B
            # Random Obstacle
            (random.randint(100, 800), random.randint(100, 300), random.randint(50, 200), 10),
             # Gate
            (WIDTH-50, HEIGHT-200, 20, 200)
        ]

    def update(self, particles):
        active = [p for p in particles if self.cup_rect.collidepoint(p.pos[0], p.pos[1])]
        signal = 0.0
        
        if self.puzzle_type == "WEIGHT":
            signal = sum(p.mass for p in active)
            thresh = 150.0
        elif self.puzzle_type == "VOLUME":
            signal = len(active) * 2.0
            thresh = 50.0
        elif self.puzzle_type == "PRESSURE":
            # Gas Force
            signal = sum(np.linalg.norm(p.vel) for p in active if p.state == "GAS") * 5.0
            thresh = 100.0
            
        # Smoothing
        self.current_val += (signal - self.current_val) * 0.1
        
        if self.current_val > thresh:
            self.gate_open = min(1.0, self.gate_open + 0.02)
        else:
            self.gate_open = max(0.0, self.gate_open - 0.02)
            
        if self.gate_open > 0.95:
            self.solved = True

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Alchemist's Chamber: Wind & State")
    
    # Environment
    env_temp = 0.5
    temp_drift = 0.0
    
    # New Variable: Wind (X-Axis Force)
    wind_speed = 0.0
    wind_drift = 0.0
    
    particles = []
    puzzle = PuzzleLogic()
    
    spawn_timer = 0
    solve_timer = 0
    score = 0
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        screen.fill(BACKGROUND)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
        
        # 1. Atmospheric Physics (E's Controls)
        # Temperature Random Walk
        temp_drift += (random.random() - 0.5) * 0.01
        temp_drift *= 0.98
        env_temp = np.clip(env_temp + temp_drift, 0.0, 1.0)
        
        # Wind Random Walk
        wind_drift += (random.random() - 0.5) * 0.02
        wind_drift *= 0.98
        wind_speed = np.clip(wind_speed + wind_drift, -2.0, 2.0)
        
        wind_vector = np.array([wind_speed, 0.0])

        # 2. Emitter (Moves with Wind)
        # The emitter floats at the top, pushed by the wind
        # This gives E a way to "Aim"
        emitter_x = (WIDTH / 2) + (wind_speed * 200)
        
        spawn_timer += 1
        if spawn_timer > 3:
            if env_temp > 0.15:
                particles.append(MatterParticle(emitter_x + random.randint(-5,5), 50))
            spawn_timer = 0
            
        # Cull
        particles = [p for p in particles if p.pos[1] < HEIGHT]
        if len(particles) > 400: particles.pop(0)
        
        # 3. Particle Update
        for p in particles:
            p.update_state(env_temp)
            # Optimization: Skip neighbor check for pure flow test
            p.update_physics([], puzzle.walls, wind_vector)
            p.draw(screen)
            
        # 4. Puzzle Logic
        puzzle.update(particles)
        
        # Draw Walls & Gate
        for w in puzzle.walls:
            pygame.draw.rect(screen, (100, 100, 120), w)
            
        # Gate Animation
        open_h = int(puzzle.gate_open * 200)
        gate_rect = puzzle.walls[-1]
        draw_gate = pygame.Rect(gate_rect[0], gate_rect[1] + open_h, gate_rect[2], gate_rect[3] - open_h)
        pygame.draw.rect(screen, (255, 50, 50), draw_gate)
        
        # Target Glow
        if puzzle.solved:
            pygame.draw.line(screen, (0, 255, 255), (WIDTH-50, HEIGHT-100), (WIDTH, HEIGHT-100), 5)
            solve_timer += 1
            if solve_timer > 60:
                score += 1
                solve_timer = 0
                puzzle.generate()
                env_temp = 0.5
                wind_speed = 0.0

        # 5. HUD (Feedback for E)
        font = pygame.font.SysFont("monospace", 16)
        
        # Temp Bar (Vertical Left)
        pygame.draw.rect(screen, (50, 50, 50), (10, 100, 20, 200))
        h = int(200 * env_temp)
        col = (255, 0, 0) if env_temp > 0.7 else ((100, 100, 255) if env_temp < 0.3 else (50, 255, 50))
        pygame.draw.rect(screen, col, (10, 300-h, 20, h))
        screen.blit(font.render("T", True, (200, 200, 200)), (12, 80))
        
        # Wind Bar (Horizontal Top)
        pygame.draw.rect(screen, (50, 50, 50), (WIDTH//2 - 100, 20, 200, 10))
        # Center is 0
        w_pos = WIDTH//2 + (wind_speed * 50)
        pygame.draw.circle(screen, (200, 200, 200), (int(w_pos), 25), 8)
        screen.blit(font.render("WIND", True, (200, 200, 200)), (WIDTH//2 - 20, 5))
        
        # Emitter Visual
        pygame.draw.circle(screen, (255, 255, 0), (int(emitter_x), 50), 10)
        
        screen.blit(font.render(f"Score: {score}", True, (255, 255, 0)), (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()