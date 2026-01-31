/**
 * Represents a home/property listing
 */
export interface Home {
    id: number
    price_per_person: number;
    city: string;
    address: string;
    bedrooms: number;
    bathrooms: number;
    distance: number;
    vibe: string;
    bills_included: boolean;
    amenities: string[];
    description?: string;
    image?: string;
    location?: string;
}

/**
 * Query parameters for searching homes
 */
export interface HomeQuery {
    location?: string;
    bedrooms?: number;
    bathrooms?: number;
    amenities?: string[];
}
