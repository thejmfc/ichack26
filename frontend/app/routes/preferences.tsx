import React, { useState, useEffect } from "react";
import { Link } from "react-router";
import type { Home } from "../types/home";
import HomeCard from "../components/HomeCard";

export function meta() {
  return [
    { title: "Calibrate Preferences — EstateSearch" },
    { name: "description", content: "Help us understand your preferences by comparing properties." },
  ];
}

const apiBaseUrl = "http://127.0.0.1:8000";

export default function Preferences() {
  const [properties, setProperties] = useState<Home[]>([]);
  const [currentPair, setCurrentPair] = useState<[Home, Home] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completedComparisons, setCompletedComparisons] = useState(0);
  const [preferences, setPreferences] = useState<Record<string, number>>({});

  const maxComparisons = 10;

  // Fetch properties on mount
  useEffect(() => {
    const fetchProperties = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/properties`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data: Home[] = await response.json();
        
        // Ensure properties have IDs
        data.forEach((home, idx) => {
          if (!home.id) {
            (home as any).id = idx + 1;
          }
        });
        
        setProperties(data);
        generateNewPair(data);
      } catch (err: any) {
        setError(err?.message || String(err));
      } finally {
        setLoading(false);
      }
    };

    fetchProperties();
  }, []);

  // Generate a random pair of properties
  const generateNewPair = (propertyList: Home[] = properties) => {
    if (propertyList.length < 2) return;
    
    const shuffled = [...propertyList].sort(() => 0.5 - Math.random());
    setCurrentPair([shuffled[0], shuffled[1]]);
  };

// Handle preference selection
const handlePreference = async (selectedHome: Home | null) => {
    if (!currentPair) return;

    if (selectedHome) {
        const homeId = selectedHome.id.toString();
        setPreferences(prev => ({
            ...prev,
            [homeId]: (prev[homeId] || 0) + 1
        }));

        // Send preference to backend
        try {
            await fetch(`${apiBaseUrl}/user/preferences/${homeId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({}),
            });
        } catch (err) {
            // Optionally handle error (e.g., show notification)
            // For now, ignore errors
        }
    }

    setCompletedComparisons(prev => prev + 1);

    // Check if we've completed enough comparisons
    if (completedComparisons + 1 >= maxComparisons) {
        // Save preferences to localStorage (you could also send to backend)
        localStorage.setItem('userPreferences', JSON.stringify(preferences));
        return;
    }

    // Generate new pair
    generateNewPair();
};

  if (loading) {
    return (
      <main className="pt-16 px-4">
        <div className="container mx-auto max-w-4xl text-center py-12">
          <div className="text-gray-600 dark:text-gray-300">Loading properties...</div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="pt-16 px-4">
        <div className="container mx-auto max-w-4xl text-center py-12">
          <div className="text-red-600">Error: {error}</div>
          <Link to="/" className="text-blue-600 hover:underline mt-4 inline-block">
            ← Back to search
          </Link>
        </div>
      </main>
    );
  }

  if (completedComparisons >= maxComparisons) {
    return (
      <main className="pt-16 px-4">
        <div className="container mx-auto max-w-4xl text-center py-12">
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-8">
            <div className="text-6xl mb-4">🎉</div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Preferences Calibrated!
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Thank you for helping us understand your preferences. Your search results will now be more personalized.
            </p>
            <Link 
              to="/"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Start Searching
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="pt-16 px-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/" className="text-blue-600 hover:underline mb-4 inline-block">
            ← Back to search
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Calibrate Your Preferences
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mb-4">
            Compare properties to help us understand what you're looking for
          </p>
          
          {/* Progress Bar */}
          <div className="max-w-md mx-auto mb-6">
            <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
              <span>Progress</span>
              <span>{completedComparisons}/{maxComparisons}</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(completedComparisons / maxComparisons) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {currentPair && (
          <>
            <div className="text-center mb-8">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Which property do you prefer?
              </h2>
            </div>

            {/* Property Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
              {currentPair.map((home) => (
                <div 
                  key={home.id} 
                  className="cursor-pointer transform transition-all duration-300 hover:scale-105 hover:shadow-xl border-2 border-transparent hover:border-blue-300 rounded-xl"
                  onClick={() => handlePreference(home)}
                >
                  <HomeCard home={home} />
                </div>
              ))}
            </div>

            {/* No Preference Option */}
            <div className="text-center">
              <button
                onClick={() => handlePreference(null)}
                className="px-8 py-3 bg-gray-500 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
              >
                No Preference / Skip
              </button>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                Click this if both properties are equally appealing or unappealing
              </p>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
