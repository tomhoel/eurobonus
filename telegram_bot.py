#!/usr/bin/env python3
"""
SAS EuroBonus Interactive Telegram Bot
Provides /search command to query award availability on-demand.

Usage:
    pip install python-telegram-bot
    python telegram_bot.py
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Import SAS API from the monitor
from sas_monitor import SASAwardAPI, Config, DESTINATIONS, ORIGINS

# ============================================================================
# Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Airport code to city name mapping
AIRPORT_NAMES = {
    # Origins
    "OSL": "Oslo",
    "CDG": "Paris",
    "CPH": "Copenhagen",
    "AMS": "Amsterdam",
    # Destinations
    "BKK": "Bangkok",
    "NRT": "Tokyo Narita",
    "HND": "Tokyo Haneda",
    "KIX": "Osaka",
    "PVG": "Shanghai",
    "PEK": "Beijing",
    "SGN": "Ho Chi Minh City",
    "HAN": "Hanoi",
    "SIN": "Singapore",
}

# Cabin class mapping
CABIN_CLASSES = {
    "AG": {"name": "Economy", "emoji": "💺"},
    "AP": {"name": "Premium", "emoji": "⭐"},
    "AB": {"name": "Business", "emoji": "💼"},
}


# ============================================================================
# Route Parser
# ============================================================================

def parse_route(text: str) -> Optional[tuple[str, str, Optional[str]]]:
    """
    Parse route from user input.

    Accepts formats:
    - OSL - BKK (origin and destination)
    - OSL-BKK
    - OSL BKK
    - OSL (origin only - returns all destinations)
    - osl bkk
    - OSL BKK July (with month)
    - OSL BKK 2026-03 (with month)
    - to BKK (reverse search - all origins to destination)
    - TO BKK July (reverse search with month)

    Returns:
        Tuple of (origin, destination, month) or None if invalid
        destination can be None for origin-only queries
        origin can be None for reverse (destination-only) queries
    """
    # Remove command prefix if present
    text = re.sub(r'^/(search|history|calendar)\s+', '', text, flags=re.IGNORECASE)

    # Check for reverse search pattern "to DESTINATION"
    reverse_match = re.search(r'\bto\s+([A-Za-z]{3})\b', text, re.IGNORECASE)

    # Check for month parameter (e.g., "July", "March", "2026-03")
    month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4}-\d{2})\b'
    month_match = re.search(month_pattern, text, re.IGNORECASE)
    month = None
    if month_match:
        month_str = month_match.group(1).lower()
        # Convert month name to YYYYMM format
        month_names = {
            'january': '01', 'jan': '01', 'february': '02', 'feb': '02',
            'march': '03', 'mar': '03', 'april': '04', 'apr': '04',
            'may': '05', 'june': '06', 'jun': '06', 'july': '07', 'jul': '07',
            'august': '08', 'aug': '08', 'september': '09', 'sep': '09',
            'october': '10', 'oct': '10', 'november': '11', 'nov': '11',
            'december': '12', 'dec': '12'
        }
        if month_str in month_names:
            # Assume current or next year
            from datetime import datetime
            current_year = datetime.now().year
            month = f"{current_year}{month_names[month_str]}"
        elif re.match(r'\d{4}-\d{2}', month_str):
            month = month_str.replace('-', '')
        # Remove month from text for airport code extraction
        text = re.sub(month_pattern, '', text, flags=re.IGNORECASE)

    # Handle reverse search
    if reverse_match:
        destination = reverse_match.group(1).upper()
        if destination not in AIRPORT_NAMES:
            return None
        # Return None as origin to indicate reverse search
        return None, destination, month

    # Extract airport codes (3 letters)
    codes = re.findall(r'\b([A-Za-z]{3})\b', text)

    if len(codes) < 1:
        return None

    origin = codes[0].upper()

    # Validate origin
    if origin not in AIRPORT_NAMES:
        return None

    # Check if destination provided
    if len(codes) >= 2:
        destination = codes[1].upper()
        # Validate destination
        if destination not in AIRPORT_NAMES:
            return None
        return origin, destination, month
    else:
        # Origin-only query
        return origin, None, month


# ============================================================================
# Message Formatters
# ============================================================================

def format_origin_search_results(
    origin: str,
    data: List[Dict],
    month: Optional[str] = None
) -> str:
    """
    Format search results for origin-only query (all destinations).
    Sort by: Business seats > Premium > Economy, then by soonest date.
    """
    if not data:
        return (
            f"🔍 <b>Search: {origin} → ALL DESTINATIONS</b>\n\n"
            f"❌ No availability data found."
        )

    # Collect all availability across all destinations
    all_availability = []
    for dest_data in data:
        destination = dest_data.get("airportCode", "")
        city_name = dest_data.get("cityName", AIRPORT_NAMES.get(destination, destination))

        for direction_key in ["outbound", "inbound"]:
            direction_data = dest_data.get("availability", {}).get(direction_key, [])
            for avail in direction_data:
                date = avail.get("date", "")
                if not date:
                    continue

                # Get seat counts
                business = avail.get("AB", 0)
                premium = avail.get("AP", 0)
                economy = avail.get("AG", 0)

                # Only include if has availability
                if business + premium + economy > 0:
                    all_availability.append({
                        'destination': destination,
                        'city_name': city_name,
                        'date': date,
                        'direction': direction_key,
                        'business': business,
                        'premium': premium,
                        'economy': economy,
                        # Sort key: prioritize business, then total seats, then date
                        'sort_key': (
                            -business,  # Most business seats first (negative for descending)
                            -(business + premium + economy),  # Then total seats
                            date  # Then earliest date
                        )
                    })

    if not all_availability:
        return (
            f"🔍 <b>Search: {origin} → ALL DESTINATIONS</b>\n\n"
            f"ℹ️ No available seats found."
        )

    # Sort by priority
    all_availability.sort(key=lambda x: x['sort_key'])

    # Build message
    origin_name = AIRPORT_NAMES.get(origin, origin)
    message = f"🔍 <b>{origin_name} ({origin}) → ALL DESTINATIONS</b>\n\n"
    message += f"Found {len(all_availability)} available flights\n"
    message += f"<i>Sorted by: Business seats → Total seats → Date</i>\n\n"

    # Group by destination for display
    by_destination = {}
    for item in all_availability[:50]:  # Limit to 50 results
        dest = item['destination']
        if dest not in by_destination:
            by_destination[dest] = {
                'city_name': item['city_name'],
                'flights': []
            }
        by_destination[dest]['flights'].append(item)

    for destination, dest_info in list(by_destination.items())[:10]:  # Show top 10 destinations
        message += f"✈️ <b>{dest_info['city_name']} ({destination})</b>\n"

        for flight in dest_info['flights'][:5]:  # Show top 5 flights per destination
            # Format date
            try:
                date_obj = datetime.strptime(flight['date'], "%Y-%m-%d")
                date_display = date_obj.strftime("%b %d")
            except:
                date_display = flight['date']

            direction_emoji = "📤" if flight['direction'] == "outbound" else "📥"

            # Build seat info
            seat_parts = []
            if flight['business'] > 0:
                seat_parts.append(f"💼 Business: {flight['business']}")
            if flight['premium'] > 0:
                seat_parts.append(f"⭐ Premium: {flight['premium']}")
            if flight['economy'] > 0:
                seat_parts.append(f"💺 Economy: {flight['economy']}")

            message += f"  {direction_emoji} {date_display}: {', '.join(seat_parts)}\n"

        message += "\n"

    if len(by_destination) > 10:
        message += f"<i>...and {len(by_destination) - 10} more destinations</i>\n\n"

    booking_url = f"https://www.sas.no/award-finder?origin={origin}"
    message += f'<a href="{booking_url}">🔗 Book on SAS</a>'

    return message.strip()


def format_reverse_search_results(
    destination: str,
    data: List[Dict],
    month: Optional[str] = None
) -> str:
    """
    Format search results for reverse search (all origins to a destination).
    Shows two sections: OUTBOUND (to destination) first, then RETURN (from destination).
    """
    dest_name = AIRPORT_NAMES.get(destination, destination)

    if not data:
        return (
            f"🔍 <b>ALL ROUTES → {dest_name} ({destination})</b>\n\n"
            f"❌ No availability data found."
        )

    # Collect all availability, separated by direction
    outbound_flights = []  # Flying TO destination
    return_flights = []    # Flying FROM destination

    for dest_data in data:
        origin = dest_data.get("origin", "")
        if not origin:
            continue

        origin_name = AIRPORT_NAMES.get(origin, origin)

        for direction_key in ["outbound", "inbound"]:
            direction_data = dest_data.get("availability", {}).get(direction_key, [])
            for avail in direction_data:
                date = avail.get("date", "")
                if not date:
                    continue

                # Get seat counts
                business = avail.get("AB", 0)
                premium = avail.get("AP", 0)
                economy = avail.get("AG", 0)

                # Only include if has availability
                if business + premium + economy > 0:
                    flight_info = {
                        'origin': origin,
                        'origin_name': origin_name,
                        'date': date,
                        'business': business,
                        'premium': premium,
                        'economy': economy,
                        # Sort key: prioritize business, then total seats, then date
                        'sort_key': (
                            -business,
                            -(business + premium + economy),
                            date
                        )
                    }
                    
                    if direction_key == "outbound":
                        outbound_flights.append(flight_info)
                    else:
                        return_flights.append(flight_info)

    if not outbound_flights and not return_flights:
        return (
            f"🔍 <b>ALL ROUTES → {dest_name} ({destination})</b>\n\n"
            f"ℹ️ No available seats found."
        )

    # Sort both lists
    outbound_flights.sort(key=lambda x: x['sort_key'])
    return_flights.sort(key=lambda x: x['sort_key'])

    # Build message
    total_flights = len(outbound_flights) + len(return_flights)
    message = f"🔍 <b>ALL ROUTES → {dest_name} ({destination})</b>\n\n"
    message += f"Found {total_flights} available flights\n\n"

    # Helper function to build a section
    def build_section(flights: list, limit: int = 25) -> str:
        section = ""
        by_origin = {}
        for item in flights[:limit]:
            orig = item['origin']
            if orig not in by_origin:
                by_origin[orig] = {
                    'origin_name': item['origin_name'],
                    'flights': []
                }
            by_origin[orig]['flights'].append(item)

        for origin, orig_info in list(by_origin.items())[:8]:
            section += f"✈️ <b>{orig_info['origin_name']} ({origin})</b>\n"

            for flight in orig_info['flights'][:5]:
                # Format date
                try:
                    date_obj = datetime.strptime(flight['date'], "%Y-%m-%d")
                    date_display = date_obj.strftime("%b %d")
                except:
                    date_display = flight['date']

                # Build seat info
                seat_parts = []
                if flight['business'] > 0:
                    seat_parts.append(f"💼 Business: {flight['business']}")
                if flight['premium'] > 0:
                    seat_parts.append(f"⭐ Premium: {flight['premium']}")
                if flight['economy'] > 0:
                    seat_parts.append(f"💺 Economy: {flight['economy']}")

                section += f"  {date_display}: {', '.join(seat_parts)}\n"

            section += "\n"
        
        return section

    # Section 1: OUTBOUND (flying TO destination)
    if outbound_flights:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📤 <b>OUTBOUND (Flying TO {dest_name})</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += build_section(outbound_flights)

    # Section 2: RETURN (flying FROM destination)
    if return_flights:
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"📥 <b>RETURN (Flying FROM {dest_name})</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        message += build_section(return_flights)

    booking_url = f"https://www.sas.no/award-finder?destination={destination}"
    message += f'<a href="{booking_url}">🔗 Book on SAS</a>'

    return message.strip()


def format_search_results(
    origin: str,
    destination: str,
    data: List[Dict],
    compact: bool = False
) -> str:
    """
    Format search results into a nicely structured message.

    Args:
        origin: Origin IATA code
        destination: Destination IATA code
        data: API response data
        compact: If True, use more compact formatting

    Returns:
        Formatted message string
    """
    if not data:
        return (
            f"🔍 <b>Search: {origin} → {destination}</b>\n\n"
            f"❌ No availability data found.\n\n"
            f"This route may not exist or has no award seats available."
        )

    dest_data = data[0]
    city_name = dest_data.get("cityName", AIRPORT_NAMES.get(destination, destination))

    # Header
    message = f"🔍 <b>Search: {origin} → {city_name} ({destination})</b>\n\n"

    # Process outbound and inbound
    availability = dest_data.get("availability", {})

    for direction_key, direction_emoji, direction_label in [
        ("outbound", "📤", "OUTBOUND"),
        ("inbound", "📥", "RETURN")
    ]:
        direction_data = availability.get(direction_key, [])

        if not direction_data:
            continue

        # Determine direction display
        if direction_key == "outbound":
            route_display = f"{origin} → {destination}"
        else:
            route_display = f"{destination} → {origin}"

        message += f"{direction_emoji} <b>{direction_label} ({route_display})</b>\n"

        # Sort by date
        direction_data_sorted = sorted(direction_data, key=lambda x: x.get("date", ""))

        available_dates = []
        for avail in direction_data_sorted:
            date = avail.get("date", "")
            if not date:
                continue

            # Get seat counts for each cabin class
            seats = {}
            has_availability = False
            for cabin_code in ["AG", "AP", "AB"]:
                seat_count = avail.get(cabin_code, 0)
                seats[cabin_code] = seat_count
                if seat_count > 0:
                    has_availability = True

            # Only show dates with availability
            if has_availability:
                available_dates.append((date, seats))

        if available_dates:
            for date, seats in available_dates:
                # Format date (YYYY-MM-DD -> more readable)
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    date_display = date_obj.strftime("%b %d, %Y")  # e.g., "Feb 15, 2026"
                except:
                    date_display = date

                # Build seat availability string
                seat_parts = []
                for cabin_code in ["AG", "AP", "AB"]:
                    count = seats[cabin_code]
                    if count > 0:
                        emoji = CABIN_CLASSES[cabin_code]["emoji"]
                        name = CABIN_CLASSES[cabin_code]["name"]
                        seat_parts.append(f"{emoji} {name}: {count}")

                if compact:
                    message += f"  📅 {date_display}: {' | '.join(seat_parts)}\n"
                else:
                    message += f"  📅 <b>{date_display}</b>\n"
                    for part in seat_parts:
                        message += f"     {part}\n"
        else:
            message += f"  ℹ️ No available dates\n"

        message += "\n"

    # Footer with booking link
    booking_url = f"https://www.sas.no/award-finder?origin={origin}&destination={destination}"
    message += f'<a href="{booking_url}">🔗 Book on SAS</a>\n'

    return message.strip()


def format_error_message(error_type: str, details: str = "") -> str:
    """Format error message for user."""
    errors = {
        "invalid_format": (
            "❌ <b>Invalid format</b>\n\n"
            "Please use: <code>/search ORIGIN DESTINATION</code>\n\n"
            "Example: <code>/search OSL BKK</code>"
        ),
        "invalid_airports": (
            "❌ <b>Unknown airport codes</b>\n\n"
            "Please check the airport codes and try again.\n\n"
            f"Valid airports:\n{details}"
        ),
        "api_error": (
            "❌ <b>API Error</b>\n\n"
            "Could not fetch data from SAS. Please try again later.\n\n"
            f"Details: {details}"
        ),
        "rate_limit": (
            "⏱️ <b>Rate limit</b>\n\n"
            "Please wait a moment before searching again."
        ),
    }
    return errors.get(error_type, f"❌ Error: {details}")


# ============================================================================
# Bot Command Handlers
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
👋 <b>Welcome to SAS EuroBonus Award Search Bot!</b>

I can help you search for award availability on SAS routes.

<b>Quick Search:</b> Tap a destination below to search from Oslo.

<b>Commands:</b>
/search OSL BKK - Search for routes
/calendar OSL BKK - Calendar view
/best - Best business availability
/status - System status
/help - Full help
"""
    # Create inline keyboard with popular destinations
    keyboard = [
        [
            InlineKeyboardButton("🇹🇭 Bangkok", callback_data="search:OSL:BKK"),
            InlineKeyboardButton("🇯🇵 Tokyo", callback_data="search:OSL:NRT"),
            InlineKeyboardButton("🇸🇬 Singapore", callback_data="search:OSL:SIN"),
        ],
        [
            InlineKeyboardButton("🇯🇵 Osaka", callback_data="search:OSL:KIX"),
            InlineKeyboardButton("🇨🇳 Shanghai", callback_data="search:OSL:PVG"),
            InlineKeyboardButton("🇻🇳 Hanoi", callback_data="search:OSL:HAN"),
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("💎 Best Bets", callback_data="best"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message, 
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
<b>SAS EuroBonus Award Search Bot</b>

<b>🔔 Notifications:</b>
/notify - Subscribe to instant alerts
/unsubscribe - Stop notifications

<b>🔍 Search:</b>
/search OSL BKK - Search specific route
/search OSL - Search all from Oslo
/search OSL BKK July - Filter by month

<b>📚 Browse Tickets:</b>
/catalogue - Browse all tracked tickets with change history

<b>📊 Analytics:</b>
/sales - Fastest selling tickets
/velocity - Hottest tickets (booking now)
/stats - System statistics
/best - Best business class availability

<b>📅 Other:</b>
/calendar OSL BKK - Emoji calendar view
/history OSL BKK - Release history
/alerts - View notification history
/status - System health

<b>Supported Routes:</b>
Origins: OSL, CDG, CPH, AMS
Destinations: BKK, NRT, HND, KIX, PVG, PEK, SGN, HAN, SIN

<b>Examples:</b>
<code>/notify</code>
<code>/search OSL</code>
<code>/catalogue</code>
<code>/sales</code>
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /search command.

    Parses route, queries SAS API, and returns formatted results.
    Supports:
    - origin+destination queries (e.g., /search OSL BKK)
    - origin-only queries (e.g., /search OSL) - shows tracked destinations only
    - reverse search (e.g., /search to BKK) - shows all origins to destination
    """
    user = update.effective_user
    query_text = update.message.text

    logger.info(f"Search request from {user.username or user.id}: {query_text}")

    # Parse route from message
    parsed = parse_route(query_text)

    if not parsed:
        # Invalid format - show error
        airport_list = "\n".join([f"  {code} - {name}" for code, name in sorted(AIRPORT_NAMES.items())])
        error_msg = format_error_message("invalid_airports", airport_list)
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        return

    origin, destination, month = parsed

    # Get API client from context
    api: SASAwardAPI = context.bot_data.get("api")
    if not api:
        await update.message.reply_text("❌ API client not initialized", parse_mode=ParseMode.HTML)
        return

    # Check for reverse search (origin is None)
    if origin is None and destination is not None:
        # Reverse search - find all origins going to this destination
        month_text = f" ({month[:4]}-{month[4:]})" if month else ""
        dest_name = AIRPORT_NAMES.get(destination, destination)
        status_msg = await update.message.reply_text(
            f"🔍 Searching ALL ORIGINS → {dest_name} ({destination}){month_text}...",
            parse_mode=ParseMode.HTML
        )

        try:
            logger.info(f"Reverse search for all origins to {destination}")

            # Query each tracked origin to this destination
            filtered_data = []
            for orig in ORIGINS:
                try:
                    avail_data = api.get_availability(origin=orig, destination=destination, month=month or "")
                    if avail_data:
                        # Add origin info to the data since API doesn't include it
                        for item in avail_data:
                            item['origin'] = orig
                        filtered_data.extend(avail_data)
                except:
                    # Skip origins that fail
                    pass

            # Format results using reverse search formatter
            result_message = format_reverse_search_results(destination, filtered_data, month)

            await status_msg.edit_text(
                result_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            logger.info(f"Reverse search completed: ALL → {destination}")

        except Exception as e:
            logger.error(f"Reverse search failed: {e}")
            error_msg = format_error_message("api_error", str(e))
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)

        return

    # Check if origin-only query
    if destination is None:
        # Origin-only search - query only tracked destinations
        month_text = f" ({month[:4]}-{month[4:]})" if month else ""
        status_msg = await update.message.reply_text(
            f"🔍 Searching {origin} → TRACKED DESTINATIONS{month_text}...",
            parse_mode=ParseMode.HTML
        )

        try:
            logger.info(f"Querying SAS API for tracked destinations from {origin}")

            # Query only tracked DESTINATIONS (not all airports)
            filtered_data = []
            for dest in DESTINATIONS:
                try:
                    avail_data = api.get_availability(origin=origin, destination=dest, month=month or "")
                    if avail_data:
                        filtered_data.extend(avail_data)
                except:
                    # Skip destinations that fail
                    pass

            # Format results
            result_message = format_origin_search_results(origin, filtered_data, month)

            await status_msg.edit_text(
                result_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )

            logger.info(f"Origin-only search completed: {origin} → TRACKED DESTINATIONS")

        except Exception as e:
            logger.error(f"Origin search failed: {e}")
            error_msg = format_error_message("api_error", str(e))
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)

        return

    # Regular origin + destination search
    month_text = f" ({month[:4]}-{month[4:]})" if month else ""
    status_msg = await update.message.reply_text(
        f"🔍 Searching {origin} → {destination}{month_text}...",
        parse_mode=ParseMode.HTML
    )

    try:
        # Query SAS API
        logger.info(f"Querying SAS API: {origin} → {destination} (month: {month})")
        data = api.get_availability(origin=origin, destination=destination, month=month or "")

        # Check if we have results
        has_availability = False
        if data:
            dest_data = data[0]
            for direction in ["outbound", "inbound"]:
                for avail in dest_data.get("availability", {}).get(direction, []):
                    for cabin in ["AG", "AP", "AB"]:
                        if avail.get(cabin, 0) > 0:
                            has_availability = True
                            break

        # Format results
        result_message = format_search_results(origin, destination, data, compact=False)

        # Connection Checker: If no availability, suggest alternatives
        if not has_availability:
            alternatives = []
            other_origins = [o for o in AIRPORT_NAMES.keys() if o != origin and o in ["OSL", "CDG", "CPH", "AMS"]]
            for alt_origin in other_origins:
                alt_data = api.get_availability(origin=alt_origin, destination=destination, month=month or "")
                if alt_data:
                    alt_dest = alt_data[0]
                    for direction in ["outbound"]:
                        for avail in alt_dest.get("availability", {}).get(direction, []):
                            for cabin in ["AB", "AP", "AG"]:  # Prefer business
                                seats = avail.get(cabin, 0)
                                if seats > 0:
                                    class_name = {"AG": "Economy", "AP": "Premium", "AB": "Business"}.get(cabin)
                                    alternatives.append(f"  ✈️ {alt_origin}→{destination}: {seats} {class_name} on {avail['date']}")
                                    break
                            if alternatives:
                                break
                    if len(alternatives) >= 3:
                        break

            if alternatives:
                result_message += "\n\n💡 <b>Alternative Origins:</b>\n" + "\n".join(alternatives[:3])

        # Create inline keyboard for actions
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data=f"search:{origin}:{destination}"),
                InlineKeyboardButton("📅 Calendar", callback_data=f"calendar:{origin}:{destination}"),
                InlineKeyboardButton("📜 History", callback_data=f"history:{origin}:{destination}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Update the status message with results
        await status_msg.edit_text(
            result_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup
        )

        logger.info(f"Search completed: {origin} → {destination}")

    except Exception as e:
        logger.error(f"Search failed: {e}")
        error_msg = format_error_message("api_error", str(e))
        await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command."""
    query_text = update.message.text
    parsed = parse_route(query_text)

    if not parsed:
        await update.message.reply_text(
            "❌ <b>Invalid format</b>\nUse: <code>/history OSL BKK</code>",
            parse_mode=ParseMode.HTML
        )
        return

    origin, destination, _ = parsed  # Ignore month for history
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        history = adb.get_release_history(origin, destination)
        if not history:
            await update.message.reply_text(
                f"ℹ️ No release history found for {origin} → {destination} in the database.",
                parse_mode=ParseMode.HTML
            )
            return

        message = f"📜 <b>Release History: {origin} → {destination}</b>\n\n"
        message += "<i>When seats were first detected:</i>\n\n"

        for date, cabin, seats, first_seen in history:
            class_name = SASAwardAPI.CABIN_CODES.get(cabin, cabin)
            emoji = CABIN_CLASSES.get(cabin, {}).get("emoji", "✈️")
            
            # Format first_seen
            try:
                fs_dt = datetime.strptime(first_seen, "%Y-%m-%d %H:%M:%S")
                fs_display = fs_dt.strftime("%b %d, %H:%M")
            except:
                fs_display = first_seen

            message += f"📅 <b>{date}</b>\n"
            message += f"  {emoji} {class_name}: {seats} seats\n"
            message += f"  ⏰ Detected: {fs_display}\n\n"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    finally:
        adb.close()


async def best_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /best command."""
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        best_bets = adb.get_best_bets(limit=15)
        if not best_bets:
            await update.message.reply_text(
                "ℹ️ No Business Class availability found in the database.",
                parse_mode=ParseMode.HTML
            )
            return

        message = "💎 <b>Best Bets: Business Class (AB)</b>\n"
        message += "<i>Routes with most current availability:</i>\n\n"

        for origin, destination, date, seats in best_bets:
            message += f"💼 <b>{origin} → {destination}</b>\n"
            message += f"  📅 {date}: <b>{seats}</b> seats\n\n"

        booking_url = "https://www.sas.no/award-finder"
        message += f'<a href="{booking_url}">🔗 Go to SAS Award Finder</a>'

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    finally:
        adb.close()


async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /notify command - subscribe to notifications."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        # Check if already subscribed
        if adb.is_subscribed(chat_id):
            await update.message.reply_text(
                "✅ <b>You're already subscribed!</b>\n\n"
                "You'll receive instant notifications when:\n"
                "🎉 New tickets are released\n"
                "📈 Seats increase\n"
                "📉 Seats decrease (being booked)\n"
                "💨 Tickets sell out\n\n"
                "Use /unsubscribe to stop notifications.",
                parse_mode=ParseMode.HTML
            )
            return

        # Subscribe the user
        success = adb.add_subscriber(
            chat_id=chat_id,
            username=user.username,
            first_name=user.first_name
        )

        if success:
            subscriber_count = adb.get_subscriber_count()
            await update.message.reply_text(
                "🔔 <b>Subscribed successfully!</b>\n\n"
                "You'll now receive instant notifications for:\n"
                "• 🎉 New ticket releases\n"
                "• 📈 Seat increases\n"
                "• 📉 Seat decreases\n"
                "• 💨 Sold out alerts\n\n"
                f"Total subscribers: {subscriber_count}\n\n"
                "Use /unsubscribe anytime to stop notifications.",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"New subscriber: {user.username or chat_id} ({subscriber_count} total)")
        else:
            await update.message.reply_text(
                "❌ Failed to subscribe. Please try again later.",
                parse_mode=ParseMode.HTML
            )
    finally:
        adb.close()


async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command - unsubscribe from notifications."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        # Check if subscribed
        if not adb.is_subscribed(chat_id):
            await update.message.reply_text(
                "ℹ️ <b>You're not subscribed</b>\n\n"
                "You're not receiving notifications.\n"
                "Use /notify to subscribe.",
                parse_mode=ParseMode.HTML
            )
            return

        # Unsubscribe the user
        success = adb.remove_subscriber(chat_id)

        if success:
            subscriber_count = adb.get_subscriber_count()
            await update.message.reply_text(
                "🔕 <b>Unsubscribed successfully</b>\n\n"
                "You won't receive any more notifications.\n\n"
                f"Remaining subscribers: {subscriber_count}\n\n"
                "You can re-subscribe anytime with /notify",
                parse_mode=ParseMode.HTML
            )
            logger.info(f"User unsubscribed: {user.username or chat_id} ({subscriber_count} remaining)")
        else:
            await update.message.reply_text(
                "❌ Failed to unsubscribe. Please try again later.",
                parse_mode=ParseMode.HTML
            )
    finally:
        adb.close()


async def sales_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sales command - show fastest-selling tickets history."""
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        fastest = adb.get_fastest_selling_tickets(limit=15)

        if not fastest:
            await update.message.reply_text(
                "ℹ️ No sales history available yet.\n\n"
                "Tickets need to sell out completely to appear here.",
                parse_mode=ParseMode.HTML
            )
            return

        message = "📊 <b>FASTEST SELLING TICKETS</b>\n\n"
        message += "<i>Tickets that sold out quickest:</i>\n\n"

        for idx, (origin, destination, date, cabin, duration_hours,
                  max_seats, avg_velocity, sold_out_at) in enumerate(fastest, 1):
            dest_name = AIRPORT_NAMES.get(destination, destination)
            class_name = CABIN_CLASSES.get(cabin, {}).get("name", cabin)

            # Format duration
            if duration_hours < 24:
                duration_str = f"{duration_hours:.1f} hours"
            else:
                days = int(duration_hours / 24)
                hours = int(duration_hours % 24)
                duration_str = f"{days}d {hours}h"

            # Determine fire emoji intensity based on velocity
            if avg_velocity >= 1.5:
                fire = "🔥🔥🔥"
            elif avg_velocity >= 1.0:
                fire = "🔥🔥"
            elif avg_velocity >= 0.5:
                fire = "🔥"
            else:
                fire = ""

            # Format sold out time
            try:
                sold_dt = datetime.strptime(sold_out_at, "%Y-%m-%d %H:%M:%S")
                sold_display = sold_dt.strftime("%b %d, %H:%M")
            except:
                sold_display = sold_out_at

            message += f"{idx}. <b>{origin} → {dest_name}</b> {date}\n"
            message += f"   💺 {class_name}: {max_seats} seats total\n"
            message += f"   ⏱️ Sold out in: <b>{duration_str}</b>\n"
            if avg_velocity > 0:
                message += f"   ⚡ {avg_velocity:.1f} seats/hour {fire}\n"
            message += f"   🕐 Sold: {sold_display}\n\n"

        message += "<i>These tickets sold out completely from first discovery.</i>"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    finally:
        adb.close()


async def velocity_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /velocity command - show hottest tickets (fastest booking)."""
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        hot_tickets = adb.get_hot_tickets(limit=15)

        if not hot_tickets:
            await update.message.reply_text(
                "ℹ️ No booking velocity data available yet.\n\n"
                "Velocity tracking requires at least one seat decrease event.",
                parse_mode=ParseMode.HTML
            )
            return

        message = "🔥 <b>HOTTEST TICKETS (Booking Fast!)</b>\n\n"
        message += "<i>Routes with highest booking velocity:</i>\n\n"

        for idx, (origin, destination, date, cabin, direction, curr_avail,
                  total_booked, velocity) in enumerate(hot_tickets, 1):
            dest_name = AIRPORT_NAMES.get(destination, destination)
            class_name = CABIN_CLASSES.get(cabin, {}).get("name", cabin)
            direction_emoji = "→" if direction == "outbound" else "←"

            # Determine fire emoji intensity
            if velocity >= 1.5:
                fire = "🔥🔥🔥"
            elif velocity >= 1.0:
                fire = "🔥🔥"
            elif velocity >= 0.5:
                fire = "🔥"
            else:
                fire = ""

            message += f"{idx}. <b>{origin} {direction_emoji} {dest_name}</b> {date}\n"
            message += f"   💺 {class_name}: {curr_avail} left ({total_booked} booked)\n"
            message += f"   ⚡ <b>{velocity:.1f} seats/hour</b> {fire}\n\n"

        message += '<a href="https://www.sas.no/award-finder">🔗 Book now on SAS</a>'

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    finally:
        adb.close()


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - enhanced status with tracking statistics."""
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        stats = adb.get_stats()

        # Format last scraped time
        last_scraped = stats.get("last_scraped", "Never")
        if last_scraped and last_scraped != "Never":
            try:
                ls_dt = datetime.strptime(last_scraped, "%Y-%m-%d %H:%M:%S")
                last_scraped = ls_dt.strftime("%b %d, %H:%M:%S UTC")
            except:
                pass

        message = "📊 <b>System Statistics Dashboard</b>\n\n"
        message += "🕐 <b>Last Scan:</b> " + last_scraped + "\n"
        message += f"📁 <b>Total Snapshots:</b> {stats.get('total_records', 0):,}\n"
        message += f"🛤️ <b>Unique Routes:</b> {stats.get('unique_routes', 0)}\n"
        message += f"🎫 <b>Tracked Tickets:</b> {stats.get('tracked_tickets', 0):,}\n"
        message += f"📋 <b>Baseline Tickets:</b> {stats.get('baseline_tickets', 0):,}\n"
        message += f"📨 <b>Notifications Sent:</b> {stats.get('notifications_sent', 0)}\n"

        # Get hot tickets count
        hot_tickets = adb.get_hot_tickets(limit=100)
        hot_count = len([t for t in hot_tickets if t[7] >= 0.5])  # velocity >= 0.5 (index 7 now includes direction)
        if hot_count > 0:
            message += f"\n🔥 <b>Hot Tickets:</b> {hot_count} (booking fast)\n"

        message += "\n✅ <i>Monitor is running</i>\n"
        message += "\n<b>Commands:</b>\n"
        message += "/tickets - View all tracked tickets\n"
        message += "/velocity - See hottest tickets\n"
        message += "/best - Best business class availability"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    finally:
        adb.close()


async def catalogue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /catalogue command - browse all tracked tickets with clean format.
    Shows: current availability, max issued, and recent changes.
    """
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        # Get all tracked tickets with change history
        tickets = adb.get_route_summary_with_changes()

        if not tickets:
            await update.message.reply_text(
                "ℹ️ No tracked tickets found.\n\n"
                "The monitor needs to run at least once to populate the catalogue.",
                parse_mode=ParseMode.HTML
            )
            return

        # Group by route, direction, then by date
        by_route = {}
        for t in tickets:
            route_key = (t['origin'], t['destination'], t['direction'])
            if route_key not in by_route:
                by_route[route_key] = {}

            date = t['date']
            if date not in by_route[route_key]:
                by_route[route_key][date] = {}

            by_route[route_key][date][t['cabin_class']] = t

        # Build message with new clean format
        message = "📚 <b>TICKET CATALOGUE</b>\n\n"

        route_count = 0
        for (origin, destination, direction), dates in sorted(by_route.items()):
            if route_count >= 5:  # Limit to 5 routes
                break
            route_count += 1

            dest_name = AIRPORT_NAMES.get(destination, destination)
            direction_emoji = "→" if direction == "outbound" else "←"
            direction_text = f" ({direction})" if direction else ""
            message += f"✈️ <b>{origin} {direction_emoji} {dest_name}</b>{direction_text}\n"

            date_count = 0
            for date, cabins in sorted(dates.items()):
                if date_count >= 3:  # Limit to 3 dates per route
                    break
                date_count += 1

                # Format date nicely
                try:
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    date_display = date_obj.strftime("%b %d, %Y")
                except:
                    date_display = date

                message += f"📅 <b>{date_display}</b>\n"

                # Show each cabin class with clean format
                for cabin_code in ["AB", "AP", "AG"]:
                    if cabin_code in cabins:
                        t = cabins[cabin_code]
                        emoji = CABIN_CLASSES.get(cabin_code, {}).get("emoji", "✈️")
                        curr = t['currently_available']
                        max_seats = t['max_issued']
                        booked = max_seats - curr

                        if curr > 0:
                            if booked > 0:
                                message += f"{emoji} {curr:2d} ← {max_seats:2d}  (-{booked} booked)\n"
                            else:
                                message += f"{emoji} {curr:2d} ← {max_seats:2d}\n"
                        else:
                            message += f"{emoji}  0 ← {max_seats:2d}  (SOLD OUT)\n"
                
                # Show recent changes if any
                all_changes = []
                for cabin_code, t in cabins.items():
                    for change in t.get('changes', []):
                        all_changes.append((change, cabin_code))
                
                if all_changes:
                    # Sort by time (most recent first) and take top 3
                    all_changes.sort(key=lambda x: x[0][0], reverse=True)
                    recent = all_changes[:3]
                    
                    change_strs = []
                    for (changed_at, cabin, prev, new, amount, change_type), cabin_code in recent:
                        emoji = CABIN_CLASSES.get(cabin_code, {}).get("emoji", "")
                        try:
                            dt = datetime.strptime(changed_at, "%Y-%m-%d %H:%M:%S")
                            time_str = dt.strftime("%H:%M")
                        except:
                            time_str = changed_at
                        
                        if amount < 0:
                            change_strs.append(f"{amount}{emoji} {time_str}")
                        else:
                            change_strs.append(f"+{amount}{emoji} {time_str}")
                    
                    if change_strs:
                        message += f"📉 Recent: {', '.join(change_strs)}\n"
                
                message += "\n"
            
            message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Add remaining routes count
        remaining = len(by_route) - route_count
        if remaining > 0:
            message += f"<i>...and {remaining} more routes</i>\n\n"
        
        message += '<a href="https://www.sas.no/award-finder">🔗 Book on SAS</a>'

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    finally:
        adb.close()


def build_catalogue_page(tickets: list, page: int = 0, sort_by: str = "recent", filter_type: str = "all") -> tuple:
    """
    Build a page of the catalogue with navigation buttons.

    Args:
        tickets: List of ticket tuples from get_all_tracked_tickets()
        page: Page number (0-indexed)
        sort_by: Sort method (recent, availability, date, route)
        filter_type: Filter (all, available, sold_out)

    Returns:
        Tuple of (message, keyboard)
    """
    ITEMS_PER_PAGE = 5  # Routes per page

    # Apply filter - now index 6 is currently_available (after adding direction at index 4)
    if filter_type == "available":
        filtered_tickets = [t for t in tickets if t[6] > 0]  # currently_available > 0
    elif filter_type == "sold_out":
        filtered_tickets = [t for t in tickets if t[6] == 0]  # currently_available == 0
    else:
        filtered_tickets = tickets

    # Apply sort - indices updated for direction column
    if sort_by == "recent":
        sorted_tickets = sorted(filtered_tickets, key=lambda x: x[8], reverse=True)  # first_seen_at desc
    elif sort_by == "availability":
        sorted_tickets = sorted(filtered_tickets, key=lambda x: (x[5], x[6]), reverse=True)  # max_issued, currently_available desc
    elif sort_by == "date":
        sorted_tickets = sorted(filtered_tickets, key=lambda x: x[2])  # date asc
    elif sort_by == "route":
        sorted_tickets = sorted(filtered_tickets, key=lambda x: (x[0], x[1], x[4], x[2]))  # origin, destination, direction, date
    else:
        sorted_tickets = filtered_tickets

    # Group by route and direction
    by_route = {}
    for ticket in sorted_tickets:
        route_key = (ticket[0], ticket[1], ticket[4])  # (origin, destination, direction)
        if route_key not in by_route:
            by_route[route_key] = []
        by_route[route_key].append(ticket)

    total_routes = len(by_route)
    total_pages = max(1, (total_routes + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))  # Clamp page

    # Get routes for this page
    route_items = list(by_route.items())
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_routes)
    page_routes = route_items[start_idx:end_idx]

    # Build message header
    sort_names = {
        "recent": "Recent Discovery",
        "availability": "Availability",
        "date": "Flight Date",
        "route": "Route"
    }
    filter_names = {
        "all": "All",
        "available": "Available Only",
        "sold_out": "Sold Out"
    }

    message = f"📚 <b>TICKET CATALOGUE</b>\n\n"
    message += f"Total: {len(filtered_tickets)} tickets across {total_routes} routes\n"
    message += f"Sort: {sort_names.get(sort_by, sort_by)} | Filter: {filter_names.get(filter_type, filter_type)}\n"
    message += f"Page {page + 1}/{total_pages}\n\n"

    # Build routes display
    for (origin, destination, direction), route_tickets in page_routes:
        dest_name = AIRPORT_NAMES.get(destination, destination)
        direction_emoji = "→" if direction == "outbound" else "←"
        message += f"✈️ <b>{origin} {direction_emoji} {dest_name}</b> ({direction}, {len(route_tickets)} tickets)\n"

        # Group by date
        by_date = {}
        for t in route_tickets:
            if t[2] not in by_date:
                by_date[t[2]] = []
            by_date[t[2]].append(t)

        for date in sorted(by_date.keys())[:3]:  # Show max 3 dates per route
            message += f"  📅 {date}\n"
            for t in by_date[date]:
                cabin = t[3]
                class_name = CABIN_CLASSES.get(cabin, {}).get("name", cabin)
                emoji = CABIN_CLASSES.get(cabin, {}).get("emoji", "✈️")
                max_issued = t[5]  # Updated index
                curr_avail = t[6]  # Updated index
                total_booked = t[7]  # Updated index

                if curr_avail > 0:
                    message += f"    {emoji} {class_name}: {curr_avail} avail ({max_issued} total, {total_booked} booked)\n"
                else:
                    message += f"    {emoji} {class_name}: SOLD OUT ({max_issued} total)\n"

        message += "\n"

    # Build keyboard
    keyboard = []

    # Sorting buttons (row 1)
    sort_row = [
        InlineKeyboardButton("🕐 Recent" + (" ✓" if sort_by == "recent" else ""),
                           callback_data=f"cat:0:recent:{filter_type}"),
        InlineKeyboardButton("💺 Avail" + (" ✓" if sort_by == "availability" else ""),
                           callback_data=f"cat:0:availability:{filter_type}"),
        InlineKeyboardButton("📅 Date" + (" ✓" if sort_by == "date" else ""),
                           callback_data=f"cat:0:date:{filter_type}"),
    ]
    keyboard.append(sort_row)

    # Filter buttons (row 2)
    filter_row = [
        InlineKeyboardButton("All" + (" ✓" if filter_type == "all" else ""),
                           callback_data=f"cat:0:{sort_by}:all"),
        InlineKeyboardButton("Available" + (" ✓" if filter_type == "available" else ""),
                           callback_data=f"cat:0:{sort_by}:available"),
        InlineKeyboardButton("Sold Out" + (" ✓" if filter_type == "sold_out" else ""),
                           callback_data=f"cat:0:{sort_by}:sold_out"),
    ]
    keyboard.append(filter_row)

    # Navigation buttons (row 3)
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous",
                                           callback_data=f"cat:{page-1}:{sort_by}:{filter_type}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️",
                                           callback_data=f"cat:{page+1}:{sort_by}:{filter_type}"))
    if nav_row:
        keyboard.append(nav_row)

    return message.strip(), keyboard


def build_alerts_page(notifications: list, page: int = 0,
                     filter_type: str = "all") -> tuple:
    """
    Build a paginated alerts history page.

    Args:
        notifications: List of notification tuples from DB
        page: Current page number (0-indexed)
        filter_type: Filter applied ('all', 'new', 'vanished', etc.)

    Returns:
        (message_text, keyboard_buttons)
    """
    from datetime import datetime

    ITEMS_PER_PAGE = 10

    # Calculate pagination
    total_items = len(notifications)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    page_items = notifications[start_idx:end_idx]

    # Build header
    filter_names = {
        "all": "All Notifications",
        "new": "New Tickets",
        "vanished": "Vanished Tickets",
        "increase": "Seat Increases",
        "decrease": "Seat Decreases"
    }

    message = f"📨 <b>Notification History</b>\n"
    message += f"Filter: {filter_names.get(filter_type, 'All')}\n"
    message += f"Page {page + 1}/{total_pages} ({total_items} total)\n\n"

    if not page_items:
        message += "No notifications found."
        return message, []

    # Build notification list
    for i, notif in enumerate(page_items, start=start_idx + 1):
        notif_id, sent_at, origin, destination, date, cabin, seats, msg_preview = notif

        # Parse timestamp
        try:
            dt = datetime.strptime(sent_at, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%b %d, %H:%M")
        except:
            time_str = sent_at

        # Detect notification type from message
        if "NEW TICKETS" in msg_preview:
            emoji = "🎉"
        elif "TICKETS GONE" in msg_preview:
            emoji = "💨"
        elif "SEATS BEING BOOKED" in msg_preview:
            emoji = "📉"
        else:
            emoji = "📨"

        # Show timestamp and message preview
        message += f"{emoji} <b>{time_str}</b>\n"

        # Clean up and show the message content
        # Remove HTML tags for cleaner display
        preview = msg_preview.replace("<b>", "").replace("</b>", "")
        preview = preview.replace("<i>", "").replace("</i>", "")
        preview = preview.replace("\n\n", "\n")  # Reduce double newlines

        # Show the preview with indentation
        lines = preview.split('\n')
        for line in lines[:4]:  # Show first 4 lines
            line = line.strip()
            if line:
                message += f"   {line}\n"

        message += "\n"

    # Build keyboard
    keyboard = []

    # Filter buttons row
    filter_row = []
    for f_type, f_name in [("all", "All"), ("new", "New"), ("vanished", "Gone"),
                           ("increase", "Incr"), ("decrease", "Decr")]:
        checkmark = "✓ " if f_type == filter_type else ""
        filter_row.append(InlineKeyboardButton(
            f"{checkmark}{f_name}",
            callback_data=f"alerts:{page}:{f_type}"
        ))
    keyboard.append(filter_row)

    # Navigation row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("< Prev", callback_data=f"alerts:{page-1}:{filter_type}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next >", callback_data=f"alerts:{page+1}:{filter_type}"))

    if nav_row:
        keyboard.append(nav_row)

    # Close button
    keyboard.append([InlineKeyboardButton("❌ Close", callback_data="close")])

    return message, keyboard


async def tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /tickets command - show all tracked tickets with historical max.
    Usage:
        /tickets              → All tracked tickets
        /tickets OSL-BKK      → Specific route
        /tickets OSL-BKK 2026-02 → Route + month filter
    """
    query_text = update.message.text
    args = query_text.split()[1:]  # Skip command

    origin = dest = month = None

    if len(args) >= 1:
        parts = args[0].split('-')
        if len(parts) == 2:
            origin, dest = parts[0].upper(), parts[1].upper()

    if len(args) >= 2:
        month = args[1].replace('-', '')  # Convert 2026-02 to 202602

    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        tickets = adb.get_all_tracked_tickets(origin, dest, month)

        if not tickets:
            filter_text = ""
            if origin and dest:
                filter_text = f" for {origin} → {dest}"
            if month:
                filter_text += f" ({month[:4]}-{month[4:]})"

            await update.message.reply_text(
                f"ℹ️ No tracked tickets found{filter_text}.",
                parse_mode=ParseMode.HTML
            )
            return

        # Group by route and direction
        by_route = {}
        for (orig, destination, date, cabin, direction, max_issued, curr_avail,
             total_booked, first_seen, velocity) in tickets:
            route_key = (orig, destination, direction)
            if route_key not in by_route:
                by_route[route_key] = []
            by_route[route_key].append({
                'date': date,
                'cabin': cabin,
                'max_issued': max_issued,
                'currently_available': curr_avail,
                'total_booked': total_booked,
                'first_seen': first_seen,
                'velocity': velocity
            })

        message = f"🎫 <b>Tracked Tickets ({len(tickets)} total)</b>\n\n"

        for (orig, destination, direction), route_tickets in sorted(by_route.items())[:10]:  # Limit to 10 routes
            dest_name = AIRPORT_NAMES.get(destination, destination)
            direction_emoji = "→" if direction == "outbound" else "←"
            message += f"✈️ <b>{orig} {direction_emoji} {dest_name}</b> ({direction})\n\n"

            # Group by date
            by_date = {}
            for t in route_tickets:
                if t['date'] not in by_date:
                    by_date[t['date']] = []
                by_date[t['date']].append(t)

            for date in sorted(by_date.keys())[:5]:  # Limit to 5 dates per route
                message += f"📅 <b>{date}</b>\n"
                for t in by_date[date]:
                    class_name = CABIN_CLASSES.get(t['cabin'], {}).get("name", t['cabin'])
                    emoji = CABIN_CLASSES.get(t['cabin'], {}).get("emoji", "✈️")

                    if t['currently_available'] > 0:
                        message += f"  {emoji} {class_name}: <b>{t['currently_available']}</b> available "
                        message += f"({t['max_issued']} total, {t['total_booked']} booked)\n"

                        # Add velocity if hot
                        if t['velocity'] and t['velocity'] > 0.3:
                            if t['velocity'] >= 1.0:
                                fire = "🔥🔥"
                            else:
                                fire = "🔥"
                            message += f"     ⚡ {t['velocity']:.1f} seats/hr {fire}\n"
                    else:
                        message += f"  {emoji} {class_name}: <b>SOLD OUT</b> "
                        message += f"({t['max_issued']} total, all booked)\n"

                    # First seen
                    try:
                        fs_dt = datetime.strptime(t['first_seen'], "%Y-%m-%d %H:%M:%S")
                        fs_display = fs_dt.strftime("%b %d, %H:%M")
                        message += f"     🕐 First seen: {fs_display}\n"
                    except:
                        pass

                message += "\n"

            message += "---\n\n"

        if len(by_route) > 10:
            message += f"<i>Showing 10 of {len(by_route)} routes. Use filters to narrow results.</i>\n\n"

        message += '<a href="https://www.sas.no/award-finder">🔗 Book on SAS</a>'

        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    finally:
        adb.close()


async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /calendar command - show emoji grid of monthly availability."""
    query_text = update.message.text
    parsed = parse_route(query_text)

    if not parsed:
        await update.message.reply_text(
            "❌ <b>Invalid format</b>\nUse: <code>/calendar OSL BKK</code> or <code>/calendar OSL BKK March</code>",
            parse_mode=ParseMode.HTML
        )
        return

    origin, destination, month = parsed
    api: SASAwardAPI = context.bot_data.get("api")

    if not api:
        await update.message.reply_text("❌ API not initialized", parse_mode=ParseMode.HTML)
        return

    # Fetch data
    data = api.get_availability(origin=origin, destination=destination, month=month or "")

    if not data:
        await update.message.reply_text(
            f"ℹ️ No data found for {origin} → {destination}",
            parse_mode=ParseMode.HTML
        )
        return

    dest_data = data[0]
    city_name = dest_data.get("cityName", destination)

    # Build calendar grid
    message = f"📅 <b>Calendar: {origin} → {city_name}</b>\n\n"
    message += "<b>Legend:</b> 🟥 None | 💺 Economy | ⭐ Premium | 💎 Business\n\n"

    for direction_key, direction_label in [("outbound", "OUTBOUND"), ("inbound", "RETURN")]:
        direction_data = dest_data.get("availability", {}).get(direction_key, [])
        if not direction_data:
            continue

        message += f"<b>{direction_label}:</b>\n"
        
        # Group by month
        by_month = {}
        for avail in sorted(direction_data, key=lambda x: x.get("date", "")):
            date = avail.get("date", "")
            if not date:
                continue
            month_key = date[:7]  # YYYY-MM
            if month_key not in by_month:
                by_month[month_key] = []
            
            # Determine best class available
            if avail.get("AB", 0) > 0:
                by_month[month_key].append("💎")
            elif avail.get("AP", 0) > 0:
                by_month[month_key].append("⭐")
            elif avail.get("AG", 0) > 0:
                by_month[month_key].append("💺")
            else:
                by_month[month_key].append("🟥")

        for month_name, emojis in by_month.items():
            message += f"<code>{month_name}:</code> {''.join(emojis)}\n"

        message += "\n"

    await update.message.reply_text(message, parse_mode=ParseMode.HTML)


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /alerts command - view notification history with pagination.
    """
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        # Get all notifications (will paginate in UI)
        notifications = adb.get_notification_history(limit=100, offset=0, filter_type="all")

        if not notifications:
            await update.message.reply_text(
                "📨 No notifications found.\n\n"
                "Notifications will appear here after the monitor detects changes "
                "and sends alerts.",
                parse_mode=ParseMode.HTML
            )
            return

        # Build first page
        message, keyboard = build_alerts_page(notifications, page=0, filter_type="all")

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    finally:
        adb.close()


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command - show system health dashboard."""
    db_path = context.bot_data.get("db_path", "sas_monitor.db")

    from sas_monitor import AvailabilityDatabase
    adb = AvailabilityDatabase(db_path)

    try:
        stats = adb.get_stats()

        # Format last scraped time
        last_scraped = stats.get("last_scraped", "Never")
        if last_scraped and last_scraped != "Never":
            try:
                from datetime import datetime
                ls_dt = datetime.strptime(last_scraped, "%Y-%m-%d %H:%M:%S")
                last_scraped = ls_dt.strftime("%b %d, %H:%M:%S")
            except:
                pass

        message = "📊 <b>System Status Dashboard</b>\n\n"
        message += f"🕐 <b>Last Scan:</b> {last_scraped}\n"
        message += f"📁 <b>Total Records:</b> {stats.get('total_records', 0):,}\n"
        message += f"🛤️ <b>Unique Routes:</b> {stats.get('unique_routes', 0)}\n"
        message += f"📋 <b>Baseline Tickets:</b> {stats.get('baseline_tickets', 0):,}\n"
        message += f"📨 <b>Notifications Sent:</b> {stats.get('notifications_sent', 0)}\n"
        message += "\n✅ <i>Monitor is running</i>"

        await update.message.reply_text(message, parse_mode=ParseMode.HTML)
    finally:
        adb.close()


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data
    logger.info(f"Callback received: {data}")

    # Parse callback data
    parts = data.split(":")
    action = parts[0]

    try:
        if action == "cat" and len(parts) == 4:
            # Catalogue pagination/sorting: cat:page:sort:filter
            page = int(parts[1])
            sort_by = parts[2]
            filter_type = parts[3]

            db_path = context.bot_data.get("db_path", "sas_monitor.db")
            from sas_monitor import AvailabilityDatabase
            adb = AvailabilityDatabase(db_path)

            try:
                tickets = adb.get_all_tracked_tickets()

                # Build new page
                message, keyboard = build_catalogue_page(tickets, page, sort_by, filter_type)

                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            finally:
                adb.close()

        elif action == "alerts" and len(parts) == 3:
            # alerts:page:filter
            page = int(parts[1])
            filter_type = parts[2]

            db_path = context.bot_data.get("db_path", "sas_monitor.db")
            from sas_monitor import AvailabilityDatabase
            adb = AvailabilityDatabase(db_path)

            try:
                # Get notifications with filter
                notifications = adb.get_notification_history(
                    limit=100, offset=0, filter_type=filter_type
                )

                # Rebuild page
                message, keyboard = build_alerts_page(notifications, page, filter_type)

                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            finally:
                adb.close()

        elif action == "search" and len(parts) == 3:
            origin, destination = parts[1], parts[2]
            api: SASAwardAPI = context.bot_data.get("api")
            
            # Show loading state
            await query.edit_message_text(
                f"🔍 Searching {origin} → {destination}...",
                parse_mode=ParseMode.HTML
            )
            
            # Query API
            api_data = api.get_availability(origin=origin, destination=destination)
            result_message = format_search_results(origin, destination, api_data, compact=False)
            
            # Create inline keyboard for actions
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"search:{origin}:{destination}"),
                    InlineKeyboardButton("📅 Calendar", callback_data=f"calendar:{origin}:{destination}"),
                    InlineKeyboardButton("📜 History", callback_data=f"history:{origin}:{destination}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                result_message,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            
        elif action == "calendar" and len(parts) == 3:
            origin, destination = parts[1], parts[2]
            api: SASAwardAPI = context.bot_data.get("api")
            
            await query.edit_message_text(
                f"📅 Loading calendar for {origin} → {destination}...",
                parse_mode=ParseMode.HTML
            )
            
            # Fetch data
            api_data = api.get_availability(origin=origin, destination=destination)
            
            if not api_data:
                await query.edit_message_text(
                    f"ℹ️ No data found for {origin} → {destination}",
                    parse_mode=ParseMode.HTML
                )
                return
            
            dest_data = api_data[0]
            city_name = dest_data.get("cityName", destination)
            
            # Build calendar grid
            message = f"📅 <b>Calendar: {origin} → {city_name}</b>\n\n"
            message += "<b>Legend:</b> 🟥 None | 💺 Economy | ⭐ Premium | 💎 Business\n\n"
            
            for direction_key, direction_label in [("outbound", "OUTBOUND"), ("inbound", "RETURN")]:
                direction_data = dest_data.get("availability", {}).get(direction_key, [])
                if not direction_data:
                    continue
                
                message += f"<b>{direction_label}:</b>\n"
                by_month = {}
                for avail in sorted(direction_data, key=lambda x: x.get("date", "")):
                    date = avail.get("date", "")
                    if not date:
                        continue
                    month_key = date[:7]
                    if month_key not in by_month:
                        by_month[month_key] = []
                    
                    if avail.get("AB", 0) > 0:
                        by_month[month_key].append("💎")
                    elif avail.get("AP", 0) > 0:
                        by_month[month_key].append("⭐")
                    elif avail.get("AG", 0) > 0:
                        by_month[month_key].append("💺")
                    else:
                        by_month[month_key].append("🟥")
                
                for month_name, emojis in by_month.items():
                    message += f"<code>{month_name}:</code> {''.join(emojis)}\n"
                message += "\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Search", callback_data=f"search:{origin}:{destination}"),
                    InlineKeyboardButton("📜 History", callback_data=f"history:{origin}:{destination}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
        elif action == "history" and len(parts) == 3:
            origin, destination = parts[1], parts[2]
            db_path = context.bot_data.get("db_path", "sas_monitor.db")
            
            from sas_monitor import AvailabilityDatabase
            adb = AvailabilityDatabase(db_path)
            
            try:
                history = adb.get_release_history(origin, destination)
                if not history:
                    await query.edit_message_text(
                        f"ℹ️ No release history found for {origin} → {destination}",
                        parse_mode=ParseMode.HTML
                    )
                    return
                
                message = f"📜 <b>Release History: {origin} → {destination}</b>\n\n"
                message += "<i>When seats were first detected:</i>\n\n"
                
                for date, cabin, seats, first_seen in history[:10]:  # Limit to 10
                    class_name = SASAwardAPI.CABIN_CODES.get(cabin, cabin)
                    emoji = CABIN_CLASSES.get(cabin, {}).get("emoji", "✈️")
                    try:
                        fs_dt = datetime.strptime(first_seen, "%Y-%m-%d %H:%M:%S")
                        fs_display = fs_dt.strftime("%b %d, %H:%M")
                    except:
                        fs_display = first_seen
                    message += f"📅 <b>{date}</b>\n  {emoji} {class_name}: {seats} | ⏰ {fs_display}\n\n"
                
                keyboard = [
                    [
                        InlineKeyboardButton("🔍 Search", callback_data=f"search:{origin}:{destination}"),
                        InlineKeyboardButton("📅 Calendar", callback_data=f"calendar:{origin}:{destination}"),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup
                )
            finally:
                adb.close()
                
        elif action == "status":
            db_path = context.bot_data.get("db_path", "sas_monitor.db")
            from sas_monitor import AvailabilityDatabase
            adb = AvailabilityDatabase(db_path)
            
            try:
                stats = adb.get_stats()
                last_scraped = stats.get("last_scraped", "Never")
                if last_scraped and last_scraped != "Never":
                    try:
                        ls_dt = datetime.strptime(last_scraped, "%Y-%m-%d %H:%M:%S")
                        last_scraped = ls_dt.strftime("%b %d, %H:%M:%S")
                    except:
                        pass
                
                message = "📊 <b>System Status Dashboard</b>\n\n"
                message += f"🕐 <b>Last Scan:</b> {last_scraped}\n"
                message += f"📁 <b>Total Records:</b> {stats.get('total_records', 0):,}\n"
                message += f"🛤️ <b>Unique Routes:</b> {stats.get('unique_routes', 0)}\n"
                message += f"📋 <b>Baseline Tickets:</b> {stats.get('baseline_tickets', 0):,}\n"
                message += f"📨 <b>Notifications Sent:</b> {stats.get('notifications_sent', 0)}\n"
                message += "\n✅ <i>Monitor is running</i>"
                
                await query.edit_message_text(message, parse_mode=ParseMode.HTML)
            finally:
                adb.close()
                
        elif action == "best":
            db_path = context.bot_data.get("db_path", "sas_monitor.db")
            from sas_monitor import AvailabilityDatabase
            adb = AvailabilityDatabase(db_path)
            
            try:
                best_bets = adb.get_best_bets(limit=10)
                if not best_bets:
                    await query.edit_message_text(
                        "ℹ️ No Business Class availability found.",
                        parse_mode=ParseMode.HTML
                    )
                    return
                
                message = "💎 <b>Best Bets: Business Class</b>\n\n"
                for origin, destination, date, seats in best_bets:
                    message += f"💼 <b>{origin} → {destination}</b>\n  📅 {date}: <b>{seats}</b> seats\n\n"
                
                await query.edit_message_text(
                    message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            finally:
                adb.close()
                
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}",
            parse_mode=ParseMode.HTML
        )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see available commands.",
        parse_mode=ParseMode.HTML
    )


# ============================================================================
# Bot Application
# ============================================================================

class SASAwardBot:
    """Interactive Telegram bot for SAS award searches."""

    def __init__(self, config: Config):
        self.config = config
        self.api = SASAwardAPI(config)

        if not config.telegram_bot_token:
            raise ValueError("Bot token not configured")

        # Initialize bot application with post_init callback
        self.application = (
            Application.builder()
            .token(config.telegram_bot_token)
            .post_init(self.post_init)
            .build()
        )

        # Store API client in bot_data for handlers to access
        self.application.bot_data["api"] = self.api
        self.application.bot_data["db_path"] = config.db_path

        # Register command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("notify", notify_command))
        self.application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        self.application.add_handler(CommandHandler("search", search_command))
        self.application.add_handler(CommandHandler("history", history_command))
        self.application.add_handler(CommandHandler("best", best_command))
        self.application.add_handler(CommandHandler("calendar", calendar_command))
        self.application.add_handler(CommandHandler("catalogue", catalogue_command))
        self.application.add_handler(CommandHandler("tickets", tickets_command))
        self.application.add_handler(CommandHandler("sales", sales_command))
        self.application.add_handler(CommandHandler("velocity", velocity_command))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("alerts", alerts_command))

        # Register callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(callback_handler))

        # Handle unknown commands via MessageHandler
        from telegram.ext import MessageHandler
        self.application.add_handler(
            MessageHandler(filters.COMMAND, unknown_command)
        )

        logger.info("Bot initialized successfully")

    async def post_init(self, application):
        """Set bot commands after initialization."""
        commands = [
            ("start", "Welcome message & quick buttons"),
            ("notify", "Subscribe to notifications"),
            ("unsubscribe", "Stop receiving notifications"),
            ("search", "Search for availability (OSL BKK)"),
            ("catalogue", "Browse all tracked tickets"),
            ("tickets", "View tracked tickets (OSL-BKK)"),
            ("sales", "Fastest selling tickets history"),
            ("velocity", "Hottest tickets (booking fast)"),
            ("calendar", "Calendar view (OSL BKK)"),
            ("history", "Release history (OSL BKK)"),
            ("best", "Best Business Class availability"),
            ("stats", "Enhanced statistics dashboard"),
            ("status", "System health dashboard"),
            ("help", "Show all commands"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands registered with Telegram")

    def run(self):
        """Start the bot with polling."""
        logger.info("Starting SAS EuroBonus Award Search Bot")
        logger.info("Bot is running. Press Ctrl+C to stop.")

        try:
            # Run bot with polling
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True  # Ignore old updates on startup
            )
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SAS EuroBonus Interactive Telegram Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python telegram_bot.py
  python telegram_bot.py --config config.json

Users can then interact with the bot:
  /start - Welcome message
  /help - Show help
  /search OSL BKK - Search for award availability
"""
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to JSON config file (default: config.json)"
    )

    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        logger.info("Please create config.json with bot token and other settings")
        sys.exit(1)

    try:
        config = Config.from_file(str(config_path))
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    if not config.telegram_bot_token:
        logger.error("telegram_bot_token not set in config")
        sys.exit(1)

    # Initialize and run bot
    try:
        bot = SASAwardBot(config)
        bot.run()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
