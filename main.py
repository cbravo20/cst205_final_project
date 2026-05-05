import os
from flask import Flask, render_template, request, redirect, session, url_for
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

openai_api_key = os.environ.get("OPENAI_API_KEY")

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
    query = request.args.get("query", "").strip()
    error = None
    albums = []
    artist_name = ""

    # This keeps the saved cart on the page.
    album_cart = session.get("album_cart", {})
    cart_items = list(album_cart.values())
    cart_ids = set(album_cart.keys())

    if request.method == "POST":
        query = request.form.get("query", "").strip()

    if query:
        try:
            results = sp_search.search(q=query, type="album", limit=10)
            if results and 'albums' in results and 'items' in results['albums']:
                albums = results['albums']['items']
                if albums:
                    artist_name = albums[0]['artists'][0]['name'] if albums[0]['artists'] else ""
        except Exception as e:
            error = f"Error fetching results: {e}"

    return render_template(
        "index.html",
        albums=albums,
        query=query,
        error=error,
        artist_name=artist_name,
        cart_items=cart_items,
        cart_ids=cart_ids
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
    # Check cart, then go to selected albums page.
    cart = session.get("album_cart", {})

    if len(cart) < 1 or len(cart) > 10:
        return redirect(url_for("index"))

    return redirect(url_for("selected_albums"))


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    # This route was added so checked albums can be saved in the cart.
    selected = request.form.getlist("selected_albums")

    if not selected:
        return redirect(url_for("index"))

    cart = session.get("album_cart", {})
    save_dir = os.path.join("static", "album_covers")
    os.makedirs(save_dir, exist_ok=True)

    for item in selected:
        try:
            album_id, name, img_url = item.split("|", 2)
        except ValueError:
            continue

        if album_id in cart:
            continue

        if len(cart) >= 10:
            break

        img_path = None

        if img_url:
            try:
                # Save the album cover image into static/album_covers.
                img_bytes = requests.get(img_url).content
                # Turn the downloaded image bytes into an image Pillow can open.
                img = Image.open(io.BytesIO(img_bytes))

                filename = name.replace(" ", "_").replace("/", "_").replace("\\", "_") + "_" + album_id + ".jpg"
                relative_path = "album_covers/" + filename
                full_path = os.path.join("static", relative_path)

                img.save(full_path)
                img_path = relative_path
            except Exception as e:
                print(f"Error saving image: {e}")
                img_path = None

        cart[album_id] = {
            "id": album_id,
            "name": name,
            "img_path": img_path
        }

    session["album_cart"] = cart
    query = request.form.get("query", "").strip()
    return redirect(url_for("index", query=query))



@app.route('/final-poster')
def final():
   return render_template('final_poster.html')

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart():
    # This route was added so albums can be removed from the cart.
    remove_ids = request.form.getlist("remove_album_ids")
    cart = session.get("album_cart", {})

    for album_id in remove_ids:
        item = cart.pop(album_id, None)
        if item and item.get("img_path"):
            # Delete the saved image file when the item is removed.
            full_path = os.path.join("static", item["img_path"])
            if os.path.exists(full_path):
                os.remove(full_path)

    session["album_cart"] = cart
    query = request.form.get("query", "").strip()
    return redirect(url_for("index", query=query))

@app.route("/selected-albums")
def selected_albums():
    return render_template("selected_albums.html", album_data=list(session.get("album_cart", {}).values()))

if __name__ == "__main__":
    app.run(debug=True)
