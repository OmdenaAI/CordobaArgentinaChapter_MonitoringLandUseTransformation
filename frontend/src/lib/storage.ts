import { Location } from './types';

const STORAGE_KEY = 'satellite_locations';

export const storage = {
  getLocations: (): Location[] => {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  },

  saveLocation: async (location: Location): Promise<void> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const locations = storage.getLocations();
    locations.push(location);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(locations));
  },

  deleteLocation: async (id: string): Promise<void> => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    const locations = storage.getLocations();
    const filtered = locations.filter(loc => loc.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
  }
};