import folium
import requests
import pandas as pd
from geopy.distance import geodesic
import speech_recognition as sr
from geopy.geocoders import Nominatim

# ---------------- Setup ----------------
journey_start = (18.9398, 72.8355)  # Mumbai
journey_end = (15.2993, 74.1240)    # Goa

overpass_url = "https://overpass-api.de/api/interpreter"

recognizer = sr.Recognizer()

# ---------------- Functions ----------------
def listen_command():
    with sr.Microphone() as source:
        print("🎤 Please say: Train Number and Derailment Location...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"📝 You said: {text}")
        return text
    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return None
    except sr.RequestError:
        print("❌ Speech service unavailable")
        return None

def extract_train_and_location(text):
    import re
    train_number = re.findall(r'\d+', text)
    location_words = [word for word in text.split() if word.isalpha()]
    location = location_words[-1] if location_words else None
    return (train_number[0] if train_number else None), location

def get_lat_lon(place_name):
    geolocator = Nominatim(user_agent="train_derailment_voice")
    location = geolocator.geocode(place_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

def find_nearby_services(lat, lon, amenity, radius=20000):
    query = f"""
    [out:json];
    node
      [amenity={amenity}]
      (around:{radius},{lat},{lon});
    out;
    """
    response = requests.post(overpass_url, data={'data': query})
    data = response.json()
    results = []
    for element in data.get('elements', []):
        name = element['tags'].get('name', 'Unnamed')
        phone = element['tags'].get('phone', 'Not Available')
        lat_ = element['lat']
        lon_ = element['lon']
        distance = round(geodesic((lat, lon), (lat_, lon_)).km, 2)
        results.append({
            'Name': name,
            'Phone': phone,
            'Amenity': amenity,
            'Latitude': lat_,
            'Longitude': lon_,
            'Distance (km)': distance
        })
    return results

# ---------------- Main Execution ----------------
text = listen_command()

if text:
    train_number, derailment_location = extract_train_and_location(text)
    
    if train_number and derailment_location:
        print(f"🚂 Train Number: {train_number}")
        print(f"📍 Location: {derailment_location}")

        derailment_lat, derailment_lon = get_lat_lon(derailment_location)

        if derailment_lat and derailment_lon:
            print("🔍 Finding nearby services...")

            hospitals = find_nearby_services(derailment_lat, derailment_lon, "hospital")
            police_stations = find_nearby_services(derailment_lat, derailment_lon, "police")
            ngos = find_nearby_services(derailment_lat, derailment_lon, "ngo")

            # Combine and Save
            all_services = hospitals + police_stations + ngos
            df_contacts = pd.DataFrame(all_services)
            df_contacts.to_csv("emergency_contacts_voice.csv", index=False)
            print("✅ Contacts saved to 'emergency_contacts_voice.csv'.")

            # Plot Map
            print("🗺️ Creating map...")
            m = folium.Map(location=[derailment_lat, derailment_lon], zoom_start=11)

            folium.PolyLine([journey_start, (derailment_lat, derailment_lon), journey_end],
                            color="blue", weight=4, tooltip="Train Path").add_to(m)

            folium.Marker(
                location=[derailment_lat, derailment_lon],
                popup=f"🚂 Derailment Spot\nTrain No: {train_number}\nLocation: {derailment_location}",
                icon=folium.Icon(color="red", icon="train", prefix="fa")
            ).add_to(m)

            for radius in [5000, 10000, 20000]:
                folium.Circle(
                    radius=radius,
                    location=[derailment_lat, derailment_lon],
                    popup=f"{radius/1000} km zone",
                    color="crimson",
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)

            for place in hospitals + police_stations + ngos:
                icon_color = "green" if place['Amenity'] == "hospital" else "blue" if place['Amenity'] == "police" else "purple"
                folium.Marker(
                    location=[place['Latitude'], place['Longitude']],
                    popup=f"{place['Name']} 📞 {place['Phone']}",
                    icon=folium.Icon(color=icon_color)
                ).add_to(m)

            m.save("train_derailment_voice_map.html")
            print("✅ Map saved as 'train_derailment_voice_map.html'.")

        else:
            print("❌ Unable to geocode the derailment location.")
    else:
        print("❌ Could not extract Train Number and Location properly.")
