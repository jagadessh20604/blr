import os
from together import Together

# Initialize Together AI client
try:
    # Get API key from environment variable
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("Error: TOGETHER_API_KEY environment variable not set")
        exit(1)
    
    # Set the API key in environment
    os.environ["TOGETHER_API_KEY"] = api_key
    
    # Initialize client
    client = Together()
    print("Successfully initialized Together AI client")
    
    # Test prompt
    test_prompt = "What is the capital of France?"
    
    # Make API call
    print("\nMaking API call...")
    response = client.chat.completions.create(
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        messages=[{"role": "user", "content": test_prompt}],
        max_tokens=1024,
        temperature=0.7,
    )
    
    # Print response
    print("\nResponse:")
    if response and hasattr(response, 'choices') and response.choices:
        print(response.choices[0].message.content.strip())
    else:
        print("No response received")
        
except Exception as e:
    print(f"Error: {str(e)}") 