from core.spec_validator import SpecValidatorException
from core.random_context import RandomContext


class MapGenerator:
    """Returns a mapped value based on the value of a dependency column.

    Each entry in `map_dict` is either:
      - a scalar: every row with that key gets exactly that value
      - a {"values": [...], "distribution": [...]}: rows with that key get one
        of `values`, sampled so the ratio is realized exactly within the group.
        `group_sizes` (key -> row count for that key, precomputed from the
        dependency column's own distribution) is required to build these.
    """

    def __init__(
        self,
        depends_on: str,
        map_dict: dict,
        default,
        group_sizes: dict | None = None,
        column_name: str = "",
        rc: RandomContext | None = None,
    ):
        self._depends_on = depends_on
        self._map = map_dict
        self._default = default
        self._sequences = {}
        self._indices = {}

        if group_sizes is not None:
            local_rng = rc.sub_rng(column_name)
            for key, group in map_dict.items():
                if not isinstance(group, dict):
                    continue
                size = group_sizes.get(key, 0)
                values = group["values"]
                distribution = group["distribution"]

                seq = []
                for v, p in zip(values, distribution):
                    seq += [v] * int(size * p)
                local_rng.shuffle(seq)

                self._sequences[key] = seq
                self._indices[key] = 0

    def generate(self, row: dict):
        source = row.get(self._depends_on)
        if source is None:
            return self._default
        key = str(source) if not isinstance(source, str) else source

        if key in self._sequences:
            idx = self._indices[key]
            self._indices[key] += 1
            return self._sequences[key][idx]

        return self._map.get(key, self._default)


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
