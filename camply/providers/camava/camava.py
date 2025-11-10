"""
Camava Provider

Provider for Camava reservation system used by Santa Barbara County Parks.
"""

import logging
import re
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from camply.containers import AvailableCampsite, CampgroundFacility
from camply.exceptions import CamplyError
from camply.providers.base_provider import BaseProvider

logger = logging.getLogger(__name__)


class CamavaError(CamplyError):
    """
    Camava Provider Error
    """


class CamavaProvider(BaseProvider):
    """
    Camava Provider for ASP.NET-based reservation systems.
    
    Much simpler than previous Itinio system:
    - No AWS WAF
    - No login required
    - Simple HTTP POST requests
    - Returns only available sites
    """
    
    def __init__(self):
        """Initialize the provider with empty campground cache"""
        super().__init__()
        self._campground_cache = None
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the Camava system"""
        pass
    
    @property
    @abstractmethod
    def parent_id(self) -> int:
        """Parent ID for the park/facility"""
        pass
    
    @property
    @abstractmethod
    def park_name(self) -> str:
        """Name of the park"""
        pass
    
    @property
    def reservation_path(self) -> str:
        """Path to reservation page"""
        return "/reservation/camping/index.asp"
    
    def find_campgrounds(
        self,
        search_string: Optional[str] = None,
        **kwargs
    ) -> List[CampgroundFacility]:
        """
        Find campgrounds by scraping the Camava facility dropdown.
        
        Returns a list of all available campgrounds from the reservation page.
        """
        # Return cached results if available
        if self._campground_cache is not None:
            return self._campground_cache
        
        logger.info(f"Fetching available campgrounds from {self.base_url}")
        
        try:
            url = f"{self.base_url}{self.reservation_path}"
            resp = requests.get(url, timeout=30)
            
            if resp.status_code != 200:
                logger.error(f"Failed to fetch campgrounds: {resp.status_code}")
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find the parent_idno select dropdown
            parent_select = soup.find('select', {'name': 'parent_idno'})
            if not parent_select:
                logger.error("Could not find parent_idno dropdown on page")
                return []
            
            campgrounds = []
            options = parent_select.find_all('option')
            
            for option in options:
                facility_id = option.get('value', '').strip()
                facility_name = option.get_text().strip()
                
                # Skip empty options
                if not facility_id or not facility_name:
                    continue
                
                try:
                    facility_id_int = int(facility_id)
                    campground = CampgroundFacility(
                        facility_name=facility_name,
                        facility_id=facility_id_int,
                        recreation_area=self.park_name,
                        recreation_area_id=facility_id_int,
                    )
                    campgrounds.append(campground)
                    logger.info(f"  ⛰️  {facility_name} (ID: {facility_id_int})")
                except ValueError:
                    continue
            
            if not campgrounds:
                logger.warning("No campgrounds found on page")
            
            # Cache the results
            self._campground_cache = campgrounds
            
            return campgrounds
            
        except Exception as e:
            logger.error(f"Error fetching campgrounds: {e}")
            return []
    
    def get_campsites(
        self,
        campground_id: int,
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> List[AvailableCampsite]:
        """
        Get available campsites for the given date range.
        
        Parameters
        ----------
        campground_id : int
            The campground ID (parent_id)
        start_date : datetime
            Check-in date
        end_date : datetime
            Check-out date
            
        Returns
        -------
        List[AvailableCampsite]
            List of available campsites
        """
        # Get campground-specific name if available
        campground_name = self._get_campground_name(campground_id)
        
        logger.info(f"🏕️  Searching {campground_name}")
        logger.info(f"   Dates: {start_date.date()} to {end_date.date()}")
        
        # Get HTML response with available sites
        html_response = self._get_availability_html(campground_id, start_date, end_date)
        
        # Parse the HTML for available sites
        campsites = self._parse_availability_html(
            html_response, campground_id, campground_name, start_date, end_date
        )
        
        logger.info(f"   ✓ Found {len(campsites)} available campsite(s)")
        return campsites
    
    def _get_campground_name(self, campground_id: int) -> str:
        """
        Get the campground name for a given ID by looking it up in the campground list.
        """
        # Fetch campgrounds if not already cached
        if self._campground_cache is None:
            self.find_campgrounds()
        
        # Look up the campground name from cache
        if self._campground_cache:
            for campground in self._campground_cache:
                if campground.facility_id == campground_id:
                    return campground.facility_name
        
        # Fallback to generic park name if not found
        return self.park_name
    
    def _get_availability_html(self, campground_id: int, start_date: datetime, end_date: datetime) -> str:
        """
        Get availability HTML from Camava system.
        
        Parameters
        ----------
        campground_id : int
            The campground/facility ID
        start_date : datetime
            Check-in date
        end_date : datetime
            Check-out date
            
        Returns
        -------
        str
            HTML response containing available sites
        """
        url = f"{self.base_url}{self.reservation_path}"
        
        # Create session and establish cookies
        session = requests.Session()
        
        # Initial GET to establish session
        logger.debug(f"Getting session from {url}")
        initial_resp = session.get(url, timeout=30)
        
        if initial_resp.status_code != 200:
            raise CamavaError(f"Failed to establish session: {initial_resp.status_code}")
        
        # Calculate reservation length
        res_length = (end_date - start_date).days
        
        # Prepare POST data
        data = {
            'reserve_type': 'camping',
            'parent_idno': str(campground_id),
            'arrive_date': start_date.strftime('%-m/%-d/%Y'),  # 1/10/2026 format
            'res_length': str(res_length),
            'depart_date': end_date.strftime('%m/%d/%Y'),  # 01/12/2026 format
            'rv_length': '0',
            'rv_width': '0',
            'site_type_idno': '',
            'max_consecutive_nights': '14',
            'min_consecutive_nights': '1',
        }
        
        # POST search request
        logger.debug(f"Posting search to {url}")
        search_resp = session.post(url, data=data, timeout=30)
        
        if search_resp.status_code != 200:
            raise CamavaError(f"Search request failed: {search_resp.status_code}")
        
        logger.debug(f"Got response: {len(search_resp.text)} chars")
        return search_resp.text
    
    def _parse_availability_html(
        self,
        html: str,
        campground_id: int,
        campground_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[AvailableCampsite]:
        """
        Parse HTML response for available campsites.
        
        Camava returns only available sites in the response, making parsing simple.
        Each site is in a div with data-id attribute.
        
        Parameters
        ----------
        html : str
            HTML response from search
        campground_id : int
            The campground/facility ID
        campground_name : str
            The campground/facility name
        start_date : datetime
            Check-in date
        end_date : datetime
            Check-out date
            
        Returns
        -------
        List[AvailableCampsite]
            List of available campsites
        """
        soup = BeautifulSoup(html, 'html.parser')
        campsites = []
        
        # Find all site containers with data-id
        site_divs = soup.find_all('div', {'data-id': True})
        
        if not site_divs:
            logger.info("   No available sites found for these dates")
            return []
        
        # Track unique sites (may appear multiple times in HTML)
        seen_sites = set()
        
        for div in site_divs:
            site_id = div.get('data-id')
            
            # Skip if we've already processed this site
            if site_id in seen_sites:
                continue
            seen_sites.add(site_id)
            
            # Extract site information
            site_info = self._extract_site_info(
                div, site_id, campground_id, campground_name, start_date, end_date
            )
            
            if site_info:
                campsites.append(site_info)
        
        return campsites
    
    def _extract_site_info(
        self,
        div,
        site_id: str,
        campground_id: int,
        campground_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[AvailableCampsite]:
        """
        Extract campsite information from a site div.
        
        Parameters
        ----------
        div : BeautifulSoup element
            The div containing site information
        site_id : str
            The site ID
        campground_id : int
            The campground/facility ID
        campground_name : str
            The campground/facility name
        start_date : datetime
            Check-in date
        end_date : datetime
            Check-out date
            
        Returns
        -------
        Optional[AvailableCampsite]
            Campsite information or None if extraction fails
        """
        try:
            # Get site text content
            text = div.get_text()
            
            # Extract site name/number
            site_match = re.search(r'Site\s+(\d+[A-Z]?)', text, re.IGNORECASE)
            if site_match:
                site_name = f"Site {site_match.group(1)}"
            else:
                site_name = f"Site {site_id}"
            
            # Extract price
            price_match = re.search(r'Use Fee:\s*\$(\d+(?:\.\d{2})?)', text)
            price = float(price_match.group(1)) if price_match else 0.0
            
            # Extract occupancy (max people)
            occupancy_match = re.search(r'Persons:\s*(\d+)', text)
            occupancy = int(occupancy_match.group(1)) if occupancy_match else 1
            
            # Extract site type
            site_type = "Standard"
            if 'RV' in text or 'rv' in text.lower():
                site_type = "RV"
            elif 'tent' in text.lower():
                site_type = "Tent"
            elif 'group' in text.lower():
                site_type = "Group"
            
            # Get coordinates if available
            lat = div.get('data-lat')
            lng = div.get('data-lng')
            location = None
            if lat and lng:
                try:
                    from camply.containers.data_containers import CampsiteLocation
                    location = CampsiteLocation(
                        latitude=float(lat),
                        longitude=float(lng)
                    )
                except:
                    pass
            
            # Create booking URL (Camava doesn't support direct site links)
            booking_url = f"{self.base_url}{self.reservation_path}"
            
            # Create campsite object
            campsite = AvailableCampsite(
                campsite_id=int(site_id),
                booking_date=start_date,
                booking_end_date=end_date,
                booking_nights=(end_date - start_date).days,
                campsite_site_name=site_name,
                campsite_loop_name=campground_name,
                campsite_type=site_type,
                campsite_occupancy=(occupancy, occupancy),
                campsite_use_type="Overnight",
                availability_status="Available",
                recreation_area=campground_name,
                recreation_area_id=campground_id,
                facility_name=campground_name,
                facility_id=campground_id,
                booking_url=booking_url,
                location=location,
            )
            
            return campsite
            
        except Exception as e:
            logger.warning(f"Error extracting site {site_id}: {e}")
            return None

