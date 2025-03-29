from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import os
from together import Together
import json

class FoodFinderApp(App):
    def build(self):
        # Set window size for testing (will be fullscreen on mobile)
        Window.size = (400, 700)
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title = Label(
            text='🍜 Bangalore Food Finder 🍛',
            size_hint_y=None,
            height=50,
            font_size='20sp'
        )
        main_layout.add_widget(title)
        
        # Input fields
        self.budget_input = TextInput(
            hint_text='Budget (INR)',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.budget_input)
        
        self.people_input = TextInput(
            hint_text='Number of People',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.people_input)
        
        self.food_type_input = TextInput(
            hint_text='Type of Food (e.g., North Indian, Pizza)',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.food_type_input)
        
        self.location_input = TextInput(
            hint_text='Location (Optional)',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.location_input)
        
        self.restaurant_input = TextInput(
            hint_text='Specific Restaurant (Optional)',
            multiline=False,
            size_hint_y=None,
            height=40
        )
        main_layout.add_widget(self.restaurant_input)
        
        # Search button
        search_button = Button(
            text='🔍 Find Food Options!',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        search_button.bind(on_press=self.search_food)
        main_layout.add_widget(search_button)
        
        # Results area
        self.results_scroll = ScrollView(size_hint=(1, 1))
        self.results_layout = GridLayout(
            cols=1,
            spacing=10,
            size_hint_y=None,
            padding=10
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.results_scroll.add_widget(self.results_layout)
        main_layout.add_widget(self.results_scroll)
        
        return main_layout
    
    def search_food(self, instance):
        try:
            # Clear previous results
            self.results_layout.clear_widgets()
            
            # Get input values
            budget = float(self.budget_input.text)
            num_people = int(self.people_input.text)
            food_type = self.food_type_input.text
            location = self.location_input.text
            restaurant = self.restaurant_input.text
            
            # Initialize Together AI client
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                self.show_error("Please set TOGETHER_API_KEY environment variable")
                return
                
            client = Together(api_key=api_key)
            
            # Create prompt
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

            # Get recommendations
            response = client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.7,
            )

            if response and response.choices:
                recommendations = response.choices[0].message.content.strip()
                
                # Split recommendations into cards
                rec_cards = recommendations.split('---')
                
                for card in rec_cards:
                    if card.strip():
                        card_label = Label(
                            text=card,
                            size_hint_y=None,
                            height=200,
                            text_size=(Window.width - 20, None),
                            halign='left',
                            valign='top'
                        )
                        card_label.bind(texture_size=card_label.setter('size'))
                        self.results_layout.add_widget(card_label)
            else:
                self.show_error("No recommendations found")
                
        except Exception as e:
            self.show_error(f"Error: {str(e)}")
    
    def show_error(self, message):
        error_label = Label(
            text=message,
            color=(1, 0, 0, 1),
            size_hint_y=None,
            height=40
        )
        self.results_layout.add_widget(error_label)

if __name__ == '__main__':
    FoodFinderApp().run() 