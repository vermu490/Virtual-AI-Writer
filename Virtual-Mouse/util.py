from typing import List
from mediapipe.framework.formats import landmark_pb2

def get_distance(landmark_list: List[landmark_pb2.NormalizedLandmark]) -> float:
    """Calculate the Euclidean distance between the first two points in the landmark list.
    
    Args:
        landmark_list: A list of NormalizedLandmark objects.
    
    Returns:
        The Euclidean distance between the first two points, scaled appropriately.
    """
    if len(landmark_list) < 2:
        return 0.0  # Not enough points to calculate distance

    # Extract x and y coordinates from the NormalizedLandmark objects
    x1, y1 = landmark_list[0].x, landmark_list[0].y
    x2, y2 = landmark_list[1].x, landmark_list[1].y

    # Calculate Euclidean distance
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    # Return the distance (you can add scaling logic here if necessary)
    return distance
