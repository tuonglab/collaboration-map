import pycountry
import pandas as pd
import folium
import numpy as np

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from math import radians, degrees, sin, cos, atan2, sqrt, asin
from pycountry_convert import country_alpha2_to_continent_code
from tqdm import tqdm


# Function to get continent from country
def get_continent(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        code = country.alpha_2
        continent_map = {
            "AF": "Africa",
            "AS": "Asia",
            "EU": "Europe",
            "NA": "North America",
            "SA": "South America",
            "OC": "Oceania",
        }
        cont_code = country_alpha2_to_continent_code(code)
        return continent_map.get(cont_code, "Other")
    except:
        return "Other"


def crosses_dateline(lon1, lon2):
    return abs(lon1 - lon2) > 180


def interpolate_arc(lat1, lon1, lat2, lon2, num_points=50):
    """Interpolates great-circle arc points between two coordinates."""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Compute angle between points
    delta = 2 * asin(
        sqrt(
            sin((lat2 - lat1) / 2) ** 2
            + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        )
    )

    if delta == 0:
        return [(degrees(lat1), degrees(lon1))] * num_points

    # Interpolate along the arc
    points = []
    for i in np.linspace(0, 1, num_points):
        A = sin((1 - i) * delta) / sin(delta)
        B = sin(i * delta) / sin(delta)

        x = A * cos(lat1) * cos(lon1) + B * cos(lat2) * cos(lon2)
        y = A * cos(lat1) * sin(lon1) + B * cos(lat2) * sin(lon2)
        z = A * sin(lat1) + B * sin(lat2)

        lat = atan2(z, sqrt(x**2 + y**2))
        lon = atan2(y, x)

        points.append(
            (degrees(lat), ((degrees(lon) + 540) % 360) - 180)
        )  # Ensures lon stays between -180 and 180

    return points


def main():
    # Load the SciVal export
    df = pd.read_csv("collab.csv")

    # Setup geocoder
    geolocator = Nominatim(user_agent="scival-map")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    # Initialize map and data holders
    locations = {}
    continent_colors = {
        "Europe": "blue",
        "Asia": "red",
        "North America": "green",
        "South America": "orange",
        "Africa": "purple",
        "Oceania": "cyan",
        "Other": "gray",
    }

    # Geocode institutions
    print("Geocoding institutions...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        inst = row["Institution"]
        country = row["Country/Region"]
        try:
            location = geocode(f"{inst}, {country}")
            if location:
                lat, lon = location.latitude, location.longitude
                continent = get_continent(country)
                locations[inst] = {
                    "lat": lat,
                    "lon": lon,
                    "country": country,
                    "continent": continent,
                    "publications": row["Co-authored publications"],
                }
        except Exception as e:
            print(f"Failed to geocode {inst}: {e}")

    # Create map centered roughly on home location
    home_location = [-27.4975, 153.0137]  # University of Queensland, St Lucia
    m = folium.Map(
        location=home_location,
        zoom_start=2,
        max_bounds=True,
        world_copy_jump=False,
        no_wrap=True,
    )

    # Add your node in the center (as the main author)
    folium.CircleMarker(
        location=home_location,
        radius=10,
        popup="You",
        color="black",
        fill=True,
        fill_opacity=0.9,
    ).add_to(m)

    # Add collaborators and lines
    for inst, data in locations.items():
        lat, lon = data["lat"], data["lon"]
        pub_count = data["publications"]
        continent = data["continent"]
        color = continent_colors.get(continent, "gray")
        # Node
        folium.CircleMarker(
            location=(lat, lon),
            radius=3 + pub_count / 3,
            popup=f"{inst} ({data['country']}) - {pub_count} papers",
            color=color,
            fill=True,
            fill_opacity=0.7,
        ).add_to(m)

        # Edge (line to your node)
        if crosses_dateline(home_location[1], lon):
            # Draw straight line instead of arc if crossing dateline
            folium.PolyLine(
                locations=[home_location, (lat, lon)],
                weight=1 + pub_count / 5,
                color="black",
                opacity=0.5,
            ).add_to(m)
        else:
            # Draw curved arc
            arc_points = interpolate_arc(
                home_location[0], home_location[1], lat, lon, num_points=50
            )
            folium.PolyLine(
                locations=arc_points,
                weight=1 + pub_count / 5,
                color="black",
                opacity=0.5,
            ).add_to(m)

    # Save the map
    m.save("scival_collaboration_map.html")
    print("Map saved as 'scival_collaboration_map.html'")


if __name__ == "__main__":
    # Display the map in a Jupyter Notebook
    main()
