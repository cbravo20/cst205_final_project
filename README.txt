Spotify Poster Generator/CST205 Final Project

Cris Bravo, David Martinez, Gigi Powers, Nadine El-Kheshen, Wyatt Marvin
CST205
CST205 Final Project/Spotify Poster Generator
05/13/2026

How to Run: 
With python environment active run 
pip install python-dotenv
pip install spotipy

Create .env file in the root directory with the following lines
SPOTIFY_CLIENT_ID= fill in with your Spotify clied id
SPOTIFY_CLIENT_SECRET= fill in with spotify secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback
FLASK_SECRET_KEY=Anasjc83jn40

Run the flask app with 
python main.py
Or
flask --app main run

Open on a browser by going to 127.0.0.1:5000

Git Repo: https://github.com/cbravo20/cst205_final_project 