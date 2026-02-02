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
    """Get coordinates for the city."""
    try:
        geolocator = Nominatim(user_agent="namaskrita_astro_app_v1")
        location = geolocator.geocode(city)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def calculate_chart(date, time, lat, lon):
    """Calculate Vedic Planetary Positions with Safety Checks."""
    jd = swe.julday(date.year, date.month, date.day, time.hour + time.minute/60.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
        "Venus": swe.VENUS, "Saturn": swe.SATURN, 
        "Rahu": swe.MEAN_NODE
    }
    
    chart_data = []
    
    # Calculate Ascendant (Lagna)
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'A', swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]
    chart_data.append({"Planet": "Lagna (Asc)", "Degree": f"{asc_deg:.2f}", "Zodiac": get_zodiac_name(asc_deg)})

    for p_name, p_id in planets.items():
        res = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        
        # SAFEGUARD: Handle different library return types
        if isinstance(res, tuple):
            if isinstance(res[0], tuple):
                deg = res[0][0]
            else:
                deg = res[0]
        else:
            deg = float(res)
            
        chart_data.append({
            "Planet": p_name,
            "Degree": f"{deg:.2f}",
            "Zodiac": get_zodiac_name(deg)
        })
        
    # Ketu
    rahu_data = next(item for item in chart_data if item["Planet"] == "Rahu")
    rahu_deg = float(rahu_data['Degree'])
    ketu_deg = (rahu_deg + 180) % 360
    
    chart_data.append({
        "Planet": "Ketu",
        "Degree": f"{ketu_deg:.2f}",
        "Zodiac": get_zodiac_name(ketu_deg)
    })
    
    return chart_data

def get_zodiac_name(lon):
    """Convert longitude to Zodiac Sign."""
    lon = lon % 360
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(lon / 30)]

def get_ai_response(model_name, prompt):
    """Try to get response, fallback if model not found."""
    model = genai.GenerativeModel(model_name)
    try:
        return model.generate_content(prompt)
    except Exception as e:
        return None

# --- MAIN APP LOGIC ---

st.title(f"✨ {name}'s Vedic Chart Analysis")

if st.sidebar.button("Generate Report"):
    if not api_key:
        st.error("Please enter a Google Gemini API Key in the sidebar.")
    else:
        with st.spinner("Calculating Planetary Positions..."):
            lat, lon = get_lat_lon(city_name)
            
            if lat is not None:
                try:
                    chart_data = calculate_chart(dob, tob, lat, lon)
                    
                    # Create Tabs
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Planetary Data", "🤖 AI Prediction", "💎 Remedies", "💰 Crypto & Wealth"])
                    
                    # TAB 1: DATA
                    with tab1:
                        st.dataframe(chart_data)
                        st.success(f"Coordinates Used: Lat {lat}, Lon {lon}")

                    # PREPARE PROMPT
                    chart_text = "\n".join([f"{item['Planet']} is in {item['Zodiac']} at {item['Degree']} degrees." for item in chart_data])
                    
                    base_prompt = f"""
                    You are an expert Vedic Astrologer named 'Namaskrita'. 
                    Analyze this birth chart for {name}:
                    {chart_text}
                    
                    Please provide a detailed analysis in strictly formatted markdown sections.
                    """
                    
                    genai.configure(api_key=api_key)

                    # TAB 2: GENERAL PREDICTIONS
                    with tab2:
                        with st.spinner("Consulting the Stars..."):
                            # Try the newest model, fallback to standard if it fails
                            response = get_ai_response("gemini-1.5-flash", base_prompt + "\n\nTask: Explain the Lagna personality, Moon Sign, and Yogas.")
                            if not response:
                                response = get_ai_response("gemini-pro", base_prompt + "\n\nTask: Explain the Lagna personality, Moon Sign, and Yogas.")
                            
                            if response:
                                st.markdown(response.text)
                            else:
                                st.error("AI connection failed. Check API Key.")

                    # TAB 3: REMEDIES
                    with tab3:
                        with st.spinner("Finding Remedies..."):
                            response_rem = get_ai_response("gemini-1.5-flash", base_prompt + "\n\nTask: Suggest Gemstones, Vastu tips, and Mantras.")
                            if not response_rem:
                                response_rem = get_ai_response("gemini-pro", base_prompt + "\n\nTask: Suggest Gemstones, Vastu tips, and Mantras.")
                            
                            if response_rem:
                                st.markdown(response_rem.text)

                    # TAB 4: WEALTH
                    with tab4:
                        with st.spinner("Analyzing Financial Charts..."):
                            response_fin = get_ai_response("gemini-1.5-flash", base_prompt + "\n\nTask: Analyze 2nd/5th/11th houses, Crypto suitability, and Stock Market luck.")
                            if not response_fin:
                                response_fin = get_ai_response("gemini-pro", base_prompt + "\n\nTask: Analyze 2nd/5th/11th houses, Crypto suitability, and Stock Market luck.")
                            
                            if response_fin:
                                st.markdown(response_fin.text)

                except Exception as e:
                    st.error(f"An error occurred: {e}")
            else:
                st.error("Could not find that city. Please try a major nearby city.")

else:
    st.info("👈 Enter details in the sidebar and click 'Generate Report' to begin.")
