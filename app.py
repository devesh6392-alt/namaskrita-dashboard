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
        geolocator = Nominatim(user_agent="astro_app")
        location = geolocator.geocode(city)
        if location:
            return location.latitude, location.longitude
        return None, None
    except:
        return None, None

def calculate_chart(date, time, lat, lon):
    """Calculate Vedic Planetary Positions using Swiss Ephemeris."""
    # Convert to Julian Day
    # Note: We are treating input time as standard time for simplicity. 
    # For professional precision, timezone conversion is recommended.
    jd = swe.julday(date.year, date.month, date.day, time.hour + time.minute/60.0)
    
    # Set Sidereal Mode (Lahiri Ayanamsa)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    planets = {
        "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
        "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, 
        "Venus": swe.VENUS, "Saturn": swe.SATURN, 
        "Rahu": swe.MEAN_NODE
    }
    
    chart_data = []
    
    # Calculate Ascendant (Lagna) - FIXED LINE
    # We pass the sidereal flag positionally, not as a keyword
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'A', swe.FLG_SIDEREAL)
    asc_deg = ascmc[0]
    chart_data.append({"Planet": "Lagna (Asc)", "Degree": f"{asc_deg:.2f}", "Zodiac": get_zodiac_name(asc_deg)})

    for p_name, p_id in planets.items():
        # FIXED LINE: Removed 'flag=' keyword
        res = swe.calc_ut(jd, p_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
        deg = res[0]
        chart_data.append({
            "Planet": p_name,
            "Degree": f"{deg:.2f}",
            "Zodiac": get_zodiac_name(deg)
        })
        
    # Ketu is exactly opposite Rahu
    rahu_deg = float([x['Degree'] for x in chart_data if x['Planet'] == "Rahu"][0])
    ketu_deg = (rahu_deg + 180) % 360
    chart_data.append({
        "Planet": "Ketu",
        "Degree": f"{ketu_deg:.2f}",
        "Zodiac": get_zodiac_name(ketu_deg)
    })
    
    return chart_data

def get_zodiac_name(lon):
    """Convert longitude to Zodiac Sign."""
    # Normalize to 0-360
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
        with st.spinner("Calculating Planetary Positions..."):
            lat, lon = get_lat_lon(city_name)
            
            if lat is not None:
                chart_data = calculate_chart(dob, tob, lat, lon)
                
                # Create Tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Planetary Data", "🤖 AI Prediction", "💎 Remedies", "💰 Crypto & Wealth"])
                
                # TAB 1: DATA
                with tab1:
                    st.dataframe(chart_data)
                    st.success(f"Coordinates Used: Lat {lat}, Lon {lon}")

                # PREPARE PROMPT FOR AI
                chart_text = "\n".join([f"{item['Planet']} is in {item['Zodiac']} at {item['Degree']} degrees." for item in chart_data])
                
                base_prompt = f"""
                You are an expert Vedic Astrologer named 'Namaskrita'. 
                Analyze this birth chart for {name}:
                {chart_text}
                
                Please provide a detailed analysis in strictly formatted markdown sections.
                """

                # TAB 2: GENERAL PREDICTIONS
                with tab2:
                    with st.spinner("Consulting the Stars..."):
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        
                        try:
                            response = model.generate_content(
                                base_prompt + 
                                "\n\nTask: Explain the Lagna (Ascendant) personality. Identify the Moon Sign. List the 'Yogas' (Good/Bad) formed by these positions. Give a general life prediction."
                            )
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"AI Error: {e}")

                # TAB 3: REMEDIES
                with tab3:
                    with st.spinner("Finding Remedies..."):
                        try:
                            response_rem = model.generate_content(
                                base_prompt + 
                                "\n\nTask: Suggest specific Gemstones (include metal and finger). Suggest Vastu tips for their home. Suggest a mantra."
                            )
                            st.markdown(response_rem.text)
                        except:
                            st.error("Could not fetch remedies.")
                        
                # TAB 4: WEALTH & CRYPTO
                with tab4:
                    with st.spinner("Analyzing Financial Charts..."):
                        try:
                            response_fin = model.generate_content(
                                base_prompt + 
                                "\n\nTask: Focus ONLY on Wealth, Speculation, and Career. "
                                "1. Analyze the 2nd (Wealth), 5th (Speculation), and 11th (Gains) houses. "
                                "2. Is this person suitable for High Risk Crypto Trading? (Check Rahu/Mercury). "
                                "3. Give a 'Luck Score' for Stock Market vs Real Estate. "
                                "4. Suggest lucky colors for trading."
                            )
                            st.markdown(response_fin.text)
                        except:
                            st.error("Could not fetch financial data.")

            else:
                st.error("Could not find that city. Please try a major nearby city.")

else:
    st.info("👈 Enter details in the sidebar and click 'Generate Report' to begin.")
