// API base URL - detect environment
const getApiBase = () => {
    // Check for explicit env variable first
    if (import.meta.env.VITE_API_BASE) {
        return import.meta.env.VITE_API_BASE;
    }
    // For production on exe.xyz, use the backend port
    if (typeof window !== 'undefined' && window.location.hostname.includes('exe.xyz')) {
        return `https://${window.location.hostname}:8000`;
    }
    // Default to localhost for development
    return 'http://localhost:8000';
};

export const API_BASE = getApiBase();
