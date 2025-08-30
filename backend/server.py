from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
import uuid
import base64
from PIL import Image
import io
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="CalorieBuddy API", description="AI-powered calorie tracking app")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    age: int
    gender: str  # male, female, other
    height: float  # in cm
    weight: float  # in kg
    activity_level: str  # sedentary, lightly_active, moderately_active, very_active, extra_active
    goal: str  # lose_weight, maintain_weight, gain_weight
    goal_weight: Optional[float] = None  # in kg
    daily_calorie_target: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    name: str
    email: str
    age: int
    gender: str
    height: float
    weight: float
    activity_level: str
    goal: str
    goal_weight: Optional[float] = None

class FoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    food_name: str
    calories: float
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    sugar: Optional[float] = None
    serving_size: Optional[str] = None
    meal_type: str  # breakfast, lunch, dinner, snack
    image_base64: Optional[str] = None
    analysis_details: Optional[Dict[str, Any]] = None
    entry_date: date = Field(default_factory=date.today, alias="date")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MealPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: date
    breakfast: List[Dict[str, Any]] = []
    lunch: List[Dict[str, Any]] = []
    dinner: List[Dict[str, Any]] = []
    snacks: List[Dict[str, Any]] = []
    total_calories: float = 0
    total_protein: float = 0
    total_carbs: float = 0
    total_fat: float = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NutritionAnalysis(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = None
    sodium: Optional[float] = None
    sugar: Optional[float] = None
    serving_size: str
    confidence: float
    detailed_breakdown: Dict[str, Any]

# Helper Functions
def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if gender.lower() == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_daily_calories(bmr: float, activity_level: str, goal: str) -> float:
    """Calculate daily calorie needs based on activity level and goal"""
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }
    
    tdee = bmr * activity_multipliers.get(activity_level, 1.2)
    
    if goal == 'lose_weight':
        return tdee - 500  # 500 calorie deficit for 1 lb/week loss
    elif goal == 'gain_weight':
        return tdee + 500  # 500 calorie surplus for 1 lb/week gain
    else:
        return tdee  # maintenance

async def analyze_food_image(image_base64: str) -> Dict[str, Any]:
    """Analyze food image using LLM to extract nutritional information"""
    try:
        # Initialize LLM chat
        api_key = os.getenv('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"food_analysis_{uuid.uuid4()}",
            system_message="""You are a nutrition expert AI that analyzes food images and provides detailed nutritional information. 
            
            When analyzing food images, please:
            1. Identify all visible food items
            2. Estimate portion sizes as accurately as possible
            3. Provide detailed nutritional breakdown including calories, protein, carbs, fat, fiber, sodium, and sugar
            4. Be specific about serving sizes
            5. Return data in JSON format with the following structure:
            {
                "food_name": "Detailed description of the food",
                "calories": number,
                "protein": number (in grams),
                "carbs": number (in grams),
                "fat": number (in grams),
                "fiber": number (in grams),
                "sodium": number (in mg),
                "sugar": number (in grams),
                "serving_size": "Description of estimated portion",
                "confidence": number (0-1 scale),
                "detailed_breakdown": {
                    "ingredients": ["list of visible ingredients"],
                    "cooking_method": "description",
                    "portion_analysis": "detailed portion size analysis",
                    "nutritional_notes": "any important nutritional information"
                }
            }
            
            Be as accurate as possible with nutritional estimates based on visual analysis."""
        ).with_model("openai", "gpt-4o")
        
        # Create image content
        image_content = ImageContent(image_base64=image_base64)
        
        # Send message with image
        user_message = UserMessage(
            text="Please analyze this food image and provide detailed nutritional information in the JSON format specified.",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Parse the response to extract JSON
        response_text = str(response).strip()
        
        # Try to extract JSON from the response
        import json
        
        # Look for JSON content in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            try:
                parsed_data = json.loads(json_str)
                return parsed_data
            except json.JSONDecodeError:
                # Fallback: create structured response from text
                return {
                    "food_name": "Unknown food item",
                    "calories": 200,
                    "protein": 10,
                    "carbs": 20,
                    "fat": 8,
                    "fiber": 3,
                    "sodium": 300,
                    "sugar": 5,
                    "serving_size": "1 serving",
                    "confidence": 0.5,
                    "detailed_breakdown": {
                        "analysis_text": response_text,
                        "note": "Could not parse structured data, using defaults"
                    }
                }
        else:
            # Fallback response
            return {
                "food_name": "Food item from image",
                "calories": 200,
                "protein": 10,
                "carbs": 20,
                "fat": 8,
                "fiber": 3,
                "sodium": 300,
                "sugar": 5,
                "serving_size": "1 serving",
                "confidence": 0.5,
                "detailed_breakdown": {
                    "analysis_text": response_text,
                    "note": "Structured analysis available in text format"
                }
            }
            
    except Exception as e:
        logging.error(f"Error analyzing food image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze food image: {str(e)}")

# API Routes
@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Create a new user profile"""
    try:
        # Calculate BMR and daily calorie target
        bmr = calculate_bmr(user_data.weight, user_data.height, user_data.age, user_data.gender)
        daily_calories = calculate_daily_calories(bmr, user_data.activity_level, user_data.goal)
        
        user_dict = user_data.dict()
        user_dict['daily_calorie_target'] = daily_calories
        user_obj = User(**user_dict)
        
        await db.users.insert_one(user_obj.dict())
        return user_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")

@api_router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user profile by ID"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

@api_router.get("/users", response_model=List[User])
async def get_all_users():
    """Get all users (for demo purposes)"""
    users = await db.users.find().to_list(100)
    return [User(**user) for user in users]

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserCreate):
    """Update user profile"""
    # Recalculate daily calorie target
    bmr = calculate_bmr(user_data.weight, user_data.height, user_data.age, user_data.gender)
    daily_calories = calculate_daily_calories(bmr, user_data.activity_level, user_data.goal)
    
    user_dict = user_data.dict()
    user_dict['daily_calorie_target'] = daily_calories
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": user_dict}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"id": user_id})
    return User(**updated_user)

@api_router.post("/analyze-food")
async def analyze_food_from_image(file: UploadFile = File(...), user_id: str = Form(...), meal_type: str = Form(...)):
    """Analyze uploaded food image and create food entry"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process image
        image_data = await file.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Analyze with LLM
        analysis = await analyze_food_image(image_base64)
        
        # Create food entry
        food_entry = FoodEntry(
            user_id=user_id,
            food_name=analysis.get('food_name', 'Unknown food'),
            calories=analysis.get('calories', 200),
            protein=analysis.get('protein', 10),
            carbs=analysis.get('carbs', 20),
            fat=analysis.get('fat', 8),
            fiber=analysis.get('fiber', 3),
            sodium=analysis.get('sodium', 300),
            sugar=analysis.get('sugar', 5),
            serving_size=analysis.get('serving_size', '1 serving'),
            meal_type=meal_type,
            image_base64=image_base64,
            analysis_details=analysis
        )
        
        await db.food_entries.insert_one(food_entry.dict())
        
        return {
            "success": True,
            "food_entry": food_entry,
            "analysis": analysis
        }
        
    except Exception as e:
        logging.error(f"Error in analyze_food_from_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze food: {str(e)}")

@api_router.get("/food-entries/{user_id}")
async def get_user_food_entries(user_id: str, date_filter: Optional[str] = None):
    """Get food entries for a user, optionally filtered by date"""
    try:
        query = {"user_id": user_id}
        
        if date_filter:
            # Parse date and filter
            from datetime import datetime
            target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query["date"] = target_date.isoformat()
        
        entries = await db.food_entries.find(query).sort("created_at", -1).to_list(100)
        return [FoodEntry(**entry) for entry in entries]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get food entries: {str(e)}")

@api_router.get("/daily-summary/{user_id}")
async def get_daily_summary(user_id: str, date_filter: Optional[str] = None):
    """Get daily nutrition summary for a user"""
    try:
        if not date_filter:
            date_filter = date.today().isoformat()
        
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get food entries for the day
        entries = await db.food_entries.find({
            "user_id": user_id,
            "date": date_filter
        }).to_list(100)
        
        # Calculate totals
        total_calories = sum(entry.get('calories', 0) for entry in entries)
        total_protein = sum(entry.get('protein', 0) for entry in entries)
        total_carbs = sum(entry.get('carbs', 0) for entry in entries)
        total_fat = sum(entry.get('fat', 0) for entry in entries)
        total_fiber = sum(entry.get('fiber', 0) for entry in entries)
        
        # Group by meal type
        meals = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snack': []
        }
        
        for entry in entries:
            meal_type = entry.get('meal_type', 'snack')
            if meal_type in meals:
                meals[meal_type].append(entry)
        
        return {
            "date": date_filter,
            "user_id": user_id,
            "daily_target": user.get('daily_calorie_target', 2000),
            "consumed": {
                "calories": total_calories,
                "protein": total_protein,
                "carbs": total_carbs,
                "fat": total_fat,
                "fiber": total_fiber
            },
            "remaining": {
                "calories": max(0, user.get('daily_calorie_target', 2000) - total_calories)
            },
            "meals": meals,
            "entries_count": len(entries)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily summary: {str(e)}")

@api_router.post("/meal-plan/{user_id}")
async def generate_meal_plan(user_id: str, target_date: str):
    """Generate AI-powered meal plan for a user"""
    try:
        # Get user info
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Initialize LLM chat for meal planning
        api_key = os.getenv('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"meal_plan_{user_id}_{target_date}",
            system_message=f"""You are a professional nutritionist creating personalized meal plans. Create a daily meal plan based on the user's profile:

            User Profile:
            - Age: {user.get('age')} years
            - Gender: {user.get('gender')}
            - Weight: {user.get('weight')} kg
            - Height: {user.get('height')} cm
            - Activity Level: {user.get('activity_level')}
            - Goal: {user.get('goal')}
            - Daily Calorie Target: {user.get('daily_calorie_target')} calories

            Create a balanced meal plan with breakfast, lunch, dinner, and 2 snacks that:
            1. Meets the daily calorie target
            2. Provides balanced macronutrients (protein, carbs, healthy fats)
            3. Includes variety and practical meal options
            4. Considers the user's health goals

            Return the meal plan in JSON format:
            {{
                "breakfast": [{{"name": "meal name", "calories": number, "protein": number, "carbs": number, "fat": number, "description": "brief description"}}],
                "lunch": [{{"name": "meal name", "calories": number, "protein": number, "carbs": number, "fat": number, "description": "brief description"}}],
                "dinner": [{{"name": "meal name", "calories": number, "protein": number, "carbs": number, "fat": number, "description": "brief description"}}],
                "snacks": [{{"name": "snack name", "calories": number, "protein": number, "carbs": number, "fat": number, "description": "brief description"}}],
                "total_calories": number,
                "total_protein": number,
                "total_carbs": number,
                "total_fat": number,
                "nutritional_notes": "any important notes about the meal plan"
            }}"""
        ).with_model("openai", "gpt-4o")
        
        user_message = UserMessage(
            text=f"Please create a personalized meal plan for {target_date} based on my profile information."
        )
        
        response = await chat.send_message(user_message)
        response_text = str(response).strip()
        
        # Parse JSON response
        import json
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            meal_plan_data = json.loads(json_str)
            
            # Create meal plan object
            meal_plan = MealPlan(
                user_id=user_id,
                date=datetime.strptime(target_date, "%Y-%m-%d").date(),
                breakfast=meal_plan_data.get('breakfast', []),
                lunch=meal_plan_data.get('lunch', []),
                dinner=meal_plan_data.get('dinner', []),
                snacks=meal_plan_data.get('snacks', []),
                total_calories=meal_plan_data.get('total_calories', 0),
                total_protein=meal_plan_data.get('total_protein', 0),
                total_carbs=meal_plan_data.get('total_carbs', 0),
                total_fat=meal_plan_data.get('total_fat', 0)
            )
            
            # Save to database
            await db.meal_plans.insert_one(meal_plan.dict())
            
            return {
                "success": True,
                "meal_plan": meal_plan,
                "nutritional_notes": meal_plan_data.get('nutritional_notes', '')
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to parse meal plan response")
            
    except Exception as e:
        logging.error(f"Error generating meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate meal plan: {str(e)}")

@api_router.get("/meal-plans/{user_id}")
async def get_meal_plans(user_id: str):
    """Get meal plans for a user"""
    try:
        meal_plans = await db.meal_plans.find({"user_id": user_id}).sort("date", -1).to_list(30)
        return [MealPlan(**plan) for plan in meal_plans]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get meal plans: {str(e)}")

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()