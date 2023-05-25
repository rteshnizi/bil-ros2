import random
import rclpy
import time
from rclpy.node import Node
from visualization_msgs.msg import Marker
from shapely.geometry import Point

class RViz(Node):
	"""
		This node prepares the visualization messages for R-Viz.
		It does not send those messages.
	"""
	def init(self):
		"""
		Create a RViz utility node.
		"""
		super().__init__("rt_bi_utils_rviz")
		self.get_logger().info("Map Interface...")
		RViz.TRANSLATION_X = 0
		RViz.TRANSLATION_Y = 0
		RViz.SCALE = 1
		self.__publisher = self.create_publisher(Marker, "visualization_marker", 10)

	def _translateCoords(coord):
		c = [RViz.SCALE * (coord[0] + RViz.TRANSLATION_X), RViz.SCALE * ((coord[1]) + RViz.TRANSLATION_Y)]
		return c

	def RandomColorString():
		return "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])

	def CreateCircle(canvas, centerX, centerY, radius, outline, tag, fill="", width=1):
		"""
		Returns shape id

		center: Point

		radius: number

		outline: color string (empty string for transparent)

		fill: color string (empty string for transparent)

		width: number

		tag: a unique identifier (use entity name)
		"""
		marker = Marker()
		marker.header.frame_id = "/bil_frame"
		marker.header.stamp = time.time()
		marker.ns = "bil"
		marker.id
		c = RViz._translateCoords([centerX, centerY])
		centerX = c[0]
		centerY = c[1]
		topLeft = Point((centerX - radius, centerY - radius))
		bottomRight = Point((centerX + radius, centerY + radius))
		shape = canvas.create_oval((topLeft.x, topLeft.y, bottomRight.x, bottomRight.y), outline=outline, fill=fill, width=width, tag=tag)
		# bindMouseEvent(canvas, shape)
		return shape

	def CreatePolygon(canvas, coords, outline, fill, width, tag, hashFill=False, hashDensity=25):
		"""
		Returns shape id

		coords: A list of coordinate pairs [x, y]

		outline: color string (empty string for transparent)

		fill: color string (empty string for transparent)

		width: number

		tag: a unique identifier (use entity name)
		"""
		if hashDensity not in [75, 50, 25, 12]: raise AssertionError("Density should be one of 75, 50, 25, or 12.")
		coords = [RViz._translateCoords(c) for c in coords]
		hashStr = "gray%d" % hashDensity if hashFill else ""
		shape = canvas.create_polygon(coords, outline=outline, fill=fill, width=width, tag=tag, stipple=hashStr)
		# Drawing.bindMouseEvent(canvas, shape)
		return shape

	def CreateLine(canvas, coords, color, tag, width=1, dash=(), arrow=False):
		"""
		Returns shape id, or None if there are no points.

		coords: A list of coordinate pairs [x, y]

		color: color string (empty string for transparent)

		width: number; default is 1

		dash: Dash pattern, given as a list of segment lengths. Only the odd segments are drawn.

		tag: a unique identifier (use entity name)
		"""
		if len(coords) == 0: return None
		coords = [RViz._translateCoords(c) for c in coords]
		shape = canvas.create_line(coords, fill=color, width=width, dash=dash, tag=tag, arrow=LAST if arrow else None)
		# Drawing.bindMouseEvent(canvas, shape)
		return shape

	def CreateText(canvas, coords, text, tag, color="Black", fontSize=10):
		"""
		Returns shape id

		coords: A list of coordinate pairs [x, y]

		text: to be rendered

		color: color string (default black)

		fontSize: number; default is 10
		"""
		coords = RViz._translateCoords(coords)
		shape = canvas.create_text(coords[0], coords[1], text=text, fill=color, font="Consolas %d" % fontSize, tag=tag)
		# Drawing.bindMouseEvent(canvas, shape)
		return shape

	def RemoveShape(canvas, shapeId):
		"""
		Remove a shape from canvas
		"""
		canvas.delete(shapeId)
