import type { Route } from "./+types/home";
import React, { useMemo, useState } from "react";
import HomeCard from "../components/HomeCard";
import useHomes from "../hooks/useHomes";
import { Link } from "react-router";
import { PiSparkleFill } from "react-icons/pi";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Find homes — EstateSearch" },
    { name: "description", content: "Search homes by location, bedrooms, bathrooms and amenities." },
  ];
}

const AMENITIES = ["Dishwasher", "Dryer", "Washer", "Parking", "Garden"];

export default function Home() {
  const { homes, loading, error, query, count } = useHomes();
  const [showExtras, setShowExtras] = useState(false);
  const [aiQuery, setAiQuery] = useState("");

  const [location, setLocation] = useState(query.location ?? "");
  const [beds, setBeds] = useState<number | null>(query.beds ?? null);
  const [baths, setBaths] = useState<number | null>(query.baths ?? null);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>(query.amenities ?? []);

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) => (prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity]));
  };

  const handleAiSearch = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await fetch("/prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: aiQuery }),
      });
      if (!response.ok) {
        throw new Error("Failed to generate embeddings");
      }
      const data = await response.json();
      console.log("Embed vectors:", data.embeds);
      // You can now use data.embeds for further search/filtering
    } catch (err) {
      console.error("AI Search error:", err);
    }
  };

  const bedOptions = useMemo(() => [null, 1, 2, 3, 4, 5], []);

  return (
    <main className="pt-16 pb-8 px-4">
      <div className="container mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Find your next home</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">Search properties by location, bedrooms, bathrooms and amenities.</p>
        </header>

        {/* AI Search Bar */}
        <div className="max-w-2xl mx-auto mb-8">
          <form onSubmit={handleAiSearch} className="relative">
            <div className="relative flex items-center bg-white dark:bg-gray-900 border-2 border-gray-200 dark:border-gray-700 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 focus-within:border-blue-500 dark:focus-within:border-blue-400">
              {/* Star Icon */}
              <div className="pl-6 pr-4 flex items-center">
                <PiSparkleFill className="w-6 h-6 text-purple-600/75" />
              </div>
              
              {/* Search Input */}
              <input
                type="text"
                value={aiQuery}
                onChange={(e) => setAiQuery(e.target.value)}
                placeholder="Ask AI"
                className="flex-1 py-4 px-2 bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 border-none outline-none text-lg"
              />
              
              {/* Search Button */}
              <button
                type="submit"
                className="mr-3 px-6 py-2 bg-linear-to-r from-blue-600 to-purple-600 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 transition-all duration-300 shadow-md hover:shadow-lg"
              >
                Search
              </button>
            </div>
          </form>
        </div>

        {/* Divider with "OR" */}
        <div className="flex items-center justify-center mb-6">
          <div className="border-t border-gray-300 dark:border-gray-600 flex-1"></div>
          <span className="px-4 text-gray-500 dark:text-gray-400 text-sm font-medium">OR USE FILTERS</span>
          <div className="border-t border-gray-300 dark:border-gray-600 flex-1"></div>
        </div>

        <form onSubmit={doSearch} className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-3 items-center">
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Enter a location (town, city or postcode)"
              className="flex-1 rounded-md border px-3 py-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            />

            <select
              value={beds ?? ""}
              onChange={(e) => setBeds(e.target.value === "" ? null : Number(e.target.value))}
              className="rounded-md border px-3 py-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">Any beds</option>
              {bedOptions.slice(1).map((b) => (
                <option key={b} value={b!}>{b}+ beds</option>
              ))}
            </select>

            <select
              value={baths ?? ""}
              onChange={(e) => setBaths(e.target.value === "" ? null : Number(e.target.value))}
              className="rounded-md border px-3 py-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">Any baths</option>
              {bedOptions.slice(1).map((b) => (
                <option key={b} value={b!}>{b}+ baths</option>
              ))}
            </select>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowExtras((s) => !s)}
                className="rounded-md px-4 py-2 border min-w-32 border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm"
              >
                {showExtras ? "Hide extras" : "Show extras"}
              </button>
              <button type="submit" className="rounded-md px-4 py-2 bg-blue-600 text-white">Search</button>
            </div>
          </div>

          {showExtras && (
            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2">
              {AMENITIES.map((a) => {
                const active = selectedAmenities.includes(a);
                return (
                  <button
                    key={a}
                    type="button"
                    onClick={() => toggleAmenity(a)}
                    className={`text-sm px-3 py-2 rounded-md border ${active ? "bg-blue-600 text-white border-blue-600" : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700"}`}
                  >
                    {a}
                  </button>
                );
              })}
            </div>
          )}
        </form>

        <section>
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm text-gray-600 dark:text-gray-300">{loading ? "Searching..." : `${count} properties found`}</div>
            {error && <div className="text-sm text-red-600">{error}</div>}
          </div>

          {homes.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {homes.map((h, idx) => (
                <Link to={`/${idx+1}`}>
                  <HomeCard key={idx} home={h} />
                </Link>
              ))}
            </div>
          ) : !loading && similarHomes && similarHomes.length > 0 ? (
            <section className="mt-6">
              <h2 className="text-xl font-semibold mb-3">Similar areas</h2>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">No direct matches for "{location}" — you might like these nearby areas:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {similarHomes.map((h) => (
                  <HomeCard key={h.address} home={h} />
                ))}
              </div>
            </section>
          ) : (
            <div className="text-sm text-gray-600 dark:text-gray-300">{loading ? "Searching..." : "No properties found."}</div>
          )}
        </section>
      </div>
    </main>
  );
}

