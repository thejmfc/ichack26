import React from "react";

export type Home = {
  id: string | number;
  title: string;
  location: string;
  price: string;
  beds: number;
  baths: number;
  image?: string | null;
  amenities?: string[];
  description?: string;
};

export function HomeCard({ home }: { home: Home }) {
  return (
    <article className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-900">
      <div className="h-44 bg-gray-100 dark:bg-gray-800 flex items-center justify-center overflow-hidden">
        {home.image ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={home.image} alt={home.title} className="w-full h-full object-cover" />
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400">No image</div>
        )}
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
          {home.title}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">{home.location}</p>
        <div className="mt-2 flex items-center justify-between">
          <div className="text-sm text-gray-700 dark:text-gray-200">{home.price}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {home.beds} bedrooms • {home.baths} bathroom{home.baths > 1 ? 's' : ''}
          </div>
        </div>

        {home.amenities && home.amenities.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {home.amenities.slice(0, 4).map((a) => (
              <span
                key={a}
                className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300"
              >
                {a}
              </span>
            ))}
          </div>
        )}

        {home.description && (
          <p className="mt-3 text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
            {home.description}
          </p>
        )}
      </div>
    </article>
  );
}

export default HomeCard;
