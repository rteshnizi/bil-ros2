import logging
from functools import partial
from math import inf, isnan, nan
from typing import AbstractSet, Any, Callable, Sequence, TypeVar, cast

import rclpy
from builtin_interfaces.msg import Duration, Time as TimeMsg
from rclpy.clock import Time
from rclpy.impl.rcutils_logger import RcutilsLogger
from rclpy.logging import LoggingSeverity
from rclpy.node import Client, Node, Publisher, Service, Subscription, Timer
from typing_extensions import deprecated

__Topic = TypeVar("__Topic")

NAMESPACE = "rt_bi_core"
__LOGGER: RcutilsLogger | None = None
# In case of failure to obtain a ROS logger, the default Python logger will be used, which most likely will log to std stream.
logging.basicConfig(format="[+][%(levelname)s]: %(message)s", force=True)
__rtBiLog: Callable[[str], bool] = lambda m: False
__strNameToIdNum: dict[str, int] = dict()
"""This map helps us assume nothing about the meaning of the names assigned to any regions."""
NANO_CONVERSION_CONSTANT = 10 ** 9


def SetLogger(logger: RcutilsLogger, defaultSeverity: LoggingSeverity) -> None:
	global __LOGGER
	global __rtBiLog
	__LOGGER = logger
	__rtBiLog = partial(__LOGGER.log, severity=defaultSeverity)
	return

def Logger() -> RcutilsLogger | logging.Logger:
	global __LOGGER
	if __LOGGER is None:
		context = rclpy.get_default_context()
		if not context.ok():
			logging.error("ROS context not OK!")
			return logging.getLogger()
		if not context._logging_initialized:
			logging.error("Logging not initialized!")
			return logging.getLogger()
		rosNodes = rclpy.get_global_executor().get_nodes()
		if len(rosNodes) == 0:
			logging.warn("No ROS nodes added to executor! Defaulting to python logger.")
			return logging.getLogger()
		__LOGGER = rosNodes[0].get_logger()
	return __LOGGER

def Log(msg: str) -> bool:
	global __rtBiLog
	return __rtBiLog(msg)

def Now(node: Node | None) -> Time:
	if node is not None:
		return node.get_clock().now()

	context = rclpy.get_default_context()
	if not context.ok():
		raise RuntimeError("ROS context not OK!")
	return rclpy.get_global_executor()._clock.now()

def DurationMsg(sec: int, nanoSec: int) -> Duration:
	d = Duration()
	d.sec = sec
	d.nanosec = nanoSec
	return d

def NanoSecToTimeMsg(nanoSec: int) -> TimeMsg:
	msg = TimeMsg()
	msg.sec = int(nanoSec / NANO_CONVERSION_CONSTANT)
	msg.nanosec = nanoSec % NANO_CONVERSION_CONSTANT
	return msg

def SecToTimeMsg(sec: float) -> TimeMsg:
	msg = TimeMsg()
	msg.sec = int(sec)
	msg.nanosec = int((sec % 1) * NANO_CONVERSION_CONSTANT)
	return msg

def TimeToInt(t: TimeMsg | Time) -> int:
	if isinstance(t, TimeMsg):
		(sec, nanoSecs) = (t.sec, t.nanosec) # CSpell: ignore nanosec
	elif isinstance(t, Time):
		(sec, nanoSecs) = cast(tuple[int, int], t.seconds_nanoseconds())
	else:
		raise ValueError(f"Value is of unknown type: {repr(t)}")
	return ((sec * NANO_CONVERSION_CONSTANT) + nanoSecs)

def CreatePublisher(node: Node, topic: __Topic, topicName: str, callbackFunc: Callable[[__Topic], None] = lambda _: None, intervalSecs: float = nan) -> tuple[Publisher, Timer | None]:
	"""
	Create and return the tuple of `(Publisher, Timer | None)`.

	Parameters
	----------
	`node : Node`
		The node who publishes the topic
	`topic : Topic`
		The data structure of the topic
	`topicName : str`
		The string name of the topic
	`callbackFunc : Callable[[], None]`
		The function callback that would be called to publish the topic
	`interval : int`
		The interval in seconds between each time the topic is published.
		If `nan` (not an number) is given, topics must be published manually.

	Returns
	-------
	`Tuple[Publisher, Union[Timer, None]]`
	"""
	publisher = node.create_publisher(topic, topicName, 10)
	timer = None if isnan(intervalSecs) else node.create_timer(intervalSecs, callbackFunc)
	try:
		freq = " @ %.2fHz" % (1 / intervalSecs)
	except:
		freq = ""
	node.get_logger().debug(f"{node.get_fully_qualified_name()} publishes topic \"{topicName}\"{freq}")
	return (publisher, timer)

def CreateSubscriber(node: Node, topic: __Topic, topicName: str, callbackFunc: Callable[[__Topic], None]) -> Subscription:
	"""
	Create and return the `Subscription`.

	Parameters
	----------
	`node : Node`
		The node who publishes the topic
	`topic : Topic`
		The data structure of the topic
	`topicName : str`
		The string name of the topic
	`callbackFunc : Callable[[], None]`
		The function callback that would be called when the topic is received

	Returns
	-------
	`Subscription`
	"""
	subscription = node.create_subscription(topic, topicName, callbackFunc, 10)
	node.get_logger().debug("%s subscribed to \"%s\"" % (node.get_fully_qualified_name(), topicName))
	return subscription

def CreateTopicName(shortTopicName: str) -> str:
	"""
	Given the short version of the topic name, this function produces the topic name including the namespace etc.

	Parameters
	----------
	shortTopicName : str
		The short name of the publisher's topic.

		For example, `rviz`.

	Returns
	-------
	str
		The full topic name to be used when creating the publisher/subscriber.

		For example, given `rviz` the returned topic would be `/namespace_prefix/rviz`.
	"""
	return "/%s/%s" % (NAMESPACE, shortTopicName)

def AppendMessage(array: Sequence[__Topic] | AbstractSet[__Topic] | list[__Topic], msg: __Topic) -> None:
	"""Appends a message to a message array.

	Parameters
	----------
	array : Union[Sequence, AbstractSet, UserList]
		The array.
	msg : Any
		The message.
	"""
	assert isinstance(array, list), ("Failed to append messages to array. Array type: %s" % type(array))
	array.append(msg)

def GetMessage(array: Sequence[__Topic] | AbstractSet[__Topic] | list[__Topic], i: int, t: type[__Topic] = Any) -> __Topic:
	"""Appends a message to a message array.

	Parameters
	----------
	array : Union[Sequence, AbstractSet, UserList]
		The array.
	msg : Any
		The message.
	"""
	assert isinstance(array, list), ("Failed to append messages to array. Array type: %s" % type(array))
	return array[i]

def ConcatMessageArray(array: Sequence[__Topic] | AbstractSet[__Topic] | list[__Topic], toConcat: Sequence[__Topic]) -> list[__Topic]:
	"""Concatenates an array of messages to another message array.

	Parameters
	----------
	array : Union[Sequence, AbstractSet, UserList]
		The array.
	msg : Any
		The message.
	"""
	assert isinstance(array, list), ("Failed to append messages to array. Array type: %s" % type(array))
	array += toConcat
	return array

@deprecated("IDs are now string, no need to register. Buggy behavior.")
def RegisterRegionId(name: str) -> int:
	if name in __strNameToIdNum:
		idNum = __strNameToIdNum[name]
		Logger().debug("Duplicate region name encountered: %s... same id assigned %d." % (name, idNum))
		return __strNameToIdNum[name]
	idNum = len(__strNameToIdNum)
	__strNameToIdNum[name] = idNum
	return idNum

def CreateTimer(node: Node, callback: Callable, intervalNs = 1000) -> Timer:
	return Timer(callback, None, intervalNs, node.get_clock(), context=node.context)

__ServiceInterface_Request = TypeVar("__ServiceInterface_Request")
__ServiceInterface_Response = TypeVar("__ServiceInterface_Response")
__ServiceInterface = TypeVar("__ServiceInterface")

def CreateService(node: Node, interface: __ServiceInterface, serviceName: str, callbackFunc: Callable[[__ServiceInterface_Request, __ServiceInterface_Response], __ServiceInterface_Response]) -> Service: # type: ignore
	l = list(filter(lambda s: s.srv_name == serviceName, node.services))
	if len(l) == 0: return node.create_service(interface, serviceName, callbackFunc)
	if len(l) == 1: return l[0]
	raise RuntimeError("This should never happen.")

def CreateClient(node: Node, interface: __ServiceInterface, serviceName: str) -> Client: # type: ignore
	l = list(filter(lambda s: s.srv_name == serviceName, node.clients))
	if len(l) == 0: return node.create_client(interface, serviceName)
	if len(l) == 1: return l[0]
	raise RuntimeError("This should never happen.")

def SendClientRequest(node: Node, client: Client, request: __ServiceInterface_Request, responseCallback: Callable[[__ServiceInterface_Request, __ServiceInterface_Response], __ServiceInterface_Response]) -> None:
	future = client.call_async(request)
	rclpy.spin_until_future_complete(node, future)
	responseCallback(request, cast(__ServiceInterface_Response, future.result()))
	return None

def GetSubscriberNames(node: Node, topic: str) -> set[str]:
	subs = node.get_subscriptions_info_by_topic(topic)
	return {f"{s.node_namespace}/{s.node_name}" for s in subs}

def Wait(node: Node, timeoutSec: float = inf) -> None:
	sleepTime = 0.05
	while node.context.ok() and timeoutSec > 0.0:
		rclpy.spin_once(node, timeout_sec=sleepTime)
		timeoutSec -= sleepTime
	return

def WaitForSubscriber(node: Node, topic: str, fullNodeName: str) -> None:
	subsName = GetSubscriberNames(node, topic)
	while fullNodeName not in subsName:
		Wait(node, 1.0)
		subsName = GetSubscriberNames(node, topic)
	return

def WaitForServicesToStart(node: Node, client: Client) -> None:
	while not client.wait_for_service():
		node.get_logger().debug("Client %s is waiting for service %s" % (node.get_name(), client.srv_name))
	node.get_logger().debug("Client %s is ready"% node.get_name())
	return
