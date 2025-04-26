import folium
import pandas as pd
import smtplib
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ------------------------- Hardcoded Inputs -------------------------
train_number = "22229"
train_name = "Vande Bharat Express"
journey_start_city = "Mumbai"
journey_end_city = "Goa"
derailment_city = "Chiplun"  # Midway city
start_time = "2025-05-01 06:00 AM"
derailment_time = "2025-05-01 09:30 AM"

# Email Settings
sender_email = "sumitpatelreso@gmail.com"
receiver_email = "sumitpatelreso@gmail.com"  # can send to multiple if needed
app_password = "rzbj dnrz fumt gnzk"  # <<< IMPORTANT: replace with your Gmail App Password (not login password)

# ------------------------- Setup -------------------------
geolocator = Nominatim(user_agent="train-derailment-system")

# Get Lat-Longs
def get_lat_lon(city_name):
    location = geolocator.geocode(city_name + ", India")
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

start_coords = get_lat_lon(journey_start_city)
end_coords = get_lat_lon(journey_end_city)
derailment_coords = get_lat_lon(derailment_city)

# Find Nearby Services
def find_nearby_services(lat, lon, amenity, radius=20000):
    import requests
    overpass_url = "https://overpass-api.de/api/interpreter"
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

hospitals = find_nearby_services(derailment_coords[0], derailment_coords[1], "hospital")
police_stations = find_nearby_services(derailment_coords[0], derailment_coords[1], "police")
ngos = find_nearby_services(derailment_coords[0], derailment_coords[1], "ngo")

# Combine
all_services = hospitals + police_stations + ngos
df_services = pd.DataFrame(all_services)
df_services.to_csv("derailment_contacts_log.csv", index=False)

# ------------------------- Send Email Alert -------------------------
def send_email_alert():
    subject = f"🚨 Emergency Alert: Train {train_number} Derailment at {derailment_city}"
    body = f"""
    Train Details:
    Train Number: {train_number}
    Train Name: {train_name}
    Start: {journey_start_city} ({start_time})
    Derailment: {derailment_city} ({derailment_time})
    Destination: {journey_end_city}

    Map + contacts saved locally.

    Immediate action required! 🚨
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, app_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()
    print("✅ Email alert sent successfully!")

send_email_alert()

# ------------------------- Create Map -------------------------
m = folium.Map(location=derailment_coords, zoom_start=10)

# Train Route
folium.PolyLine([start_coords, derailment_coords, end_coords], color="blue", weight=4, tooltip="Train Route").add_to(m)

# Derailment Spot
folium.Marker(
    derailment_coords,
    popup=f"🚂 Derailment\nTrain No: {train_number}\nAt: {derailment_city}",
    icon=folium.Icon(color="red", icon="train", prefix="fa")
).add_to(m)

# Draw Circles
for radius in [5000, 10000, 20000]:
    folium.Circle(
        radius=radius,
        location=derailment_coords,
        popup=f"{radius/1000} km zone",
        color="crimson",
        fill=True,
        fill_opacity=0.2
    ).add_to(m)

# Nearby Services
for place in all_services:
    color = "green" if place['Amenity'] == "hospital" else "blue" if place['Amenity'] == "police" else "purple"
    folium.Marker(
        location=[place['Latitude'], place['Longitude']],
        popup=f"{place['Name']} 📞 {place['Phone']}",
        icon=folium.Icon(color=color)
    ).add_to(m)

# Save map
m.save("derailment_emergency_map.html")
print("✅ Map saved as 'derailment_emergency_map.html'.")
print("✅ Emergency contacts saved as 'derailment_contacts_log.csv'.")
