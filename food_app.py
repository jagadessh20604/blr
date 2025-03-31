import streamlit as st
import os
from together import Together
from google_search import perform_google_search

# Initialize API keys and client
def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables."""
    try:
        # Try to get from Streamlit secrets first
        return {
            "TOGETHER_API_KEY": st.secrets["TOGETHER_API_KEY"],
            "GOOGLE_API_KEY": st.secrets["GOOGLE_API_KEY"],
            "GOOGLE_CSE_ID": st.secrets["GOOGLE_CSE_ID"]
        }
    except Exception as e:
        st.warning(f"Could not access Streamlit secrets: {str(e)}")
        # Fallback to environment variables
        return {
            "TOGETHER_API_KEY": os.getenv("TOGETHER_API_KEY"),
            "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
            "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID")
        }

# Get API keys
api_keys = get_api_keys()

# Check if any keys are missing
missing_keys = [key for key, value in api_keys.items() if not value]
if missing_keys:
    st.error(f"""
    ⚠️ Missing API Keys!
    
    The following keys are missing:
    {', '.join(missing_keys)}
    
    Please add them to your Streamlit Cloud configuration:
    
    ```toml
    [secrets]
    TOGETHER_API_KEY = "your-together-api-key"
    GOOGLE_API_KEY = "your-google-api-key"
    GOOGLE_CSE_ID = "your-google-cse-id"
    ```
    
    You can add these in your Streamlit Cloud dashboard under Settings > Secrets.
    """)
    st.stop()

# Initialize Together AI client
try:
    client = Together(api_key=api_keys["TOGETHER_API_KEY"])
except Exception as e:
    st.error(f"""
    ⚠️ Error initializing Together AI client!
    
    Error details: {str(e)}
    
    Please check if your Together API key is valid.
    """)
    st.stop()

# Add some basic styling
st.markdown("""
<style>
    .stApp {
        background: #f0f2f6;
    }
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
    }
    .stForm {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: #FF4B4B;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: 600;
    }
    .stButton>button:hover {
        background: #FF6B6B;
    }
    .recommendation-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .restaurant-name {
        color: #FF4B4B;
        font-size: 1.2em;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .price-range {
        color: #00C853;
        font-weight: 600;
    }
    .stTable {
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .stTable > div {
        padding: 1rem;
    }
    .stTable th {
        background: #FF4B4B;
        color: white;
        font-weight: 600;
    }
    .stTable td {
        padding: 0.5rem;
    }
    .menu-item {
        margin: 0.25rem 0;
    }
    .special-offer {
        color: #FF4B4B;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def get_food_recommendations(food_type: str, budget: float, num_people: int, 
                           restaurant: str = None, location: str = None) -> str:
    """Generate food recommendations using Together AI and Google Search."""
    try:
        # Get search results
        search_query = f"Best {food_type} {location or 'Bangalore'}"
        search_results = perform_google_search(search_query, num_results=5)
        
        # Format search results
        search_info = "\nSearch Results:\n"
        for result in search_results:
            search_info += f"\nTitle: {result['title']}\n"
            search_info += f"Link: {result['link']}\n"
            search_info += f"Snippet: {result['snippet']}\n"
            if 'name' in result:
                search_info += f"Restaurant: {result['name']}\n"
            if 'cuisine' in result:
                search_info += f"Cuisine: {result['cuisine']}\n"
            if 'price_range' in result:
                search_info += f"Price Range: {result['price_range']}\n"
            if 'specialties' in result:
                search_info += f"Specialties: {result['specialties']}\n"
            search_info += "-" * 50 + "\n"

        # Create prompt for Together AI
        prompt = f"""You are a food recommendation expert. Your task is to suggest the best food combinations that fit within the user's budget.

CORE REQUIREMENTS:
1. Focus on suggesting food combinations that:
   - Match the user's food type preference
   - Stay within the specified budget of ₹{budget} for {num_people} people
   - Are available at restaurants in the specified location

2. For each recommendation, calculate and show:
   - Total cost for the combination
   - Cost per person
   - Whether it fits within the budget

3. Prioritize restaurants that:
   - Have clear pricing information
   - Offer good value for money
   - Have confirmed menu items and prices

User Criteria:
- Food Type: {food_type}
- Budget: ₹{budget} for {num_people} people
- Location: {location or 'Bangalore'}
- Specific Restaurant: {restaurant if restaurant else 'Any'}

Search Results:
{search_info}

For each recommended combination, provide in this exact format:
🏪 Restaurant Name
📍 Location
💰 Total Cost: ₹X (₹Y per person)
🍽️ Recommended Combination:
   - Item 1: ₹X
   - Item 2: ₹Y
   - Item 3: ₹Z
   Total: ₹T
✨ Why This Combo: (explain why this combination is good value)
🎁 Special Offers: (if any)

Separate each recommendation with "---"."""

        # Get AI recommendations
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )
        
        if response and response.choices:
            return response.choices[0].message.content.strip()
        else:
            return "Error: No response received from Together AI"
        
    except Exception as e:
        st.error(f"Error in get_food_recommendations: {str(e)}")
        return f"An error occurred: {str(e)}"

# Streamlit UI
st.title("🍜 Bangalore Food Finder")
st.markdown("### Find the best food options in Bangalore!")

with st.form("food_finder"):
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.number_input("💰 Budget (INR)", min_value=0, value=1000, step=50)
        num_people = st.number_input("👥 Number of People", min_value=1, value=2, step=1)
    
    with col2:
        food_type = st.text_input("🍽️ Type of Food", placeholder="e.g., Pizza, Biryani...")
        location = st.text_input("📍 Location (Optional)", placeholder="e.g., Koramangala...")
    
    restaurant = st.text_input("🏪 Restaurant (Optional)", placeholder="e.g., Truffles...")
    submit = st.form_submit_button("🔍 Find Food Options!")

if submit:
    with st.spinner("Finding the best food options..."):
        recommendations = get_food_recommendations(food_type, budget, num_people, restaurant, location)
        
        # Split recommendations into cards
        rec_cards = recommendations.split('---')
        
        # Create a table to display recommendations
        table_data = []
        for card in rec_cards:
            if card.strip():
                # Parse the card content
                lines = card.strip().split('\n')
                data = {
                    'Restaurant': '',
                    'Location': '',
                    'Total Cost': '',
                    'Menu Items': [],
                    'Why Recommended': '',
                    'Special Offers': ''
                }
                
                for line in lines:
                    if line.startswith('🏪'):
                        data['Restaurant'] = line.replace('🏪', '').strip()
                    elif line.startswith('📍'):
                        data['Location'] = line.replace('📍', '').strip()
                    elif line.startswith('💰'):
                        data['Total Cost'] = line.replace('💰', '').strip()
                    elif line.startswith('🍽️'):
                        menu_items = []
                        for item in lines[lines.index(line)+1:]:
                            if item.strip().startswith('-'):
                                menu_items.append(item.strip())
                            elif not item.strip().startswith('✨'):
                                break
                        data['Menu Items'] = menu_items
                    elif line.startswith('✨'):
                        data['Why Recommended'] = line.replace('✨', '').strip()
                    elif line.startswith('🎁'):
                        data['Special Offers'] = line.replace('🎁', '').strip()
                
                table_data.append(data)
        
        # Display recommendations in a table
        if table_data:
            st.markdown("### Recommended Food Combinations")
            for data in table_data:
                st.markdown(f"""
                    <div class="recommendation-card">
                        <div class="restaurant-name">{data['Restaurant']}</div>
                        <div>📍 {data['Location']}</div>
                        <div class="price-range">💰 {data['Total Cost']}</div>
                        <div>🍽️ Menu Items:</div>
                        {"".join([f'<div class="menu-item">{item}</div>' for item in data['Menu Items']])}
                        <div>✨ {data['Why Recommended']}</div>
                        {f'<div class="special-offer">🎁 {data["Special Offers"]}</div>' if data['Special Offers'] else ''}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No recommendations found matching your criteria. Please try a different search or location.")
        
        st.markdown("---")
        st.markdown("*Note: Prices and availability may vary. Please check with the restaurant directly.*") 