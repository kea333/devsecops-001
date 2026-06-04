"""
Weather App – Pytest Test Suite
Tests: routing, input parsing, helper functions, error handling
"""

import pytest
from app import (
    app,
    parse_search_input,
    best_match,
    weather_background,
    icon_type,
    WEATHER_BACKGROUNDS,
    DEFAULT_BACKGROUND,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def client():
    """Flask test client with testing mode enabled."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ============================================================
# ROUTE TESTS
# ============================================================

class TestRoutes:

    def test_home_returns_200(self, client):
        """Home page loads successfully."""
        response = client.get("/")
        assert response.status_code == 999  # deliberately wrong (200 --> 999) - breaking a test to confirm the gate works

    def test_home_contains_search_form(self, client):
        """Home page contains the search form."""
        response = client.get("/")
        assert b"searchForm" in response.data

    def test_home_shows_initial_state(self, client):
        """Home page shows the initial prompt text."""
        response = client.get("/")
        assert b"Search for a city" in response.data

    def test_weather_empty_query_returns_initial(self, client):
        """Empty query redirects to initial state."""
        response = client.get("/weather?q=")
        assert response.status_code == 200
        assert b"Search for a city" in response.data

    def test_weather_invalid_city_shows_error(self, client):
        """Gibberish city name returns an error state."""
        response = client.get("/weather?q=xyzxyzxyznotacity")
        assert response.status_code == 200
        assert b"error" in response.data.lower() or b"not found" in response.data.lower()

    def test_footer_present(self, client):
        """Footer is rendered on the home page."""
        response = client.get("/")
        assert b"Cloud &amp; Data Projects Portfolio" in response.data


# ============================================================
# PARSE SEARCH INPUT TESTS
# ============================================================

class TestParseSearchInput:

    def test_city_only(self):
        city, code = parse_search_input("London")
        assert city == "London"
        assert code is None

    def test_city_comma_country_code(self):
        city, code = parse_search_input("Newcastle, UK")
        assert city == "Newcastle"
        assert code == "GB"

    def test_city_comma_country_name(self):
        city, code = parse_search_input("Paris, France")
        assert city == "Paris"
        assert code == "FR"

    def test_city_space_country_code(self):
        city, code = parse_search_input("Manchester UK")
        assert city == "Manchester"
        assert code == "GB"

    def test_city_space_two_word_country(self):
        city, code = parse_search_input("Cape Town South Africa")
        assert city == "Cape Town"
        assert code == "ZA"

    def test_case_insensitive(self):
        city, code = parse_search_input("BERLIN, germany")
        assert city == "BERLIN"
        assert code == "DE"

    def test_extra_whitespace_trimmed(self):
        city, code = parse_search_input("  Tokyo  ")
        assert city == "Tokyo"
        assert code is None

    def test_usa_alias(self):
        city, code = parse_search_input("Houston, USA")
        assert code == "US"

    def test_two_letter_country_code(self):
        city, code = parse_search_input("Lyon, FR")
        assert city == "Lyon"
        assert code == "FR"


# ============================================================
# BEST MATCH TESTS
# ============================================================

class TestBestMatch:

    def setup_method(self):
        """Sample geocoding results."""
        self.results = [
            {"name": "Newcastle", "country": "Australia", "country_code": "AU"},
            {"name": "Newcastle", "country": "United Kingdom", "country_code": "GB"},
            {"name": "Newcastle", "country": "United States", "country_code": "US"},
        ]

    def test_returns_first_result_when_no_country(self):
        match = best_match(self.results, None)
        assert match["country_code"] == "AU"

    def test_matches_correct_country(self):
        match = best_match(self.results, "GB")
        assert match["country"] == "United Kingdom"

    def test_returns_none_when_country_not_found(self):
        match = best_match(self.results, "DE")
        assert match is None

    def test_returns_none_for_empty_results(self):
        match = best_match([], "GB")
        assert match is None

    def test_case_insensitive_country_match(self):
        match = best_match(self.results, "gb")
        assert match["country_code"] == "GB"


# ============================================================
# WEATHER BACKGROUND TESTS
# ============================================================

class TestWeatherBackground:

    def test_clear_sky_is_sunny(self):
        assert weather_background(0) == WEATHER_BACKGROUNDS["sunny"]

    def test_mainly_clear_is_sunny(self):
        assert weather_background(1) == WEATHER_BACKGROUNDS["sunny"]

    def test_overcast_is_cloudy(self):
        assert weather_background(3) == WEATHER_BACKGROUNDS["cloudy"]

    def test_fog_is_foggy(self):
        assert weather_background(45) == WEATHER_BACKGROUNDS["foggy"]

    def test_drizzle_is_rainy(self):
        assert weather_background(51) == WEATHER_BACKGROUNDS["rainy"]

    def test_heavy_rain_is_rainy(self):
        assert weather_background(65) == WEATHER_BACKGROUNDS["rainy"]

    def test_snow_is_snowy(self):
        assert weather_background(71) == WEATHER_BACKGROUNDS["snowy"]

    def test_thunderstorm_is_stormy(self):
        assert weather_background(95) == WEATHER_BACKGROUNDS["stormy"]

    def test_unknown_code_returns_default(self):
        assert weather_background(999) == DEFAULT_BACKGROUND


# ============================================================
# ICON TYPE TESTS
# ============================================================

class TestIconType:

    def test_clear_is_sunny(self):
        assert icon_type(0) == "sunny"

    def test_partly_cloudy(self):
        assert icon_type(2) == "partly-cloudy"

    def test_overcast_is_cloudy(self):
        assert icon_type(3) == "cloudy"

    def test_fog_is_cloudy(self):
        assert icon_type(45) == "cloudy"

    def test_rain(self):
        assert icon_type(61) == "rain"

    def test_rain_showers(self):
        assert icon_type(80) == "rain"

    def test_snow(self):
        assert icon_type(73) == "snow"

    def test_storm(self):
        assert icon_type(95) == "storm"

    def test_storm_with_hail(self):
        assert icon_type(99) == "storm"