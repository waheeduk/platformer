import arcade
import time

#constants
SCREEN_HEIGHT = 600 
SCREEN_WIDTH = 1200
SCREEN_TITLE = "THE GAME"
TILE_SCALING = 1
GRID_SIZE = 64

#player constants
PLAYER_MOVEMENT_SPEED = 5
PLAYER_JUMP_SPEED = 10
GRAVITY = 0.5
START_X = 64
START_Y = (12*GRID_SIZE) +32

STARTING_POINT = 0
MOVING_PLATFORM_SPEED = 5

# How many pixels to keep as a minimum margin between the character
# and the edge of the screen.
LEFT_VIEWPORT_MARGIN = 250
RIGHT_VIEWPORT_MARGIN = 250
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100

class PlayerCharacter(arcade.Sprite):
	"""Player sprite"""
	def __init__(self):
		#set up parent class
		super().__init__()

		self.cur_texture = 0
		self.scale = TILE_SCALING


		#load textures
		#main directory where art is held
		main_path = "art/PNG/Players/Player Blue/playerBlue"

		#load textures for idle
		self.idle_texture = arcade.load_texture(f"{main_path}_stand.png")

		#load textures for running/walking
		self.run_textures = [ ]
		for i in range(6):
			texture = arcade.load_texture(f"{main_path}_walk{i}.png")
			self.run_textures.append(texture)
		
		#set initial texture
		self.texture = self.idle_texture

		#create hitbox
		self.set_hit_box(self.texture.hit_box_points)		
	
	def update_animation(self, delta_time: float = 1/60):
		
		#idle animation
		if self.change_x == 0:
			self.texture = self.idle_texture
			return
		
		#running animation
		self.cur_texture += 1
		if self.cur_texture > 5:
			self.cur_texture = 0
		self.texture = self.run_textures[self.cur_texture]


class MyGame(arcade.Window):
	"""
	Main application class
	"""

	def __init__(self):
		#call parent class
		super().__init__(SCREEN_WIDTH,SCREEN_HEIGHT, SCREEN_TITLE)
		arcade.set_background_color(arcade.csscolor.AZURE)

		#track current state of what key is pressed
		self.left_pressed = False
		self.right_pressed = False
		self.up_pressed = False
		self.down_pressed = False
		self.jump_needs_reset = False

		#lists to keep track of sprites
		self.wall_list = None
		self.coin_list = None
		self.player_list = None
		self.background_list = None
		self.ladder_list = None

		self.player_sprite = None

		self.physics_engine = None 

		#keeps track of scroll margins
		self.view_bottom = 0
		self.view_left = 0

		#load sounds
		self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")

	def setup(self):
		#creates the sprite lists
		self.player_list = arcade.SpriteList()
		self.wall_list = arcade.SpriteList(use_spatial_hash=True)
		self.background_list = arcade.SpriteList()
		self.water_list = arcade.SpriteList()
		self.ladder_list = arcade.SpriteList()
		self.moving_platform_list = arcade.SpriteList(use_spatial_hash=True)

		#sets up the player and drops it at a location
		self.player_sprite = PlayerCharacter()
		self.player_sprite.center_x = START_X
		self.player_sprite.center_y = START_Y
		self.player_list.append(self.player_sprite)

		#load map from map editor

		#name of map file to load
		map_name = "map/map_overworld.tmx"
		#name of the layer in the file that has the platform
		platforms_layer_name = 'Platforms'
		moving_platforms_layer_name = 'Moving Platforms'
		ladders_layer_name = 'Ladders'

		#layer containing background items
		background_layer_name = 'Background'
		#layer containing items that will cause death and a reset
		water_layer_name = 'Water'

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

		
		if my_map.background_color:
			arcade.set_background_color(my_map.background_color)

		#create physics engine
		self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
															 self.wall_list,
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

	def on_draw(self):
		"""render the screen"""
		arcade.start_render()
		self.background_list.draw()
		self.water_list.draw()
		self.wall_list.draw()
		self.ladder_list.draw()
		self.player_list.draw()
		self.moving_platform_list.draw()

	def on_update(self, delta_time):
		""" Movement and game logic """

		# Move the player with the physics engine
		self.physics_engine.update()

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
	
		# Track if we need to change the viewport

		#check if player fell off map, this also works for the player falls in
		#water, as the water level is always nine grid blocks above 0
		if self.player_sprite.center_y < 9* GRID_SIZE:
			self.player_sprite.center_x = START_X
			self.player_sprite.center_y = START_Y

			#reset camera to start
			self.view_left = 0
			self.view_bottom = 0
			changed_viewport = True

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