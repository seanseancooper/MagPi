#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#
# signal_semiotics_toolkit/core/signal_collections.py

from .primitives import Emitter, EMField, SignalEvent, SignalMessage
from .signal_model import SignalFrame
from .time_frequency_frame import TimeFrequencyFrame
from typing import Any, Optional, Generic, TypeVar, List, Dict, Callable
import re

T = TypeVar("T")


class SignalCollection(Generic[T]):

    def __init__(self, items: List[T]):
        self.items = items

    def filter_by_time(self, start: float, end: float) -> List[T]:
        """Return items within [start, end] timestamp range."""
        return [i for i in self.items if hasattr(i, "timestamp") and start <= i.timestamp <= end]

    def sort_by_time(self):
        """Sort items in-place by timestamp, if available."""
        self.items.sort(key=lambda x: getattr(x, "timestamp", float('inf')))

    def mapped(self, func: Callable[[T], T]) -> 'SignalCollection[T]':
        """Apply mutation function to each element."""
        return SignalCollection([func(item) for item in self.items])

    # verify this; I want this to behave as a List.
    def append(self, item):
        self.items.append(item)

    def __getitem__(self, index):
        return self.items[index]

    def __iter__(self):
        return iter(self.items)


class SignalFrameList(SignalCollection[SignalFrame]):
    def group_to_time_domain(self):
        return SignalFrameList([f.to_time_domain() for f in self.items if f.domain == "frequency"])

    def group_to_frequency_domain(self):
        return SignalFrameList([f.to_frequency_domain() for f in self.items if f.domain == "time"])

    def select_range(self, start: float, end: float) -> List[SignalFrame]:
        return [f for f in self.items if start <= f.timestamp <= end]


class TimeFrequencyFrameList(SignalCollection[TimeFrequencyFrame]):
    def group_slice_time(self, start, end):
        return TimeFrequencyFrameList([item.slice_time(start, end) for item in self.items if item.domain == "frequency"])

    def group_slice_frequency(self, f_start, f_end):
        return TimeFrequencyFrameList([item.slice_frequency(f_start, f_end) for item in self.items if item.domain == "time"])


class EmitterGroup:
    def __init__(self, emitters: Dict[str, Emitter]):
        self.emitters = emitters

    def get_emitter(self, _id: str) -> Optional[Emitter]:
        return self.emitters.get(_id)

    def get_emitters_by_platform_type(self, platform_type: str) -> List[Emitter]:
        return [em for em in self.emitters.values() if em.platform_type == platform_type]

    def compare_biases(
        self,
        x_biases: Optional[Dict[str, Any]],
        y_biases: Optional[Dict[str, Any]]
    ) -> int:
        """Return number of key-value pairs shared between two known_bias dictionaries."""
        if not x_biases or not y_biases:
            return 0
        return sum(1 for k in x_biases if k in y_biases and x_biases[k] == y_biases[k])

    def merge_biases(self, new_biases: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine all known_bias dictionaries from emitters and update with new_biases."""
        all_biases = {}
        for emitter in self.emitters.values():
            if emitter.known_bias:
                all_biases.update(emitter.known_bias)
        if new_biases:
            all_biases.update(new_biases)
        return all_biases

    def search_description(self, query: str) -> List[str]:
        """Return emitter IDs where the description matches the regex query."""
        pattern = re.compile(query, re.IGNORECASE)
        return [em.id for em in self.emitters.values() if pattern.search(str(em.description))]

    def list_ids(self) -> List[str]:
        return list(self.emitters.keys())

    def list_descriptions(self) -> List[str]:
        return [str(em.description) for em in self.emitters.values()]


class EMFieldList(SignalCollection[EMField]):
    pass


class SignalEventList(SignalCollection[SignalEvent]):
    pass


class SignalMessageList(SignalCollection[SignalMessage]):
    pass
