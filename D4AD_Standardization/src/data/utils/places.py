import os
import googlemaps
from googlemaps.types import GeneratorType
import googlemaps import responses

ENV_GOOGLE_MAP_API_KEY = "GOOGLE_API_KEY"
class Gmap(object):
    # see: types, https://developers.google.com/places/supported_types:
    # see: https://developers.google.com/places/web-service/details
    def __init__(self, address=True, name=True, url=True, place_types=['school','university']):
        self.api_url = "https://maps.googleapis.com/maps/api/place/details/
        self.key = os.environ.get("ENV_GOOGLE_MAP_API_KEY")
        self.client = googlemaps.Client(self.key)
        self.place_types = place_types # I assume multiple can be used

        self.language = "en-US"
        self.region = "US"
        self.radius = 100

        # I don't think we'll actually use this
        self.ask_for_address = address
        self.ask_for_name = name
        self.ask_for_url = url

    @responses.activate
    def lookup(address=None, Name=None, URL=None):

        proceed = True
        if not (address and self.ask_for_address):
            proceed = False
        if not (name and self.ask_for_name):
            proceed = False
        if not (name and self.ask_for_url):
            proceed = False

        if proceed:
            # for each type make a query? Too expensive? Maybe if nothing found?
            request = {

            }
            responses.add(
                responses.GET,
                self.api_url,
                body='{"status": "OK", "candidates": []}',
                status=200,
                content_type="application/json",
            )

            for place_type in self.place_types:
                self.client.find_place(
                    "restaurant",
                    "textquery",
                    fields=["business_status", "geometry/location", "place_id"],
                    location_bias="point:90,90",
                    language=self.language,
                )

            # TODO: see place detail call
            # https://github.com/googlemaps/google-maps-services-python/blob/5fd6f0e962a2afbff4e6190e4ae91841b756ff4f/tests/test_places.py
            # TODO: see https://github.com/googlemaps/google-maps-services-python/blob/c875f3561c040c9b16c2d5c2b58d75cb0a7793cf/tests/test_client.py
            # check that response is had

                if len(response):
                    break

            # TODO: break out response
            # ntoe that client has callbacks, rate limiting
