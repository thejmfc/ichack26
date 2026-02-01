import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import type { Home } from "../../types/home";

export function meta({ params }: { params: Record<string, string> }) {
  const id = params?.id ?? "";
  return [{ title: `Property ${id} — EstateSearch` }];
}

const apiBaseUrl = "http://127.0.0.1:8000";

export default function PropertyDetails() {
  const { id } = useParams() as { id?: string };
  const [home, setHome] = useState<Home | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const fetchProperty = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBaseUrl}/properties/${encodeURIComponent(id)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Home = await res.json();
        if (!cancelled) setHome(data);
      } catch (e: any) {
        if (!cancelled) setError(e?.message || String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchProperty();

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (!id) {
    return (
      <main className="pt-16 px-4">
        <div className="container mx-auto">Missing property id.</div>
      </main>
    );
  }

  return (
    <main className="pt-16 px-4">
      <div className="container mx-auto">
        <div className="mb-4">
          <Link to="/" className="text-blue-600">← Back to search</Link>
        </div>

        {loading ? (
          <div className="text-gray-600">Loading property #{id}…</div>
        ) : error ? (
          <div className="text-red-600">Error: {error}</div>
        ) : !home ? (
          <div className="text-gray-600">No property found.</div>
        ) : (
          <article className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6">
            {home.image && (
              <div className="mb-4">
                <img src={home.image} alt={home.address} className="w-full rounded-md object-cover h-64" />
              </div>
            )}

            <header className="mb-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{home.address}</h1>
                {(home.niceness_rating ?? 0) > 0 && (
                  <StarRating niceness_rating={home.niceness_rating ?? 0} />
                )}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-300">{home.city}</div>
            </header>

            <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="col-span-2">
                <p className="text-gray-700 dark:text-gray-300 mb-3">{home.description ?? "No description available."}</p>
                <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li><strong>Bedrooms:</strong> {home.bedrooms ?? home.beds ?? "—"}</li>
                  <li><strong>Bathrooms:</strong> {home.bathrooms ?? home.baths ?? "—"}</li>
                  <li><strong>Distance:</strong> {home.distance ?? "—"} km</li>
                  <li><strong>Vibe:</strong> {home.vibe ?? "—"}</li>
                  <li><strong>Bills included:</strong> {home.bills_included ? "Yes" : "No"}</li>
                </ul>
              </div>

              <aside className="p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                <div className="text-lg font-bold mb-2">{home.price ?? home.price_per_person ? `£${home.price ?? home.price_per_person}` : "Price N/A"}</div>
                <div className="text-sm text-gray-600 dark:text-gray-300 mb-3">{home.location ?? ""}</div>

                {home.amenities && home.amenities.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">Amenities</h3>
                    <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                      {home.amenities.map((a) => (
                        <li key={a}>• {a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </aside>
            </section>
          </article>
        )}
      </div>
    </main>
  );
}
