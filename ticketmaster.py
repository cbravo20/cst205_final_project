"""
Cris Bravo, David Martinez, Gigi Powers, Nadine El-Kheshen, Wyatt Marvin
CST205
CST205 Final Project/Spotify Poster Generator
05/13/2026
Abstract: This Python file contains the functions for ticketmaster features.
https://developer.ticketmaster.com/products-and-docs/apis/getting-started/ 
"""

#made by David
import os
import requests


class Ticketmaster:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
    # Send a request to Ticketmaster to search events using a keyword 
    def search_events(self, keyword, size=10):
        params = {
            "keyword": keyword,
            "apikey": self.api_key,
            "size": size
        }
        response = requests.get(f"{self.base_url}/events.json", params=params, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def get_concerts(self, artist):
        concerts = []
        try:
             # Search Ticketmaster using the artist name from Spotify
            data = self.search_events(artist, size=10)
            events = data.get("_embedded", {}).get("events", [])
            # Loop through events and extract only needed fields 
            for event in events[:10]:
                concert = {
                    "artist": artist,
                    "name": event.get("name", "Unknown"),
                    "date": event.get("dates", {}).get("start", {}).get("localDate", "Date TBA"),
                    "venue": event.get("_embedded", {}).get("venues", [{}])[0].get("name", "Venue TBA"),
                    "city": event.get("_embedded", {}).get("venues", [{}])[0].get("city", {}).get("name", "City TBA"),
                    "url": event.get("url", "#")
                }
                concerts.append(concert)
        except Exception as e:
            pass
        
        return concerts


tm = Ticketmaster(api_key=os.environ.get("TICKETMASTER_API_KEY"))


def fetch_concerts_for_artists(artists):
    # Fetch concerts for a list of artists and return a combined list of concerts
    concerts = []
    for artist in artists:
         # Get concerts for each artist and add to main list
        concerts.extend(tm.get_concerts(artist))
    return concerts
