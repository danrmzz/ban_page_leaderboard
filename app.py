from flask import Flask, render_template
import json

app = Flask(__name__)

# Function to read the leaderboard JSON file
def read_leaderboard():
    with open('webscrape/top10.json', 'r') as f:
        leaderboard = json.load(f)
    return leaderboard

@app.route('/')
def index():
    top_10_sorted = read_leaderboard()
    return render_template('index.html', top_10_sorted=top_10_sorted)

if __name__ == '__main__':
    app.run(debug=True)
