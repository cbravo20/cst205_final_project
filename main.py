import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")


def get_spotify_token():
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
    )
    return response.json().get("access_token")


def search_spotify(query, search_type="track,album,artist", limit=10):
    token = get_spotify_token()
    response = requests.get(
        "https://api.spotify.com/v1/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": search_type, "limit": limit},
    )
    return response.json()


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    query = ""
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            try:
                results = search_spotify(query)
            except Exception as e:
                error = f"Error fetching results: {e}"

    return render_template("index.html", results=results, query=query, error=error)


if __name__ == "__main__":
    app.run(debug=True)
