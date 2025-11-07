"""
Camava Provider Variations

Specific implementations for parks using the Camava system.
"""

from camply.providers.camava.camava import CamavaProvider


class SantaBarbaraCountyParks(CamavaProvider):
    """
    Santa Barbara County Parks (Camava)
    
    Supports multiple parks in Santa Barbara County, California.
    Uses the Camava reservation system starting January 1, 2026.
    
    Parks:
    - Cachuma Lake (campground_id=1)
    - Jalama Beach (campground_id=2)
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> from camply.providers.camava import SantaBarbaraCountyParks
        >>> 
        >>> provider = SantaBarbaraCountyParks()
        >>> start = datetime.now() + timedelta(days=14)
        >>> end = start + timedelta(days=2)
        >>> 
        >>> # Search Jalama Beach
        >>> campsites = provider.get_campsites(
        ...     campground_id=2,
        ...     start_date=start,
        ...     end_date=end
        ... )
        >>> 
        >>> # Search Cachuma Lake
        >>> campsites = provider.get_campsites(
        ...     campground_id=1,
        ...     start_date=start,
        ...     end_date=end
        ... )
    """
    
    base_url = "https://santabarbara.camava.com"
    parent_id = 2  # Default to Jalama Beach
    park_name = "Santa Barbara County Parks"
    state_code = "CA"

