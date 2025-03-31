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

def get_recipe_from_ai(main_ingredient, dietary_restrictions, cooking_time, difficulty):
    system_content = """You are a world-class AI chef. Generate a creative recipe based on the given ingredients and preferences. 
    Provide the recipe in JSON format with the following structure:
    {
        "title": "Recipe name",
        "cooking_time": "Time in minutes",
        "difficulty": "Difficulty level",
        "ingredients": ["ingredient1", "ingredient2", ...],
        "instructions": ["step1", "step2", ...],
        "nutrition": {"calories": "xxx kcal", "protein": "xxg", "carbs": "xxg", "fat": "xxg"},
        "flavor_profile": "Description",
        "garnish_tips": "Tips",
        "pairing_suggestions": "Suggestions"
    }"""

    query = f"""Create a recipe using {main_ingredient} as the main ingredient.
    Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
    Maximum cooking time: {cooking_time} minutes
    Cooking skill level: {difficulty}"""

    try:
        chat_response = client.chat.completions.create(
            model="meta-llama/llama-3.3-70b-instruct",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": query},
            ],
            stream=False,
            max_tokens=1000,  # Increased for full recipe
            temperature=0.7,   # Increased for creativity
            top_p=0.9         # Increased for variety
        )

        recipe_json = json.loads(chat_response.choices[0].message.content)
        return Recipe(**recipe_json)
    except Exception as e:
        st.error(f"Error generating recipe: {str(e)}")
        return None

def create_recipe_app():
    st.title("🍳 AI Chef's Recipe Generator")
    
    # Sidebar for user inputs
    st.sidebar.header("Customize Your Recipe")
    
    main_ingredient = st.sidebar.selectbox(
        "Main Ingredient",
        ["Chicken", "Fish", "Beef", "Vegetarian", "Pork"]
    )
    
    dietary_restrictions = st.sidebar.multiselect(
        "Dietary Restrictions",
        ["Gluten-free", "Dairy-free", "Vegan", "Nut-free", "Low-carb"]
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
        with st.spinner("👩‍🍳 Creating your personalized recipe..."):
            recipe = get_recipe_from_ai(
                main_ingredient,
                dietary_restrictions,
                cooking_time_pref,
                difficulty_pref
            )
            if recipe:
                display_recipe(recipe)

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