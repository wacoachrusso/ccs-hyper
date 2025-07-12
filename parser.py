from bs4 import BeautifulSoup
import arrow
import re

def parse_and_group_schedule(html_content):
    """DEPRECATED: Parses the simple master schedule HTML and groups trips."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the month and year from the header
    header = soup.find('div', class_='sg-header-text')
    month_year_str = header.text.strip() if header else 'July 2025'
    month_name, year_str = month_year_str.split()
    month = list(arrow.locales.EnglishLocale.month_names).index(month_name)
    year = int(year_str)

    trips = []
    current_trip = None

    for row in soup.find_all('div', class_='sg-data-row'):
        pairing_div = row.find('div', class_='sg-pairing')
        if not pairing_div:
            continue

        pairing_code = pairing_div.text.strip()
        
        # If it's a new trip, start a new group
        if current_trip is None or current_trip['pairing_code'] != pairing_code:
            if current_trip:
                trips.append(current_trip)
            current_trip = {
                'pairing_code': pairing_code,
                'description': '',
                'start_date': None,
                'end_date': None,
                'days': []
            }

        # Extract details for the day
        day_details = {}
        day_cell = row.find('div', title=re.compile(r'Date: (\d+/\d+/\d+)'))
        if day_cell:
            day_num = int(day_cell.text.strip())
            day_details['date'] = arrow.get(year, month, day_num).format('YYYY-MM-DD')
            if not current_trip['start_date']:
                current_trip['start_date'] = day_details['date']
            current_trip['end_date'] = arrow.get(day_details['date']).shift(days=+1).format('YYYY-MM-DD')

        desc_rows = row.find_all('div', class_='sg-description-row')
        full_day_description = []
        for desc_row in desc_rows:
            label = desc_row.find('div', class_='sg-description-label').text.strip()
            value = desc_row.find('div', class_='sg-description-data').text.strip()
            day_details[label.lower().replace(':', '')] = value
            full_day_description.append(f"{label} {value}")
        
        current_trip['description'] += '\n'.join(full_day_description) + '\n\n'
        current_trip['days'].append(day_details)

    # Append the last trip
    if current_trip:
        trips.append(current_trip)

    return trips, month, year
