import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Car, Bike, Footprints, Navigation, MapPin, Clock,
  Compass, ExternalLink, AlertCircle, ArrowRightLeft,
  CheckCircle2, Loader2, Sparkles, Building2, Hotel,
  Pill, PhoneCall, ShieldAlert, HeartPulse, Siren,
  Route, ChevronRight, Search
} from 'lucide-react';
import L from 'leaflet';
import {
  calculateMedicalRoute,
  getNearbyPOIs,
  getEmergencyServices,
  OpenRouteResponse,
  NearbyPOI,
  EmergencyServicesResponse,
  getHospitalById
} from '../services/api';

type TravelMode = 'car' | 'two_wheeler' | 'walking' | 'bicycle' | 'transit';
type ActiveTab = 'route' | 'hotels' | 'pharmacies' | 'emergency';

interface ModeOption {
  id: TravelMode;
  label: string;
  icon: React.FC<{ className?: string }>;
  description: string;
}

const TRAVEL_MODES: ModeOption[] = [
  { id: 'car', label: 'Car / Ambulance', icon: Car, description: 'Direct road route for personal or patient transfer' },
  { id: 'two_wheeler', label: 'Two-Wheeler', icon: Bike, description: 'Agile city transit / motorbike' },
  { id: 'bicycle', label: 'Bicycle', icon: Bike, description: 'Cycle-friendly designated lanes & paths' },
  { id: 'walking', label: 'Walking', icon: Footprints, description: 'Pedestrian footpaths and sidewalks' },
  { id: 'transit', label: 'Transit Est.', icon: Navigation, description: 'Road-network estimate for shared/transit travel (OSRM driving profile, adjusted speed factor — not live bus/rail schedules)' },
];

export const MedicalTravelPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const hospitalIdParam = searchParams.get('hospital_id');
  const destQueryParam = searchParams.get('destination');

  const [activeTab, setActiveTab] = useState<ActiveTab>('route');

  // Route State
  const [origin, setOrigin] = useState<string>('MG Road, Bangalore');
  const [destination, setDestination] = useState<string>('Apollo Hospital, Bannerghatta Road, Bangalore');
  const [travelMode, setTravelMode] = useState<TravelMode>('car');
  const [hospitalInfo, setHospitalInfo] = useState<{ id: number; name: string; city: string; address?: string } | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [routeResult, setRouteResult] = useState<OpenRouteResponse | null>(null);

  // POI Search States
  const [poiAnchor, setPoiAnchor] = useState<string>('Apollo Hospital, Bannerghatta Road, Bangalore');
  const [hotels, setHotels] = useState<NearbyPOI[]>([]);
  const [pharmacies, setPharmacies] = useState<NearbyPOI[]>([]);
  const [loadingPois, setLoadingPois] = useState<boolean>(false);
  const [poiError, setPoiError] = useState<string | null>(null);

  // Emergency Services State
  const [emergencyData, setEmergencyData] = useState<EmergencyServicesResponse | null>(null);
  const [loadingEmergency, setLoadingEmergency] = useState<boolean>(false);

  // Map container refs
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const routeLayerGroupRef = useRef<L.LayerGroup | null>(null);

  // Load hospital context if provided in query params
  useEffect(() => {
    if (hospitalIdParam) {
      getHospitalById(hospitalIdParam)
        .then((h) => {
          if (h) {
            setHospitalInfo({ id: h.id, name: h.name, city: h.city, address: h.address });
            const destStr = h.address ? `${h.name}, ${h.address}` : `${h.name}, ${h.city}`;
            setDestination(destStr);
            setPoiAnchor(destStr);
          }
        })
        .catch((e) => {
          console.warn('Could not fetch hospital for destination prefill:', e);
        });
    } else if (destQueryParam) {
      setDestination(destQueryParam);
      setPoiAnchor(destQueryParam);
    }
  }, [hospitalIdParam, destQueryParam]);

  // Synchronize POI anchor when destination changes
  useEffect(() => {
    if (destination) {
      setPoiAnchor(destination);
    }
  }, [destination]);

  // Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [12.9716, 77.5946],
        zoom: 12,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      routeLayerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        routeLayerGroupRef.current = null;
      }
    };
  }, []);

  // Update map polyline and markers when routeResult updates
  useEffect(() => {
    if (!mapInstanceRef.current || !routeLayerGroupRef.current || !routeResult) return;

    const layerGroup = routeLayerGroupRef.current;
    layerGroup.clearLayers();

    const oLat = routeResult.origin.lat;
    const oLon = routeResult.origin.lon;
    const dLat = routeResult.destination.lat;
    const dLon = routeResult.destination.lon;

    const originIcon = L.divIcon({
      className: 'custom-div-icon',
      html: `<div style="background-color:#10b981; width:28px; height:28px; border-radius:50%; border:3px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; color:white; font-size:12px; font-weight:bold;">A</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    const destIcon = L.divIcon({
      className: 'custom-div-icon',
      html: `<div style="background-color:#0284c7; width:28px; height:28px; border-radius:50%; border:3px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; color:white; font-size:12px; font-weight:bold;">H</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    const oMarker = L.marker([oLat, oLon], { icon: originIcon }).bindPopup(
      `<strong>Origin:</strong><br/>${routeResult.origin.name}`
    );
    const dMarker = L.marker([dLat, dLon], { icon: destIcon }).bindPopup(
      `<strong>Destination:</strong><br/>${routeResult.destination.name}`
    );

    layerGroup.addLayer(oMarker);
    layerGroup.addLayer(dMarker);

    if (routeResult.route_geometry && routeResult.route_geometry.length > 0) {
      const polyline = L.polyline(routeResult.route_geometry, {
        color: '#0284c7',
        weight: 5,
        opacity: 0.85,
        lineJoin: 'round',
      });
      layerGroup.addLayer(polyline);

      mapInstanceRef.current.fitBounds(polyline.getBounds(), {
        padding: [40, 40],
      });
    } else {
      mapInstanceRef.current.fitBounds(
        L.latLngBounds([
          [oLat, oLon],
          [dLat, dLon],
        ]),
        { padding: [50, 50] }
      );
    }
  }, [routeResult]);

  // Handler for route calculation
  const handleCalculateRoute = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!origin.trim()) {
      setError('Please provide a starting origin address.');
      return;
    }
    if (!destination.trim()) {
      setError('Please provide a destination hospital or address.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const res = await calculateMedicalRoute({
        origin: origin.trim(),
        destination: destination.trim(),
        travel_mode: travelMode,
      });
      setRouteResult(res);
      setActiveTab('route');
    } catch (err: any) {
      console.error('Route calculation failed:', err);
      setError(err?.message || 'Could not calculate route. Please verify addresses and try again.');
    } finally {
      setLoading(false);
    }
  };

  // Search Nearby POIs (Hotels or Pharmacies)
  const handleFetchPOIs = async (category: 'hotel' | 'pharmacy') => {
    if (!poiAnchor.trim()) {
      setPoiError('Please enter a location or hospital to search around.');
      return;
    }

    setPoiError(null);
    setLoadingPois(true);

    try {
      const res = await getNearbyPOIs(poiAnchor.trim(), category, 6);
      if (category === 'hotel') {
        setHotels(res.items);
      } else {
        setPharmacies(res.items);
      }

      // If map is loaded and items found, add markers to Leaflet map
      if (mapInstanceRef.current && routeLayerGroupRef.current && res.items.length > 0) {
        const group = routeLayerGroupRef.current;
        group.clearLayers();

        const bounds: [number, number][] = [];

        res.items.forEach((item, idx) => {
          bounds.push([item.lat, item.lon]);
          const pinBg = category === 'hotel' ? '#f59e0b' : '#10b981';
          const pinLetter = category === 'hotel' ? 'H' : 'P';

          const icon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color:${pinBg}; width:26px; height:26px; border-radius:50%; border:2px solid white; box-shadow:0 2px 5px rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; color:white; font-size:11px; font-weight:bold;">${pinLetter}${idx + 1}</div>`,
            iconSize: [26, 26],
            iconAnchor: [13, 13],
          });

          const marker = L.marker([item.lat, item.lon], { icon }).bindPopup(
            `<strong>${item.name}</strong><br/>${item.address}<br/>${item.distance_km ? `Distance: ${item.distance_km} km` : ''}`
          );
          group.addLayer(marker);
        });

        if (bounds.length > 0) {
          mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
      }
    } catch (err: any) {
      console.error(`Failed to fetch ${category}:`, err);
      setPoiError(err?.message || `Could not find nearby ${category}s. Try refining location.`);
    } finally {
      setLoadingPois(false);
    }
  };

  // Fetch Emergency Services Data
  const handleLoadEmergencyServices = async () => {
    setLoadingEmergency(true);
    try {
      const cityQuery = hospitalInfo?.city || (destination.includes('Bangalore') ? 'Bangalore' : undefined);
      const res = await getEmergencyServices(cityQuery, hospitalInfo?.id);
      setEmergencyData(res);
    } catch (err: any) {
      console.error('Failed to load emergency services:', err);
    } finally {
      setLoadingEmergency(false);
    }
  };

  // Auto-fetch data when tab switches
  useEffect(() => {
    if (activeTab === 'hotels' && hotels.length === 0) {
      handleFetchPOIs('hotel');
    } else if (activeTab === 'pharmacies' && pharmacies.length === 0) {
      handleFetchPOIs('pharmacy');
    } else if (activeTab === 'emergency' && !emergencyData) {
      handleLoadEmergencyServices();
    }
  }, [activeTab]);

  // Route action from POI or Emergency to destination
  const handleRouteToPOI = (poiAddress: string) => {
    setDestination(poiAddress);
    setActiveTab('route');
    // Calculate route from current origin
    setTimeout(() => {
      handleCalculateRoute();
    }, 100);
  };

  const handleRouteFromPOI = (poiAddress: string) => {
    setOrigin(poiAddress);
    setActiveTab('route');
    setTimeout(() => {
      handleCalculateRoute();
    }, 100);
  };

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-md bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300">
              Open Navigation
            </span>
            <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              100% Free / Zero Paid APIs
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Medical Travel System
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            Comprehensive patient transit support: Street routing, nearby hotels, pharmacies, and emergency dispatch.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/hospitals"
            className="flex items-center gap-1.5 text-xs font-bold text-slate-700 dark:text-slate-300 hover:text-sky-600 bg-white dark:bg-slate-800 px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm"
          >
            <Building2 className="w-3.5 h-3.5 text-sky-600" />
            <span>Select Recommended Hospital</span>
          </Link>
        </div>
      </div>

      {/* Hospital Pre-fill Banner */}
      {hospitalInfo && (
        <div className="bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800 rounded-xl p-3 flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-sky-800 dark:text-sky-300">
            <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
            <span>
              Destination linked with recommended facility: <strong>{hospitalInfo.name}</strong> ({hospitalInfo.city})
            </span>
          </div>
          <button
            onClick={() => setHospitalInfo(null)}
            className="text-[11px] text-sky-600 hover:underline font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('route')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'route'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Route className="w-4 h-4" />
          <span>Route Planner</span>
        </button>

        <button
          onClick={() => setActiveTab('hotels')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'hotels'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Hotel className="w-4 h-4" />
          <span>Nearby Hotels</span>
        </button>

        <button
          onClick={() => setActiveTab('pharmacies')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'pharmacies'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Pill className="w-4 h-4" />
          <span>Nearby Pharmacies</span>
        </button>

        <button
          onClick={() => setActiveTab('emergency')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === 'emergency'
              ? 'bg-rose-600 text-white shadow-sm'
              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
        >
          <Siren className="w-4 h-4" />
          <span>Emergency Services</span>
        </button>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Side: Active Tab Controls & Information */}
        <div className="lg:col-span-6 space-y-5">
          
          {/* TAB 1: ROUTE PLANNER */}
          {activeTab === 'route' && (
            <div className="glass-card rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Compass className="w-4 h-4 text-sky-600" />
                Dynamic Route Settings
              </h2>

              <form onSubmit={handleCalculateRoute} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
                    Origin Address / Location
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={origin}
                      onChange={(e) => setOrigin(e.target.value)}
                      placeholder="Enter city, landmark, or street address"
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
                    />
                    <MapPin className="w-4 h-4 text-slate-400 absolute right-3 top-2.5 pointer-events-none" />
                  </div>
                </div>

                <div className="flex justify-center -my-1">
                  <button
                    type="button"
                    onClick={handleSwap}
                    className="p-1.5 rounded-full bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 transition-colors"
                    title="Swap Origin and Destination"
                  >
                    <ArrowRightLeft className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-sky-600 inline-block"></span>
                    Destination Hospital / Location
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="Enter destination hospital, landmark, or address"
                      className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
                    />
                    <Building2 className="w-4 h-4 text-slate-400 absolute right-3 top-2.5 pointer-events-none" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Travel Mode
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {TRAVEL_MODES.map((mode) => {
                      const Icon = mode.icon;
                      const isSelected = travelMode === mode.id;
                      return (
                        <button
                          key={mode.id}
                          type="button"
                          onClick={() => setTravelMode(mode.id)}
                          className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-center transition-all ${
                            isSelected
                              ? 'bg-sky-50 dark:bg-sky-950/60 border-sky-600 text-sky-700 dark:text-sky-300 shadow-sm'
                              : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          <Icon className={`w-4 h-4 mb-1 ${isSelected ? 'text-sky-600' : 'text-slate-500'}`} />
                          <span className="text-[11px] font-bold leading-tight">{mode.label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-2 flex items-center justify-center gap-2 font-bold text-xs text-white gradient-bg py-3 px-4 rounded-xl shadow hover:opacity-95 transition-opacity disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Calculating Open Route...</span>
                    </>
                  ) : (
                    <>
                      <Navigation className="w-4 h-4" />
                      <span>Calculate Route</span>
                    </>
                  )}
                </button>
              </form>

              {error && (
                <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {routeResult && (
                <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-extrabold text-sm text-slate-900 dark:text-white flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Route Metric Summary
                    </h3>
                    <span className="text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded">
                      {routeResult.routing_service}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-700">
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium flex items-center gap-1">
                        <Navigation className="w-3.5 h-3.5 text-sky-600" />
                        Total Distance
                      </span>
                      <p className="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
                        {routeResult.distance_km} <span className="text-xs font-semibold text-slate-500">km</span>
                      </p>
                    </div>

                    <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-700">
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-sky-600" />
                        Estimated Duration
                      </span>
                      <p className="text-xl font-extrabold text-slate-900 dark:text-white mt-1">
                        {routeResult.duration_text}
                      </p>
                    </div>
                  </div>

                  <a
                    href={routeResult.open_map_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-1.5 text-xs font-bold text-sky-700 dark:text-sky-300 hover:text-sky-800 bg-sky-50 dark:bg-sky-950/60 py-2.5 px-3 rounded-xl border border-sky-200 dark:border-sky-800 transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Open in OpenStreetMap Directions</span>
                  </a>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: NEARBY HOTELS */}
          {activeTab === 'hotels' && (
            <div className="glass-card rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Hotel className="w-4 h-4 text-amber-500" />
                  Nearby Patient Accommodations &amp; Hotels
                </h2>
                <span className="text-[10px] text-slate-500 font-medium">OSM Nominatim</span>
              </div>

              {/* Anchor Search Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={poiAnchor}
                  onChange={(e) => setPoiAnchor(e.target.value)}
                  placeholder="Enter hospital or destination area"
                  className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => handleFetchPOIs('hotel')}
                  disabled={loadingPois}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-xs transition-colors disabled:opacity-50"
                >
                  {loadingPois ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  <span>Search</span>
                </button>
              </div>

              {poiError && (
                <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-xs">{poiError}</div>
              )}

              {/* Hotels List */}
              <div className="space-y-3">
                {hotels.map((hotel, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <h4 className="font-bold text-xs text-slate-900 dark:text-white">{hotel.name}</h4>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                        {hotel.address}
                      </p>
                      {hotel.distance_km !== undefined && hotel.distance_km !== null && (
                        <span className="inline-block mt-1 text-[10px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">
                          ~{hotel.distance_km} km from destination
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleRouteFromPOI(hotel.address)}
                        className="text-[11px] font-bold text-sky-700 dark:text-sky-300 bg-sky-50 dark:bg-sky-950 px-3 py-1.5 rounded-lg border border-sky-200 dark:border-sky-800 hover:bg-sky-100 transition-colors"
                      >
                        Route to Hospital
                      </button>
                      <a
                        href={hotel.open_map_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 text-slate-500 hover:text-sky-600 transition-colors"
                        title="Open in OpenStreetMap"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: NEARBY PHARMACIES */}
          {activeTab === 'pharmacies' && (
            <div className="glass-card rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Pill className="w-4 h-4 text-emerald-600" />
                  Nearby Pharmacies &amp; Medical Stores
                </h2>
                <span className="text-[10px] text-slate-500 font-medium">OSM Nominatim</span>
              </div>

              {/* Anchor Search Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={poiAnchor}
                  onChange={(e) => setPoiAnchor(e.target.value)}
                  placeholder="Enter hospital or destination area"
                  className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-sky-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => handleFetchPOIs('pharmacy')}
                  disabled={loadingPois}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors disabled:opacity-50"
                >
                  {loadingPois ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  <span>Search</span>
                </button>
              </div>

              {poiError && (
                <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-xs">{poiError}</div>
              )}

              {/* Pharmacy List */}
              <div className="space-y-3">
                {pharmacies.map((pharmacy, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <h4 className="font-bold text-xs text-slate-900 dark:text-white">{pharmacy.name}</h4>
                      </div>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                        {pharmacy.address}
                      </p>
                      {pharmacy.distance_km !== undefined && pharmacy.distance_km !== null && (
                        <span className="inline-block mt-1 text-[10px] font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded">
                          ~{pharmacy.distance_km} km from destination
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => handleRouteToPOI(pharmacy.address)}
                        className="text-[11px] font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950 px-3 py-1.5 rounded-lg border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100 transition-colors"
                      >
                        Get Directions
                      </button>
                      <a
                        href={pharmacy.open_map_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 text-slate-500 hover:text-sky-600 transition-colors"
                        title="Open in OpenStreetMap"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: EMERGENCY SERVICES */}
          {activeTab === 'emergency' && (
            <div className="glass-card rounded-2xl p-6 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
                <div>
                  <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Siren className="w-4 h-4 text-rose-600" />
                    Emergency Dispatch &amp; Trauma Support
                  </h2>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Location: {emergencyData?.city || 'Regional'}, {emergencyData?.state || 'India'}
                  </p>
                </div>
                <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-rose-100 text-rose-800">
                  24x7 Critical Line
                </span>
              </div>

              {/* National & State Emergency Quick Dial Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold text-rose-700 dark:text-rose-300">National Emergency</span>
                  <p className="text-2xl font-black text-rose-600 mt-1">112</p>
                </div>

                <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold text-emerald-700 dark:text-emerald-300">Ambulance</span>
                  <p className="text-2xl font-black text-emerald-600 mt-1">{emergencyData?.ambulance_number || '108'}</p>
                </div>

                <div className="p-3 bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-900 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold text-sky-700 dark:text-sky-300">Police</span>
                  <p className="text-xl font-black text-sky-600 mt-1">{emergencyData?.police_number || '100'}</p>
                </div>

                <div className="p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 rounded-xl text-center">
                  <span className="text-[10px] uppercase font-bold text-amber-700 dark:text-amber-300">Fire &amp; Rescue</span>
                  <p className="text-2xl font-black text-amber-600 mt-1">{emergencyData?.fire_number || '101'}</p>
                </div>
              </div>

              {/* Nearest/Recommended Hospital Emergency Department */}
              {emergencyData?.hospital_emergency_dept && (
                <div className="p-4 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <HeartPulse className="w-4 h-4 text-rose-600" />
                      {emergencyData.hospital_emergency_dept.hospital_name}
                    </span>
                    {emergencyData.hospital_emergency_dept.emergency_24x7 && (
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        24×7 Emergency Dept (Reference)
                      </span>
                    )}
                  </div>

                  <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                    <p><strong>Address:</strong> {emergencyData.hospital_emergency_dept.address}</p>
                    <p><strong>Emergency Desk:</strong> {emergencyData.hospital_emergency_dept.emergency_phone}</p>
                    <p><strong>ICU Capacity:</strong> {emergencyData.hospital_emergency_dept.icu_beds} Intensive Care Beds</p>
                  </div>

                  <div className="pt-2 flex items-center gap-2">
                    <button
                      onClick={() => handleRouteToPOI(emergencyData.hospital_emergency_dept!.address)}
                      className="flex items-center gap-1.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 px-3.5 py-1.5 rounded-lg transition-colors"
                    >
                      <Navigation className="w-3.5 h-3.5" />
                      <span>Route to Emergency Room</span>
                    </button>
                  </div>
                </div>
              )}

              {/* Complete Emergency Helpline Directory */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Emergency Services Directory</h4>
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {emergencyData?.contacts.map((contact, i) => (
                    <div key={i} className="py-2 flex items-center justify-between text-xs">
                      <div>
                        <p className="font-semibold text-slate-800 dark:text-slate-200">{contact.service_name}</p>
                        <p className="text-[10px] text-slate-500">{contact.description}</p>
                      </div>
                      <span className="font-mono font-bold text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-700 px-2.5 py-1 rounded">
                        {contact.number}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl text-[11px] text-rose-800 dark:text-rose-300">
                <strong>Disclaimer:</strong> {emergencyData?.disclaimer || 'In any life-threatening situation, dial 112 or 108 immediately.'}
              </div>
            </div>
          )}

        </div>

        {/* Right Side: Embedded Leaflet Map */}
        <div className="lg:col-span-6">
          <div className="glass-card rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-3 px-1">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-sky-600" />
                <h3 className="font-extrabold text-sm text-slate-900 dark:text-white">
                  Interactive OpenStreetMap
                </h3>
              </div>
              <span className="text-[10px] text-slate-500 font-medium">
                Leaflet.js / OSRM
              </span>
            </div>

            {/* Map Container */}
            <div
              ref={mapContainerRef}
              className="w-full h-[540px] rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 z-10"
              style={{ minHeight: '520px' }}
            />

            {/* Map Bottom Legend */}
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 dark:text-slate-400 px-1 pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span>
                  <span className="text-[11px] font-semibold">Origin / Pharmacy</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-sky-600 inline-block"></span>
                  <span className="text-[11px] font-semibold">Hospital</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span>
                  <span className="text-[11px] font-semibold">Hotels</span>
                </div>
              </div>
              <span className="text-[10px] text-slate-400">
                © OpenStreetMap contributors
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default MedicalTravelPage;
