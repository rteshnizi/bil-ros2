import os
import pathlib

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

packageName = pathlib.Path(__file__).parent.parent.name

def generate_launch_description():
	yamlPath = os.path.join(get_package_share_directory(packageName), "config", "case1.avs.yaml")

	return LaunchDescription([
		Node(
			package=packageName,
			namespace=packageName,
			executable="AvEmulator",
			name="av1",
			parameters=[yamlPath]
		),
		Node(
			package=packageName,
			namespace=packageName,
			executable="AvEmulator",
			name="av2",
			parameters=[yamlPath]
		),
	])
