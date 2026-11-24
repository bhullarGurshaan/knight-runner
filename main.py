'''Group members: Aiden, Gurshaan
Description: A simple runner game made using the pygame module. The game is
similar in concept to the Google offline dinosaur game, with custom made
graphics and an attack feature, offering a high risk high reward playstyle.'''

# imports
import pygame as pg
from numpy import array
from os import path
from math import ceil
from random import randint, choice
from threading import Thread

# checks if the font or mixer is disabled in the laptop or whatever system is running the program
if not pg.font:
    print("Warning, fonts disabled")
if not pg.mixer:
    print("Warning, sound disabled")

# Save the data directory to a variable to easily obtain file paths
main_dir = path.split(path.abspath(__file__))[0]
data_dir = path.join(main_dir, "data")

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 450
FPS = 60

# RGB values for sky colours
DAY_SKY = array((135, 206, 235))
NIGHT_SKY = array((25, 25, 112))
sky_colour = DAY_SKY

class Ground:
    '''Handles all functionality relating to the ground, in order to keep the 
    main function more organized'''

    def __init__(self):
        global GROUND_TOP # Used to position several other game objects

        self.image = load_image(path.join(data_dir, "ground.png"), 0.3)
        self.surface = self.image.copy()
        
        rect = self.image.get_rect()
        rect.bottom = WINDOW_HEIGHT # Places ground at the bottom of the screen
        self.tile_width = rect.width
        GROUND_TOP = rect.top

        num_tiles = ceil(WINDOW_WIDTH / self.tile_width) + 1
        self.tiles = [rect for i in range(num_tiles)]
        self.offset = 0

    def update(self):
        '''Updates the ground offset, used to scroll the ground to the left'''

        self.offset -= 5
        # Resets offset once first ground tile is offscreen
        if abs(self.offset) >= self.tile_width: self.offset = 0

    def draw(self, screen):
        '''Description: Draws all of the ground tiles to the screen
        Arguments: the screen'''

        for i in range(len(self.tiles)):
            self.tiles[i].x = self.tile_width * i + self.offset
            screen.blit(self.surface, self.tiles[i])

    def change_colour(self, daytime):
        '''Changes the colour of the ground, darkening it when the game's time
        changes to night
        Arguments: the time of day'''

        ground_array = array(pg.surfarray.array3d(self.image))

        orig_ground = ground_array if daytime else ground_array / 2
        dest_ground = ground_array / 2 if daytime else ground_array

        for i in range(1, 101):
            diff = (dest_ground - orig_ground) * i / 100
            pg.surfarray.blit_array(self.surface, orig_ground + diff)
            pg.time.wait(1000 // FPS)

class Cloud(pg.sprite.Sprite):
    '''A class inheriting from pygame's Sprite class. When used in conjunction 
    with the Group class from pygame's sprite module, this class makes it easy 
    to handle several clouds at the same time'''

    def __init__(self):
        super().__init__()

        # Required attributes for pygame's sprite class
        self.image = load_image(path.join(data_dir, "cloud.png"), \
                                randint(5, 8) / 10)
        self.rect = self.image.get_rect()

        self.image.set_alpha(200) # Makes cloud slightly transparent

        # Position the cloud, generating a random y-coordinate between the
        # ground and the screen
        self.rect.left = WINDOW_WIDTH
        self.rect.centery = randint(100, GROUND_TOP - 200)

    def update(self):
        self.rect.x -= 1
        if self.rect.right < 0:
            self.kill()

class Player(pg.sprite.Sprite):
    '''A player class inheriting from pygame's Sprite class. Handles 
    functionality relating to the player'''

    def __init__(self):
        global player_midleft # Used to position attack relative to player

        super().__init__()

        # Load all of the player's animation frames
        image_dir = path.join(data_dir, "Player")
        self.walk_frames = [load_image(path.join(image_dir, f"walk{i}.png"), 0.7) \
                            for i in range(1, 5)]
        self.jump_frame = load_image(path.join(image_dir, "jump.png"), 0.7)
        self.fall_frame = load_image(path.join(image_dir, "fall.png"), 0.7)

        self.walk_index = 0
        self.gravity = 0
        self.jump_sound = load_sound(path.join(data_dir, "jump_sound.mp3"), 0.2)

        # Required attributes for pygame's Sprite class
        self.image = self.walk_frames[self.walk_index]
        self.rect = self.image.get_rect(midbottom=(80, GROUND_TOP))

        player_midleft = self.rect.midleft

    def jump(self):
        '''Changes the player's gravity attribute to initiate a jump, and plays
        a sound effect'''

        if self.rect.bottom == GROUND_TOP: # If the player is on the ground
            self.gravity = -20
            self.jump_sound.play()

    def apply_gravity(self):
        '''Changes the player's position according to the gravity, and updates
        the gravity to simulate acceleration due to gravity'''

        self.rect.y += self.gravity
        self.gravity += 1
        if self.rect.bottom > GROUND_TOP: self.rect.bottom = GROUND_TOP

    def animate(self):
        '''Scrolls through the player's animation frames. Also handles changing
        to jump/fall animation frames depending on the player's position and 
        gravity'''

        if self.rect.bottom < GROUND_TOP: # If player is off the ground
            # Check the vertical direction the player is travelling in, and set
            # the sprite image accordingly
            if self.gravity <= 0: self.image = self.jump_frame
            else: self.image = self.fall_frame
        else:
            # Cycle through the player's walking animation frames
            self.walk_index += 0.15
            if int(self.walk_index) >= len(self.walk_frames): self.walk_index = 0
            self.image = self.walk_frames[int(self.walk_index)]

    def update(self):
        '''Required function for pygame's Sprite class. Updates any player 
        attributes that need to be updated on each frame'''

        # Needs to be updated on each frame to position the attack
        global player_midleft
        player_midleft = self.rect.midleft

        self.apply_gravity()
        self.animate()

class Attack(pg.sprite.Sprite):
    '''An attack class that plays the attack animation once before deleting
    itself. In the main program, collisions will be checked between this sprite
    and the enemies in order for the player to attack them.'''

    def __init__(self, frames):
        super().__init__()

        self.frames = frames
        self.index = 0

        # Required attributes for pygame's Sprite class
        self.image = self.frames[self.index]
        self.rect = self.image.get_rect(midleft=player_midleft)

        load_sound(path.join(data_dir, "sword_sound.mp3"), 0.2).play()

    def animate(self):
        # index to scroll through the different frames in the attack images
        self.index += 0.5
        
        # if the index is bigger than amount of frames it kills that instance of
        # the attack class
        if int(self.index) >= len(self.frames):
            self.kill()
            return
        self.image = self.frames[int(self.index)]

    def update(self):
        self.animate()
        self.rect.midleft = player_midleft

class Enemy(pg.sprite.Sprite):
    '''An Enemy sprite class that loads all the 2 different enemies and makes
    them function'''

    def __init__(self, type):
        super().__init__()
        image_dir = path.join(data_dir, "Bird")
        image_dir1 = path.join(data_dir, "Slime")

        # Load all the animation frames, depending on the enemy type
        if type == 'bird':
            fly1 = load_image(path.join(image_dir, "bird1.png"), 0.7)
            fly2 = load_image(path.join(image_dir, "bird2.png"), 0.7)
            fly3 = load_image(path.join(image_dir, "bird3.png"), 0.7)
            fly4 = load_image(path.join(image_dir, "bird4.png"), 0.7)
            fly5 = load_image(path.join(image_dir, "bird5.png"), 0.7)
            fly6 = load_image(path.join(image_dir, "bird6.png"), 0.7)
            self.frames = [fly1,fly2,fly3,fly4,fly5,fly6]
            y_pos = 170
        
        else:
            slime1 = load_image(path.join(image_dir1, "slime1.png"), 0.7)
            slime2 = load_image(path.join(image_dir1, "slime2.png"), 0.7)
            slime3 = load_image(path.join(image_dir1, "slime3.png"), 0.7)
            slime4 = load_image(path.join(image_dir1, "slime4.png"), 0.7)
            self.frames = [slime1, slime2, slime3, slime4]
            y_pos = GROUND_TOP

        # to check if the enemy has been hit or not 
        self.living = True

        self.index = 0
        self.image = self.frames[self.index]

        # setting the rectangle as random point between 900 and 1100 so it spawns randomly
        self.rect = self.image.get_rect(midbottom = (randint(900,1100), y_pos))

    def animation(self):
        '''scrolls through the enemy's animation frames to create an animation'''

        self.index += 0.15

        if self.index >= len(self.frames):
            self.index = 0
        self.image = self.frames[int(self.index)]
    
    def update(self):
        global hit_score

        # if the function is not hit then it updates the instance and moves it to the left
        if self.living:
            self.animation()
            self.rect.x -= 6
            self.destroy()

            # Check collisions with the player's attack and checks if the attack
            # animation index is below two, which makes attack timing more strict
            if pg.sprite.spritecollide(self, attack_group, False) and \
                attack_group.sprite.index <= 2: 
                self.living = False
                hit_score += 50
        
        # if the living state of the enemy is false, it moves the image to the right
        # and calls the destroy method to kill that sprite once it is offscreen
        else:
            self.rect.x += 10
            self.destroy()
    
    def destroy(self):
        '''Checks if the enemy is offscreen, either by walking into the left
        end, or being hit to the right end by the player, then deletes the enemy
        instance'''

        if self.rect.right <= 0 or (self.rect.x >= WINDOW_WIDTH and not self.living): 
            self.kill()    

class Spikes(pg.sprite.Sprite):
    '''A separate Sprite class for spikes so that the player is not able to
    attack the spikes like they're able to attack enemies'''

    def __init__(self):
        super().__init__()
        
        self.image = load_image(path.join(data_dir, "spikes.png"))
        y_pos = GROUND_TOP

        self.rect = self.image.get_rect(midbottom = (randint(1000,1200), y_pos))
        
    def update(self):
        self.rect.x -= 5
        self.destroy()
    
    def destroy(self):
        if self.rect.x <= -100:
            self.kill()

def load_image(file_path, scale=1):
    '''Description: Creates a pygame surface using pygame.image.load() with 
    error checking, image conversion, and a scale factor.
    Arguments: image path, scale factor (float)
    Returns: a pygame Surface object, a pygame Rect object'''

    try: image = pg.image.load(file_path)
    except: 
        print(f"Error, could not locate file: {path.basename(file_path)}")

        # Closes the program
        pg.quit()
        raise SystemExit

    # Convert the image to a format that is easier for pygame to work with
    image = image.convert_alpha()

    size = (image.get_width() * scale, image.get_height() * scale)
    image = pg.transform.scale(image, size)

    return image

def load_sound(file_path, volume=1):
    '''Description: Creates a pygame Sound object with error checking for
    missing files, and a volume setting
    Arguments: sound path, volume (float between 0 and 1)
    Returns: A pygame Sound object'''

    # Creates a dummy class that can take the place of a Sound object if there
    # are missing files, without causing an error.
    class DummySound:
        def play(self, *args, **kwargs):
            pass

    if not pg.mixer or not pg.mixer.get_init():
        return DummySound()
    
    try: sound = pg.mixer.Sound(file_path)
    except:
        print(f"Warning, could not locate file: {path.basename(file_path)}")
        return DummySound()
    
    sound.set_volume(volume)
    
    return sound

def load_font(file_path, font_size=12):
    '''Description: Creates a pygame Font object, with error checking for 
    missing files
    Arguments: font path, font_size (integer, default value 12)
    Returns: A pygame font object'''

    # Creates a dummy class that can take the place of a Font object if the
    # pygame font module is missing, without causing an error
    class DummyFont:
        def render(self, *args, **kwargs):
            return pg.surface.Surface((0, 0))
        
    if not pg.font or not pg.font.get_init():
        return DummyFont()

    try: font = pg.font.Font(file_path, font_size)
    except:
        print(f"Warning, could not locate file: {path.basename(file_path)}")
        
        # Returns a font with pygame's default font "freesansbold"
        return pg.font.Font(None, font_size)
    
    return font

def merge_sky_colours(old_sky, new_sky):
    '''Briefly merges the two sky colours together, to create a fading
    effect that darkens or brightens the sky. Used when changing time of day'''

    global sky_colour

    for i in range(1, 101):
        diff = (new_sky - old_sky) * i / 100
        sky_colour = old_sky + diff
        pg.time.wait(1000 // FPS)

def change_scene(daytime, ground):
    '''Changes the time of day by changing the colours of certain parts of the 
    screen, notably the ground and sky.
    Arguments: time of day, ground object (used to effect ground colours)'''

    old_sky = DAY_SKY if daytime else NIGHT_SKY
    new_sky = NIGHT_SKY if daytime else DAY_SKY

    # Python's threading module is used to create new threads, allowing the sky
    # and ground colours to be changed without pausing the main program
    Thread(target=merge_sky_colours, args=(old_sky, new_sky)).start()
    Thread(target=ground.change_colour, args=(daytime,)).start()

def display_score(screen, start_time):
    '''Calculates and displays the score, which is based off of the time the
    player has survived, and how many enemies they've hit'''

    game_font = load_font(path.join(data_dir,"Pixeltype.ttf"), 50)

    current_time = int(pg.time.get_ticks() / 300) - start_time
    total_score = current_time + hit_score
    score_surf = game_font.render(f'Score: {total_score}', False, (0,0,0))
    score_rect = score_surf.get_rect(center=(400,20))
    screen.blit(score_surf, score_rect)

    return total_score
    
def main():
    global sky_colour, attack_group, hit_score

    # Initialize pygame and assets needed like score, window title, clock for the FPS
    pg.init()
    screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pg.display.set_caption("Knight Runner")
    clock = pg.time.Clock()
    start_time = 0
    score = 0
    hit_score = 0
    game_active = False

    # Load all the assets and create class instances needed before game begins
    bg_music = load_sound(path.join(data_dir, "background_music.mp3"), 0.1)
    bg_music.play(-1)

    ground = Ground()

    player = Player()
    player_group = pg.sprite.GroupSingle(player)

    # Attack images are loaded outside of the class to avoid repeated loading
    attack_group = pg.sprite.GroupSingle()
    attack_frames = [load_image(path.join(data_dir, "Attack", f"attack{i}.png"), 0.7) \
                     for i in range(1, 10)]
    attack_cooldown = 0

    # .set_alpha(200) makes the sun and moon images slightly transparent
    sun = load_image(path.join(data_dir, "sun.png"), 0.4)
    sun.set_alpha(200)
    sun_rect = sun.get_rect(topleft=(WINDOW_WIDTH, 50))

    moon = load_image(path.join(data_dir, "moon.png"), 0.4)
    moon.set_alpha(200)
    moon_rect = moon.get_rect(topleft=(WINDOW_WIDTH, 50))

    # Set a timer to move the sun or moon, as moving them every frame is
    # slightly too fast
    move_sun_or_moon = pg.USEREVENT + 1
    pg.time.set_timer(move_sun_or_moon, 30)
    daytime = True

    # Create remaining sprite groups for enemies and spikes
    obstacle_group = pg.sprite.Group()

    # Creates a pygame event that triggers every 5 seconds, which spawns a cloud
    spawn_cloud = pg.USEREVENT + 2
    pg.time.set_timer(spawn_cloud, 5000)
    cloud_group = pg.sprite.Group()

    # A timer that triggers every 1.5 seconds, spawning an enemy or obstacle
    spawn_obstacle = pg.USEREVENT + 3
    pg.time.set_timer(spawn_obstacle, 1500)

    # Loading all the images and rendering all the fonts for the title screen
    stand_dir = path.join(data_dir, "Player")
    player_stand = load_image(path.join(stand_dir, "jump.png"), 1.2)
    player_stand_rect = player_stand.get_rect(midbottom=((WINDOW_WIDTH / 2) - 10 ,270))

    font = load_font(path.join(data_dir,"Pixeltype.ttf"), 100)
    font1 = load_font(path.join(data_dir,"Pixeltype.ttf"), 50)
    font2 = load_font(path.join(data_dir,"Pixeltype.ttf"), 30)

    game_name = font.render('Knight Runner', False, (0,0,0))
    game_name_rect = game_name.get_rect(midbottom = (WINDOW_WIDTH / 2, 100))

    controls1 = font1.render('Space Bar: Player Jump', False, (0,0,0))
    controls1_rect = controls1.get_rect(midbottom = (WINDOW_WIDTH / 2, 340))

    controls2 = font1.render('F: Player Attack', False, (0,0,0))
    controls2_rect = controls2.get_rect(midbottom = (WINDOW_WIDTH / 2, 380))

    g_continue = font2.render('Press Space to Continue', False, (0,0,0))
    g_continue_rect = g_continue.get_rect(midbottom = (WINDOW_WIDTH / 2, 430))

    # Begin the game loop
    while True:
        # Pygame's event loop, handles quitting the game and player input
        for event in pg.event.get():
            if event.type == pg.QUIT:
                # Closes the program
                pg.quit()
                raise SystemExit

            # if game_active is true meaning if the game is running:
            if game_active:
                
                # anytime a key is pressed down
                if event.type == pg.KEYDOWN:
                    # if space key is pressed ti calls the jump event from the Player Class
                    if event.key == pg.K_SPACE:
                        player.jump()
                    # if the F key is pressed and the attack cooldown is less than zero
                    # it lets the player attack again and sets the cooldown higher
                    # so that the player cannot spam F and attack
                    if event.key == pg.K_f and attack_cooldown <= 0:
                        attack_group.add(Attack(attack_frames))
                        attack_cooldown = 30

                # if the event type is spawn obstacles it spawns the different enemies
                if event.type == spawn_obstacle:
                    if randint(0, 3): obstacle_group.add(Enemy(choice(['bird','slime','slime'])))
                    else: obstacle_group.add(Spikes())

                if event.type == spawn_cloud:
                    # Only place a cloud 3/4 of the time
                    if randint(0, 3): cloud_group.add(Cloud())

                if event.type == move_sun_or_moon:
                    if daytime:
                        sun_rect.x -= 1
                        if sun_rect.right < 0: # When sun is offscreen
                            # Changes time to night
                            change_scene(daytime, ground)
                            daytime = False
                            sun_rect.left = WINDOW_WIDTH
                    else:
                        moon_rect.x -= 1
                        if moon_rect.right < 0: # When moon is offscreen
                            # Changes time to day
                            change_scene(daytime, ground)
                            daytime = True
                            moon_rect.left = WINDOW_WIDTH

            else: # If game is not active 

                # if the event is a button pressed down and if that button is the space bar
                # then game_active is back to true and it runs the program again 
                # and displays the score as the previous score achieved while playing
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    game_active = True
                    start_time = int(pg.time.get_ticks() / 300)

        # if game_active is true or if the game is running:
        if game_active:

            # fills the screen with sky blue
            screen.fill(sky_colour)

            # calls the display score funtion to display the score
            score = display_score(screen, start_time)

            # blits the sun and moon the the screen
            screen.blit(sun, sun_rect)
            screen.blit(moon, moon_rect)

            # updates and draws the different classes to the screen
            cloud_group.update()
            cloud_group.draw(screen)

            ground.update()
            ground.draw(screen)

            obstacle_group.update()
            obstacle_group.draw(screen)

            player_group.update()
            player_group.draw(screen)

            attack_cooldown -= 1
            attack_group.update()
            attack_group.draw(screen)

            # if the player and obstacles collide then game_active becomes false
            game_active = not pg.sprite.groupcollide(player_group, \
                                                      obstacle_group, False, False)

        # If the game is not active
        else: 

            # changes the screen colour to a blue colour and adds an image of the player
            screen.fill((134, 176, 194))
            screen.blit(player_stand, player_stand_rect)
            
            # renders the score message 
            score_message = font.render(f'Your Score: {score}', False, (0,0,0))
            score_message_rect = score_message.get_rect(midbottom = (400,100))
            
            # if the score is 0 then it displays the game name
            if score == 0:
                screen.blit(game_name, game_name_rect)

            # if the score is greater than 0 then it displays the score of the previous attempt
            else:
                screen.blit(score_message,score_message_rect)

            # adds the controls and the continue text to the screen
            screen.blit(controls1, controls1_rect)
            screen.blit(controls2, controls2_rect)
            screen.blit(g_continue,g_continue_rect)

            # Removes all of the obstacles from the game so they don't appear
            # when the game starts again
            obstacle_group.empty()

            hit_score = 0

            # Resets sun and moon positions, and makes the game daytime
            sun_rect.left = WINDOW_WIDTH
            moon_rect.left = WINDOW_WIDTH
            daytime = True
            sky_colour = DAY_SKY
            pg.surfarray.blit_array(ground.surface, pg.surfarray.array3d(ground.image))

        # The screen must be updated for all of the changes to be seen
        pg.display.update()
        
        # Makes the game run at a set frames per second
        clock.tick(FPS)

if __name__ == "__main__":
    main()