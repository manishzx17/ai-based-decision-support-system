import React, { useState } from 'react';
import { Navigation, MapPin, Clock, ArrowRight, Compass, ShieldAlert } from 'lucide-react';
import { DisclaimerBadge } from '../components/DisclaimerBadge';

export const NavigationPage: React.FC = () => {
  const [origin, setOrigin] = useState('Airport');
  const [destination, setDestination] = useState('Hospital');

  const navRoute = {
    distance_km: 24.5,
    travel_time_min: 35,
    traffic: "Moderate",
    waypoints: [
      "Start from Rajiv Gandhi International Airport (HYD)",
      "Merge onto Outer Ring Road (ORR) Expressway Northbound (18.0 km)",
      "Take Gachibowli / Jubilee Hills Exit towards Road No 36",
      "Turn right onto Road No 72 towards Apollo Hospitals Main Gate",
      "Arrive at destination: Apollo Hospitals Jubilee Hills Emergency Entrance"
    ]
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900">A* Spatial Graph Route Navigation</h1>
          <p className="text-xs text-slate-500 mt-1">Shortest spatial path planning between travel hubs, hotel, hospital & pharmacy</p>
        </div>

        <DisclaimerBadge type="external" text="A* Pathfinding Map Router" />
      </div>

      {/* Control Selector */}
      <div className="glass-card rounded-2xl p-4 border border-slate-200 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Starting Origin</label>
          <select
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            <option value="Airport">Rajiv Gandhi Intl Airport (HYD)</option>
            <option value="RailwayStation">Secunderabad Railway Station</option>
            <option value="Hotel">Taj Jubilee Stays</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">Destination Facility</label>
          <select
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-sky-500"
          >
            <option value="Hospital">Apollo Hospitals Jubilee Hills</option>
            <option value="Pharmacy">Apollo 24x7 Pharmacy</option>
            <option value="TraumaCenter">Yashoda Emergency Trauma Unit</option>
          </select>
        </div>
      </div>

      {/* Map Representation & Route Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Visual Simulated Map Display */}
        <div className="lg:col-span-2 glass-card rounded-3xl p-6 border border-slate-200 bg-slate-900 text-white min-h-[300px] flex flex-col justify-between relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold uppercase bg-sky-500/20 text-sky-400 px-3 py-1 rounded-full border border-sky-500/30">
              Live Map Route Simulation
            </span>
            <span className="text-xs font-bold text-slate-400">Traffic: {navRoute.traffic}</span>
          </div>

          {/* Graphical Nodes mockup */}
          <div className="my-8 flex items-center justify-between px-6 relative z-10">
            <div className="text-center">
              <div className="w-10 h-10 rounded-full bg-sky-500 text-white flex items-center justify-center font-bold mx-auto mb-1 shadow-lg">
                <MapPin className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold text-slate-200">{origin}</span>
            </div>

            <div className="flex-1 mx-4 h-1 bg-gradient-to-r from-sky-500 via-teal-400 to-indigo-500 rounded relative">
              <div className="w-3 h-3 rounded-full bg-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 shadow animate-ping"></div>
            </div>

            <div className="text-center">
              <div className="w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold mx-auto mb-1 shadow-lg">
                <Compass className="w-5 h-5" />
              </div>
              <span className="text-xs font-bold text-slate-200">{destination}</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-300 pt-3 border-t border-slate-800">
            <span><strong>Distance:</strong> {navRoute.distance_km} km</span>
            <span><strong>Est. Travel Time:</strong> ~{navRoute.travel_time_min} mins</span>
          </div>
        </div>

        {/* Turn-by-Turn Waypoints */}
        <div className="glass-card rounded-3xl p-6 border border-slate-200 space-y-3">
          <h3 className="font-extrabold text-slate-900 text-sm mb-2 flex items-center gap-2">
            <Navigation className="w-4 h-4 text-sky-600" />
            Turn-by-Turn Route Itinerary
          </h3>

          <div className="space-y-2 text-xs">
            {navRoute.waypoints.map((wp, i) => (
              <div key={i} className="p-2.5 bg-slate-50 rounded-xl border border-slate-200/80 text-slate-700 leading-relaxed flex items-start gap-2">
                <span className="font-bold text-sky-600 shrink-0">{i + 1}.</span>
                <span>{wp}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
};
