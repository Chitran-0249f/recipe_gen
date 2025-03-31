import streamlit as st
from openai import OpenAI
import os
from dataclasses import dataclass
from typing import List
import json

# Initialize the OpenAI client with Novita AI endpoint
client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key=os.getenv('OPENAI_API_KEY'),
)

@dataclass
class Recipe:
    title: str
    cooking_time: str
    difficulty: str
    ingredients: List[str]
    instructions: List[str]
    nutrition: dict
    flavor_profile: str
    garnish_tips: str
    pairing_suggestions: str
# ... existing code ...

def get_recipe_from_ai(cuisine_type, available_ingredients, cooking_time, difficulty):
    system_content = """You are an expert Indian chef. Generate a creative Indian recipe based on the available ingredients and preferences. 
    Response must be in valid JSON format with the following structure:
    {
        "title": "Recipe name",
        "cooking_time": "Time in minutes",
        "difficulty": "Difficulty level",
        "ingredients": ["ingredient1 with quantity", "ingredient2 with quantity", ...],
        "instructions": ["step1", "step2", ...],
        "nutrition": {"calories": "xxx kcal", "protein": "xxg", "carbs": "xxg", "fat": "xxg"},
        "flavor_profile": "Description of taste and spice level",
        "garnish_tips": "Tips for garnishing",
        "pairing_suggestions": "Suggestions for accompaniments like rice, roti, etc."
    }"""

    query = f"""Create an Indian {cuisine_type} recipe using these available ingredients: {', '.join(available_ingredients)}.
    Maximum cooking time: {cooking_time} minutes
    Cooking skill level: {difficulty}
    Only use the ingredients mentioned or very basic Indian kitchen ingredients."""

    try:
        chat_response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": query},
            ],
            stream=False,
            max_tokens=1500,
            temperature=0.7,
            top_p=0.9
        )

        # Clean and validate the response
        response_text = chat_response.choices[0].message.content.strip()
        # Find the JSON part of the response (in case the model adds any extra text)
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            recipe_json = json.loads(response_text[start_idx:end_idx])
            return Recipe(**recipe_json)
        else:
            raise ValueError("No valid JSON found in response")
            
    except Exception as e:
        st.error(f"Error generating recipe: {str(e)}")
        return None

def get_cooking_assistance(query, recipe: Recipe, cuisine_type, cooking_time, difficulty):
    system_content = f"""You are an expert Indian chef assistant helping with cooking queries. 
    You have access to this recipe:
    Title: {recipe.title}
    Ingredients: {', '.join(recipe.ingredients)}
    Cooking Time: {cooking_time} minutes
    Difficulty: {difficulty}
    
    Provide clear, specific answers about cooking techniques, ingredient substitutions, 
    timing adjustments, or any other cooking-related questions for this recipe.
    Keep responses concise and practical."""

    try:
        chat_response = client.chat.completions.create(
            model="meta-llama/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": query},
            ],
            stream=False,
            max_tokens=500,
            temperature=0.7,
            top_p=0.9
        )
        return chat_response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I couldn't process your question: {str(e)}"

def display_recipe_and_chat(recipe: Recipe, cuisine_type, cooking_time, difficulty):
    # Store recipe in session state to persist it
    if 'current_recipe' not in st.session_state:
        st.session_state.current_recipe = recipe
    
    # Create two main sections using columns
    recipe_col, chat_col = st.columns([2, 1], gap="large")
    
    # Left column: Fixed recipe display
    with recipe_col:
        # Recipe title
        st.header(f"🍽️ {st.session_state.current_recipe.title}")
        
        # Quick info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"⏱️ Cooking Time: {st.session_state.current_recipe.cooking_time}")
        with col2:
            st.write(f"📊 Difficulty: {st.session_state.current_recipe.difficulty}")
        
        # Create tabs for recipe details
        recipe_tab, details_tab = st.tabs(["📝 Recipe", "✨ Additional Details"])
        
        with recipe_tab:
            # Ingredients section
            st.subheader("Ingredients")
            for ingredient in st.session_state.current_recipe.ingredients:
                st.write(f"• {ingredient}")
            
            # Instructions section
            st.subheader("Instructions")
            for i, instruction in enumerate(st.session_state.current_recipe.instructions, 1):
                st.write(f"{i}. {instruction}")
        
        with details_tab:
            # Nutrition information
            with st.expander("Nutrition Information"):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Calories", st.session_state.current_recipe.nutrition["calories"])
                col2.metric("Protein", st.session_state.current_recipe.nutrition["protein"])
                col3.metric("Carbs", st.session_state.current_recipe.nutrition["carbs"])
                col4.metric("Fat", st.session_state.current_recipe.nutrition["fat"])
            
            st.write(f"**Flavor Profile:** {st.session_state.current_recipe.flavor_profile}")
            st.write(f"**Garnishing Tips:** {st.session_state.current_recipe.garnish_tips}")
            st.write(f"**Pairing Suggestions:** {st.session_state.current_recipe.pairing_suggestions}")
    
    # Right column: Chat interface
    with chat_col:
        st.markdown("### 👩‍🍳 Cooking Assistant")
        st.write("Ask any questions about the recipe!")
        
        # Initialize chat history if not exists
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Create a container for chat messages
        chat_container = st.container()
        
        # Chat input at the bottom
        user_question = st.chat_input("Ask your cooking question here...")
        
        # Handle user input
        if user_question:
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            
            # Get assistant response
            response = get_cooking_assistance(
                user_question,
                st.session_state.current_recipe,
                cuisine_type,
                cooking_time,
                difficulty
            )
            
            # Add assistant response to history
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Display chat history
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

def create_recipe_app():
    st.title("👩‍🍳 Indian Recipe Generator")
    
    # Sidebar for user inputs
    st.sidebar.header("Customize Your Recipe")
    
    # Veg/Non-veg selection
    cuisine_type = st.sidebar.radio(
        "Select Cuisine Type",
        ["Vegetarian", "Non-Vegetarian"]
    )
    
    # Common Indian ingredients based on cuisine type
    common_veg_ingredients = [
        "Potatoes", "Tomatoes", "Onions", "Green Peas", "Cauliflower", 
        "Paneer", "Spinach", "Bell Peppers", "Carrots", "Beans",
        "Mushrooms", "Cabbage", "Eggplant", "Okra", "Lentils (Dal)"
    ]
    
    common_nonveg_ingredients = [
        "Chicken", "Mutton", "Fish", "Eggs", "Prawns"
    ] if cuisine_type == "Non-Vegetarian" else []
    
    # Common Indian spices
    common_spices = [
        "Turmeric", "Red Chili Powder", "Garam Masala", "Cumin Seeds",
        "Coriander Powder", "Ginger", "Garlic", "Green Chilies"
    ]
    
    # Combine ingredients based on selection
    available_ingredients = st.sidebar.multiselect(
        "Select Available Ingredients",
        common_veg_ingredients + common_nonveg_ingredients,
        help="Select the main ingredients you have"
    )
    
    available_spices = st.sidebar.multiselect(
        "Select Available Spices",
        common_spices,
        default=["Turmeric", "Red Chili Powder", "Garam Masala"],
        help="Select the spices you have"
    )
    
    cooking_time_pref = st.sidebar.slider(
        "Maximum Cooking Time (minutes)",
        15, 120, 45
    )
    
    difficulty_pref = st.sidebar.selectbox(
        "Cooking Skill Level",
        ["Beginner", "Intermediate", "Expert"]
    )

    if st.sidebar.button("Generate Recipe"):
        if not available_ingredients:
            st.warning("Please select at least one main ingredient!")
            return
            
        with st.spinner("👩‍🍳 Creating your personalized Indian recipe..."):
            # Combine all ingredients for the recipe generation
            all_ingredients = available_ingredients + available_spices
            recipe = get_recipe_from_ai(
                cuisine_type,
                all_ingredients,
                cooking_time_pref,
                difficulty_pref
            )
            if recipe:
                # Update to use new display function that includes chat
                display_recipe_and_chat(
                    recipe,
                    cuisine_type,
                    cooking_time_pref,
                    difficulty_pref
                )
                
                # Move clear chat button to a more accessible location
                cols = st.sidebar.columns(2)
                with cols[0]:
                    if st.button("Clear Chat"):
                        st.session_state.chat_history = []
                        st.experimental_rerun()
                with cols[1]:
                    if st.button("New Recipe"):
                        st.session_state.clear()
                        st.experimental_rerun()

# ... rest of the existing display_recipe function and main block remains the same ...

def display_recipe(recipe: Recipe):
    # Display recipe title with emoji
    st.header(f"🍽️ {recipe.title}")
    
    # Cooking time and difficulty
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"⏱️ Cooking Time: {recipe.cooking_time}")
    with col2:
        st.write(f"📊 Difficulty: {recipe.difficulty}")
    
    # Ingredients
    st.subheader("📝 Ingredients")
    for ingredient in recipe.ingredients:
        st.write(f"• {ingredient}")
    
    # Instructions
    st.subheader("👩‍🍳 Instructions")
    for i, instruction in enumerate(recipe.instructions, 1):
        st.write(f"{i}. {instruction}")
    
    # Nutrition information in an expander
    with st.expander("Nutrition Information"):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Calories", recipe.nutrition["calories"])
        col2.metric("Protein", recipe.nutrition["protein"])
        col3.metric("Carbs", recipe.nutrition["carbs"])
        col4.metric("Fat", recipe.nutrition["fat"])
    
    # Additional information
    st.subheader("✨ Additional Details")
    st.write(f"**Flavor Profile:** {recipe.flavor_profile}")
    st.write(f"**Garnishing Tips:** {recipe.garnish_tips}")
    st.write(f"**Pairing Suggestions:** {recipe.pairing_suggestions}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="AI Chef's Recipe Generator",
        page_icon="🍳",
        layout="wide"
    )
    create_recipe_app()
