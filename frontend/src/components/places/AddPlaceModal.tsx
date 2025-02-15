import React, { useState, useRef } from 'react';
import { X } from 'lucide-react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import axiosInstance from '../../config/axios';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';

interface AddPlaceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPlaceAdded: (place: any) => void;
}

interface PlaceForm {
  name: string;
  description: string;
  geometry: any;
}

export default function AddPlaceModal({ isOpen, onClose, onPlaceAdded }: AddPlaceModalProps) {
  const [formData, setFormData] = useState<PlaceForm>({
    name: '',
    description: '',
    geometry: null,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const featureGroupRef = useRef<any>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.geometry) {
      setError('Please draw a polygon on the map');
      return;
    }

    setLoading(true);
    try {
      const response = await axiosInstance.post('/places/', {
        name: formData.name,
        description: formData.description,
        geometry: formData.geometry,
      });
      onPlaceAdded(response.data);
    } catch (err) {
      setError('Failed to create place');
    } finally {
      setLoading(false);
    }
  };

  const handleCreated = (e: any) => {
    const layer = e.layer;
    const geoJSON = layer.toGeoJSON();
    setFormData(prev => ({
      ...prev,
      geometry: geoJSON.geometry
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg w-full max-w-3xl">
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Add New Place</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-4">
            {error && (
              <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              <div className="h-96">
                <MapContainer
                  center={[-31.4201, -64.1888]} // Córdoba, Argentina
                  zoom={13}
                  className="h-full w-full rounded-lg"
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <FeatureGroup ref={featureGroupRef}>
                    <EditControl
                      position="topright"
                      onCreated={handleCreated}
                      draw={{
                        rectangle: false,
                        circle: false,
                        circlemarker: false,
                        marker: false,
                        polyline: false,
                      }}
                    />
                  </FeatureGroup>
                </MapContainer>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Place'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
} 