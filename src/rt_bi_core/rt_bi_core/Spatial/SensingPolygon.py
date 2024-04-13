from typing import Literal

from rt_bi_commons.Shared.Color import RGBA, ColorNames
from rt_bi_commons.Shared.Pose import Coords, CoordsList
from rt_bi_commons.Shared.Predicates import Predicates
from rt_bi_commons.Utils import Ros
from rt_bi_commons.Utils.RViz import RViz
from rt_bi_core.Spatial.AffinePolygonBase import AffinePolygonBase
from rt_bi_core.Spatial.Tracklet import Tracklet


class SensingPolygon(AffinePolygonBase):
	"""
	An Affine Polygon within which we are able to observe moving targets.
	"""
	type: Literal[AffinePolygonBase.Types.SENSING] = AffinePolygonBase.Types.SENSING
	Type = Literal[AffinePolygonBase.Types.SENSING]
	def __init__(self,
			polygonId: str,
			regionId: str,
			subPartId: str,
			envelope: CoordsList,
			centerOfRotation: Coords,
			timeNanoSecs: int,
			predicates: Predicates,
			tracklets: dict[str, Tracklet] = {},
			**kwArgs
		) -> None:
		super().__init__(
			polygonId=polygonId,
			regionId=regionId,
			subPartId=subPartId,
			envelope=envelope,
			predicates=predicates,
			envelopeColor=kwArgs.pop("envelopeColor", ColorNames.GREEN_LIGHT),
			timeNanoSecs=timeNanoSecs,
			centerOfRotation=centerOfRotation,
			**kwArgs
		)
		self.__tracklets: dict[str, Tracklet] = {}
		for i in tracklets:
			if not tracklets[i].exited:
				self.__tracklets[i] = tracklets[i]

	@property
	def tracklets(self) -> dict[str, Tracklet]:
		"""The information about every tracklet, if any, within this sensing region."""
		return self.__tracklets

	@property
	def hasTrack(self) -> bool:
		"""
		Whether this sensing region contains any track observations information.

		:return: `True` if there is any tracklets information, `False` otherwise.
		:rtype: bool
		"""
		return len(self.__tracklets) > 0

	@property
	def trackEntered(self) -> bool:
		if not self.hasTrack: return False
		for trackId in self.tracklets:
			tracklet = self.tracklets[trackId]
			if tracklet.entered: return True
		return False

	@property
	def trackExited(self) -> bool:
		if not self.hasTrack: return False
		for trackId in self.tracklets:
			tracklet = self.tracklets[trackId]
			if tracklet.exited: return True
		return False

	def createMarkers(self, durationNs: int = AffinePolygonBase.DEFAULT_RENDER_DURATION_NS, renderText: bool = False, envelopeColor: RGBA | None = None, stamped: bool = True, renderTracklet = True) -> list[RViz.Msgs.Marker]:
		msgs = super().createMarkers(durationNs=durationNs, renderText=renderText, envelopeColor=envelopeColor, stamped=stamped)
		if renderTracklet:
			for i in self.__tracklets: Ros.ConcatMessageArray(msgs, self.__tracklets[i].createMarkers())
		return msgs

	def deleteMarkers(self) -> list[RViz.Msgs.Marker]:
		msgs = super().deleteMarkers()
		for tracklet in self.__tracklets: Ros.ConcatMessageArray(msgs, self.__tracklets[tracklet].deleteMarkers())
		return msgs
