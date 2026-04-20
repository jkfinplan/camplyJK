"""
Oregon State Parks on Reserve America (api.reserveamerica.com).

Bookable only for parks supported by the Reserve America app JSON API; see
https://github.com/juftin/camply/issues/321
"""

from __future__ import annotations

import logging
import re
import sys
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from camply.containers import AvailableCampsite, CampgroundFacility, RecreationArea
from camply.containers.data_containers import CampsiteLocation
from camply.exceptions import CamplyError
from camply.providers.base_provider import BaseProvider
from camply.providers.reserve_america.client import ReserveAmericaClient
from camply.utils.logging_utils import log_sorted_response

logger = logging.getLogger(__name__)

SEARCH_PATH = "/jaxrs-json/search"
BOOKING_WEB = "https://oregonstateparks.reserveamerica.com"


def _facility_path_slug(facility_name: str) -> Optional[str]:
    """
    Reserve America web URLs use a slug under /camping/<slug>/r/..., e.g. tumalo-state-park.
    Derived from the facility display name (same source as CLI/search), not the campsites API.
    """
    name = facility_name.strip()
    if re.fullmatch(r"(?i)facility\s+\d+", name):
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or None


class OregonStateParksRA(BaseProvider):
    """
    Oregon State Parks reservations hosted on ReserveAmerica.com (contract OR).
    """

    state_code = "OR"
    contract_code = "OR"

    def __init__(self) -> None:
        super().__init__()
        self._ra = ReserveAmericaClient()

    def _search_state_records(self, interest: str = "camping") -> List[Dict[str, Any]]:
        """
        Paginate /jaxrs-json/search for Oregon camping inventory.
        """
        params: Dict[str, Any] = {
            "stype": "state",
            "tstc": self.state_code,
            "rcp": 0,
            "interest": interest,
        }
        responses: List[Dict[str, Any]] = []
        while True:
            data = self._ra.get_json(SEARCH_PATH, params=params)
            responses.append(data)
            records = data.get("records") or []
            if not records:
                break
            control = data.get("control") or {}
            current_page = control.get("currentPage", params["rcp"])
            total_pages = data.get("totalPages", 1)
            if current_page >= total_pages - 1:
                break
            params["rcp"] = int(params["rcp"]) + 1
            time.sleep(0.25)

        merged: List[Dict[str, Any]] = []
        for chunk in responses:
            merged.extend(chunk.get("records") or [])
        return merged

    @staticmethod
    def _record_to_facility(rec: Dict[str, Any]) -> CampgroundFacility:
        details = rec.get("details") or {}
        fid = details.get("id") or rec.get("id")
        name = rec.get("name") or details.get("name") or "Unknown"
        coords = None
        c = details.get("coordinates")
        if isinstance(c, dict) and c.get("latitude") is not None:
            coords = (float(c["latitude"]), float(c["longitude"]))
        return CampgroundFacility(
            facility_name=name,
            recreation_area="Oregon State Parks",
            facility_id=int(fid),
            recreation_area_id=int(fid),
            map_id=None,
            coordinates=coords,
            contract_code=OregonStateParksRA.contract_code,
        )

    @staticmethod
    def _record_to_recreation_area(rec: Dict[str, Any]) -> RecreationArea:
        details = rec.get("details") or {}
        fid = details.get("id") or rec.get("id")
        name = rec.get("name") or details.get("name") or "Unknown"
        coords = None
        c = details.get("coordinates")
        if isinstance(c, dict) and c.get("latitude") is not None:
            coords = (float(c["latitude"]), float(c["longitude"]))
        desc = details.get("description")
        return RecreationArea(
            recreation_area=name,
            recreation_area_id=int(fid),
            recreation_area_location="OR, USA",
            coordinates=coords,
            description=desc,
        )

    def search_for_recreation_areas(
        self, query: Optional[str] = None, state: Optional[str] = None
    ) -> List[RecreationArea]:
        if state is not None and state.upper() != self.state_code:
            raise CamplyError(
                f"{self.__class__.__name__} only supports state={self.state_code}"
            )
        if not query:
            logger.error(
                "You must provide a search string to search Oregon State Parks "
                "recreation areas"
            )
            sys.exit(1)
        logger.info('Searching Oregon State Parks recreation areas for "%s"', query)
        records = self._search_state_records()
        q = query.lower()
        matches = [
            r
            for r in records
            if q in (r.get("name") or "").lower()
            or q in ((r.get("details") or {}).get("name") or "").lower()
        ]
        areas = [self._record_to_recreation_area(r) for r in matches]
        logger.info("%s Matching Recreation Areas Found", len(areas))
        log_sorted_response(areas)
        return areas

    def find_campgrounds(
        self,
        search_string: Optional[str] = None,
        rec_area_id: Optional[List[int]] = None,
        campground_id: Optional[List[int]] = None,
        campsite_id: Optional[List[int]] = None,
        state: Optional[str] = None,
        **kwargs: Any,
    ) -> List[CampgroundFacility]:
        if campsite_id not in (None, [], ()):
            logger.error("OregonStateParksRA does not support --campsite lookup yet")
            sys.exit(1)
        if state is not None and state.upper() != self.state_code:
            raise CamplyError(
                f"{self.__class__.__name__} only supports state={self.state_code}"
            )

        if (
            rec_area_id in (None, [])
            and campground_id in (None, [])
            and not search_string
        ):
            logger.error(
                "Provide --search, --rec-area, or --campground to search Oregon campgrounds"
            )
            sys.exit(1)

        records = self._search_state_records()
        by_id = {
            int((r.get("details") or {}).get("id") or r.get("id")): r for r in records
        }

        if campground_id:
            out: List[CampgroundFacility] = []
            for cid in campground_id:
                rec = by_id.get(int(cid))
                if rec is None:
                    logger.warning(
                        "Campground id %s not found in Oregon camping search index; "
                        "using id without metadata refresh",
                        cid,
                    )
                    out.append(
                        CampgroundFacility(
                            facility_name=f"Facility {cid}",
                            recreation_area="Oregon State Parks",
                            facility_id=int(cid),
                            recreation_area_id=int(cid),
                            map_id=None,
                            coordinates=None,
                            contract_code=self.contract_code,
                        )
                    )
                else:
                    out.append(self._record_to_facility(rec))
            logger.info("%s Matching Campgrounds Found", len(out))
            log_sorted_response(out)
            return out

        if rec_area_id:
            out = []
            for rid in rec_area_id:
                rec = by_id.get(int(rid))
                if rec is None:
                    logger.warning(
                        "Recreation area id %s not found in state listing", rid
                    )
                    out.append(
                        CampgroundFacility(
                            facility_name=f"Facility {rid}",
                            recreation_area="Oregon State Parks",
                            facility_id=int(rid),
                            recreation_area_id=int(rid),
                            map_id=None,
                            coordinates=None,
                            contract_code=self.contract_code,
                        )
                    )
                else:
                    out.append(self._record_to_facility(rec))
            logger.info("%s Matching Campgrounds Found", len(out))
            log_sorted_response(out)
            return out

        assert search_string
        q = search_string.lower()
        matches = [
            r
            for r in records
            if q in (r.get("name") or "").lower()
            or q in ((r.get("details") or {}).get("name") or "").lower()
        ]
        facilities = [self._record_to_facility(r) for r in matches]
        logger.info("%s Matching Campgrounds Found", len(facilities))
        log_sorted_response(facilities)
        return facilities

    def _booking_url(self, facility_id: int) -> str:
        return (
            f"{BOOKING_WEB}/camping/campgroundDetails.do"
            f"?contractCode={self.contract_code}&parkId={facility_id}"
        )

    @staticmethod
    def _numeric_site_id(rec: Dict[str, Any]) -> Optional[int]:
        """
        Reserve America JSON may expose siteId, productId, or id for the bookable unit.
        """
        for key in ("siteId", "productId", "id"):
            v = rec.get(key)
            if v is None:
                continue
            try:
                return int(v)
            except (TypeError, ValueError):
                continue
        return None

    def _booking_url_for_site(
        self, facility_id: int, rec: Dict[str, Any], facility_name: str
    ) -> str:
        """
        Per-site web URL: /camping/<park-slug>/r/campsiteDetails.do?contractCode&siteId&parkId.
        Slug is derived from facility_name (search/CLI), matching Oregon's Reserve America site.
        """
        sid = self._numeric_site_id(rec)
        if sid is None:
            return self._booking_url(facility_id)
        query = (
            f"?contractCode={self.contract_code}"
            f"&siteId={sid}&parkId={facility_id}"
        )
        slug = _facility_path_slug(facility_name)
        if slug:
            return f"{BOOKING_WEB}/camping/{slug}/r/campsiteDetails.do{query}"
        logger.warning(
            "Could not derive park URL slug from facility name %r; "
            "using campground listing instead of per-site page.",
            facility_name,
        )
        return self._booking_url(facility_id)

    def _fetch_campsite_records(
        self, facility_id: int, arrival: date, nights: int
    ) -> List[Dict[str, Any]]:
        params = {
            "displayGISMap": "false",
            "rcp": 0,
            "next": "true",
            "fc": "false",
            "arv": arrival.isoformat(),
            "lsy": str(nights),
        }
        all_rows: List[Dict[str, Any]] = []
        rcp = 0
        while True:
            params["rcp"] = rcp
            path = f"/jaxrs-json/products/{self.contract_code}/{facility_id}/campsites"
            data = self._ra.get_json(path, params=params)
            rows = data.get("records") or []
            all_rows.extend(rows)
            control = data.get("control") or {}
            current_page = control.get("currentPage", rcp)
            total_pages = data.get("totalPages", 1)
            if not rows or current_page >= total_pages - 1:
                break
            rcp += 1
            time.sleep(0.15)
        return all_rows

    def get_campsites(
        self,
        campground_id: int,
        start_date: Union[datetime, date],
        end_date: Union[datetime, date],
        nights: int = 1,
        **kwargs: Any,
    ) -> List[AvailableCampsite]:
        """
        Availability for each night in [start_date, end_date] (month slice from search).
        """
        facility_label = kwargs.get("facility_name") or f"Facility {campground_id}"
        start = start_date.date() if isinstance(start_date, datetime) else start_date
        end = end_date.date() if isinstance(end_date, datetime) else end_date
        if end < start:
            return []

        found: List[AvailableCampsite] = []
        d = start
        while d <= end:
            rows = self._fetch_campsite_records(
                facility_id=int(campground_id), arrival=d, nights=nights
            )
            for rec in rows:
                site_name = str(rec.get("name") or rec.get("siteName") or "Site")
                numeric_site = self._numeric_site_id(rec)
                site_id: Union[int, str] = (
                    numeric_site
                    if numeric_site is not None
                    else rec.get("productId", rec.get("id", site_name))
                )
                loop = rec.get("loop") or rec.get("loopName")
                site_type = (
                    rec.get("siteType") or rec.get("productTypeName") or "Camping"
                )
                for cell in rec.get("availabilityGrid") or []:
                    if str(cell.get("date")) != d.isoformat():
                        continue
                    status = (cell.get("status") or "").upper()
                    if status != "AVAILABLE":
                        continue
                    start_dt = datetime.combine(d, datetime.min.time())
                    end_dt = start_dt + timedelta(days=nights)
                    loc = None
                    lat = rec.get("latitude")
                    lon = rec.get("longitude")
                    if lat is not None and lon is not None:
                        loc = CampsiteLocation(
                            latitude=float(lat), longitude=float(lon)
                        )
                    found.append(
                        AvailableCampsite(
                            campsite_id=site_id,
                            booking_date=start_dt,
                            booking_end_date=end_dt,
                            booking_nights=nights,
                            campsite_site_name=site_name,
                            campsite_loop_name=loop,
                            campsite_type=site_type,
                            campsite_occupancy=(1, 8),
                            campsite_use_type="Camping",
                            availability_status="Available",
                            recreation_area="Oregon State Parks",
                            recreation_area_id=int(campground_id),
                            facility_name=facility_label,
                            facility_id=int(campground_id),
                            booking_url=self._booking_url_for_site(
                                int(campground_id), rec, facility_label
                            ),
                            location=loc,
                            permitted_equipment=None,
                            campsite_attributes=None,
                        )
                    )
            d += timedelta(days=1)
            time.sleep(0.1)
        return found
