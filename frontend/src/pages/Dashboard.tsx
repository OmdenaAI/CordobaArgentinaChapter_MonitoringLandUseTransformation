import React, { useState, useEffect } from 'react';
import { MapPin, Activity, Clock, AlertTriangle, Map } from 'lucide-react';
import { Link } from 'react-router-dom';
import axiosInstance from '../config/axios';
import { MapContainer, TileLayer, Polygon } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

interface Place {
  id: number;
  name: string;
  geometry: any;
}

interface DashboardStats {
  totalPlaces: number;
  recentPlaces: number;
  activeTasks: number;
  detectedChanges: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalPlaces: 0,
    recentPlaces: 0,
    activeTasks: 0,
    detectedChanges: 0,
  });
  const [recentPlaces, setRecentPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch places for the map and stats
      const placesResponse = await axiosInstance.get('/places/');
      const places = placesResponse.data;
      
      setRecentPlaces(places.slice(0, 5)); // Get 5 most recent places
      setStats({
        totalPlaces: places.length,
        recentPlaces: places.filter((p: any) => {
          const createdAt = new Date(p.created_at);
          const oneWeekAgo = new Date();
          oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
          return createdAt > oneWeekAgo;
        }).length,
        activeTasks: 0, // You can update this when implementing the tasks feature
        detectedChanges: 0, // You can update this when implementing change detection
      });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, color }: any) => (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <Link
          to="/places"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Manage Places
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Places"
          value={stats.totalPlaces}
          icon={MapPin}
          color="bg-blue-600"
        />
        <StatCard
          title="Recent Places"
          value={stats.recentPlaces}
          icon={Clock}
          color="bg-green-600"
        />
        <StatCard
          title="Active Tasks"
          value={stats.activeTasks}
          icon={Activity}
          color="bg-yellow-600"
        />
        <StatCard
          title="Detected Changes"
          value={stats.detectedChanges}
          icon={AlertTriangle}
          color="bg-red-600"
        />
      </div>

      {/* Map and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map Overview */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Places Overview</h2>
          <div className="h-[400px]">
            <MapContainer
              center={[-31.4201, -64.1888]}
              zoom={11}
              className="h-full w-full rounded-lg"
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {recentPlaces.map((place) => (
                <Polygon
                  key={place.id}
                  positions={place.geometry.coordinates[0].map((coord: number[]) => [coord[1], coord[0]])}
                  pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.2 }}
                />
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-md p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Places</h2>
          <div className="space-y-4">
            {recentPlaces.map((place) => (
              <div
                key={place.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-gray-900">{place.name}</span>
                </div>
                <Link
                  to={`/places/${place.id}`}
                  className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  View Details
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 