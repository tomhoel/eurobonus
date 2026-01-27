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
from sas_monitor import SASAwardAPI, Config

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
    - OSL - BKK
    - OSL-BKK
    - OSL BKK
    - osl bkk
    - OSL BKK July (with month)
    - OSL BKK 2026-03 (with month)

    Returns:
        Tuple of (origin, destination, month) or None if invalid
    """
    # Remove command prefix if present
    text = re.sub(r'^/(search|history|calendar)\s+', '', text, flags=re.IGNORECASE)

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

    # Extract airport codes (3 letters)
    codes = re.findall(r'\b([A-Za-z]{3})\b', text)

    if len(codes) < 2:
        return None

    origin, destination = [code.upper() for code in codes[:2]]

    # Validate against known airports
    if origin not in AIRPORT_NAMES or destination not in AIRPORT_NAMES:
        return None

    return origin, destination, month


# ============================================================================
# Message Formatters
# ============================================================================

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

<b>Supported Origins:</b>
🇳🇴 OSL - Oslo
🇫🇷 CDG - Paris
🇩🇰 CPH - Copenhagen
🇳🇱 AMS - Amsterdam

<b>Supported Destinations:</b>
🇹🇭 BKK - Bangkok
🇯🇵 NRT - Tokyo Narita
🇯🇵 HND - Tokyo Haneda
🇯🇵 KIX - Osaka
🇨🇳 PVG - Shanghai
🇨🇳 PEK - Beijing
🇻🇳 SGN - Ho Chi Minh City
🇻🇳 HAN - Hanoi
🇸🇬 SIN - Singapore

<b>Commands:</b>
/search OSL BKK - Search for availability
/search OSL BKK July - Search with month filter
/tickets - View all tracked tickets
/tickets OSL-BKK - View specific route tickets
/velocity - See hottest tickets (booking fast)
/calendar OSL BKK - Emoji grid calendar view
/history OSL BKK - Show release history
/best - Best business class availability
/stats - Enhanced statistics dashboard
/status - System health dashboard
/help - Show this help message

<b>Examples:</b>
<code>/search OSL BKK</code>
<code>/tickets OSL-BKK 2026-02</code>
<code>/velocity</code>
<code>/calendar CPH NRT</code>
<code>/stats</code>
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /search command.

    Parses route, queries SAS API, and returns formatted results.
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

    # Send "searching" message
    month_text = f" ({month[:4]}-{month[4:]})" if month else ""
    status_msg = await update.message.reply_text(
        f"🔍 Searching {origin} → {destination}{month_text}...",
        parse_mode=ParseMode.HTML
    )

    try:
        # Get API client from context (passed during initialization)
        api: SASAwardAPI = context.bot_data.get("api")

        if not api:
            raise Exception("API client not initialized")

        # Query SAS API (pass month if specified)
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

        for idx, (origin, destination, date, cabin, curr_avail,
                  total_booked, velocity) in enumerate(hot_tickets, 1):
            dest_name = AIRPORT_NAMES.get(destination, destination)
            class_name = CABIN_CLASSES.get(cabin, {}).get("name", cabin)

            # Determine fire emoji intensity
            if velocity >= 1.5:
                fire = "🔥🔥🔥"
            elif velocity >= 1.0:
                fire = "🔥🔥"
            elif velocity >= 0.5:
                fire = "🔥"
            else:
                fire = ""

            message += f"{idx}. <b>{origin} → {dest_name}</b> {date}\n"
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
        hot_count = len([t for t in hot_tickets if t[6] >= 0.5])  # velocity >= 0.5
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

        # Group by route
        by_route = {}
        for (orig, destination, date, cabin, max_issued, curr_avail,
             total_booked, first_seen, velocity) in tickets:
            route_key = (orig, destination)
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

        for (orig, destination), route_tickets in sorted(by_route.items())[:10]:  # Limit to 10 routes
            dest_name = AIRPORT_NAMES.get(destination, destination)
            message += f"✈️ <b>{orig} → {dest_name}</b>\n\n"

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
        if action == "search" and len(parts) == 3:
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
        self.application.add_handler(CommandHandler("search", search_command))
        self.application.add_handler(CommandHandler("history", history_command))
        self.application.add_handler(CommandHandler("best", best_command))
        self.application.add_handler(CommandHandler("calendar", calendar_command))
        self.application.add_handler(CommandHandler("tickets", tickets_command))
        self.application.add_handler(CommandHandler("velocity", velocity_command))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("status", status_command))
        
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
            ("search", "Search for availability (OSL BKK)"),
            ("tickets", "View tracked tickets (OSL-BKK)"),
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
