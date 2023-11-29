from typing import List

import rclpy
from rclpy.node import Node

import rt_bi_utils.Ros as RosUtils
from rt_bi_core.Model.PolygonalRegion import PolygonalRegion


class DynamicReachability(Node):
	"""
	This Node listens to all the messages published on the topics related to the Dynamic Reachability.
	This node combines topic listeners and service clients.
	"""
	def __init__(self) -> None:
		""" Create a Dynamic Reachability node. """
		super().__init__(node_name="rt_bi_core_dr") # type: ignore - parameter_overrides: List[Parameter] = None
		self.get_logger().info("%s is initializing." % self.get_fully_qualified_name())
		RosUtils.SetLogger(self.get_logger())

	def render(self, regions: List[PolygonalRegion]) -> None:
		self.get_logger().info("Render BA.")
		return

def main(args=None):
	rclpy.init(args=args)
	node = DynamicReachability()
	rclpy.spin(node)
	node.destroy_node()
	rclpy.shutdown()
	return

if __name__ == "__main__":
	main()
