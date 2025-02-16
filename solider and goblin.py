import os
import pygame as pg

SIZE = WIDTH, HEIGHT = 852, 568
FPS = 60
# Font size
SMALL_FONT_SIZE = 20
FONT_SIZE = 40
BIG_FONT_SIZE = 60
# Scale by SCALE_FACTOR
SCALE_FACTOR = 4

# Get dictionary path
main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, 'data of soldier & goblin')

# Initialize pygame modules
pg.init()
# Set screen
screen = pg.display.set_mode(SIZE)
pg.display.set_caption('Soldier Animation')
image_stand = pg.image.load(os.path.join(data_dir, 'standing.png'))
pg.display.set_icon(image_stand)
# Set font
small_font = pg.font.Font(None, SMALL_FONT_SIZE)
font = pg.font.Font(None, FONT_SIZE)
big_font = pg.font.Font(None, BIG_FONT_SIZE)
# Set clock
clock = pg.time.Clock()

# Load music and set volume
pg.mixer.music.load(os.path.join(data_dir, 'music.mp3'))
pg.mixer.music.set_volume(0.15)

# Load fist sound and set volume
shake_fist = pg.mixer.Sound(os.path.join(data_dir, 'shake-fist.mp3'))
shake_fist.set_volume(0.5)
punch_sound = pg.mixer.Sound(os.path.join(data_dir, 'punch.mp3'))
punch_sound.set_volume(45)

# load bullet sound and set volume
bullet_sound = pg.mixer.Sound(os.path.join(data_dir, 'bullet.mp3'))
bullet_sound.set_volume(1)
bullet_hit_sound = pg.mixer.Sound(os.path.join(data_dir, 'bullet-hit.mp3'))
bullet_hit_sound.set_volume(5)

# Load background
background = pg.image.load(os.path.join(data_dir, 'background.jpg')).convert()

scale_by = pg.transform.scale_by
# Load enemy image to walk left and right and scale them by 3
enemy_image_left = []
enemy_image_right = []
for i in range(7):
    enemy_image_left.append(scale_by(pg.image.load(os.path.join(data_dir, f'L{i + 1}E.png')).convert_alpha(), SCALE_FACTOR))
    enemy_image_right.append(scale_by(pg.image.load(os.path.join(data_dir, f'R{i + 1}E.png')).convert_alpha(), SCALE_FACTOR))
# Load enemy image to hit left and right and scale them by 3
hit_left = []
hit_right = []
for i in range(8, 12):
    hit_left.append(scale_by(pg.image.load(os.path.join(data_dir, f'L{i}E.png')).convert_alpha(), SCALE_FACTOR))
    hit_right.append(scale_by(pg.image.load(os.path.join(data_dir, f'R{i}E.png')).convert_alpha(), SCALE_FACTOR))
# Load image to walk left and right and scale them by 3
image_left = []
image_right = []
for i in range(9):
    image_left.append(scale_by(pg.image.load(os.path.join(data_dir, f'L{i + 1}.png')).convert_alpha(), SCALE_FACTOR))
    image_right.append(scale_by(pg.image.load(os.path.join(data_dir, f'R{i + 1}.png')).convert_alpha(), SCALE_FACTOR))
# Scale stand image by 3
image_stand = pg.transform.scale_by(image_stand, SCALE_FACTOR)


# Base class which control move and jump
class Player:
    def __init__(self, P_id, name, x, y, horizon_move, jump_limit):
        self.health_point = 100
        self.name = name
        self.id = P_id
        self.x = x
        self.y = y
        if P_id == 1:
            self.left = False
            self.right = True
        else:
            self.right = False
            self.left = True
        self.standing = True
        self.walking = False
        self.jump = False
        self.horizon_move = horizon_move  # Move horizon_move pixels in a frame
        self.jump_limit = jump_limit  # Move jump_limit most pixels in a frame
        self.jump_move = jump_limit  # Jump jump_move pixels in a frame

    @property
    def jump(self):
        return self._jump

    @jump.setter
    def jump(self, b):
        if not isinstance(b, bool):
            raise ValueError("Jump value type must be bool")
        self._jump = b

    def move(self, left_m=False, right_m=False):
        if left_m:
            self.walking = True
            self.left = True
            self.right = False
            self.standing = False
            self.x -= self.horizon_move
        elif right_m:
            self.walking = True
            self.left = False
            self.right = True
            self.standing = False
            self.x += self.horizon_move
        else:
            self.walking = False
            self.standing = True

    def update(self):
        # Update jump position
        if self.jump:
            if self.jump_move >= -self.jump_limit:
                self.y -= self.jump_move
                self.jump_move -= 2
            else:
                self.jump = False
                self.jump_move = self.jump_limit


class Goblin(Player):
    walk_left = [image for image in enemy_image_left]
    walk_right = [image for image in enemy_image_right]
    hit_left = [image for image in hit_left]
    hit_right = [image for image in hit_right]
    width = 256  # Goblin width
    height = 256  # Goblin height
    walk_left_most = -60
    walk_right_most = 650
    walk_limit = 21  # Walk 21 times in a direction
    hit_limit = 12  # Hit 12 times in a hit
    hit_time = 200  # Spend to hit
    hit_harm = 7  # Hit health_point once
    cooldown_time = 600  # Wait to hit again(millisecond)

    def __init__(self, P_id, name=f'goblin', x=None, y=HEIGHT - height, horizon_move=10, jump_limit=30, extra_harm=0):
        x = Goblin.walk_left_most if P_id == 1 else Goblin.walk_right_most
        super().__init__(P_id, name + str(P_id), x, y, horizon_move, jump_limit)
        self.walk_count = 0  # Record walk count to determine which walk image
        self.hitting = False
        self.hit_count = 0  # Record hit count to determine which hit image
        self.hit_start = 0  # Record hit start
        self.hit_end = 0   # Record hit end
        self.extra_harm = extra_harm  # Total harm = Goblin.hit_harm + self.extra_harm
        self.target = None  # Hit target
        self.punch_over = True  # Punch once
        self.cooldown = False
        self.cooldown_start = 0  # Record cooldown start
        self.cooldown_end = 0  # Record cooldown end
        self.hitbox = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)
        self.hitbox_leftfist = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)
        self.hitbox_rightfist = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)

    def recover(self):
        self.health_point = 100
        self.x = Goblin.walk_left_most if self.id == 1 else Goblin.walk_right_most
        self.y = HEIGHT - Goblin.height
        self.standing = True
        self.walking = False
        self.jump = False
        self.left = True
        self.right = False
        self.jump_move = self.jump_limit
        self.walk_count = 0  # Record walk count to determine which walk image
        self.hitting = False
        self.hit_count = 0  # Record hit count to determine which hit image
        self.hit_start = 0  # Record hit start
        self.hit_end = 0  # Record hit end
        self.target = None  # Hit target
        self.punch_over = True  # Punch once
        self.cooldown = False
        self.cooldown_start = 0  # Record cooldown start
        self.cooldown_end = 0  # Record cooldown end
        self.hitbox = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)
        self.hitbox_leftfist = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)
        self.hitbox_rightfist = pg.rect.Rect(self.x, self.y, Goblin.width, Goblin.height)

    def move(self, left_m=False, right_m=False):
        super().move(left_m, right_m)
        # Move left most
        if self.x < Goblin.walk_left_most:
            self.x = Goblin.walk_left_most
        # Move left most
        if self.x > Goblin.walk_right_most:
            self.x = Goblin.walk_right_most

    def hit(self, target):
        if not self.cooldown:
            shake_fist.play()
            self.cooldown = True
            self.hitting = True
            self.target = target
            self.punch_over = False
            self.cooldown_start = self.cooldown_end = pg.time.get_ticks()
            self.hit_start = pg.time.get_ticks()

    def punch(self):
        if not self.punch_over:
            if self.left:
                if self.hitbox_leftfist.colliderect(self.target.hitbox):
                    # print('punch')
                    punch_sound.play()
                    self.target.health_point -= Goblin.hit_harm + self.extra_harm
            if self.right:
                if self.hitbox_rightfist.colliderect(self.target.hitbox):
                    # print('punch')
                    punch_sound.play()
                    self.target.health_point -= Goblin.hit_harm + self.extra_harm
        self.punch_over = True

    def update(self):
        # Update jump
        super().update()
        # Update hit
        if self.hitting:
            self.punch()
            self.hit_end = pg.time.get_ticks()
            hit_time = self.hit_end - self.hit_start
            if hit_time > Goblin.hit_time:
                self.hitting = False
        # Update cooldown
        if self.cooldown:
            self.cooldown_end = pg.time.get_ticks()
            cooldown_time = self.cooldown_end - self.cooldown_start
            if cooldown_time > Goblin.cooldown_time:
                self.cooldown_start = self.cooldown_end = 0
                self.cooldown = False
        # Update hitbox
        if self.left:
            self.hitbox = pg.rect.Rect(self.x + 100, self.y + 30, Goblin.width - 160, Goblin.height - 40)
            self.hitbox_leftfist = pg.rect.Rect(self.x + 65, self.y + 105, 35, 30)
        elif self.right:
            self.hitbox = pg.rect.Rect(self.x + 50, self.y + 30, Goblin.width - 160, Goblin.height - 40)
            self.hitbox_rightfist = pg.rect.Rect(self.x + 200, self.y + 100, 35, 30)

    def draw_info(self, window):
        # Draw title
        title = font.render(self.name, True, (247, 79, 7))
        if self.left:
            window.blit(title, title.get_rect(left=self.x + 100, top=self.y - 10))
        else:
            window.blit(title, title.get_rect(left=self.x + 50, top=self.y - 10))
        if self.id == 1:
            # Draw name
            name = font.render(f'P{self.id}: {self.name}', True, (143, 7, 240))
            window.blit(name, name.get_rect(left=10, top=10))
            # Draw health point
            hp = font.render('HP: ', True, (143, 7, 240))
            window.blit(hp, name.get_rect(left=10, top=40))
            pg.draw.line(window, (235, 7, 26), (60, 53), (60 + self.health_point * 1.4, 53), 10)
            # Draw cooldown
            CD = font.render('CD: ', True, (143, 7, 240))
            window.blit(CD, name.get_rect(left=10, top=70))
            pg.draw.line(window, (5, 96, 252), (60, 83),
                         (200 - (self.cooldown_end - self.cooldown_start) / 6 * 1.4, 83), 10)
        else:
            # Draw name
            name = font.render(f'P{self.id}: {self.name}', True, (143, 7, 240))
            window.blit(name, name.get_rect(left=WIDTH - 200, top=10))
            # Draw health point
            hp = font.render('HP: ', True, (143, 7, 240))
            window.blit(hp, name.get_rect(left=WIDTH - 200, top=40))
            pg.draw.line(window, (235, 7, 26), (WIDTH - 150, 53), (WIDTH - 150 + self.health_point * 1.4, 53), 10)
            # Draw cooldown
            CD = font.render('CD: ', True, (143, 7, 240))
            window.blit(CD, name.get_rect(left=WIDTH - 200, top=70))
            pg.draw.line(window, (5, 96, 252), (WIDTH - 150, 83),
                         (WIDTH - 10 - (self.cooldown_end - self.cooldown_start) / 6 * 1.4, 83), 10)

    def draw(self, window):
        self.update()

        # Repeat walk image
        if self.walk_count >= Goblin.walk_limit:
            self.walk_count = 0
        # Repeat hit image
        if self.hit_count >= Goblin.hit_limit:
            self.hit_count = 0

        # Hit
        if self.hitting:
            if self.left:
                window.blit(Goblin.hit_left[self.hit_count // 3], (self.x, self.y))
            elif self.right:
                window.blit(Goblin.hit_right[self.hit_count // 3], (self.x, self.y))
            self.hit_count += 1
        # Stand
        elif self.standing:
            if self.left:
                window.blit(Goblin.walk_left[0], (self.x, self.y))
            elif self.right:
                window.blit(Goblin.walk_right[0], (self.x, self.y))
            # Should a stand image
            else:
                window.blit(Goblin.walk_left[0], (self.x, self.y))
            self.walk_count = 0
        # Walk
        elif self.walking:
            if self.left:
                window.blit(Goblin.walk_left[self.walk_count // 3], (self.x, self.y))
            elif self.right:
                window.blit(Goblin.walk_right[self.walk_count // 3], (self.x, self.y))
            self.walk_count += 1
        # pg.draw.rect(window, (255, 0, 0), self.hitbox, 2)
        # pg.draw.rect(window, (255, 0, 0), self.hitbox_leftfist, 2)
        # pg.draw.rect(window, (255, 0, 0), self.hitbox_rightfist, 2)


class Soldier(Player):
    walk_left = [image for image in image_left]
    walk_right = [image for image in image_right]
    stand = image_stand
    width = 256  # Soldier width
    height = 256  # Soldier height
    walk_left_most = -60
    walk_right_most = 700
    walk_limit = 27  # Walk 27 times in a direction
    shot_time = 500  # Spend to shot (millisecond)
    bullet_max = 15
    reload_time = 1000  # spend to reload (millisecond)

    def __init__(self, P_id, name='soldier', x=None, y=HEIGHT - height - 10, horizon_move=5, jump_limit=25, extra_harm=0):
        x = Soldier.walk_left_most if P_id == 1 else Soldier.walk_right_most
        super().__init__(P_id, name + str(P_id), x, y, horizon_move, jump_limit)
        self.walk_count = 0  # Record walk count soldier haven walk now
        self.bullet_count = Soldier.bullet_max
        self.shooting = False  # Soldier is shooting
        self.extra_harm = extra_harm  # Total harm = Projectile.shot_harm + self.extra_harm
        self.shot_start = 0
        self.shot_end = 0
        self.shot_bullets = []
        self.reload = False
        self.reload_start = 0
        self.reload_end = 0
        self.hitbox = pg.rect.Rect(self.x, self.y, Soldier.width, Soldier.height)

    def recover(self):
        self.health_point = 100
        self.x = Soldier.walk_left_most if self.id == 1 else Soldier.walk_right_most
        self.y = HEIGHT - Soldier.height - 10
        self.standing = True
        self.walking = False
        self.jump = False
        self.left = False
        self.right = False
        self.jump_move = self.jump_limit
        self.walk_count = 0
        self.bullet_count = Soldier.bullet_max
        self.shot_bullets.clear()
        self.shooting = False
        self.shot_start = 0
        self.shot_end = 0
        self.reload = False
        self.reload_start = 0
        self.reload_end = 0
        self.hitbox = pg.rect.Rect(self.x, self.y, Soldier.width, Soldier.height)

    def move(self, left_m=False, right_m=False):
        super().move(left_m, right_m)
        # Move left most
        if self.x < Goblin.walk_left_most:
            self.x = Goblin.walk_left_most
        # Move right most
        if self.x > Goblin.walk_right_most:
            self.x = Goblin.walk_right_most

    def shot(self):
        if self.bullet_count and not self.shooting and not self.reload:
            self.shot_bullets.append(Projectile(round(self.x + Soldier.width//2), round(self.y + Soldier.height/2 + 20),
                                                self.right))
            self.shooting = True
            self.shot_start = pg.time.get_ticks()
            self.bullet_count -= 1
            bullet_sound.play()

    def reload_bullet(self):
        if not self.reload:
            self.reload = True
            self.reload_start = pg.time.get_ticks()

    def update(self):
        # Update jump position
        super().update()
        # Update reload info
        if self.reload:
            self.reload_end = pg.time.get_ticks()
            reload_time = self.reload_end - self.reload_start
            if reload_time > Soldier.reload_time:
                self.bullet_count = self.bullet_max
                self.reload = False
        # When shooting
        if self.shooting:
            self.shot_end = pg.time.get_ticks()
            shot_time = self.shot_end - self.shot_start
            if shot_time > Soldier.shot_time:
                self.shooting = False
        # Update hitbox
        if self.left:
            self.hitbox = pg.rect.Rect(self.x + 85, self.y + 52, Soldier.width - 160, Soldier.height - 50)
        elif self.right:
            self.hitbox = pg.rect.Rect(self.x + 80, self.y + 52, Soldier.width - 160, Soldier.height - 50)

    def draw(self, window):
        self.update()

        if self.walk_count >= Soldier.walk_limit:
            self.walk_count = 0

        if self.walking:
            if self.left:
                window.blit(Soldier.walk_left[self.walk_count // 3], (self.x, self.y))
                self.walk_count += 1
            elif self.right:
                window.blit(Soldier.walk_right[self.walk_count // 3], (self.x, self.y))
                self.walk_count += 1
        elif self.standing:
            if self.left:
                window.blit(Soldier.walk_left[0], (self.x, self.y))
            elif self.right:
                window.blit(Soldier.walk_right[0], (self.x, self.y))
            else:
                window.blit(Soldier.stand, (self.x, self.y))
            self.walk_count = 0
        # pg.draw.rect(window, (255, 0, 0), self.hitbox, 2)


    def draw_info(self, window):
        # Draw title
        title = font.render(self.name, True, (247, 79, 7))
        if self.left:
            window.blit(title, title.get_rect(left=self.x + 80, top=self.y + 20))
        else:
            window.blit(title, title.get_rect(left=self.x + 80, top=self.y + 20))
        if self.id == 1:
            # Draw name
            name = font.render(f'P{self.id}: {self.name}', True, (143, 7, 240))
            window.blit(name, name.get_rect(left=10, top=10))
            # Draw health point
            hp = font.render('HP: ', True, (143, 7, 240))
            window.blit(hp, name.get_rect(left=10, top=40))
            pg.draw.line(window, (235, 7, 26), (60, 53), (60 + self.health_point * 1.4, 53), 10)
            # Draw bullets
            BT = font.render('BT: ', True, (143, 7, 240))
            window.blit(BT, name.get_rect(left=10, top=70))
            pg.draw.line(window, (224, 181, 7), (60, 83), (60 + self.bullet_count * 28 / 3, 83), 10)
        else:
            # Draw name
            name = font.render(f'P{self.id}: {self.name}', True, (143, 7, 240))
            window.blit(name, name.get_rect(left=WIDTH - 200, top=10))
            # Draw health point
            hp = font.render('HP: ', True, (143, 7, 240))
            window.blit(hp, name.get_rect(left=WIDTH - 200, top=40))
            pg.draw.line(window, (235, 7, 26), (WIDTH - 150, 53), (WIDTH - 150 + self.health_point * 1.4, 53), 10)
            # Draw bullets
            BT = font.render('BT: ', True, (143, 7, 240))
            window.blit(BT, name.get_rect(left=WIDTH - 200, top=70))
            pg.draw.line(window, (224, 181, 7), (WIDTH - 150, 83), (WIDTH - 150 + self.bullet_count * 28 / 3, 83), 10)

    def update_bullet(self, target):
        for shot_bullet in self.shot_bullets:
            if shot_bullet.shooting:
                shot_bullet.shot(self.extra_harm, target)

    def draw_bullet(self, window):
        for shot_bullet in self.shot_bullets:
            shot_bullet.move()
            if shot_bullet.existence:
                shot_bullet.draw(window)
            else:
                self.shot_bullets.pop(self.shot_bullets.index(shot_bullet))


class Projectile:
    def __init__(self, x, y, facing, color=(0, 0, 0), radius=12, velocity=10):
        self.x = x
        self.y = y
        self.color = color
        self.radius = radius
        self.facing = facing  # True if facing right
        self.velocity = velocity
        self.existence = True
        self.shooting = True  # Indicate bullet still not shot target
        self.harm = 5

    def shot(self, extra_harm, target):
        # True if facing right
        if self.facing:
            if target.hitbox.collidepoint(self.x + self.radius, self.y):
                target.health_point -= self.harm + extra_harm
                bullet_hit_sound.play()
                self.shooting = False
        else:
            if target.hitbox.collidepoint(self.x - self.radius, self.y):
                target.health_point -= self.harm + extra_harm
                bullet_hit_sound.play()
                self.shooting = False

    def move(self):
        if self.facing:
            self.x += self.velocity
        else:
            self.x -= self.velocity
        if not 0 <= self.x <= WIDTH:
            self.existence = False

    def draw(self, window):
        pg.draw.circle(window, self.color, (self.x, self.y), self.radius)


game = True
def init_game(players, window):
    window.blit(background, (0, 0))

    # Recover players
    players[0].recover()
    players[1].recover()

    # Draw info of players
    players[0].draw_info(window)
    players[1].draw_info(window)
def game_over(players):
    global game
    if players[0].health_point <= 0:
        game = False
        return players[1].name
    elif players[1].health_point <= 0:
        game = False
        return players[0].name


# The author is lazy
# There should be a Character Selection Screen
p1 = Goblin(1, extra_harm=50)
p2 = Goblin(2, extra_harm=50)
# players[0] use 'w', 'a', 's' to move , 'f' to attack, 'r' to reload bullets if players[0] is a soldier
# players[1] use 'up', 'left', 'right' to move , '0' to attack, '1' to reload bullets if players[1] is a soldier
# p2 appear right, p1 appear left
players = [p1, p2]

# Initialize game
init_game(players, screen)
pg.mixer.music.play(-1)
run = True
while run:
    clock.tick(FPS)

    # Exit
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False

    # If game over
    winner = game_over(players)

    if game:
        keys = pg.key.get_pressed()

        # Move
        if keys[pg.K_a]:
            players[0].move(left_m=True)
        elif keys[pg.K_d]:
            players[0].move(right_m=True)
        else:
            players[0].move()

        if keys[pg.K_LEFT]:
            players[1].move(left_m=True)
        elif keys[pg.K_RIGHT]:
            players[1].move(right_m=True)
        else:
            players[1].move()

        # Jump
        if not players[0].jump:
            if keys[pg.K_w]:
                players[0].jump = True

        if not players[1].jump:
            if keys[pg.K_UP]:
                players[1].jump = True

        # Shot
        if isinstance(players[0], Soldier):
            if keys[pg.K_f]:
                players[0].shot()
        if isinstance(players[1], Soldier):
            if keys[pg.K_KP0]:
                players[1].shot()

        # Hit
        if isinstance(players[0], Goblin):
            if keys[pg.K_f]:
                players[0].hit(players[1])
        if isinstance(players[1], Goblin):
            if keys[pg.K_KP0]:
                players[1].hit(players[0])

        # Reload
        if isinstance(players[0], Soldier):
            if keys[pg.K_r]:
                players[0].reload_bullet()
        if isinstance(players[1], Soldier):
            if keys[pg.K_KP1]:
                players[1].reload_bullet()

        # Draw background
        screen.blit(background, (0, 0))

        # Draw info of players
        players[0].draw_info(screen)
        players[1].draw_info(screen)

        # Draw player
        players[0].draw(screen)
        players[1].draw(screen)
        if isinstance(players[0], Soldier):
            players[0].update_bullet(players[1])
            players[0].draw_bullet(screen)
        if isinstance(players[1], Soldier):
            players[1].update_bullet(players[0])
            players[1].draw_bullet(screen)

    else:
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE]:
            game = True
            init_game(players, screen)

        screen.blit(background, (0, 0))

        text = big_font.render(f'Winner: {winner}', True, (230, 7, 29))
        screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 7 * 3)))
        text = big_font.render('Enter space to restart ...', True, (14, 10, 245))
        screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 7 * 4)))

    pg.display.update()

pg.quit()
