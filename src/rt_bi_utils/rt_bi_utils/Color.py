from typing import Tuple, Union

numeric = Union[int, float]
RGBA = Tuple[numeric, numeric, numeric, numeric]
""" A tuple that represents an RGBA value. Values between [0-1]. """
RGB = Tuple[numeric, numeric, numeric]
""" A tuple that represents an RGB value. Values between [0-1]. """

class RgbaNames:
	BLACK: RGBA = 			(0, 0, 0, 1)
	BLUE: RGBA = 			(0, 0, 1, 1)
	COLD_BLUE: RGBA = 		(0, 0.5, 1, 1)
	CYAN: RGBA =	 		(0, 1, 1, 1)
	DARK_BLUE: RGBA = 		(0, 0, 0.25, 1)
	DARK_CYAN: RGBA = 		(0, 0.5, 0.5, 1)
	DARK_GREEN: RGBA = 		(0, 0.25, 0, 1)
	DARK_GREY: RGBA = 		(0.25, 0.25, 0.25, 1)
	DARK_MAGENTA: RGBA =	(0.7, 0, 0.7, 1)
	DARK_RED: RGBA =		(0.94, 0.24, 0.24, 1)
	DARK_YELLOW: RGBA =		(0.7, 0.7, 0, 1)
	GREEN: RGBA = 			(0, 1, 0, 1)
	GREY: RGBA = 			(0.5, 0.5, 0.5, 1)
	LIGHT_GREEN: RGBA = 	(0.24, 0.94, 0.24, 1)
	LIGHT_GREY: RGBA = 		(0.75, 0.75, 0.75, 1)
	MAGENTA: RGBA = 		(1, 0, 1, 1)
	MAROON: RGBA = 			(0.5, 0, 0, 1)
	ORANGE: RGBA = 			(1, 0.647, 0, 1)
	PURPLE: RGBA = 			(0.36, 0.25, 0.83, 1)
	RED: RGBA = 			(1, 0, 0, 1)
	TRANSPARENT: RGBA = 	(0, 0, 0, 0)
	WHITE: RGBA = 			(1, 1, 1, 1)
	YELLOW: RGBA =			(1, 1, 0, 1)

def toHexStr(color: RGBA) -> str:
	return "#" + "".join(format(int(round(val * 255)), "02x") for val in color)
