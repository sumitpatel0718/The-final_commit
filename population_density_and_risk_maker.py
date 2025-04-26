import folium
from geopy.geocoders import Nominatim
import random
import time

# ------------------- Settings -------------------

CITY_EVENTS = {
    "Mumbai": [
        ("MI vs CSK Match", "Wankhede Stadium", "April 28, 2025"),
        ("Siddhivinayak Darshan", "Siddhivinayak Temple", "April 29, 2025"),
        ("Marine Drive Food Festival", "Marine Drive", "April 30, 2025"),
    ],
    "Pune": [
        ("Marathon for Charity", "Shivaji Nagar", "April 28, 2025"),
        ("Ganpati Utsav", "Dagadusheth Temple", "April 29, 2025"),
        ("Rock Music Concert", "Balewadi Stadium", "April 30, 2025"),
    ],
    "Delhi": [
        ("Political Rally", "India Gate", "April 28, 2025"),
        ("International Trade Fair", "Pragati Maidan", "April 29, 2025"),
        ("Cultural Dance Show", "Siri Fort Auditorium", "April 30, 2025"),
    ],
    "Bangalore": [
        ("Startup Conclave", "Nimhans Convention Centre", "April 28, 2025"),
        ("IPL Match RCB vs CSK", "Chinnaswamy Stadium", "April 29, 2025"),
        ("Food Carnival", "Indiranagar", "April 30, 2025"),
    ],
    "Chennai": [
        ("Classical Music Night", "Music Academy", "April 28, 2025"),
        ("Marathon for Unity", "Marina Beach", "April 29, 2025"),
        ("CSK Fan Meet", "M.A. Chidambaram Stadium", "April 30, 2025"),
    ]
}

PAST_EVENT_INCIDENTS = {
    "Wankhede Stadium": ["Stampede during MI match"],
    "Siddhivinayak Temple": ["Overcrowding during darshan"],
    "Marine Drive": ["New Year overcrowding"],
    "India Gate": ["Protest chaos"],
    "Chinnaswamy Stadium": ["Stampede after IPL match"],
    "Marina Beach": ["Overcrowding during festivals"],
}

event_risk_levels = {
    "Cricket Match": "High",
    "Religious Gathering": "Moderate",
    "Music Concert": "Moderate",
    "Political Rally": "High",
    "Marathon": "Moderate",
    "Food Festival": "Low",
    "Trade Fair": "Moderate",
    "Cultural Show": "Low",
    "Other": "Low"
}

# ------------------- Functions -------------------

def classify_event_type(event_name):
    event_name = event_name.lower()
    if "cricket" in event_name or "match" in event_name:
        return "Cricket Match"
    elif "darshan" in event_name or "temple" in event_name or "pooja" in event_name:
        return "Religious Gathering"
    elif "music" in event_name or "concert" in event_name:
        return "Music Concert"
    elif "rally" in event_name or "protest" in event_name:
        return "Political Rally"
    elif "marathon" in event_name or "run" in event_name:
        return "Marathon"
    elif "food" in event_name or "carnival" in event_name or "festival" in event_name:
        return "Food Festival"
    elif "trade" in event_name or "fair" in event_name:
        return "Trade Fair"
    elif "dance" in event_name or "show" in event_name:
        return "Cultural Show"
    else:
        return "Other"

def analyze_event_risk(event_name, venue):
    event_type = classify_event_type(event_name)
    past_incident = PAST_EVENT_INCIDENTS.get(venue, None)
    base_risk = event_risk_levels.get(event_type, "Low")

    if past_incident:
        if base_risk == "Low":
            risk = "Moderate"
        elif base_risk == "Moderate":
            risk = "High"
        else:
            risk = "High"
    else:
        risk = base_risk

    # Random fluctuation
    if random.random() < 0.1:
        risk = "High" if risk == "Moderate" else risk

    return event_type, risk, past_incident

def suggest_precautions(risk_level):
    if risk_level == "High":
        return "🔴 Increase police, emergency exits, drones."
    elif risk_level == "Moderate":
        return "🟠 Extra staff, manage gates."
    else:
        return "🟢 Basic security sufficient."

def get_coordinates(place, city):
    geolocator = Nominatim(user_agent="crowd_predictor")
    try:
        location = geolocator.geocode(f"{place}, {city}", timeout=10)
        if location:
            return (location.latitude, location.longitude)
    except:
        time.sleep(1)
    return None

def risk_color(risk):
    if risk == "High":
        return "red"
    elif risk == "Moderate":
        return "orange"
    else:
        return "green"

def generate_crowd_scatter(base_lat, base_lon, risk_level, num_points=10):
    scattered_points = []
    for _ in range(num_points):
        lat_offset = random.uniform(-0.002, 0.002)
        lon_offset = random.uniform(-0.002, 0.002)
        scattered_points.append((base_lat + lat_offset, base_lon + lon_offset, risk_level))
    return scattered_points

# ------------------- Main Program -------------------

def main():
    print("\nAvailable Cities:", ', '.join(CITY_EVENTS.keys()))
    cities = input("\nEnter city names separated by commas (example: Mumbai,Pune,Delhi): ").strip().split(",")

    cities = [city.strip().capitalize() for city in cities]

    map_ = folium.Map(location=(20.5937, 78.9629), zoom_start=5)

    for city in cities:
        if city not in CITY_EVENTS:
            print(f"⚠️ No events hardcoded for {city}. Skipping...")
            continue

        events = CITY_EVENTS[city]
        print(f"\n🔎 Analyzing {city} events...")

        for name, venue, date_text in events:
            event_type, risk, past_incident = analyze_event_risk(name, venue)
            coords = get_coordinates(venue, city)

            if coords:
                base_lat, base_lon = coords

                # Main marker for event
                popup_text = f"🏟️ <b>{name}</b><br>" \
                             f"📍 Venue: {venue}<br>" \
                             f"📅 Date: {date_text}<br>" \
                             f"🎯 Type: {event_type}<br>" \
                             f"⚠️ Risk: {risk}<br>" \
                             f"💡 {suggest_precautions(risk)}"
                folium.Marker(
                    location=(base_lat, base_lon),
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=risk_color(risk))
                ).add_to(map_)

                # Scatter surrounding small points
                scattered = generate_crowd_scatter(base_lat, base_lon, risk)
                for lat, lon, r in scattered:
                    folium.CircleMarker(
                        location=(lat, lon),
                        radius=4,
                        color=risk_color(r),
                        fill=True,
                        fill_opacity=0.7
                    ).add_to(map_)

            # Print details to console
            print(f"📍 Event: {name}")
            print(f"    Venue: {venue}")
            print(f"    Date: {date_text}")
            print(f"    Type: {event_type}")
            print(f"    Predicted Risk: {risk}")
            if past_incident:
                print(f"    ⚠️ Past Incident(s): {past_incident}")
            print(f"    Suggested Precautions: {suggest_precautions(risk)}")
            print("-" * 60)

    map_.save("scattered_crowd_risk_map.html")
    print("\n✅ Crowd Risk Map saved as 'scattered_crowd_risk_map.html'. Open it!")

if __name__ == "__main__":
    main()
