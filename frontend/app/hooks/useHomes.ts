import { useCallback, useEffect, useMemo, useState } from "react";
import type { Home } from "../components/HomeCard";

type Query = {
  location?: string;
  beds?: number | null;
  baths?: number | null;
  amenities?: string[];
};

export function useHomes(initialQuery?: Query) {
  const [homes, setHomes] = useState<Home[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState<Query>(initialQuery || {});

  const apiBase = import.meta.env.VITE_HOMES_API_URL as string | undefined;

  const fetchHomes = useCallback(async (q: Query) => {
    setLoading(true);
    setError(null);
    try {
      if (apiBase) {
        const params = new URLSearchParams();
        if (q.location) params.set("location", q.location);
        if (q.beds != null) params.set("beds", String(q.beds));
        if (q.baths != null) params.set("baths", String(q.baths));
        if (q.amenities && q.amenities.length) params.set("amenities", q.amenities.join(","));

        const res = await fetch(`${apiBase.replace(/\/$/, "")}/homes?${params.toString()}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: Home[] = await res.json();
        setHomes(data || []);
      } else {
        // fallback sample data if no API configured
        await new Promise((r) => setTimeout(r, 250));
        const sample: Home[] = [
          {
            id: 1,
            title: "Charming 3-bedroom terrace",
            location: "Brighton, BN1",
            price: "£425,000",
            beds: 3,
            baths: 2,
            image: null,
            amenities: ["Dishwasher", "Washer"],
            description: "Lovely terrace house close to shops and transport.",
          },
          {
            id: 2,
            title: "Modern apartment with balcony",
            location: "London, SW1",
            price: "£1,100,000",
            beds: 2,
            baths: 1,
            image: null,
            amenities: ["Dryer", "Parking"],
            description: "Bright apartment with great views.",
          },
          {
            id: 3,
            title: "Family home with garden",
            location: "Manchester, M1",
            price: "£625,000",
            beds: 4,
            baths: 3,
            image: null,
            amenities: ["Dishwasher", "Dryer", "Washer"],
            description: "Spacious family home with a large garden.",
          },
        ];

        // apply simple client-side filters
        let filtered = sample;
        if (q.location) {
          const lc = q.location.toLowerCase();
          filtered = filtered.filter((h) => h.location.toLowerCase().includes(lc) || h.title.toLowerCase().includes(lc));
        }
        if (q.beds != null) filtered = filtered.filter((h) => h.beds >= (q.beds || 0));
        if (q.baths != null) filtered = filtered.filter((h) => h.baths >= (q.baths || 0));
        if (q.amenities && q.amenities.length) {
          filtered = filtered.filter((h) => q.amenities!.every((a) => h.amenities?.includes(a)));
        }

        setHomes(filtered);
      }
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }, [apiBase]);

  useEffect(() => {
    fetchHomes(query);
  }, [fetchHomes, query]);

  const search = useCallback((q: Query) => setQuery((prev) => ({ ...prev, ...q })), []);

  const count = useMemo(() => homes.length, [homes]);

  return { homes, loading, error, search, query, setQuery, count } as const;
}

export default useHomes;
