import streamlit as st
import google.generativeai as genai
import swisseph as swe
import datetime
import pytz
from geopy.geocoders import Nominatim

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Namaskrita Astro Solutions", layout="wide")

# --- SIDEBAR INPUTS ---
st.sidebar.title("🔮 Namaskrita Astro")
st.sidebar.subheader("Client Details")

name = st.sidebar.text_input("Name", "Client Name")
dob = st.sidebar.date_input("Date of Birth", datetime.date(2000, 1, 1))
tob = st.sidebar.time_input("Time of Birth", datetime.time(12, 0))
city_name = st.sidebar.text_input("City of Birth", "New Delhi, India")

st.sidebar.markdown("---")
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

# --- HELPER FUNCTIONS ---

def get_lat_lon(city):
    try:
        geolocator = Nominatim(user_agent="namaskrita_astro_app_debug")
        location = geolocator.geocode(city)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def calculate_chart(date, time, lat, lon):
    jd = swe.julday(date.year, date.month, date.day, time.hour + time.minute/60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
        "Venus": swe.VENUS, "Saturn": swe.SATURN, 
        "Rahu": swe.MEAN_NODE
    }
    
    chart_data = []
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'A', swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]
    chart_data.append({"Planet": "Lagna (Asc)", "Degree": f"{asc_deg:.2f}", "Zodiac": get_zodiac_name(asc_deg)})

    for p_name, p_id in planets.items():
        res = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        if isinstance(res, tuple):
            if isinstance(res[0], tuple):
                deg = res[0][0]
            else:
                deg = res[0]
        else:
            deg = float(res)
        chart_data.append({"Planet": p_name, "Degree": f"{deg:.2f}", "Zodiac": get_zodiac_name(deg)})
        
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
        with st.spinner("Calculating..."):
            lat, lon = get_lat_lon(city_name)
            if lat:
                # 1. Calculate
                chart_data = calculate_chart(dob, tob, lat, lon)
                
                # 2. Display Tabs
                tab1, tab2 = st.tabs(["📊 Planetary Data", "🤖 AI Prediction"])
                
                with tab1:
                    st.dataframe(chart_data)
                    st.success(f"Lat: {lat}, Lon: {lon}")

                # 3. AI Section (DEBUG MODE)
                with tab2:
                    st.info("Attempting to connect to Google AI...")
                    
                    chart_text = "\n".join([f"{item['Planet']} in {item['Zodiac']}" for item in chart_data])
                    prompt = f"Analyze this chart: {chart_text}"
                    
                    # Configure Key
                    genai.configure(api_key=api_key)
                    
                    # Try Method A: Flash Model
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(prompt)
                        st.markdown("### ✅ Success with Flash Model")
                        st.markdown(response.text)
                    except Exception as e1:
                        st.warning(f"⚠️ Flash Model Failed: {e1}")
                        
                        # Try Method B: Pro Model (Fallback)
                        try:
                            st.info("Trying older model (Gemini Pro)...")
                            model_old = genai.GenerativeModel("gemini-pro")
                            response = model_old.generate_content(prompt)
                            st.markdown("### ✅ Success with Gemini Pro")
                            st.markdown(response.text)
                        except Exception as e2:
                            st.error(f"❌ ALL Models Failed. Error details:")
                            st.code(f"Error 1: {e1}\nError 2: {e2}")
                            st.error("Please check your API Key carefully.")
            else:
                st.error("City not found.")
