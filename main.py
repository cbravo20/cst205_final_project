"""
Cris Bravo, David Martinez, Gigi Powers, Nadine El-Kheshen, Wyatt Marvin
CST205
CST205 Final Project/Spotify Poster Generator
05/13/2026
Abstract: This Python Flask web app uses the Spotify API to retreive album covers
to generate posters for the user. The user can also sign in to their account and retrieve their
top 10 tracks to use those album covers as well. Users can apply the effects from previous labs/hw
such as sepia, negative and greyscale. 

Spotipy Documentation was used to code the spotipy functions such as get_oauth()
https://spotipy.readthedocs.io/en/2.22.1/

Github: https://github.com/cbravo20/cst205_final_project 
Trello: https://trello.com/invite/b/69e6a245782a29d61c5b40fb/ATTIa5cdad7183d8c44247a3b8fba2ed83a666994ACE/cst205-final-project 
"""

#initial app was made by Cris
#Wyatt, Gigi, Nadine primarily worked on the HTML pages and stylizing them
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import requests
from PIL import Image
import io
from spotipy.cache_handler import FlaskSessionCacheHandler
from effects import EFFECTS, make_album_collage, original_img_path
from ticketmaster import fetch_concerts_for_artists

#loads env variables from .env file(ex. Spotify api key)
load_dotenv()

#creates the flask app and sets the secret key for session cookies
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

#public spotify client used for album searches (no user login required)
sp_search = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET")
))


#taken from spotipy documentation, returns a SpotifyOAuth object for user login with the user-top-read
def get_oauth():
    return SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"),
        scope="user-top-read",
        cache_handler=FlaskSessionCacheHandler(session)
    )


#main search page, searches spotify for albums matching the user's query
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
            #searches spotify for albums and returns up to 10 results
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


#redirects the user to spotify's login page
@app.route("/login")
def login():
    return redirect(get_oauth().get_authorize_url() + "&show_dialog=true")


#spotify redirects here after login, exchanges the auth code for an access token
@app.route("/callback")
def callback():
    code = request.args.get("code")
    get_oauth().get_access_token(code)
    return redirect(url_for("top_tracks"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#made by Cris
#fetches the logged-in user's top 10 tracks from the last 4 weeks
@app.route("/top-tracks")
def top_tracks():
    oauth = get_oauth()
    token_info = oauth.get_cached_token()
    if not token_info:
        return redirect(url_for("login"))

    sp = spotipy.Spotify(auth=token_info["access_token"])
    tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")

    album_cart = session.get("album_cart", {})
    cart_items = list(album_cart.values())
    cart_ids = set(album_cart.keys())

    return render_template("top_tracks.html", tracks=tracks["items"],
                           cart_items=cart_items, cart_ids=cart_ids)

#worked on by David
@app.route("/select-albums", methods=["POST"])
def select_albums():
    # Check cart, then go to selected albums page.
    cart = session.get("album_cart", {})

    if len(cart) < 1 or len(cart) > 10:
        return redirect(url_for("index"))

    return redirect(url_for("selected_albums"))

#worked on by David and Cris
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
        artist_name = ""

        if img_url:
            try:
                # Save the album cover image into static/album_covers.
                img_bytes = requests.get(img_url).content
                # Turn the downloaded image bytes into an image Pillow can open.
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

                filename = name.replace(" ", "_").replace("/", "_").replace("\\", "_") + "_" + album_id + ".jpg"
                relative_path = "album_covers/" + filename
                full_path = os.path.join("static", relative_path)

                img.save(full_path)
                img_path = relative_path
            except Exception as e:
                print(f"Error saving image: {e}")
                img_path = None
        
        try:
            sp_album = sp_search.album(album_id)
            if sp_album.get("artists"):
                artist_name = sp_album["artists"][0]["name"]
        except Exception as e:
            print(f"Error fetching album details: {e}")

        cart[album_id] = {
            "id": album_id,
            "name": name,
            "img_path": img_path,
            "artist": artist_name
        }

    session["album_cart"] = cart
    redirect_to = request.form.get("redirect_to", "index")
    if redirect_to == "top_tracks":
        return redirect(url_for("top_tracks"))
    query = request.form.get("query", "").strip()
    return redirect(url_for("index", query=query))

#worked on by Wyatt
@app.route('/final-poster')
def final():
    collage_path = session.get("collage_path")
    concerts = session.get("concerts", [])
    return render_template('final_poster.html', collage_path=collage_path, concerts=concerts)

#by Cris and David
@app.route('/generate-collage')
def generate_collage():
    # grab all image paths from the cart, skipping any that didn't save properly
    cart = session.get("album_cart", {})
    image_paths = [
        os.path.join("static", item["img_path"])
        for item in cart.values()
        if item.get("img_path")
    ]

    if not image_paths:
        flash("No images to generate a collage.")
        return redirect(url_for("selected_albums"))

    # make sure the output folder exists before saving
    save_dir = os.path.join("static", "final_poster")
    os.makedirs(save_dir, exist_ok=True)
    output_path = os.path.join(save_dir, "collage.jpg")

    # build the collage and store the path in session so final-poster can show it
    if len(image_paths) == 6:
        make_album_collage(image_paths, output_path, cols=2)
    elif len(image_paths) == 9:
        make_album_collage(image_paths, output_path, cols=3)
    else:
        make_album_collage(image_paths, output_path)

    artists = []
    for item in cart.values():
        artist_name = item.get("artist")
        if artist_name and artist_name not in artists:
            artists.append(artist_name)

    #Feeds spotify api artist into ticketmaster to get concert data
    session["concerts"] = fetch_concerts_for_artists(artists)
    session["collage_path"] = "final_poster/collage.jpg"
    return redirect(url_for("final"))

#worked on by David
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
    redirect_to = request.form.get("redirect_to", "index")
    if redirect_to == "top_tracks":
        return redirect(url_for("top_tracks"))
    query = request.form.get("query", "").strip()
    return redirect(url_for("index", query=query))

@app.route("/selected-albums")
def selected_albums():
    return render_template("selected_albums.html", album_data=list(session.get("album_cart", {}).values()))

#worked on by Cris
@app.route("/apply-effect", methods=["POST"])
def apply_effect():
    img_path = request.form.get("img_path")
    effect = request.form.get("effect")
    album_id = request.form.get("album_id")

    # always apply to the original so effects dont combine
    img_path = original_img_path(img_path)
    full_path = os.path.join("static", img_path)

    try:
        # run the effect and save the result path back into the cart
        new_full_path = EFFECTS[effect](full_path)
        new_relative = os.path.relpath(new_full_path, "static")
        album_cart = session.get("album_cart", {})
        if album_id in album_cart:
            album_cart[album_id]["img_path"] = new_relative
            session["album_cart"] = album_cart
    except Exception as e:
        flash(f"Error applying effect: {e}")

    return redirect(url_for("selected_albums"))


if __name__ == "__main__":
    app.run(debug=True)