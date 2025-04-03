from sklearn.preprocessing import MinMaxScaler
import numpy as np
import geohash
import cv2
import hashlib

# Version 1.0: Initial implementation of encoding length, width, height, and color histogram
# Version 1.1: Added geohashing for latitude and longitude
# Version 1.2: Replaced color strings with RGB tuples
# Version 1.3: Encoded latitude and longitude as a single compact string
# Version 1.4: Introduced hashing for color histogram
# Version 1.5: Added camera capture for extracting color histogram
# Version 1.6: Refactored into a class

class ObjectEncoder:
    def __init__(self, precision=12, bins=8):
        self.precision = precision
        self.bins = bins
        self.scaler = MinMaxScaler()

    def encode_lat_lon(self, latitude, longitude):
        """
        Encodes latitude and longitude using geohashing.
        """
        return geohash.encode(latitude, longitude, precision=self.precision)

    def extract_color_histogram_from_image(self, image):
        """
        Extracts an 8-bin color histogram from an image.
        """
        histogram = cv2.calcHist([image], [0, 1, 2], None, [self.bins, self.bins, self.bins], [0, 256, 0, 256, 0, 256])
        histogram = cv2.normalize(histogram, histogram).flatten()
        return histogram.tolist()

    def hash_color_histogram(self, histogram):
        """
        Hashes the color histogram using SHA-256.
        """
        histogram_str = ','.join(map(str, histogram))
        return hashlib.sha256(histogram_str.encode()).hexdigest()

    def capture_frame_from_camera(self):
        """
        Captures a frame from the default camera.
        """
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Could not open video device")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise Exception("Failed to capture image from camera")

        return frame

    def encode_features(self, objects, hash_histogram=False):
        """
        Encodes length, width, height, color histogram, and latitude/longitude as a geohash.
        """
        # Extract numerical features
        numerical_features = np.array([
            [obj['length'], obj['width'], obj['height']]
            for obj in objects
        ])

        # Normalize numerical features
        normalized_features = self.scaler.fit_transform(numerical_features)

        # Encode latitude and longitude using geohashing
        lat_lon_features = [self.encode_lat_lon(obj['latitude'], obj['longitude']) for obj in objects]

        # Capture frame and extract color histogram
        frame = self.capture_frame_from_camera()
        color_histogram = self.extract_color_histogram_from_image(frame)

        hashed_histogram = self.hash_color_histogram(color_histogram) if hash_histogram else None

        # Combine numerical, color histogram, hashed histogram, and lat/lon string features
        encoded_data = [list(features) + color_histogram + [hashed_histogram] + [lat_lon]
                        for features, lat_lon in zip(normalized_features, lat_lon_features)]

        return encoded_data

# Example usage
objects = [
    {'length': 5.2, 'width': 2.5, 'height': 1.8, 'latitude': 40.7128, 'longitude': -74.0060},
    {'length': 3.1, 'width': 1.2, 'height': 2.2, 'latitude': 34.0522, 'longitude': -118.2437},
    {'length': 4.3, 'width': 2.0, 'height': 1.5, 'latitude': 51.5074, 'longitude': -0.1278}
]

encoder = ObjectEncoder()
encoded_features = encoder.encode_features(objects, hash_histogram=True)
print("Encoded Features:")
for row in encoded_features:
    print(row)
