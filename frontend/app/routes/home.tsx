import type { Route } from "./+types/home";
import React, { useMemo, useState } from "react";
import HomeCard from "../components/HomeCard";
import useHomes from "../hooks/useHomes";
import { Link } from "react-router";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Find homes — EstateSearch" },
    { name: "description", content: "Search homes by location, bedrooms, bathrooms and amenities." },
  ];
}

const AMENITIES = ["Dishwasher", "Dryer", "Washer", "Parking", "Garden"];

export default function Home() {
  const { homes, similarHomes, loading, error, search, query, count } = useHomes();
  const [showExtras, setShowExtras] = useState(false);

  const [location, setLocation] = useState(query.location ?? "");
  const [beds, setBeds] = useState<number | null>(query.beds ?? null);
  const [baths, setBaths] = useState<number | null>(query.baths ?? null);
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>(query.amenities ?? []);

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) => (prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity]));
  };

  const doSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    search({ location: location || undefined, beds, baths, amenities: selectedAmenities });
  };

  const bedOptions = useMemo(() => [null, 1, 2, 3, 4, 5], []);

  return (
    <main className="pt-16 pb-8 px-4">
      <div className="container mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Find your next home</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2">Search properties by location, bedrooms, bathrooms and amenities.</p>
        </header>

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
                <option key={b} value={b}>{b}+ beds</option>
              ))}
            </select>

            <select
              value={baths ?? ""}
              onChange={(e) => setBaths(e.target.value === "" ? null : Number(e.target.value))}
              className="rounded-md border px-3 py-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            >
              <option value="">Any baths</option>
              {bedOptions.slice(1).map((b) => (
                <option key={b} value={b}>{b}+ baths</option>
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
              {homes.map((h) => (
                <Link to={`/${h.id}`}>
                  <HomeCard key={h.id} home={h} />
                </Link>
              ))}
            </div>
          ) : !loading && similarHomes && similarHomes.length > 0 ? (
            <section className="mt-6">
              <h2 className="text-xl font-semibold mb-3">Similar areas</h2>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">No direct matches for "{location}" — you might like these nearby areas:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {similarHomes.map((h) => (
                  <HomeCard key={h.id} home={h} />
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

