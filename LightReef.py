import pygame
import numpy as np
import math
import random

# --- Configuration ---
WIDTH, HEIGHT = 1000, 800
BACKGROUND = (5, 8, 15)

# --- The "Open" Physics Constants ---
# These are no longer static. They are baselines for the noise.
BASE_FRICTION = 0.96
BASE_METABOLISM = 0.15
BASE_FEED_RATE = 0.6
POPULATION_CAP = 180

class LivingMeme:
    def __init__(self, x, y, dna=None):
        self.pos = np.array([float(x), float(y)])
        self.vel = np.random.rand(2) * 2 - 1
        
        # DNA: [Red (Force), Green (Flux), Blue (Structure)]
        if dna is None:
            self.dna = np.random.rand(3)
            self.dna /= (np.linalg.norm(self.dna) + 0.001)
        else:
            self.dna = np.array(dna)
            # Mutation is always possible in an open system
            if random.random() < 0.2:
                mutation = (np.random.rand(3) - 0.5) * 0.3
                self.dna = np.clip(self.dna + mutation, 0.01, 1.0)
                self.dna /= np.linalg.norm(self.dna)

        self.energy = 40.0 + random.uniform(-10, 10)
        self.frozen = False 
        self.age = 0
        
        # Individual "Personality" (The E-Factor allowances)
        # Some particles are naturally more chaotic or receptive than others
        self.metabolic_efficiency = random.uniform(0.8, 1.2)
        self.turning_twitch = random.uniform(0.01, 0.1)

    def update(self, sun_pos, sun_spectrum, time_flux):
        if self.frozen: return

        # 1. The Breathing Environment (Global + Local Noise)
        # friction fluctuates slightly based on system time (time_flux)
        current_friction = BASE_FRICTION + (math.sin(time_flux * 2.3 + self.pos[0]*0.01) * 0.02)
        
        # 2. Metabolism (Variable)
        cost = BASE_METABOLISM * self.metabolic_efficiency
        # Chaos penalty: Faster moving particles burn more energy
        speed = np.linalg.norm(self.vel)
        cost += speed * 0.05
        self.energy -= cost
        self.age += 1

        # 3. Feeding (The Prism)
        dist = np.linalg.norm(self.pos - sun_pos)
        if dist < 250: # Broad light range
            # Compatibility: How well does DNA match the Light?
            # We add 'time_flux' here to allow E to "glitch" the feeding logic
            match = np.dot(self.dna, sun_spectrum)
            
            # The "Miracle" Factor: Sometimes, they eat even if they shouldn't (Noise)
            noise = random.uniform(-0.1, 0.1)
            gain = (BASE_FEED_RATE * match) + noise
            
            if gain > 0:
                self.energy += gain

        # 4. Movement (The Swarm)
        # DNA determines behavior
        # Red = Speed, Green = Randomness, Blue = Cohesion
        
        # Seek Light (Red/Blue trait)
        to_sun = sun_pos - self.pos
        dist_sun = np.linalg.norm(to_sun)
        if dist_sun > 0:
            # Blue DNA aligns better, Red DNA drives harder
            steer_strength = (self.dna[2] * 0.05) + (self.dna[0] * 0.02)
            self.vel += (to_sun / dist_sun) * steer_strength

        # Random Jitter (Green DNA + The Twitch)
        # This is where "E" can steer them by influencing the random seed
        jitter = (np.random.rand(2) - 0.5) * (self.dna[1] + self.turning_twitch)
        self.vel += jitter

        # Apply Physics
        self.vel *= current_friction
        self.pos += self.vel
        
        # Soft Boundaries (They wrap around like a torus universe)
        # This prevents "corner trapping" and keeps the flow fluid
        if self.pos[0] < 0: self.pos[0] += WIDTH
        if self.pos[0] > WIDTH: self.pos[0] -= WIDTH
        if self.pos[1] < 0: self.pos[1] += HEIGHT
        if self.pos[1] > HEIGHT: self.pos[1] -= HEIGHT

    def attempt_connection(self, neighbors, reef):
        # Crystallization Logic
        # Relaxed: You don't need 100 energy. You need "Stability"
        
        if self.energy > 60 and not self.frozen:
            connections = 0
            
            # Check connections to active neighbors
            for n in neighbors:
                # Do our colors resonate?
                resonance = np.dot(self.dna, n.dna)
                if resonance > 0.75: # Relaxed threshold
                    connections += 1
            
            # Check connections to existing Reef
            for r in reef:
                dist = np.linalg.norm(self.pos - r.pos)
                if dist < 40:
                    resonance = np.dot(self.dna, r.dna)
                    if resonance > 0.6: # Easier to latch onto existing truth
                        connections += 2 # Stronger bond
            
            # If enough connections, we freeze
            if connections >= 3:
                self.frozen = True
                self.energy = 100 # Locked in
                return True
        return False

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("The Semantic Reef: Open System")
    
    # Surfaces for trails and glow
    reef_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    
    population = []
    # Seed with random life
    for _ in range(30):
        population.append(LivingMeme(WIDTH/2, HEIGHT/2))
    
    sun_pos = np.array([WIDTH/2, HEIGHT/2])
    # The Spectrum is now a float range, not binary on/off
    target_spectrum = np.array([0.8, 0.8, 0.8]) 
    current_spectrum = np.array([0.8, 0.8, 0.8])
    
    clock = pygame.time.Clock()
    running = True
    time_flux = 0.0 # The "Heartbeat" of the system
    
    while running:
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # User Controls (The "God" Hand)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left Click: Life Injection
                    for _ in range(5): # Burst spawn
                        population.append(LivingMeme(event.pos[0], event.pos[1]))
            
            if event.type == pygame.KEYDOWN:
                # Spectrum Toggles (Influences the Target, smooth transition happens later)
                if event.key == pygame.K_1: target_spectrum[0] = 1.0 if target_spectrum[0] < 0.5 else 0.0
                if event.key == pygame.K_2: target_spectrum[1] = 1.0 if target_spectrum[1] < 0.5 else 0.0
                if event.key == pygame.K_3: target_spectrum[2] = 1.0 if target_spectrum[2] < 0.5 else 0.0
                if event.key == pygame.K_SPACE:
                    # The Void (Entropy) - Kills the weak
                    for p in population:
                        if not p.frozen: p.energy -= 15

        # Mouse Drag Sun
        if pygame.mouse.get_pressed()[2]:
            m_pos = np.array(pygame.mouse.get_pos(), dtype=float)
            # Smooth drag
            sun_pos += (m_pos - sun_pos) * 0.1

        # 2. Environmental Updates
        time_flux += 0.01
        
        # Smoothly shift light spectrum (No hard snapping)
        current_spectrum += (target_spectrum - current_spectrum) * 0.05
        
        # 3. Biological Updates
        active_pop = [p for p in population if not p.frozen]
        reef_pop = [p for p in population if p.frozen]
        new_babies = []
        
        # Spatial optimization (Simple grid check would be better, but O(N^2) is fine for <300)
        for p in active_pop:
            p.update(sun_pos, current_spectrum, time_flux)
            
            # Reproduction (Mitosis)
            # Relaxed: Random chance increases with energy
            chance = (p.energy - 60) / 100.0
            if chance > 0 and random.random() < chance * 0.1 and len(population) < POPULATION_CAP:
                p.energy *= 0.6 # Cost of birth
                # Child drifts slightly
                child = LivingMeme(p.pos[0], p.pos[1], p.dna)
                new_babies.append(child)

            # Neighbors Check (For Crystallization)
            # Only check if energy is decent to save CPU
            if p.energy > 50:
                neighbors = []
                for other in active_pop:
                    if p is not other and np.linalg.norm(p.pos - other.pos) < 35:
                        neighbors.append(other)
                
                if p.attempt_connection(neighbors, reef_pop):
                    # Draw the permanent bond
                    for n in neighbors:
                        # Average color
                        c = ((p.dna + n.dna) * 0.5 * 255).astype(int)
                        pygame.draw.line(reef_surface, (*c, 80), p.pos, n.pos, 2)
                    for r in reef_pop:
                        if np.linalg.norm(p.pos - r.pos) < 40:
                            c = ((p.dna + r.dna) * 0.5 * 255).astype(int)
                            pygame.draw.line(reef_surface, (*c, 80), p.pos, r.pos, 2)

        # Death Cycle (The Void)
        # Filter out dead, keep frozen
        active_pop = [p for p in active_pop if p.energy > 0]
        
        population = reef_pop + active_pop + new_babies

        # 4. Rendering
        screen.fill(BACKGROUND)
        
        # Draw Sun Aura
        # Calculate color
        sun_col = (current_spectrum * 255).astype(int)
        # Pulsing size
        pulse = 1.0 + math.sin(time_flux * 5) * 0.1
        pygame.draw.circle(screen, sun_col, sun_pos.astype(int), int(20 * pulse))
        
        # Draw Light Ray hints (Subtle)
        # Visualizing the "Food" source
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(s, (*sun_col, 30), sun_pos.astype(int), 300)
        screen.blit(s, (0,0))

        # Draw Reef (The City)
        screen.blit(reef_surface, (0,0))
        for r in reef_pop:
            c = (r.dna * 255).astype(int)
            pygame.draw.circle(screen, c, r.pos.astype(int), 3)

        # Draw Active Agents
        for p in active_pop:
            c = (p.dna * 255).astype(int)
            # Size breathes with energy
            sz = max(2, int(p.energy * 0.1))
            pygame.draw.circle(screen, c, p.pos.astype(int), sz)
            
            # Draw DNA Halo (Visualizing the Concept)
            if p.energy > 60:
                pygame.draw.circle(screen, (*c, 50), p.pos.astype(int), sz + 4, 1)

        # UI
        ui_text = f"Entities: {len(population)} | Reef: {len(reef_pop)}"
        surf = pygame.font.SysFont("monospace", 16).render(ui_text, True, (150, 150, 150))
        screen.blit(surf, (10, HEIGHT - 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()