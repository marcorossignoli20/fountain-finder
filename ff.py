import gpxpy
import osmnx as ox
import folium
from shapely.geometry import LineString, Point
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

FILE_PATH = './veneto_trail.gpx'

# Function to parse the GPX file and return the track points
def parse_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    track_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                track_points.append((point.latitude, point.longitude))
    
    return track_points

# Function to find public fountains along the track
def find_fountains(starting_track_points, search_radius=1000):
    # Convert track points to a LineString
    track_points = starting_track_points[::20]
    track_line = LineString([Point(lat, lon) for lat, lon in track_points])
    
    tags = {'amenity': 'drinking_water'}
    
    fountains_near_track = []

    def fetch_fountains(point):
        try:
            fountains = ox.features_from_point(point, tags, dist=1000)
            return fountains
        except ox._errors.InsufficientResponseError:
            return None
    
    with ThreadPoolExecutor(max_workers=1000) as executor:  # Adjust max_workers as needed
        futures = [executor.submit(fetch_fountains, point) for point in track_line.coords]
        
        for future in futures:
            result = future.result()
            if result is not None and not result.empty:
                for idx, row in result.iterrows():
                    if row.geometry.geom_type == 'Point':
                        fountains_near_track.append((row.geometry.x, row.geometry.y))

    # # Filter fountains within the search radius from the track
    # for idx, fountain in fountains.iterrows():
    #     if track_line.distance(fountain_point) <= search_radius:
    #         fountains_near_track.append(fountain_point)
    
    return fountains_near_track

# Function to plot the track and fountains on a map
def plot_map(track_points, fountains):
    # Create a map centered around the first track point
    track_map = folium.Map(location=track_points[0], zoom_start=14)
    
    # Add the GPX track to the map
    folium.PolyLine(track_points, color='blue', weight=2.5, opacity=1).add_to(track_map)
    
    # Add the fountains to the map
    for fountain in fountains:
        folium.Marker(
            location=[fountain[1], fountain[0]],
            icon=folium.Icon(color='green', icon='tint', prefix='fa')
        ).add_to(track_map)
    
    return track_map

# Main function to execute the script
def main(gpx_file):
    track_points = parse_gpx(gpx_file)
    fountains = find_fountains(track_points)
    
    print(f"Found {len(fountains)} public fountains along the track:")
    # print(fountains)
    # for fountain in fountains:
        # print(f"Fountain at: {fountain.y}, {fountain.x}")
    
    track_map = plot_map(track_points, fountains)

    track_map.save(FILE_PATH)
    print("Map has been saved to 'track_with_fountains.html'")

# Example usage
if __name__ == "__main__":
    main(FILE_PATH)