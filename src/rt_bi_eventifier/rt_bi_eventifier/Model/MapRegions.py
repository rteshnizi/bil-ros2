from typing import List, Set

from rt_bi_core.MapRegion import MapRegion
from rt_bi_core.RegularAffineRegion import RegularAffineRegion


class MapRegions(RegularAffineRegion[MapRegion]):
	"""A Class to model Shadows."""
	def __init__(self, regions: List[MapRegion] = []):
		"""
		A dictionary from `region.name` to the `MapRegion` object.
		"""
		super().__init__(regions=regions)

	def __and__(self, other: "MapRegions") -> Set[str]:
		return super().__and__(other)

	def __add__(self, other: "MapRegions") -> Set[str]:
		return super().__add__(other)

	def __sub__(self, other: "MapRegions") -> Set[str]:
		return super().__sub__(other)

	def __getitem__(self, regionName: str) -> MapRegion:
		return super().__getitem__(regionName)

	def addConnectedComponent(self, region: MapRegion) -> None:
		if region.regionType != MapRegion.RegionType.MAP: raise TypeError(f"Incorrect region type {region.regionType}")
		return super().addConnectedComponent(region)

	def intersection(self, other: "MapRegions") -> Set[str]:
		return super().intersection(other)

	def union(self, other: "MapRegions") -> Set[str]:
		return super().union(other)

	def difference(self, other: "MapRegions") -> Set[str]:
		return super().difference(other)
