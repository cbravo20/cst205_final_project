import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from PIL import Image
import io
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
    albums = []
    artist_name = ""

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            try:
                results = sp_search.search(q=query, type="album", limit=10)
                if results and 'albums' in results and 'items' in results['albums']:
                    albums = results['albums']['items']
                    if albums:
                        # Use the first album's artist as the artist_name for the UI
                        artist_name = albums[0]['artists'][0]['name'] if albums[0]['artists'] else ""
            except Exception as e:
                error = f"Error fetching results: {e}"

    return render_template(
        "index.html",
        albums=albums,
        query=query,
        error=error,
        artist_name=artist_name
    )


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


@app.route("/select-albums", methods=["POST"])
def select_albums():
    selected = request.form.getlist("selected_albums")

    if len(selected) < 1 or len(selected) > 8:
        flash("Select 1 to 8 album covers.")
        return redirect(url_for("index"))

    album_data = []
    save_dir = os.path.join("static", "album_covers")
    os.makedirs(save_dir, exist_ok=True)

    for item in selected:
        name, img_url = item.split("|")

        try:
            img_bytes = requests.get(img_url).content
            img = Image.open(io.BytesIO(img_bytes))

            filename = name.replace(" ", "_") + ".jpg"
            relative_path = f"album_covers/{filename}"
            full_path = os.path.join("static", relative_path)

            img.save(full_path)

            album_data.append({
                "name": name,
                "img_path": relative_path
            })

        except:
            album_data.append({
                "name": name,
                "img_path": None
            })

    return render_template("selected_albums.html", album_data=album_data)


if __name__ == "__main__":
    app.run(debug=True)
