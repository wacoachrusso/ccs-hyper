from bs4 import BeautifulSoup
import arrow
import re

class EnhancedParser:
    """
    Parses the detailed HTML from the CCS 'Print View'.
    Extracts pairings, flights, crew members, and other details.
    """
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.pairings = []

    def parse(self):
        """Main parsing method."""
        pairing_tables = self.soup.find_all('table', class_='pairing-details')
        for table in pairing_tables:
            pairing_data = self._parse_pairing_info(table)
            pairing_data['flights'] = self._parse_flight_info(table)
            pairing_data['crew'] = self._parse_crew_info(table)
            self.pairings.append(pairing_data)
        return self.pairings

    def _parse_pairing_info(self, table):
        """Parses the main pairing details from its table."""
        pairing_info = {}
        header = table.find('td', class_='pairing-header').text
        match = re.search(r'Pairing (\w+) - (\d{2}/\d{2}/\d{4})', header)
        if match:
            pairing_info['pairing_code'] = match.group(1)
            pairing_info['start_date'] = arrow.get(match.group(2), 'MM/DD/YYYY').format('YYYY-MM-DD')
        
        # Extract other details like Block, Credit, TFP
        # This requires inspecting the actual HTML structure
        return pairing_info

    def _parse_flight_info(self, table):
        """Parses all flight legs within a pairing."""
        flights = []
        flight_rows = table.find_all('tr', class_='flight-row')
        for row in flight_rows:
            flight = {}
            columns = row.find_all('td')
            flight['flight_number'] = columns[0].text.strip()
            flight['departure_airport'] = columns[1].text.strip()
            flight['arrival_airport'] = columns[2].text.strip()
            # ... parse other flight details (times, aircraft, etc.)
            flights.append(flight)
        return flights

    def _parse_crew_info(self, table):
        """Parses the crew list for a pairing."""
        crew = []
        crew_rows = table.find_all('tr', class_='crew-row')
        for row in crew_rows:
            member = {}
            columns = row.find_all('td')
            member['name'] = columns[0].text.strip()
            member['position'] = columns[1].text.strip()
            member['employee_id'] = columns[2].text.strip()
            # ... parse other crew details
            crew.append(member)
        return crew
