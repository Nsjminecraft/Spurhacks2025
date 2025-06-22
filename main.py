from flask import Flask, render_template, request, url_for, redirect, jsonify

from flask_login import current_user, login_user, logout_user, UserMixin, LoginManager, login_required
from flask_bcrypt import Bcrypt

from datetime import datetime

from bson import ObjectId

from pymongo import MongoClient, DESCENDING

from db_helpers import getPersonalInfo, getPastWorkouts, generate_workout_xp
from ai_engine import generate_weekly_workout_plan, generate_meal_plan

import json
import re
import google.generativeai as genai

app = Flask(__name__)

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config['SECRET_KEY'] = "ewiufbbfewbfuwhiewieuhi"

client = MongoClient("mongodb+srv://irvinsivya:Zhnu69DZ8NrcbBKt@spurhacks2025.rsmksdw.mongodb.net/")

db = client.spurhacks2025
users_collection = db.users
personal_info_collection = db.personal_info
rewards_collection = db.rewards
workout_stats_collection = db.workout

# AI Model for goals
GEMINI_API_KEY = "AIzaSyAGlCV3GgQ1emDnatySXiduCqR6jVbcGzk"
genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel('models/gemini-2.0-flash')
except Exception as e:
    print(f"Model initialization error: {e}")
    model = None

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

class User(UserMixin):
    def __init__(self, user):
        self._user_dict = user
        self.id = str(user['_id']) 
        
    def __getattr__(self, name):
        return self._user_dict.get(name)
    
    @property
    def is_active(self):
        return True

@login_manager.user_loader
def load_user(user_id):
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        return User(user)
    return None

def isExistingEmail(email):
    return True if users_collection.find_one({'email': email}) != None else False

@app.route("/")
def signUp():
    return render_template("registration.html")

@app.route("/verifyRegistration", methods = ["POST"])
def registration():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")
    repeated_password = request.form.get("repeated_password")

    if password!=repeated_password:
        return jsonify({"error": "Passwords don't match"})
    
    if isExistingEmail(email)==True:
        return jsonify({"error": "Account already exists"})
        
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
    users_collection.insert_one({"first_name": first_name, "last_name": last_name, "email": email, "hashed_password": hashed_password})

    user = User(users_collection.find_one({"email": email}))

    login_user(user)

    return render_template("personalInfo.html")

@app.route("/personalInfo", methods=["POST"])
def updateInfo():
    weight = request.form.get("weight")
    height = request.form.get("height")
    age = request.form.get("age")
    months_lifting = request.form.get("months_lifting")

    personal_info_collection.insert_one({"user_id": ObjectId(current_user.id), "weight": weight, "height": height, "age": age, "months_lifting": months_lifting, "current_xp": 0})

    return redirect(url_for("main"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/verifyLogin", methods = ["POST"])
def verifyLogin():
    email = request.form.get("email")
    password = request.form.get("password")
    
    if isExistingEmail(email)==False:
        return jsonify({"error": "Account doesn't exist"})
    
    student = users_collection.find_one({"email": email})
    
    if not student:
        return jsonify({"error": "Account doesn't exist"})

    hashed_password = student['hashed_password']

    if bcrypt.check_password_hash(hashed_password, password):
        user = User(student)
        login_user(user)
        return redirect(url_for("main"))
    else:
        return jsonify({"error": "Invalid email or password"})

@app.route("/main", methods = ["POST", "GET"])
@login_required
def main():
    last_workout = workout_stats_collection.find_one({"user_id": ObjectId(current_user.id)}, sort=[("date", DESCENDING)])
    personal_info = personal_info_collection.find_one({"user_id": ObjectId(current_user.id)})
    return render_template("main.html", last_workout=last_workout, personal_info=personal_info)

@app.route("/logWorkout")
@login_required
def logWorkout():
    return render_template("logWorkout.html")

@app.route("/viewPastWorkouts")
@login_required
def viewPastWorkouts():
    past_workouts = list(workout_stats_collection.find({"user_id": ObjectId(current_user.id)}).sort("date", DESCENDING).limit(7))
    return render_template("pastWorkouts.html", past_workouts=past_workouts)

@app.route("/addWorkout", methods = ["POST"])
@login_required
def addWorkout():
    date = datetime.now()
    workout_type = request.form.get("workout_type")

    exercises = request.form.getlist("exercise[]")
    sets = request.form.getlist("sets[]")
    reps = request.form.getlist("reps[]")
    weight = request.form.getlist("weight[]")

    exercise_entries = []

    for i in range(len(exercises)):
        exercise_entry = {
            "exercise": exercises[i],
            "sets": int(sets[i]),
            "reps": int(reps[i]),
            "weight": float(weight[i]),
        }

        exercise_entries.append(exercise_entry)

    workout_stats_collection.insert_one({"user_id": ObjectId(current_user.id), "date": date, "workout_type": workout_type, "exercises": exercise_entries})

    return redirect(url_for("main"))

@app.route("/sponsor")
def sponsors():
    sponsors_list = [
        {"name": "Annonymous", "url": "https://www.nike.com", "logo": "someguy.jpeg"},
        {"name": "Annonymous", "url": "https://www.adidas.com", "logo": "someguy.jpeg"},
        {"name": "Annonymous", "url": "https://www.underarmour.com", "logo": "someguy.jpeg"}
    ]
    return render_template("sponsors.html", sponsors=sponsors_list)

@app.route("/redeemRewards")
@login_required
def redeemRewards():
    rewards =  [
        {"name": "Nike", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "logo": url_for('static', filename='someguy.jpeg'), "xp_cost": 300},
        {"name": "Adidas", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "logo": url_for('static', filename='someguy.jpeg'), "xp_cost": 300},
        {"name": "Under Armour", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "logo": url_for('static', filename='someguy.jpeg'), "xp_cost": 300}
    ]
    rewards_collection.insert_many(rewards)

    personal_info = personal_info_collection.find_one({"user_id": ObjectId(current_user.id)})
    current_xp = personal_info['current_xp'] if personal_info else 0

    return render_template("redeemRewards.html", rewards = rewards, user_xp =current_xp)

@app.route("/cashReward", methods=["POST","GET"])
def cashReward():
    reward_name = request.form.get("reward_id")
    personal_info = personal_info_collection.find_one({"user_id": ObjectId(current_user.id)})
    
    if not personal_info:
        return jsonify({"error": "No personal info found for the user"})
    
    current_xp = personal_info.get('current_xp', 0)
    
    reward_id = request.form.get("reward_id")
    reward = rewards_collection.find_one({"_id": ObjectId(reward_id)})

    if not reward or (current_xp < reward['xp_cost']):
        return jsonify({"error": "Not enough XP to redeem this reward"})
    
    new_xp = current_xp - reward['xp_cost']
    personal_info_collection.update_one(
        {"user_id": ObjectId(current_user.id)},
        {"$set": {"current_xp": new_xp}}
    )
    
    print(f"🎉 Reward redeemed: {reward_name} for {reward['xp_cost']} XP. New total: {new_xp} XP")
    
    return redirect(url_for("main"))

@app.route("/workoutPlan", methods=["POST", "GET"])
@login_required
def workoutPlan():
    personal_info = getPersonalInfo(personal_info_collection, current_user.id)
    past_workouts = getPastWorkouts(workout_stats_collection, current_user.id)

    print(f"🔍 Generating workout plan for user {current_user.id}")
    print(f"📊 Personal info: {personal_info}")
    
    workout_plan = generate_weekly_workout_plan(personal_info, past_workouts)
    
    print(f"🤖 Generated workout plan: {workout_plan}")
    
    if not workout_plan:
        return jsonify({"error": "Failed to generate workout plan"})
    
    workout_xp = generate_workout_xp(workout_plan)

    return render_template("workoutPlan.html", workout_plan = workout_plan, workout_xp = workout_xp)

@app.route("/mealPlan", methods=["POST", "GET"])
@login_required
def mealPlan():    
    personal_info = getPersonalInfo(personal_info_collection, current_user.id)
    past_workouts = getPastWorkouts(workout_stats_collection, current_user.id)
    workout_plan = generate_weekly_workout_plan(personal_info, past_workouts)

    if not workout_plan:
        return jsonify({"error": "Failed to generate workout plan"})
    
    print(f"🔍 Generating meal plan for user {current_user.id}")
    meal_plan = generate_meal_plan(personal_info, workout_plan)
    
    print(f"🤖 Generated meal plan: {meal_plan}")
    
    if not meal_plan:
        return jsonify({"error": "Failed to generate meal plan"})

    return render_template("mealPlan.html", meal_plan = meal_plan)

@app.route("/goals", methods=["POST","GET"])
@login_required
def goals():
    personal_info = personal_info_collection.find_one({"user_id": ObjectId(current_user.id)})
    if personal_info is None:
        return jsonify({"error": "No personal info found for the user"})
    
    # Check if user has existing goals, if not generate new ones
    existing_goals = personal_info.get('goals', [])
    if not existing_goals:
        goals = generate_goals(personal_info)
        # Save goals to database
        personal_info_collection.update_one(
            {"user_id": ObjectId(current_user.id)},
            {"$set": {"goals": goals}}
        )
    else:
        goals = existing_goals
    
    return render_template("goals.html", goals = goals, personal_info = personal_info)

@app.route("/completeGoal", methods=["POST","GET"])
@login_required
def completeGoal():
    goal_index = request.form.get("goal_index")
    if goal_index is None:
        goal_index = 0
    
    goal_index = int(goal_index)  # Remove the +2, use actual index
    
    print(f"🎯 Completing goal at index: {goal_index}")
    
    # Get current goals from database
    personal_info = personal_info_collection.find_one({"user_id": ObjectId(current_user.id)})
    if not personal_info:
        return redirect(url_for("goals"))
    
    current_goals = personal_info.get('goals', [])
    
    # Check if goal exists at that index
    if goal_index >= len(current_goals):
        print(f"❌ Goal index {goal_index} out of range (max: {len(current_goals)-1})")
        return redirect(url_for("goals"))
    
    # Get the completed goal and its XP reward
    completed_goal = current_goals[goal_index]
    xp_reward = completed_goal.get('xp_reward', 0)
    
    # Remove the completed goal
    current_goals.pop(goal_index)
    
    # Generate one new goal to replace the completed one
    new_goal = generate_single_goal(personal_info)
    if new_goal:
        current_goals.append(new_goal)
    
    # Update user's XP and goals in database
    new_xp = personal_info.get('current_xp', 0) + xp_reward
    personal_info_collection.update_one(
        {"user_id": ObjectId(current_user.id)},
        {"$set": {"current_xp": new_xp, "goals": current_goals}}
    )
    
    print(f"🎉 Goal completed! Added {xp_reward} XP. New total: {new_xp}")
    print(f"📋 Remaining goals: {len(current_goals)}")
    
    return redirect(url_for("goals"))

def generate_single_goal(personal_info):
    """Generate a single personalized fitness goal using AI"""
    if not model or not personal_info:
        return None
        
    # Calculate experience level
    months_lifting = int(personal_info.get('months_lifting', 6))
    if months_lifting < 6:
        experience_level = "beginner"
    elif months_lifting < 24:
        experience_level = "intermediate"
    else:
        experience_level = "advanced"
    
    prompt = f"""
    Create 1 personalized fitness goal for a {experience_level} lifter.
    
    User Profile:
    - Age: {personal_info.get('age', 25)}
    - Weight: {personal_info.get('weight', 70)} kg
    - Height: {personal_info.get('height', 170)} cm
    - Experience: {experience_level} ({months_lifting} months)
    
    Create a goal that is specific, measurable, and realistic.
    
    Return ONLY valid JSON (single goal object):
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
    }}
    """
    
    try:
        print("🤖 Generating new single goal...")
        response = model.generate_content(prompt)
        json_text = extract_json_from_response(response.text)
        goal = json.loads(json_text)
        # Ensure it's a single goal, not a list
        if isinstance(goal, list) and len(goal) > 0:
            goal = goal[0]
        return goal
    except Exception as e:
        print(f"AI Error generating single goal: {e}")
        # Return fallback goal
        return {"id": 1, "title": "Build Strength", "description": "Increase bench press by 10kg", "target_value": "Bench press 80kg", "current_value": "Bench press 70kg", "deadline": "2024-03-01", "xp_reward": 50, "category": "strength", "progress": 0, "completed": False}

def generate_goals(personal_info):
    """Generate personalized fitness goals using AI"""
    if not model or not personal_info:
        return []
        
    # Calculate experience level
    months_lifting = int(personal_info.get('months_lifting', 6))
    if months_lifting < 6:
        experience_level = "beginner"
    elif months_lifting < 24:
        experience_level = "intermediate"
    else:
        experience_level = "advanced"
    
    prompt = f"""
    Create 5 personalized fitness goals for a {experience_level} lifter.
    
    User Profile:
    - Age: {personal_info.get('age', 25)}
    - Weight: {personal_info.get('weight', 70)} kg
    - Height: {personal_info.get('height', 170)} cm
    - Experience: {experience_level} ({months_lifting} months)
    
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
        print("🤖 Generating new goals...")
        response = model.generate_content(prompt)
        json_text = extract_json_from_response(response.text)
        return json.loads(json_text)
    except Exception as e:
        print(f"AI Error generating goals: {e}")
        # Return fallback goals
        return [
            {"id": 1, "title": "Build Strength", "description": "Increase bench press by 10kg", "target_value": "Bench press 80kg", "current_value": "Bench press 70kg", "deadline": "2024-03-01", "xp_reward": 50, "category": "strength", "progress": 0, "completed": False},
            {"id": 2, "title": "Improve Consistency", "description": "Complete 4 workouts this week", "target_value": "4 workouts", "current_value": "0 workouts", "deadline": "2024-02-15", "xp_reward": 30, "category": "consistency", "progress": 0, "completed": False}
        ]

@app.route("/faq")
def faq():
    faqs = [
        {"question": "What is SpurHacks Gym App?", "answer": "A modern gym tracker and AI workout generator for SpurHacks 2025."},
        {"question": "How do I log a workout?", "answer": "Go to the main page and add a workout."},
        {"question": "How do I redeem rewards?", "answer": "Visit the 'Redeem Rewards' page and select your reward."},
        {"question": "How do I generate an AI workout plan?", "answer": "Go to 'Workout Plan' and let our AI generate a weekly plan for you."},
        {"question": "Who can I contact for support?", "answer": "Email us at support@flowlift.com."}
    ]
    return render_template("faq.html", faqs=faqs)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("signUp"))

if __name__ == "__main__":
    app.run(debug=True)