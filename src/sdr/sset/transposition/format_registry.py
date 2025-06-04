#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#

from typing import Callable, Dict, Optional, Any
from collections import OrderedDict
import numpy as np
import csv
from PIL import Image
from scipy.io import wavfile


class DataFormat:
    def __init__(
        self,
        name: str,
        mime_type: str,
        extension: str,
        reader: Optional[Callable[..., np.ndarray]] = None,
        writer: Optional[Callable[..., Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.mime_type = mime_type
        self.extension = extension
        self.reader = reader
        self.writer = writer
        self.options = options or {}

    def read(self, file_path: str) -> np.ndarray:
        if not self.reader:
            raise NotImplementedError(f"No reader implemented for {self.name}")
        return self.reader(file_path, **self.options)

    def write(self, file_path: str, array: np.ndarray):
        if not self.writer:
            raise NotImplementedError(f"No writer implemented for {self.name}")
        return self.writer(file_path, array, **self.options)

# === Reader/Writer Implementations ===

def csv_reader(file_path: str, **kwargs) -> np.ndarray:
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [list(map(float, row)) for row in reader]
    return np.array(data)

def csv_writer(file_path: str, array: np.ndarray, **kwargs):
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for row in array:
            writer.writerow(row)
    return True

def jpeg_reader(file_path: str, **kwargs) -> np.ndarray:
    img = Image.open(file_path).convert("RGB")
    return np.array(img)

def jpeg_writer(file_path: str, array: np.ndarray, **kwargs):
    img = Image.fromarray(array.astype('uint8'))
    img.save(file_path, format='JPEG')
    return True

def wav_reader(file_path: str, **kwargs) -> np.ndarray:
    rate, data = wavfile.read(file_path)
    return data.astype(np.float32) / np.iinfo(data.dtype).max

def wav_writer(file_path: str, array: np.ndarray, **kwargs):
    rate = kwargs.get("rate", 44100)
    scaled = (array * 32767).astype(np.int16)
    wavfile.write(file_path, rate, scaled)
    return True

# === Domain Constructor ===

def make_format_domain(entries: Dict[str, Dict[str, str]]) -> Dict[str, DataFormat]:
    return {
        name: DataFormat(
            name,
            entry["mime"],
            entry["ext"]
        ) for name, entry in entries.items()
    }

# === Format Domains ===

raster_formats = make_format_domain(OrderedDict({
    "jpeg": {"mime": "image/jpeg", "ext": ".jpg"},
    "tiff": {"mime": "image/tiff", "ext": ".tiff"},
}))

vector_formats = make_format_domain(OrderedDict({
    "svg": {"mime": "image/svg+xml", "ext": ".svg"},
    "ol_vector": {"mime": "application/json", "ext": ".geojson"},
}))

audio_formats = make_format_domain(OrderedDict({
    "wav": {"mime": "audio/wav", "ext": ".wav"},
}))

scientific_formats = make_format_domain(OrderedDict({
    "hd5": {"mime": "application/x-hdf5", "ext": ".h5"},
    "netcdf": {"mime": "application/x-netcdf", "ext": ".nc"},
}))

textual_formats = make_format_domain(OrderedDict({
    "csv": {"mime": "text/csv", "ext": ".csv"},
    "tsv": {"mime": "text/tab-separated-values", "ext": ".tsv"},
    "json": {"mime": "application/json", "ext": ".json"},
}))

# Assign real reader/writer functions
textual_formats["csv"].reader = csv_reader
textual_formats["csv"].writer = csv_writer

raster_formats["jpeg"].reader = jpeg_reader
raster_formats["jpeg"].writer = jpeg_writer

audio_formats["wav"].reader = wav_reader
audio_formats["wav"].writer = wav_writer

# === Unified Registry ===

format_registry: Dict[str, Dict[str, DataFormat]] = OrderedDict({
    "raster": raster_formats,
    "vector": vector_formats,
    "audio": audio_formats,
    "scientific": scientific_formats,
    "textual": textual_formats,
})

def list_available_formats():
    for domain, formats in format_registry.items():
        print(f"\n[DOMAIN] {domain.upper()}")
        for name, fmt in formats.items():
            print(f" - {name} ({fmt.mime_type}) -> {fmt.extension}")
