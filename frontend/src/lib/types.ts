export interface Location {
  id: string;
  name: string;
  createdAt: string;
  geometry: GeoJSON.Feature;
}

export interface LocationsState {
  locations: Location[];
  currentPage: number;
  totalPages: number;
  itemsPerPage: number;
}