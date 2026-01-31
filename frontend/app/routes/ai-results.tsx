import React, { useEffect, useState } from "react";
import { useLocation, useParams } from "react-router";
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

                // Normalize data into an array of results we can display.
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
                await new Promise((resolve) => setTimeout(resolve, 5000));
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
							results.map((r, i) => (
								<pre key={i} className="p-3 bg-white dark:bg-gray-900 border rounded text-sm overflow-auto">
									{JSON.stringify(r, null, 2)}
								</pre>
							))
						)}
					</div>
				)}
			</div>
		</main>
	);
}

