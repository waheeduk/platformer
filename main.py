import arcade

SCREEN_HEIGHT = 600 
SCREEN_WIDTH = 1200
SCREEN_TITLE = "THE INVINCIBLES"

class MyGame(arcade.Window):
	"""
	Main application class
	"""

	def __init__(self):
		#call parent class
		super().__init__(SCREEN_WIDTH,SCREEN_HEIGHT, SCREEN_TITLE)
		arcade.set_background_color(arcade.csscolor.AZURE)

	def setup(self):
		"""sets up the game"""
		pass

	def on_draw(self):
		"""render the screen"""
		arcade.start_render()

def main():
	"""main method"""
	window = MyGame()
	window.setup()
	arcade.run()

if __name__ == "__main__":
	main()