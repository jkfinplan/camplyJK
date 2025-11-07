"""
Search for Camava Providers
"""

import logging
from typing import Any, List, Optional, Union

from camply.containers import AvailableCampsite, SearchWindow
from camply.providers.camava import SantaBarbaraCountyParks
from camply.search.base_search import BaseCampingSearch
from camply.utils import make_list

logger = logging.getLogger(__name__)


class SearchSantaBarbaraCountyParks(BaseCampingSearch):
    """
    Campsite Search Object for Santa Barbara County Parks (Camava)
    
    Supports multiple parks - specify with campground_id:
    - Cachuma Lake: campground_id=1
    - Jalama Beach: campground_id=2
    """

    provider_class = SantaBarbaraCountyParks
    list_campsites_supported: bool = False

    def __init__(
        self,
        search_window: Union[SearchWindow, List[SearchWindow]],
        weekends_only: bool = False,
        campgrounds: Optional[Union[List[str], str]] = None,
        nights: int = 1,
        offline_search: bool = False,
        offline_search_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Initialize with Search Parameters

        Parameters
        ----------
        search_window: Union[SearchWindow, List[SearchWindow]]
            Search Window tuple containing start date and End Date
        weekends_only: bool
            Whether to only search for weekend availabilities
        campgrounds: Optional[Union[List[str], str]]
            Campground ID or List of Campground IDs (1=Cachuma, 2=Jalama)
        nights: int
            Minimum number of consecutive nights to search per campsite
        offline_search: bool
            Save and load campsite results
        offline_search_path: Optional[str]
            Path for offline search file
        """
        super().__init__(
            search_window=search_window,
            weekends_only=weekends_only,
            nights=nights,
            offline_search=offline_search,
            offline_search_path=offline_search_path,
            **kwargs,
        )
        self.campgrounds = make_list(campgrounds)

    def get_all_campsites(self) -> List[AvailableCampsite]:
        """
        Search for all matching campsites.

        Returns
        -------
        List[AvailableCampsite]
        """
        from datetime import datetime as dt
        
        all_campsites = []
        
        # Get campground IDs to search - use provided IDs or default
        campground_ids = self.campgrounds if self.campgrounds else [2]  # Default to Jalama
        
        # Search each campground for each date range
        for campground_id in campground_ids:
            for search_window in self.search_window:
                # Convert date to datetime
                start_date = dt.combine(search_window.start_date, dt.min.time())
                end_date = dt.combine(search_window.end_date, dt.min.time())
                
                try:
                    campsites = self.campsite_finder.get_campsites(
                        campground_id=int(campground_id),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    all_campsites.extend(campsites)
                except Exception as e:
                    logger.error(f"Error searching campground {campground_id}: {e}")
        
        return all_campsites

    def list_campsite_units(self) -> Any:
        """
        List Campsite Units

        Returns
        -------
        Any
        """
        raise NotImplementedError("Campsite unit listing not supported for Camava provider")
