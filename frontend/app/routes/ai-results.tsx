import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router";
import HomeCard from "~/components/HomeCard";
import type LoadingScreen from "~/components/AiLoad";
import AiLoad from "~/components/AiLoad";

export default function AiResults() {
    const { query } = useParams() as { query?: string };
	const [loading, setLoading] = useState(true);
	const [results, setResults] = useState<any[]>([]);
	const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setError(null);

        const url = `http://127.0.0.1:8000/prompt`;
        if (!query) {
            // nothing to do if no query param provided
            setLoading(false);
            return;
        }

        const controller = new AbortController();
        const signal = controller.signal;

        (async () => {
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ prompt: query }),
                    signal,
                });

                if (!res.ok) {
                    throw new Error(`Request failed: ${res.status} ${res.statusText}`);
                }

                const data = await res.json();

                if (signal.aborted) return;

                if (Array.isArray(data)) {
                    setResults(data);
                } else if (data && typeof data === "object" && Array.isArray((data as any).results)) {
                    setResults((data as any).results);
                } else {
                    setResults([data]);
                }
            } catch (err: any) {
                if (err.name === "AbortError") return; // expected during cleanup
                setError(err?.message || String(err));
            } finally {
                if (!signal.aborted) {
                    // small randomized delay to keep UX consistent
                    await new Promise((resolve) => setTimeout(resolve, Math.random() * 1500 + 2000));
                    setLoading(false);
                }
            }

            if (!signal.aborted) {
                setResults((prev) =>
                    [...prev].sort((a, b) => {
                        const distA = Math.abs(1 - parseFloat(a.distance ?? a.Distance ?? "0"));
                        const distB = Math.abs(1 - parseFloat(b.distance ?? b.Distance ?? "0"));
                        return distA - distB;
                    })
                );
            }
        })();

        return () => {
            controller.abort();
        };
    }, [query]);

    if (loading) { return <AiLoad /> }
	return (
		<main className="pt-16 pb-8 px-4 w-full flex flex-col items-center justify-center">
            <h1 className="text-2xl font-semibold mb-4">Results for '{query?.substring(0,30)}{query?.length > 30 ? '...' : ''}'</h1>
            <div className="container mx-auto max-w-3xl grid grid-cols-1 md:grid-cols-3 gap-6 items-start justify-center">

                {error ? (
                    <div className="text-red-600">{error}</div>
                ) : results.length === 0 ? (
                    <div className="text-gray-600">No results.</div>
                ) : (
                    results.map((r, idx) => {
                        const lines = (r.document || "").split("\n");
                        const keyValuePairs = lines
                            .map((line: string) => {
                                const [key, ...rest] = line.split(":");
                                if (!key || rest.length === 0) return null;
                                return { key: key.trim(), value: rest.join(":").trim() };
                            })
                            .filter(Boolean) as { key: string; value: string }[];


                        const home: Home = keyValuePairs.reduce((acc: Home, pair) => {
                            acc[pair.key.toLowerCase().replaceAll(" ", "_")] = pair.value;
                            return acc;
                        }, {} as Home);

                        // Fill missing fields from r if available
                        home.id = home.id ?? r.id ?? idx;
                        home.price_per_person = home.price_per_person ?? r.price_per_person ?? "";
                        home.city = home.city ?? r.city ?? "";
                        home.address = home.address ?? r.address ?? "";
                        home.amenities = home.amenities ?? r.amenities ?? [];
                        home.image = home.image ?? r.image ?? "";
                        home.name = home.name ?? r.name ?? "";
                        home.description = home.description ?? r.description ?? "";
                        home.distance = home.distance ?? r.distance ?? "";
                        home.image = home.image ?? ""
                        home.niceness_rating = Number(home.niceness_rating) ?? 0

                        if (typeof home.amenities === "string") {
                            home.amenities = home.amenities.split(",").map((a: string) => a.trim());
                        }

                        return (
                            <Link to={`/homes/${Number(home.id) + 1}`} key={Number(home.id) + 1} className="relative p-5">
                                {idx === 0 && (
                                    <p className="absolute top-7 border px-2 py-1 text-center rounded-2xl text-green-800 bg-green-200 left-7 z-40 min-w-20 whitespace-nowrap">
                                        Best Match
                                    </p>
                                )}
                                {idx !== 0 && Number(home.price_per_person.replaceAll('£', '')) < 80 && 
                                    (
                                        <p className="absolute top-7 left-7 text-center border px-2 py-1 rounded-2xl text-blue-800 bg-blue-200 z-40 min-w-20 whitespace-nowrap">
                                            Cheap
                                        </p>
                                    )
                                }
                                <HomeCard home={home} />
                            </Link>
                        );
                    })
                )}
			</div>
		</main>
	);
}

