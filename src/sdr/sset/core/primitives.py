#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#

### signal_semiotics_toolkit/core/primitives.py

from typing import Optional, Dict, Any, Tuple, Union, List
import numpy as np


class Emitter:

    def __init__(self,
                 id: str,
                 description: str,
                 platform_type: str,
                 known_bias: Optional[Dict[str, Any]] = None):
        self.id = id
        self.description = description
        self.platform_type = platform_type
        self.known_bias = known_bias or {}

    def get_id(self) -> str:
        return self.id
    
    def get_description(self) -> str:
        return self.description

    def set_description(self, description:str):
        self.description = description
    
    def get_platform_type(self) -> str:
        return self.platform_type

    def set_platform_type(self, platform_type: str):
        self.platform_type = platform_type
    
    def get_known_bias(self) -> Optional[Dict[str, Any]]:
        return self.known_bias

    def set_known_bias(self, known_bias: Optional[Dict[str, Any]]):
        self.known_bias = known_bias

    def get_known_bias_by_key(self, meta_key: str):
        return self.known_bias[meta_key]

    def set_known_bias_by_key(self, meta_key: str, meta_val):
        self.known_bias[meta_key] = meta_val

    def __eq__(self, other):
        return ((self.id == other.id) and
                (self.platform_type == other.platform_type)
        )


class EMField:

    def __init__(
        self,
        timestamp: float,
        location: Tuple[float, float, Optional[float]],
        domain: str,  # associative key to ?
        data: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.timestamp = timestamp
        self.location = location                # lat, lon, optional altitude.
        self.domain = domain                    # 'time', 'frequency', 'spatial', 'symbolic'
        self.data = data
        self.metadata = metadata or {}

    def get_timestamp(self) -> float:
        return self.timestamp

    def get_location(self) -> Tuple[float, float, Optional[float]]:
        return self.location

    def get_lat_lon(self) -> Tuple[float, float]:
        return self.location[0], self.location[1]

    def get_altitude(self) -> Optional[float]:
        return self.location[2] if self.location[2] else None

    def get_domain(self) -> str:
        return self.domain

    def get_data(self) -> np.ndarray:
        return self.data

    def set_data(self, data: np.ndarray):
        self.data = data

    def get_metadata(self) -> Optional[Dict[str, Any]]:
        return self.metadata

    def set_metadata(self, metadata: Optional[Dict[str, Any]]):
        self.metadata = metadata

    def get_metadata_value_by_key(self, meta_key: str):
        return self.metadata[meta_key]

    def set_metadata_value_by_key(self, meta_key: str, meta_val):
        self.metadata[meta_key] = meta_val

    def __eq__(self, other):
        return (self.timestamp == other.timestamp and
                self.location == other.location and
                self.domain == other.domain)



class SignalEvent(EMField):
    # add methods for location lat, lon & geohash
    def __init__(
        self,
        timestamp: float,
        location: Tuple[float, float, Optional[float]],
        domain: str,  # associative fk to an EMField
        data: np.ndarray,
        duration: float,
        carrier_freq: float,  # the signal component
        bandwidth: float,
        emitter: Optional[Emitter] = None,  # has a bias
        modulation: Optional[str] = None,  # variance,
        snr: Optional[float] = None,  # ...and noise
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(timestamp, location, domain, data, metadata)
        self.duration = duration
        self.carrier_freq = carrier_freq
        self.bandwidth = bandwidth
        self.emitter = emitter
        self.modulation = modulation
        self.snr = snr

    def get_duration(self) -> float:
        # calculate and set this from self.timestamp
        return self.duration

    def get_carrier_freq(self) -> float:
        return self.carrier_freq

    def get_bandwidth(self) -> float:
        return self.bandwidth

    def set_emitter(self, emitter: Emitter):
        self.emitter = emitter

    def set_emitters(self, emitters: List[Emitter]):
        """ set emitter with a filtered list of [Emitter] """
        self.emitter = [e for e in emitters if type(e) is Emitter]

    def get_emitter(self) -> Optional[Emitter]:
        return self.emitter

    def get_modulation(self) -> Optional[str]:
        return self.modulation

    def get_snr(self) ->Optional[float]:
        return self.snr

    def __eq__(self, other):
        return (
            isinstance(other, SignalEvent)
            and super().__eq__(other)
            and self.carrier_freq == other.carrier_freq
        )


class SignalMessage(SignalEvent):
    # add methods for location lat, lon & geohash
    def __init__(
        self,
        timestamp: float,
        location: Tuple[float, float, Optional[float]],
        domain: str,  # associative fk to a SignalEvent
        data: np.ndarray,
        duration: float,
        carrier_freq: float,  # the signal
        bandwidth: float,
        decoded: Optional[Union[str, bytes, Dict]] = None,
        semantics: Optional[str] = None,
        emitter: Optional[Emitter] = None,  # has bias
        modulation: Optional[str] = None,  # variance,
        snr: Optional[float] = None,  # ... and noise
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(timestamp, location, domain, data, duration, carrier_freq, bandwidth, emitter, modulation, snr, metadata)
        self.decoded = decoded
        self.semantics = semantics

    def get_decoded(self) -> Optional[Union[str, bytes, Dict]]:
        return self.decoded

    def set_decoded(self, decoded: Optional[Union[str, bytes, Dict]]):
        self.decoded = decoded

    def get_semantics(self) -> Optional[str]:
        return self.semantics

    def set_semantics(self, semantics: Optional[str]):
        self.semantics = semantics

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __eq__(self, other):
        return (
            isinstance(other, SignalMessage)
            and super().__eq__(other)
            and self.semantics == other.semantics
        )

