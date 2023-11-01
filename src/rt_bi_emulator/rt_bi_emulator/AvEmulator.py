import json
from typing import List

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sa_msgs.msg import RobotState

import rt_bi_utils.Ros as RosUtils
from rt_bi_utils.Geometry import AffineTransform, Geometry, Polygon
from rt_bi_utils.Pose import Pose
from rt_bi_utils.SaMsgs import SaMsgs


class Av:
	def __init__(self, id: int, p: Pose, fov: Geometry.CoordsList) -> None:
		self.robotId: int = id
		self.pose = p
		self.interior = fov

class AvEmulator(Node):
	""" The Viewer ROS Node """
	NANO_CONVERSION_CONSTANT = 10 ** 9
	def __init__(self):
		""" Create a Viewer ROS node. """
		super().__init__(node_name="rt_bi_av_emulator") # type: ignore - parameter_overrides: List[Parameter] = None
		self.get_logger().debug("%s is initializing." % self.get_fully_qualified_name())
		self.__declareParameters()
		RosUtils.SetLogger(self.get_logger())
		self.__robotId = -1
		self.__updateInterval = 1
		self.__initTime = float(self.get_clock().now().nanoseconds)
		self.__avPositions: List[Av] = []
		self.__initFovPoly = Polygon()
		self.__totalTimeNanoSecs = 0.0
		self.__transformationMatrix = AffineTransform()
		self.__parseConfigFileParameters()
		(self.__fovPublisher, _) = SaMsgs.createSaRobotStatePublisher(self, self.__publishMyFov, self.__updateInterval)
		# Junk code below
		self.__passed295 = -1

	def __declareParameters(self) -> None:
		self.get_logger().debug("%s is setting node parameters." % self.get_fully_qualified_name())
		self.declare_parameter("robotId", Parameter.Type.INTEGER)
		self.declare_parameter("updateInterval", Parameter.Type.DOUBLE)
		self.declare_parameter("timeSecs", Parameter.Type.DOUBLE_ARRAY)
		self.declare_parameter("saPose", Parameter.Type.STRING_ARRAY)
		self.declare_parameter("fov", Parameter.Type.STRING_ARRAY)
		return

	def __parseConfigFileParameters(self) -> None:
		self.get_logger().debug("%s is parsing parameters." % self.get_fully_qualified_name())
		self.__robotId = self.get_parameter("robotId").get_parameter_value().integer_value
		self.__updateInterval = self.get_parameter("updateInterval").get_parameter_value().double_value
		timePoints = self.get_parameter("timeSecs").get_parameter_value().double_array_value
		saPoses = self.get_parameter("saPose").get_parameter_value().string_array_value
		saPoses = [json.loads(pose) for pose in saPoses]
		saPoses = tuple(saPoses)
		fov = self.get_parameter("fov").get_parameter_value().string_array_value
		parsedFov = []
		for f in fov:
			f = json.loads(f)
			parsedFov.append([tuple(p) for p in f])
		for i in range(len(timePoints)):
			timeNanoSecs = int(timePoints[i] * AvEmulator.NANO_CONVERSION_CONSTANT)
			self.__avPositions.append(Av(self.__robotId, Pose(timeNanoSecs, *(saPoses[0])), parsedFov[i]))
		self.__initFovPoly = Polygon(self.__avPositions[0].interior)
		self.__transformationMatrix = Geometry.getAffineTransformation(self.__avPositions[0].interior, self.__avPositions[-1].interior)
		self.__totalTimeNanoSecs = timePoints[-1] * AvEmulator.NANO_CONVERSION_CONSTANT
		return

	def __publishMyFov(self) -> None:
		timeOfPublish = float(self.get_clock().now().nanoseconds)
		if self.__passed295 < 0 and ((timeOfPublish - self.__initTime) / AvEmulator.NANO_CONVERSION_CONSTANT) > 29.5:
			self.__passed295 = timeOfPublish
		elif self.__passed295 > 0:
			timeOfPublish = self.__passed295
		elapsedTimeRatio = (timeOfPublish - self.__initTime) / self.__totalTimeNanoSecs
		elapsedTimeRatio = 1 if elapsedTimeRatio > 1 else elapsedTimeRatio
		if elapsedTimeRatio < 1:
			matrix = Geometry.getParameterizedAffineTransformation(self.__transformationMatrix, elapsedTimeRatio)
			fov = Geometry.applyMatrixTransformToPolygon(matrix, self.__initFovPoly)
		else:
			fov = Polygon(self.__avPositions[-1].interior)
		msg = RobotState()
		msg.robot_id = self.__robotId
		msg.pose = SaMsgs.createSaPoseMsg(self.__avPositions[0].pose.x, self.__avPositions[0].pose.y)
		msg.fov = SaMsgs.createSaFovMsg(list(fov.exterior.coords))
		self.get_logger().debug("Sending updated fov location for robot %d @ param = %.3f" % (self.__robotId, elapsedTimeRatio))
		self.__fovPublisher.publish(msg)
		return

def main(args=None):
	"""
	Start the Behavior Inference Run-time.
	"""
	rclpy.init(args=args)
	avNode = AvEmulator()
	rclpy.spin(avNode)
	avNode.destroy_node()
	rclpy.shutdown()
	return

if __name__ == "__main__":
	main()
