import gradio as gr
import os
from together import Together

# --- Configuration ---
# WARNING: Storing API keys directly in code is insecure for production.
# Consider using environment variables or a config file.
# For demonstration purposes, using the provided key:
API_KEY = "f01a0276256f368dc64e80d6ebad5a96d7c4b58c7f1bf54c9d7ef5475df2a1b9"

# Initialize the Together AI client
try:
    client = Together(api_key=API_KEY)
except Exception as e:
    print(f"Error initializing Together AI client: {e}")
    # You might want to handle this more gracefully, e.g., disable the AI feature
    client = None

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

    print("--- Sending Prompt to Together AI ---")
    print(prompt)
    print("------------------------------------")

    try:
        response = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.7,
        )

        if response and response.choices:
            result = response.choices[0].message.content.strip()
            # Format the result with HTML for better presentation
            # Split the result into recommendations
            recommendations = result.split('---')
            formatted_recommendations = []
            
            for rec in recommendations:
                if rec.strip():
                    # Convert markdown-style formatting to HTML
                    rec = rec.replace('🏪', '<div class="restaurant-name">')
                    rec = rec.replace('📍', '<div class="location">')
                    rec = rec.replace('🍽️', '<div class="dishes">')
                    rec = rec.replace('💰', '<div class="price-range">')
                    rec = rec.replace('✨', '<div class="explanation">')
                    
                    # Close the divs
                    rec = rec.replace('\n\n', '</div>')
                    
                    formatted_recommendations.append(f'<div class="recommendation-card">{rec}</div>')
            
            formatted_result = f"""
            <div class="output-box">
                <h2>✨ Your Personalized Food Recommendations ✨</h2>
                {''.join(formatted_recommendations)}
            </div>
            """
            return formatted_result
        else:
            return "Error: Received an unexpected response format from the AI service."

    except Exception as e:
        print(f"Error during Together AI API call: {e}")
        return f"An error occurred while fetching recommendations: {e}. Please check your API key and network connection."

# Custom CSS for modern food theme
custom_css = """
.gradio-container {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    padding: 30px;
    backdrop-filter: blur(10px);
}

.title {
    text-align: center;
    color: #2c3e50;
    font-size: 2.5em;
    margin-bottom: 30px;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
}

.subtitle {
    text-align: center;
    color: #7f8c8d;
    font-size: 1.2em;
    margin-bottom: 40px;
}

.input-group {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.3s ease;
}

.input-group:hover {
    transform: translateY(-2px);
}

.input-group label {
    color: #2c3e50;
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 1.1em;
}

input, select {
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 12px;
    width: 100%;
    transition: all 0.3s ease;
    background: white;
}

input:focus, select:focus {
    border-color: #4ECDC4;
    box-shadow: 0 0 0 3px rgba(78,205,196,0.1);
    outline: none;
}

button {
    background: linear-gradient(135deg, #FF6B6B 0%, #FF8E8E 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 15px 30px;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    margin-top: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(255,107,107,0.3);
}

.output-box {
    background: white;
    border-radius: 15px;
    padding: 30px;
    margin-top: 20px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
}

.output-box h2 {
    color: #2c3e50;
    margin-bottom: 20px;
    font-size: 1.8em;
    text-align: center;
}

.recommendation-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    border-left: 4px solid #4ECDC4;
    transition: transform 0.3s ease;
}

.recommendation-card:hover {
    transform: translateX(5px);
}

.restaurant-name {
    color: #2c3e50;
    font-size: 1.4em;
    font-weight: 600;
    margin-bottom: 10px;
}

.location {
    color: #7f8c8d;
    font-size: 1.1em;
    margin-bottom: 15px;
}

.dishes {
    color: #34495e;
    margin: 15px 0;
}

.price-range {
    color: #27ae60;
    font-weight: 600;
    margin: 10px 0;
}

.explanation {
    color: #7f8c8d;
    font-style: italic;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #e0e0e0;
}

.disclaimer {
    text-align: center;
    color: #7f8c8d;
    font-size: 0.9em;
    margin-top: 30px;
    padding: 15px;
    background: rgba(255,255,255,0.8);
    border-radius: 10px;
}

.food-icon {
    font-size: 2em;
    margin-right: 10px;
    vertical-align: middle;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: #4ECDC4;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #45b7ae;
}
"""

# --- Gradio Interface ---
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
    with gr.Column(elem_classes="container"):
        gr.Markdown(
            """
            # 🍜 Bangalore Food Finder 🍛
            ### Discover the best food options in Bangalore tailored to your preferences!
            """,
            elem_classes="title"
        )
        
        gr.Markdown(
            """
            Enter your preferences below to get personalized food recommendations. 
            We'll find the perfect spots that match your budget and taste!
            """,
            elem_classes="subtitle"
        )

        with gr.Row():
            with gr.Column(scale=1):
                budget_inp = gr.Number(
                    label="💰 Total Budget (INR)", 
                    minimum=0, 
                    step=50, 
                    value=1000,
                    elem_classes="input-group"
                )
            with gr.Column(scale=1):
                people_inp = gr.Number(
                    label="👥 Number of People", 
                    minimum=1, 
                    step=1, 
                    value=2, 
                    precision=0,
                    elem_classes="input-group"
                )

        food_type_inp = gr.Textbox(
            label="🍽️ Type of Food", 
            placeholder="e.g., North Indian, Pizza, Biryani, South Indian Thali, Chinese...",
            elem_classes="input-group"
        )

        with gr.Row():
            with gr.Column(scale=1):
                location_inp = gr.Textbox(
                    label="📍 Location in Bangalore (Optional)", 
                    placeholder="e.g., Koramangala, Indiranagar, Jayanagar...",
                    elem_classes="input-group"
                )
            with gr.Column(scale=1):
                restaurant_inp = gr.Textbox(
                    label="🏪 Specific Restaurant (Optional)", 
                    placeholder="e.g., Truffles, Meghana Foods...",
                    elem_classes="input-group"
                )

        submit_btn = gr.Button(
            "🔍 Find Food Options!", 
            variant="primary",
            elem_classes="button"
        )

        output_box = gr.HTML(
            label="✨ Recommendations", 
            elem_classes="output-box"
        )

        submit_btn.click(
            fn=get_food_recommendations,
            inputs=[budget_inp, people_inp, food_type_inp, location_inp, restaurant_inp],
            outputs=output_box
        )

        gr.Markdown(
            """
            ---
            *Disclaimer: Recommendations are generated by AI based on training data. Prices and availability may vary. Always check with the restaurant directly.*
            """,
            elem_classes="disclaimer"
        )

# --- Run the App ---
if __name__ == "__main__":
    print("Launching Gradio App...")
    # share=True creates a temporary public link (useful for sharing)
    # Set share=False if running locally only
    demo.launch(share=False)