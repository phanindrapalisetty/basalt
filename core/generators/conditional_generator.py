from core.spec_validator import SpecValidatorException


class MapGenerator:
    """Returns a mapped value based on the value of a dependency column."""

    def __init__(self, depends_on: str, map_dict: dict, default):
        self._depends_on = depends_on
        self._map = map_dict
        self._default = default

    def generate(self, row: dict):
        source = row.get(self._depends_on)
        if source is None:
            return self._default
        return self._map.get(str(source) if not isinstance(source, str) else source, self._default)


class RangeGenerator:
    """Returns a value based on which numeric range the dependency column falls into."""

    def __init__(self, depends_on: str, ranges: list, default):
        self._depends_on = depends_on
        self._ranges = ranges
        self._default = default

    def generate(self, row: dict):
        source = row.get(self._depends_on)
        if source is None:
            return self._default
        for r in self._ranges:
            lo = r.get("min")
            hi = r.get("max")
            if (lo is None or source >= lo) and (hi is None or source <= hi):
                return r["then"]
        return self._default
