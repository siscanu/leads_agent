"""
This module provides tools for searching business information using the Google Maps API.

Prerequisites:
- Set the environment variable `GOOGLE_MAPS_API_KEY` with your Google Maps API key.
  You can obtain the API key from the Google Cloud Console:
  https://console.cloud.google.com/projectselector2/google/maps-apis/credentials

- You also need to activate the Address Validation API for your .
  https://console.developers.google.com/apis/api/addressvalidation.googleapis.com

"""

import json
from datetime import datetime
from os import getenv
from typing import List, Optional

from agno.tools import Toolkit

try:
    import googlemaps
except ImportError:
    print("Error importing googlemaps. Please install the package using `pip install googlemaps`.")


class GoogleMapTools(Toolkit):
    def __init__(
        self,
        key: Optional[str] = None,
        search_places: bool = True,
        get_directions: bool = True,
        validate_address: bool = True,
        geocode_address: bool = True,
        reverse_geocode: bool = True,
        get_distance_matrix: bool = True,
        get_elevation: bool = True,
        get_timezone: bool = True,
    ):
        super().__init__(name="google_maps")

        api_key = key or getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is not set in the environment variables.")
        self.client = googlemaps.Client(key=api_key)

        if search_places:
            self.register(self.search_places)
        if get_directions:
            self.register(self.get_directions)
        if validate_address:
            self.register(self.validate_address)
        if geocode_address:
            self.register(self.geocode_address)
        if reverse_geocode:
            self.register(self.reverse_geocode)
        if get_distance_matrix:
            self.register(self.get_distance_matrix)
        if get_elevation:
            self.register(self.get_elevation)
        if get_timezone:
            self.register(self.get_timezone)

    def search_places(self, query: str) -> str:
        """
        Search for places using Google Maps Places API.
        This tool takes a search query and returns detailed place information.

        Args:
            query (str): The query string to search for using Google Maps Search API. (e.g., "dental clinics in Noida")

        Returns:
            Stringified list of dictionaries containing business information like name, address, phone, website, rating, and reviews etc.
        """
        try:
            # Perform places search
            places_result = self.client.places(query)

            if not places_result or "results" not in places_result:
                return str([])

            places = []
            for place in places_result["results"]:
                place_info = {
                    "name": place.get("name", ""),
                    "address": place.get("formatted_address", ""),
                    "rating": place.get("rating", 0.0),
                    "reviews": place.get("user_ratings_total", 0),
                    "place_id": place.get("place_id", ""),
                }

                # Get place details for additional information
                if place_info.get("place_id"):
                    try:
                        details = self.client.place(place_info["place_id"])
                        if details and "result" in details:
                            result = details["result"]
                            place_info.update(
                                {
                                    "phone": result.get("formatted_phone_number", ""),
                                    "website": result.get("website", ""),
                                    "hours": result.get("opening_hours", {}).get("weekday_text", []),
                                }
                            )
                    except Exception as e:
                        print(f"Error getting place details: {str(e)}")
                        # Continue with basic place info if details fetch fails

                places.append(place_info)

            return json.dumps(places)

        except Exception as e:
            print(f"Error searching Google Maps: {str(e)}")
            return str([])

    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving",
        departure_time: Optional[str] = None,
        avoid: Optional[List[str]] = None,
    ) -> str:
        """
        Get directions between two locations using Google Maps Directions API.

        Args:
            origin (str): Starting point address or coordinates
            destination (str): Destination address or coordinates
            mode (str, optional): Travel mode. Options: "driving", "walking", "bicycling", "transit". Defaults to "driving"
            departure_time (str, optional): Desired departure time for transit directions (ISO format datetime string)
            avoid (List[str], optional): Features to avoid: "tolls", "highways", "ferries"

        Returns:
            str: Stringified dictionary containing route information including steps, distance, duration, etc.
        """
        try:
            # Convert departure_time from string to datetime if provided
            departure_datetime = None
            if departure_time:
                try:
                    departure_datetime = datetime.fromisoformat(departure_time)
                except ValueError:
                    print(f"Invalid datetime format for departure_time: {departure_time}. Expected ISO format.")
            
            result = self.client.directions(origin, destination, mode=mode, departure_time=departure_datetime, avoid=avoid)
            return str(result)
        except Exception as e:
            print(f"Error getting directions: {str(e)}")
            return str([])

    def validate_address(
        self, address: str, region_code: str = "US", locality: Optional[str] = None, enable_usps_cass: bool = False
    ) -> str:
        """
        Validate an address using Google Maps Address Validation API.

        Args:
            address (str): The address to validate
            region_code (str): The region code (e.g., "US" for United States)
            locality (str, optional): The locality (city) to help with validation
            enable_usps_cass (bool): Whether to enable USPS CASS validation for US addresses

        Returns:
            str: Stringified dictionary containing address validation results
        """
        try:
            result = self.client.addressvalidation(
                [address], regionCode=region_code, locality=locality, enableUspsCass=enable_usps_cass
            )
            return str(result)
        except Exception as e:
            print(f"Error validating address: {str(e)}")
            return str({})

    def geocode_address(self, address: str, region: Optional[str] = None) -> str:
        """
        Convert an address into geographic coordinates using Google Maps Geocoding API.

        Args:
            address (str): The address to geocode
            region (str, optional): The region code to bias results

        Returns:
            str: Stringified list of dictionaries containing location information
        """
        try:
            result = self.client.geocode(address, region=region)
            return str(result)
        except Exception as e:
            print(f"Error geocoding address: {str(e)}")
            return str([])

    def reverse_geocode(
        self, lat: float, lng: float, result_type: Optional[List[str]] = None, location_type: Optional[List[str]] = None
    ) -> str:
        """
        Convert geographic coordinates into an address using Google Maps Reverse Geocoding API.

        Args:
            lat (float): Latitude
            lng (float): Longitude
            result_type (List[str], optional): Array of address types to filter results
            location_type (List[str], optional): Array of location types to filter results

        Returns:
            str: Stringified list of dictionaries containing address information
        """
        try:
            result = self.client.reverse_geocode((lat, lng), result_type=result_type, location_type=location_type)
            return str(result)
        except Exception as e:
            print(f"Error reverse geocoding: {str(e)}")
            return str([])

    def get_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving",
        departure_time: Optional[str] = None,
        avoid: Optional[List[str]] = None,
    ) -> str:
        """
        Calculate distance and time for a matrix of origins and destinations.

        Args:
            origins (List[str]): List of addresses or coordinates
            destinations (List[str]): List of addresses or coordinates
            mode (str, optional): Travel mode. Options: "driving", "walking", "bicycling", "transit"
            departure_time (str, optional): Desired departure time (ISO format datetime string)
            avoid (List[str], optional): Features to avoid: "tolls", "highways", "ferries"

        Returns:
            str: Stringified dictionary containing distance and duration information
        """
        try:
            # Convert departure_time from string to datetime if provided
            departure_datetime = None
            if departure_time:
                try:
                    departure_datetime = datetime.fromisoformat(departure_time)
                except ValueError:
                    print(f"Invalid datetime format for departure_time: {departure_time}. Expected ISO format.")
            
            result = self.client.distance_matrix(
                origins, destinations, mode=mode, departure_time=departure_datetime, avoid=avoid
            )
            return str(result)
        except Exception as e:
            print(f"Error getting distance matrix: {str(e)}")
            return str({})

    def get_elevation(self, lat: float, lng: float) -> str:
        """
        Get the elevation for a specific location using Google Maps Elevation API.

        Args:
            lat (float): Latitude
            lng (float): Longitude

        Returns:
            str: Stringified dictionary containing elevation data
        """
        try:
            result = self.client.elevation((lat, lng))
            return str(result)
        except Exception as e:
            print(f"Error getting elevation: {str(e)}")
            return str([])

    def get_timezone(self, lat: float, lng: float, timestamp: Optional[str] = None) -> str:
        """
        Get timezone information for a location using Google Maps Time Zone API.

        Args:
            lat (float): Latitude
            lng (float): Longitude
            timestamp (str, optional): The timestamp to use for timezone calculation (ISO format datetime string)

        Returns:
            str: Stringified dictionary containing timezone information
        """
        try:
            # Convert timestamp from string to datetime if provided
            timestamp_datetime = datetime.now()
            if timestamp:
                try:
                    timestamp_datetime = datetime.fromisoformat(timestamp)
                except ValueError:
                    print(f"Invalid datetime format for timestamp: {timestamp}. Expected ISO format. Using current time.")

            result = self.client.timezone(location=(lat, lng), timestamp=timestamp_datetime)
            return str(result)
        except Exception as e:
            print(f"Error getting timezone: {str(e)}")
            return str({})
