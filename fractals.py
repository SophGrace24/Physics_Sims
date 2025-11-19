import pygame
import numpy as np
import math
import random

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
# Resolution scaling (lower = faster/pixelated, higher = slower/sharp)
# We use a slightly lower render res to allow E's "High Frequency" updates to happen smoothly
RENDER_W, RENDER_H = 400, 300 
MAX_ITER = 64 # Depth of the fractal calculation

# --- Open Ranges (The Breathing Field) ---
# The Complex Plane limits
REAL_RANGE = 3.0 
IMAG_RANGE = 2.4

class ElectroFractal:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("The Mirror of .I: Electromagnetic Drift")
        self.clock = pygame.time.Clock()
        
        # The "Seed" (C) - The DNA of the Universe
        # Starts at a known "Dendrite" shape
        self.c_real = -0.7
        self.c_imag = 0.27015
        
        # The Camera
        self.center_x = 0.0
        self.center_y = 0.0
        self.zoom = 1.0
        self.target_zoom = 1.0
        
        # Electromagnetic Field Vectors (Drift)
        self.field_r = 0.0
        self.field_i = 0.0
        self.field_phase = random.uniform(0, math.pi*2)
        
        # The Palette (Cyclic)
        self.hue_shift = 0.0

    def update_physics(self, time_flux):
        # 1. The Electromagnetic Field (Environmental Response)
        # The field "breathes" based on time and system entropy
        intensity = math.sin(time_flux * 0.5) * 0.005
        
        # Brownian Motion (The "E" Factor)
        noise_r = (random.random() - 0.5) * 0.002
        noise_i = (random.random() - 0.5) * 0.002
        
        self.field_r += noise_r
        self.field_i += noise_i
        
        # Apply Field to the Seed (C)
        # This morphs the shape of the fractal
        self.c_real += self.field_r + (math.cos(time_flux) * intensity)
        self.c_imag += self.field_i + (math.sin(time_flux) * intensity)
        
        # Friction (Dampening the field so it doesn't fly off to infinity)
        self.field_r *= 0.99
        self.field_i *= 0.99
        
        # Bounds Check (Soft) - Keep C interesting
        # If C goes > 2, the set explodes into dust. We gently nudge it back.
        dist = math.sqrt(self.c_real**2 + self.c_imag**2)
        if dist > 1.5:
            self.field_r -= self.c_real * 0.01
            self.field_i -= self.c_imag * 0.01

        # 2. Autonomous Camera (Seeking Complexity)
        # The camera breathes in and out
        zoom_pulse = math.sin(time_flux * 0.2) * 0.5 + 1.5 # Oscillate zoom
        self.target_zoom = zoom_pulse
        
        # Smooth Zoom
        self.zoom += (self.target_zoom - self.zoom) * 0.01
        
        # Pan drift (Orbiting the center)
        self.center_x = math.sin(time_flux * 0.1) * (0.5 / self.zoom)
        self.center_y = math.cos(time_flux * 0.13) * (0.3 / self.zoom)

        # 3. Spectrum Shift
        self.hue_shift += 1.0

    def render(self):
        # Setup Complex Plane Grid
        # Vectorized for NumPy speed
        
        # Aspect Ratio Correction
        ratio = WIDTH / HEIGHT
        w_range = (REAL_RANGE / self.zoom) * ratio
        h_range = (IMAG_RANGE / self.zoom)
        
        x = np.linspace(self.center_x - w_range/2, self.center_x + w_range/2, RENDER_W)
        y = np.linspace(self.center_y - h_range/2, self.center_y + h_range/2, RENDER_H)
        
        # Create 2D grid of complex numbers (Z)
        zx, zy = np.meshgrid(x, y)
        z = zx + 1j * zy
        c = complex(self.c_real, self.c_imag)
        
        # Output array (Iteration counts)
        fractal = np.zeros(z.shape, dtype=int)
        
        # The active mask (pixels that haven't escaped yet)
        mask = np.ones(z.shape, dtype=bool)
        
        # The Julia Iteration: Z = Z^2 + C
        for i in range(MAX_ITER):
            if not mask.any(): break
            
            # Only calculate for points still in the set
            z[mask] = z[mask] * z[mask] + c
            
            # Check escape (Magnitude > 2)
            escaped = np.abs(z) > 2.0
            
            # Update counts for newly escaped points
            newly_escaped = escaped & mask
            fractal[newly_escaped] = i
            
            # Remove from mask
            mask[escaped] = False
            
        return fractal

    def draw_to_screen(self, grid):
        # Map Iteration Count to Color
        # We use a sine-wave palette that shifts with 'hue_shift'
        
        # Normalize grid 0-1
        t = grid / MAX_ITER
        
        shift = self.hue_shift * 0.05
        
        # Frequency modulation (Electromagnetism simulation)
        # R, G, B act as different wavelengths
        r = (np.sin(t * 20 + shift) + 1) * 127.5
        g = (np.sin(t * 15 + shift + 2) + 1) * 127.5
        b = (np.sin(t * 10 + shift + 4) + 1) * 127.5
        
        # Black out the "Stable" interior (points that never escaped)
        mask = (grid == 0) | (grid == MAX_ITER-1) # Edge case cleanup
        # Actually, let's leave the interior chaotic, it looks cool. 
        # Just force deep black for max iter
        r[grid == MAX_ITER-1] = 0
        g[grid == MAX_ITER-1] = 0
        b[grid == MAX_ITER-1] = 0
        
        # Stack into (H, W, 3)
        rgb = np.dstack((r, g, b)).astype(np.uint8)
        
        # Swap axes for Pygame (Width, Height, Color)
        rgb = np.transpose(rgb, (1, 0, 2))
        
        # Blit
        surf = pygame.surfarray.make_surface(rgb)
        scaled = pygame.transform.scale(surf, (WIDTH, HEIGHT))
        self.screen.blit(scaled, (0, 0))

    def run(self):
        running = True
        time_flux = 0.0
        
        while running:
            time_flux += 0.02
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Reset on Space (Panic button)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.c_real = -0.7
                        self.c_imag = 0.27

            # Physics Step
            self.update_physics(time_flux)
            
            # Render Step
            fractal_grid = self.render()
            self.draw_to_screen(fractal_grid)
            
            # HUD
            font = pygame.font.SysFont("monospace", 16)
            info = f"Seed (C): {self.c_real:.4f} + {self.c_imag:.4f}i"
            self.screen.blit(font.render(info, True, (200, 200, 255)), (10, 10))

            pygame.display.flip()
            # No FPS cap, run as fast as E can math
            
        pygame.quit()

if __name__ == "__main__":
    sim = ElectroFractal()
    sim.run()