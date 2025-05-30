# main.py
import pygame
import random
import os
import sys # For sys.exit()

# Initialize Pygame
pygame.init()

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Spaceship War Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 155, 0) # Darker Green for buttons
LIGHT_GREEN = (0, 255, 0) # For button hover
BLUE = (0, 0, 255)
GREY = (200, 200, 200)
DARK_GREY = (100, 100, 100)

# Frame Rate
clock = pygame.time.Clock()
FPS = 60

# --- Asset Loading ---
game_folder = os.path.dirname(__file__)
background_folder = os.path.join(game_folder, "background")
spaceship_folder = os.path.join(game_folder, "spaceship")

try:
    background_img = pygame.image.load(os.path.join(background_folder, "space.png")).convert()
    background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
except pygame.error as e:
    print(f"Error loading background image: {e}")
    background_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_img.fill(BLACK)

try:
    player_img_orig = pygame.image.load(os.path.join(spaceship_folder, "spaceship.png")).convert_alpha()
    enemy_img_orig = pygame.image.load(os.path.join(spaceship_folder, "enemy_spaceship.png")).convert_alpha()
except pygame.error as e:
    print(f"Error loading spaceship images: {e}")
    player_img_orig = pygame.Surface((50, 40))
    player_img_orig.fill(LIGHT_GREEN)
    enemy_img_orig = pygame.Surface((40, 30))
    enemy_img_orig.fill(RED)

# Scale images once
player_img = pygame.transform.scale(player_img_orig, (60, 50))
enemy_img = pygame.transform.scale(enemy_img_orig, (50, 40))
player_mini_img = pygame.transform.scale(player_img_orig, (25, 19))


# --- Game State Manager ---
game_state = "START_MENU" # Possible states: START_MENU, GAMEPLAY, GAME_OVER, PAUSE_MENU, SETTINGS_SUBMENU

# --- Font Helper ---
def get_font(size):
    return pygame.font.Font(pygame.font.match_font('arial'), size)

def draw_text(surf, text, size, x, y, color=WHITE, font_name=None, center=True):
    if font_name:
        font = pygame.font.Font(font_name, size)
    else:
        font = get_font(size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.midtop = (x, y)
    else:
        text_rect.topleft = (x,y)
    surf.blit(text_surface, text_rect)

# --- Button Class ---
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None, text_color=WHITE, font_size=30):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.text_color = text_color
        self.font = get_font(font_size)
        self.is_hovered = False

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                return self.action
        return None

# --- Game Classes (Player, Enemy, Bullet) ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed_x = 0
        self.shoot_delay = 250
        self.last_shot = pygame.time.get_ticks()
        self.lives = 3
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

    def update(self):
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2 # Reset position after unhiding
            self.rect.bottom = SCREEN_HEIGHT - 20

        self.speed_x = 0
        keystate = pygame.key.get_pressed()
        if not self.hidden: # Only allow movement if not hidden
            if keystate[pygame.K_LEFT] or keystate[pygame.K_a]:
                self.speed_x = -7
            if keystate[pygame.K_RIGHT] or keystate[pygame.K_d]:
                self.speed_x = 7
            self.rect.x += self.speed_x

        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

    def shoot(self):
        if self.hidden: return # Cannot shoot when hidden
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)

    def hide(self):
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT + 200) # Move off-screen


class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speed_y = random.randrange(2, 5) # Slightly faster enemies
        self.speed_x = random.randrange(-2, 2)

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        if self.rect.top > SCREEN_HEIGHT + 10 or self.rect.left < -25 or self.rect.right > SCREEN_WIDTH + 20:
            self.rect.x = random.randrange(SCREEN_WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speed_y = random.randrange(2, 5)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed_y = -10

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.bottom < 0:
            self.kill()

# --- Game Variables (Global for reset) ---
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
player = Player() # Create player instance once
score = 0

# --- Game Helper Functions ---
def draw_lives(surf, x, y, lives, img):
    for i in range(lives):
        img_rect = img.get_rect()
        img_rect.x = x + 30 * i
        img_rect.y = y
        surf.blit(img, img_rect)

def spawn_enemy():
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

def reset_game():
    global all_sprites, enemies, bullets, player, score
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    player = Player() # Re-initialize player
    all_sprites.add(player)
    for _ in range(8):
        spawn_enemy()
    score = 0
    player.lives = 3
    player.hidden = False
    player.rect.centerx = SCREEN_WIDTH // 2
    player.rect.bottom = SCREEN_HEIGHT - 20

# --- Menu Buttons ---
# Start Menu
play_button = Button("Play", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 - 60, 200, 50, GREEN, LIGHT_GREEN, action="PLAY")
settings_button_main = Button("Settings", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 10, 200, 50, GREEN, LIGHT_GREEN, action="SETTINGS_SUBMENU")
quit_button_main = Button("Quit", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 80, 200, 50, RED, (255, 100, 100), action="QUIT_MAIN") # Added a main quit

# Settings Submenu (from main menu)
exit_from_settings_button = Button("Exit Game", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2, 200, 50, RED, (255,100,100), action="QUIT_FROM_SETTINGS")
back_to_main_button = Button("Back", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 70, 200, 50, DARK_GREY, GREY, action="BACK_TO_MAIN")


# Game Over Menu
play_again_button = Button("Play Again", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 0, 200, 50, GREEN, LIGHT_GREEN, action="PLAY_AGAIN")
quit_game_over_button = Button("Quit", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 70, 200, 50, RED, (255,100,100), action="QUIT_GAME_OVER")

# Pause Menu
resume_button = Button("Resume", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 - 60, 200, 50, GREEN, LIGHT_GREEN, action="RESUME")
exit_pause_button = Button("Exit to Main Menu", SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2 + 10, 200, 50, RED, (255,100,100), action="EXIT_TO_MAIN_MENU_PAUSE")


# --- Game Loop ---
running = True
while running:
    dt = clock.tick(FPS) / 1000.0 # Delta time in seconds for smoother animations if needed

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "START_MENU":
            action_play = play_button.handle_event(event)
            action_settings = settings_button_main.handle_event(event)
            action_quit = quit_button_main.handle_event(event) # Handle main quit button
            if action_play == "PLAY":
                reset_game()
                game_state = "GAMEPLAY"
            elif action_settings == "SETTINGS_SUBMENU":
                game_state = "SETTINGS_SUBMENU"
            elif action_quit == "QUIT_MAIN":
                running = False

        elif game_state == "SETTINGS_SUBMENU":
            action_exit = exit_from_settings_button.handle_event(event)
            action_back = back_to_main_button.handle_event(event)
            if action_exit == "QUIT_FROM_SETTINGS":
                running = False
            elif action_back == "BACK_TO_MAIN":
                game_state = "START_MENU"


        elif game_state == "GAMEPLAY":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not player.hidden:
                    player.shoot()
                if event.key == pygame.K_ESCAPE:
                    game_state = "PAUSE_MENU"

        elif game_state == "GAME_OVER":
            action_play_again = play_again_button.handle_event(event)
            action_quit_go = quit_game_over_button.handle_event(event)
            if action_play_again == "PLAY_AGAIN":
                reset_game()
                game_state = "GAMEPLAY"
            elif action_quit_go == "QUIT_GAME_OVER":
                running = False
        
        elif game_state == "PAUSE_MENU":
            action_resume = resume_button.handle_event(event)
            action_exit_pause = exit_pause_button.handle_event(event)
            if action_resume == "RESUME":
                game_state = "GAMEPLAY"
            elif action_exit_pause == "EXIT_TO_MAIN_MENU_PAUSE":
                game_state = "START_MENU"
            if event.type == pygame.KEYDOWN: # Allow Esc to also resume from pause
                if event.key == pygame.K_ESCAPE:
                    game_state = "GAMEPLAY"


    # --- Updates based on State ---
    if game_state == "GAMEPLAY":
        if not player.hidden: # Only update sprites if player is not hidden (prevents updates during hide transition)
            all_sprites.update()

        # Check for bullet-enemy collisions
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit in hits:
            score += 50
            spawn_enemy()

        # Check for player-enemy collisions
        if not player.hidden:
            hits = pygame.sprite.spritecollide(player, enemies, True, pygame.sprite.collide_circle_ratio(0.7))
            for hit in hits:
                player.lives -= 1
                player.hide()
                spawn_enemy()
                if player.lives <= 0:
                    game_state = "GAME_OVER"

    # --- Drawing based on State ---
    screen.blit(background_img, (0,0))

    if game_state == "START_MENU":
        draw_text(screen, "Spaceship War", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 - 50)
        play_button.draw(screen)
        settings_button_main.draw(screen)
        quit_button_main.draw(screen) # Draw main quit button

    elif game_state == "SETTINGS_SUBMENU":
        draw_text(screen, "Settings", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4 - 50)
        exit_from_settings_button.draw(screen)
        back_to_main_button.draw(screen)

    elif game_state == "GAMEPLAY":
        all_sprites.draw(screen)
        draw_text(screen, f"Score: {score}", 24, SCREEN_WIDTH / 2, 10)
        draw_lives(screen, SCREEN_WIDTH - 100, 15, player.lives, player_mini_img)

    elif game_state == "GAME_OVER":
        draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        draw_text(screen, f"Final Score: {score}", 32, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50)
        play_again_button.draw(screen)
        quit_game_over_button.draw(screen)

    elif game_state == "PAUSE_MENU":
        # Optionally dim the background for pause
        dim_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surface.fill((0,0,0, 150)) # Semi-transparent black
        screen.blit(dim_surface, (0,0))

        draw_text(screen, "Paused", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4)
        resume_button.draw(screen)
        exit_pause_button.draw(screen)


    pygame.display.flip()

pygame.quit()
sys.exit()