import React from "react";
import type { Home } from "~/types/home";

// Converts niceness_rating (1-10 scale) to 5-star rating
function StarRating({ niceness_rating }: { niceness_rating: number }) {
  const rating = niceness_rating / 2; // Convert 1-10 to 0.5-5
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  return (
    <div className="flex items-center gap-0.5 text-yellow-400">
      {Array(fullStars).fill(null).map((_, i) => (
        <span key={`full-${i}`}>★</span>
      ))}
      {hasHalfStar && <span>★</span>}
      {Array(emptyStars).fill(null).map((_, i) => (
        <span key={`empty-${i}`} className="text-gray-300 dark:text-gray-600">★</span>
      ))}
    </div>
  );
}

export function HomeCard({ home }: { home: Home }) {
  return (
      <article className="border rounded-lg min-h-92 max-h-92 min-w-80 overflow-hidden shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-900">
        <div className="h-44 bg-gray-100 dark:bg-gray-800 flex items-center justify-center overflow-hidden">
          {home.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={home.image} alt={home.address} className="w-full h-full object-cover" />
          ) : (
            <div className="text-sm text-gray-500 dark:text-gray-400">No image</div>
          )}
        </div>
        <div className="p-4">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate flex-1">
              {home.address}
            </h3>
            {1 == 1&& (
              <div className="flex items-center gap-1 ml-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">{(home?.niceness_rating ?? 0).toFixed(1)}</span>
              </div>
            )}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{home.location}</p>
          <div className="mt-2 flex items-center justify-between">
            <div className="text-sm text-gray-700 dark:text-gray-200">{home.price_per_person} per person</div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {home.bedrooms} bedrooms • {home.bathrooms} bathroom{home.bathrooms > 1 ? 's' : ''}
            </div>
          </div>

          {home.amenities && home.amenities.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {home.amenities.slice(0, 4).map((a) => (
                <span
                  key={a}
                  className="text-xs px-2 py-1 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300"
                >
                  {a.replaceAll('_', ' ')}
                </span>
              ))}
            </div>
          )}

          {home.description && (
            <p className="mt-3 mb-3 text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
              {home.description}
            </p>
          )}
        </div>
      </article>
  );
}

export default HomeCard;
