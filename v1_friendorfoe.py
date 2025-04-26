import networkx as nx
import matplotlib.pyplot as plt
import spacy
import pandas as pd

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Step 1: Ask user for input
sentence = input("Enter a geopolitical conflict statement (e.g. 'China attacked India'): ")

# Step 2: Extract countries (GPE = GeoPolitical Entity)
doc = nlp(sentence)
countries = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

if len(countries) < 2:
    print("❌ Could not detect two countries. Please try again.")
    exit()

attacker, defender = countries[0], countries[1]
print(f"🔍 Attacker: {attacker}, Defender: {defender}")

# Step 3: Load CSVs
alliances_df = pd.read_csv("alliancess.csv")
conflict_df = pd.read_csv("conflict_historys.csv")
trade_df = pd.read_csv("trade_volumes.csv")

# Step 4: Normalize country pairs
def normalize_pair(row):
    return tuple(sorted([row['country_a'], row['country_b']]))

alliances_df['pair'] = alliances_df.apply(normalize_pair, axis=1)
conflict_df['pair'] = conflict_df.apply(normalize_pair, axis=1)
trade_df['pair'] = trade_df.apply(normalize_pair, axis=1)

# Step 5: Merge all datasets
merged = pd.merge(alliances_df[['pair', 'alliance_strength']], conflict_df[['pair', 'conflict_severity']], on='pair', how='outer')
merged = pd.merge(merged, trade_df[['pair', 'trade_volume_usd_billion']], on='pair', how='outer')
merged = merged.fillna(0)

# Step 6: Scoring function
def calculate_score(row):
    return (
        0.5 * row['alliance_strength'] +
        0.3 * (row['trade_volume_usd_billion'] / 700) - 
        0.2 * row['conflict_severity']
    )

merged['support_score'] = merged.apply(calculate_score, axis=1)

# Step 7: Get supporters
def get_supporters(attacker, defender, top_n=5):
    countries = set([a for pair in merged['pair'] for a in pair])
    countries.discard(attacker)
    countries.discard(defender)
    
    attacker_scores = []
    defender_scores = []
    
    for country in countries:
        pair_attacker = tuple(sorted([country, attacker]))
        pair_defender = tuple(sorted([country, defender]))
        
        row_attacker = merged[merged['pair'] == pair_attacker]
        row_defender = merged[merged['pair'] == pair_defender]
        
        attacker_score = row_attacker['support_score'].values[0] if not row_attacker.empty else 0
        defender_score = row_defender['support_score'].values[0] if not row_defender.empty else 0
        
        attacker_scores.append((country, attacker_score))
        defender_scores.append((country, defender_score))
    
    attacker_scores.sort(key=lambda x: x[1], reverse=True)
    defender_scores.sort(key=lambda x: x[1], reverse=True)
    
    return {
        f"Supports {attacker}": attacker_scores[:top_n],
        f"Supports {defender}": defender_scores[:top_n]
    }

# Step 8: Run prediction
result = get_supporters(attacker, defender)

# Step 9: Beautified visualization
def visualize_console_graph(attacker, defender, result_dict):
    G = nx.Graph()
    G.add_node(attacker, size=3000, color='skyblue')
    G.add_node(defender, size=3000, color='salmon')

    print("\n📊 Console Graph Representation:\n")

    # Add supporters and print them
    for label, supporters in result_dict.items():
        target = attacker if attacker in label else defender
        print(f"{target} is supported by:")
        for supporter, score in supporters:
            print(f"  → {supporter} (Score: {score:.2f})")
            G.add_node(supporter)
            G.add_edge(supporter, target, weight=score)

    # Set color and size for nodes and edges based on score
    node_colors = []
    node_sizes = []
    for node in G.nodes():
        if node == attacker:
            node_colors.append('skyblue')
            node_sizes.append(3000)  # Attacker node is large
        elif node == defender:
            node_colors.append('salmon')
            node_sizes.append(3000)  # Defender node is large
        else:
            node_colors.append('lightgray')  # Neutral countries
            node_sizes.append(1500)

    edge_colors = []
    edge_weights = []
    for u, v in G.edges():
        score = G[u][v]['weight']
        if score > 0.3:
            edge_colors.append('green')
        elif score <= 0:
            edge_colors.append('red')
        else:
            edge_colors.append('gray')
        edge_weights.append(max(1.0, abs(score) * 5))  # Larger edge weight for stronger relationships

    # Layout and drawing
    pos = nx.spring_layout(G, seed=42, k=0.15)  # Adjust k for better spacing
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, alpha=0.7)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, width=edge_weights, alpha=0.7)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', font_color='black')

    plt.title(f"🌍 Geopolitical Support and Opposition: {attacker} vs {defender}")
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# Step 10: Call visualizer
visualize_console_graph(attacker, defender, result)
