from bson import ObjectId
from pymongo import DESCENDING

def getPersonalInfo(personal_info_collection, user_id):
    """Get personal info for a user"""
    return personal_info_collection.find_one({"user_id": ObjectId(user_id)})

def getPastWorkouts(workout_stats_collection, user_id):
    """Get past workouts for a user"""
    return list(workout_stats_collection.find({"user_id": ObjectId(user_id)}).sort("date", DESCENDING).limit(10))

def generate_workout_xp(workout_plan):
    """Calculate XP for a workout plan"""
    base_xp = 10
    
    if workout_plan and 'week' in workout_plan:
        for day in workout_plan['week']:
            # Workout type bonus
            workout_type = day.get('workout_type', '').lower()
            if 'push' in workout_type or 'pull' in workout_type:
                base_xp += 5
            elif 'legs' in workout_type:
                base_xp += 8
            
            # Exercise bonus
            exercises = day.get('exercises', [])
            exercise_bonus = min(len(exercises) * 2, 10)
            base_xp += exercise_bonus
    
    return min(int(base_xp), 25)  # Cap at 25 