import google.generativeai as genai
import json
import re
from datetime import datetime, timedelta
from pymongo import MongoClient, DESCENDING
from bson import ObjectId

# Configuration
GEMINI_API_KEY = "AIzaSyAGlCV3GgQ1emDnatySXiduCqR6jVbcGzk"

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://irvinsivya:Zhnu69DZ8NrcbBKt@spurhacks2025.rsmksdw.mongodb.net/"
DATABASE_NAME = "spurhacks2025"

# Configure Google Gemini AI
print(f"🔑 Using API Key: {GEMINI_API_KEY[:10]}...")
genai.configure(api_key=GEMINI_API_KEY)

# MongoDB Connection
try:
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    users_collection = db.users
    personal_info_collection = db.personal_info
    workout_stats_collection = db.workout
    print("✅ Connected to MongoDB")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None
    db = None

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

# List available models first
def list_models():
    """List available models"""
    try:
        print("🔍 Checking available models...")
        models = genai.list_models()
        print("Available models:")
        for model in models:
            print(f"  - {model.name}")
        return models
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []

# List models first
available_models = list_models()
print()

# Try to find a working model (2.0 flash first)
model = None
model_names_to_try = ['models/gemini-2.0-flash', 'models/gemini-2.0-flash-001']

for model_name in model_names_to_try:
    try:
        print(f"🔄 Trying model: {model_name}")
        model = genai.GenerativeModel(model_name)
        # Test with a simple call
        response = model.generate_content("Hi")
        print(f"✅ Successfully using {model_name}")
        break
    except Exception as e:
        print(f"❌ {model_name} failed: {e}")
        continue

if not model:
    print("❌ No working model found")

# Test API connection
def test_api():
    """Test if the API is working"""
    if not model:
        return False
    
    try:
        print("🧪 Testing with simple prompt...")
        response = model.generate_content("Hello")
        print(f"🧪 API Test Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

# Sample user data (constants)
SAMPLE_USER = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
}

SAMPLE_PERSONAL_INFO = {
    "age": 25,
    "weight": 75,  # kg
    "height": 180,  # cm
    "months_lifting": 12,
    "current_xp": 150,
    "level": 2
}

class SimpleFlowliftAI:
    def __init__(self):
        """Simple AI demo without database dependencies"""
        self.user = SAMPLE_USER
        self.personal_info = SAMPLE_PERSONAL_INFO
        self.bmi = self._calculate_bmi()
        self.experience_level = self._determine_experience_level()
        
    def _calculate_bmi(self):
        """Calculate BMI from weight and height"""
        weight_kg = float(self.personal_info['weight'])
        height_m = float(self.personal_info['height']) / 100
        return weight_kg / (height_m ** 2)
    
    def _determine_experience_level(self):
        """Determine experience level based on months lifting"""
        months = int(self.personal_info['months_lifting'])
        if months < 6:
            return "beginner"
        elif months < 24:
            return "intermediate"
        else:
            return "advanced"
    
    def generate_workout_plan(self):
        """Generate a 3-day split workout plan using AI"""
        if not model:
            print("❌ No AI model available")
            return {"week": []}
            
        prompt = f"""
        Create a 3-day split workout plan for a {self.experience_level} lifter.
        
        User Profile:
        - Age: {self.personal_info['age']}
        - Weight: {self.personal_info['weight']} kg
        - Height: {self.personal_info['height']} cm
        - BMI: {self.bmi:.1f}
        - Experience: {self.experience_level} ({self.personal_info['months_lifting']} months)
        
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
                    "difficulty": "{self.experience_level}",
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
                }},
                {{
                    "day": 2,
                    "workout_type": "Pull",
                    "difficulty": "{self.experience_level}",
                    "exercises": [
                        {{
                            "name": "Deadlift",
                            "sets": 4,
                            "reps": "6-8",
                            "weight": "100kg",
                            "rest_time": "120 seconds",
                            "notes": "Keep back straight"
                        }}
                    ],
                    "warm_up": ["5 min cardio", "Shoulder rotations"],
                    "cool_down": ["Back stretches"],
                    "xp_reward": 20
                }},
                {{
                    "day": 3,
                    "workout_type": "Legs",
                    "difficulty": "{self.experience_level}",
                    "exercises": [
                        {{
                            "name": "Squats",
                            "sets": 4,
                            "reps": "8-10",
                            "weight": "80kg",
                            "rest_time": "120 seconds",
                            "notes": "Go parallel or below"
                        }}
                    ],
                    "warm_up": ["5 min cardio", "Leg swings"],
                    "cool_down": ["Quad stretches"],
                    "xp_reward": 22
                }}
            ]
        }}
        """
        
        try:
            print("🤖 Sending workout prompt to AI...")
            response = model.generate_content(prompt)
            print(f"📝 FULL AI Response:\n{response.text}\n---END RAW RESPONSE---\n")
            # Extract JSON from markdown response
            json_text = extract_json_from_response(response.text)
            return json.loads(json_text)
        except Exception as e:
            print(f"AI Error: {e}")
            return {"week": []}
    
    def generate_meal_plan(self, workout_plan=None):
        """Generate a 7-day meal plan using AI"""
        if not model:
            print("❌ No AI model available")
            return {"week": []}
            
        prompt = f"""
        Create a 7-day meal plan for a {self.experience_level} lifter.
        
        User Profile:
        - Age: {self.personal_info['age']}
        - Weight: {self.personal_info['weight']} kg
        - Height: {self.personal_info['height']} cm
        - BMI: {self.bmi:.1f}
        
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
            print("🤖 Sending meal plan prompt to AI...")
            response = model.generate_content(prompt)
            print(f"📝 FULL AI Response:\n{response.text}\n---END RAW RESPONSE---\n")
            # Extract JSON from markdown response
            json_text = extract_json_from_response(response.text)
            return json.loads(json_text)
        except Exception as e:
            print(f"AI Error: {e}")
            return {"week": []}
    
    def generate_goals(self):
        """Generate personalized fitness goals using AI"""
        if not model:
            print("❌ No AI model available")
            return []
            
        prompt = f"""
        Create 5 personalized fitness goals for a {self.experience_level} lifter.
        
        User Profile:
        - Age: {self.personal_info['age']}
        - Weight: {self.personal_info['weight']} kg
        - Height: {self.personal_info['height']} cm
        - Experience: {self.experience_level} ({self.personal_info['months_lifting']} months)
        
        Create goals that are specific, measurable, and realistic.
        
        Return ONLY valid JSON:
        [
            {{
                "id": 1,
                "title": "Build Strength",
                "description": "Increase bench press by 10kg",
                "target_value": "Bench press 80kg",
                "current_value": "Bench press 70kg",
                "deadline": "2024-03-01",
                "xp_reward": 50,
                "category": "strength",
                "progress": 0,
                "completed": false
            }},
            {{
                "id": 2,
                "title": "Improve Consistency",
                "description": "Complete 4 workouts this week",
                "target_value": "4 workouts",
                "current_value": "0 workouts",
                "deadline": "2024-02-15",
                "xp_reward": 30,
                "category": "consistency",
                "progress": 0,
                "completed": false
            }}
        ]
        """
        
        try:
            print("🤖 Sending goals prompt to AI...")
            response = model.generate_content(prompt)
            print(f"📝 FULL AI Response:\n{response.text}\n---END RAW RESPONSE---\n")
            # Extract JSON from markdown response
            json_text = extract_json_from_response(response.text)
            return json.loads(json_text)
        except Exception as e:
            print(f"AI Error: {e}")
            return []
    
    def calculate_workout_xp(self, workout_data):
        """Calculate XP for a workout"""
        base_xp = 10
        
        # Workout type bonus
        workout_type = workout_data.get('workout_type', '').lower()
        if 'push' in workout_type or 'pull' in workout_type:
            base_xp += 5
        elif 'legs' in workout_type:
            base_xp += 8
        
        # Exercise bonus
        exercises = workout_data.get('exercises', [])
        exercise_bonus = min(len(exercises) * 2, 10)
        base_xp += exercise_bonus
        
        return min(int(base_xp), 25)  # Cap at 25

def demo_ai_features():
    """Demo all AI features"""
    print("🏋️‍♂️ FLOWLIFT AI DEMO 🏋️‍♂️")
    print("=" * 50)
    
    # Test API connection first
    print("🧪 TESTING API CONNECTION...")
    if test_api():
        print("✅ API connection successful!")
    else:
        print("❌ API connection failed!")
        print("Please check your API key and internet connection.")
        return
    print()
    
    # Initialize AI
    ai = SimpleFlowliftAI()
    
    print(f"👤 User Profile:")
    print(f"   Name: {ai.user['first_name']} {ai.user['last_name']}")
    print(f"   Age: {ai.personal_info['age']}")
    print(f"   Weight: {ai.personal_info['weight']}kg")
    print(f"   Height: {ai.personal_info['height']}cm")
    print(f"   BMI: {ai.bmi:.1f}")
    print(f"   Experience: {ai.experience_level} ({ai.personal_info['months_lifting']} months)")
    print(f"   Current XP: {ai.personal_info['current_xp']}")
    print(f"   Level: {ai.personal_info['level']}")
    print()
    
    # Generate Workout Plan
    print("💪 GENERATING WORKOUT PLAN...")
    workout_plan = ai.generate_workout_plan()
    print("✅ Workout Plan Generated!")
    print()
    
    # Show workout plan
    print("📋 WORKOUT PLAN:")
    if workout_plan.get('week'):
        for day in workout_plan['week']:
            print(f"   Day {day['day']}: {day['workout_type']} ({day['difficulty']})")
            print(f"   XP Reward: {day['xp_reward']}")
            print(f"   Exercises:")
            for exercise in day.get('exercises', []):
                print(f"     • {exercise['name']}: {exercise['sets']} sets x {exercise['reps']} reps @ {exercise['weight']}")
            print()
    else:
        print("   ❌ No workout plan generated")
        print()
    
    # Generate Meal Plan
    print("🍽️ GENERATING MEAL PLAN...")
    meal_plan = ai.generate_meal_plan()
    print("✅ Meal Plan Generated!")
    print()
    
    # Show meal plan
    print("🍎 MEAL PLAN:")
    if meal_plan.get('week'):
        for day in meal_plan['week']:
            print(f"   Day {day['day']}:")
            meals = day.get('meals', {})
            for meal_type, meal in meals.items():
                if isinstance(meal, dict):
                    print(f"     {meal_type.title()}: {meal['name']}")
                    print(f"       Calories: {meal['calories']}, Protein: {meal['protein']}")
            print(f"   Total: {day.get('total_calories', 0)} calories, {day.get('total_protein', '0g')} protein")
            print()
    else:
        print("   ❌ No meal plan generated")
        print()
    
    # Generate Goals
    print("🎯 GENERATING GOALS...")
    goals = ai.generate_goals()
    print("✅ Goals Generated!")
    print()
    
    # Show goals
    print("🎯 PERSONALIZED GOALS:")
    if goals:
        for goal in goals:
            print(f"   {goal['id']}. {goal['title']}")
            print(f"      Description: {goal['description']}")
            print(f"      Target: {goal['target_value']}")
            print(f"      Current: {goal['current_value']}")
            print(f"      XP Reward: {goal['xp_reward']}")
            print(f"      Category: {goal['category']}")
            print(f"      Deadline: {goal['deadline']}")
            print()
    else:
        print("   ❌ No goals generated")
        print()
    
    # XP System Demo
    print("⭐ XP SYSTEM DEMO:")
    print(f"   Current XP: {ai.personal_info['current_xp']}")
    print(f"   Current Level: {ai.personal_info['level']}")
    
    # Initialize variables
    new_xp = ai.personal_info['current_xp']
    new_level = ai.personal_info['level']
    
    # Calculate XP for sample workout (only if workout plan exists)
    if workout_plan.get('week'):
        sample_workout = workout_plan['week'][0]
        xp_earned = ai.calculate_workout_xp(sample_workout)
        new_xp = ai.personal_info['current_xp'] + xp_earned
        new_level = (new_xp // 100) + 1
        
        print(f"   XP from {sample_workout['workout_type']} workout: {xp_earned}")
        print(f"   New total XP: {new_xp}")
        print(f"   New level: {new_level}")
    else:
        print("   ❌ Cannot calculate XP - no workout plan available")
    print()
    
    # Rewards Demo
    print("🎁 REWARDS SYSTEM:")
    rewards = Config.REWARDS
    for i, reward in enumerate(rewards):
        can_afford = new_xp >= reward['xp_cost']
        status = "✅ Can afford" if can_afford else "❌ Need more XP"
        print(f"   {i+1}. {reward['name']} - {reward['xp_cost']} XP ({status})")
    
    print()
    print("🎉 AI DEMO COMPLETE! 🎉")
    print("All features working without database connections!")

if __name__ == "__main__":
    demo_ai_features() 