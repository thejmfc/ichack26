export type Home = {
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
    price?: string | number;
    beds?: number;
    baths?: number;
};
