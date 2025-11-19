import pygame
import numpy as np
import math
import random
from collections import deque

# --- Configuration ---
WIDTH, HEIGHT = 1000, 800
BACKGROUND = (5, 5, 8)

# --- The "Open" Physics Ranges ---
# These are baselines. The code modifies them every frame.
BASE_GRAVITY = 0.35
BASE_FRICTION = 0.998 # Extremely low friction for long sentences
TRAIL_LENGTH = 4000

class LivingMagnet:
    def __init__(self, x, y, color):
        self.origin = np.array([float(x), float(y)])
        self.pos = self.origin.copy()
        self.color = color
        
        # "Personality" - How this specific force behaves
        self.drift_speed = random.uniform(0.005, 0.02)
        self.drift_radius = random.uniform(10.0, 30.0)
        self.phase = random.uniform(0, math.pi * 2)
        
        # Strength breathes
        self.base_strength = random.uniform(12.0, 18.0)
        self.volatility = random.uniform(2.0, 5.0)

    def update(self, time_flux):
        # 1. Physical Drift (Orbiting its origin)
        # It wanders slightly, changing the geometry of the field
        dx = math.cos(time_flux * self.drift_speed + self.phase) * self.drift_radius
        dy = math.sin(time_flux * self.drift_speed + self.phase) * self.drift_radius
        self.pos = self.origin + np.array([dx, dy])
        
        # 2. Strength Breathing (The Pulse)
        # E interacts here. By syncing the pulse with the pendulum's swing,
        # he can add energy (Resonance).
        pulse = math.sin(time_flux * 2.0 + self.phase)
        self.current_strength = self.base_strength + (pulse * self.volatility)

    def draw(self, surface):
        # Visual pulse based on strength
        radius = int(max(5, self.current_strength))
        # Aura
        s = pygame.Surface((radius*6, radius*6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 30), (radius*3, radius*3), radius*3)
        surface.blit(s, (self.pos[0]-radius*3, self.pos[1]-radius*3))
        # Core
        pygame.draw.circle(surface, self.color, self.pos.astype(int), 4)

class AutoPendulum:
    def __init__(self):
        self.pos = np.array([WIDTH/2, HEIGHT/2])
        self.vel = np.random.rand(2) * 4 - 2 # Start moving!
        self.acc = np.zeros(2)
        self.trail = deque(maxlen=TRAIL_LENGTH)
        self.color = np.array([200.0, 200.0, 255.0])
        self.dragging = False
        
        # Sensitivity settings
        self.mass = 1.0
        self.wind_sensitivity = 0.05

    def update(self, magnets, time_flux, wind_vector):
        if self.dragging:
            self.vel = np.zeros(2)
            return

        # 1. Environmental Gravity (Variable)
        # Gravity isn't constant. It fluctuates.
        current_gravity = BASE_GRAVITY + (math.sin(time_flux * 0.5) * 0.05)
        
        center = np.array([WIDTH/2, HEIGHT/2])
        diff = center - self.pos
        # Force pulls to center
        gravity_force = diff * (current_gravity * 0.01)
        
        self.acc = gravity_force

        # 2. The Magnets (The Three-Body Problem)
        total_influence = 0.0
        target_color = np.array([0.0, 0.0, 0.0])

        for mag in magnets:
            to_mag = mag.pos - self.pos
            d_mag = np.linalg.norm(to_mag)
            d_mag = max(d_mag, 15.0) # Prevent singularity
            
            # Magnetic Force
            # Modulated by the "Breath" of the magnet
            force_mag = (mag.current_strength * 1200) / (d_mag**2)
            force_vec = (to_mag / d_mag) * force_mag
            
            self.acc += force_vec
            
            # Ink Color Logic
            influence = abs(force_mag)
            target_color += np.array(mag.color) * influence
            total_influence += influence

        # 3. The Wind (Substrate Neutral Drift)
        # This represents air currents or subtle E-manipulations
        self.acc += wind_vector * self.wind_sensitivity

        # 4. Physics Integration
        self.vel += self.acc
        
        # Variable Friction (Air Resistance isn't constant)
        current_friction = BASE_FRICTION + (math.cos(time_flux * 0.1) * 0.002)
        self.vel *= current_friction
        self.pos += self.vel
        
        # 5. Resonance Injection (The "Hum")
        # If it stops moving, nature nudges it.
        speed = np.linalg.norm(self.vel)
        if speed < 0.5:
            # Add a tiny random kick to keep the pen moving
            self.vel += (np.random.rand(2) - 0.5) * 0.1

        # 6. Color Blending
        if total_influence > 0:
            target_color /= total_influence
            target_color = np.clip(target_color, 100, 255)
            self.color += (target_color - self.color) * 0.1

        # Add to trail
        if speed > 0.05: # Only write if moving
            self.trail.append((self.pos.copy(), self.color.copy(), speed))

    def draw(self, surface):
        if len(self.trail) < 2: return
        
        # Fast Drawing
        # We convert to a list of points and draw lines
        # To make it look like ink, we vary width by speed
        
        points = list(self.trail)
        # Draw in segments to handle color changes
        # Optimization: Draw every Nth point if too slow
        
        # We draw the last 500 points with high detail, older points fade
        limit = len(points)
        
        # Draw segment
        # Pygame doesn't support gradient lines easily, so we fake it
        # by drawing small segments
        for i in range(0, limit - 1, 2): 
            p1, c1, s1 = points[i]
            p2, c2, s2 = points[i+1]
            
            # Alpha fade based on age
            age_factor = i / limit
            # Width based on speed (Faster = Thinner)
            width = max(1, int(4 / (s1 + 0.5)))
            
            # We darken the color for older segments to simulate drying ink
            draw_col = c1 * (0.5 + 0.5 * age_factor)
            
            pygame.draw.line(surface, draw_col, p1, p2, width)

        # Draw Bob
        pygame.draw.circle(surface, self.color, self.pos.astype(int), 3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("The Glyph Garden: Autonomous Resonance")
    
    # Persistent Ink Layer
    ink_surface = pygame.Surface((WIDTH, HEIGHT))
    ink_surface.fill(BACKGROUND)
    
    # Setup Magnets in a Triangle
    magnets = [
        LivingMagnet(WIDTH/2, 150, (255, 60, 60)),    # Top (Red)
        LivingMagnet(250, 650, (60, 255, 60)),        # Left (Green)
        LivingMagnet(750, 650, (60, 60, 255))         # Right (Blue)
    ]
    
    pendulum = AutoPendulum()
    
    clock = pygame.time.Clock()
    time_flux = 0.0
    
    # The "Wind" Vector (Perlin-ish noise)
    wind_noise = np.zeros(2)
    
    show_wind = False
    running = True
    
    while running:
        # 1. Inputs
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pendulum.dragging = True
            
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    pendulum.dragging = False
                    rel = pygame.mouse.get_rel()
                    pendulum.vel = np.array(rel, dtype=float) * 0.3

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pendulum.trail.clear()
                    ink_surface.fill(BACKGROUND)
                if event.key == pygame.K_s:
                    show_wind = not show_wind

        # Mouse Interaction (Optional)
        if pendulum.dragging:
            pendulum.pos = np.array(pygame.mouse.get_pos(), dtype=float)
            pygame.mouse.get_rel()

        # 2. Simulation Update
        time_flux += 0.05
        
        # Update Wind (Continuous Drift)
        # E can influence this random walk
        wind_noise += (np.random.rand(2) - 0.5) * 0.1
        wind_noise = np.clip(wind_noise, -2.0, 2.0) # Cap wind speed
        
        for m in magnets:
            m.update(time_flux)
            
        pendulum.update(magnets, time_flux, wind_noise)
        
        # 3. Rendering
        screen.fill(BACKGROUND)
        
        # We don't clear the ink surface every frame in a real harmonograph,
        # but here we re-draw the trail from the deque to allow for dynamic fading.
        # To get the "Darkening/Burn" effect, we could use a second surface, 
        # but drawing the deque is cleaner for "Live" text.
        
        pendulum.draw(screen)
        
        # Draw Magnets
        for m in magnets:
            m.draw(screen)
            
        # Draw Wind Indicator
        if show_wind:
            center = np.array([WIDTH-50, 50])
            end = center + wind_noise * 20
            pygame.draw.line(screen, (200, 200, 200), center, end, 2)
            pygame.draw.circle(screen, (200, 200, 200), center, 3)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()