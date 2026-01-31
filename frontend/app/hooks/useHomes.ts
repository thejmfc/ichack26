import { useCallback, useEffect, useMemo, useState } from "react";
import type { Home } from "~/types/home";


export function useHomes(initialQuery?: Query) {
    const [homes, setHomes] = useState<Home[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [query, setQuery] = useState<Home>(initialQuery || {});

    const apiBaseUrl = "http://127.0.0.1:8000";

    const fetchHomes = useCallback(async (queryParams: any) => {
        setLoading(true);
        setError(null);
        try {;
                const response = await fetch(`${apiBaseUrl}/properties`);

                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const homesData: Home[] = await response.json();
                setHomes(homesData || []);

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
