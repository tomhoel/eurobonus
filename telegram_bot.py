#!/usr/bin/env python3
"""
SAS EuroBonus Telegram Bot - Search & Subscription Interface

Commands:
- /start: Intro
- /search [Origin]-[Dest]: Search award flights with interactive calendar
- /search OSL-* or *-BKK: Multi-destination search
- /search OSL-BKK cheap: Find cheapest across all dates
- /search OSL-* 50000pts: Search within points budget
- /subscribe [Origin] [Dest] [Cabin]: Add alert
- /unsubscribe [ID]: Remove alert
- /status: Health check
"""

import os
import sys
import logging
import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from sas_monitor import Config, AvailabilityDatabase
from sas_search_api import SASSearchEngine, AvailabilityDate, FlightOffer, PartnerFlight

# Logger setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Region definitions for destination grouping
REGIONS = {
    "Scandinavia": ["OSL", "ARN", "CPH", "BGO", "TRD", "SVG", "GOT", "BLL", "AAL", "AAR", "TOS", "BOO", "KRS", "HAU", "AES", "MOL", "KSU", "SDN", "EVE", "BDU", "LYR"],
    "Europe": ["LHR", "CDG", "AMS", "FRA", "MUC", "ZRH", "VIE", "BRU", "DUB", "MAN", "BCN", "MAD", "LIS", "FCO", "MXP", "ATH", "IST", "WAW", "PRG", "BUD", "HEL", "TLL", "RIX", "VNO", "GDN", "WRO", "KRK", "NCE", "GVA", "HAM", "DUS", "BER", "EDI", "GLA"],
    "Asia": ["BKK", "HKT", "KBV", "HND", "NRT", "SIN", "HKG", "PVG", "PEK", "ICN", "DEL", "BOM", "KUL", "CGK", "MNL", "TPE", "SGN", "HAN"],
    "Americas": ["JFK", "EWR", "LAX", "SFO", "MIA", "ORD", "BOS", "IAD", "YYZ", "YVR", "YUL", "GRU", "EZE", "MEX", "PTY"],
    "Middle East": ["DXB", "DOH", "AUH", "TLV", "AMM", "CAI", "JED", "RUH"],
    "Africa": ["JNB", "CPT", "NBO", "ADD", "CMN", "LOS", "ACC"],
    "Oceania": ["SYD", "MEL", "AKL", "BNE", "PER"],
}

# Major SAS hubs for reverse lookups (finding origins that fly TO a destination)
REVERSE_SEARCH_HUBS = [
    "OSL", "CPH", "ARN", "BGO", "TRD", "SVG",  # Scandinavia
    "LHR", "FRA", "AMS", "CDG", "MUC", "ZRH",  # Europe
    "JFK", "EWR", "LAX", "MIA", "SFO",         # Americas
]

# SkyTeam partner airline code -> name mapping
SKYTEAM_AIRLINES = {
    "AF": "Air France", "KL": "KLM", "DL": "Delta",
    "KE": "Korean Air", "MU": "China Eastern", "CZ": "China Southern",
    "AR": "Aerolineas Argentinas", "AM": "Aeromexico",
    "CI": "China Airlines", "GA": "Garuda Indonesia", "ME": "MEA",
    "RO": "TAROM", "VN": "Vietnam Airlines", "SV": "Saudia",
    "OK": "Czech Airlines", "UX": "Air Europa", "AZ": "ITA Airways",
    "SK": "SAS", "XQ": "SunExpress", "EY": "Etihad",
}

def get_region(airport_code: str) -> str:
    """Get region for an airport code."""
    for region, codes in REGIONS.items():
        if airport_code in codes:
            return region
    return "Other"


class SubscriptionBot:
    # Cabin mappings
    CABIN_CODES = {"ECONOMY": "AG", "PREMIUM": "AP", "BUSINESS": "AB"}
    CABIN_NAMES = {"AG": "Economy", "AP": "Premium", "AB": "Business"}

    # Sort options
    SORT_OPTIONS = {
        "date": ("📅 Date", lambda d: d.date),
        "seats": ("💺 Seats", lambda d: -(d.economy_seats + d.premium_seats + d.business_seats)),
        "biz": ("👔 Business", lambda d: -d.business_seats),
    }

    def __init__(self):
        self.config = Config.from_env()
        self.db = AvailabilityDatabase(self.config.db_path)

        # Initialize search engine with session if available
        possible_paths = [
            "sas_session.json",
            "data/sas_session.json",
            os.path.join(os.path.dirname(__file__), "sas_session.json"),
            self.config.db_path.replace("sas_monitor.db", "sas_session.json"),
        ]

        session_path = None
        for path in possible_paths:
            if os.path.exists(path):
                session_path = path
                break

        try:
            if session_path:
                self.search_engine = SASSearchEngine(cookies_file=session_path)
                logger.info(f"Search engine initialized with session from {session_path}")
            else:
                self.search_engine = SASSearchEngine()
                logger.warning("No session file found, using anonymous mode")
        except Exception as e:
            logger.warning(f"Failed to load session, using anonymous: {e}")
            self.search_engine = SASSearchEngine()

        # Cache for search results
        self.search_cache: Dict[str, Dict[str, Any]] = {}

        # Global deals cache (shared across all users)
        self.deals_cache: Dict[str, Any] = {
            "data": [],
            "timestamp": 0,
            "ttl": 600,  # 10 minutes
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a welcome message."""
        await update.message.reply_text(
            "✈️ **SAS EuroBonus Award Finder**\n\n"
            "Search & monitor award seats 24/7.\n\n"
            "**Search Commands:**\n"
            "`/search OSL-BKK` - Search route\n"
            "`/search OSL-BKK Feb` - Specific month\n"
            "`/search OSL-BKK business` - Filter cabin\n"
            "`/search OSL-BKK cheap` - Find cheapest\n"
            "`/search OSL-BKK direct` - Direct flights only\n"
            "`/search OSL-*` - All destinations from OSL\n"
            "`/search *-BKK` - All origins to BKK\n"
            "`/search OSL-* 50000pts` - Within budget\n\n"
            "**Partner Airlines (SkyTeam):**\n"
            "`/partner OSL-NRT` - Partner flights next 14 days\n"
            "`/partner OSL-BKK business` - Business class partners\n"
            "`/partner CPH-CDG Feb` - Specific month\n\n"
            "**Quick Finds:**\n"
            "`/deals` - Hot deals right now\n"
            "`/deals business` - Business class deals\n\n"
            "**Alerts:**\n"
            "`/subscribe OSL BKK Business` - Add alert\n"
            "`/subscriptions` - List alerts\n"
            "`/unsubscribe [ID]` - Remove alert\n"
            "`/status` - System health",
            parse_mode="Markdown"
        )

    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new subscription."""
        chat_id = str(update.effective_chat.id)
        args = context.args

        if len(args) < 2:
            await update.message.reply_text(
                "Usage: `/subscribe [Origin] [Dest] [Cabin] [bonus]`\n\n"
                "Examples:\n"
                "`/subscribe OSL BKK` - Any cabin, any ticket\n"
                "`/subscribe OSL BKK Business` - Business only\n"
                "`/subscribe OSL BKK bonus` - Any cabin, bonus tickets only\n"
                "`/subscribe OSL BKK Business bonus` - Business bonus only\n\n"
                "🌟 **Bonus tickets** = Fixed points (30k eco, 45k prem, 60k biz)\n"
                "Can use AMEX 2-for-1 voucher!",
                parse_mode="Markdown"
            )
            return

        origin = args[0].upper()
        dest = args[1].upper()

        # Parse remaining args for cabin and saver_only
        cabin = None
        saver_only = False
        valid_cabins = {"ECONOMY": "AG", "PREMIUM": "AP", "BUSINESS": "AB", "AG": "AG", "AP": "AP", "AB": "AB", "ECO": "AG", "PREM": "AP", "BIZ": "AB"}

        for arg in args[2:]:
            arg_upper = arg.upper()
            if arg_upper in ("BONUS", "SAVER"):
                saver_only = True
            elif arg_upper in valid_cabins:
                cabin = arg_upper

        cabin_code = valid_cabins.get(cabin) if cabin else None

        if self.db.add_subscription(chat_id, origin, dest, cabin_code, saver_only):
            c_text = cabin or "ANY"
            saver_text = " 🌟BONUS" if saver_only else ""
            await update.message.reply_text(f"✅ Alert added: **{origin} → {dest}** ({c_text}{saver_text})\nI'll notify you when seats appear.", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ You already have this exact subscription.")

    async def list_subscriptions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List active subscriptions."""
        chat_id = str(update.effective_chat.id)
        subs = self.db.get_subscriptions(chat_id)

        if not subs:
            await update.message.reply_text("You have no active alerts. Use `/subscribe` to add one.", parse_mode="Markdown")
            return

        msg = "**Your Active Alerts:**\n\n"
        for s in subs:
            cabin = s["cabin_filter"] or "ANY"
            saver = s["saver_only"] if "saver_only" in s.keys() else 0
            saver_text = " 🌟BONUS" if saver else ""
            msg += f"🆔 `{s['id']}`: {s['origin']} ➡️ {s['destination']} ({cabin}{saver_text})\n"

        msg += "\nTo remove: `/unsubscribe [ID]`"
        await update.message.reply_text(msg, parse_mode="Markdown")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a subscription."""
        chat_id = str(update.effective_chat.id)
        args = context.args

        if not args:
            await update.message.reply_text("Usage: `/unsubscribe [ID]` (find ID with `/subscriptions`)")
            return

        try:
            sub_id = int(args[0])
            if self.db.remove_subscription(sub_id, chat_id):
                await update.message.reply_text(f"🗑 Alert ID {sub_id} removed.")
            else:
                await update.message.reply_text(f"❌ Could not find alert ID {sub_id}.")
        except ValueError:
            await update.message.reply_text("ID must be a number.")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system status (compact view)."""
        await self._send_status_view(update.message, compact=True)

    async def _send_status_view(self, message, compact: bool = True, edit: bool = False):
        """Send status view (compact or expanded)."""
        stats = self.db.get_stats()
        session_valid = self.search_engine.session is not None

        # Calculate cache freshness
        cache_age = "N/A"
        if stats["last_cache_update"]:
            try:
                last_update = datetime.strptime(stats["last_cache_update"], "%Y-%m-%d %H:%M:%S")
                delta = datetime.now() - last_update
                if delta.total_seconds() < 60:
                    cache_age = f"{int(delta.total_seconds())}s ago"
                elif delta.total_seconds() < 3600:
                    cache_age = f"{int(delta.total_seconds() // 60)}m ago"
                else:
                    cache_age = f"{int(delta.total_seconds() // 3600)}h ago"
            except:
                cache_age = "Unknown"

        if compact:
            # Compact view
            routes_str = f"{stats['routes']} routes" if stats['routes'] > 0 else "no routes"
            msg = (
                f"🟢 **System Status**\n\n"
                f"📊 **Subscriptions**\n"
                f"• Active: {stats['subscriptions']} alerts across {routes_str}\n"
                f"• Notifications: {stats['notifications_today']} today | {stats['notifications_week']} this week\n\n"
                f"✈️ **Cache**: {stats['cached_dates']} dates tracked | Updated {cache_age}\n"
                f"🔐 **Session**: {'Valid ✅' if session_valid else 'Invalid ❌'}"
            )
            keyboard = [
                [
                    InlineKeyboardButton("📋 Details", callback_data="status:detail"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="status:refresh")
                ]
            ]
        else:
            # Expanded view
            routes_list = ", ".join([f"{r[0]}-{r[1]}" for r in stats['route_list']]) if stats['route_list'] else "None"
            seats_eco = stats['seats_by_cabin'].get('AG', 0) or 0
            seats_biz = stats['seats_by_cabin'].get('AB', 0) or 0
            seats_prem = stats['seats_by_cabin'].get('AP', 0) or 0

            msg = (
                f"🟢 **System Status**\n\n"
                f"📊 **Subscriptions & Alerts**\n"
                f"• Active: {stats['subscriptions']} alerts\n"
                f"• Routes: {routes_list}\n"
                f"• Notifications: {stats['notifications_today']} today | {stats['notifications_week']} this week\n\n"
                f"✈️ **Availability Cache**\n"
                f"• Dates tracked: {stats['cached_dates']}\n"
                f"• Seats: Eco {seats_eco:,} | Prem {seats_prem:,} | Biz {seats_biz:,}\n"
                f"• Last update: {cache_age}\n\n"
                f"⏱️ **Monitor**\n"
                f"• Tier 1 scan: hourly\n"
                f"• Tier 2 verify: every 15min\n\n"
                f"🔐 **Session**: {'Valid ✅' if session_valid else 'Invalid ❌'}"
            )
            keyboard = [
                [
                    InlineKeyboardButton("📋 Compact", callback_data="status:compact"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="status:refresh")
                ]
            ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        if edit:
            await message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

    # =========================================================================
    # DEALS - HOT AWARD AVAILABILITY
    # =========================================================================

    async def deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show hot deals - live scan of all SAS hubs."""
        # Parse optional cabin filter from args
        cabin_filter = None  # None = all, "eco", "prem", "biz"
        if context.args:
            arg = context.args[0].upper()
            filter_map = {
                "ECONOMY": "eco", "ECO": "eco", "AG": "eco",
                "PREMIUM": "prem", "PREM": "prem", "AP": "prem",
                "BUSINESS": "biz", "BIZ": "biz", "AB": "biz",
            }
            cabin_filter = filter_map.get(arg)

        # Check cache freshness
        now = time.time()
        cache_age = now - self.deals_cache["timestamp"]
        if self.deals_cache["data"] and cache_age < self.deals_cache["ttl"]:
            # Use cached data
            deals_data = self.deals_cache["data"]
        else:
            # Fresh fetch
            status_msg = await update.message.reply_text(
                "🔍 Scanning hubs for deals...\n"
                "Checking OSL, CPH, ARN (3 API calls)"
            )
            try:
                deals_data = await self._fetch_live_deals()
                if not deals_data:
                    await status_msg.edit_text(
                        "❌ No deals found. The API might be temporarily unavailable.\n"
                        "Try again in a few minutes."
                    )
                    return
                await status_msg.delete()
            except Exception as e:
                logger.error(f"Deals fetch error: {e}", exc_info=True)
                await status_msg.edit_text(f"❌ Failed to fetch deals: {str(e)[:100]}")
                return

        # Filter + sort
        filtered = self._filter_deals(deals_data, cabin_filter)

        if not filtered:
            filter_name = {"eco": "Economy", "prem": "Premium", "biz": "Business"}.get(cabin_filter, "")
            await update.message.reply_text(
                f"🔍 No {filter_name} deals found across hubs.\n"
                f"Try `/deals` to see all cabins.",
                parse_mode="Markdown"
            )
            return

        text = self._format_deals_message(filtered, cabin_filter)
        keyboard = self._build_deals_keyboard(filtered, cabin_filter)

        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    async def _fetch_live_deals(self) -> List[Dict[str, Any]]:
        """Fetch live availability from all 3 SAS hubs."""
        hubs = ["OSL", "CPH", "ARN"]
        scandinavian_codes = set(REGIONS.get("Scandinavia", []))
        today = datetime.now().strftime("%Y-%m-%d")

        # Aggregate per (origin, dest)
        route_data: Dict[str, Dict[str, Any]] = {}

        for hub in hubs:
            try:
                raw = self.search_engine.get_availability_calendar(
                    origin=hub, destination=""
                )
                if not raw:
                    continue

                for dest in raw:
                    dest_code = dest.get("airportCode") or dest.get("iataCode", "")
                    if not dest_code:
                        continue

                    # Skip intra-Scandinavian routes (not interesting deals)
                    if dest_code in scandinavian_codes:
                        continue

                    availability = dest.get("availability", {})
                    outbound = availability.get("outbound", [])

                    route_key = f"{hub}:{dest_code}"
                    if route_key not in route_data:
                        route_data[route_key] = {
                            "origin": hub,
                            "destination": dest_code,
                            "region": get_region(dest_code),
                            "total_eco": 0,
                            "total_prem": 0,
                            "total_biz": 0,
                            "date_count": 0,
                            "biz_date_count": 0,
                            "sample_dates": [],
                        }

                    entry = route_data[route_key]

                    for day in outbound:
                        date_str = day.get("date", "")
                        if date_str < today:
                            continue

                        eco = int(day.get("AG", 0) or 0)
                        prem = int(day.get("AP", 0) or 0)
                        biz = int(day.get("AB", 0) or 0)

                        if eco + prem + biz > 0:
                            entry["total_eco"] += eco
                            entry["total_prem"] += prem
                            entry["total_biz"] += biz
                            entry["date_count"] += 1
                            if biz > 0:
                                entry["biz_date_count"] += 1
                            if len(entry["sample_dates"]) < 10:
                                entry["sample_dates"].append(date_str)

                await asyncio.sleep(0.3)  # Rate limit between hubs
            except Exception as e:
                logger.warning(f"Failed to fetch deals for hub {hub}: {e}")
                continue

        deals = list(route_data.values())

        # Sort by total seats (all cabins combined)
        deals.sort(key=lambda d: -(d["total_eco"] + d["total_prem"] + d["total_biz"]))

        # Update cache
        self.deals_cache["data"] = deals
        self.deals_cache["timestamp"] = time.time()

        return deals

    def _filter_deals(self, deals: List[Dict], cabin_filter: Optional[str]) -> List[Dict]:
        """Filter deals by cabin and return top 10."""
        if not cabin_filter:
            return deals[:10]

        if cabin_filter == "eco":
            filtered = [d for d in deals if d["total_eco"] > 0]
            filtered.sort(key=lambda d: -d["total_eco"])
        elif cabin_filter == "prem":
            filtered = [d for d in deals if d["total_prem"] > 0]
            filtered.sort(key=lambda d: -d["total_prem"])
        elif cabin_filter == "biz":
            filtered = [d for d in deals if d["total_biz"] > 0]
            filtered.sort(key=lambda d: -d["total_biz"])
        else:
            filtered = deals

        return filtered[:10]

    def _format_deals_message(self, deals: List[Dict], cabin_filter: Optional[str]) -> str:
        """Format deals into a Telegram message."""
        filter_label = {
            "eco": "Economy", "prem": "Premium", "biz": "Business"
        }.get(cabin_filter, "All Cabins")

        header = f"🔥 *Hot Deals — {filter_label}*\n"
        header += "_Best availability across OSL, CPH, ARN_\n\n"

        lines = []
        for i, deal in enumerate(deals, 1):
            route = f"{deal['origin']} → {deal['destination']}"
            region = deal.get("region", "Other")

            # Seat summary
            seat_parts = []
            if deal["total_eco"]:
                seat_parts.append(f"💺{deal['total_eco']}")
            if deal["total_prem"]:
                seat_parts.append(f"💎{deal['total_prem']}")
            if deal["total_biz"]:
                seat_parts.append(f"👔{deal['total_biz']}")
            seats_str = " · ".join(seat_parts) if seat_parts else "—"

            # Date summary
            date_count = deal["date_count"]
            sample = deal.get("sample_dates", [])
            if sample:
                shown = [d[5:] for d in sample[:3]]  # MM-DD
                date_str = ", ".join(shown)
                if len(sample) > 3:
                    date_str += f" +{len(sample) - 3}"
            else:
                date_str = "—"

            lines.append(
                f"{i}. *{route}* ({region})\n"
                f"   {seats_str} · {date_count} dates\n"
                f"   🗓 {date_str}"
            )

        footer = "\n\n💺 Go · 💎 Plus · 👔 Biz\n💡 _Tap a route to see full calendar_"

        return header + "\n".join(lines) + footer

    def _build_deals_keyboard(self, deals: List[Dict], cabin_filter: Optional[str]) -> List[List[InlineKeyboardButton]]:
        """Build inline keyboard for deals view."""
        keyboard = []

        # Route buttons (top 5)
        route_buttons = []
        for deal in deals[:5]:
            origin = deal["origin"]
            dest = deal["destination"]
            label = f"{origin}-{dest}"
            callback = f"dest:f:{origin}:{dest}"
            route_buttons.append(InlineKeyboardButton(label, callback_data=callback))

        # Split into rows of 3
        for i in range(0, len(route_buttons), 3):
            keyboard.append(route_buttons[i:i + 3])

        # Cabin filter buttons
        active = cabin_filter or "all"
        eco_label = "💺 Eco ✓" if active == "eco" else "💺 Eco"
        prem_label = "💎 Plus ✓" if active == "prem" else "💎 Plus"
        biz_label = "👔 Biz ✓" if active == "biz" else "👔 Biz"
        all_label = "All ✓" if active == "all" else "All"

        keyboard.append([
            InlineKeyboardButton(eco_label, callback_data="deals:eco"),
            InlineKeyboardButton(prem_label, callback_data="deals:prem"),
            InlineKeyboardButton(biz_label, callback_data="deals:biz"),
            InlineKeyboardButton(all_label, callback_data="deals:all"),
        ])

        # Refresh button
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="deals:refresh"),
        ])

        return keyboard

    # =========================================================================
    # PARTNER (SKYTEAM) SEARCH
    # =========================================================================

    async def partner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for SkyTeam partner award flights."""
        chat_id = str(update.effective_chat.id)

        if not context.args:
            await update.message.reply_text(
                "🌐 **SkyTeam Partner Award Search**\n\n"
                "Search Air France, KLM, Delta, Korean Air & more.\n\n"
                "**Usage:**\n"
                "`/partner OSL-NRT` - Next 14 days\n"
                "`/partner OSL-NRT Feb` - Specific month\n"
                "`/partner CPH-BKK business` - Business class\n"
                "`/partner OSL-CDG Feb economy` - Combined\n\n"
                "Requires active SAS EuroBonus session.",
                parse_mode="Markdown"
            )
            return

        parsed = self._parse_search_query(context.args)
        if parsed.get("error"):
            await update.message.reply_text(parsed["error"], parse_mode="Markdown")
            return

        if parsed.get("multi_dest"):
            await update.message.reply_text(
                "Partner search doesn't support wildcard routes.\n"
                "Use a specific route: `/partner OSL-NRT`",
                parse_mode="Markdown"
            )
            return

        # Check session
        if not self.search_engine.session.headers.get("sas-user-session-id"):
            await update.message.reply_text(
                "**Session required** for partner search.\n\n"
                "The SAS partner API needs an authenticated session.\n"
                "Run `capture_session.py` to refresh credentials.",
                parse_mode="Markdown"
            )
            return

        await self._search_partner(update, chat_id, parsed)

    def _build_partner_date_list(self, month_filter: Optional[str] = None) -> List[str]:
        """Build list of dates to scan for partner search."""
        import calendar as cal_mod
        now = datetime.now()

        if month_filter:
            year = int(month_filter[:4])
            month = int(month_filter[4:6])
            days_in_month = cal_mod.monthrange(year, month)[1]
            all_days = [
                f"{year}-{month:02d}-{d:02d}"
                for d in range(1, days_in_month + 1)
            ]
            # Skip past dates
            today_str = now.strftime("%Y-%m-%d")
            all_days = [d for d in all_days if d > today_str]
            # Sample every other day if too many
            if len(all_days) > 15:
                all_days = all_days[::2]
            return all_days[:15]
        else:
            # Default: next 14 days
            return [
                (now + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(1, 15)
            ]

    async def _search_partner(self, update: Update, chat_id: str, parsed: Dict):
        """Scan multiple dates for partner/award flights."""
        origin = parsed["origin"]
        destination = parsed["destination"]
        month_filter = parsed.get("month")
        cabin_filter = parsed.get("cabin_filter")

        dates_to_scan = self._build_partner_date_list(month_filter)

        status_msg = await update.message.reply_text(
            f"🌐 **Partner: {origin} → {destination}**\n"
            f"Scanning {len(dates_to_scan)} dates for award flights...\n"
            f"Progress: 0/{len(dates_to_scan)}"
        )

        all_flights: List[PartnerFlight] = []
        use_fallback = False
        rate_limit_count = 0

        # Try partner API on first date to check auth
        try:
            test_raw = self.search_engine.get_partner_awards(
                origin, destination, dates_to_scan[0]
            )
            if test_raw and test_raw.get("outboundFlights"):
                parsed_flights = self.search_engine.parse_partner_flights(
                    test_raw, origin, destination, dates_to_scan[0]
                )
                all_flights.extend(parsed_flights)
        except Exception as e:
            if "401" in str(e) or "403" in str(e):
                use_fallback = True
                logger.info("Partner API auth failed, falling back to offers API")
                await status_msg.edit_text(
                    f"🌐 **{origin} → {destination}**\n"
                    f"Using award search (partner API needs session refresh)...\n"
                    f"Progress: 0/{len(dates_to_scan)}"
                )
            else:
                logger.warning(f"Partner API error: {e}")

        start_idx = 0 if use_fallback else 1  # Skip first date if already checked

        for i, date in enumerate(dates_to_scan[start_idx:], start=start_idx):
            try:
                if use_fallback:
                    # Use regular offers API (works with session cookies)
                    offers = self.search_engine.search_flights(
                        origin=origin, destination=destination,
                        date=date, cabin_filter=cabin_filter
                    )
                    # Convert FlightOffer objects to PartnerFlight format
                    seen_flights = set()
                    for o in offers:
                        # Build route and carrier info from segments
                        airports = []
                        carriers = []
                        carrier_names = []
                        for s in o.segments:
                            airports.append(s.departure_airport)
                            code = s.carrier or s.carrier_name or "SK"
                            name = s.carrier_name or SKYTEAM_AIRLINES.get(code, code)
                            if code and code not in carriers:
                                carriers.append(code)
                            if name and name not in carrier_names:
                                carrier_names.append(name)
                        if o.segments:
                            airports.append(o.segments[-1].arrival_airport)

                        route = " -> ".join(airports)
                        flight_key = f"{date}_{route}_{o.cabin_class}"
                        if flight_key in seen_flights:
                            continue
                        seen_flights.add(flight_key)

                        all_flights.append(PartnerFlight(
                            date=date,
                            departure_time=o.segments[0].departure_time if o.segments else "",
                            arrival_time=o.segments[-1].arrival_time if o.segments else "",
                            origin=origin,
                            destination=destination,
                            route=route,
                            carriers=carriers,
                            carrier_names=carrier_names,
                            stops=o.stops,
                            total_duration_minutes=o.total_duration_minutes,
                            cabins=[{
                                "cabin": o.cabin_class,
                                "points": o.points,
                                "cash": o.taxes,
                                "seats": o.available_seats,
                            }],
                        ))
                else:
                    # Use partner API
                    raw = self.search_engine.get_partner_awards(origin, destination, date)
                    if raw and raw.get("outboundFlights"):
                        parsed_flights = self.search_engine.parse_partner_flights(
                            raw, origin, destination, date
                        )
                        if cabin_filter:
                            parsed_flights = [
                                f for f in parsed_flights
                                if any(c["cabin"] == cabin_filter for c in f.cabins)
                            ]
                        all_flights.extend(parsed_flights)

                # Update progress on every date
                await status_msg.edit_text(
                    f"🌐 {'Award' if use_fallback else 'Partner'}: {origin} → {destination}\n"
                    f"Progress: {i + 1}/{len(dates_to_scan)} | "
                    f"Found: {len(all_flights)} flight(s)"
                )

                await asyncio.sleep(0.5)

            except Exception as e:
                if "429" in str(e):
                    rate_limit_count += 1
                    if rate_limit_count >= 2:
                        break
                    await asyncio.sleep(30)
                else:
                    logger.warning(f"Partner scan error for {date}: {e}")
                    # Still update progress on errors
                    try:
                        await status_msg.edit_text(
                            f"🌐 {origin} → {destination}\n"
                            f"Progress: {i + 1}/{len(dates_to_scan)} | "
                            f"Found: {len(all_flights)} flight(s)"
                        )
                    except Exception:
                        pass
                    continue

        if not all_flights:
            await status_msg.edit_text(
                f"❌ No award flights found: {origin} → {destination}\n\n"
                f"Try `/search {origin}-{destination}` for calendar view.",
                parse_mode="Markdown"
            )
            return

        # Cache results (keep unfiltered copy for cabin toggling)
        self.search_cache[chat_id] = {
            "origin": origin,
            "destination": destination,
            "partner_flights": all_flights,
            "partner_flights_all": all_flights,  # unfiltered backup
            "cabin_filter": cabin_filter,
            "current_page": 0,
            "mode": "partner",
            "use_fallback": use_fallback,
        }

        await self._send_partner_view(status_msg, chat_id)

    async def _send_partner_view(self, message, chat_id: str, page: int = 0, edit: bool = True):
        """Render partner search results with inline keyboard."""
        cache = self.search_cache.get(chat_id)
        if not cache or cache.get("mode") != "partner":
            if edit:
                await message.edit_text("Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        flights = cache["partner_flights"]
        cabin_filter = cache.get("cabin_filter")

        PAGE_SIZE = 5
        total_pages = max(1, (len(flights) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        cache["current_page"] = page

        start = page * PAGE_SIZE
        page_flights = flights[start:start + PAGE_SIZE]

        # Collect all unique airlines across all results
        all_carriers = set()
        for f in flights:
            for name in f.carrier_names:
                all_carriers.add(name)
            for code in f.carriers:
                if code in SKYTEAM_AIRLINES:
                    all_carriers.add(SKYTEAM_AIRLINES[code])

        # Header
        header = f"🌐 **Partner Flights: {origin} → {destination}**\n"
        if all_carriers:
            header += f"Airlines: {', '.join(sorted(all_carriers))}\n"
        header += f"{len(flights)} flight(s)"
        if cabin_filter:
            cabin_label = {"ECONOMY": "Economy", "PREMIUM": "Premium", "BUSINESS": "Business"}.get(cabin_filter, cabin_filter)
            header += f" ({cabin_label})"
        if total_pages > 1:
            header += f" | Page {page + 1}/{total_pages}"
        header += "\n\n"

        # Body
        lines = []
        current_date = None
        cabin_emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔", "FIRST": "👑"}

        for f in page_flights:
            if f.date != current_date:
                if current_date is not None:
                    lines.append("")
                date_obj = datetime.strptime(f.date, "%Y-%m-%d")
                lines.append(f"**{date_obj.strftime('%a %d %b')}**")
                current_date = f.date

            carrier_display = [SKYTEAM_AIRLINES.get(c, c) for c in f.carriers]
            carrier_str = " / ".join(carrier_display)

            hours = f.total_duration_minutes // 60
            mins = f.total_duration_minutes % 60
            dur_str = f"{hours}h{mins:02d}m" if f.total_duration_minutes else ""
            stops_str = "Direct" if f.is_direct else f"{f.stops} stop{'s' if f.stops > 1 else ''}"

            lines.append(f"  ✈️ `{f.departure_time}→{f.arrival_time}` | {carrier_str}")
            detail_parts = [stops_str]
            if dur_str:
                detail_parts.append(dur_str)
            lines.append(f"     {f.route} | {' | '.join(detail_parts)}")

            for c in f.cabins:
                if cabin_filter and c["cabin"] != cabin_filter:
                    continue
                emoji = cabin_emoji.get(c["cabin"], "✈️")
                seats_str = f" | {c['seats']} seats" if c.get("seats") else ""
                lines.append(f"     {emoji} `{c['points']:,}` pts{seats_str}")

        body = "\n".join(lines)

        # Inline keyboard
        keyboard = []

        # Pagination
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"partner_page:{page - 1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"partner_page:{page + 1}"))
        if nav:
            keyboard.append(nav)

        # Date buttons for this page
        unique_dates = list(dict.fromkeys(f.date for f in page_flights))
        date_buttons = []
        for d in unique_dates:
            d_obj = datetime.strptime(d, "%Y-%m-%d")
            date_buttons.append(
                InlineKeyboardButton(d_obj.strftime("%d %b"), callback_data=f"partner_date:{d}")
            )
        if date_buttons:
            for i in range(0, len(date_buttons), 5):
                keyboard.append(date_buttons[i:i + 5])

        # Cabin filters
        keyboard.append([
            InlineKeyboardButton("💺 Eco", callback_data="partner_cabin:ECONOMY"),
            InlineKeyboardButton("💎 Plus", callback_data="partner_cabin:PREMIUM"),
            InlineKeyboardButton("👔 Biz", callback_data="partner_cabin:BUSINESS"),
            InlineKeyboardButton("All", callback_data="partner_cabin:ALL"),
        ])

        # Actions
        keyboard.append([
            InlineKeyboardButton("🔄 Refresh", callback_data="partner_refresh"),
            InlineKeyboardButton("🔔 Alert", callback_data="partner_alert"),
        ])
        keyboard.append([
            InlineKeyboardButton("📅 SAS Search", callback_data="partner_to_sas"),
        ])

        text = header + body
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated. Use page navigation._"

        reply_markup = InlineKeyboardMarkup(keyboard)
        if edit:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _send_partner_date_detail(self, message, chat_id: str, date: str, flights: List[PartnerFlight]):
        """Show detailed partner flights for a specific date."""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        header = f"🌐 **Partner Flights — {date_obj.strftime('%A, %d %B %Y')}**\n\n"

        lines = []
        cabin_emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔", "FIRST": "👑"}

        for i, f in enumerate(flights):
            carrier_display = [SKYTEAM_AIRLINES.get(c, c) for c in f.carriers]
            carrier_str = " / ".join(carrier_display)

            hours = f.total_duration_minutes // 60
            mins = f.total_duration_minutes % 60
            dur_str = f"{hours}h{mins:02d}m" if f.total_duration_minutes else ""
            stops_str = "Direct" if f.is_direct else f"{f.stops} stop{'s' if f.stops > 1 else ''}"

            lines.append(f"**Option {i + 1}: {carrier_str}**")
            lines.append(f"  `{f.departure_time} → {f.arrival_time}` | {stops_str} | {dur_str}")
            lines.append(f"  Route: {f.route}")

            for c in f.cabins:
                emoji = cabin_emoji.get(c["cabin"], "✈️")
                seats_str = f" | {c['seats']} seats" if c.get("seats") else ""
                cash_str = f" + {c['cash']:.0f} cash" if c.get("cash") else ""
                lines.append(f"  {emoji} {c['cabin']}: `{c['points']:,}` pts{cash_str}{seats_str}")

            lines.append("")

        body = "\n".join(lines)

        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Results", callback_data="partner_back")],
            [InlineKeyboardButton("🔔 Alert", callback_data="partner_alert")],
        ]

        text = header + body
        if len(text) > 4000:
            text = text[:3950] + "\n\n_...truncated._"

        await message.edit_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )

    # =========================================================================
    # SEARCH FUNCTIONALITY - PHASE 2 & 3
    # =========================================================================

    def _parse_search_query(self, args: List[str]) -> Dict[str, Any]:
        """Parse search query arguments into structured data."""
        result = {
            "origin": None,
            "destination": None,
            "month": None,
            "cabin_filter": None,
            "direct_only": False,
            "cheapest_mode": False,
            "multi_dest": False,  # OSL-* or *-BKK
            "points_budget": None,
            "saver_only": False,  # Only bonus/saver tickets
            "error": None
        }

        if not args:
            result["error"] = (
                "Usage:\n"
                "`/search OSL-BKK` - Search route\n"
                "`/search OSL-*` - All destinations\n"
                "`/search OSL-BKK cheap` - Find cheapest\n"
                "`/search OSL-* 50000pts` - Budget search"
            )
            return result

        query = " ".join(args).upper()

        # Check for multi-destination pattern (OSL-* or *-BKK)
        multi_match = re.match(r"([A-Z]{3}|\*)\s*[-\s]+\s*([A-Z]{3}|\*)", query)
        if multi_match:
            origin = multi_match.group(1)
            dest = multi_match.group(2)

            if origin == "*" and dest == "*":
                result["error"] = "Cannot use * for both origin and destination"
                return result

            if origin == "*" or dest == "*":
                result["multi_dest"] = True

            result["origin"] = origin if origin != "*" else None
            result["destination"] = dest if dest != "*" else None
        else:
            # Standard route pattern
            route_match = re.match(r"([A-Z]{3})\s*[-\s]+\s*([A-Z]{3})", query)
            if not route_match:
                result["error"] = "Invalid route format. Use: `/search OSL-BKK` or `/search OSL-*`"
                return result
            result["origin"] = route_match.group(1)
            result["destination"] = route_match.group(2)

        # Extract remaining arguments
        remaining = query[multi_match.end() if multi_match else 0:].strip()
        if multi_match:
            remaining = query[multi_match.end():].strip()

        tokens = remaining.split()

        month_names = {
            "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
            "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
            "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
            "JANUARY": "01", "FEBRUARY": "02", "MARCH": "03", "APRIL": "04",
            "JUNE": "06", "JULY": "07", "AUGUST": "08",
            "SEPTEMBER": "09", "OCTOBER": "10", "NOVEMBER": "11", "DECEMBER": "12"
        }
        cabin_keywords = {"ECONOMY", "PREMIUM", "BUSINESS", "ECO", "BIZ", "PREM"}

        for token in tokens:
            # Check for points budget (e.g., "50000PTS", "50KPTS", "50000")
            pts_match = re.match(r"(\d+)(K)?(PTS)?", token)
            if pts_match and (pts_match.group(3) or pts_match.group(2)):
                points = int(pts_match.group(1))
                if pts_match.group(2):  # "K" suffix
                    points *= 1000
                result["points_budget"] = points
                continue

            # Check for month
            if token in month_names:
                month_num = month_names[token]
                now = datetime.now()
                year = now.year if int(month_num) >= now.month else now.year + 1
                result["month"] = f"{year}{month_num}"
            # Check for cabin
            elif token in cabin_keywords:
                if token == "ECO":
                    result["cabin_filter"] = "ECONOMY"
                elif token == "BIZ":
                    result["cabin_filter"] = "BUSINESS"
                elif token == "PREM":
                    result["cabin_filter"] = "PREMIUM"
                else:
                    result["cabin_filter"] = token
            # Check for direct
            elif token == "DIRECT":
                result["direct_only"] = True
            # Check for cheap mode
            elif token in ("CHEAP", "CHEAPEST", "LOWEST"):
                result["cheapest_mode"] = True
            # Check for bonus/saver mode
            elif token in ("BONUS", "SAVER"):
                result["saver_only"] = True

        return result

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for award flights with calendar view."""
        chat_id = str(update.effective_chat.id)

        parsed = self._parse_search_query(context.args)
        if parsed["error"]:
            await update.message.reply_text(parsed["error"], parse_mode="Markdown")
            return

        # Dispatch to appropriate search handler
        if parsed["multi_dest"]:
            await self._search_multi_destination(update, chat_id, parsed)
        elif parsed["cheapest_mode"]:
            await self._search_cheapest(update, chat_id, parsed)
        elif parsed["saver_only"]:
            await self._search_bonus(update, chat_id, parsed)
        else:
            await self._search_calendar(update, chat_id, parsed)

    async def _search_calendar(self, update: Update, chat_id: str, parsed: Dict):
        """Standard calendar search for a specific route."""
        origin = parsed["origin"]
        destination = parsed["destination"]
        month_filter = parsed["month"]
        cabin_filter = parsed["cabin_filter"]
        direct_only = parsed["direct_only"]

        status_msg = await update.message.reply_text(
            f"🔍 Searching {origin} → {destination}...\n"
            f"{'Direct flights only | ' if direct_only else ''}Fetching calendar..."
        )

        try:
            dates = self.search_engine.get_available_dates(
                origin=origin,
                destination=destination,
                month=month_filter or "",
                cabin=self.CABIN_CODES.get(cabin_filter) if cabin_filter else None
            )

            available_dates = [d for d in dates if d.has_availability] if dates else []

            # Fallback: if calendar API returns nothing, probe the offers API
            # for upcoming dates. This catches new routes not yet in the calendar.
            if not available_dates:
                await status_msg.edit_text(
                    f"🔍 {origin} → {destination} not in calendar.\n"
                    f"Probing flights directly (new route?)..."
                )

                probe_dates = []
                now = datetime.now()
                # Probe ~2 dates per week for the next 8 weeks
                for week_offset in range(8):
                    probe_day = now + timedelta(days=7 + week_offset * 7)
                    probe_dates.append(probe_day.strftime("%Y-%m-%d"))

                for pd in probe_dates:
                    try:
                        offers = self.search_engine.search_flights(
                            origin=origin, destination=destination, date=pd
                        )
                        if offers:
                            # Build an AvailabilityDate from offer data
                            eco = sum(o.available_seats for o in offers if o.cabin_class == "ECONOMY")
                            prem = sum(o.available_seats for o in offers if o.cabin_class == "PREMIUM")
                            biz = sum(o.available_seats for o in offers if o.cabin_class == "BUSINESS")
                            available_dates.append(AvailabilityDate(
                                date=pd,
                                economy_seats=eco or (1 if any(o.cabin_class == "ECONOMY" for o in offers) else 0),
                                premium_seats=prem or (1 if any(o.cabin_class == "PREMIUM" for o in offers) else 0),
                                business_seats=biz or (1 if any(o.cabin_class == "BUSINESS" for o in offers) else 0),
                            ))
                        await asyncio.sleep(0.4)
                    except Exception as e:
                        logger.warning(f"Probe failed for {pd}: {e}")
                        continue

            if not available_dates:
                await status_msg.edit_text(
                    f"❌ No availability found for {origin} → {destination}\n\n"
                    f"Set up an alert: `/subscribe {origin} {destination}`",
                    parse_mode="Markdown"
                )
                return

            # Cache search data
            self.search_cache[chat_id] = {
                "origin": origin,
                "destination": destination,
                "dates": available_dates,
                "all_dates": available_dates.copy(),  # Keep original for filtering
                "cabin_filter": cabin_filter,
                "direct_only": direct_only,
                "saver_only": parsed.get("saver_only", False),
                "sort_by": "date",
                "current_page": 0,
                "mode": "calendar"
            }

            await self._send_calendar_view(status_msg, chat_id)

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ Search failed: {str(e)[:100]}")

    async def _search_bonus(self, update: Update, chat_id: str, parsed: Dict):
        """Search for bonus/saver tickets only - scans dates for actual bonus availability."""
        origin = parsed["origin"]
        destination = parsed["destination"]
        cabin_filter = parsed["cabin_filter"]

        status_msg = await update.message.reply_text(
            f"🌟 Scanning for BONUS tickets {origin} → {destination}...\n"
            f"Checking dates for 30k/45k/60k awards..."
        )

        try:
            # First get available dates from calendar
            dates = self.search_engine.get_available_dates(
                origin=origin,
                destination=destination,
                cabin=self.CABIN_CODES.get(cabin_filter) if cabin_filter else None
            )

            available_dates = [d for d in dates if d.has_availability]

            if not available_dates:
                await status_msg.edit_text(
                    f"❌ No availability found for {origin} → {destination}\n\n"
                    f"Set up alert: `/subscribe {origin} {destination} bonus`",
                    parse_mode="Markdown"
                )
                return

            # Limit dates to check (avoid timeout)
            dates_to_check = available_dates[:20]

            await status_msg.edit_text(
                f"🌟 Scanning {len(dates_to_check)} dates for BONUS tickets...\n"
                f"Progress: 0/{len(dates_to_check)}"
            )

            # Collect bonus offers from each date
            bonus_results = []  # [(date, cabin, points, seats, stops, duration)]

            for i, d in enumerate(dates_to_check):
                try:
                    offers = self.search_engine.search_flights(
                        origin=origin,
                        destination=destination,
                        date=d.date,
                        cabin_filter=cabin_filter
                    )

                    # Filter to bonus only
                    bonus_offers = [o for o in offers if o.is_saver_award]

                    # Get best bonus offer per cabin for this date
                    seen_cabins = set()
                    for o in bonus_offers:
                        if o.cabin_class not in seen_cabins:
                            bonus_results.append({
                                "date": d.date,
                                "cabin": o.cabin_class,
                                "points": o.points,
                                "seats": o.available_seats,
                                "stops": o.stops,
                                "duration": o.total_duration_minutes,
                                "product": o.product_name,
                                "taxes": o.taxes,
                                "currency": o.currency
                            })
                            seen_cabins.add(o.cabin_class)

                    # Update progress every 3 dates
                    if (i + 1) % 3 == 0:
                        await status_msg.edit_text(
                            f"🌟 Scanning for BONUS tickets...\n"
                            f"Progress: {i + 1}/{len(dates_to_check)} | Found: {len(bonus_results)}"
                        )

                    await asyncio.sleep(0.3)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Failed to check {d.date}: {e}")
                    continue

            if not bonus_results:
                await status_msg.edit_text(
                    f"❌ No BONUS tickets available for {origin} → {destination}\n\n"
                    f"Only standard (expensive) tickets found.\n"
                    f"Set up alert: `/subscribe {origin} {destination} bonus`",
                    parse_mode="Markdown"
                )
                return

            # Cache results
            self.search_cache[chat_id] = {
                "origin": origin,
                "destination": destination,
                "bonus_results": bonus_results,
                "cabin_filter": cabin_filter,
                "mode": "bonus"
            }

            await self._send_bonus_view(status_msg, chat_id)

        except Exception as e:
            logger.error(f"Bonus search error: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ Search failed: {str(e)[:100]}")

    async def _send_bonus_view(self, message, chat_id: str, edit: bool = True):
        """Send bonus tickets results."""
        cache = self.search_cache.get(chat_id)
        if not cache or cache.get("mode") != "bonus":
            if edit:
                await message.edit_text("❌ Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        results = cache["bonus_results"]
        cabin_filter = cache.get("cabin_filter")

        # Group by cabin
        by_cabin = {"ECONOMY": [], "PREMIUM": [], "BUSINESS": []}
        for r in results:
            if r["cabin"] in by_cabin:
                by_cabin[r["cabin"]].append(r)

        # Sort each cabin by date
        for cabin in by_cabin:
            by_cabin[cabin].sort(key=lambda x: x["date"])

        header = f"🌟 **BONUS Tickets: {origin} → {destination}**\n"
        if cabin_filter:
            header += f"Cabin: {cabin_filter}\n"

        # Count unique dates with bonus
        unique_dates = len(set(r["date"] for r in results))
        header += f"📊 Found {len(results)} bonus options across {unique_dates} dates\n\n"

        lines = []
        cabin_emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔"}
        cabin_points = {"ECONOMY": "30k", "PREMIUM": "45k", "BUSINESS": "60k"}

        for cabin in ["ECONOMY", "PREMIUM", "BUSINESS"]:
            cabin_results = by_cabin[cabin]
            if not cabin_results:
                continue

            lines.append(f"**{cabin_emoji[cabin]} {cabin} BONUS** ({cabin_points[cabin]} pts)")

            for r in cabin_results[:6]:  # Show up to 6 dates per cabin
                date_obj = datetime.strptime(r["date"], "%Y-%m-%d")
                date_str = date_obj.strftime("%a %d %b")
                stops_str = "Direct" if r["stops"] == 0 else f"{r['stops']}stop"
                hours = r["duration"] // 60

                lines.append(
                    f"  `{date_str}` | {r['seats']} seats | {stops_str} | {hours}h"
                )

            if len(cabin_results) > 6:
                lines.append(f"  _+{len(cabin_results) - 6} more dates..._")
            lines.append("")

        body = "\n".join(lines)

        # Keyboard
        keyboard = []

        # Date buttons for quick access (first 10 unique dates)
        unique_dates_list = sorted(set(r["date"] for r in results))[:10]
        date_buttons = []
        for d in unique_dates_list:
            date_obj = datetime.strptime(d, "%Y-%m-%d")
            btn_text = date_obj.strftime("%d %b")
            date_buttons.append(InlineKeyboardButton(btn_text, callback_data=f"bonusdate:{d}"))

        for i in range(0, len(date_buttons), 5):
            keyboard.append(date_buttons[i:i+5])

        # Action buttons
        keyboard.append([
            InlineKeyboardButton("🔔 Alert (Bonus)", callback_data="alert_bonus"),
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_bonus")
        ])
        keyboard.append([
            InlineKeyboardButton("📅 All Dates (Calendar)", callback_data="to_calendar_from_bonus")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = header + body

        if edit:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _search_cheapest(self, update: Update, chat_id: str, parsed: Dict):
        """Find cheapest flights across all dates."""
        origin = parsed["origin"]
        destination = parsed["destination"]
        cabin_filter = parsed["cabin_filter"]

        status_msg = await update.message.reply_text(
            f"🔍 Finding cheapest {origin} → {destination}...\n"
            f"Scanning all available dates (this may take a moment)..."
        )

        try:
            # First get available dates
            dates = self.search_engine.get_available_dates(
                origin=origin,
                destination=destination,
                cabin=self.CABIN_CODES.get(cabin_filter) if cabin_filter else None
            )

            available_dates = [d for d in dates if d.has_availability]

            if not available_dates:
                await status_msg.edit_text(f"❌ No availability found for {origin} → {destination}")
                return

            # Limit to first 30 dates to avoid timeout
            dates_to_check = available_dates[:30]

            await status_msg.edit_text(
                f"🔍 Checking {len(dates_to_check)} dates for best prices...\n"
                f"Progress: 0/{len(dates_to_check)}"
            )

            # Collect cheapest offers from each date
            all_offers: List[Tuple[str, FlightOffer]] = []

            for i, d in enumerate(dates_to_check):
                try:
                    offers = self.search_engine.search_flights(
                        origin=origin,
                        destination=destination,
                        date=d.date,
                        cabin_filter=cabin_filter
                    )
                    for offer in offers:
                        all_offers.append((d.date, offer))

                    # Update progress every 5 dates
                    if (i + 1) % 5 == 0:
                        await status_msg.edit_text(
                            f"🔍 Checking dates for best prices...\n"
                            f"Progress: {i + 1}/{len(dates_to_check)}"
                        )

                    await asyncio.sleep(0.3)  # Rate limiting
                except Exception as e:
                    logger.warning(f"Failed to check {d.date}: {e}")
                    continue

            if not all_offers:
                await status_msg.edit_text(f"❌ Could not fetch pricing data")
                return

            # Sort by points and get top results
            all_offers.sort(key=lambda x: x[1].points)

            # Cache results
            self.search_cache[chat_id] = {
                "origin": origin,
                "destination": destination,
                "cheapest_offers": all_offers[:20],  # Top 20
                "cabin_filter": cabin_filter,
                "mode": "cheapest"
            }

            await self._send_cheapest_view(status_msg, chat_id)

        except Exception as e:
            logger.error(f"Cheapest search error: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ Search failed: {str(e)[:100]}")

    async def _search_multi_destination(self, update: Update, chat_id: str, parsed: Dict):
        """Search all destinations from origin or all origins to destination."""
        origin = parsed["origin"]
        destination = parsed["destination"]
        points_budget = parsed["points_budget"]
        cabin_filter = parsed["cabin_filter"]

        if origin:
            # OSL-* search: forward query
            search_type = "from"
            fixed_airport = origin
            status_msg = await update.message.reply_text(
                f"🔍 Finding all destinations from {origin}...\n"
                f"{'Budget: ' + str(points_budget) + ' pts | ' if points_budget else ''}"
                f"Scanning network..."
            )
        else:
            # *-BKK search: reverse query - need to scan hubs
            search_type = "to"
            fixed_airport = destination
            status_msg = await update.message.reply_text(
                f"🔍 Finding routes to {destination}...\n"
                f"Scanning {len(REVERSE_SEARCH_HUBS)} hubs..."
            )

        try:
            destinations_data = []

            if search_type == "from":
                # Forward search: use calendar API directly
                raw_data = self.search_engine.get_availability_calendar(
                    origin=origin,
                    destination="",
                )

                for dest in raw_data:
                    dest_code = dest.get("airportCode") or dest.get("iataCode", "")
                    if not dest_code:
                        continue

                    availability = dest.get("availability", {})
                    outbound = availability.get("outbound", [])

                    total_dates = 0
                    total_eco = 0
                    total_prem = 0
                    total_biz = 0

                    for day in outbound:
                        eco = int(day.get("AG", 0) or 0)
                        prem = int(day.get("AP", 0) or 0)
                        biz = int(day.get("AB", 0) or 0)

                        if eco + prem + biz > 0:
                            total_dates += 1
                            total_eco += eco
                            total_prem += prem
                            total_biz += biz

                    if total_dates > 0:
                        destinations_data.append({
                            "code": dest_code,
                            "region": get_region(dest_code),
                            "dates": total_dates,
                            "economy": total_eco,
                            "premium": total_prem,
                            "business": total_biz,
                        })
            else:
                # Reverse search: scan hubs to find origins that fly TO destination
                for i, hub in enumerate(REVERSE_SEARCH_HUBS):
                    # Skip if hub is the destination itself
                    if hub == destination:
                        continue

                    try:
                        dates = self.search_engine.get_available_dates(hub, destination)
                        avail_dates = [d for d in dates if d.has_availability]

                        if avail_dates:
                            total_eco = sum(d.economy_seats for d in avail_dates)
                            total_prem = sum(d.premium_seats for d in avail_dates)
                            total_biz = sum(d.business_seats for d in avail_dates)

                            destinations_data.append({
                                "code": hub,
                                "region": get_region(hub),
                                "dates": len(avail_dates),
                                "economy": total_eco,
                                "premium": total_prem,
                                "business": total_biz,
                            })

                        # Update progress every 3 hubs
                        if (i + 1) % 3 == 0:
                            await status_msg.edit_text(
                                f"🔍 Scanning hubs to {destination}... {i + 1}/{len(REVERSE_SEARCH_HUBS)}"
                            )

                        await asyncio.sleep(0.2)  # Rate limit
                    except Exception as e:
                        logger.warning(f"Failed to check hub {hub}: {e}")
                        continue

            if not destinations_data:
                if search_type == "from":
                    await status_msg.edit_text(f"❌ No destinations found from {fixed_airport}")
                else:
                    await status_msg.edit_text(f"❌ No routes found to {fixed_airport}")
                return

            # Sort by number of available dates
            destinations_data.sort(key=lambda x: -x["dates"])

            # Cache results
            self.search_cache[chat_id] = {
                "origin": origin,
                "destination": destination,
                "fixed_airport": fixed_airport,
                "search_type": search_type,
                "destinations": destinations_data,
                "points_budget": points_budget,
                "cabin_filter": cabin_filter,
                "current_page": 0,
                "group_by_region": True,
                "mode": "multi_dest"
            }

            await self._send_multi_dest_view(status_msg, chat_id)

        except Exception as e:
            logger.error(f"Multi-dest search error: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ Search failed: {str(e)[:100]}")

    async def _send_calendar_view(self, message, chat_id: str, page: int = 0, edit: bool = True):
        """Send or edit the calendar view message."""
        cache = self.search_cache.get(chat_id)
        if not cache:
            if edit:
                await message.edit_text("❌ Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        dates = cache["dates"]
        # Sort by date by default for calendar view
        dates = sorted(dates, key=lambda d: d.date)

        # Pagination
        PAGE_SIZE = 10
        total_pages = max(1, (len(dates) + PAGE_SIZE - 1) // PAGE_SIZE)
        page = max(0, min(page, total_pages - 1))
        cache["current_page"] = page

        start_idx = page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(dates))
        page_dates = dates[start_idx:end_idx]

        # Compute summary stats across ALL dates
        total_eco = sum(d.economy_seats for d in dates)
        total_prem = sum(d.premium_seats for d in dates)
        total_biz = sum(d.business_seats for d in dates)
        dates_with_biz = sum(1 for d in dates if d.business_seats > 0)
        dates_with_prem = sum(1 for d in dates if d.premium_seats > 0)

        best_date = max(dates, key=lambda d: d.economy_seats + d.premium_seats + d.business_seats) if dates else None
        best_total = (best_date.economy_seats + best_date.premium_seats + best_date.business_seats) if best_date else 0

        # Header
        header = f"✈️ **{origin} → {destination}**\n"

        # Summary line
        cabin_summary_parts = []
        if total_eco:
            cabin_summary_parts.append(f"💺{total_eco}")
        if total_prem:
            cabin_summary_parts.append(f"💎{total_prem}")
        if total_biz:
            cabin_summary_parts.append(f"👔{total_biz}")
        header += f"{len(dates)} dates · {' · '.join(cabin_summary_parts)} total seats\n"

        # Best date highlight
        if best_date:
            best_obj = datetime.strptime(best_date.date, "%Y-%m-%d")
            best_parts = []
            if best_date.economy_seats:
                best_parts.append(f"💺{best_date.economy_seats}")
            if best_date.premium_seats:
                best_parts.append(f"💎{best_date.premium_seats}")
            if best_date.business_seats:
                best_parts.append(f"👔{best_date.business_seats}")
            header += f"⭐ Best: **{best_obj.strftime('%a %d %b')}** — {' '.join(best_parts)}\n"

        # Premium cabin callouts
        cabin_callouts = []
        if dates_with_biz:
            cabin_callouts.append(f"👔 Biz on {dates_with_biz} date{'s' if dates_with_biz != 1 else ''}")
        if dates_with_prem:
            cabin_callouts.append(f"💎 Plus on {dates_with_prem} date{'s' if dates_with_prem != 1 else ''}")
        if cabin_callouts:
            header += " · ".join(cabin_callouts) + "\n"

        if total_pages > 1:
            header += f"_Page {page + 1}/{total_pages}_\n"

        header += "\n"

        # Body - date rows grouped by month
        lines = []
        current_month = None

        for d in page_dates:
            date_obj = datetime.strptime(d.date, "%Y-%m-%d")

            # Month group header
            month_name = date_obj.strftime("%b %Y")
            if month_name != current_month:
                if current_month is not None:
                    lines.append("")  # spacing between months
                lines.append(f"**{month_name}**")
                current_month = month_name

            # Availability indicator
            total = d.economy_seats + d.premium_seats + d.business_seats
            if total >= 10:
                dot = "🟢"
            elif total >= 4:
                dot = "🟡"
            else:
                dot = "🔴"

            # Cabin breakdown
            cabins = []
            if d.economy_seats > 0:
                cabins.append(f"💺{d.economy_seats}")
            if d.premium_seats > 0:
                cabins.append(f"💎{d.premium_seats}")
            if d.business_seats > 0:
                cabins.append(f"👔{d.business_seats}")

            cabin_str = "  ".join(cabins)

            # Star marker for best date
            star = " ⭐" if best_date and d.date == best_date.date and len(dates) > 1 else ""

            day_str = date_obj.strftime("%a %d")
            lines.append(f"  `{day_str}` {dot} {cabin_str}{star}")

        body = "\n".join(lines)

        # Compact legend
        footer = "\n\n💺 Go · 💎 Plus · 👔 Biz"
        footer += "\n🟢 10+ · 🟡 4-9 · 🔴 1-3 seats"

        # Keyboard construction
        keyboard = []

        # Date Buttons (Row of 5)
        row = []
        for d in page_dates:
            d_obj = datetime.strptime(d.date, "%Y-%m-%d")
            row.append(InlineKeyboardButton(d_obj.strftime("%d"), callback_data=f"date:{d.date}"))
            if len(row) == 5:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Navigation
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))
        if nav:
            keyboard.append(nav)

        # Actions
        keyboard.append([
            InlineKeyboardButton("🔎 Load Details (Prices & Times)", callback_data="load_details"),
            InlineKeyboardButton("🔔 Alert", callback_data="alert")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        final_text = header + body + footer

        if edit:
            await message.edit_text(final_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(final_text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _send_cheapest_view(self, message, chat_id: str, edit: bool = True):
        """Send cheapest flights results."""
        cache = self.search_cache.get(chat_id)
        if not cache or cache.get("mode") != "cheapest":
            if edit:
                await message.edit_text("❌ Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        offers = cache["cheapest_offers"]
        cabin_filter = cache.get("cabin_filter")

        header = f"💰 **Cheapest: {origin} → {destination}**\n"
        if cabin_filter:
            header += f"Cabin: {cabin_filter}\n"
        header += f"Top {len(offers)} options:\n\n"

        lines = []
        by_cabin: Dict[str, List] = {"ECONOMY": [], "PREMIUM": [], "BUSINESS": []}

        for date, offer in offers:
            if offer.cabin_class in by_cabin:
                by_cabin[offer.cabin_class].append((date, offer))

        cabin_emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔"}

        for cabin in ["ECONOMY", "PREMIUM", "BUSINESS"]:
            cabin_offers = by_cabin[cabin][:5]  # Top 5 per cabin
            if not cabin_offers:
                continue

            lines.append(f"**{cabin_emoji[cabin]} {cabin}**")
            for date, o in cabin_offers:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                date_str = date_obj.strftime("%d %b")
                stops_str = "Direct" if o.is_direct else f"{o.stops}stop"
                lines.append(f"  `{o.points:,}` pts | {date_str} | {stops_str}")
            lines.append("")

        body = "\n".join(lines)

        # Keyboard
        keyboard = [
            [InlineKeyboardButton("🔔 Set Alert", callback_data="alert")],
            [InlineKeyboardButton("📅 Calendar View", callback_data="to_calendar")],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = header + body

        if edit:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _send_multi_dest_view(self, message, chat_id: str, page: int = 0, edit: bool = True):
        """Send multi-destination search results."""
        cache = self.search_cache.get(chat_id)
        if not cache or cache.get("mode") != "multi_dest":
            if edit:
                await message.edit_text("❌ Search expired. Please search again.")
            return

        fixed_airport = cache["fixed_airport"]
        search_type = cache["search_type"]
        destinations = cache["destinations"]
        points_budget = cache.get("points_budget")
        group_by_region = cache.get("group_by_region", True)

        label = "destinations" if search_type == "from" else "origins"

        if search_type == "from":
            header = f"🌍 **{fixed_airport} → All Destinations**\n"
        else:
            header = f"🌍 **All Origins → {fixed_airport}**\n"

        # Summary stats
        total_dates = sum(d["dates"] for d in destinations)
        total_eco = sum(d["economy"] for d in destinations)
        total_prem = sum(d["premium"] for d in destinations)
        total_biz = sum(d["business"] for d in destinations)
        origins_with_biz = sum(1 for d in destinations if d["business"] > 0)
        origins_with_prem = sum(1 for d in destinations if d["premium"] > 0)

        header += f"{len(destinations)} {label} · {total_dates} dates\n"

        seat_parts = []
        if total_eco:
            seat_parts.append(f"💺{total_eco}")
        if total_prem:
            seat_parts.append(f"💎{total_prem}")
        if total_biz:
            seat_parts.append(f"👔{total_biz}")
        if seat_parts:
            header += " · ".join(seat_parts) + " total seats\n"

        cabin_callouts = []
        if origins_with_biz:
            cabin_callouts.append(f"👔 Biz from {origins_with_biz} {label}")
        if origins_with_prem:
            cabin_callouts.append(f"💎 Plus from {origins_with_prem} {label}")
        if cabin_callouts:
            header += " · ".join(cabin_callouts) + "\n"

        if points_budget:
            header += f"💰 Budget: {points_budget:,} pts\n"

        header += "\n"

        lines = []

        if group_by_region:
            # Group by region
            by_region: Dict[str, List] = {}
            for dest in destinations:
                region = dest["region"]
                if region not in by_region:
                    by_region[region] = []
                by_region[region].append(dest)

            # Sort regions by total destinations
            sorted_regions = sorted(by_region.items(), key=lambda x: -len(x[1]))

            for region, dests in sorted_regions:  # Show ALL regions
                lines.append(f"**{region}**")
                for d in dests:  # Show ALL destinations
                    cabins = []
                    if d["economy"] > 0:
                        cabins.append(f"💺{d['economy']}")
                    if d["premium"] > 0:
                        cabins.append(f"💎{d['premium']}")
                    if d["business"] > 0:
                        cabins.append(f"👔{d['business']}")
                    cabin_str = "  ".join(cabins)
                    lines.append(f"  `{d['code']}` {d['dates']}d {cabin_str}")
                lines.append("")
        else:
            # Flat list sorted by seats
            PAGE_SIZE = 20
            total_pages = max(1, (len(destinations) + PAGE_SIZE - 1) // PAGE_SIZE)
            page = max(0, min(page, total_pages - 1))
            cache["current_page"] = page

            start_idx = page * PAGE_SIZE
            end_idx = min(start_idx + PAGE_SIZE, len(destinations))
            page_dests = destinations[start_idx:end_idx]

            header += f"_Page {page + 1}/{total_pages}_\n\n"

            for d in page_dests:
                cabins = []
                if d["economy"] > 0:
                    cabins.append(f"💺{d['economy']}")
                if d["premium"] > 0:
                    cabins.append(f"💎{d['premium']}")
                if d["business"] > 0:
                    cabins.append(f"👔{d['business']}")
                cabin_str = "  ".join(cabins)
                lines.append(f"`{d['code']}` ({d['region'][:4]}) {d['dates']}d {cabin_str}")

        body = "\n".join(lines)

        # Footer
        footer = "\n💺 Go · 💎 Plus · 👔 Biz · _d = dates with seats_"

        # Keyboard
        keyboard = []

        # Destination buttons (top destinations, increased to 15)
        dest_buttons = []
        for d in destinations[:15]:
            # Filter out self-loops (don't show BKK when searching *-BKK)
            if search_type == "to" and d["code"] == cache["destination"]:
                continue
            if search_type == "from" and d["code"] == cache["origin"]:
                continue

            # Use explicit direction encoding: dest:f:origin:destination or dest:t:origin:destination
            if search_type == "from":
                # OSL-* search: origin is fixed, d['code'] is destination
                callback = f"dest:f:{cache['origin']}:{d['code']}"
            else:
                # *-BKK search: d['code'] is origin, destination is fixed
                callback = f"dest:t:{d['code']}:{cache['destination']}"
            dest_buttons.append(InlineKeyboardButton(d["code"], callback_data=callback))

        for i in range(0, len(dest_buttons), 5):
            keyboard.append(dest_buttons[i:i+5])

        # View toggle and navigation
        view_row = []
        if group_by_region:
            view_row.append(InlineKeyboardButton("📋 List View", callback_data="view:list"))
        else:
            view_row.append(InlineKeyboardButton("🌍 Region View", callback_data="view:region"))
            if page > 0:
                view_row.append(InlineKeyboardButton("⬅️", callback_data=f"mdpage:{page-1}"))
            if page < (len(destinations) // 20):
                view_row.append(InlineKeyboardButton("➡️", callback_data=f"mdpage:{page+1}"))
        keyboard.append(view_row)

        # Refresh
        keyboard.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_multi")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = header + body + footer

        if edit:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

    async def _send_date_details(self, message, chat_id: str, date: str):
        """Send detailed flight information for a specific date."""
        cache = self.search_cache.get(chat_id)
        if not cache:
            await message.edit_text("❌ Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        cabin_filter = cache.get("cabin_filter")
        direct_only = cache.get("direct_only", False)
        saver_only = cache.get("saver_only", False)

        await message.edit_text(f"🔍 Loading flights for {date}...\n{origin} → {destination}")

        try:
            logger.info(f"DATE DETAILS: Searching {origin} → {destination} on {date}")
            offers = self.search_engine.search_flights(
                origin=origin,
                destination=destination,
                date=date,
                cabin_filter=cabin_filter
            )

            logger.info(f"DATE DETAILS: Got {len(offers)} offers")
            for o in offers[:3]:  # Log first 3
                logger.info(f"  Offer: {o.cabin_class} {o.points}pts is_saver={o.is_saver_award} product={o.product_name}")

            # Filter to saver/bonus tickets only if requested
            if saver_only and offers:
                offers = [o for o in offers if o.is_saver_award]

            # Filter direct if needed
            if direct_only and offers:
                offers = [o for o in offers if o.is_direct]

            if not offers:
                routes = self.search_engine.get_route_details(origin, destination, date)
                if direct_only and routes:
                    routes = [r for r in routes if r.num_flights == 1]

                if routes:
                    text = self._format_routes_fallback(origin, destination, date, routes)
                else:
                    text = f"❌ No {'direct ' if direct_only else ''}flights available for {date}"

                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
                await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return

            text = self._format_flight_offers(origin, destination, date, offers)

            keyboard = [
                [InlineKeyboardButton("⬅️ Back to Calendar", callback_data="back")],
                [
                    InlineKeyboardButton("🔔 Alert", callback_data=f"alert_date:{date}"),
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_date:{date}")
                ]
            ]

            await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Date details error: {e}", exc_info=True)
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back")]]
            await message.edit_text(f"❌ Failed to load details: {str(e)[:100]}", reply_markup=InlineKeyboardMarkup(keyboard))

    def _format_flight_offers(self, origin: str, destination: str, date: str, offers: List[FlightOffer]) -> str:
        """Format flight offers into a readable message."""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        header = f"✈️ **{origin} → {destination}**\n"
        header += f"📅 {date_obj.strftime('%A, %d %B %Y')}\n\n"

        by_cabin: Dict[str, List[FlightOffer]] = {}
        for o in offers:
            if o.cabin_class not in by_cabin:
                by_cabin[o.cabin_class] = []
            by_cabin[o.cabin_class].append(o)

        lines = []
        cabin_order = ["ECONOMY", "PREMIUM", "BUSINESS"]

        for cabin in cabin_order:
            if cabin not in by_cabin:
                continue

            cabin_offers = by_cabin[cabin]
            cabin_offers.sort(key=lambda x: x.points)

            emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔"}.get(cabin, "✈️")
            lines.append(f"**{emoji} {cabin}**")

            for o in cabin_offers[:3]:
                hours = o.total_duration_minutes // 60
                mins = o.total_duration_minutes % 60
                duration_str = f"{hours}h{mins}m" if mins else f"{hours}h"
                stops_str = "Direct" if o.is_direct else f"{o.stops} stop{'s' if o.stops > 1 else ''}"
                bonus_marker = "🌟" if o.is_saver_award else "📌"
                route = " → ".join([s.departure_airport for s in o.segments] + [destination])

                lines.append(
                    f"  {bonus_marker}`{o.points:,}` pts + {o.taxes:.0f} {o.currency}\n"
                    f"  {stops_str} | {duration_str} | {o.available_seats} seats\n"
                    f"  {route}"
                )
            lines.append("")

        return header + "\n".join(lines)

    def _format_routes_fallback(self, origin: str, destination: str, date: str, routes) -> str:
        """Format route info as fallback when offers API unavailable."""
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        header = f"✈️ **{origin} → {destination}**\n"
        header += f"📅 {date_obj.strftime('%A, %d %B %Y')}\n"
        header += f"_(Points pricing unavailable)_\n\n"

        lines = []
        for r in routes[:5]:
            hours = r.total_time // 60
            mins = r.total_time % 60
            duration_str = f"{hours}h{mins}m" if mins else f"{hours}h"
            stops_str = "Direct" if r.num_flights == 1 else f"{r.num_flights - 1} stop(s)"
            eco = r.availability.get("AG", 0)
            prem = r.availability.get("AP", 0)
            biz = r.availability.get("AB", 0)
            seats_str = f"Eco:{eco} | Prem:{prem} | Biz:{biz}"

            lines.append(
                f"🕐 {r.departure_time} → {r.arrival_time}\n"
                f"   {stops_str} | {duration_str}\n"
                f"   {seats_str}\n"
            )

        return header + "\n".join(lines)

    async def _send_detailed_view(self, message, chat_id: str, edit: bool = True):
        """Fetch and display detailed pricing/times for the current calendar page."""
        cache = self.search_cache.get(chat_id)
        if not cache:
            if edit:
                await message.edit_text("❌ Search expired. Please search again.")
            return

        origin = cache["origin"]
        destination = cache["destination"]
        dates = cache["dates"]
        page = cache.get("current_page", 0)
        PAGE_SIZE = 10
        start_idx = page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(dates))
        page_dates = dates[start_idx:end_idx]

        if not page_dates:
            return

        # Status update
        await message.edit_text(
            f"🔎 Loading details for {len(page_dates)} dates...\n"
            f"Fetching exact prices and times. Please wait."
        )

        detailed_results = []
        
        # Fetch details for each date
        # We limit concurrency or just do sequential to avoid hitting rate limits too hard
        # For better UX, we could use a pool, but let's keep it simple and robust for now.
        for i, d in enumerate(page_dates):
            if i % 3 == 0: # Update status every 3 requests
                await message.edit_text(
                    f"🔎 Loading details... ({i}/{len(page_dates)})\n"
                    f"Fetching exact prices and times..."
                )
            
            try:
                offers = self.search_engine.search_flights(
                    origin=origin,
                    destination=destination,
                    date=d.date,
                    cabin_filter=cache.get("cabin_filter")
                )
                
                # CHEAPEST PRICE LOGIC
                # Find lowest points for each cabin present
                lowest_fares = {}
                for o in offers:
                    if o.points > 0:
                        if o.cabin_class not in lowest_fares or o.points < lowest_fares[o.cabin_class].points:
                            lowest_fares[o.cabin_class] = o
                
                detailed_results.append({
                    "date": d.date,
                    "offers": list(lowest_fares.values()),
                    "count": len(offers)
                })
                
                await asyncio.sleep(0.5) # Politeness delay
            except Exception as e:
                logger.error(f"Failed to fetch details for {d.date}: {e}")
                detailed_results.append({"date": d.date, "error": True})

        # Build Detailed Message
        header = f"✈️ **{origin} → {destination}** (Detailed)\n"
        header += f"📅 Dates {start_idx+1}-{end_idx}\n\n"
        
        lines = []
        for res in detailed_results:
            d_str = datetime.strptime(res["date"], "%Y-%m-%d").strftime("%a %d %b")
            
            if res.get("error"):
                lines.append(f"⚠️ `{d_str}` - Failed to load")
                continue
                
            offers = res["offers"]
            if not offers:
                lines.append(f"❌ `{d_str}` - No bookable flights found")
                continue
                
            # Sort offers by cabin rank (Eco -> Biz)
            cabin_rank = {"ECONOMY": 1, "PREMIUM": 2, "BUSINESS": 3}
            offers.sort(key=lambda x: cabin_rank.get(x.cabin_class, 0))
            
            lines.append(f"🗓 **{d_str}**")
            for o in offers:
                emoji = {"ECONOMY": "💺", "PREMIUM": "💎", "BUSINESS": "👔"}.get(o.cabin_class, "✈️")
                
                # Times: 12:00-18:00
                dep = o.segments[0].departure_time[:5]
                arr = o.segments[-1].arrival_time[:5]
                stops = "Direct" if o.is_direct else f"{o.stops} stop"
                
                # Price formatting
                pts_str = f"{o.points/1000:.1f}k"
                if pts_str.endswith(".0k"): pts_str = pts_str[:-3] + "k"
                
                lines.append(f"  {emoji} {dep}-{arr} | {pts_str} | {stops}")
            lines.append("")

        body = "\n".join(lines)
        
        # Footer
        footer = "Prices are per person + taxes."

        # Navigation to go back
        keyboard = [[InlineKeyboardButton("⬅️ Back to Calendar", callback_data="back")]]
        
        await message.edit_text(header + body + footer, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button callbacks."""
        query = update.callback_query
        try:
            await query.answer()
        except Exception:
            pass # Ignore if answer fails (e.g. timeout)

        chat_id = str(update.effective_chat.id)
        data = query.data
        cache = self.search_cache.get(chat_id)

        # Deals callbacks
        if data.startswith("deals:"):
            action = data.split(":", 1)[1]
            if action == "refresh":
                # Force fresh fetch by resetting cache timestamp
                self.deals_cache["timestamp"] = 0
                await query.message.edit_text("🔍 Refreshing deals...\nScanning OSL, CPH, ARN")
                try:
                    deals_data = await self._fetch_live_deals()
                    if not deals_data:
                        await query.message.edit_text("❌ No deals found. Try again later.")
                        return
                except Exception as e:
                    await query.message.edit_text(f"❌ Refresh failed: {str(e)[:100]}")
                    return
                filtered = self._filter_deals(deals_data, None)
                text = self._format_deals_message(filtered, None)
                keyboard = self._build_deals_keyboard(filtered, None)
                await query.message.edit_text(
                    text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
                )
            else:
                # Cabin filter: eco, prem, biz, all
                cabin_filter = action if action != "all" else None
                deals_data = self.deals_cache.get("data", [])
                if not deals_data:
                    await query.message.edit_text("❌ No cached deals. Tap 🔄 Refresh.")
                    return
                filtered = self._filter_deals(deals_data, cabin_filter)
                if not filtered:
                    filter_name = {"eco": "Economy", "prem": "Premium", "biz": "Business"}.get(cabin_filter, "")
                    await query.message.edit_text(
                        f"🔍 No {filter_name} deals found. Try a different cabin filter.",
                    )
                    return
                text = self._format_deals_message(filtered, cabin_filter)
                keyboard = self._build_deals_keyboard(filtered, cabin_filter)
                await query.message.edit_text(
                    text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
                )
            return

        # Load Details Action
        if data == "load_details":
            await self._send_detailed_view(query.message, chat_id)
            return

        # Date selection
        if data.startswith("date:"):
            date = data.split(":", 1)[1]
            await self._send_date_details(query.message, chat_id, date)

        # Page navigation
        elif data.startswith("page:"):
            page = int(data.split(":", 1)[1])
            await self._send_calendar_view(query.message, chat_id, page=page)

        # Multi-dest page navigation
        elif data.startswith("mdpage:"):
            page = int(data.split(":", 1)[1])
            await self._send_multi_dest_view(query.message, chat_id, page=page)

        # Sort change
        elif data.startswith("sort:"):
            sort_key = data.split(":", 1)[1]
            if cache:
                cache["sort_by"] = sort_key
                cache["current_page"] = 0
                await self._send_calendar_view(query.message, chat_id)

        # Cabin filter
        elif data.startswith("cabin:"):
            cabin = data.split(":", 1)[1]
            if cache:
                if cache.get("cabin_filter") == cabin:
                    cache["cabin_filter"] = None
                else:
                    cache["cabin_filter"] = cabin

                await query.message.edit_text(f"🔍 Filtering by {cabin if cache['cabin_filter'] else 'all cabins'}...")

                origin = cache["origin"]
                destination = cache["destination"]
                cabin_code = self.CABIN_CODES.get(cabin) if cache["cabin_filter"] else None

                dates = self.search_engine.get_available_dates(origin=origin, destination=destination, cabin=cabin_code)
                cache["dates"] = [d for d in dates if d.has_availability]
                cache["current_page"] = 0

                await self._send_calendar_view(query.message, chat_id)

        # Direct toggle
        elif data == "toggle_direct":
            if cache:
                cache["direct_only"] = not cache.get("direct_only", False)
                await self._send_calendar_view(query.message, chat_id)

        # Saver/Bonus toggle
        elif data == "toggle_saver":
            if cache:
                cache["saver_only"] = not cache.get("saver_only", False)
                await self._send_calendar_view(query.message, chat_id)

        # Bonus view callbacks
        elif data.startswith("bonusdate:"):
            date = data.split(":", 1)[1]
            if cache:
                # Set saver_only filter and show date details
                cache["saver_only"] = True
                cache["mode"] = "calendar"  # Switch mode for date details
            await self._send_date_details(query.message, chat_id, date)

        elif data == "alert_bonus":
            if cache:
                origin = cache["origin"]
                destination = cache["destination"]
                cabin_filter = cache.get("cabin_filter")
                cabin_code = self.CABIN_CODES.get(cabin_filter) if cabin_filter else None

                if self.db.add_subscription(chat_id, origin, destination, cabin_code, saver_only=True):
                    cabin_text = cabin_filter or "ANY"
                    await query.message.reply_text(
                        f"✅ BONUS alert added: **{origin} → {destination}** ({cabin_text} 🌟BONUS)\n"
                        f"I'll notify you when bonus tickets appear!",
                        parse_mode="Markdown"
                    )
                else:
                    await query.message.reply_text("⚠️ Alert already exists.")

        elif data == "refresh_bonus":
            if cache:
                await query.message.edit_text("🔄 Refreshing bonus search...")
                origin = cache["origin"]
                destination = cache["destination"]
                cabin_filter = cache.get("cabin_filter")

                # Re-scan for bonus tickets
                dates = self.search_engine.get_available_dates(origin=origin, destination=destination)
                available_dates = [d for d in dates if d.has_availability][:15]

                bonus_results = []
                for d in available_dates:
                    try:
                        offers = self.search_engine.search_flights(origin, destination, d.date, cabin_filter)
                        bonus_offers = [o for o in offers if o.is_saver_award]
                        seen_cabins = set()
                        for o in bonus_offers:
                            if o.cabin_class not in seen_cabins:
                                bonus_results.append({
                                    "date": d.date, "cabin": o.cabin_class, "points": o.points,
                                    "seats": o.available_seats, "stops": o.stops,
                                    "duration": o.total_duration_minutes, "product": o.product_name,
                                    "taxes": o.taxes, "currency": o.currency
                                })
                                seen_cabins.add(o.cabin_class)
                        await asyncio.sleep(0.3)
                    except:
                        continue

                cache["bonus_results"] = bonus_results
                cache["mode"] = "bonus"
                await self._send_bonus_view(query.message, chat_id)

        elif data == "to_calendar_from_bonus":
            if cache:
                cache["mode"] = "calendar"
                cache["saver_only"] = False
                await query.message.edit_text(f"🔍 Loading calendar for {cache['origin']} → {cache['destination']}...")
                dates = self.search_engine.get_available_dates(origin=cache["origin"], destination=cache["destination"])
                cache["dates"] = [d for d in dates if d.has_availability]
                cache["current_page"] = 0
                await self._send_calendar_view(query.message, chat_id)

        elif data == "search_bonus_from_cal":
            if cache:
                await query.message.edit_text(f"🌟 Scanning for BONUS tickets {cache['origin']} → {cache['destination']}...")
                origin = cache["origin"]
                destination = cache["destination"]

                # Scan for bonus tickets using the same engine that works for date clicks
                dates = cache.get("dates", [])[:10]
                bonus_results = []
                total_offers_found = 0

                logger.info(f"BONUS SCAN: Starting scan for {origin} → {destination}, {len(dates)} dates to check")

                for i, d in enumerate(dates):
                    try:
                        date_str = d.date
                        logger.info(f"BONUS SCAN: Checking date {date_str}")

                        # Use self.search_engine with named params - same as _send_date_details
                        offers = self.search_engine.search_flights(
                            origin=origin,
                            destination=destination,
                            date=date_str,
                            cabin_filter=None
                        )

                        total_offers_found += len(offers)
                        logger.info(f"BONUS SCAN: Got {len(offers)} offers for {date_str}")

                        # Debug: log saver status of each offer
                        for o in offers[:3]:  # Log first 3
                            logger.info(f"  Offer: {o.cabin_class} {o.points}pts is_saver={o.is_saver_award} product={o.product_name}")

                        seen_cabins = set()
                        for o in offers:
                            if o.is_saver_award and o.cabin_class not in seen_cabins:
                                bonus_results.append({
                                    "date": date_str, "cabin": o.cabin_class, "points": o.points,
                                    "seats": o.available_seats, "stops": o.stops,
                                    "duration": o.total_duration_minutes, "product": o.product_name,
                                    "taxes": o.taxes, "currency": o.currency
                                })
                                seen_cabins.add(o.cabin_class)
                                logger.info(f"  FOUND BONUS: {o.cabin_class} {o.points}pts")

                        if (i + 1) % 2 == 0:
                            await query.message.edit_text(f"🌟 Scanning... {i+1}/{len(dates)} | Found: {len(bonus_results)}")
                        await asyncio.sleep(0.5)  # Increased delay for rate limiting
                    except Exception as e:
                        logger.error(f"Bonus scan error for {d.date}: {e}", exc_info=True)
                        continue

                logger.info(f"BONUS SCAN: Completed. Found {len(bonus_results)} bonus, {total_offers_found} total offers")

                # If we got 0 offers across all dates, likely a transient API issue
                if total_offers_found == 0 and len(dates) > 0:
                    logger.warning(f"BONUS SCAN: Got 0 offers for all dates - possible API issue, retrying once...")
                    await query.message.edit_text(f"🔄 Retrying scan (API hiccup)...")
                    await asyncio.sleep(1.0)

                    # Retry with just the first 3 dates
                    for d in dates[:3]:
                        try:
                            offers = self.search_engine.search_flights(origin, destination, d.date, None)
                            total_offers_found += len(offers)
                            for o in offers:
                                if o.is_saver_award:
                                    bonus_results.append({
                                        "date": d.date, "cabin": o.cabin_class, "points": o.points,
                                        "seats": o.available_seats, "stops": o.stops,
                                        "duration": o.total_duration_minutes, "product": o.product_name,
                                        "taxes": o.taxes, "currency": o.currency
                                    })
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            logger.error(f"Retry error for {d.date}: {e}")
                    logger.info(f"BONUS SCAN RETRY: Found {len(bonus_results)} bonus after retry")

                if bonus_results:
                    cache["bonus_results"] = bonus_results
                    cache["mode"] = "bonus"
                    await self._send_bonus_view(query.message, chat_id)
                else:
                    await query.message.edit_text(
                        f"❌ No BONUS tickets found for {origin} → {destination}\n"
                        f"Only standard (expensive) tickets available.\n"
                        f"_Try tapping a date directly to see all offers._",
                        parse_mode="Markdown"
                    )

        # View toggle (multi-dest)
        elif data.startswith("view:"):
            view_type = data.split(":", 1)[1]
            if cache:
                cache["group_by_region"] = (view_type == "region")
                cache["current_page"] = 0
                await self._send_multi_dest_view(query.message, chat_id)

        # Destination selection from multi-dest
        elif data.startswith("dest:"):
            # Parse new format: dest:f:OSL:BKK or dest:t:OSL:BKK
            parts = data.split(":")
            if len(parts) == 4:
                # New format with explicit direction
                direction = parts[1]  # "f" (from) or "t" (to)
                origin = parts[2]
                destination = parts[3]
            else:
                # Legacy fallback (should not happen with new code)
                route = parts[1]
                origin, destination = route.split("-")

            # Start new calendar search for this route
            self.search_cache[chat_id] = {
                "origin": origin,
                "destination": destination,
                "dates": [],
                "cabin_filter": None,
                "direct_only": False,
                "sort_by": "date",
                "current_page": 0,
                "mode": "calendar"
            }
            await query.message.edit_text(f"🔍 Searching {origin} → {destination}...")

            dates = self.search_engine.get_available_dates(origin=origin, destination=destination)
            self.search_cache[chat_id]["dates"] = [d for d in dates if d.has_availability]
            self.search_cache[chat_id]["all_dates"] = self.search_cache[chat_id]["dates"].copy()

            await self._send_calendar_view(query.message, chat_id)

        # Back to calendar
        elif data == "back":
            if cache and cache.get("mode") == "calendar":
                await self._send_calendar_view(query.message, chat_id)
            elif cache and cache.get("mode") == "multi_dest":
                await self._send_multi_dest_view(query.message, chat_id)
            else:
                await self._send_calendar_view(query.message, chat_id)

        # To calendar from cheapest view
        elif data == "to_calendar":
            if cache:
                cache["mode"] = "calendar"
                # Fetch dates
                dates = self.search_engine.get_available_dates(
                    origin=cache["origin"],
                    destination=cache["destination"],
                    cabin=self.CABIN_CODES.get(cache.get("cabin_filter")) if cache.get("cabin_filter") else None
                )
                cache["dates"] = [d for d in dates if d.has_availability]
                cache["current_page"] = 0
                await self._send_calendar_view(query.message, chat_id)

        # Find cheapest from calendar
        elif data == "find_cheapest":
            if cache:
                await query.message.edit_text("🔍 Scanning for cheapest options...")
                # Reuse existing data
                cache["mode"] = "cheapest"
                cache["cheapest_offers"] = []

                dates_to_check = cache.get("dates", [])[:20]

                for d in dates_to_check:
                    try:
                        offers = self.search_engine.search_flights(
                            origin=cache["origin"],
                            destination=cache["destination"],
                            date=d.date,
                            cabin_filter=cache.get("cabin_filter")
                        )
                        for offer in offers:
                            cache["cheapest_offers"].append((d.date, offer))
                        await asyncio.sleep(0.3)
                    except:
                        continue

                cache["cheapest_offers"].sort(key=lambda x: x[1].points)
                cache["cheapest_offers"] = cache["cheapest_offers"][:20]

                await self._send_cheapest_view(query.message, chat_id)

        # Refresh
        elif data == "refresh":
            if cache:
                await query.message.edit_text("🔄 Refreshing...")
                cabin_code = self.CABIN_CODES.get(cache.get("cabin_filter")) if cache.get("cabin_filter") else None
                dates = self.search_engine.get_available_dates(
                    origin=cache["origin"],
                    destination=cache["destination"],
                    cabin=cabin_code
                )
                cache["dates"] = [d for d in dates if d.has_availability]
                await self._send_calendar_view(query.message, chat_id)

        elif data == "refresh_multi":
            if cache and cache.get("mode") == "multi_dest":
                await query.message.edit_text("🔄 Refreshing destinations...")
                # Re-fetch destinations
                raw_data = self.search_engine.get_availability_calendar(
                    origin=cache.get("origin") or "OSL",
                    destination=cache.get("destination") or "",
                )
                # Reparse (simplified)
                await self._send_multi_dest_view(query.message, chat_id)

        elif data.startswith("refresh_date:"):
            date = data.split(":", 1)[1]
            await self._send_date_details(query.message, chat_id, date)

        # Status callbacks
        elif data == "status:detail":
            await self._send_status_view(query.message, compact=False, edit=True)

        elif data == "status:compact":
            await self._send_status_view(query.message, compact=True, edit=True)

        elif data == "status:refresh":
            await query.message.edit_text("🔄 Refreshing status...")
            await self._send_status_view(query.message, compact=True, edit=True)

        # Partner callbacks
        elif data.startswith("partner_page:"):
            page = int(data.split(":", 1)[1])
            await self._send_partner_view(query.message, chat_id, page=page)

        elif data.startswith("partner_date:"):
            date = data.split(":", 1)[1]
            if cache and cache.get("mode") == "partner":
                date_flights = [f for f in cache["partner_flights"] if f.date == date]
                if date_flights:
                    await self._send_partner_date_detail(query.message, chat_id, date, date_flights)
                else:
                    await query.message.edit_text(f"No partner flights on {date}.")

        elif data.startswith("partner_cabin:"):
            cabin = data.split(":", 1)[1]
            if cache and cache.get("mode") == "partner":
                all_flights = cache.get("partner_flights_all", cache["partner_flights"])
                if cabin == "ALL":
                    cache["cabin_filter"] = None
                    cache["partner_flights"] = all_flights
                else:
                    cache["cabin_filter"] = cabin
                    cache["partner_flights"] = [
                        f for f in all_flights
                        if any(c["cabin"] == cabin for c in f.cabins)
                    ]
                cache["current_page"] = 0
                await self._send_partner_view(query.message, chat_id)

        elif data == "partner_refresh":
            if cache and cache.get("mode") == "partner":
                origin = cache["origin"]
                destination = cache["destination"]
                cabin_filter = cache.get("cabin_filter")
                await query.message.edit_text(
                    f"🔄 Refreshing partner search {origin} → {destination}..."
                )
                dates_to_scan = self._build_partner_date_list()
                all_flights: List[PartnerFlight] = []
                for i, date in enumerate(dates_to_scan):
                    try:
                        raw = self.search_engine.get_partner_awards(origin, destination, date)
                        if raw and raw.get("outboundFlights"):
                            parsed_flights = self.search_engine.parse_partner_flights(
                                raw, origin, destination, date
                            )
                            if cabin_filter:
                                parsed_flights = [
                                    f for f in parsed_flights
                                    if any(c["cabin"] == cabin_filter for c in f.cabins)
                                ]
                            all_flights.extend(parsed_flights)
                        if (i + 1) % 3 == 0:
                            await query.message.edit_text(
                                f"🔄 Refreshing... {i + 1}/{len(dates_to_scan)} | Found: {len(all_flights)}"
                            )
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        if "429" in str(e):
                            break
                        continue
                cache["partner_flights"] = all_flights
                cache["partner_flights_all"] = all_flights
                cache["current_page"] = 0
                await self._send_partner_view(query.message, chat_id)

        elif data == "partner_alert":
            if cache and cache.get("mode") == "partner":
                origin = cache["origin"]
                destination = cache["destination"]
                if self.db.add_subscription(chat_id, origin, destination, None):
                    await query.message.reply_text(
                        f"🔔 Alert added: **{origin} → {destination}**\n"
                        f"You'll be notified when availability changes.",
                        parse_mode="Markdown"
                    )
                else:
                    await query.message.reply_text("⚠️ Alert already exists.")

        elif data == "partner_to_sas":
            if cache:
                origin = cache.get("origin")
                destination = cache.get("destination")
                await query.message.edit_text(f"🔍 Searching SAS flights {origin} → {destination}...")
                dates = self.search_engine.get_available_dates(origin=origin, destination=destination)
                self.search_cache[chat_id] = {
                    "origin": origin,
                    "destination": destination,
                    "dates": [d for d in dates if d.has_availability],
                    "cabin_filter": None,
                    "direct_only": False,
                    "sort_by": "date",
                    "current_page": 0,
                    "mode": "calendar"
                }
                await self._send_calendar_view(query.message, chat_id)

        elif data == "partner_back":
            if cache and cache.get("mode") == "partner":
                await self._send_partner_view(query.message, chat_id, page=cache.get("current_page", 0))

        # Alert
        elif data == "alert" or data.startswith("alert_date:"):
            if cache:
                origin = cache["origin"]
                destination = cache["destination"]
                cabin_filter = cache.get("cabin_filter")
                cabin_code = self.CABIN_CODES.get(cabin_filter) if cabin_filter else None

                if self.db.add_subscription(chat_id, origin, destination, cabin_code):
                    cabin_text = cabin_filter or "ANY"
                    await query.message.reply_text(
                        f"✅ Alert added: **{origin} → {destination}** ({cabin_text})",
                        parse_mode="Markdown"
                    )
                else:
                    await query.message.reply_text("⚠️ Alert already exists.")

    def run(self):
        """Start the bot."""
        if not self.config.telegram_bot_token:
            logger.error("No token found! Set TELEGRAM_BOT_TOKEN.")
            return

        app = Application.builder().token(self.config.telegram_bot_token).build()

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("deals", self.deals))
        app.add_handler(CommandHandler("partner", self.partner))
        app.add_handler(CommandHandler("subscribe", self.subscribe))
        app.add_handler(CommandHandler("subscriptions", self.list_subscriptions))
        app.add_handler(CommandHandler("unsubscribe", self.unsubscribe))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CallbackQueryHandler(self.handle_callback))

        logger.info("Bot started with Phase 2+3 features...")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    bot = SubscriptionBot()
    bot.run()
