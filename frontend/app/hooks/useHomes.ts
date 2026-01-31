import { useCallback, useEffect, useMemo, useState } from "react";
import type { Home } from "../components/HomeCard";
import { computeSimilarity } from "../scripts/similarity";

type Query = {
    location?: string;
    beds?: number | null;
    baths?: number | null;
    amenities?: string[];
};

export function useHomes(initialQuery?: Query) {
    const [homes, setHomes] = useState<Home[]>([]);
    const [similarHomes, setSimilarHomes] = useState<Home[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState<Query>(initialQuery || {});

    const apiBaseUrl = import.meta.env.VITE_HOMES_API_URL as string | undefined;

    // similarity logic moved to ../scripts/similarity.ts (computeSimilarity)

    const fetchHomes = useCallback(async (queryParams: Query) => {
        setLoading(true);
        setError(null);
        try {
            if (apiBaseUrl) {
                const urlParams = new URLSearchParams();
                if (queryParams.location) urlParams.set("location", queryParams.location);
                if (queryParams.beds != null) urlParams.set("beds", String(queryParams.beds));
                if (queryParams.baths != null) urlParams.set("baths", String(queryParams.baths));
                if (queryParams.amenities && queryParams.amenities.length) urlParams.set("amenities", queryParams.amenities.join(","));

                const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/homes?${urlParams.toString()}`);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const homesData: Home[] = await response.json();
                setHomes(homesData || []);

                // if no direct results and a location was provided, try to fetch candidate homes and compute similar areas
                if ((homesData || []).length === 0 && queryParams.location) {
                    try {
                        // fetch candidate homes without location filter but keep other filters to narrow down
                        const candidateParams = new URLSearchParams();
                        if (queryParams.beds != null) candidateParams.set("beds", String(queryParams.beds));
                        if (queryParams.baths != null) candidateParams.set("baths", String(queryParams.baths));
                        if (queryParams.amenities && queryParams.amenities.length) candidateParams.set("amenities", queryParams.amenities.join(","));

                        const candRes = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/homes?${candidateParams.toString()}`);
                        if (candRes.ok) {
                            const candidates: Home[] = await candRes.json();
                            const similarHomesScored = candidates
                                .map((candidateHome) => ({
                                    home: candidateHome,
                                    score: Math.max(
                                        computeSimilarity(queryParams.location, candidateHome.location),
                                        computeSimilarity(queryParams.location, candidateHome.title)
                                    ),
                                }))
                                .filter((scoredHome) => scoredHome.score > 0.25)
                                .sort((a, b) => b.score - a.score)
                                .slice(0, 8)
                                .map((scoredHome) => scoredHome.home);

                            setSimilarHomes(similarHomesScored);
                        } else {
                            setSimilarHomes([]);
                        }
                    } catch (e) {
                        setSimilarHomes([]);
                    }
                } else {
                    setSimilarHomes([]);
                }
            } else {
                // fallback sample data if no API configured
                await new Promise((resolve) => setTimeout(resolve, 250));
                const sampleHomes: Home[] = [
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
                let filteredHomes = sampleHomes;
                if (queryParams.location) {
                    const locationLower = queryParams.location.toLowerCase();
                    filteredHomes = filteredHomes.filter((home) =>
                        home.location.toLowerCase().includes(locationLower) ||
                        home.title.toLowerCase().includes(locationLower)
                    );
                }
                if (queryParams.beds != null) filteredHomes = filteredHomes.filter((home) => home.beds >= (queryParams.beds || 0));
                if (queryParams.baths != null) filteredHomes = filteredHomes.filter((home) => home.baths >= (queryParams.baths || 0));
                if (queryParams.amenities && queryParams.amenities.length) {
                    filteredHomes = filteredHomes.filter((home) =>
                        queryParams.amenities!.every((amenity) => home.amenities?.includes(amenity))
                    );
                }


                setHomes(filteredHomes);

                // if no direct matches for client-side sample, compute similar matches from sample set
                if (filteredHomes.length === 0 && queryParams.location) {
                    const scored = sampleHomes
                        .map((c) => ({ home: c, score: Math.max(computeSimilarity(queryParams.location, c.location), computeSimilarity(queryParams.location, c.title)) }))
                        .filter((s) => s.score > 0.25)
                        .sort((a, b) => b.score - a.score)
                        .slice(0, 8)
                        .map((s) => s.home);
                    setSimilarHomes(scored);
                } else {
                    setSimilarHomes([]);
                }
            }
        } catch (caughtError: any) {
            setError(caughtError?.message || String(caughtError));
        } finally {
            setLoading(false);
        }
    }, [apiBaseUrl]);

    useEffect(() => {
        fetchHomes(query);
    }, [fetchHomes, query]);

    const search = useCallback((newQuery: Query) => setQuery((prevQuery) => ({ ...prevQuery, ...newQuery })), []);

    const count = useMemo(() => homes.length, [homes]);

    return { homes, similarHomes, loading, error, search, query, setQuery, count } as const;
}

export default useHomes;
