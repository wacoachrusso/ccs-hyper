from bs4 import BeautifulSoup
import re
import arrow

def _get_datetime_from_day_and_time(year, month, day_of_month, time_str):
    """Helper to create an Arrow datetime object from parts."""
    return arrow.get(year, month, day_of_month).replace(
        hour=int(time_str[:2]), 
        minute=int(time_str[2:]), 
        second=0, 
        microsecond=0
    )

def parse_schedule(html_content):
    """Parse CCS Master Schedule HTML (new format) and return calendar event dicts."""
    print("\n\n=== STARTING PARSER ===\n")
    soup = BeautifulSoup(html_content, 'html.parser')
    print(f"HTML size: {len(html_content)} bytes, {len(soup.select('div.sg__row.sg__day'))} day rows found")
    # --- STAGE 1: Parse all days into a flat list --- #
    all_days = []
    prev_day_int = None
    # Current month is July 2025 - fixed based on user feedback
    current_year = 2025
    current_month = 7  # July
    print(f"Setting initial month/year to {current_month}/{current_year}")

    for row in soup.select('div.sg__row.sg__day'):
        date_label = row.select_one('div.sg__date label.sg__day-number')
        if not date_label:
            continue
        day_int = int(date_label.text.strip())

        # Disable month rollover detection - user confirmed all trips are in July
        # We were incorrectly advancing to August when day numbers reset
        # (This can be re-enabled with proper month detection from HTML if needed in future)
        #if prev_day_int is not None and day_int < prev_day_int:
        #    current_month = 1 if current_month == 12 else current_month + 1
        #    if current_month == 1:
        #        current_year += 1
        if prev_day_int is not None and day_int < prev_day_int:
            print(f"SKIPPING month rollover from day {prev_day_int} to {day_int} - all trips are in July")
        # Always maintain July 2025 throughout parsing
        prev_day_int = day_int

        pairing_span = row.select_one('span.links__one')
        if not pairing_span:
            all_days.append({'type': 'day_off'})
            continue

        pairing_code = pairing_span.text.strip()
        desc_span = row.select_one('span.sg__description')
        desc_text = desc_span.get_text(strip=True) if desc_span else ''
        time_spans = [s for s in row.select('div.sg__time span') if 'hidden' not in s.attrs]
        start_time = time_spans[0].text.strip().replace(':', '')[:4] if time_spans else '0000'
        end_time = time_spans[1].text.strip().replace(':', '')[:4] if len(time_spans) > 1 else '2359'

        start_dt = _get_datetime_from_day_and_time(current_year, current_month, day_int, start_time)
        end_dt = _get_datetime_from_day_and_time(current_year, current_month, day_int, end_time)
        if end_dt < start_dt:
            end_dt = end_dt.shift(months=+1)

        all_days.append({
            'type': 'trip',
            'pairing': pairing_code,
            'start_dt': start_dt,
            'end_dt': end_dt,
            'description': f"{start_dt.format('YYYY-MM-DD')} {start_time[:2]}:{start_time[2:]} - {end_time[:2]}:{end_time[2:]} {desc_text}"
        })
        print(f"Found trip day: {pairing_code} on {start_dt.format('YYYY-MM-DD')} from {start_time} to {end_time}")

    # --- STAGE 2: Group consecutive trip days into events --- #
    print(f"\nFound {len(all_days)} total day entries, starting grouping...")
    events = []
    current_trip = None

    for i, day in enumerate(all_days):
        print(f"Processing day {i+1}/{len(all_days)}: {day.get('type', 'unknown')}")
        
        if day['type'] == 'day_off':
            if current_trip:
                print(f"  Found day off - finalizing trip {current_trip['summary']} from {current_trip['start']['date']} to {current_trip['end']['date']}")
                events.append(current_trip)
                current_trip = None
            else:
                print("  Skipping day off (no active trip)")
            continue

        print(f"  Trip day: {day['pairing']} on {day['start_dt'].format('YYYY-MM-DD')}")
        
        # Check if this day is part of the same trip as the previous day
        # AND the dates are consecutive (to avoid merging separate trips with same pairing code)
        is_consecutive = False
        if current_trip and current_trip['summary'] == f"TRIP: {day['pairing']}":
            # Check if this day is right after the previous one
            current_end_date = arrow.get(current_trip['end']['date'])
            this_start_date = arrow.get(day['start_dt'].format('YYYY-MM-DD'))
            days_between = (this_start_date - current_end_date.shift(days=-1)).days
            
            is_consecutive = days_between <= 1
            print(f"  Days between: {days_between}, consecutive: {is_consecutive}")
            
        if current_trip and current_trip['summary'] == f"TRIP: {day['pairing']}" and is_consecutive:
            # Extend the current trip
            old_end = current_trip['end']['date']
            current_trip['end']['date'] = day['end_dt'].shift(days=+1).format('YYYY-MM-DD')
            print(f"  Extending trip {current_trip['summary']}, changing end date from {old_end} to {current_trip['end']['date']}")
            
            # Add this day's details to the description
            current_trip['description'] += f"\n\n--- DAY {day['start_dt'].format('MM/DD')} ---\n"
            current_trip['description'] += day['description']
        else:
            # Finalize old trip and start a new one
            if current_trip:
                print(f"  Ending trip {current_trip['summary']} ({current_trip['start']['date']} to {current_trip['end']['date']})") 
                events.append(current_trip)
            
            # Extract additional details for enriched description
            trip_value = "" 
            block_hours = ""
            credit_hours = ""
            
            # Look for trip value/block/credit details in the description
            desc_lines = day['description'].split('\n')
            for line in desc_lines:
                if "BLOCK:" in line:
                    block_hours = line.strip()
                if "CREDIT:" in line:
                    credit_hours = line.strip()
                if "VALUE:" in line or "PAY:" in line:
                    trip_value = line.strip()
            
            # Enhanced description with comprehensive pairing details
            enhanced_desc = f"PAIRING: {day['pairing']}\n\n"
            enhanced_desc += f"CHECK-IN: {day['start_dt'].format('MM/DD/YYYY')} @ {day['start_dt'].format('HH:mm')}\n"
            
            # Set end date to next day for multi-day span visualization
            end_dt = day['start_dt'].shift(days=+2)  # Add 2 days for proper visual span
            
            # Use actual block-out time for check-out display
            block_out_time = day['end_dt'].format('HH:mm')
            enhanced_desc += f"BLOCK-OUT: {end_dt.format('MM/DD/YYYY')} @ {block_out_time}\n\n"
            
            # Add trip value/worth information
            if block_hours:
                enhanced_desc += f"{block_hours}\n"
            if credit_hours:
                enhanced_desc += f"{credit_hours}\n"
            if trip_value:
                enhanced_desc += f"{trip_value}\n"
            
            enhanced_desc += f"\nDAY DETAILS:\n{day['description']}"
            
            print(f"Creating trip spanning from {day['start_dt'].format('YYYY-MM-DD')} to {end_dt.format('YYYY-MM-DD')}")
            
            current_trip = {
                'summary': f"TRIP: {day['pairing']}",
                'start': {'date': day['start_dt'].format('YYYY-MM-DD')},
                'end': {'date': end_dt.format('YYYY-MM-DD')},  # Ensure trip spans multiple days
                'description': enhanced_desc,
                'colorId': '11'
            }
            print(f"  Starting new trip {current_trip['summary']} from {current_trip['start']['date']} to {current_trip['end']['date']}")

    # Finalize any remaining trip after the loop
    if current_trip:
        print(f"Final trip {current_trip['summary']} from {current_trip['start']['date']} to {current_trip['end']['date']}")
        events.append(current_trip)
        
    print(f"\nGenerated {len(events)} calendar events:")
    for i, event in enumerate(events):
        print(f"  {i+1}. {event['summary']} ({event['start']['date']} to {event['end']['date']})")
        print(f"     Description: {event['description'][:50]}...")

    return events
