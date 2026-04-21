""" Constants """
import pyray as pr


ALLOWED_ZONES = [
    "normal",
    "blocked",
    "restricted",
    "priority"
]

ALLOWED_COLORS = [
    "black",
    "blue",
    "brown",
    "crimson",
    "cyan",
    "darkred",
    "gold",
    "green",
    "maroon",
    "orange",
    "purple",
    "rainbow",
    "red",
    "violet",
    "yellow"
]

COLOR_MAP = {
    "black": pr.BLACK,
    "blue": pr.BLUE,
    "brown": pr.BROWN,
    "crimson": (220, 20, 60, 255),
    "cyan": (0, 255, 255, 255),
    "darkred": (139, 0, 0, 255),
    "gold": pr.GOLD,
    "green": pr.GREEN,
    "maroon": pr.MAROON,
    "orange": pr.ORANGE,
    "purple": pr.PURPLE,
    "rainbow": pr.RAYWHITE,
    "red": pr.RED,
    "violet": pr.VIOLET,
    "yellow": pr.YELLOW
}

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
CAMERA_FOV = 80
MOVEMENT_SPEED = 5.0
NODE_SIZE = 0.2
LINE_WIDTH = 3

DRONE_SIZE = 0.2
DRONE_SPEED = 5
