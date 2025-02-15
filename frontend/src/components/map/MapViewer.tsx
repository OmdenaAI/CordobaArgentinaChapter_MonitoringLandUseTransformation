import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polygon, Popup } from 'react-leaflet';
import axiosInstance from '../../config/axios';
import 'leaflet/dist/leaflet.css';

interface Place {
  id: number;
  name: string;
  description: string;
  geometry: any;
  created_at: string;
}

export function MapViewer() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPlaces();
  }, []);

  const fetchPlaces = async () => {
    try {
      const response = await axiosInstance.get('/places/');
      setPlaces(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching places:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 h-full">
      <div className="bg-white rounded-lg shadow-md p-4 h-full">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Places Overview</h2>
          <span className="text-sm text-gray-500">
            {places.length} places found
          </span>
        </div>
        <div className="h-[calc(100vh-200px)]">
          <MapContainer
            center={[-31.4201, -64.1888]}
            zoom={11}
            className="h-full w-full rounded-lg"
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {places.map((place) => (
              <Polygon
                key={place.id}
                positions={place.geometry.coordinates[0].map((coord: number[]) => [coord[1], coord[0]])}
                pathOptions={{ 
                  color: 'blue', 
                  fillColor: 'blue', 
                  fillOpacity: 0.2,
                  weight: 2
                }}
              >
                <Popup>
                  <div className="p-2">
                    <h3 className="font-semibold text-lg">{place.name}</h3>
                    <p className="text-gray-600 mt-1">{place.description}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      Created: {new Date(place.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </Popup>
              </Polygon>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}