import streamlit as st
import os
from together import Together
from PIL import Image
import base64

# --- Core Logic ---
def get_food_recommendations(budget, num_people, food_type, location, restaurant):
    """
    Generates food recommendations using the Together AI API based on user inputs.
    """
    if not client:
        return "Error: Could not initialize the AI Service. Please check API key or network."
    if not food_type:
        return "Please specify the type of food you are looking for."
    if not budget or not num_people:
        return "Please provide both budget and number of people."

    try:
        budget = float(budget)
        num_people = int(num_people)
    except ValueError:
        return "Budget and Number of People must be valid numbers."

    prompt = f"""
    You are a Bangalore food recommendation expert. Your goal is to suggest the best food options, especially combos, based on the user's criteria.

    User Criteria:
    - Budget: INR {budget:.2f} total
    - Number of People: {num_people}
    - Preferred Food Type: {food_type}
    """

    if location:
        prompt += f"- Specific Location in Bangalore: {location}\n"
    else:
        prompt += "- Location: Anywhere in Bangalore (suggest popular areas if relevant)\n"

    if restaurant:
        prompt += f"- Specific Restaurant: {restaurant}\n"
        prompt += "\nInstructions: Find suitable options *only within this specific restaurant* that match the budget, number of people, and food type. If the restaurant doesn't fit the criteria well, state that clearly."
    else:
        prompt += "- Restaurant: Any suitable restaurant\n"
        prompt += "\nInstructions: Find the best value-for-money options and combos across Bangalore matching the criteria. Suggest 3-5 diverse options from different well-regarded restaurants known for the specified food type."

    prompt += f"""
    Output Format:
    Format your response in the following way for each recommendation:

    🏪 [Restaurant Name]
    📍 [Location/Area]
    
    🍽️ Recommended Dishes:
    - [Dish 1]
    - [Dish 2]
    - [etc...]
    
    💰 Price Range: [Price range]
    
    ✨ Why We Recommend:
    [Brief explanation of why this is a good option]
    
    ---
    
    Ensure all recommendations fit within the budget of INR {budget:.2f} for {num_people} people.
    If no suitable options are found, state that clearly.
    """

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )

        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Error: Received an unexpected response format from the AI service."

    except Exception as e:
        st.error(f"Error during Together AI API call: {e}")
        return f"An error occurred while fetching recommendations: {e}. Please check your API key and network connection."

# --- Configuration ---
# Get API key from environment variable
API_KEY = os.getenv("TOGETHER_API_KEY")
if not API_KEY:
    st.error("Please set the TOGETHER_API_KEY environment variable")
    st.stop()

# Initialize the Together AI client
try:
    client = Together(api_key=API_KEY)
except Exception as e:
    st.error(f"Error initializing Together AI client: {e}")
    st.stop()

# --- Streamlit Interface ---
st.set_page_config(
    page_title="Bangalore Food Finder",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Add PWA meta tags and manifest
st.markdown("""
    <link rel="manifest" href="manifest.json">
    <meta name="theme-color" content="#4ECDC4">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Food Finder">
    <link rel="apple-touch-icon" href="icon-192x192.png">
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(registration => {
                        console.log('ServiceWorker registration successful');
                    })
                    .catch(err => {
                        console.log('ServiceWorker registration failed: ', err);
                    });
            });
        }
    </script>
""", unsafe_allow_html=True)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
        color: #2c3e50;
        min-height: 100vh;
    }
    
    /* Content container */
    .main .block-container {
        max-width: 800px;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Form elements */
    .stForm {
        background: rgba(255, 255, 255, 0.9);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .stTextInput input, .stNumberInput input {
        border-radius: 5px;
        border: 1px solid #ddd;
        padding: 0.5rem;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 1rem;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #FF8E8E 0%, #FF6B6B 100%);
    }
    
    /* Recommendation cards */
    .recommendation-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Text styles */
    .restaurant-name {
        color: #2c3e50;
        font-size: 1.2em;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .location {
        color: #7f8c8d;
        font-size: 1em;
        margin-bottom: 0.75rem;
    }
    
    .dishes {
        color: #34495e;
        margin: 0.75rem 0;
    }
    
    .price-range {
        color: #27ae60;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .explanation {
        color: #7f8c8d;
        font-style: italic;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
        }
        
        .stForm {
            padding: 0.75rem;
        }
        
        .recommendation-card {
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        h1 {
            font-size: 1.8em !important;
        }
        
        p {
            font-size: 0.9em !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Main title and description
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <h1 style='color: #2c3e50; font-size: 2em; margin-bottom: 0.5em;'>🍜 Bangalore Food Finder 🍛</h1>
        <p style='color: #7f8c8d; font-size: 1.1em; margin-bottom: 1em;'>
            Discover the best food options in Bangalore tailored to your preferences!
        </p>
    </div>
""", unsafe_allow_html=True)

# Input form
with st.form("food_finder_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.number_input(
            "💰 Total Budget (INR)",
            min_value=0,
            value=1000,
            step=50
        )
        num_people = st.number_input(
            "👥 Number of People",
            min_value=1,
            value=2,
            step=1
        )
    
    with col2:
        food_type = st.text_input(
            "🍽️ Type of Food",
            placeholder="e.g., North Indian, Pizza, Biryani..."
        )
        location = st.text_input(
            "📍 Location in Bangalore (Optional)",
            placeholder="e.g., Koramangala, Indiranagar..."
        )
    
    restaurant = st.text_input(
        "🏪 Specific Restaurant (Optional)",
        placeholder="e.g., Truffles, Meghana Foods..."
    )
    
    submit_button = st.form_submit_button("🔍 Find Food Options!")

# Handle form submission
if submit_button:
    with st.spinner("Finding the best food options for you..."):
        try:
            recommendations = get_food_recommendations(budget, num_people, food_type, location, restaurant)
            
            # Split recommendations into cards
            rec_cards = recommendations.split('---')
            
            for card in rec_cards:
                if card.strip():
                    st.markdown(f"""
                        <div class="recommendation-card">
                            {card}
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"An error occurred while processing your request: {e}")

# Footer
st.markdown("""
    <div style='text-align: center; margin-top: 2em; padding: 1rem; background: rgba(255,255,255,0.8); border-radius: 10px;'>
        <p style='color: #7f8c8d; font-size: 0.9em;'>
            *Disclaimer: Recommendations are generated by AI based on training data. Prices and availability may vary. Always check with the restaurant directly.*
        </p>
    </div>
""", unsafe_allow_html=True) 