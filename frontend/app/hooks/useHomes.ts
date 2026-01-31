import { useCallback, useEffect, useMemo, useState } from "react";
import type { Home } from "~/types/home";
import similarity from "~/scripts/similarity";


export function useHomes(initialQuery?: Query) {
    const [homes, setHomes] = useState<Home[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState<Home>(initialQuery || {});

    const apiBaseUrl = "http://127.0.0.1:8000";

    const fetchHomes = useCallback(async (queryParams: Home) => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`${apiBaseUrl}/properties`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const homesData: Home[] = await response.json();

            // Filter homes client-side based on queryParams
            const filteredHomes = homesData.filter((home) => {
                if (queryParams.bathrooms && home.bathrooms < queryParams.bathrooms) return false;
                if (queryParams.bedrooms && home.bedrooms < queryParams.bedrooms) return false;
                if (queryParams.amenities && Array.isArray(queryParams.amenities)) {
                    if (!queryParams.amenities.every((a: string) =>
                        home.amenities?.some((ha: string) => ha.toLowerCase() === a.toLowerCase())
                    )) return false;
                }
                if (queryParams.address) {
                    if (!similarity.computeSimilarity(home.address, queryParams.address)) return false;
                }
                return true;
            });

            setHomes(filteredHomes);
        } catch (caughtError: any) {
            setError(caughtError?.message || String(caughtError));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchHomes(query);
    }, [fetchHomes, query]);

    const count = useMemo(() => homes.length, [homes]);

    return { homes, loading, error, query, setQuery, count } as const;
}

export default useHomes;
