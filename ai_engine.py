import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta

# Configuration
GEMINI_API_KEY = "AIzaSyAGlCV3GgQ1emDnatySXiduCqR6jVbcGzk"

# Configure Google Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

def extract_json_from_response(response_text):
    """Extract JSON from markdown code blocks or return as-is"""
    # Remove markdown code block wrappers
    json_match = re.search(r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    # If no code block, try to find JSON in the text
    json_match = re.search(r'(\{.*?\}|\[.*?\])', response_text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    # If still no match, return the original text
    return response_text

# Initialize model
try:
    model = genai.GenerativeModel('models/gemini-2.0-flash')
except Exception as e:
    print(f"Model initialization error: {e}")
    model = None

def generate_weekly_workout_plan(personal_info, past_workouts=None):
    """Generate a weekly workout plan using AI"""
    if not model or not personal_info:
        return None
    
    # Calculate BMI and experience level
    weight_kg = float(personal_info.get('weight', 70))
    height_cm = float(personal_info.get('height', 170))
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    months_lifting = int(personal_info.get('months_lifting', 6))
    if months_lifting < 6:
        experience_level = "beginner"
    elif months_lifting < 24:
        experience_level = "intermediate"
    else:
        experience_level = "advanced"
    
    prompt = f"""
    Create a 3-day split workout plan for a {experience_level} lifter.
    
    User Profile:
    - Age: {personal_info.get('age', 25)}
    - Weight: {weight_kg} kg
    - Height: {height_cm} cm
    - BMI: {bmi:.1f}
    - Experience: {experience_level} ({months_lifting} months)
    
    Create exactly 3 workouts:
    - Day 1: Push (Chest, Shoulders, Triceps)
    - Day 2: Pull (Back, Biceps, Rear Delts)
    - Day 3: Legs (Quads, Hamstrings, Glutes, Calves)
    
    Each workout should have 4-6 exercises with sets, reps, and weight recommendations.
    
    Return ONLY valid JSON:
    {{
        "week": [
            {{
                "day": 1,
                "workout_type": "Push",
                "difficulty": "{experience_level}",
                "exercises": [
                    {{
                        "name": "Bench Press",
                        "sets": 4,
                        "reps": "8-12",
                        "weight": "70kg",
                        "rest_time": "90 seconds",
                        "notes": "Keep form tight"
                    }}
                ],
                "warm_up": ["5 min cardio", "Arm circles"],
                "cool_down": ["Chest stretches"],
                "xp_reward": 18
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        json_text = extract_json_from_response(response.text)
        return json.loads(json_text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def generate_meal_plan(personal_info, workout_plan=None):
    """Generate a meal plan using AI"""
    if not model or not personal_info:
        return None
    
    # Calculate BMI
    weight_kg = float(personal_info.get('weight', 70))
    height_cm = float(personal_info.get('height', 170))
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    months_lifting = int(personal_info.get('months_lifting', 6))
    if months_lifting < 6:
        experience_level = "beginner"
    elif months_lifting < 24:
        experience_level = "intermediate"
    else:
        experience_level = "advanced"
    
    prompt = f"""
    Create a 7-day meal plan for a {experience_level} lifter.
    
    User Profile:
    - Age: {personal_info.get('age', 25)}
    - Weight: {weight_kg} kg
    - Height: {height_cm} cm
    - BMI: {bmi:.1f}
    
    Create a 7-day meal plan that supports muscle growth and recovery.
    Include breakfast, lunch, dinner, and snacks for all 7 days.
    
    Return ONLY valid JSON:
    {{
        "week": [
            {{
                "day": 1,
                "meals": {{
                    "breakfast": {{
                        "name": "Protein Oatmeal Bowl",
                        "ingredients": ["Oats", "Protein powder", "Banana", "Almonds"],
                        "calories": 450,
                        "protein": "30g",
                        "carbs": "55g",
                        "fat": "18g",
                        "prep_time": "10 minutes"
                    }},
                    "lunch": {{
                        "name": "Grilled Chicken Salad",
                        "ingredients": ["Chicken breast", "Mixed greens", "Cherry tomatoes"],
                        "calories": 520,
                        "protein": "40g",
                        "carbs": "25g",
                        "fat": "28g",
                        "prep_time": "15 minutes"
                    }},
                    "dinner": {{
                        "name": "Salmon with Quinoa",
                        "ingredients": ["Salmon fillet", "Quinoa", "Broccoli"],
                        "calories": 580,
                        "protein": "45g",
                        "carbs": "55g",
                        "fat": "22g",
                        "prep_time": "25 minutes"
                    }},
                    "snacks": ["Greek yogurt with berries", "Handful of almonds"]
                }},
                "total_calories": 2200,
                "total_protein": "155g"
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        json_text = extract_json_from_response(response.text)
        return json.loads(json_text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None 