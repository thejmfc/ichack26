import React, { useState } from "react";
import { useNavigate, Link } from "react-router";

interface FormField {
    name: string;
    label: string;
    type: "text" | "email" | "password";
}

interface AuthFormProps {
    title: string;
    fields: FormField[];
    submitLabel: string;
    loadingLabel: string;
    apiEndpoint: string;
    alternateLink?: {
        text: string;
        to: string;
        linkText: string;
    };
}

/**
 * Reusable authentication form component
 */
export function AuthForm({
    title,
    fields,
    submitLabel,
    loadingLabel,
    apiEndpoint,
    alternateLink,
}: AuthFormProps) {
    const [formData, setFormData] = useState<Record<string, string>>(
        Object.fromEntries(fields.map((f) => [f.name, ""]))
    );
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleChange = (name: string, value: string) => {
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await fetch(apiEndpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || "Request failed");
            if (data.token) {
                localStorage.setItem("token", data.token);
            }
            navigate("/");
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : String(err);
            setError(message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="container mx-auto px-4 py-24 max-w-md">
            <h1 className="text-2xl font-semibold mb-4">{title}</h1>
            <form onSubmit={handleSubmit} className="space-y-4">
                {fields.map((field) => (
                    <div key={field.name}>
                        <label className="block text-sm font-medium">{field.label}</label>
                        <input
                            type={field.type}
                            className="mt-1 block w-full rounded-md border px-3 py-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                            value={formData[field.name]}
                            onChange={(e) => handleChange(field.name, e.target.value)}
                        />
                    </div>
                ))}

                {error && <div className="text-red-600">{error}</div>}

                <div>
                    <button
                        type="submit"
                        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                        disabled={loading}
                    >
                        {loading ? loadingLabel : submitLabel}
                    </button>
                </div>

                {alternateLink && (
                    <p className="text-sm text-center text-gray-600 dark:text-gray-400">
                        {alternateLink.text}{" "}
                        <Link to={alternateLink.to} className="text-blue-600 hover:underline">
                            {alternateLink.linkText}
                        </Link>
                    </p>
                )}
            </form>
        </div>
    );
}

export default AuthForm;
