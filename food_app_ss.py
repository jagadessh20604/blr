import streamlit as st
import os
import requests
import json
from google_search import perform_google_search
import google_search
import importlib.metadata
import re

# Add debug log for library version using importlib.metadata
# st.write(f"DEBUG: Together library version: {importlib.metadata.version('together')}") # Commented out

# Initialize API keys and client
def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables."""
    try:
        # Debug logging
        # st.write("Attempting to access Streamlit secrets...") # Commented out
        
        # Try to get from Streamlit secrets first
        try:
            # Try to get from api_keys section first
            if "api_keys" in st.secrets:
                keys = {
                    "TOGETHER_API_KEY": st.secrets.api_keys.TOGETHER_API_KEY,
                    "GOOGLE_API_KEY": st.secrets.api_keys.GOOGLE_API_KEY,
                    "GOOGLE_CSE_ID": st.secrets.api_keys.GOOGLE_CSE_ID
                }
            else:
                # Fallback to root level secrets
                keys = {
                    "TOGETHER_API_KEY": st.secrets["TOGETHER_API_KEY"],
                    "GOOGLE_API_KEY": st.secrets["GOOGLE_API_KEY"],
                    "GOOGLE_CSE_ID": st.secrets["GOOGLE_CSE_ID"]
                }
            # st.write("Successfully retrieved keys from secrets") # Commented out
            return keys
        except KeyError as e:
            st.warning(f"Could not find secret key: {str(e)}")
            st.write("Falling back to environment variables...")
            # Fallback to environment variables
            return {
                "TOGETHER_API_KEY": os.getenv("TOGETHER_API_KEY"),
                "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"),
                "GOOGLE_CSE_ID": os.getenv("GOOGLE_CSE_ID")
            }
    except Exception as e:
        st.warning(f"Could not access Streamlit secrets: {str(e)}")
        st.write("Falling back to environment variables...")
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

def get_food_recommendations(food_query: str, budget: float, num_people: int, 
                           restaurant: str = None) -> str:
    """Generate food recommendations using a specific food query, Together AI, and Google Search."""
    try:
        # Perform Google search using the provided query - fetch more results
        st.write(f"DEBUG: Performing Google search for: {food_query}") # Debug log
        search_results = perform_google_search(food_query, num_results=10) # Increased to 10 results
        
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
        prompt = f"""You are a food recommendation expert. Your task is to suggest the best food combinations that fit strictly within the user's budget, based *only* on the provided web search results.

**CRITICAL BUDGET INSTRUCTION:** You MUST ensure the 'Total Cost' for any recommended combination is LESS THAN OR EQUAL TO the user's budget of ₹{budget} for {num_people} people. If you cannot find combinations that meet the budget based *only* on the prices mentioned or strongly implied in the Search Results Provided, DO NOT suggest combinations that exceed the budget. Instead, clearly state that you couldn't find options within the budget based on the available information.

CORE REQUIREMENTS:
1. Focus on suggesting food combinations that:
   - Match the user's food type preference (derived from the search query).
   - Strictly adhere to the budget constraint mentioned above.
   - Are available at restaurants mentioned in the search results.

2. For each recommended combination, calculate and show:
   - Total cost for the combination (use prices from search results if available, otherwise estimate cautiously or state price is unknown).
   - Cost per person.
   - Confirm it fits within the budget (₹{budget}).

3. Analyze the search results provided. Give preference to options that appear to be from Swiggy or Zomato if mentioned, but base recommendations primarily on the information presented.

User Criteria:
- Search Query Used: {food_query}
- Budget: ₹{budget} for {num_people} people (MAXIMUM)
- Specific Restaurant Focus (if any): {restaurant if restaurant else 'None'}

Search Results Provided:
{search_info}

For each recommended combination, provide in this exact format:
🏪 Restaurant Name
📍 Location (if identifiable from results)
🔗 Source Link (if available)
💰 Total Cost: ₹X (₹Y per person) - MUST BE <= ₹{budget}
🍽️ Recommended Combination:
   - Item 1: ₹X (or Unknown)
   - Item 2: ₹Y (or Unknown)
   - Item 3: ₹Z (or Unknown)
   Total: ₹T
✨ Why This Combo: (explain why this combination is good value based on search results and budget)
🎁 Special Offers: (if mentioned in search results)

Separate each recommendation with "---". If no combinations meet the budget, state that clearly.
"""

        # ---- Using requests library for Together AI API call ----
        url = "https://api.together.xyz/v1/completions"

        payload = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7,
            # Add other parameters if needed, e.g., "stop": ["---"]
        }

        # Get API key securely
        together_api_key = api_keys.get("TOGETHER_API_KEY")
        if not together_api_key:
            st.error("TOGETHER_API_KEY not found in secrets or environment variables.")
            return "Error: TOGETHER_API_KEY is missing."

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {together_api_key}" # Use securely fetched key
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        response_data = response.json()
        
        if response_data and 'choices' in response_data and response_data['choices']:
            recommendation_text = response_data['choices'][0].get('text', '').strip()
            if not recommendation_text:
                return "Error: Could not extract text from API response."
        else:
            return "Error: Unexpected response format from Together AI."

        return recommendation_text
        # ---- End of requests library usage ----
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error making API request to Together AI: {str(e)}")
        return f"An error occurred while contacting Together AI: {str(e)}"
    except Exception as e:
        st.error(f"Error in get_food_recommendations: {str(e)}")
        return f"An error occurred: {str(e)}"

# Streamlit UI
st.title("🍜 Bangalore Food Finder (Broad Search)") # Updated Title
st.markdown("### Find the best food options in Bangalore using web search!") # Updated Subtitle

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
    # Determine the location, defaulting to Bangalore
    search_location = location if location and location.strip() else "Bangalore"
    
    # Construct the Google Search query (NO SITE FILTER)
    if food_type and food_type.strip():
        # User provided a specific food type
        search_food_type = food_type.strip()
        google_query = f"best {search_food_type} {search_location}"
    else:
        # User did not provide a food type, search for restaurants
        search_food_type = "best food"
        google_query = f"best restaurants {search_location}"

    # If a specific restaurant is mentioned, prioritize it in the query
    if restaurant and restaurant.strip():
        google_query = f"{restaurant.strip()} {search_location} menu prices"
        # Also update the display message to reflect searching for a specific restaurant
        display_message = f"Searching web for menu at '{restaurant.strip()}' in {search_location} within budget ₹{budget} for {num_people} people."
    else:
        display_message = f"Searching web for: '{search_food_type}' in {search_location} within budget ₹{budget} for {num_people} people."

    
    # Display what is being searched
    st.info(display_message)
    
    with st.spinner("Finding the best food options from web search..."):
        recommendations = get_food_recommendations(
            food_query=google_query, # Pass the broad Google query
            budget=budget, 
            num_people=num_people, 
            restaurant=restaurant # Still pass restaurant for the AI prompt context
        )
        
        # Split recommendations into cards
        rec_cards = recommendations.split('---')
        
        # Create a table to display recommendations
        unfiltered_table_data = []
        for card in rec_cards:
            if card.strip():
                # Parse the card content
                lines = card.strip().split('\n')
                data = {
                    'Restaurant': '',
                    'Location': '',
                    'SourceLink': '',
                    'Total Cost String': '', # Store raw string for display
                    'Total Cost Value': float('inf'), # Store numeric value for filtering
                    'Menu Items': [],
                    'Why Recommended': '',
                    'Special Offers': ''
                }
                
                for line in lines:
                    if line.startswith('🏪'):
                        data['Restaurant'] = line.replace('🏪', '').strip()
                    elif line.startswith('📍'):
                        data['Location'] = line.replace('📍', '').strip()
                    elif line.startswith('🔗'):
                        data['SourceLink'] = line.replace('🔗', '').strip()
                    elif line.startswith('💰'):
                        cost_string = line.replace('💰', '').strip()
                        data['Total Cost String'] = cost_string
                        # Extract numeric value from cost string (e.g., "Total Cost: ₹1,800 (₹900 per person)")
                        match = re.search(r'₹\s*([\d,]+(?:\.\d+)?)', cost_string)
                        if match:
                            try:
                                cost_value = float(match.group(1).replace(',', ''))
                                data['Total Cost Value'] = cost_value
                            except ValueError:
                                pass # Keep as infinity if conversion fails
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
                
                unfiltered_table_data.append(data)

        # Filter recommendations based on budget
        table_data = [data for data in unfiltered_table_data if data['Total Cost Value'] <= budget]

        # Display recommendations in a table
        if table_data:
            st.markdown("### Recommended Food Combinations (Within Budget)") # Updated heading
            for data in table_data:
                # Construct optional link HTML
                link_html = f'<div>🔗 <a href="{data["SourceLink"]}" target="_blank">Source Link</a></div>' if data.get("SourceLink") else ""
                
                # Clean the cost string for display
                raw_cost_string = data['Total Cost String']
                display_cost_string = raw_cost_string.split(" - MUST BE")[0].strip()
                
                st.markdown(f"""
                    <div class="recommendation-card">
                        <div class="restaurant-name">{data['Restaurant']}</div>
                        <div>📍 {data['Location']}</div>
                        {link_html}
                        <div class="price-range">💰 {display_cost_string}</div> # Display cleaned string
                        <div>🍽️ Menu Items:</div>
                        {"".join([f'<div class="menu-item">{item}</div>' for item in data['Menu Items']])}
                        <div>✨ {data['Why Recommended']}</div>
                        {f'<div class="special-offer">🎁 {data["Special Offers"]}</div>' if data['Special Offers'] else ''}
                    </div>
                """, unsafe_allow_html=True)
        else:
            # Check if there were results that were filtered out
            if unfiltered_table_data: 
                 st.warning(f"Found some recommendations, but none strictly met the budget of ₹{budget}. Showing nothing.")
            else:
                 st.warning("No recommendations found matching your criteria. Please try a different search or location.")
        
        st.markdown("---")
        st.markdown("*Note: Prices and availability may vary. Please check with the restaurant directly.*") 