from flask import Flask, render_template, request, redirect, url_for
import requests
from services.tmdb_service import *
from database import get_connection
from config import TMDB_API_KEY, TMDB_BASE_URL

app = Flask(__name__)
app.secret_key = "week4_final_submission"

@app.route("/", methods=["GET", "POST"])
def index():
    trending, results = [], []
    try:
        res = requests.get(f"{TMDB_BASE_URL}/trending/all/day", params={"api_key": TMDB_API_KEY}, timeout=5)
        trending = res.json().get("results", [])[:10]
    except: pass
    if request.method == "POST":
        results = search_multi(request.form.get("query")).get("results", [])
    return render_template("index.html", results=results, trending=trending)

@app.route("/detail/<m_type>/<m_id>")
def detail(m_type, m_id):
    # 1. Fetch data using your service
    media = get_details(m_type, m_id)
    credits_data = get_credits(m_type, m_id)
    rec_data = get_recommendations(m_type, m_id) # Fetches similar movies

    # 2. Fetch Streaming Providers (Where to Watch)
    # We use a direct request here to ensure we hit the sub-resource correctly
    prov_url = f"{TMDB_BASE_URL}/{m_type}/{m_id}/watch/providers"
    prov_res = requests.get(prov_url, params={"api_key": TMDB_API_KEY}).json()
    # 'IN' is for India, change to 'US' if needed
    providers = prov_res.get("results", {}).get("IN", {}) 

    conn = get_connection()
    # History tracking
    try:
        conn.execute("INSERT INTO history (media_id, title, poster, media_type) VALUES (?,?,?,?)",
                     (m_id, media.get('title') or media.get('name'), media.get('poster_path'), m_type))
        conn.commit()
    except: pass

    # Check database status
    watch = conn.execute("SELECT * FROM watchlist WHERE media_id=?", (m_id,)).fetchone()
    fav = conn.execute("SELECT * FROM favorites WHERE media_id=?", (m_id,)).fetchone()
    reviews = conn.execute("SELECT * FROM reviews WHERE media_id=?", (m_id,)).fetchall()
    conn.close()

    return render_template("movie.html", 
                           media=media, 
                           cast=credits_data.get("cast", [])[:8], 
                           recommendations=rec_data.get("results", [])[:6], # Pass this to HTML
                           reviews=reviews, 
                           m_type=m_type, 
                           in_watchlist=watch, 
                           in_favorites=fav, 
                           providers=providers, # Pass this to HTML
                           share_url=request.url)

@app.route("/dashboard")
def dashboard():
    conn = get_connection()
    stats = {
        'watched': conn.execute("SELECT COUNT(*) FROM history").fetchone()[0],
        'favs': conn.execute("SELECT COUNT(*) FROM favorites").fetchone()[0],
        'reviews': conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        'recent': conn.execute("SELECT * FROM history ORDER BY watched_at DESC LIMIT 5").fetchall()
    }
    conn.close()
    return render_template("dashboard.html", stats=stats)

# --- CUSTOM COLLECTIONS (Week 4 Updated) ---
@app.route("/collections", methods=["GET", "POST"])
def collections():
    conn = get_connection()
    if request.method == "POST":
        # We allow multiple movies to have the same collection_name
        conn.execute("INSERT INTO collections (collection_name, media_id, title, poster, media_type) VALUES (?,?,?,?,?)",
                     (request.form['c_name'], request.form['m_id'], request.form['title'], request.form['poster'], request.form['m_type']))
        conn.commit()
        return redirect("/collections")
    
    # Fetch all items, ordered by collection name to group them in the UI
    data = conn.execute("SELECT * FROM collections ORDER BY collection_name").fetchall()
    conn.close()
    return render_template("collections.html", collections=data)

@app.route("/remove_collection/<int:id>")
def remove_collection(id):
    conn = get_connection()
    conn.execute("DELETE FROM collections WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/collections")

@app.route("/watchlist")
def watchlist():
    conn = get_connection()
    movies = conn.execute("SELECT * FROM watchlist").fetchall()
    conn.close()
    return render_template("watchlist.html", movies=movies)

@app.route("/favorites")
def favorites():
    conn = get_connection()
    movies = conn.execute("SELECT * FROM favorites").fetchall()
    conn.close()
    return render_template("favorites.html", movies=movies)

@app.route("/remove_watchlist/<m_id>")
def remove_watchlist(m_id):
    conn = get_connection()
    conn.execute("DELETE FROM watchlist WHERE media_id=?", (m_id,))
    conn.commit()
    conn.close()
    return redirect("/watchlist")

@app.route("/remove_favorites/<m_id>")
def remove_favorites(m_id):
    conn = get_connection()
    conn.execute("DELETE FROM favorites WHERE media_id=?", (m_id,))
    conn.commit()
    conn.close()
    return redirect("/favorites")

@app.route("/add_<list_type>", methods=["POST"])
def add_to_list(list_type):
    conn = get_connection()
    conn.execute(f"INSERT OR IGNORE INTO {list_type} (media_id, title, poster, media_type) VALUES (?,?,?,?)",
                 (request.form['m_id'], request.form['title'], request.form['poster'], request.form['m_type']))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route("/add_review", methods=["POST"])
def add_review():
    conn = get_connection()
    conn.execute("INSERT INTO reviews (media_id, rating, review) VALUES (?,?,?)",
                 (request.form['m_id'], request.form['rating'], request.form['review']))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route("/history")
def history():
    conn = get_connection()
    data = conn.execute("SELECT * FROM history ORDER BY watched_at DESC").fetchall()
    conn.close()
    return render_template("history.html", history=data)

@app.route("/discover")
def discover():
    params = {"api_key": TMDB_API_KEY, "sort_by": "popularity.desc",
              "with_genres": request.args.get("genre"), "primary_release_year": request.args.get("year"),
              "vote_average.gte": request.args.get("rating")}
    res = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params).json()
    return render_template("discover.html", results=res.get("results", []))

if __name__ == "__main__":
    app.run(debug=True)
