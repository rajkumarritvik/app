import React, { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";
import axios from "axios";
import Webcam from "react-webcam";
import { 
  Camera, 
  Upload, 
  User, 
  Home, 
  Calendar,
  Target,
  Activity,
  Plus,
  Utensils,
  TrendingUp,
  Award,
  Settings
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [showCamera, setShowCamera] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [dailySummary, setDailySummary] = useState(null);
  const [showUserForm, setShowUserForm] = useState(false);
  const [mealPlans, setMealPlans] = useState([]);
  const [selectedMealType, setSelectedMealType] = useState('breakfast');
  
  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);

  // User form state
  const [userForm, setUserForm] = useState({
    name: '',
    email: '',
    age: '',
    gender: 'female',
    height: '',
    weight: '',
    activity_level: 'moderately_active',
    goal: 'maintain_weight',
    goal_weight: ''
  });

  // Load user data on component mount
  useEffect(() => {
    loadUserData();
  }, []);

  // Load daily summary when user changes
  useEffect(() => {
    if (currentUser) {
      loadDailySummary();
      loadMealPlans();
    }
  }, [currentUser]);

  const loadUserData = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      if (response.data && response.data.length > 0) {
        setCurrentUser(response.data[0]); // Use first user for demo
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const loadDailySummary = async () => {
    if (!currentUser) return;
    
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API}/daily-summary/${currentUser.id}?date_filter=${today}`);
      setDailySummary(response.data);
    } catch (error) {
      console.error('Error loading daily summary:', error);
    }
  };

  const loadMealPlans = async () => {
    if (!currentUser) return;
    
    try {
      const response = await axios.get(`${API}/meal-plans/${currentUser.id}`);
      setMealPlans(response.data);
    } catch (error) {
      console.error('Error loading meal plans:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const userData = {
        ...userForm,
        age: parseInt(userForm.age),
        height: parseFloat(userForm.height),
        weight: parseFloat(userForm.weight),
        goal_weight: userForm.goal_weight ? parseFloat(userForm.goal_weight) : null
      };

      const response = await axios.post(`${API}/users`, userData);
      setCurrentUser(response.data);
      setShowUserForm(false);
      setCurrentView('dashboard');
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Failed to create user profile. Please try again.');
    }
  };

  const capturePhoto = useCallback(() => {
    const imageSrc = webcamRef.current.getScreenshot();
    setCapturedImage(imageSrc);
    setShowCamera(false);
  }, [webcamRef]);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setCapturedImage(event.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const analyzeFood = async () => {
    if (!capturedImage || !currentUser) return;

    setAnalyzing(true);
    try {
      // Convert base64 to blob
      const response = await fetch(capturedImage);
      const blob = await response.blob();
      
      // Create form data
      const formData = new FormData();
      formData.append('file', blob, 'food_image.jpg');
      formData.append('user_id', currentUser.id);
      formData.append('meal_type', selectedMealType);

      const analysisResponse = await axios.post(`${API}/analyze-food`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (analysisResponse.data.success) {
        alert(`Food analyzed successfully! ${analysisResponse.data.analysis.food_name} - ${analysisResponse.data.analysis.calories} calories`);
        setCapturedImage(null);
        loadDailySummary(); // Refresh daily summary
      }
    } catch (error) {
      console.error('Error analyzing food:', error);
      alert('Failed to analyze food. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const generateMealPlan = async () => {
    if (!currentUser) return;
    
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.post(`${API}/meal-plan/${currentUser.id}?target_date=${today}`);
      
      if (response.data.success) {
        alert('Meal plan generated successfully!');
        loadMealPlans();
      }
    } catch (error) {
      console.error('Error generating meal plan:', error);
      alert('Failed to generate meal plan. Please try again.');
    }
  };

  const renderNavigation = () => (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2 z-50">
      <div className="flex justify-around items-center max-w-md mx-auto">
        <button
          onClick={() => setCurrentView('dashboard')}
          className={`flex flex-col items-center p-2 rounded-lg ${currentView === 'dashboard' ? 'text-blue-600 bg-blue-50' : 'text-gray-600'}`}
        >
          <Home size={20} />
          <span className="text-xs mt-1">Home</span>
        </button>
        
        <button
          onClick={() => setCurrentView('camera')}
          className={`flex flex-col items-center p-2 rounded-lg ${currentView === 'camera' ? 'text-blue-600 bg-blue-50' : 'text-gray-600'}`}
        >
          <Camera size={20} />
          <span className="text-xs mt-1">Scan</span>
        </button>
        
        <button
          onClick={() => setCurrentView('meals')}
          className={`flex flex-col items-center p-2 rounded-lg ${currentView === 'meals' ? 'text-blue-600 bg-blue-50' : 'text-gray-600'}`}
        >
          <Utensils size={20} />
          <span className="text-xs mt-1">Meals</span>
        </button>
        
        <button
          onClick={() => setCurrentView('profile')}
          className={`flex flex-col items-center p-2 rounded-lg ${currentView === 'profile' ? 'text-blue-600 bg-blue-50' : 'text-gray-600'}`}
        >
          <User size={20} />
          <span className="text-xs mt-1">Profile</span>
        </button>
      </div>
    </nav>
  );

  const renderDashboard = () => (
    <div className="p-4 pb-20">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-2">
          Hello, {currentUser?.name || 'User'}! 👋
        </h1>
        <p className="text-gray-600">Track your nutrition journey</p>
      </div>

      {dailySummary && (
        <div className="mb-6">
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center">
              <Target className="mr-2 text-blue-600" size={20} />
              Today's Progress
            </h2>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {Math.round(dailySummary.consumed.calories)}
                </div>
                <div className="text-sm text-gray-600">Consumed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-800">
                  {Math.round(dailySummary.daily_target)}
                </div>
                <div className="text-sm text-gray-600">Target</div>
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                style={{ 
                  width: `${Math.min(100, (dailySummary.consumed.calories / dailySummary.daily_target) * 100)}%` 
                }}
              ></div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="font-medium text-green-600">{Math.round(dailySummary.consumed.protein)}g</div>
                <div className="text-gray-600">Protein</div>
              </div>
              <div className="text-center">
                <div className="font-medium text-orange-600">{Math.round(dailySummary.consumed.carbs)}g</div>
                <div className="text-gray-600">Carbs</div>
              </div>
              <div className="text-center">
                <div className="font-medium text-purple-600">{Math.round(dailySummary.consumed.fat)}g</div>
                <div className="text-gray-600">Fat</div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-center mb-2">
                <Utensils className="mr-2 text-green-600" size={16} />
                <span className="text-sm font-medium">Meals Logged</span>
              </div>
              <div className="text-2xl font-bold text-gray-800">{dailySummary.entries_count}</div>
            </div>
            
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <div className="flex items-center mb-2">
                <Activity className="mr-2 text-red-600" size={16} />
                <span className="text-sm font-medium">Remaining</span>
              </div>
              <div className="text-2xl font-bold text-gray-800">
                {Math.round(dailySummary.remaining.calories)}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4">
        <button
          onClick={() => setCurrentView('camera')}
          className="bg-blue-600 text-white rounded-xl p-4 flex items-center justify-center space-x-2 shadow-sm hover:bg-blue-700 transition-colors"
        >
          <Camera size={20} />
          <span className="font-medium">Scan Food</span>
        </button>
        
        <button
          onClick={generateMealPlan}
          className="bg-green-600 text-white rounded-xl p-4 flex items-center justify-center space-x-2 shadow-sm hover:bg-green-700 transition-colors"
        >
          <Calendar size={20} />
          <span className="font-medium">Generate Meal Plan</span>
        </button>
      </div>
    </div>
  );

  const renderCamera = () => (
    <div className="p-4 pb-20">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Scan Your Food</h1>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Meal Type
        </label>
        <select
          value={selectedMealType}
          onChange={(e) => setSelectedMealType(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="breakfast">Breakfast</option>
          <option value="lunch">Lunch</option>
          <option value="dinner">Dinner</option>
          <option value="snack">Snack</option>
        </select>
      </div>

      {!showCamera && !capturedImage && (
        <div className="space-y-4">
          <button
            onClick={() => setShowCamera(true)}
            className="w-full bg-blue-600 text-white rounded-xl p-4 flex items-center justify-center space-x-2 shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Camera size={20} />
            <span className="font-medium">Take Photo</span>
          </button>
          
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full bg-gray-600 text-white rounded-xl p-4 flex items-center justify-center space-x-2 shadow-sm hover:bg-gray-700 transition-colors"
          >
            <Upload size={20} />
            <span className="font-medium">Upload Photo</span>
          </button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      )}

      {showCamera && (
        <div className="space-y-4">
          <div className="relative rounded-xl overflow-hidden">
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              className="w-full h-64 object-cover"
              videoConstraints={{
                width: 640,
                height: 480,
                facingMode: "environment"
              }}
            />
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={capturePhoto}
              className="flex-1 bg-blue-600 text-white rounded-xl p-3 font-medium hover:bg-blue-700 transition-colors"
            >
              Capture
            </button>
            <button
              onClick={() => setShowCamera(false)}
              className="flex-1 bg-gray-600 text-white rounded-xl p-3 font-medium hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {capturedImage && (
        <div className="space-y-4">
          <div className="rounded-xl overflow-hidden">
            <img src={capturedImage} alt="Captured food" className="w-full h-64 object-cover" />
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={analyzeFood}
              disabled={analyzing}
              className="flex-1 bg-green-600 text-white rounded-xl p-3 font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {analyzing ? 'Analyzing...' : 'Analyze Food'}
            </button>
            <button
              onClick={() => setCapturedImage(null)}
              className="flex-1 bg-gray-600 text-white rounded-xl p-3 font-medium hover:bg-gray-700 transition-colors"
            >
              Retake
            </button>
          </div>
        </div>
      )}
    </div>
  );

  const renderMeals = () => (
    <div className="p-4 pb-20">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Meal Plans</h1>
      
      {mealPlans.length === 0 ? (
        <div className="text-center py-8">
          <Calendar className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-gray-600 mb-4">No meal plans yet</p>
          <button
            onClick={generateMealPlan}
            className="bg-blue-600 text-white rounded-xl px-6 py-3 font-medium hover:bg-blue-700 transition-colors"
          >
            Generate First Meal Plan
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {mealPlans.map((plan) => (
            <div key={plan.id} className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">
                  {new Date(plan.date).toLocaleDateString()}
                </h3>
                <div className="text-sm text-gray-600">
                  {Math.round(plan.total_calories)} cal
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium text-green-600 mb-2">Breakfast</h4>
                  {plan.breakfast.map((item, idx) => (
                    <div key={idx} className="text-sm text-gray-600 mb-1">
                      {item.name} ({item.calories} cal)
                    </div>
                  ))}
                </div>
                
                <div>
                  <h4 className="font-medium text-blue-600 mb-2">Lunch</h4>
                  {plan.lunch.map((item, idx) => (
                    <div key={idx} className="text-sm text-gray-600 mb-1">
                      {item.name} ({item.calories} cal)
                    </div>
                  ))}
                </div>
                
                <div>
                  <h4 className="font-medium text-red-600 mb-2">Dinner</h4>
                  {plan.dinner.map((item, idx) => (
                    <div key={idx} className="text-sm text-gray-600 mb-1">
                      {item.name} ({item.calories} cal)
                    </div>
                  ))}
                </div>
                
                <div>
                  <h4 className="font-medium text-purple-600 mb-2">Snacks</h4>
                  {plan.snacks.map((item, idx) => (
                    <div key={idx} className="text-sm text-gray-600 mb-1">
                      {item.name} ({item.calories} cal)
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderProfile = () => (
    <div className="p-4 pb-20">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Profile</h1>
      
      {currentUser ? (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Name:</span>
                <span className="font-medium">{currentUser.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Age:</span>
                <span className="font-medium">{currentUser.age} years</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Gender:</span>
                <span className="font-medium capitalize">{currentUser.gender}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Height:</span>
                <span className="font-medium">{currentUser.height} cm</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Weight:</span>
                <span className="font-medium">{currentUser.weight} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Goal:</span>
                <span className="font-medium capitalize">{currentUser.goal.replace('_', ' ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Daily Target:</span>
                <span className="font-medium">{Math.round(currentUser.daily_calorie_target)} cal</span>
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setShowUserForm(true)}
            className="w-full bg-blue-600 text-white rounded-xl p-4 flex items-center justify-center space-x-2 shadow-sm hover:bg-blue-700 transition-colors"
          >
            <Settings size={20} />
            <span className="font-medium">Edit Profile</span>
          </button>
        </div>
      ) : (
        <div className="text-center py-8">
          <User className="mx-auto mb-4 text-gray-400" size={48} />
          <p className="text-gray-600 mb-4">No profile found</p>
          <button
            onClick={() => setShowUserForm(true)}
            className="bg-blue-600 text-white rounded-xl px-6 py-3 font-medium hover:bg-blue-700 transition-colors"
          >
            Create Profile
          </button>
        </div>
      )}
    </div>
  );

  const renderUserForm = () => (
    <div className="p-4 pb-20">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        {currentUser ? 'Edit Profile' : 'Create Profile'}
      </h1>
      
      <form onSubmit={handleCreateUser} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
          <input
            type="text"
            value={userForm.name}
            onChange={(e) => setUserForm({...userForm, name: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
          <input
            type="email"
            value={userForm.email}
            onChange={(e) => setUserForm({...userForm, email: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
            <input
              type="number"
              value={userForm.age}
              onChange={(e) => setUserForm({...userForm, age: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Gender</label>
            <select
              value={userForm.gender}
              onChange={(e) => setUserForm({...userForm, gender: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Height (cm)</label>
            <input
              type="number"
              value={userForm.height}
              onChange={(e) => setUserForm({...userForm, height: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Weight (kg)</label>
            <input
              type="number"
              value={userForm.weight}
              onChange={(e) => setUserForm({...userForm, weight: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Activity Level</label>
          <select
            value={userForm.activity_level}
            onChange={(e) => setUserForm({...userForm, activity_level: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="sedentary">Sedentary (little/no exercise)</option>
            <option value="lightly_active">Lightly Active (light exercise 1-3 days/week)</option>
            <option value="moderately_active">Moderately Active (moderate exercise 3-5 days/week)</option>
            <option value="very_active">Very Active (hard exercise 6-7 days/week)</option>
            <option value="extra_active">Extra Active (very hard exercise/physical job)</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Goal</label>
          <select
            value={userForm.goal}
            onChange={(e) => setUserForm({...userForm, goal: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="lose_weight">Lose Weight</option>
            <option value="maintain_weight">Maintain Weight</option>
            <option value="gain_weight">Gain Weight</option>
          </select>
        </div>
        
        {(userForm.goal === 'lose_weight' || userForm.goal === 'gain_weight') && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Goal Weight (kg)</label>
            <input
              type="number"
              value={userForm.goal_weight}
              onChange={(e) => setUserForm({...userForm, goal_weight: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        )}
        
        <div className="flex space-x-4">
          <button
            type="submit"
            className="flex-1 bg-blue-600 text-white rounded-xl p-4 font-medium hover:bg-blue-700 transition-colors"
          >
            {currentUser ? 'Update Profile' : 'Create Profile'}
          </button>
          <button
            type="button"
            onClick={() => setShowUserForm(false)}
            className="flex-1 bg-gray-600 text-white rounded-xl p-4 font-medium hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );

  if (showUserForm) {
    return (
      <div className="min-h-screen bg-gray-50">
        {renderUserForm()}
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <User className="mx-auto mb-4 text-gray-400" size={64} />
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Welcome to CalorieBuddy!</h1>
          <p className="text-gray-600 mb-6">Create your profile to start tracking your nutrition</p>
          <button
            onClick={() => setShowUserForm(true)}
            className="bg-blue-600 text-white rounded-xl px-8 py-4 font-medium hover:bg-blue-700 transition-colors"
          >
            Get Started
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === 'dashboard' && renderDashboard()}
      {currentView === 'camera' && renderCamera()}
      {currentView === 'meals' && renderMeals()}
      {currentView === 'profile' && renderProfile()}
      {renderNavigation()}
    </div>
  );
}

export default App;