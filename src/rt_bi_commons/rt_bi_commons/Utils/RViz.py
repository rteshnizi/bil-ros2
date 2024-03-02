from ctypes import c_int32
from math import cos, sin
from typing import Final
from zlib import adler32

from rclpy.node import Publisher, Timer

from rt_bi_commons.Base.RtBiNode import RtBiNode
from rt_bi_commons.Shared.Color import RGBA, ColorNames
from rt_bi_commons.Utils import Ros
from rt_bi_commons.Utils.Geometry import GeometryLib
from rt_bi_commons.Utils.Msgs import NANO_CONVERSION_CONSTANT, Msgs as MsgsUtils
from rt_bi_commons.Utils.NetworkX import NxUtils

DEFAULT_RENDER_DURATION_NS: Final[int] = int(1.75 * NANO_CONVERSION_CONSTANT)
"""`1.75` secs, converted to NanoSecs."""

class RViz:
	"""
		This class only prepares the visualization messages for R-Viz.
		All the shapes are rendered as Markers.
		Any closed shape is rendered as a LINE_STRIP in which
		the points list contains the same point as its first and last elements.
		http://wiki.ros.org/rviz/Tutorials/Markers%3A%20Points%20and%20Lines#The_Code_Explained
	"""
	import visualization_msgs.msg as Msgs
	Id = NxUtils.Id
	FRAME_ID = "map"

	@staticmethod
	def isRVizReady(node: RtBiNode, publisher: Publisher) -> bool:
		if node.executor is None:
			node.get_logger().error("No Executor.")
			return False
		if any(n for n in node.executor.get_nodes() if n.get_name().lower().find("rviz") > -1):
			node.log("No node containing the name RViz was found.")
			return False
		if publisher.get_subscription_count() == 0:
			node.log("No subscribers to visualization messages.")
			return False
		return True

	@staticmethod
	def createRVizPublisher(node: RtBiNode, topic: str) -> tuple[Publisher, Timer | None]:
		return Ros.CreatePublisher(node, RViz.Msgs.MarkerArray, topic)

	@staticmethod
	def __createPointMessage(x: float, y: float, z = 0.0) -> MsgsUtils.Geometry.Point:
		"""
		Create a Point Msg.

		Parameters
		----------
		x : float
		y : float
		z : float, optional
			by default 0.0
		Returns
		-------
		Point
		"""
		p = MsgsUtils.Geometry.Point()
		p.x = float(x)
		p.y = float(y)
		p.z = float(z)
		return p

	@staticmethod
	def __setMarkerColor(marker: Msgs.Marker, color: RGBA) -> Msgs.Marker:
		marker.color.r = float(color[0])
		marker.color.g = float(color[1])
		marker.color.b = float(color[2])
		marker.color.a = float(color[3])
		return marker

	@staticmethod
	def __setMarkerPose(marker: Msgs.Marker, coords: GeometryLib.Coords) -> Msgs.Marker:
		marker.pose.position.x = float(coords[0])
		marker.pose.position.y = float(coords[1])
		return marker

	@staticmethod
	def __setMarkerId(marker: Msgs.Marker, id: Id, suffix: str) -> Msgs.Marker:
		idStr = f"{repr(id)}{suffix}"
		uInt = adler32(idStr.encode("utf-8"))
		marker.id = c_int32(uInt).value
		return marker

	@staticmethod
	def __setMarkerHeader(marker: Msgs.Marker, durationNs: int) -> Msgs.Marker:
		marker.ns = Ros.NAMESPACE
		marker.action = RViz.Msgs.Marker.ADD
		if durationNs > 0:
			marker.lifetime = MsgsUtils.DurationMsg(int(durationNs / NANO_CONVERSION_CONSTANT), durationNs % NANO_CONVERSION_CONSTANT)
		marker.pose.orientation.w = 1.0
		marker.header.frame_id = RViz.FRAME_ID
		marker.header.stamp = Ros.Now(None).to_msg()
		return marker

	@staticmethod
	def __logMarker(id: Id, suffix: str, created: bool) -> None:
		if created: Ros.Logger().debug(f"Marker {repr(id)}{suffix} created.")
		else: Ros.Logger().debug(f"Marker {repr(id)}{suffix} is set to delete.")
		return

	@staticmethod
	def createCircle(id: Id, centerX: float, centerY: float, radius: float, outline: RGBA, width = 1.0, durationNs: int = DEFAULT_RENDER_DURATION_NS, idSuffix: str = "") -> Msgs.Marker:
		circle = RViz.Msgs.Marker()
		circle = RViz.__setMarkerHeader(circle, durationNs)
		circle = RViz.__setMarkerId(circle, id, idSuffix)
		circle.type = RViz.Msgs.Marker.LINE_STRIP
		circle = RViz.__setMarkerColor(circle, outline)
		# LINE_STRIP markers use only the x component of scale, for the line width
		circle.scale.x = width
		for i in range(32):
			p = RViz.__createPointMessage(centerX + (radius * cos(i)), centerY + (radius * sin(i)))
			Ros.AppendMessage(circle.points, p)
		p = RViz.__createPointMessage(centerX + (radius * cos(0)), centerY + (radius * sin(0)))
		Ros.AppendMessage(circle.points, p)
		RViz.__logMarker(id, idSuffix, True)
		return circle

	@staticmethod
	def createPolygon(id: Id, coords: GeometryLib.CoordsList, outline: RGBA, width: float, durationNs: int = DEFAULT_RENDER_DURATION_NS, idSuffix: str = "") -> Msgs.Marker:
		"""Create a polygon Msgs.Marker message.

		Parameters
		----------
		id : str
			Used for refreshing the same element over successive frames.
		coords : Geometry.Coords
			The placement.
		outline : Color
			The color of the outline.
		width : float
			The width of the rendered outline.

		Returns
		-------
		Msgs.Marker
			The marker message.
		"""
		polygon = RViz.Msgs.Marker()
		polygon = RViz.__setMarkerHeader(polygon, durationNs)
		polygon = RViz.__setMarkerId(polygon, id, idSuffix)
		polygon.type = RViz.Msgs.Marker.LINE_STRIP
		polygon = RViz.__setMarkerColor(polygon, outline)
		# LINE_STRIP markers use only the x component of scale, for the line width
		polygon.scale.x = float(width)
		for (x, y) in coords:
			Ros.AppendMessage(polygon.points, RViz.__createPointMessage(x, y))
		RViz.__logMarker(id, idSuffix, True)

		if GeometryLib.coordsAreEqual(coords[0], coords[-1]): return polygon
		# If the last vertex is not the same as the first one, we need to close the loop-back here.
		Ros.AppendMessage(polygon.points, RViz.__createPointMessage(*coords[0]))
		return polygon

	@staticmethod
	def createLine(id: Id, coords: GeometryLib.CoordsList, outline: RGBA, width: float, arrow = False, durationNs: int = DEFAULT_RENDER_DURATION_NS, idSuffix: str = "") -> Msgs.Marker:
		"""Create a line Msgs.Marker message.

		Parameters
		----------
		id : str
			Used for refreshing the same element over successive frames.
		coords : Geometry.Coords
			The placement.
		outline : Color
			The color.
		width : float
			The width of the rendered line.
		arrow : bool, optional
			Whether to render an arrow-head, by default False.

		Returns
		-------
		Msgs.Marker
			The marker message.
		"""
		Ros.Logger().debug("Render line strip id %s." % id)
		lineSeg = RViz.Msgs.Marker()
		lineSeg = RViz.__setMarkerHeader(lineSeg, durationNs)
		lineSeg = RViz.__setMarkerId(lineSeg, id, idSuffix)
		lineSeg.type = RViz.Msgs.Marker.LINE_STRIP
		lineSeg = RViz.__setMarkerColor(lineSeg, outline)
		# LINE_STRIP markers use only the x component of scale, for the line width
		lineSeg.scale.x = float(width)
		for (x, y) in coords:
			Ros.AppendMessage(lineSeg.points, RViz.__createPointMessage(x, y))
		if arrow: Ros.Logger().info("Rendering arrow-head is not implemented.")
		# if not self.renderArrows: continue
		# (dx, dy) = Geometry.getUnitVectorFromAngle(end.angleFromX)
		# dx = dx * self.HEADING_ARROW_LENGTH
		# dy = dy * self.HEADING_ARROW_LENGTH
		# msgs.append(RViz.createLine(canvas, [[p.pt.x, p.pt.y], [p.pt.x + dx, p.pt.y + dy]], color=self.MARKING_COLOR, tag=self.name, arrow=True))
		RViz.__logMarker(id, idSuffix, True)
		return lineSeg

	@staticmethod
	def createText(id: Id, coords: GeometryLib.Coords, text: str, outline: RGBA = ColorNames.BLACK, fontSize = 10.0, durationNs: int = DEFAULT_RENDER_DURATION_NS, idSuffix: str = "") -> Msgs.Marker:
		"""Create a text Msgs.Marker message.

		Parameters
		----------
		id : str
			Used for refreshing the same element over successive frames.
		coords : Geometry.Coords
			The placement.
		text : str
			The text.
		outline : Color, optional
			The color, by default KnownColors.BLACK
		fontSize : float, optional
			The font size, by default 10.0

		Returns
		-------
		Msgs.Marker
			The marker message.
		"""
		Ros.Logger().debug("Render text id %s." % id)
		textMarker = RViz.Msgs.Marker()
		textMarker = RViz.__setMarkerHeader(textMarker, durationNs)
		textMarker = RViz.__setMarkerId(textMarker, id, idSuffix)
		textMarker.type = RViz.Msgs.Marker.TEXT_VIEW_FACING
		textMarker.text = text
		textMarker = RViz.__setMarkerPose(textMarker, coords)
		textMarker = RViz.__setMarkerColor(textMarker, outline)
		textMarker.scale.z = float(fontSize)
		RViz.__logMarker(id, idSuffix, True)
		return textMarker

	@staticmethod
	def removeMarker(id: Id, idSuffix: str = "") -> Msgs.Marker:
		"""
		Remove a shape from RViz.
		"""
		Ros.Logger().debug("Clear rendered RViz shape id %s." % id)
		marker = RViz.Msgs.Marker()
		marker = RViz.__setMarkerHeader(marker, -1)
		marker.action = RViz.Msgs.Marker.DELETE # To remove shape
		marker = RViz.__setMarkerId(marker, id, idSuffix)
		RViz.__logMarker(id, idSuffix, False)
		return marker

	@staticmethod
	def removeAllMarkers() -> Msgs.Marker:
		"""
		Remove all shapes from RViz
		"""
		marker = RViz.Msgs.Marker()
		marker = RViz.__setMarkerHeader(marker, -1)
		marker.action = RViz.Msgs.Marker.DELETEALL # To remove shape # CSpell: disable-line
		Ros.Logger().debug("Setting all markers to delete.")
		return marker
