import requests
from typing import Optional
from ...utils import logger

def geocode(location:str):

    """
    Function for geocoding from natural naming to coordinates.
    Args:
        - location: location in natural languages as a plain text
    Returns:
        - coordinates of object as a dict {'lat':latitude, 'lon':longitude}
    """
    
    nomimatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q':location,
        'format':'json',
        'limit':1, 
        'addresdetails':0
    }

    resp: Optional[requests.Response] = None

    try:
        resp = requests.get(nomimatim_url, params=params, headers={"User-Agent":"mock@gmail.com"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data or len(data) == 0: 
            logger.warning(f'[Geocoding] POI is not found {location}')
            return None
        
        result = data[0]
        coords = {
            'lat':float(result['lat']),
            'lon':float(result['lon'])
        }

        return coords
    
    except requests.exceptions.Timeout:
        logger.error(f'[Geocoding] Timeout for request: {location}')
        return None
    
    except requests.exceptions.HTTPError as e:
        assert resp is not None

        if resp.status_code == 429:
            logger.error('[Geocoding] Превышен лимит запросов к Nominatim!')
        else:
            logger.error(f'[Geocoding] HTTP error {resp.status_code}: {e}')
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f'[Geocoding] Network error: {e}')
        return None
    
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f'[Geocoding] An error occured while response parsing: {e}')
        return None

