#!/usr/bin/env python3
"""
CalorieBuddy Backend API Test Suite
Tests all backend endpoints for the AI-powered calorie tracking app
"""

import requests
import json
import base64
import io
from PIL import Image
import os
from datetime import datetime, date
import uuid

# Configuration
BASE_URL = "https://wellnessbuddy-10.preview.emergentagent.com/api"
TEST_USER_ID = None

def create_test_image():
    """Create a simple test image for food analysis"""
    # Create a simple colored image to simulate food
    img = Image.new('RGB', (300, 300), color='orange')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    
    return img_data

def test_health_check():
    """Test the health check endpoint"""
    print("\n=== Testing Health Check ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_user_creation():
    """Test user profile creation with BMR calculation"""
    print("\n=== Testing User Creation ===")
    global TEST_USER_ID
    
    user_data = {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "age": 28,
        "gender": "female",
        "height": 165.0,  # cm
        "weight": 68.0,   # kg
        "activity_level": "moderately_active",
        "goal": "lose_weight",
        "goal_weight": 63.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            TEST_USER_ID = user['id']
            print(f"Created User ID: {TEST_USER_ID}")
            print(f"Daily Calorie Target: {user.get('daily_calorie_target')}")
            
            # Verify BMR calculation (Mifflin-St Jeor for female)
            expected_bmr = 10 * 68.0 + 6.25 * 165.0 - 5 * 28 - 161
            expected_tdee = expected_bmr * 1.55  # moderately_active
            expected_calories = expected_tdee - 500  # lose_weight goal
            
            actual_calories = user.get('daily_calorie_target')
            print(f"Expected calories: {expected_calories:.1f}")
            print(f"Actual calories: {actual_calories}")
            
            if abs(actual_calories - expected_calories) < 5:
                print("✅ User creation and BMR calculation passed")
                return True
            else:
                print("❌ BMR calculation incorrect")
                return False
        else:
            print(f"❌ User creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User creation error: {str(e)}")
        return False

def test_user_retrieval():
    """Test user profile retrieval"""
    print("\n=== Testing User Retrieval ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/users/{TEST_USER_ID}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"Retrieved user: {user['name']} ({user['email']})")
            print("✅ User retrieval passed")
            return True
        else:
            print(f"❌ User retrieval failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User retrieval error: {str(e)}")
        return False

def test_get_all_users():
    """Test getting all users"""
    print("\n=== Testing Get All Users ===")
    
    try:
        response = requests.get(f"{BASE_URL}/users")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users")
            print("✅ Get all users passed")
            return True
        else:
            print(f"❌ Get all users failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get all users error: {str(e)}")
        return False

def test_food_image_analysis():
    """Test food image analysis with LLM integration"""
    print("\n=== Testing Food Image Analysis ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        # Create test image
        img_data = create_test_image()
        
        # Prepare multipart form data
        files = {
            'file': ('test_food.jpg', img_data, 'image/jpeg')
        }
        data = {
            'user_id': TEST_USER_ID,
            'meal_type': 'lunch'
        }
        
        response = requests.post(f"{BASE_URL}/analyze-food", files=files, data=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Analysis success: {result.get('success')}")
            
            food_entry = result.get('food_entry', {})
            analysis = result.get('analysis', {})
            
            print(f"Food name: {food_entry.get('food_name')}")
            print(f"Calories: {food_entry.get('calories')}")
            print(f"Protein: {food_entry.get('protein')}g")
            print(f"Carbs: {food_entry.get('carbs')}g")
            print(f"Fat: {food_entry.get('fat')}g")
            print(f"Confidence: {analysis.get('confidence', 'N/A')}")
            
            # Check if essential fields are present
            required_fields = ['food_name', 'calories', 'protein', 'carbs', 'fat']
            if all(food_entry.get(field) is not None for field in required_fields):
                print("✅ Food image analysis passed")
                return True
            else:
                print("❌ Missing required nutritional data")
                return False
        else:
            print(f"❌ Food analysis failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Food analysis error: {str(e)}")
        return False

def test_food_entries_retrieval():
    """Test food entries retrieval"""
    print("\n=== Testing Food Entries Retrieval ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        # Test without date filter
        response = requests.get(f"{BASE_URL}/food-entries/{TEST_USER_ID}")
        print(f"Status Code (all entries): {response.status_code}")
        
        if response.status_code == 200:
            entries = response.json()
            print(f"Found {len(entries)} food entries")
            
            # Test with date filter
            today = date.today().isoformat()
            response_filtered = requests.get(f"{BASE_URL}/food-entries/{TEST_USER_ID}?date_filter={today}")
            print(f"Status Code (filtered): {response_filtered.status_code}")
            
            if response_filtered.status_code == 200:
                filtered_entries = response_filtered.json()
                print(f"Found {len(filtered_entries)} entries for today")
                print("✅ Food entries retrieval passed")
                return True
            else:
                print(f"❌ Filtered retrieval failed: {response_filtered.text}")
                return False
        else:
            print(f"❌ Food entries retrieval failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Food entries retrieval error: {str(e)}")
        return False

def test_daily_summary():
    """Test daily nutrition summary"""
    print("\n=== Testing Daily Summary ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        # Test without date (should use today)
        response = requests.get(f"{BASE_URL}/daily-summary/{TEST_USER_ID}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"Date: {summary.get('date')}")
            print(f"Daily target: {summary.get('daily_target')} calories")
            
            consumed = summary.get('consumed', {})
            print(f"Consumed calories: {consumed.get('calories', 0)}")
            print(f"Consumed protein: {consumed.get('protein', 0)}g")
            print(f"Consumed carbs: {consumed.get('carbs', 0)}g")
            print(f"Consumed fat: {consumed.get('fat', 0)}g")
            
            remaining = summary.get('remaining', {})
            print(f"Remaining calories: {remaining.get('calories', 0)}")
            
            meals = summary.get('meals', {})
            print(f"Meals breakdown: {list(meals.keys())}")
            print(f"Total entries: {summary.get('entries_count', 0)}")
            
            # Verify structure
            required_fields = ['date', 'user_id', 'daily_target', 'consumed', 'remaining', 'meals']
            if all(field in summary for field in required_fields):
                print("✅ Daily summary passed")
                return True
            else:
                print("❌ Missing required summary fields")
                return False
        else:
            print(f"❌ Daily summary failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Daily summary error: {str(e)}")
        return False

def test_meal_plan_generation():
    """Test AI-powered meal plan generation"""
    print("\n=== Testing Meal Plan Generation ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        # Generate meal plan for tomorrow
        from datetime import timedelta
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        
        response = requests.post(f"{BASE_URL}/meal-plan/{TEST_USER_ID}?target_date={tomorrow}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Generation success: {result.get('success')}")
            
            meal_plan = result.get('meal_plan', {})
            print(f"Date: {meal_plan.get('date')}")
            print(f"Total calories: {meal_plan.get('total_calories')}")
            print(f"Total protein: {meal_plan.get('total_protein')}g")
            
            # Check meal categories
            breakfast = meal_plan.get('breakfast', [])
            lunch = meal_plan.get('lunch', [])
            dinner = meal_plan.get('dinner', [])
            snacks = meal_plan.get('snacks', [])
            
            print(f"Breakfast items: {len(breakfast)}")
            print(f"Lunch items: {len(lunch)}")
            print(f"Dinner items: {len(dinner)}")
            print(f"Snack items: {len(snacks)}")
            
            if breakfast or lunch or dinner:
                print("✅ Meal plan generation passed")
                return True
            else:
                print("❌ No meals generated")
                return False
        else:
            print(f"❌ Meal plan generation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Meal plan generation error: {str(e)}")
        return False

def test_meal_plans_retrieval():
    """Test meal plans retrieval"""
    print("\n=== Testing Meal Plans Retrieval ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/meal-plans/{TEST_USER_ID}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            meal_plans = response.json()
            print(f"Found {len(meal_plans)} meal plans")
            
            if meal_plans:
                latest_plan = meal_plans[0]
                print(f"Latest plan date: {latest_plan.get('date')}")
                print(f"Latest plan calories: {latest_plan.get('total_calories')}")
            
            print("✅ Meal plans retrieval passed")
            return True
        else:
            print(f"❌ Meal plans retrieval failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Meal plans retrieval error: {str(e)}")
        return False

def test_user_update():
    """Test user profile update"""
    print("\n=== Testing User Update ===")
    
    if not TEST_USER_ID:
        print("❌ No test user ID available")
        return False
    
    updated_data = {
        "name": "Sarah Johnson",
        "email": "sarah.johnson@email.com",
        "age": 28,
        "gender": "female",
        "height": 165.0,
        "weight": 66.0,  # Updated weight
        "activity_level": "very_active",  # Updated activity level
        "goal": "lose_weight",
        "goal_weight": 63.0
    }
    
    try:
        response = requests.put(f"{BASE_URL}/users/{TEST_USER_ID}", json=updated_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"Updated weight: {user.get('weight')}")
            print(f"Updated activity: {user.get('activity_level')}")
            print(f"New calorie target: {user.get('daily_calorie_target')}")
            print("✅ User update passed")
            return True
        else:
            print(f"❌ User update failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ User update error: {str(e)}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting CalorieBuddy Backend API Tests")
    print("=" * 50)
    
    test_results = []
    
    # Core functionality tests
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("User Creation", test_user_creation()))
    test_results.append(("User Retrieval", test_user_retrieval()))
    test_results.append(("Get All Users", test_get_all_users()))
    test_results.append(("User Update", test_user_update()))
    
    # LLM Integration tests
    test_results.append(("Food Image Analysis", test_food_image_analysis()))
    test_results.append(("Food Entries Retrieval", test_food_entries_retrieval()))
    
    # Analytics tests
    test_results.append(("Daily Summary", test_daily_summary()))
    
    # AI Meal Planning tests
    test_results.append(("Meal Plan Generation", test_meal_plan_generation()))
    test_results.append(("Meal Plans Retrieval", test_meal_plans_retrieval()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed/len(test_results)*100):.1f}%")
    
    return passed, failed, test_results

if __name__ == "__main__":
    passed, failed, results = run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)