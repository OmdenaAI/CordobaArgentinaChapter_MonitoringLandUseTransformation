import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import { MapPin } from 'lucide-react';
import axiosInstance from '../config/axios';
import AddPlaceModal from '../components/places/AddPlaceModal';

interface Place {
  id: number;
  name: string;
  description: string;
  geometry: any;
  created_at: string;
  updated_at: string | null;
}

export default function Places() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPlaces();
  }, []);

  const fetchPlaces = async () => {
    try {
      const response = await axiosInstance.get('/places/');
      setPlaces(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to load places');
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this place?')) {
      try {
        await axiosInstance.delete(`/places/${id}`);
        setPlaces(places.filter(place => place.id !== id));
      } catch (err) {
        setError('Failed to delete place');
      }
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">My Places</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Add Place
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {places.map((place) => (
            <div
              key={place.id}
              className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
            >
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    <h3 className="text-lg font-semibold text-gray-900">{place.name}</h3>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleDelete(place.id)}
                      className="p-1 text-gray-500 hover:text-red-600 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1 text-gray-500 hover:text-blue-600 rounded"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="mt-2 text-gray-600">{place.description}</p>
                <div className="mt-4 text-sm text-gray-500">
                  Created: {new Date(place.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <AddPlaceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onPlaceAdded={(newPlace) => {
          setPlaces([...places, newPlace]);
          setIsModalOpen(false);
        }}
      />
    </div>
  );
} 