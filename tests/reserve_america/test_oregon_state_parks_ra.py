"""
Tests for Oregon State Parks (Reserve America) provider.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from camply.containers import CampgroundFacility
from camply.providers.reserve_america.oregon_state_parks_ra import (
    OregonStateParksRA,
    _facility_path_slug,
)


@pytest.fixture
def sample_search_record() -> dict:
    return {
        "type": "camping",
        "name": "Tumalo Test Park",
        "id": 402486,
        "details": {
            "id": 402486,
            "name": "Tumalo Test Park",
            "coordinates": {"latitude": 44.0, "longitude": -121.5},
        },
    }


@pytest.fixture
def sample_campsite_payload() -> dict:
    return {
        "records": [
            {
                "name": "001",
                "siteId": 15616,
                "productId": 9001,
                "availabilityGrid": [
                    {
                        "date": "2026-07-01",
                        "status": "AVAILABLE",
                        "inventoryCount": 1,
                    }
                ],
            }
        ],
        "control": {"currentPage": 0, "pageSize": 20},
        "totalPages": 1,
        "totalRecords": 1,
    }


def test_record_to_facility_maps_contract(sample_search_record):
    fac = OregonStateParksRA._record_to_facility(sample_search_record)
    assert fac.facility_id == 402486
    assert fac.contract_code == "OR"
    assert "Tumalo" in fac.facility_name


def test_find_campground_by_id_builds_facility(sample_search_record):
    provider = OregonStateParksRA()
    with patch.object(
        provider,
        "_search_state_records",
        return_value=[sample_search_record],
    ):
        out = provider.find_campgrounds(campground_id=[402486], state="OR")
    assert len(out) == 1
    assert out[0].facility_id == 402486
    assert out[0].contract_code == "OR"


def test_get_campsites_parses_available(sample_campsite_payload):
    provider = OregonStateParksRA()
    provider._ra = MagicMock()
    provider._ra.get_json.return_value = sample_campsite_payload

    sites = provider.get_campsites(
        campground_id=402486,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 1),
        nights=1,
        facility_name="Tumalo Test Park",
    )
    assert len(sites) == 1
    assert sites[0].campsite_site_name == "001"
    assert sites[0].facility_name == "Tumalo Test Park"
    assert sites[0].availability_status == "Available"
    assert "/camping/tumalo-test-park/r/campsiteDetails.do" in sites[0].booking_url
    assert "siteId=15616" in sites[0].booking_url
    assert "parkId=402486" in sites[0].booking_url
    assert sites[0].campsite_id == 15616


def test_facility_path_slug_matches_oregon_web_urls():
    assert _facility_path_slug("Tumalo State Park") == "tumalo-state-park"
    assert _facility_path_slug("Facility 402486") is None


def test_campground_facility_optional_contract_code():
    c = CampgroundFacility(
        facility_name="X",
        recreation_area="Y",
        facility_id=1,
        recreation_area_id=1,
        map_id=None,
        coordinates=None,
    )
    assert c.contract_code is None
