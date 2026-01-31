#!/usr/bin/env python3
"""
SAS EuroBonus Search Engine API

Comprehensive API client combining multiple SAS endpoints for award flight search:
- /bff/award-finder/destinations/v1 - Calendar availability
- /bff/award-finder/routes/v1 - Route details with times
- /api/offers/flights - Points pricing (EuroBonus)

Usage:
    from sas_search_api import SASSearchEngine
    
    api = SASSearchEngine()
    
    # Get flight offers with exact points pricing
    results = api.search_flights('OSL', 'BKK', '2026-02-05')
    for offer in results:
        print(f"{offer.cabin}: {offer.points} pts + {offer.taxes} NOK")
"""

import json
import logging
import time
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

import requests

# ============================================================================
# Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class FlightSegment:
    """Single flight leg in a journey."""
    flight_number: str          # e.g., "SK975"
    carrier: str                # e.g., "SK" (SAS)
    departure_airport: str      # IATA code
    arrival_airport: str        # IATA code
    departure_time: str         # ISO format or HH:MM
    arrival_time: str           # ISO format or HH:MM
    departure_date: str         # YYYY-MM-DD
    arrival_date: str           # YYYY-MM-DD
    aircraft: str               # e.g., "359" (Airbus A350)
    duration_minutes: int       # Flight duration
    departure_terminal: str = "" # e.g., "3"
    arrival_terminal: str = ""   # e.g., "M"
    distance_miles: int = 0      # Distance in miles
    carrier_name: str = ""       # e.g., "SAS"
    
    @property
    def formatted_departure(self) -> str:
        return f"{self.departure_date} {self.departure_time}"
    
    @property
    def formatted_arrival(self) -> str:
        return f"{self.arrival_date} {self.arrival_time}"


@dataclass
class FlightOffer:
    """Complete flight offer with pricing."""
    origin: str                 # Origin IATA code
    destination: str            # Destination IATA code
    date: str                   # Departure date YYYY-MM-DD
    cabin_class: str            # ECONOMY, PREMIUM, BUSINESS
    product_name: str           # e.g., "ECONOMY BONUS", "PLUS FLEX"
    points: int                 # EuroBonus points cost
    taxes: float                # Cash taxes (in local currency, e.g., NOK)
    currency: str               # Tax currency code
    available_seats: int        # Seats available
    booking_class: str          # Fare booking class
    segments: List[FlightSegment] = field(default_factory=list)
    total_duration_minutes: int = 0  # Total journey time
    stops: int = 0              # Number of stops (0 = direct)
    flight_id: str = ""         # Unique flight identifier
    product_type: str = ""      # e.g., "ECONOMY BONUS", "STANDARD"
    is_saver_award: bool = False # True if this is a standard award ticket
    fare_class: str = ""        # Booking class (e.g., "X", "I", "T")
    cash_price: float = 0.0     # Total cash price in local currency
    base_price: float = 0.0     # Base price (excluding taxes)
    lowest_fare: bool = False   # Flag if this is the lowest fare in cabin
    sas_recommended: bool = False # Flag if SAS recommends this flight
    
    @property
    def is_direct(self) -> bool:
        return self.stops == 0
    
    @property
    def total_duration_hours(self) -> float:
        return self.total_duration_minutes / 60
    
    def __repr__(self) -> str:
        stops_str = "direct" if self.is_direct else f"{self.stops} stop(s)"
        award_tag = "[AWARD] " if self.is_saver_award else ""
        return (f"FlightOffer({award_tag}{self.origin}→{self.destination} {self.date}, "
                f"{self.cabin_class} ({self.product_name}): {self.points:,} pts + {self.taxes:.0f} {self.currency}, "
                f"{stops_str})")


@dataclass
class AvailabilityDate:
    """Single date availability from calendar endpoint."""
    date: str                   # YYYY-MM-DD
    economy_seats: int          # AG seats available
    premium_seats: int          # AP seats available
    business_seats: int         # AB seats available
    
    @property
    def has_availability(self) -> bool:
        return (int(self.economy_seats or 0) + int(self.premium_seats or 0) + int(self.business_seats or 0)) > 0
    
    def get_seats(self, cabin: str) -> int:
        """Get seats for cabin code (AG, AP, AB) or name."""
        cabin_map = {
            "AG": self.economy_seats,
            "AP": self.premium_seats, 
            "AB": self.business_seats,
            "ECONOMY": self.economy_seats,
            "PREMIUM": self.premium_seats,
            "BUSINESS": self.business_seats,
        }
        return cabin_map.get(cabin.upper(), 0)


@dataclass
class RouteInfo:
    """Route information from routes endpoint."""
    flight_id: str
    departure_date: str
    departure_time: str
    arrival_date: str
    arrival_time: str
    fly_time: int               # Flying time in minutes
    total_time: int             # Total journey time in minutes
    num_flights: int            # Number of segments
    haul_type: str              # LH (Long Haul), SH (Short Haul)
    availability: Dict[str, int]  # Cabin code -> seats


# ============================================================================
# SAS Search Engine API
# ============================================================================

class SASSearchEngine:
    """
    Unified SAS EuroBonus Search Engine combining all endpoints.
    
    Endpoints:
        - destinations/v1: Calendar availability (seat counts by date)
        - routes/v1: Route details (times, connections)
        - offers/flights: Points pricing (exact EuroBonus costs)
    """
    
    # API Endpoints
    DESTINATIONS_URL = "https://www.sas.no/bff/award-finder/destinations/v1"
    ROUTES_URL = "https://www.sas.no/bff/award-finder/routes/v1"
    OFFERS_URL = "https://www.sas.no/api/offers/flights"
    PARTNER_AWARD_URL = "https://www.sas.no/award-api/flights"
    
    # Cabin class mapping
    CABIN_CODES = {"AG": "ECONOMY", "AP": "PREMIUM", "AB": "BUSINESS"}
    CABIN_NAMES = {"ECONOMY": "AG", "PREMIUM": "AP", "BUSINESS": "AB"}
    
    # Aircraft type mapping (common types)
    AIRCRAFT_TYPES = {
        "359": "Airbus A350-900",
        "333": "Airbus A330-300",
        "321": "Airbus A321",
        "320": "Airbus A320",
        "319": "Airbus A319",
        "738": "Boeing 737-800",
        "73H": "Boeing 737-800",
        "E90": "Embraer E190",
        "CR9": "CRJ-900",
    }
    
    # Modern User Agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    ]
    
    def __init__(
        self,
        market: str = "no-no",
        pos: str = "no",
        cookies: str = "",
        cookies_file: str = "",
        user_agent: Optional[str] = None
    ):
        """
        Initialize the search engine.
        
        Args:
            market: Market identifier (e.g., "no-no" for Norway)
            pos: Point of sale (e.g., "no")
            cookies: Optional session cookies string
            cookies_file: Optional path to file containing cookies
            user_agent: User agent string
        """
        self.market = market
        self.pos = pos
        self.session = requests.Session()
        
        # Select initial User-Agent
        selected_ua = user_agent or random.choice(self.USER_AGENTS)
        
        self.session.headers.update({
            "User-Agent": selected_ua,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        })
        
        # Load session if provided
        self.session_manager = None
        if cookies_file and cookies_file.endswith('.json'):
            from sas_session_manager import SASSessionManager
            self.session_manager = SASSessionManager(cookies_file)
            self.session.cookies.update(self.session_manager.get_cookie_dict())
            self.session.headers.update({
                "sas-user-session-id": self.session_manager.get_cookie_dict().get("session_id", ""),
                "channel": "WEB",
                "pos": self.pos.upper() if self.pos else "NO"
            })
            logger.info(f"Loaded session from {cookies_file}")
        elif cookies_file:
            cookies = self._load_cookies_from_file(cookies_file)
        
        if cookies and not self.session_manager:
            self.session.headers["Cookie"] = cookies
    
    @staticmethod
    def _load_cookies_from_file(path: str) -> str:
        """Load cookies from a text file."""
        try:
            from pathlib import Path
            cookie_content = Path(path).read_text().strip()
            logger.info(f"Loaded cookies from {path}")
            return cookie_content
        except Exception as e:
            logger.warning(f"Failed to load cookies from {path}: {e}")
            return ""
    
    def rotate_user_agent(self):
        """Rotate the session's User-Agent to a new random one."""
        import random
        new_ua = random.choice(self.USER_AGENTS)
        self.session.headers["User-Agent"] = new_ua
        logger.debug(f"Rotated User-Agent to: {new_ua}")
    
    @classmethod
    def from_cookies_file(cls, cookies_file: str, **kwargs) -> "SASSearchEngine":
        """Create instance with cookies loaded from file."""
        return cls(cookies_file=cookies_file, **kwargs)
    
    # =========================================================================
    # Core API Methods
    # =========================================================================
    
    def get_availability_calendar(
        self,
        origin: str,
        destination: str = "",
        month: str = "",
        passengers: int = 1,
        direct: bool = False,
        cabin_class: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get award availability calendar from destinations endpoint.
        
        Args:
            origin: Origin IATA code (e.g., "OSL")
            destination: Destination IATA code or empty for all
            month: YYYYMM format or empty for all months
            passengers: Number of passengers (1-9)
            direct: Filter for direct flights only
            cabin_class: AG/AP/AB or empty for all
            
        Returns:
            List of destination availability objects with outbound/inbound dates
        """
        params = {
            "market": self.market,
            "origin": origin,
            "destinations": destination,
            "selectedMonth": month,
            "passengers": passengers,
            "direct": str(direct).lower(),
            "availability": "true",
            "selectedFlightClass": cabin_class,
        }
        
        return self._request(self.DESTINATIONS_URL, params)
    
    def get_route_details(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        direct: bool = False
    ) -> List[RouteInfo]:
        """
        Get detailed route info for a specific date.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            departure_date: Date in YYYY-MM-DD format
            direct: Filter for direct flights only
            
        Returns:
            List of RouteInfo objects with flight details
        """
        params = {
            "market": self.market,
            "origin": origin,
            "destination": destination,
            "departureDate": departure_date,
            "direct": str(direct).lower(),
        }
        
        data = self._request(self.ROUTES_URL, params)
        
        routes = []
        for item in data:
            routes.append(RouteInfo(
                flight_id=item.get("flightId", ""),
                departure_date=item.get("departureDate", ""),
                departure_time=item.get("departureTime", ""),
                arrival_date=item.get("arrivalDate", ""),
                arrival_time=item.get("arrivalTime", ""),
                fly_time=item.get("flyTime", 0),
                total_time=item.get("totalTime", 0),
                num_flights=item.get("noOfFlights", 1),
                haul_type=item.get("haulType", ""),
                availability=item.get("availability", {})
            ))
        
        return routes
    
    def get_offers_with_points(
        self,
        origin: str,
        destination: str,
        date: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        youths: int = 0,
        booking_flow: str = "points"
    ) -> Dict[str, Any]:
        """
        Get flight offers with exact points pricing.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            date: Departure date in YYYYMMDD or YYYY-MM-DD format
            adults: Number of adult passengers
            children: Number of children
            infants: Number of infants
            youths: Number of youths
            booking_flow: "points" for EuroBonus, "revenue" for cash
            
        Returns:
            Raw API response with outboundFlights containing pricing
        """
        # Normalize date format to YYYYMMDD
        if "-" in date:
            date = date.replace("-", "")
        
        params = {
            "from": origin,
            "to": destination,
            "outDate": date,
            "adt": adults,
            "chd": children,
            "inf": infants,
            "yth": youths,
            "bookingFlow": booking_flow,
            "pos": self.pos,
            "channel": "web",
            "displayType": "upsell",
        }
        
        return self._request(self.OFFERS_URL, params)
    
    def get_partner_awards(
        self,
        origin: str,
        destination: str,
        date: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        youths: int = 0
    ) -> Dict[str, Any]:
        """
        Get partner award flights (SkyTeam) with exact points pricing.
        Requires authenticated session.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            date: Departure date in YYYY-MM-DD format
            adults, children, infants, youths: Number of passengers
            
        Returns:
            Raw API response with outboundFlights
        """
        # Ensure date format is YYYY-MM-DD
        if len(date) == 8 and "-" not in date:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            
        params = {
            "origin": origin,
            "destination": destination,
            "outboundDate": date,
            "tripType": "one-way",
            "selectedCouponCodes": "",
            "adults": adults,
            "children": children,
            "infants": infants,
            "youths": youths
        }
        
        # Ensure required headers are present (usually set in __init__ for session)
        if "sas-user-session-id" not in self.session.headers:
            logger.warning("sas-user-session-id missing! Partner API will likely fail.")
            
        return self._request(self.PARTNER_AWARD_URL, params)
    
    # =========================================================================
    # Unified Search Methods
    # =========================================================================
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        date: str,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        cabin_filter: Optional[str] = None
    ) -> List[FlightOffer]:
        """
        Search flights and return parsed FlightOffer objects.
        
        This is the main search method that combines the offers endpoint
        with data parsing into structured FlightOffer objects.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            date: Departure date (YYYY-MM-DD or YYYYMMDD)
            adults: Number of adult passengers
            children: Number of children
            infants: Number of infants
            cabin_filter: Optional filter: "ECONOMY", "PREMIUM", "BUSINESS"
            
        Returns:
            List of FlightOffer objects sorted by points (cheapest first)
        """
        offers_data = self.get_offers_with_points(
            origin=origin,
            destination=destination,
            date=date,
            adults=adults,
            children=children,
            infants=infants
        )
        
        offers = self._parse_offers(offers_data, origin, destination, date)
        
        # Apply cabin filter if specified
        if cabin_filter:
            cabin_filter = cabin_filter.upper()
            offers = [o for o in offers if o.cabin_class == cabin_filter]
        
        # Sort by points (cheapest first)
        offers.sort(key=lambda o: o.points)
        
        return offers
    
    def find_cheapest_by_cabin(
        self,
        origin: str,
        destination: str,
        dates: List[str],
        cabin: str = "ECONOMY"
    ) -> Optional[FlightOffer]:
        """
        Find the cheapest flight for a cabin class across multiple dates.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            dates: List of dates to check (YYYY-MM-DD format)
            cabin: Cabin class: "ECONOMY", "PREMIUM", "BUSINESS"
            
        Returns:
            Cheapest FlightOffer or None if no availability
        """
        all_offers = []
        
        for date in dates:
            try:
                offers = self.search_flights(
                    origin=origin,
                    destination=destination,
                    date=date,
                    cabin_filter=cabin
                )
                all_offers.extend(offers)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.warning(f"Failed to search {date}: {e}")
                continue
        
        if not all_offers:
            return None
        
        return min(all_offers, key=lambda o: o.points)
    
    def get_available_dates(
        self,
        origin: str,
        destination: str,
        month: str = "",
        cabin: Optional[str] = None
    ) -> List[AvailabilityDate]:
        """
        Get dates with availability from calendar endpoint.
        
        Args:
            origin: Origin IATA code
            destination: Destination IATA code
            month: Optional month filter (YYYYMM)
            cabin: Optional cabin filter (AG, AP, AB)
            
        Returns:
            List of AvailabilityDate objects
        """
        data = self.get_availability_calendar(
            origin=origin,
            destination=destination,
            month=month,
            cabin_class=cabin or ""
        )
        
        dates = []
        for dest in data:
            # API returns airportCode, not iataCode
            dest_code = dest.get("airportCode") or dest.get("iataCode", "")
            if dest_code == destination or not destination:
                availability = dest.get("availability", {})
                for day in availability.get("outbound", []):
                    dates.append(AvailabilityDate(
                        date=day.get("date", ""),
                        economy_seats=int(day.get("AG", 0) or 0),
                        premium_seats=int(day.get("AP", 0) or 0),
                        business_seats=int(day.get("AB", 0) or 0)
                    ))
        
        return dates
    
    # =========================================================================
    # Private Helper Methods
    # =========================================================================
    
    def _request(self, url: str, params: Dict[str, Any]) -> Any:
        """Make API request with retry, exponential backoff, and automated session refresh."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                
                # Check for auth errors (401 or 403)
                if response.status_code in [401, 403] and self.session_manager:
                    logger.warning(f"Authentication failed (Status {response.status_code}). Attempting session refresh...")
                    
                    # Rotate UA on auth failure to blend in
                    self.rotate_user_agent()
                    
                    if self.session_manager.refresh_session():
                        # Update current session with new credentials
                        self.session.cookies.update(self.session_manager.get_cookie_dict())
                        self.session.headers.update({
                            "sas-user-session-id": self.session_manager.get_cookie_dict().get("session_id", ""),
                        })
                        # Retry the request immediately
                        response = self.session.get(url, params=params, timeout=30)
                    else:
                        logger.error("Automated session refresh failed.")
                
                response.raise_for_status()
                return response.json()
            except requests.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request timeout after {max_retries} retries")
                    return {}
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request failed: {e}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} retries: {e}")
                    return {}
            except json.JSONDecodeError:
                logger.error("Invalid JSON response")
                return {}
        
        return {}
    
    def _parse_offers(
        self,
        data: Dict[str, Any],
        origin: str,
        destination: str,
        date: str
    ) -> List[FlightOffer]:
        """Parse raw API response into FlightOffer objects."""
        offers = []
        
        # Normalize date format
        if len(date) == 8:  # YYYYMMDD
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            
        if not isinstance(data, dict):
            return []
            
        outbound_flights = data.get("outboundFlights", {})
        if not isinstance(outbound_flights, dict):
            # Handle list case if it's a list (some endpoints might return a list)
            if isinstance(outbound_flights, list):
                outbound_flights = {str(i): f for i, f in enumerate(outbound_flights)}
            else:
                return []
        
        for flight_key, flight_data in outbound_flights.items():
            if not isinstance(flight_data, dict):
                continue
            
            # Parse segments
            segments = []
            segs_raw = flight_data.get("segments", [])
            for seg in segs_raw:
                if not isinstance(seg, dict):
                    continue
                # Parse duration (can be int minutes or "HH:MM:SS" string)
                duration_raw = seg.get("duration", 0)
                if isinstance(duration_raw, str) and ":" in duration_raw:
                    parts = duration_raw.split(":")
                    duration_mins = int(parts[0]) * 60 + int(parts[1])
                else:
                    duration_mins = int(duration_raw or 0)

                # Extract airport codes
                dep_air = seg.get("departureAirport", "")
                if isinstance(dep_air, dict): dep_air = dep_air.get("code", "")
                
                arr_air = seg.get("arrivalAirport", "")
                if isinstance(arr_air, dict): arr_air = arr_air.get("code", "")
                
                # Extract aircraft details
                ac_raw = seg.get("airCraft", {})
                ac_name = ac_raw.get("name", "") if isinstance(ac_raw, dict) else self._get_aircraft_name(str(ac_raw))
                
                # Extract carrier details
                mc_raw = seg.get("marketingCarrier", {})
                mc_name = mc_raw.get("name", "") if isinstance(mc_raw, dict) else ""

                segments.append(FlightSegment(
                    flight_number=seg.get("flightNumber", ""),
                    carrier=seg.get("carrier", {}).get("code", "") if isinstance(seg.get("carrier"), dict) else seg.get("carrier", ""),
                    departure_airport=dep_air,
                    arrival_airport=arr_air,
                    departure_time=seg.get("departureTime", ""),
                    arrival_time=seg.get("arrivalTime", ""),
                    departure_date=seg.get("departureDate", date),
                    arrival_date=seg.get("arrivalDate", date),
                    aircraft=ac_name,
                    duration_minutes=duration_mins,
                    departure_terminal=seg.get("departureTerminal", ""),
                    arrival_terminal=seg.get("arrivalTerminal", ""),
                    distance_miles=int(seg.get("miles", 0) or 0),
                    carrier_name=mc_name
                ))
            
            # Calculate total duration and stops
            total_duration = sum(s.duration_minutes for s in segments)
            stops = len(segments) - 1 if segments else 0
            
            # Parse cabins and products
            cabins_raw = flight_data.get("cabins", {})
            
            # If it's a dict, we iterate over items. If it's a list, we iterate over items.
            cabin_items = cabins_raw.items() if isinstance(cabins_raw, dict) else enumerate(cabins_raw)
            
            for cabin_key, cabin_val in cabin_items:
                # If it was a dict, cabin_key is "ECONOMY" etc. If list, it's index.
                if isinstance(cabin_val, dict):
                    cabin_class = cabin_val.get("cabinClass", str(cabin_key))
                all_products = []
                
                # Check 1: Standard structure
                if isinstance(cabin_val, dict) and "products" in cabin_val:
                    raw = cabin_val["products"]
                    if isinstance(raw, list):
                        all_products.extend(raw)
                    elif isinstance(raw, dict):
                         all_products.extend(raw.values())
                
                # Check 2: Upsell structure (deeply nested products or direct products)
                elif isinstance(cabin_val, dict):
                    for sub_val in cabin_val.values():
                        if isinstance(sub_val, dict):
                            if "products" in sub_val:
                                sub_raw = sub_val["products"]
                                if isinstance(sub_raw, list):
                                    all_products.extend(sub_raw)
                                elif isinstance(sub_raw, dict):
                                    all_products.extend(sub_raw.values())
                            else:
                                # Start assuming sub_val IS the product
                                all_products.append(sub_val)

                for product in all_products:
                    if not isinstance(product, dict):
                        continue
                    
                    price_info = product.get("price", {})
                    
                    fares = product.get("fares", [{}])
                    first_fare = fares[0] if fares else {}
                    
                    points = price_info.get("points", 0)
                    if not points:
                        # Fallback for upsell mode? upsell mode should have points if bookingFlow=points
                        # In upsell JSON from earlier debug: "points": 60476 is directly in price dict.
                        pass
                        
                    if not points:
                         # Extra check
                         continue
                    
                    is_saver = product.get("isStandardAward", False)
                    prod_type = product.get("productType", "")
                    
                    offers.append(FlightOffer(
                        origin=origin,
                        destination=destination,
                        date=date,
                        cabin_class=cabin_class,
                        product_name=product.get("productName", ""),
                        points=int(price_info.get("points", 0) or 0),
                        taxes=float(price_info.get("totalTax", 0) or 0),
                        currency=price_info.get("currency", "NOK"),
                        available_seats=int(first_fare.get("avlSeats", 0) or 0),
                        booking_class=first_fare.get("bookingClass", ""),
                        segments=segments,
                        total_duration_minutes=total_duration,
                        stops=stops,
                        flight_id=flight_key,
                        is_saver_award=is_saver,
                        product_type=prod_type,
                        fare_class=first_fare.get("fareClass", ""),
                        cash_price=float(price_info.get("totalPrice", 0) or 0),
                        base_price=float(price_info.get("basePrice", 0) or 0),
                        lowest_fare=product.get("lowestFare", False),
                        sas_recommended=product.get("sasRecommended", False)
                    ))
        
        return offers
    
    def _get_aircraft_name(self, code: str) -> str:
        """Convert aircraft code to human-readable name."""
        return self.AIRCRAFT_TYPES.get(code, code)


# ============================================================================
# CLI & Testing
# ============================================================================

def main():
    """CLI for testing the search engine."""
    import argparse
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description="SAS EuroBonus Search Engine")
    parser.add_argument("--origin", "-o", default="OSL", help="Origin airport")
    parser.add_argument("--destination", "-d", default="BKK", help="Destination airport")
    parser.add_argument("--date", default="20260205", help="Date (YYYYMMDD)")
    parser.add_argument("--cabin", choices=["ECONOMY", "PREMIUM", "BUSINESS"], help="Cabin filter")
    parser.add_argument("--cookies", "-c", help="Path to cookies file for Cloudflare bypass")
    parser.add_argument("--mode", choices=["offers", "calendar", "routes", "partner"], default="offers",
                       help="API mode: offers (SAS points), calendar (availability), routes (times), partner (Star Alliance)")
    args = parser.parse_args()
    
    # Auto-detect cookies file if not specified
    cookies_file = args.cookies
    if not cookies_file:
        default_cookie_path = Path(__file__).parent / "sas_session.json"
        if default_cookie_path.exists():
            cookies_file = str(default_cookie_path)
            print(f"📝 Using session from {default_cookie_path}")
        else:
             # Fallback to cookies.txt
             txt_path = Path(__file__).parent / "cookies.txt"
             if txt_path.exists():
                 cookies_file = str(txt_path)
                 print(f"📝 Using cookies from {txt_path}")
    
    api = SASSearchEngine(cookies_file=cookies_file) if cookies_file else SASSearchEngine()
    
    print(f"\n🔍 Searching {args.origin} → {args.destination} on {args.date}...\n")
    
    if args.mode == "calendar":
        # Calendar mode - just show availability
        dates = api.get_available_dates(args.origin, args.destination)
        if not dates:
            print("❌ No availability found")
            return
        print(f"✅ Found {len(dates)} dates with availability:\n")
        for d in dates[:10]:
            print(f"  {d.date}: Economy={d.economy_seats} Premium={d.premium_seats} Business={d.business_seats}")
        return
    
    if args.mode == "routes":
        # Routes mode - show flight times
        # Normalize date to YYYY-MM-DD
        date = args.date
        if len(date) == 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        routes = api.get_route_details(args.origin, args.destination, date)
        if not routes:
            print("❌ No routes found")
            return
        print(f"✅ Found {len(routes)} routes:\n")
        for r in routes:
            stops_str = "Direct" if r.num_flights == 1 else f"{r.num_flights-1} stop(s)"
            print(f"  {r.departure_time} → {r.arrival_time} ({r.total_time//60}h{r.total_time%60}m) | {stops_str}")
            print(f"    Seats: Economy={r.availability.get('AG',0)} Premium={r.availability.get('AP',0)} Business={r.availability.get('AB',0)}")
        return
        
    if args.mode == "partner":
        # Partner awards mode
        date = args.date
        if len(date) == 8:
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
            
        try:
            res = api.get_partner_awards(args.origin, args.destination, date)
            flights = res.get("outboundFlights", [])
            if not flights:
                print("❌ No partner flights found")
                return
                
            print(f"✅ Found {len(flights)} partner options:\n")
            for f in flights:
                segments = f.get("segments", [])
                
                # Build route string
                route_str = ""
                carriers = []
                total_duration = 0
                
                if segments:
                    deps = [s.get("departureAirport", {}).get("code", "") for s in segments]
                    arrs = [s.get("arrivalAirport", {}).get("code", "") for s in segments]
                    # Full path: Dep1 -> Arr1/Dep2 -> Arr2 ...
                    path = []
                    for i, s in enumerate(segments):
                        d_code = s.get("departureAirport", {}).get("code", "???")
                        a_code = s.get("arrivalAirport", {}).get("code", "???")
                        path.append(d_code)
                        if i == len(segments) - 1:
                            path.append(a_code)
                    
                    route_str = " -> ".join(path)
                    
                    for s in segments:
                        c_raw = s.get("marketingCarrier", {})
                        if isinstance(c_raw, dict):
                            carriers.append(c_raw.get("code", "??"))
                        else:
                            carriers.append(str(c_raw))
                    
                    import re
                    for s in segments:
                        raw_dur = s.get("duration", 0)
                        d_mins = 0
                        if isinstance(raw_dur, int):
                            d_mins = raw_dur
                        elif isinstance(raw_dur, str):
                            if ":" in raw_dur:
                                parts = raw_dur.split(":")
                                d_mins = int(parts[0]) * 60 + int(parts[1])
                            elif "h" in raw_dur:
                                # Parse "1h 20m" or "1h" or "45m"
                                h = 0
                                m = 0
                                match_h = re.search(r'(\d+)h', raw_dur)
                                match_m = re.search(r'(\d+)m', raw_dur)
                                if match_h: h = int(match_h.group(1))
                                if match_m: m = int(match_m.group(1))
                                d_mins = h * 60 + m
                            else:
                                try: d_mins = int(raw_dur)
                                except: pass
                        total_duration += d_mins
                
                cabins = f.get("cabins", [])
                points_str = "N/A"
                for c in cabins:
                     # Usually just one price for partner awards or tiered
                     p = c.get("price", {}).get("points", 0)
                     if p:
                         points_str = f"{p} pts"
                         break
                         
                carrier_str = "/".join(carriers)
                duration_str = f"{total_duration//60}h{total_duration%60}m"
                
                print(f"  ✈️  {carrier_str} | {route_str} | {duration_str} | {points_str}")
                
        except Exception as e:
            print(f"❌ Partner search failed: {e}")
            import traceback
            traceback.print_exc()
        return
    
    # Default: offers mode with points pricing
    offers = api.search_flights(
        origin=args.origin,
        destination=args.destination,
        date=args.date,
        cabin_filter=args.cabin
    )
    
    if not offers:
        print("❌ No flights found")
        print("\n💡 Tip: If you're getting 403 errors, the /api/offers/flights endpoint requires")
        print("   browser cookies. Try: --cookies cookies.txt")
        print("\n   You can also use --mode calendar to check availability without cookies.")
        return
    
    print(f"✅ Found {len(offers)} flight offers:\n")
    
    # Group by cabin
    offers_by_cabin = {}
    for o in offers:
        if o.cabin_class not in offers_by_cabin:
            offers_by_cabin[o.cabin_class] = []
        offers_by_cabin[o.cabin_class].append(o)
    
    for cabin in sorted(offers_by_cabin.keys()):
        print(f"=== {cabin} ===")
        for o in offers_by_cabin[cabin]:
            stops_str = "Direct" if o.is_direct else f"{o.stops} stop(s)"
            
            # Highlight AWARD tickets
            prefix = "🌟 AWARD" if o.is_saver_award else "  Upsell"
            
            # Format route
            route_parts = [s.departure_airport for s in o.segments] + [o.destination]
            route = " → ".join(route_parts)
            
            # Show recommendation
            rec_tag = " [REC]" if o.sas_recommended else ""
            low_tag = " [CHEAPEST]" if o.lowest_fare else ""
            
            # Price in NOK (if it's an upsell, this is helpful to see the conversion)
            price_nok = f" ({o.cash_price:,.0f} {o.currency})" if o.cash_price > 0 else ""
            
            print(f"  {prefix} | {o.points:>7,} pts + {o.taxes:>4.0f} {o.currency}{price_nok} | {stops_str}{rec_tag}{low_tag} | {route}")
            
            # Detail line
            segment_details = []
            for s in o.segments:
                term_info = f" T{s.departure_terminal}" if s.departure_terminal else ""
                segment_details.append(f"{s.carrier} {s.flight_number}{term_info} ({s.aircraft})")
            
            print(f"           {o.product_name} ({o.booking_class}) | {o.available_seats} seats | {o.total_duration_hours:.1f}h | {' / '.join(segment_details)}")
        print("")
    return
if __name__ == "__main__":
    main()
