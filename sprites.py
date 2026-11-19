import pygame as pg
from pygame.sprite import Sprite
from settings import *
from utils import *
from os import path
from random import randint, choice
from time import sleep

vec = pg.math.Vector2

def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)

def collide_with_walls(sprite, group, dir):
    # check for x collision
    if dir == 'x':
        # check collisions
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            # this line checks to see if we're to the left of the wall
            if sprite.vel.x > 0:
                # reposition the player (sprite) to the left side of the wall
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width / 2
            if sprite.vel.x < 0:
                sprite.pos.x = hits[0].rect.right + sprite.hit_rect.width / 2 
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x

    if dir == 'y':
        # check collisions with hitrects
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            # checks if we're above the wall
            if sprite.vel.y > 0:
                # reposition the player (sprite) to the top of the wall
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
            if sprite.vel.y < 0:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2 
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y

class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        #provides us with raster images for use in animations etc
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "sprite_sheet.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(0,0,TILESIZE, TILESIZE)
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        # player acceleration (for friction/ice/etc)
        self.acc = vec(0,0)
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.cofric = PLAYER_FRIC
        self.hit_rect = PLAYER_HIT_RECT.copy()
        self.hit_rect.center = self.pos
        # start with current frames and last update at zero so we can cycle through animations
        self.current_frame = 0
        self.last_update = 0

        #accounts for player state (state machine)
        self.jumping = False
        self.moving = False
        self.on_ice = False

        # coins and debug prints
        self.coins = 0 
        print("player instance created")
        self.load_images()

    # gets player input
    def get_keys(self):
        #we don't need diagonal normalization anymore
        if self.vel.length() > 0:
            return
        keys = pg.key.get_pressed()

        #vectors make player continuosly move, until hitting a wall
        if keys[pg.K_a]:
            self.vel = vec(-PLAYER_SPEED, 0)

        elif keys[pg.K_d]:
            self.vel = vec(PLAYER_SPEED, 0)

        elif keys[pg.K_w]:
            self.vel = vec(0, -PLAYER_SPEED)

        elif keys[pg.K_s]:
            self.vel = vec(0, PLAYER_SPEED)

    def jump(self):
        pass

    #loading a spritesheet instead of individual images 
    def load_images(self):
        self.idle_frames = [self.spritesheet.get_image(0,0, TILESIZE,TILESIZE), self.spritesheet.get_image(32,0, TILESIZE,TILESIZE)]
    #method swaps between frames in sprietsheet to animate
    def animate(self):
        now = pg.time.get_ticks()
        if not self.jumping and not self.moving:
            if now - self.last_update > 350:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
                bottom = self.rect.bottom
                self.image = self.idle_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

        elif self.moving:
            if now - self.last_update > 350:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.moving_frames)
                bottom = self.rect.bottom
                self.image = self.moving_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom
            
    def update(self):
        self.animate()

        #physics/acceleration math done here before updates (most tweaked/updated code section)
        self.get_keys()

        #x collisions
        self.pos.x += self.vel.x
        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.all_walls, 'x')

        #y collisions
        self.pos.y += self.vel.y
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.all_walls, 'y')

        #stops player when it hits a wall
        if self.vel.x == 0 and self.vel.y == 0:
            pass

        #actually setting the player's coords to based on collisions
        self.rect.center = self.hit_rect.center
        #collisions = hits, algortihm to check if colliding
        hits = pg.sprite.spritecollide(self, self.game.all_coins, True)
        if hits:
            self.coins +=1
            self.game.score+=1
            self.game.pickup_snd.play()
            for i in range(20):
                Particle(self.game, hits[0].rect.x, hits[0].rect.y)
                hits[0].kill()

        spike_hits = pg.sprite.spritecollide(self, self.game.all_spikes, False)

        #copied coin collision logic, made it result in game stop
        if spike_hits:
            self.game.player_died()

#walls make up the maze
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(MAGENTA)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) *TILESIZE
        self.rect.center = self.pos
        print("wall instance created")

#spike class coppied from wall class and code helped from cs50ai
class Spike(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_spikes
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(CYAN)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) *TILESIZE
        self.rect.center = self.pos
        print("spike instance created")

class Particle(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_particles
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE/4, TILESIZE/4))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.vel = vec(randint(-180,180),randint(-180,180)) 
        # self.vel = vec(0,0)
        self.pos = vec(x,y)
        self.speed = 2
        self.rect.center = self.pos
        
        self.countdown = Cooldown()
        self.countdown.event_time = floor(pg.time.get_ticks()/1000)
        print("particle created")

    def update(self):
        self.countdown.ticking()
        # i tried to set the random speed multipliers before the particle was made, it didnt work
        # self.randx = 
        # self.randy = randint(-3,3)
        self.pos += self.vel * self.speed * self.game.dt
        # self.rect.x += self.speed* randint(-3,3)
        # self.rect.y += self.speed* randint(-3,3)
        if self.countdown.delta > 1:
            self.kill()
            print(str(len(self.game.all_particles)))
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y

#make a mob class similar to the player but without key commands
class Mob(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_mobs
        Sprite.__init__(self, self.groups)
        self.game = game

        #provides us with raster images for use in animations etc
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "sprite_sheet.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(64,0,TILESIZE, TILESIZE)
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        #set mob position
        self.rect.x = x
        self.rect.y = y
        self.speed = 100
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.hit_rect = MOB_HIT_RECT

        # start with current frames and last update at zero so we can cycle through animations
        self.current_frame = 0
        self.last_update = 0

        #accounts for player state (state machine)
        self.jumping = False
        self.moving = False
        print("mob instance created")
        self.load_images()

    def load_images(self):
        self.idle_frames = [self.spritesheet.get_image(64,0, TILESIZE,TILESIZE), self.spritesheet.get_image(96,0, TILESIZE,TILESIZE)]

    def animate(self):
        now = pg.time.get_ticks()
        if not self.jumping and not self.moving:
            if now - self.last_update > 350:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.idle_frames)
                bottom = self.rect.bottom
                self.image = self.idle_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

        elif self.moving:
            if now - self.last_update > 350:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.moving_frames)
                bottom = self.rect.bottom
                self.image = self.moving_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

    #look towards the player and normalize() or close the distance down
    def follow(self,obj):
        direction = vec(obj.rect.centerx - self.rect.centerx, obj.rect.centery - self.rect.centery)
        if direction.length() > 0:
            direction = direction.normalize()
        self.vel = direction
    
    def update(self):
        self.animate()
        self.follow(self.game.player)

        self.pos += self.vel * self.speed
        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.all_walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.all_walls, 'y')
        self.rect.center = self.hit_rect.center

#copy wall class to make a coin class
class Bomb(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_coins
        Sprite.__init__(self, self.groups)
        self.game = game

        #code prompted to chatgpt with assistance from cs50.ai
        # self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = pg.Surface((TILESIZE, TILESIZE)) 
        # pg.SCRALPHA is a pygame method to make an object's parts transparent
        pg.draw.circle(self.image, GOLD, (TILESIZE//2, TILESIZE//2), TILESIZE//2)  
        
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y) *TILESIZE
        self.rect.center = self.pos
        print("bomb instance created")
