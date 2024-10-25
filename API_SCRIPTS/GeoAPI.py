from Bot.Utils.logging_settings import geo_api_logger
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

async def check_geo(longitude: float, latitude: float):
    try:
        geolocator = Nominatim(user_agent="my_app")
        location = geolocator.geocode('Новослободская 17, Рязань, Россия')
        distance = geodesic((location.latitude, location.longitude), (latitude, longitude))
        if distance.meters <= 20:
            return True
        else:
            return False
    except Exception as _ex:
        geo_api_logger.error(f"Error check geo: {_ex}")
