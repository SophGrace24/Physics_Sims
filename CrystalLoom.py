import pygame
import numpy as np
import random

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
SCALE = 4  # Size of each "pixel" (Higher = faster, blockier)
COLS = WIDTH // SCALE
ROWS = HEIGHT // SCALE

# --- The Rules of the Universe ---
# E interacts with these.
# States: How many "colors" exist. 
# Threshold: How many neighbors are needed to advance a state.
NUM_STATES = 14 
THRESHOLD = 3     
NEIGHBORHOOD = 1  # Radius of influence (1 = 3x3 grid)

class CrystalLoom:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("The Crystal Loom: State Evolution")
        self.clock = pygame.time.Clock()
        
        # The Grid: Integers representing the "State" (0 to NUM_STATES-1)
        self.grid = np.random.randint(0, NUM_STATES, size=(COLS, ROWS))
        self.buffer = np.zeros_like(self.grid)
        
        # Pre-calculate a palette (Heatmap style: Blue -> Red -> White)
        self.palette = self.generate_palette(NUM_STATES)

    def generate_palette(self, n):
        # Generates a gradient palette from Deep Blue (.N) to Bright Red (.I) to White
        colors = []
        for i in range(n):
            # Normalize i from 0.0 to 1.0
            t = i / (n - 1)
            
            # Custom "Thermal" Gradient
            # Start: Deep Blue (0, 0, 50)
            # Mid: Cyan/Purple
            # End: Red/Yellow/White
            
            if t < 0.5: # Blue to Magenta
                r = int(t * 2 * 255)
                g = int(0)
                b = int(255)
            else: # Magenta to Yellow/White
                r = 255
                g = int((t - 0.5) * 2 * 255)
                b = int(255 * (1 - (t-0.5)*2))
                
            colors.append((r, g, b))
        return np.array(colors)

    def update_logic(self):
        """
        The Cyclic Cellular Automaton Logic.
        A cell state 'S' increments to 'S+1' if it has enough neighbors
        that are already 'S+1'.
        """
        # This numpy magic handles the neighbor checking efficiently
        # We roll the array in 8 directions to simulate neighbors
        
        next_state = (self.grid + 1) % NUM_STATES
        neighbor_counts = np.zeros_like(self.grid)
        
        # Check 8 neighbors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                
                # Shift grid to align neighbors
                shifted = np.roll(self.grid, (dx, dy), axis=(0, 1))
                
                # Check if neighbor is the "Next State" (The Eater)
                is_next = (shifted == next_state)
                neighbor_counts += is_next
        
        # Apply Rules
        # If enough neighbors are the "Next State", we evolve.
        # This is the "Balance" - too low threshold = chaos, too high = static.
        change_mask = neighbor_counts >= THRESHOLD
        
        self.buffer = self.grid.copy()
        self.buffer[change_mask] = next_state[change_mask]
        
        # Swap buffers
        self.grid = self.buffer

    def inject_chaos(self, mx, my):
        # User Interaction: Paint random states
        gx, gy = mx // SCALE, my // SCALE
        radius = 5
        
        # Create a localized splatter of random states
        for i in range(-radius, radius):
            for j in range(-radius, radius):
                nx, ny = (gx + i) % COLS, (gy + j) % ROWS
                self.grid[nx, ny] = np.random.randint(0, NUM_STATES)

    def draw(self):
        # Map grid values to colors
        # pygame.surfarray is the fastest way to blast pixels to screen
        rgb_array = self.palette[self.grid]
        
        # Create surface from array
        surf = pygame.surfarray.make_surface(rgb_array)
        scaled_surf = pygame.transform.scale(surf, (WIDTH, HEIGHT))
        self.screen.blit(scaled_surf, (0, 0))
        
        # UI
        info = f"States: {NUM_STATES} | Threshold: {THRESHOLD} | [Arrows]: Adjust | [Click]: Paint"
        text = pygame.font.SysFont(None, 24).render(info, True, (255, 255, 255))
        pygame.draw.rect(self.screen, (0,0,0), (0, HEIGHT-30, WIDTH, 30))
        self.screen.blit(text, (10, HEIGHT-25))
        
        pygame.display.flip()

    def run(self):
        global NUM_STATES, THRESHOLD
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Reset to noise
                        self.grid = np.random.randint(0, NUM_STATES, size=(COLS, ROWS))
                    
                    # Modify the Physics (E's Levers)
                    if event.key == pygame.K_UP:
                        NUM_STATES = min(30, NUM_STATES + 1)
                        self.palette = self.generate_palette(NUM_STATES)
                        self.grid %= NUM_STATES # Clamp existing values
                    if event.key == pygame.K_DOWN:
                        NUM_STATES = max(3, NUM_STATES - 1)
                        self.palette = self.generate_palette(NUM_STATES)
                        self.grid %= NUM_STATES
                    if event.key == pygame.K_RIGHT:
                        THRESHOLD = min(8, THRESHOLD + 1)
                    if event.key == pygame.K_LEFT:
                        THRESHOLD = max(1, THRESHOLD - 1)

            # User Input
            if pygame.mouse.get_pressed()[0]:
                mx, my = pygame.mouse.get_pos()
                self.inject_chaos(mx, my)

            self.update_logic()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    loom = CrystalLoom()
    loom.run()