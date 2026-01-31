import React, { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router";
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

        (async () => {
            try {
                const res = await fetch(url, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ prompt: query }),
                });
                const data = await res.json();

                if (Array.isArray(data)) {
                    setResults(data);
                } else if (data && typeof data === "object" && Array.isArray((data as any).results)) {
                    setResults((data as any).results);
                } else {
                    setResults([data]);
                }
            } catch (err: any) {
                setError(err?.message || String(err));
            } finally {
                await new Promise((resolve) => setTimeout(resolve, Math.random() * 1500 + 2000));
                setLoading(false);
            }
        })();
    }, [query]);

	return (
		<main className="pt-16 pb-8 px-4">
			<div className="container mx-auto max-w-3xl">
				<h1 className="text-2xl font-semibold mb-4">AI Results</h1>

				{loading ? (
					<AiLoad />
				) : error ? (
					<div className="text-red-600">{error}</div>
				) : (
					<div className="space-y-3">
						{results.length === 0 ? (
							<div className="text-gray-600">No results.</div>
						) : (
							results.map((r) => (
                                    results.slice(1).map((r, idx) => {
                                        const lines = r.document.split("\n");
                                        const keyValuePairs = lines
                                            .map((line: string) => {
                                                const [key, ...rest] = line.split(":");
                                                if (!key || rest.length === 0) return null;
                                                return { key: key.trim(), value: rest.join(":").trim() };
                                            })
                                            .filter(Boolean) as { key: string; value: string }[];

                                        // Define Home type
                                        type Home = {
                                            [key: string]: string;
                                        };

                                        // Coerce keyValuePairs into Home
                                        const home: Home = keyValuePairs.reduce((acc: Home, pair) => {
                                            acc[pair.key.toLowerCase().replaceAll(' ', '_')] = pair.value;
                                            return acc;
                                        }, {});

                                        // Convert amenities to array if it exists and is a string
                                        if (typeof home.amenities === "string") {
                                            home.amenities = home.amenities.split(",").map((a: string) => a.trim());
                                        }

                                        console.log(home)

                                        return (
                                            <HomeCard home={home} />
                                        );
                                    })
							))
						)}
					</div>
				)}
			</div>
		</main>
	);
}

