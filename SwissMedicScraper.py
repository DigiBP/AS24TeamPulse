import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time

class SwissMedicScraper:
    def __init__(self):
        self.base_url = "https://www.spezialitätenliste.ch/ShowPreparations.aspx"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'de-CH,de;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def extract_form_data(self, soup):
        """Extract hidden form fields required for POST requests"""
        form_data = {}
        for input_tag in soup.find_all('input', type='hidden'):
            if input_tag.get('name'):
                form_data[input_tag['name']] = input_tag.get('value', '')
        return form_data

    def parse_medication_row(self, row):
        """Parse a single medication row from the table"""
        cols = row.find_all('td')
        if len(cols) < 20:  # Ensure row has enough columns
            return None
        
        return {
            'name': cols[1].get_text(strip=True),
            'form_dosage': cols[2].get_text(strip=True),
            'package': cols[3].get_text(strip=True),
            'fap_price': cols[4].get_text(strip=True),  # Factory price
            'pp_price': cols[5].get_text(strip=True),   # Public price
            'last_change': cols[6].get_text(strip=True),
            'swissmedic_code': cols[11].get_text(strip=True),
            'manufacturer': cols[12].get_text(strip=True),
            'active_substance': cols[13].get_text(strip=True),
            'bag_dossier': cols[14].get_text(strip=True),
            'approval_date': cols[15].get_text(strip=True),
            'atc_code': cols[21].get_text(strip=True)
        }

    def scrape_medications(self, search_type='PreparationName', search_value=''):
        """Scrape medication data with optional search parameters"""
        try:
            # Initial GET request to get form data
            session = requests.Session()
            response = session.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get form data
            form_data = self.extract_form_data(soup)
            
            # Add search parameters
            form_data.update({
                'ctl00$cphContent$ucSearchBoxPreparations$ddlSearchType': search_type,
                'ctl00$cphContent$ucSearchBoxPreparations$txtSearchValue': search_value,
                'ctl00$cphContent$ucSearchBoxPreparations$btnSearch': 'Suchen'
            })
            
            # Make POST request with search parameters
            response = session.post(self.base_url, data=form_data, headers=self.headers)
            response.raise_for_status()
            
            # Parse the results
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'id': 'ctl00_cphContent_gvwPreparations'})
            
            if not table:
                return pd.DataFrame()
            
            medications = []
            for row in table.find_all('tr', class_=['rowstyle', 'alternatingrowstyle']):
                med_data = self.parse_medication_row(row)
                if med_data:
                    medications.append(med_data)
            
            # Convert to DataFrame
            df = pd.DataFrame(medications)
            
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'swiss_medications_{timestamp}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            return df
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return pd.DataFrame()

def main():
    scraper = SwissMedicScraper()
    
    # Example search for medications
    df = scraper.scrape_medications(search_type='PreparationName', search_value='')
    
    if not df.empty:
        print(f"Successfully scraped {len(df)} medications")
        print("\nFirst few entries:")
        print(df.head())
    else:
        print("No data found or error occurred")

if __name__ == "__main__":
    main()
