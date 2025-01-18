import React, { useState, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, LayersControl, ZoomControl, FeatureGroup, GeoJSON } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Trash2, Map as MapIcon } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { storage } from '../../lib/storage';
import { Location, LocationsState } from '../../lib/types';
import { cn } from '../../lib/utils';

const ITEMS_PER_PAGE = 5;

export function MapViewer() {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mapRef = useRef(null);
  const queryClient = useQueryClient();

  // Fetch locations
  const { data: locations = [] } = useQuery({
    queryKey: ['locations'],
    queryFn: storage.getLocations,
  });

  // Calculate pagination
  const totalPages = Math.ceil(locations.length / ITEMS_PER_PAGE);
  const paginatedLocations = locations.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Mutations
  const saveMutation = useMutation({
    mutationFn: storage.saveLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      setSuccessMessage('Location saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: storage.deleteLocation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] });
      setSuccessMessage('Location deleted successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    },
  });

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = JSON.parse(e.target?.result as string);
        if (!content.type || content.type !== 'Feature') {
          throw new Error('Invalid GeoJSON format');
        }

        const newLocation: Location = {
          id: uuidv4(),
          name: file.name.replace('.geojson', ''),
          createdAt: new Date().toISOString(),
          geometry: content,
        };

        await saveMutation.mutateAsync(newLocation);
      } catch (error) {
        setUploadError('Invalid GeoJSON file format');
        setTimeout(() => setUploadError(null), 3000);
      }
    };
    reader.readAsText(file);
  };

  const handleDrawCreated = async (e: any) => {
    const layer = e.layer;
    const geoJson = layer.toGeoJSON();

    const newLocation: Location = {
      id: uuidv4(),
      name: `Area of Interest ${locations.length + 1}`,
      createdAt: new Date().toISOString(),
      geometry: geoJson,
    };

    await saveMutation.mutateAsync(newLocation);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left Sidebar - My Places */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-4">My Places</h2>
          
          {/* File Upload */}
          <div className="mb-6">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".geojson"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Upload GeoJSON
            </button>
          </div>

          {/* Locations List */}
          <div className="space-y-2">
            {paginatedLocations.map((location) => (
              <div
                key={location.id}
                className="p-3 border border-gray-200 rounded-lg hover:border-blue-500 transition-colors"
              >
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-medium text-sm">{location.name}</h3>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setSelectedLocation(location)}
                      className="p-1 text-gray-600 hover:text-blue-600"
                      title="View on map"
                    >
                      <MapIcon className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(location.id)}
                      className="p-1 text-gray-600 hover:text-red-600"
                      title="Delete location"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500">
                  {new Date(location.createdAt).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-1 mt-4">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={cn(
                    "px-2 py-1 rounded text-sm",
                    currentPage === page
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  )}
                >
                  {page}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Map */}
      <div className="flex-1 relative">
        <MapContainer
          center={[-31.4201, -64.1888]}
          zoom={12}
          className="h-full w-full"
          ref={mapRef}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              />
            </LayersControl.BaseLayer>
            <LayersControl.BaseLayer name="Satellite">
              <TileLayer
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                attribution="Esri World Imagery"
              />
            </LayersControl.BaseLayer>
          </LayersControl>

          <FeatureGroup>
            <EditControl
              position="topleft"
              onCreated={handleDrawCreated}
              draw={{
                rectangle: {
                  shapeOptions: {
                    color: '#4338ca',
                    weight: 2
                  }
                },
                polygon: {
                  shapeOptions: {
                    color: '#4338ca',
                    weight: 2
                  },
                  allowIntersection: false,
                  drawError: {
                    color: '#e11d48',
                    timeout: 1000
                  },
                  showArea: true
                },
                circle: false,
                circlemarker: false,
                marker: false,
                polyline: false
              }}
              edit={{
                featureGroup: {
                  remove: {
                    deleteText: 'Click to remove this area'
                  }
                },
                edit: {
                  selectedPathOptions: {
                    color: '#4338ca',
                    fillColor: '#4338ca',
                    fillOpacity: 0.2,
                    maintainColor: true
                  }
                }
              }}
            />
          </FeatureGroup>

          {selectedLocation && (
            <GeoJSON 
              data={selectedLocation.geometry}
              style={{
                color: '#4338ca',
                weight: 2,
                fillOpacity: 0.2
              }}
            />
          )}
        </MapContainer>

        {/* Notifications */}
        {successMessage && (
          <div className="absolute top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg">
            {successMessage}
          </div>
        )}
        {uploadError && (
          <div className="absolute top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
            {uploadError}
          </div>
        )}
      </div>
    </div>
  );
}