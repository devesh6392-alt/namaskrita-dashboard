import streamlit as st
import google.generativeai as genai
import swisseph as swe
import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Namaskrita Astro Solutions", layout="wide")

# --- SIDEBAR INPUTS ---
st.sidebar.title("🔮 Namaskrita Astro")
st.sidebar.subheader("Client Details")

name = st.sidebar.text_input("Name", "Client Name")
dob = st.sidebar.date_input("Date of Birth", datetime.date(2000, 1, 1))
tob = st.sidebar.time_input("Time of Birth", datetime.time(12, 0))

# --- NEW: ROBUST LOCATION INPUT ---
st.sidebar.markdown("### 📍 Location Details")
st.sidebar.info("If City Search fails, these Manual Coordinates will be used.")
city_name = st.sidebar.text_input("City Name (Try first)", "Udaipur")
lat_manual = st.sidebar.number_input("Manual Latitude", value=24.5854, format="%.4f")
lon_manual = st.sidebar.number_input("Manual Longitude", value=73.7125, format="%.4f")

st.sidebar.markdown("---")
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# --- HELPER FUNCTIONS ---

def get_lat_lon(city):
    """Try to find city, return None if fails."""
    try:
        # We use a specific timeout and user_agent to avoid blocking
        geolocator = Nominatim(user_agent="namaskrita_astro_v2_fix", timeout=10)
        location = geolocator.geocode(city)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def calculate_chart(date, time, lat, lon):
    # Convert to Julian Day
    jd = swe.julday(date.year, date.month, date.day, time.hour + time.minute/60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
        "Venus": swe.VENUS, "Saturn": swe.SATURN, 
        "Rahu": swe.MEAN_NODE
    }
    
    chart_data = []
    
    # Calculate Ascendant
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'A', swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]
    chart_data.append({"Planet": "Lagna (Asc)", "Degree": f"{asc_deg:.2f}", "Zodiac": get_zodiac_name(asc_deg)})

    for p_name, p_id in planets.items():
        res = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        
        # Format Safe-Guard
        if isinstance(res, tuple):
            if isinstance(res[0], tuple):
                deg = res[0][0]
            else:
                deg = res[0]
        else:
            deg = float(res)
            
        chart_data.append({"Planet": p_name, "Degree": f"{deg:.2f}", "Zodiac": get_zodiac_name(deg)})
        
    # Calculate Ketu
    rahu_data = next(item for item in chart_data if item["Planet"] == "Rahu")
    ketu_deg = (float(rahu_data['Degree']) + 180) % 360
    chart_data.append({"Planet": "Ketu", "Degree": f"{ketu_deg:.2f}", "Zodiac": get_zodiac_name(ketu_deg)})
    
    return chart_data

def get_zodiac_name(lon):
    lon = lon % 360
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(lon / 30)]

# --- MAIN APP LOGIC ---

st.title(f"✨ {name}'s Vedic Chart Analysis")

if st.sidebar.button("Generate Report"):
    if not api_key:
        st.error("Please enter a Google Gemini API Key in the sidebar.")
    else:
        with st.spinner("Locating & Calculating..."):
            
            # --- LOCATION LOGIC ---
            # 1. Try to find the city
            lat, lon = get_lat_lon(city_name)
            
            # 2. If City fails, use the Manual Numbers from sidebar
            used_manual = False
            if lat is None:
                lat = lat_manual
                lon = lon_manual
                used_manual = True
            
            # --- CALCULATION ---
            if lat is not None:
                try:
                    chart_data = calculate_chart(dob, tob, lat, lon)
                    
                    # Create Tabs
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Planetary Data", "🤖 AI Prediction", "💎 Remedies", "💰 Crypto & Wealth"])
                    
                    with tab1:
                        st.dataframe(chart_data)
                        if used_manual:
                            st.warning(f"⚠️ Could not find city name. Used Manual Coordinates: {lat}, {lon}")
                        else:
                            st.success(f"✅ Found City: {city_name} ({lat}, {lon})")

                    # AI Setup
                    chart_text = "\n".join([f"{item['Planet']} in {item['Zodiac']}" for item in chart_data])
                    base_prompt = f"You are Namaskrita, a Vedic Astrologer. Analyze this chart: {chart_text}"
                    genai.configure(api_key=api_key)

                    # TAB 2: Predictions
                    with tab2:
                        with st.spinner("AI Thinking..."):
                            try:
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                res = model.generate_content(base_prompt + "\n\nTask: Explain Lagna, Moon Sign, and Key Yogas.")
                                st.markdown(res.text)
                            except:
                                # Fallback to Pro if Flash fails
                                try:
                                    model = genai.GenerativeModel("gemini-pro")
                                    res = model.generate_content(base_prompt + "\n\nTask: Explain Lagna, Moon Sign, and Key Yogas.")
                                    st.markdown(res.text)
                                except Exception as e:
                                    st.error(f"AI Failed: {e}")

                    # TAB 3: Remedies
                    with tab3:
                         with st.spinner("Fetching Remedies..."):
                            try:
                                model = genai.GenerativeModel("gemini-1.5-flash")
                                res = model.generate_content(base_prompt + "\n\nTask: Suggest Gemstones (Metal/Finger) and Mantras.")
                                st.markdown(res.text)
                            except:
                                st.error("Remedies loading failed.")

                    # TAB 4: Crypto
                    with tab4:
                         with st.spinner("Analyzing Market Luck..."):
                            try:
