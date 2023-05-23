from typing import Dict, List, Union
from shapely.geometry import Polygon
from rt_bi_core.Model.FeatureMap import Feature
from rt_bi_core.Model.MapRegion import MapRegion
from rt_bi_utils.geometry import Geometry, Polygon
from sa_msgs.msg import FeatureInfo
from rclpy.node import Node
from sa_msgs.msg import EstimationMsg

class MapInterface(Node):
	"""The Viewer ROS Node"""
	def __init__(self):
		"""
		Create a Viewer ROS node.

		Parameters
		----------
		mapPath : str, optional
			The path to the JSON file to be parsed, by default "".
		"""
		super().__init__("rt_bi_core_mi")
		self.get_logger().info("Map Interface...")
		self.__regions: Union[Dict[str, MapRegion], None] = None
		self.__regionDefs: Union[FeatureInfo, None] = None
		self.__polygon: Union[Polygon, None] = None
		self.__subscribeToTopics()

	@property
	def polygon(self) -> Polygon:
		if self.__polygon is None:
			polygons = [self.regions[r].polygon for r in self.regions]
			self.__polygon = Geometry.union(polygons)
		return self.__polygon

	def regions(self, update: Union[FeatureInfo, None] = None) -> Dict[str, MapRegion]:
		if self.__regionDefs is None and update is None: return {}
		if update is not None and self.__regionDefs is not None and hash(update) == hash(self.__regionDefs):
			return self.__regions
		regions = {}
		self.__regionDefs = update
		self.get_logger().info("Updating region definitions...")
		for i in range(len(self.__regionDefs.polygon_shape_list)):
			# FIXME: currently visibility_av has the content for both type and visibility_av
			# featureName = self.__regionDefs.type[i]
			featureName = self.__regionDefs.feature_name[i]
			visibilityAv = "self.__regionDefs.visibility_av[i]"
			traversabilityCar = self.__regionDefs.traversability_gv_car[i]
			traversabilityTank = self.__regionDefs.traversability_gv_tank[i]
			feature = Feature(featureName, {
					"visibility_av": visibilityAv,
					"traversability_gv_car": traversabilityCar,
					"traversability_gv_tank": traversabilityTank
			})
			regionName = self.__regionDefs.feature_name[i]
			coords = self.__regionDefs.polygon_shape_list[i]
			self.get_logger().info("Creating region %s..." % regionName)
			regions["r%d" % i] = MapRegion(regionName, coords, featureName, feature)
		self.__regions = regions
		return self.__regions

	def __subscribeToTopics(self) -> None:
		self.create_subscription(FeatureInfo, "/sa_map/FeatureMap_BIL", self.mapUpdate, 10)
		return

	def mapUpdate(self, msg: FeatureInfo) -> None:
		"""
		Callback function for the reception of map messages.
		"""
		self.regions(update=msg)
		self.render()
		return

	def observationUpdate(self, msg: EstimationMsg) -> None:
		"""
		Callback function for the reception of trajectory estimation messages.

		Parameters
		----------
		msg : EstimationMsg
		```python
		float detection_time
		sa_msgs/RobotState robot_state
		sa_msgs/PoseEstimation[] pose_estimations
		int discrete_detections
		```
		"""
		self.get_logger().info("EM")
		return

	def render(self):
		self.get_logger().info("RENDER")
		return
		for region in self.regions.values():
			region.render()

	def clearRender(self):
		for region in self.regions.values():
			region.clearRender()
