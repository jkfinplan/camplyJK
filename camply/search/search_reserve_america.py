"""
Search: Oregon State Parks (Reserve America JSON API).
"""

import logging
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from camply.containers import AvailableCampsite, RecreationArea, SearchWindow
from camply.providers.reserve_america.oregon_state_parks_ra import OregonStateParksRA
from camply.search.base_search import BaseCampingSearch
from camply.utils import logging_utils, make_list
from camply.utils.logging_utils import format_log_string, log_sorted_response

logger = logging.getLogger(__name__)


class SearchOregonStateParksRA(BaseCampingSearch):
    """
    Oregon State Parks reservations on oregonstateparks.reserveamerica.com (contract OR).
    """

    provider_class = OregonStateParksRA
    list_campsites_supported: bool = False

    def __init__(
        self,
        search_window: Union[SearchWindow, List[SearchWindow]],
        recreation_area: List[int],
        weekends_only: bool = False,
        campgrounds: Optional[Union[List[str], str]] = None,
        nights: int = 1,
        **kwargs,
    ) -> None:
        super().__init__(
            search_window=search_window,
            weekends_only=weekends_only,
            nights=nights,
            **kwargs,
        )
        self._recreation_area_ids: List[int] = make_list(recreation_area, coerce=int)
        self._campground_ids: List[int] = make_list(campgrounds, coerce=int)
        campsites = make_list(kwargs.get("campsites", []), coerce=int) or []
        if len(campsites) > 0:
            logger.error(
                "%s does not support --campsite filtering yet",
                self.provider_class.__name__,
            )
            sys.exit(1)
        try:
            assert any(
                [
                    self._campground_ids not in (None, []),
                    self._recreation_area_ids not in (None, []),
                ]
            )
        except AssertionError:
            logger.error(
                "You must provide --campground or --rec-area for %s",
                self.provider_class.__name__,
            )
            sys.exit(1)
        if self._campground_ids:
            self.campgrounds = self.campsite_finder.find_campgrounds(
                campground_id=self._campground_ids,
                verbose=False,
            )
        else:
            self.campgrounds = self.campsite_finder.find_campgrounds(
                rec_area_id=self._recreation_area_ids,
                verbose=False,
            )
        self.campground_ids = [int(item.facility_id) for item in self.campgrounds]
        if len(self.campground_ids) == 0:
            logger.error("No campgrounds found matching your search criteria")
            sys.exit(1)
        if kwargs.get("equipment", ()):
            logger.warning(
                "%s does not support --equipment yet",
                self.provider_class.__name__,
            )

    def get_all_campsites(self, **kwargs: Dict) -> List[AvailableCampsite]:
        logger.info("Searching across %s campground(s)", len(self.campgrounds))
        for campground in self.campgrounds:
            logger.info("    %s", format_log_string(campground))
        campsites_found: List[AvailableCampsite] = []
        for month in self.search_months:
            month_days = sorted(
                {
                    d.date() if isinstance(d, datetime) else d
                    for d in self.search_days
                    if d.year == month.year and d.month == month.month
                }
            )
            if not month_days:
                continue
            range_start = month_days[0]
            range_end = month_days[-1]
            for campground in self.campgrounds:
                logger.info(
                    "Searching %s, %s (%s) for availability: %s",
                    campground.facility_name,
                    campground.recreation_area,
                    campground.facility_id,
                    month.strftime("%B, %Y"),
                )
                campsites = self.campsite_finder.get_campsites(
                    campground_id=int(campground.facility_id),
                    start_date=range_start,
                    end_date=range_end,
                    nights=self.nights,
                    facility_name=campground.facility_name,
                )
                logger.info(
                    "\t%s\t%s total sites found in month of %s",
                    logging_utils.get_emoji(campsites),
                    len(campsites),
                    month.strftime("%B"),
                )
                campsites_found += campsites
        campsite_df = self.campsites_to_df(campsites=campsites_found)
        campsite_df_validated = self._filter_date_overlap(campsites=campsite_df)
        consolidated_campsites = self._consolidate_campsites(
            campsite_df=campsite_df_validated, nights=self.nights
        )
        compiled_campsites = self.df_to_campsites(campsite_df=consolidated_campsites)
        return compiled_campsites

    def list_campsite_units(self) -> Any:
        """
        Not supported for Oregon State Parks (Reserve America) yet.
        """
        raise NotImplementedError(
            f"{self.provider_class.__name__} does not support list-campsites yet"
        )

    @classmethod
    def find_recreation_areas(
        cls, search_string: str, **kwargs
    ) -> List[RecreationArea]:
        rec_areas = cls.provider_class().search_for_recreation_areas(
            query=search_string, state=kwargs.get("state")
        )
        logger.info("%s Matching Recreation Areas Found", len(rec_areas))
        log_sorted_response(rec_areas)
        return rec_areas
