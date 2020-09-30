import requests
import ipyleaflet

"""Class for creating POI (point of interest) with its full detailed geographic data
"""

class poi:
    """Initialize the POI by specifying the name of the place
    and the country in which the place exist and its OpenStreetMaps types

    We are relying on Nominatim API to query the OSM data. The name of
    the place could be just the name of the place like University of Toronto.

    You need to specify the name of the country so we can limit the search space,
    and as you probably imagine the same name of one place points to different places
    in different countries. You can find "London" in UK and in USA.

    As we have discussed in GettingStarted repositories there are three types of entities
    in OSM data, which is nodes and ways and relations. Nodes are just a place like a certain
    hospital or shop and ways/relations are just a set of nodes that specify some poly[gon-line]
    in a map. When we query Nominatim API with a certain address, it replies back with nodes/ways/relations
    that match that address, so we need the parameter osm_type to retrieve the right type.

    Parameters
    ----------
    name: the name/address of the POI
    country: the name of the country of the POI
    osm_type: data types of OSM entities [node - way - relation]

    Examples
    -------
    >>> UofT = poi("university of toronto", "canada")
    >>> UofT.coordinates
    ... (-79.3973638, 43.6620257)
    >>> UofT.address
    ... 'University of Toronto, St George Street, University—Rosedale, Old Toronto, Toronto, Peel, Golden Horseshoe, Ontario, M5T 2Z9, Canada'

    """
    def __init__(self, name, country, osm_type = "node"):
        self.__geo_decode(name, country, osm_type)

    """ Calls Nominatim API for geodecoding the address
    """

    def __geo_decode(self, name, country, osm_type):

        # check https://nominatim.org/release-docs/develop/

        response = requests.get(f'https://nominatim.openstreetmap.org/search?q={name} - {country}&format=geocodejson')

        if response.status_code != 200:
            raise ValueError("We couldn't decode the address, please make sure you entered it correctly")

        response_json = response.json()

        # the response may contain multiple places with
        # the same name, we will only take the first result
        # of the response which would be the place you desired
        # that is why we get the index zero from the response
        # IF and only if the place returned has the same type
        # that we want, which is usually node. Remember that we
        # have multiple types of data in osm format like node
        # and way and relation
        index = 0
        place = response_json['features'][index] 

        while place['properties']['geocoding']['osm_type'] != osm_type:
            index += 1
            try:
                place = response_json['features'][index]
            except:
                raise ValueError(f"We couldn't find places with the type {osm_type}")

        self.address = place['properties']['geocoding']['label']
        self.osmid = place['properties']['geocoding']['osm_id']
        self.coordinates = tuple(place['geometry']['coordinates']) # (longitude, latitude)

    """Takes another poi object and find the route between the calling object and 
    the other object with specified mode of transportation like car - bike - foot.
    Driving mode is equivalent to car mode. If there are not many available mode 
    for the specified route, the API returns the car/driving mode by default.

    Parameters
    ----------
    destination: another poi object that would be the target of the route
    mode: this is the mode of transportation, there are three available modes: car/driving - bike - foot

    Returns
    -------
    Route dictionary: dictionary that consists of three keys
                    1. 'route' which is the (lat, log) coordinates that defines the route
                    2. 'length' the length of the route by meters
                    3. 'duration' based on the speed limit of the route and its length and its is seconds
    """
    def route_to(self, destination, mode = "driving"):
        src = self.coordinates
        dest = destination.coordinates

        # check http://project-osrm.org/docs/v5.22.0/api/#general-options

        response = requests.get(f'http://router.project-osrm.org/route/v1/{mode}/{src[0]},{src[1]};{dest[0]},{dest[1]}?steps=true')
        response_json = response.json()

        if response_json['code'] != 'Ok':
            raise ValueError(f"OSRM couldn't find a route between {src} and {dest}")

        route = response_json["routes"][0]
        cost = route["distance"]
        duration = route["duration"]
        legs = route["legs"][0]
        steps = legs["steps"]

        route_coords = list()
        for route_step in steps:
            maneuver = route_step["maneuver"]
            location = maneuver["location"]
            location = location[::-1]   # from (longitude, latitude) to (latitude, longitude) so ipyleaflet can handle it
            route_coords.append(tuple(location))
        
        return {'route' : route_coords, 
                'length' : cost,
                'duration' : duration}
    
    def __eq__(self, other):
        return self.osmid == other.osmid

    def __hash__(self):
        return self.osmid


##########################################################################################################
##########################################################################################################
##########################################################################################################
##########################################################################################################


def 