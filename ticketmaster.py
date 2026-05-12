import os
import requests


class Ticketmaster:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
    
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
            data = self.search_events(artist, size=10)
            events = data.get("_embedded", {}).get("events", [])
            
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
    concerts = []
    for artist in artists:
        concerts.extend(tm.get_concerts(artist))
    return concerts
