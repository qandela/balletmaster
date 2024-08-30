import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def search_wikidata(name):
    """
    Search Wikidata for the given name and retrieve the first matching QID.
    """
    search_url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'en',
        'search': name
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()  # Raise an HTTPError if the status is 4xx or 5xx
        data = response.json()
        
        if data.get('search'):
            # Return the QID of the first result
            qid = data['search'][0]['id']
            return qid
        else:
            print(f"No results found for '{name}'")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for '{name}': {e}")
        return None

def get_displayed_items_count(qid):
    """
    Get the number of displayed items from the 'WhatLinksHere' page for the given QID.
    """
    url = f'https://www.wikidata.org/wiki/Special:WhatLinksHere/{qid}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError if the status is 4xx or 5xx
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Search for either "Displayed X items" or "Displayed 1 item" using 'string' instead of 'text'
        displayed_text = soup.find(string=lambda t: t and "Displayed" in t and "item" in t)
        
        if displayed_text:
            # Extract the number from the displayed text
            try:
                num_items = int(displayed_text.split()[1])
                return num_items
            except ValueError:
                print("Could not extract the number of items from the displayed text.")
                return None
        else:
            print("Could not find the displayed items count.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request error for QID {qid}: {e}")
        return None

def main():
    # List of names to search for
    data = pd.read_csv('balletmasters_final.csv')
    names = data['ballet_master']
    
    # Open a file to write results incrementally
    with open('wikidata_results.csv', 'w') as file:
        # Write the header
        file.write('Name,QID,Displayed Items Count\n')
        
        for name in names:
            retries = 3  # Number of retries if an error occurs
            
            while retries > 0:
                print(f"Searching for '{name}'...")
                qid = search_wikidata(name)
                
                if qid:
                    print(f"Found QID: {qid}")
                    count = get_displayed_items_count(qid)
                    if count is not None:
                        print(f"Displayed items: {count}")
                        # Write the result directly to the CSV file
                        file.write(f"{name},{qid},{count}\n")
                        break
                    else:
                        print(f"Error processing '{name}', retrying...")
                else:
                    print(f"Error finding QID for '{name}', retrying...")
                
                retries -= 1
                if retries > 0:
                    print(f"Waiting for 5 seconds before retrying...")
                    time.sleep(5)
                else:
                    print(f"Skipping '{name}' after multiple failed attempts.")
                    # Log the name with no result in the CSV
                    file.write(f"{name},N/A,N/A\n")

if __name__ == "__main__":
    main()
