import arcade
import time

#constants
SCREEN_HEIGHT = 600 
SCREEN_WIDTH = 1200
SCREEN_TITLE = "THE GAME"
TILE_SCALING = 1
GRID_SIZE = 64
LASER_SCALING = 0.5

#player constants
PLAYER_MOVEMENT_SPEED = 5
PLAYER_SWIM_SPEED = 2
PLAYER_JUMP_SPEED = 10
PLAYER_DASH_SPEED = 20
GRAVITY = 0.5
FLUID_GRAVITY = 0.1
LASER_SPEED = 25

#enemy constants
ENEMY_PATROL_SPEED = 3
ENEMY_LASER_SPEED = 10

STARTING_POINT = 0
MOVING_PLATFORM_SPEED = 5
UPDATES_PER_FRAME = 5

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 250
RIGHT_VIEWPORT_MARGIN = 250
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100

RIGHT_FACING = 0
LEFT_FACING = 1

def load_texture_pair(filename):
	"""load a texture pair"""
	return [
		arcade.load_texture(filename),
		arcade.load_texture(filename, mirrored= True)
	]

class PlayerCharacter(arcade.Sprite):
	"""Player sprite"""
	def __init__(self):
		#set up parent class
		super().__init__()

		#character faces right by default
		self.character_face_direction = RIGHT_FACING

		self.cur_texture = 0
		self.scale = TILE_SCALING

		#load textures
		#main directory where art is held
		main_path = "art/PNG/Players/Player Blue/playerBlue"

		#load textures for idle
		self.idle_texture = load_texture_pair(f"{main_path}_stand.png")

		#load textures for running/walking
		self.run_textures = [ ]
		for i in range(6):
			texture = load_texture_pair(f"{main_path}_walk{i}.png")
			self.run_textures.append(texture)
		
		#set initial texture, default idle, facing right
		self.texture = self.idle_texture[0]

		#create hitbox
		self.set_hit_box(self.texture.hit_box_points)		
	
	def update_animation(self, delta_time: float = 1/60):
		
		#figure out if its right or left
		if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
			self.character_face_direction = LEFT_FACING
		elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
			self.character_face_direction = RIGHT_FACING

		#idle animation
		if self.change_x == 0:
			self.texture = self.idle_texture[self.character_face_direction]
			return
		
		#running animation
		self.cur_texture += 1
		if self.cur_texture > 5 * UPDATES_PER_FRAME:
			self.cur_texture = 1
		self.texture = self.run_textures[self.cur_texture//UPDATES_PER_FRAME][self.character_face_direction]


class MyGame(arcade.Window):
	"""
	Main application class
	"""

	def __init__(self):
		#call parent class
		super().__init__(SCREEN_WIDTH,SCREEN_HEIGHT, SCREEN_TITLE)
		arcade.set_background_color(arcade.csscolor.AZURE)

		#keeps track of frames
		self.frame_count = 0

		self.ability_count = 0
		self.heart_count = 3

		#track player state
		self.in_fluid = False
		self.START_X = 64
		self.START_Y = (12*GRID_SIZE) +32

		#track current state of what key is pressed
		self.left_pressed = False
		self.right_pressed = False
		self.up_pressed = False
		self.down_pressed = False
		self.jump_needs_reset = False
		self.dash_pressed = False
		self.shoot_pressed = False
		self.parry_pressed = False

		#lists to keep track of sprites
		self.wall_list = None
		self.coin_list = None
		self.player_list = None
		self.bullet_list = None
		self.background_list = None
		self.scalable_wall_list = None
		self.ladder_list = None
		self.gem_list = None
		self.checkpoint_list = None
		self.heart_list = None

		self.heart_sprite = None

		self.player_sprite = None
		self.physics_engine = None 

		self.checkpoint = -1

		self.distance = 0

		#keeps track of scroll margins
		self.view_bottom = 0
		self.view_left = 0

		#load sounds
		self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

	def setup(self):
		#creates the sprite lists
		self.player_list = arcade.SpriteList()
		self.bullet_list = arcade.SpriteList()
		self.wall_list = arcade.SpriteList(use_spatial_hash=True)
		self.scalable_wall_list = arcade.SpriteList(use_spatial_hash=True)
		self.background_list = arcade.SpriteList()
		self.water_list = arcade.SpriteList()
		self.ladder_list = arcade.SpriteList()
		self.enemy_list = arcade.SpriteList()
		self.projectile_enemy_list = arcade.SpriteList()
		self.enemy_laser_list = arcade.SpriteList()
		self.moving_platform_list = arcade.SpriteList(use_spatial_hash=True)
		self.invisible_platform_list = arcade.SpriteList()
		self.heart_list = arcade.SpriteList()
		self.checkpoint_list = arcade.SpriteList()
		self.gem_list = arcade.SpriteList()
		self.ability_reset_count = 0

		#sets up the player and drops it at a location
		self.player_sprite = PlayerCharacter()
		self.player_sprite.center_x = self.START_X
		self.player_sprite.center_y = self.START_Y
		self.player_list.append(self.player_sprite)


		#load map from map editor

		#name of map file to load
		map_name = "map/map_overworld.tmx"
		#name of the layer in the file that has the platform
		platforms_layer_name = 'Platforms'
		moving_platforms_layer_name = 'Moving Platforms'
		ladders_layer_name = 'Ladders'
		invisible_platform_layer_name = 'Invisible Platforms'
		scalable_wall_layer_name = 'Scalable'

		#layer containing background items
		background_layer_name = 'Background'
		#layer containing items that will cause death and a reset
		water_layer_name = 'Water'

		#layer containing general enemies loaded in
		enemy_layer_name = 'Enemies'

		#layer contaning enemies that shoot projectiles
		projectile_enemy_layer_name = 'Projectile Enemies'

		#layer containing checkpoint
		checkpoint_layer_name = 'Checkpoint'

		#layer containing gems
		gem_layer_name = 'Gems'

		#read in tiled map
		my_map = arcade.tilemap.read_tmx(map_name)

		#brings in background tiles
		self.background_list = arcade.tilemap.process_layer(my_map,
															background_layer_name,
															TILE_SCALING)
		


		#brings in platforms tiles
		self.wall_list = arcade.tilemap.process_layer(map_object = my_map,
													  layer_name = platforms_layer_name,
													  scaling = TILE_SCALING)

		#brings in scalable walls
		self.scalable_wall_list = arcade.tilemap.process_layer(map_object= my_map,
																layer_name=scalable_wall_layer_name,
																scaling = TILE_SCALING)

		#brings in ladder tiles
		self.ladder_list = arcade.tilemap.process_layer(map_object = my_map,
														layer_name = ladders_layer_name,
														scaling=  TILE_SCALING)
		
		#water layer
		self.water_list = arcade.tilemap.process_layer(map_object = my_map,
														layer_name = water_layer_name,
														scaling = TILE_SCALING)

		#brings in moving platforms
		self.moving_platform_list = arcade.tilemap.process_layer(map_object = my_map,
																 layer_name = moving_platforms_layer_name,
																 scaling = TILE_SCALING)

		#brings in general enemies
		self.enemy_list = arcade.tilemap.process_layer(map_object= my_map,
														layer_name= enemy_layer_name,
														scaling=TILE_SCALING)

		#brings in enemies that shoot projectiles
		self.projectile_enemy_list = arcade.tilemap.process_layer(map_object=my_map,
																layer_name=projectile_enemy_layer_name,
																scaling= TILE_SCALING)

		#brings in platforms that pen in enemies
		self.invisible_platform_list = arcade.tilemap.process_layer(map_object = my_map,
																	layer_name= invisible_platform_layer_name,
																	scaling=TILE_SCALING)

		#brings in checkpoint layers
		self.checkpoint_list = arcade.tilemap.process_layer(map_object=my_map,
		layer_name=checkpoint_layer_name,
		scaling=TILE_SCALING)

		#brings in gems
		self.gem_list = arcade.tilemap.process_layer(map_object=my_map,
													layer_name= gem_layer_name,
													scaling=TILE_SCALING)

		#creates a list of all the platforms that the physics engine takes a note of
		self.all_platform_list = arcade.SpriteList(use_spatial_hash=True)
		for platform in self.wall_list:
			self.all_platform_list.append(platform)
		for scalable in self.scalable_wall_list:
			self.all_platform_list.append(scalable)

		if my_map.background_color:
			arcade.set_background_color(my_map.background_color)

		#create physics engine
		self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
															 self.all_platform_list,
															 gravity_constant = GRAVITY,
															 ladders = self.ladder_list)

	def process_keychange(self):
		# Process up/down
		if self.up_pressed and not self.down_pressed:
			if self.physics_engine.is_on_ladder():
				self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
			elif self.physics_engine.can_jump() and not self.jump_needs_reset:
				self.player_sprite.change_y = PLAYER_JUMP_SPEED
				self.jump_needs_reset = True
				arcade.play_sound(self.jump_sound)
		elif self.down_pressed and not self.up_pressed:
			if self.physics_engine.is_on_ladder():
				self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED

		# Process up/down when on a ladder and no movement
		if self.physics_engine.is_on_ladder():
			if not self.up_pressed and not self.down_pressed:
				self.player_sprite.change_y = 0
			elif self.up_pressed and self.down_pressed:
				self.player_sprite.change_y = 0

		# Process left/right
		if self.right_pressed and not self.left_pressed:
			self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
		elif self.left_pressed and not self.right_pressed:
			self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
		else:
			self.player_sprite.change_x = 0

		#process dash
		if self.dash_pressed and self.right_pressed and self.ability_count > 0:
			self.player_sprite.change_x = PLAYER_DASH_SPEED
		elif self.dash_pressed and self.left_pressed and self.ability_count >0:
			self.player_sprite.change_x = -PLAYER_DASH_SPEED
		
		#process shooting
		if self.shoot_pressed and self.left_pressed and self.ability_count > 0:
			#creates laser
			laser = arcade.Sprite("art/PNG/lasers/laserBlueHorizontal.png", scale=LASER_SCALING)
			#position the laser
			laser.center_x = self.player_sprite.center_x
			laser.center_y = self.player_sprite.center_y
			#gives laser speed and direction
			laser.change_x = -LASER_SPEED
			self.bullet_list.append(laser)
			#removes ability after being used once
			self.ability_count -=1
		elif self.shoot_pressed and self.ability_count > 0:
			#creates laser
			laser = arcade.Sprite("art/PNG/lasers/laserBlueHorizontal.png", scale=LASER_SCALING)
			#position the laser
			laser.center_x = self.player_sprite.center_x
			laser.center_y = self.player_sprite.center_y
			#gives laser speed and direction
			laser.change_x = LASER_SPEED
			self.bullet_list.append(laser)
			#removes ability after being used once
			self.ability_count -=1

		#process swimming
		if self.in_fluid == True:
			#reduces gravity to give swimming a floatier feel
			self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
			self.all_platform_list,
			gravity_constant= FLUID_GRAVITY,
			ladders=self.ladder_list)
			#process underwater movement left/right/up/down
			if self.left_pressed:
				self.player_sprite.change_x = -PLAYER_SWIM_SPEED
			elif self.right_pressed:
				self.player_sprite.change_x = PLAYER_SWIM_SPEED
			elif self.up_pressed:
				self.player_sprite.change_y = PLAYER_SWIM_SPEED
			elif self.down_pressed:
				self.player_sprite.change_y = -PLAYER_SWIM_SPEED
			#process underwater dash
			elif self.dash_pressed and self.right_pressed:
				self.player_sprite.change_x = PLAYER_DASH_SPEED
			elif self.dash_pressed and self.left_pressed:
				self.player_sprite.change_x = -PLAYER_DASH_SPEED
			#underwater parry should work regardless, test this out
		else:
			#returns physics back to normal
			self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
															 self.all_platform_list,
															 gravity_constant = GRAVITY,
															 ladders = self.ladder_list)

	def on_key_press(self, key, modifiers):
		"""called whenever a key is pressed"""
		if key == arcade.key.UP or key == arcade.key.W:
			self.up_pressed = True
		elif key == arcade.key.DOWN or key == arcade.key.S:
			self.down_pressed = True
		elif key == arcade.key.LEFT or key == arcade.key.A:
			self.left_pressed = True
		elif key == arcade.key.RIGHT or key == arcade.key.D:
			self.right_pressed = True
		elif key == arcade.key.SPACE:
			self.dash_pressed = True
		elif key == arcade.key.RETURN:
			self.shoot_pressed = True
		elif key == arcade.key.E:
			self.parry_pressed = True

		self.process_keychange()

	def on_key_release(self, key, modifiers):
		"""Called when the user releases a key. """

		if key == arcade.key.UP or key == arcade.key.W:
			self.up_pressed = False
			self.jump_needs_reset = False
		elif key == arcade.key.DOWN or key == arcade.key.S:
			self.down_pressed = False
		elif key == arcade.key.LEFT or key == arcade.key.A:
			self.left_pressed = False
		elif key == arcade.key.RIGHT or key == arcade.key.D:
			self.right_pressed = False
		elif key == arcade.key.SPACE:
			self.dash_pressed = False
			if self.ability_count > 0:
				self.ability_count -= 1
			print(self.ability_count)
		elif key == arcade.key.RETURN:
			self.shoot_pressed = False
		elif key == arcade.key.E:
			self.parry_pressed = False

	def on_draw(self):
		"""render the screen"""
		arcade.start_render()
		self.background_list.draw()
		self.water_list.draw()
		self.wall_list.draw()
		self.scalable_wall_list.draw()
		self.ladder_list.draw()
		self.checkpoint_list.draw()
		self.player_list.draw()
		self.moving_platform_list.draw()
		self.bullet_list.draw()
		self.enemy_list.draw()
		self.projectile_enemy_list.draw()
		self.gem_list.draw()
		self.enemy_laser_list.draw()
		#creates hearts to show the player lives
		#move to draw function and draw individually

		# self.heart_list.draw()
		self.heart_sprite.draw()

	def reset_position(self):
		#move the player to start
		self.player_sprite.center_x = self.START_X
		self.player_sprite.center_y = self.START_Y

		#reset camera to start
		self.view_left = 0
		self.view_bottom = 0
		changed_viewport = 0
		self.ability_count += self.ability_reset_count
		self.heart_count -= 1
		self.ability_reset_count = 0

	def on_update(self, delta_time):
		""" Movement and game logic """
		self.frame_count += 1

		# Move the player with the physics engine
		self.physics_engine.update()

		#check if the player is in water, water is always at a certain level, so
		#can just check if player is below this level

		if self.player_sprite.center_y < 9 * GRID_SIZE:
			self.in_fluid = True
		else:
			self.in_fluid = False

		# Update animations
		if self.physics_engine.can_jump():
			self.player_sprite.can_jump = False
		else:
			self.player_sprite.can_jump = True

		if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
			self.player_sprite.is_on_ladder = True
			self.process_keychange()
		else:
			self.player_sprite.is_on_ladder = False
			self.process_keychange()

		self.player_list.update_animation(delta_time)

		self.bullet_list.update()

		#remove lasers if they go offscreen to save memory
		for laser in self.bullet_list:
			if laser.center_x + 18 > self.view_left + SCREEN_WIDTH:
				laser.remove_from_sprite_lists()
				print('laser removed')
			elif laser.center_x - 18 < self.view_left:
				laser.remove_from_sprite_lists()
				print('laser removed')

		#check to see if enemies were hit by player laser, in which case they are 
		#destroyed
		for laser in self.bullet_list:
			enemy_hit_list = arcade.check_for_collision_with_list(laser, self.enemy_list)
			projectile_enemy_hit_list = arcade.check_for_collision_with_list(laser, self.projectile_enemy_list)
			if len(enemy_hit_list) > 0:
				laser.remove_from_sprite_lists()
				for enemy in enemy_hit_list:
					enemy.remove_from_sprite_lists()
				continue
			elif len(projectile_enemy_hit_list) > 0:
				laser.remove_from_sprite_lists()
				for enemy in projectile_enemy_hit_list:
					enemy.remove_from_sprite_lists()
				continue

		#initialise the heart sprite
		self.heart_sprite = arcade.Sprite("art/PNG/Other/heart.png", scale=LASER_SCALING, center_x= -188, center_y= 346)

		#check to see if gems were contacted by player sprite, in which case the 
		#player gains an ability point
		gem_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.gem_list)
		for gem in gem_hit_list:
			self.ability_reset_count += 1
			gem.remove_from_sprite_lists()
			#add the gems collected to a list so they can be recalled upon reset
			self.ability_count += 1

		#make enemies patrol on platforms
		#create invisible platforms in foreground, i.e. platforms we do not call in
		#draw, and then if enemy collides with these, they turn around
		for enemy in self.enemy_list:
			if enemy.change_x >0.5 and arcade.check_for_collision_with_list(enemy, self.invisible_platform_list):
				enemy.change_x = -ENEMY_PATROL_SPEED 
			elif enemy.change_x <-0.5 and arcade.check_for_collision_with_list(enemy, self.invisible_platform_list):
				enemy.change_x = ENEMY_PATROL_SPEED
			elif enemy.change_x == 0:
				enemy.change_x = ENEMY_PATROL_SPEED

		#build double jump	
		if arcade.check_for_collision_with_list(self.player_sprite, self.scalable_wall_list) == True:
			self.player_sprite.change_y = PLAYER_DASH_SPEED
			print(self.player_sprite.change_y)
			print('Collision detected')
			self.physics_engine.can_jump()

		self.frame_count +=1
		for enemy in self.projectile_enemy_list:
			if self.frame_count % 240 == 0:
				enemy_laser = arcade.Sprite("art/PNG/lasers/laserRedVertical.png", scale=LASER_SCALING)
				enemy_laser.center_x = enemy.center_x
				enemy_laser.center_y = enemy.center_y - 54
				enemy_laser.change_y = -ENEMY_LASER_SPEED
				self.enemy_laser_list.append(enemy_laser)

		for laser in self.enemy_laser_list:
			projectile_enemy_hit_list = arcade.check_for_collision_with_list(laser, self.projectile_enemy_list)
			#removes laser if it hits a platform
			if arcade.check_for_collision_with_list(laser, self.wall_list):
				laser.remove_from_sprite_lists()
			if len(projectile_enemy_hit_list) >0:
				laser.remove_from_sprite_lists()
				for enemy in projectile_enemy_hit_list:
					enemy.remove_from_sprite_lists()
				continue
			#gets distance between player and laser, then creates parry mechanic
			self.distance = arcade.get_distance_between_sprites(laser, self.player_sprite)
			if self.parry_pressed and self.distance < 80:
				laser.change_y = ENEMY_LASER_SPEED

		self.enemy_laser_list.update()
		self.projectile_enemy_list.update()

		self.enemy_list.update()

		#----TRACK DEATH EVENTS----#

		#check if player fell off map, this also works for the player falls in
		#water, as the water level is always nine grid blocks above 0
		if self.player_sprite.center_y < 1 * GRID_SIZE:
			self.reset_position()

		# print(self.player_sprite.center_y)

		#check if player came into contact with general/type enemy, and then 'dies'
		if arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list):
			self.reset_position()
		
		if arcade.check_for_collision_with_list(self.player_sprite, self.projectile_enemy_list):
			self.reset_position()

		if arcade.check_for_collision_with_list(self.player_sprite, self.enemy_laser_list):
			self.reset_position()

		#checks to see if the player hit the checkpoint, in which case their
		#starting coordinates are reset to the checkpoint
		if arcade.check_for_collision_with_list(self.player_sprite, self.checkpoint_list):
			print('checkpoint collision detectedd')
			#coordinates should roughly be 2400, 992
			self.START_X = self.checkpoint_list[0].center_x
			self.START_Y = self.checkpoint_list[0].center_y
			print(self.START_X)

		# Track if we need to change the viewport
		changed = False

        # Scroll left
		left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
		if self.player_sprite.left < left_boundary:
			self.view_left -= left_boundary - self.player_sprite.left
			changed = True

        # Scroll right
		right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
		if self.player_sprite.right > right_boundary:
			self.view_left += self.player_sprite.right - right_boundary
			changed = True

		# Scroll up
		top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
		if self.player_sprite.top > top_boundary:
			self.view_bottom += self.player_sprite.top - top_boundary
			changed = True

        # Scroll down
		bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
		if self.player_sprite.bottom < bottom_boundary:
			self.view_bottom -= bottom_boundary - self.player_sprite.bottom
			changed = True

		if changed:
            # Only scroll to integers. Otherwise we end up with pixels that
            # don't line up on the screen
			self.view_bottom = int(self.view_bottom)
			self.view_left = int(self.view_left)

            # Do the scrolling
			arcade.set_viewport(self.view_left,
								SCREEN_WIDTH + self.view_left,
								self.view_bottom,
								SCREEN_HEIGHT + self.view_bottom)

def main():
	"""main method"""
	window = MyGame()
	window.setup()
	arcade.run()

if __name__ == "__main__":
	main()