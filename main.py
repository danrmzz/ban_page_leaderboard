from collections import Counter
import json
import glob

# Initialize the counter for usernames
final_counts = Counter()

# Load and merge top 10 players from all JSON files
for file_name in glob.glob("results*.json"):
    with open(file_name, 'r') as f:
        top_players = json.load(f)
        final_counts.update(dict(top_players))

# Get the top 10 players
top_players = final_counts.most_common()

# Sort top players lexicographically if they have the same count
sorted_top_players = sorted(top_players, key=lambda x: (-x[1], x[0].lower()))

# Get the top 10 sorted players
top_10_sorted = sorted_top_players[:10]

# Print the top 10 players
print("Final Leaderboard:")
for username, count in top_10_sorted:
    print(f"{username}: {count}")
