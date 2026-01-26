# Interactive Bot Examples

Real-world examples of how to use the Telegram bot.

## Example 1: Basic Search

**User sends:**
```
/search OSL BKK
```

**Bot responds:**
```
🔍 Search: OSL → Bangkok (BKK)

📤 OUTBOUND (OSL → BKK):
  📅 Feb 15, 2026
     💺 Economy: 4
     ⭐ Premium: 2
     💼 Business: 1
  📅 Feb 16, 2026
     💺 Economy: 2
  📅 Feb 20, 2026
     💺 Economy: 6
     ⭐ Premium: 1
     💼 Business: 2

📥 RETURN (BKK → OSL):
  📅 Feb 22, 2026
     💺 Economy: 3
     ⭐ Premium: 1
  📅 Feb 25, 2026
     💺 Economy: 5
     💼 Business: 1
  📅 Mar 01, 2026
     💺 Economy: 8
     ⭐ Premium: 2
     💼 Business: 3

🔗 Book on SAS
```

## Example 2: Different Input Formats

All of these work the same:

```
/search OSL BKK
/search OSL - BKK
/search OSL-BKK
/search osl bkk
```

## Example 3: Multiple Routes

**Search Copenhagen to Tokyo:**
```
/search CPH NRT
```

**Search Amsterdam to Singapore:**
```
/search AMS SIN
```

**Search Paris to Shanghai:**
```
/search CDG PVG
```

## Example 4: No Availability

**User sends:**
```
/search OSL KIX
```

**Bot responds:**
```
🔍 Search: OSL → Osaka (KIX)

📤 OUTBOUND (OSL → KIX):
  ℹ️ No available dates

📥 RETURN (KIX → OSL):
  ℹ️ No available dates

🔗 Book on SAS
```

## Example 5: Invalid Route

**User sends:**
```
/search OSL XXX
```

**Bot responds:**
```
❌ Unknown airport codes

Please check the airport codes and try again.

Valid airports:
  AMS - Amsterdam
  BKK - Bangkok
  CDG - Paris
  CPH - Copenhagen
  HAN - Hanoi
  HND - Tokyo Haneda
  KIX - Osaka
  NRT - Tokyo Narita
  OSL - Oslo
  PEK - Beijing
  PVG - Shanghai
  SGN - Ho Chi Minh City
  SIN - Singapore
```

## Example 6: Getting Help

**User sends:**
```
/help
```

**Bot responds:**
```
SAS EuroBonus Award Search Bot

Usage:
/search ORIGIN DESTINATION

Supported Origins:
🇳🇴 OSL - Oslo
🇫🇷 CDG - Paris
🇩🇰 CPH - Copenhagen
🇳🇱 AMS - Amsterdam

Supported Destinations:
🇹🇭 BKK - Bangkok
🇯🇵 NRT - Tokyo Narita
🇯🇵 HND - Tokyo Haneda
🇯🇵 KIX - Osaka
🇨🇳 PVG - Shanghai
🇨🇳 PEK - Beijing
🇻🇳 SGN - Ho Chi Minh City
🇻🇳 HAN - Hanoi
🇸🇬 SIN - Singapore

Cabin Classes:
💺 Economy (AG)
⭐ Premium (AP)
💼 Business (AB)

Example searches:
/search OSL BKK
/search CPH NRT
/search AMS SIN
```

## Example 7: First Time Usage

**User sends:**
```
/start
```

**Bot responds:**
```
👋 Welcome to SAS EuroBonus Award Search Bot!

I can help you search for award availability on SAS routes.

Commands:
/search OSL BKK - Search for routes
/help - Show this help message

Example:
/search OSL BKK
/search CPH NRT

Supported routes:
Origins: OSL, CDG, CPH, AMS
Destinations: BKK, NRT, HND, KIX, PVG, PEK, SGN, HAN, SIN
```

## Example 8: Business Class Search

**User sends:**
```
/search CPH NRT
```

**Bot shows Business class availability (if available):**
```
🔍 Search: CPH → Tokyo Narita (NRT)

📤 OUTBOUND (CPH → NRT):
  📅 Mar 15, 2026
     💺 Economy: 8
     💼 Business: 2
  📅 Mar 18, 2026
     💺 Economy: 4
     ⭐ Premium: 1
     💼 Business: 1

📥 RETURN (NRT → CPH):
  📅 Mar 25, 2026
     💺 Economy: 6
     💼 Business: 3

🔗 Book on SAS
```

## Example 9: Quick Route Comparison

Want to compare multiple routes? Just send multiple searches:

```
/search OSL BKK
/search CPH BKK
/search AMS BKK
```

The bot will respond to each search with availability for that specific route.

## Example 10: Real-World Scenario

**Planning a trip to Japan from different European cities:**

```
/search OSL NRT
/search OSL HND
/search CPH NRT
/search CPH HND
```

This lets you quickly compare:
- Oslo vs Copenhagen as departure city
- Narita vs Haneda as arrival airport
- Which route has better availability
- Which cabin classes are available

## Tips

1. **Check both directions** - The bot shows outbound AND return flights in one search

2. **Try different dates** - If no availability shows, the route might exist but have no award seats at the moment

3. **Compare airports** - Some cities have multiple airports (Tokyo: NRT and HND)

4. **Be flexible** - If your preferred route is full, try a nearby departure city

5. **Book quickly** - Award seats can disappear fast, use the booking link immediately

## Difference from Monitor

**Interactive Bot (this):**
- You request searches manually
- Shows current availability
- On-demand, any time you want
- No notifications

**Background Monitor (sas_monitor.py):**
- Runs automatically every 15 minutes
- Notifies you when NEW seats are released
- You don't need to do anything
- Proactive alerts

**Best of both worlds:**
Run both services together! The monitor alerts you to new releases, and you can use the bot to explore other routes on-demand.
