"""
Search for Camava Providers
"""

import logging
import re
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
        campsites: Optional[Union[List[str], str]] = None,
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
        campsites: Optional[Union[List[str], str]]
            Specific campsite numbers to search for (e.g., 47, 45)
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
        self.campsites = make_list(campsites) if campsites else None

    def get_all_campsites(self) -> List[AvailableCampsite]:
        """
        Search for all matching campsites.

        Returns
        -------
        List[AvailableCampsite]
        """
        from datetime import datetime as dt, timedelta
        
        all_campsites = []
        
        # Get campground IDs to search - use provided IDs or default
        campground_ids = self.campgrounds if self.campgrounds else [2]  # Default to Jalama
        
        # Get all search days from base class (handles weekends filtering)
        search_days = self._get_search_days()
        
        # If weekends_only and nights not explicitly set to 2, use 2 nights
        nights = self.nights if self.nights > 1 else (2 if self.weekends_only else 1)
        
        # For weekend searches, only search Friday nights (Friday + Saturday = weekend)
        # Filter out Saturday since that would give Sat-Mon which isn't a weekend
        if self.weekends_only:
            search_days = [day for day in search_days if day.weekday() == 4]  # Friday only
        
        logger.info(f"Searching {len(search_days)} days with {nights} night stays")
        
        # Search each campground for each search day
        for campground_id in campground_ids:
            for search_day in search_days:
                # Create datetime for start and end
                start_date = dt.combine(search_day, dt.min.time())
                end_date = start_date + timedelta(days=nights)
                
                logger.debug(f"Searching {search_day.strftime('%a %Y-%m-%d')} for {nights} nights")
                
                try:
                    campsites = self.campsite_finder.get_campsites(
                        campground_id=int(campground_id),
                        start_date=start_date,
                        end_date=end_date,
                    )
                    all_campsites.extend(campsites)
                except Exception as e:
                    logger.error(f"Error searching campground {campground_id}: {e}")
        
        # Filter by specific campsite numbers if provided
        if self.campsites:
            logger.info(f"Filtering to specific campsites: {', '.join(str(c) for c in self.campsites)}")
            filtered_campsites = []
            for campsite in all_campsites:
                # Extract site number from campsite_site_name (e.g., "Site 47" -> "47")
                site_match = re.search(r'Site\s+(\d+[A-Z]?)', campsite.campsite_site_name, re.IGNORECASE)
                if site_match:
                    site_number = site_match.group(1)
                    if site_number in self.campsites or str(site_number) in [str(c) for c in self.campsites]:
                        filtered_campsites.append(campsite)
            
            return filtered_campsites
        
        return all_campsites

    def list_campsite_units(self) -> Any:
        """
        List Campsite Units

        Returns
        -------
        Any
        """
        error_message = (
            "Campsite listing is not directly supported by the Camava provider.\n\n"
            "To see available campsites, run a search for a date range:\n\n"
            "  camply campsites \\\n"
            "    --provider SantaBarbaraCountyParks \\\n"
            "    --campground 2 \\\n"
            "    --start-date 2026-05-01 \\\n"
            "    --end-date 2026-05-03\n\n"
            "To search for a specific campsite number:\n\n"
            "  camply campsites \\\n"
            "    --provider SantaBarbaraCountyParks \\\n"
            "    --campground 2 \\\n"
            "    --campsite 47 \\\n"
            "    --start-date 2026-05-01 \\\n"
            "    --end-date 2026-05-03"
        )
        logger.error(error_message)
        raise NotImplementedError(error_message)
