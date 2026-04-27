import os
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

sp_search = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET")
))


def get_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
        scope="user-top-read",
        cache_handler=FlaskSessionCacheHandler(session)
    )


@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    query = ""
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            try:
                results = sp_search.search(q=query, type="track,album,artist", limit=10)
            except Exception as e:
                error = f"Error fetching results: {e}"

    return render_template("index.html", results=results, query=query, error=error)


@app.route("/login")
def login():
    return redirect(get_oauth().get_authorize_url() + "&show_dialog=true")


@app.route("/callback")
def callback():
    code = request.args.get("code")
    get_oauth().get_access_token(code)
    return redirect(url_for("top_tracks"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/top-tracks")
def top_tracks():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("login"))

    sp = spotipy.Spotify(auth=token_info["access_token"])
    tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
    return render_template("top_tracks.html", tracks=tracks["items"])


if __name__ == "__main__":
    app.run(debug=True)

#test
