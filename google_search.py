import os
import requests
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import time
import re
from googleapiclient.discovery import build
import json
import sys # Import sys module
import streamlit as st

def extract_price_range(text: str) -> str:
    """Extract price range from text using common patterns."""
    price_patterns = [
        r'₹\s*(\d+)\s*-\s*₹\s*(\d+)',  # ₹100 - ₹500
        r'Rs\.?\s*(\d+)\s*-\s*Rs\.?\s*(\d+)',  # Rs.100 - Rs.500
        r'INR\s*(\d+)\s*-\s*INR\s*(\d+)',  # INR100 - INR500
        r'(\d+)\s*-\s*(\d+)\s*rupees',  # 100 - 500 rupees
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"₹{match.group(1)} - ₹{match.group(2)}"
    return ""

def extract_rating(text: str) -> str:
    """Extract rating from text using common patterns."""
    rating_patterns = [
        r'(\d+\.?\d*)\s*\/\s*5',  # 4.5/5
        r'(\d+\.?\d*)\s*out\s*of\s*5',  # 4.5 out of 5
        r'rating\s*:\s*(\d+\.?\d*)',  # rating: 4.5
    ]
    
    for pattern in rating_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

def scrape_website(url: str) -> Dict[str, Any]:
    """
    Scrape additional restaurant details from a given URL.
    Focuses on Cuisine, Location, Price Range, Rating, Specialties, Contact, Timing, Features, and Menu Items/Prices.

    Args:
        url (str): The URL of the restaurant website or listing page.

    Returns:
        Dict[str, Any]: A dictionary containing scraped restaurant information.
                       Returns an empty dictionary if scraping fails or no relevant info is found.
    """
    try:
        # Send HTTP request with a user-agent to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15) # Increased timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Check if content type is suitable for parsing
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' not in content_type:
            print(f"Skipping scraping for non-HTML content type: {content_type}")
            return {}

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        restaurant_info = {
            'name': '',
            'cuisine': '', 
            'location': '', 
            'price_range': '', 
            'rating': '', 
            'specialties': '', 
            'contact': '', 
            'timing': '', 
            'features': '',
            'menu_items': [] # Initialize as list
        }
        
        # --- Enhanced Information Extraction --- 

        # 1. Restaurant Name (Try H1, title, specific meta tags)
        name_tag = soup.find('h1')
        if name_tag:
            restaurant_info['name'] = name_tag.text.strip()
        if not restaurant_info['name']:
            title_tag = soup.find('title')
            if title_tag:
                 # Basic cleaning of title for restaurant name
                 restaurant_info['name'] = re.sub(r'\|.*$| - .*$|', '', title_tag.text).strip()

        # 2. Common Patterns for Sections (using text search and sibling/parent navigation)
        def find_info_near_keyword(soup, keywords, search_depth=3):
            pattern = re.compile(r'|'.join(keywords), re.IGNORECASE)
            keyword_tags = soup.find_all(string=pattern)
            found_info = []
            for tag in keyword_tags:
                current = tag
                for _ in range(search_depth):
                    parent = current.find_parent()
                    if not parent: break
                    # Look for text in siblings or the parent itself
                    text_content = ' '.join(parent.stripped_strings)
                    # Simple heuristic: Check if text is sufficiently long and doesn't just repeat the keyword
                    if len(text_content) > len(tag) + 10 and tag.lower() not in text_content.lower()[len(tag):]:
                         # Basic cleaning
                        cleaned_text = re.sub(r'\s+', ' ', text_content).strip()
                        # Avoid overly long generic text blocks
                        if len(cleaned_text) < 300: 
                            found_info.append(cleaned_text)
                            break # Take the first plausible parent/sibling text
                    current = parent
            return ' | '.join(list(set(found_info))) # Join unique findings

        restaurant_info['cuisine'] = find_info_near_keyword(soup, ['cuisine', 'food type', 'serves', 'specializes in'])
        restaurant_info['location'] = find_info_near_keyword(soup, ['address', 'location', 'located at', 'find us'])
        restaurant_info['price_range'] = find_info_near_keyword(soup, ['price range', 'cost for two', 'average cost', 'price level'])
        restaurant_info['rating'] = find_info_near_keyword(soup, ['rating', 'score', 'reviews?', 'stars?'])
        restaurant_info['specialties'] = find_info_near_keyword(soup, ['specialt(?:ies|y)', 'signature', 'popular', 'recommended', 'must try'])
        restaurant_info['contact'] = find_info_near_keyword(soup, ['phone', 'contact', 'tel', 'call', 'book table'])
        restaurant_info['timing'] = find_info_near_keyword(soup, ['timing', 'hours', 'open(?:ing)?', 'days?'])
        restaurant_info['features'] = find_info_near_keyword(soup, ['features', 'amenities', 'facilities', 'serv(?:es|ice)'])
        
        # 3. Menu Items and Prices (More Robust Extraction)
        menu_items = []
        
        # Regex for price (common currencies/formats)
        # Allows for optional decimal part
        price_pattern = re.compile(r'(?:₹|Rs\.?|INR|\$|€|£)\s*(\d+(?:\.\d{1,2})?)\b') 
        
        # Look for common menu containers
        menu_containers = soup.find_all(['div', 'section', 'ul'], 
                                       class_=re.compile(r'menu|item|dish|product|section', re.IGNORECASE))
        if not menu_containers:
            menu_containers = soup.find_all('body') # Fallback to body if no specific containers
            
        for container in menu_containers:
            # Try finding elements with potential item names and prices nearby
            potential_items = container.find_all(['div', 'li', 'p', 'span', 'h3', 'h4'])
            
            for item_tag in potential_items:
                item_text = ' '.join(item_tag.stripped_strings)
                if not item_text or len(item_text) < 3: continue # Skip empty or very short tags
                
                # Search for price within the item's text or immediate siblings/children
                price_match = price_pattern.search(item_text)
                price = None
                if price_match:
                    price = price_match.group(1)
                    # Try to extract the item name (text before the price)
                    item_name = item_text[:price_match.start()].strip()
                    # Basic cleaning of item name
                    item_name = re.sub(r'[\r\n\t]+', ' ', item_name) # Remove newlines/tabs
                    item_name = re.sub(r'\s{2,}', ' ', item_name).strip() # Condense spaces
                    # Filter out very short/generic names or likely descriptions
                    if len(item_name) > 2 and len(item_name.split()) < 10 and not item_name.isdigit():
                        # Avoid duplicates
                        if not any(d['name'] == item_name for d in menu_items):
                             menu_items.append({'name': item_name, 'price': price})
                             # Limit number of items found to avoid overly large results
                             if len(menu_items) > 50: break 
            if len(menu_items) > 50: break # Stop searching containers if enough items found

        # Add extracted menu items to the main dictionary
        restaurant_info['menu_items'] = menu_items
        
        # --- Clean up empty fields --- 
        cleaned_info = {k: v for k, v in restaurant_info.items() if v}
        
        # Optional: Log if important fields are missing
        if not cleaned_info.get('location') or not cleaned_info.get('cuisine'):
             print(f"Warning: Missing location or cuisine for {url}")
             
        return cleaned_info
        
    except requests.exceptions.Timeout:
        print(f"Scraping timed out for URL: {url}")
        return {}
    except requests.exceptions.RequestException as e:
        print(f"Error scraping URL {url}: {str(e)}")
        return {}
    except Exception as e:
        # Catch other potential errors during parsing
        print(f"Error processing HTML for {url}: {str(e)}")
        import traceback
        traceback.print_exc() # Print stack trace for debugging unexpected errors
        return {}

def perform_google_search(query: str, num_results: int = 10, scrape_details: bool = True) -> List[Dict[str, str]]:
    """
    Perform a Google Custom Search and optionally scrape additional details from the results.
    Filters out advertisements and promotional content.

    Args:
        query (str): The search query
        num_results (int): Number of results to return (default: 10)
        scrape_details (bool): Whether to scrape additional details from each result (default: True)

    Returns:
        List[Dict[str, str]]: List of dictionaries containing search results and scraped details
    """
    try:
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            cse_id = st.secrets["GOOGLE_CSE_ID"]
        except KeyError as e:
            st.error(f"""
            ⚠️ Missing Google API credentials in Streamlit Secrets!
            
            Could not find secret key: {str(e)}
            
            Please add the following secrets to your Streamlit Cloud configuration:
            
            ```toml
            GOOGLE_API_KEY = "your_google_api_key"
            GOOGLE_CSE_ID = "your_google_cse_id"
            ```
            
            You can add these in your Streamlit Cloud dashboard under Settings > Secrets.
            """)
            return []
    except Exception as e:
        st.error(f"Could not access Streamlit secrets: {str(e)}")
        return []

    if not api_key or not cse_id:
        st.error("Google API credentials are empty. Please check your Streamlit secrets configuration.")
        return []

    # 1. Extract Location
    location = None
    location_type = None
    base_query_text = query # Start with the full query
    location_context = "Bangalore" # Assume Bangalore context unless location is Bangalore itself

    print(f"Original Query: {query}")

    # --- Strategy 1: Explicit Patterns (near/in/at/area) --- 
    location_keywords_boundary = r'\b(?:menu|price|cost|review|restaurant|hotel|food|rating|$)|'
    location_patterns = [
        (r'\b(?:near|in|at)\s+((?:[A-Za-z0-9][A-Za-z0-9\s,\-]*?))(?=\s*(?:'+location_keywords_boundary+r'))\b', None),
        (r'\b((?:[A-Za-z0-9][A-Za-z0-9\s,\-]*?))\s+area(?=\s*(?:'+location_keywords_boundary+r'))\b', 'area')
    ]

    for pattern, loc_relation in location_patterns:
        # print(f"Trying pattern: {pattern}") # Debug print
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            # print(f"Explicit pattern matched!") # Debug print
            extracted_location = match.group(1).strip()
            if len(extracted_location) > 1:
                location = extracted_location
                if loc_relation == 'area':
                    location_type = 'in'
                else:
                    relation_keyword = match.group(0).split()[0].lower()
                    location_type = relation_keyword
                base_query_text = query.replace(match.group(0), '', 1).strip()
                print(f"Found location via explicit pattern: {location} ({location_type})")
                break
            # else: print(f"Extracted location '{extracted_location}' too short, ignoring match.") # Debug
        # else: print("Pattern did not match.") # Debug

    # --- Strategy 2: Fallback - Known Localities (if explicit patterns failed) --- 
    if not location:
        print("Explicit location patterns failed. Trying fallback with known localities...")
        # Simple list of common Bangalore localities (can be expanded)
        known_localities = [
            'koramangala', 'indiranagar', 'hsr layout', 'btm layout', 'jayanagar',
            'jp nagar', 'whitefield', 'marathahalli', 'bellandur', 'electronic city',
            'sarjapur road', 'mg road', 'brigade road', 'commercial street',
            'rajajinagar', 'malleshwaram', 'banashankari', 'yelahanka', 'hebbal'
            # Add more common areas lowercase
        ]
        query_words = query.lower().split()
        found_locality = None
        # Check from the end of the query backwards
        for i in range(len(query_words) - 1, -1, -1):
            # Check single words
            if query_words[i] in known_localities:
                found_locality = query_words[i]
                # Attempt to reconstruct original casing (simple title case)
                # Find the original word in the query corresponding to this lowercase word
                original_case_words = [w for w in query.split() if w.lower() == found_locality]
                location = original_case_words[0] if original_case_words else found_locality.title()
                break
            # Optional: Check two-word phrases (like 'sarjapur road')
            if i > 0:
                two_word_phrase = f"{query_words[i-1]} {query_words[i]}"
                if two_word_phrase in known_localities:
                    found_locality = two_word_phrase
                    original_case_words = [w for w in query.split() if w.lower() == query_words[i-1]]
                    original_case_words_2 = [w for w in query.split() if w.lower() == query_words[i]]
                    if original_case_words and original_case_words_2:
                        location = f"{original_case_words[0]} {original_case_words_2[0]}"
                    else:
                         location = found_locality.title()
                    break
        
        if location: # Found via fallback
            location_type = 'in' # Assume 'in' if no explicit preposition
            # Remove the found locality from the base query text (case-insensitive replace)
            # Build a regex pattern to match the found locality case-insensitively
            pattern_to_remove = r'\b' + re.escape(location) + r'\b'
            base_query_text = re.sub(pattern_to_remove, '', base_query_text, flags=re.IGNORECASE).strip()
            print(f"Found location via fallback: {location} ({location_type})")
        else:
            print("Fallback locality check failed.")

    # --- Strategy 3: Default Location (if both explicit and fallback failed) --- 
    if not location:
        location = "Bangalore"
        location_type = "in"
        location_context = "" # Location is Bangalore, so no extra context needed
        print(f"No location found, using default: {location}")
    # Set context if a specific locality was found and it's not Bangalore
    elif location.lower() != 'bangalore' and location.lower() != 'bengaluru':
        location_context = "Bangalore"
    else: # Location found is Bangalore
         location_context = ""

    # Clean potential duplicate spaces from base_query_text after removal
    base_query_text = re.sub(r'\s+', ' ', base_query_text).strip()

    # 2. Process Remaining Text for Base Query
    filter_words = {
        'near', 'in', 'at', 'area', 'menu', 'prices', 'price', 'cost',
        'restaurant', 'restaurants', 'hotel', 'hotels', 'food', 'dining',
        'the', 'and', 'or', 'for', 'with', 'to', 'from', 'by', 'on', 'a', 'an', 'of',
        'reviews', 'review', 'rating', 'ratings'
    }
    query_terms = [word for word in base_query_text.split() if word.lower() not in filter_words]
    base_query = ' '.join(query_terms)

    # Fallback for base query
    if not base_query:
        print(f"Filtering left no terms from: '{base_query_text}'")
        fallback_filter = {'near', 'in', 'at', 'area', 'menu', 'prices', 'price', 'cost',
                           'restaurant', 'restaurants', 'reviews', 'review'}
        base_query = ' '.join(word for word in base_query_text.split() if word.lower() not in fallback_filter)
        print(f"Using fallback base query: '{base_query}'")
    if not base_query:
        print("Fallback also resulted in empty query, using 'food' as default.")
        base_query = "food"

    print(f"Refined Base query: '{base_query}'")

    # 3. Construct Enhanced Query
    location_part = f"{location_type} {location}"
    if location_context:
        location_part += f" {location_context}"
    
    # Simplify query construction and remove potentially problematic parts
    enhanced_query = f"{base_query} {location_part}"
    enhanced_query = re.sub(r'\s+', ' ', enhanced_query).strip()
    print(f"Enhanced query: {enhanced_query}")

    # Construct the API request URL with simplified parameters
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': enhanced_query,
        'num': min(num_results * 2, 20),  # Request more results to account for filtering
        'gl': 'in'  # Set location to India
    }

    try:
        # Make the API request with error handling
        response = requests.get(url, params=params)
        if response.status_code == 400:
            print(f"Bad Request Error. Response content: {response.text}")
            # Try a simpler query as fallback
            fallback_query = f"{base_query} {location}"
            print(f"Trying fallback query: {fallback_query}")
            params['q'] = fallback_query
            # Remove potentially problematic parameters for fallback
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': fallback_query,
                'num': min(num_results * 2, 20)
            }
            response = requests.get(url, params=params)
        
        response.raise_for_status()
        data = response.json()

        if 'items' not in data:
            print(f"No search results found for: {enhanced_query}")
            return []

        print(f"Found {len(data['items'])} initial results")

        results = []
        ad_keywords = ['sponsored', 'advertisement', 'promoted', 'ad:', 'deals', 'offers', 'discount', 'sale']
        processed_links = set()

        for item in data['items']:
            link = item.get('link', '')
            if not link or link in processed_links:
                continue
            processed_links.add(link)

            title = item.get('title', '').lower()
            snippet = item.get('snippet', '').lower()

            if any(keyword in title or keyword in snippet for keyword in ad_keywords):
                print(f"Skipping ad result: {title}")
                continue

            if any(domain in link.lower() for domain in ['ad.', '.ad', 'ads.', 'advertising.', 'promo.', 'deals.']):
                print(f"Skipping ad domain: {link}")
                continue

            # Check location relevance using extracted location AND context
            location_terms = location.lower().split()
            context_terms = location_context.lower().split()
            content = (title + ' ' + snippet).lower()

            location_relevant = any(term in content for term in location_terms) or \
                              (location_context and any(term in content for term in context_terms))

            # If not relevant based on specific location/context, try fallback check for Bangalore
            if not location_relevant:
                 if location_context.lower() == 'bangalore' and any(city in content for city in ['bangalore', 'bengaluru']):
                     location_relevant = True # Override: Consider it relevant if Bangalore matches
            
            # After potential override, check final relevance status
            if not location_relevant:
                 print(f"Skipping result not relevant to {location} or {location_context}: {title}")
                 continue # Skip this item if it's still not relevant

            # --- If we reach here, the result is considered relevant --- 
            result = {
                'title': item.get('title', ''),
                'link': link,
                'snippet': item.get('snippet', ''),
                'query_location': location,
                'query_location_type': location_type
            }

            if scrape_details:
                try:
                    print(f"Scraping details from: {link}")
                    scraped_data = scrape_website(link)
                    if scraped_data:
                        result.update(scraped_data)
                        print(f"Successfully scraped details from: {link}")
                except Exception as e:
                    print(f"Error scraping {link}: {str(e)}")

            results.append(result)
            print(f"Added result: {result['title']}")
            time.sleep(0.5)

            if len(results) >= num_results:
                break

        print(f"Returning {len(results)} final results")
        return results

    except requests.exceptions.RequestException as e:
        print(f"Error performing Google search: {str(e)}")
        return []

# Test the search functionality
if __name__ == "__main__":
    # Check if a query is provided via command-line argument
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"Using query from command line: '{query}'")
    else:
        # Use a default query if no argument is provided
        query = "best restaurants in Bangalore"
        print(f"No query provided, using default: '{query}'")

    # Perform the search using the determined query
    results = perform_google_search(query, num_results=5, scrape_details=True)
    
    # Print results
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Title: {result['title']}")
        print(f"Link: {result['link']}")
        print(f"Snippet: {result['snippet']}")
        
        if 'restaurant_info' in result:
            info = result['restaurant_info']
            print("\nRestaurant Details:")
            print(f"Name: {info.get('name', 'N/A')}")
            print(f"Cuisine: {info.get('cuisine', 'N/A')}")
            print(f"Location: {info.get('location', 'N/A')}")
            print(f"Price Range: {info.get('price_range', 'N/A')}")
            print(f"Rating: {info.get('rating', 'N/A')}")
            print(f"Specialties: {info.get('specialties', 'N/A')}")
            print(f"Contact: {info.get('contact', 'N/A')}")
            print(f"Timing: {info.get('timing', 'N/A')}")
            print(f"Features: {info.get('features', 'N/A')}")
            
            # Print menu items if available
            menu_items = info.get('menu_items', [])
            if menu_items:
                print("\nMenu Items:")
                for item in menu_items:
                    print(f"{item['name']}: {item['price']}")
