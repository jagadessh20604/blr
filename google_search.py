import os
import requests
from typing import List, Dict, Optional

def perform_google_search(
    query: str,
    api_key: str,
    cse_id: str,
    num_results: int = 5
) -> List[Dict[str, str]]:
    """
    Perform a Google Custom Search and return the results.
    
    Args:
        query (str): The search query
        api_key (str): Your Google API key
        cse_id (str): Your Custom Search Engine ID
        num_results (int): Number of results to return (default: 5)
        
    Returns:
        List[Dict[str, str]]: List of search results, each containing 'title', 'link', and 'snippet'
    """
    base_url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num_results
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'items' not in data:
            return []
            
        results = []
        for item in data['items']:
            results.append({
                'title': item.get('title', ''),
                'link': item.get('link', ''),
                'snippet': item.get('snippet', '')
            })
        return results
        
    except requests.exceptions.RequestException as e:
        print(f"Error performing Google search: {e}")
        return []

if __name__ == "__main__":
    # Test the search function
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    
    if not api_key or not cse_id:
        print("Please set GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables")
        exit(1)
        
    # Test search
    results = perform_google_search("best restaurants in Bangalore", api_key, cse_id)
    for result in results:
        print(f"\nTitle: {result['title']}")
        print(f"Link: {result['link']}")
        print(f"Snippet: {result['snippet']}")
