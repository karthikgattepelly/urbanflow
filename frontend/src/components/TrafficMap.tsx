import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { RoadSegment, Incident, RouteOption, EmergencyRequest } from '../types/urbanflow';

interface TrafficMapProps {
  segments: Record<string, RoadSegment>;
  incidents: Incident[];
  activeRoutes: Record<string, RouteOption>;
  activeEmergency?: EmergencyRequest | null;
  selectedSegmentId?: string | null;
  onSelectSegment?: (segment: RoadSegment) => void;
}

export const TrafficMap: React.FC<TrafficMapProps> = ({
  segments,
  incidents,
  activeRoutes,
  activeEmergency,
  selectedSegmentId,
  onSelectSegment
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersGroupRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on downtown Metro Core
    const map = L.map(mapContainerRef.current, {
      center: [37.7850, -122.4100],
      zoom: 15,
      zoomControl: false,
      attributionControl: false
    });

    // Dark sleek tile layer
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
  maxZoom: 19,
}).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const layerGroup = L.layerGroup().addTo(map);
    layersGroupRef.current = layerGroup;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Map Layers whenever segments, incidents, or routes update
  useEffect(() => {
    if (!mapInstanceRef.current || !layersGroupRef.current) return;

    const layerGroup = layersGroupRef.current;
    layerGroup.clearLayers();

    // 1. Draw Road Segments
    Object.values(segments).forEach((seg) => {
      let color = '#3B82F6'; // Default normal blue
      let weight = 5;
      let opacity = 0.85;
      let dashArray: string | undefined = undefined;

      if (seg.status === 'blocked') {
        color = '#EF4444'; // Red
        weight = 8;
        opacity = 1.0;
      } else if (seg.status === 'priority_corridor') {
        color = '#10B981'; // Emerald priority
        weight = 8;
        opacity = 0.95;
      } else if (seg.risk_level === 'critical' || seg.risk_level === 'high') {
        color = '#F59E0B'; // Amber risk
        weight = 7;
        opacity = 0.90;
      } else if (seg.occupancy > 0.40) {
        color = '#EAB308'; // Moderate occupancy
        weight = 6;
      }

      if (selectedSegmentId === seg.id) {
        color = '#FFFFFF';
        weight = 9;
      }

      const polyline = L.polyline(seg.coordinates, {
        color,
        weight,
        opacity,
        dashArray,
        lineCap: 'round',
        lineJoin: 'round'
      });

      // Tooltip
      polyline.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px; color: #F8FAFC; background: #0F172A; padding: 6px 10px; border-radius: 6px; border: 1px solid #334155;">
          <div style="font-weight: bold; margin-bottom: 2px;">${seg.name} (${seg.id})</div>
          <div>Speed: <b style="color: #38BDF8;">${seg.current_speed} km/h</b> (Limit: ${seg.speed_limit_kmh})</div>
          <div>Occupancy: <b>${Math.round(seg.occupancy * 100)}%</b></div>
          <div>15m Risk: <b style="color: ${seg.forecast_15m_risk > 0.6 ? '#F87171' : '#34D399'};">${Math.round(seg.forecast_15m_risk * 100)}% (${seg.risk_level})</b></div>
          <div style="margin-top: 3px; font-size: 10px; text-transform: uppercase; color: ${color}; font-weight: bold;">Status: ${seg.status}</div>
        </div>
      `, { sticky: true, opacity: 0.95 });

      polyline.on('click', () => {
        if (onSelectSegment) onSelectSegment(seg);
      });

      polyline.addTo(layerGroup);
    });

    // 2. Draw Active Route Highlights (Primary, Alternative, Corridor)
    const corridorRoute = activeRoutes['emergency_corridor'];
    const primaryRoute = activeRoutes['primary'];
    const altRoute = activeRoutes['alternative'];

    if (corridorRoute && corridorRoute.coordinates.length > 0) {
      // Glow background for corridor
      L.polyline(corridorRoute.coordinates, {
        color: '#10B981',
        weight: 12,
        opacity: 0.35,
        lineCap: 'round'
      }).addTo(layerGroup);

      L.polyline(corridorRoute.coordinates, {
        color: '#34D399',
        weight: 6,
        opacity: 0.95,
        dashArray: '8, 8',
        lineCap: 'round'
      }).addTo(layerGroup);
    } else if (primaryRoute && primaryRoute.coordinates.length > 0) {
      L.polyline(primaryRoute.coordinates, {
        color: '#60A5FA',
        weight: 7,
        opacity: 0.60,
        dashArray: '6, 6',
        lineCap: 'round'
      }).addTo(layerGroup);
    }

    // 3. Draw Incidents
    incidents.forEach((inc) => {
      if (inc.status !== 'active') return;

      const incidentIcon = L.divIcon({
        className: 'custom-incident-marker',
        html: `
          <div style="position: relative; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; width: 30px; height: 30px; border-radius: 50%; background: rgba(239, 68, 68, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="position: relative; width: 26px; height: 26px; border-radius: 50%; background: #EF4444; border: 2px solid #FFFFFF; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
              <span style="color: white; font-size: 13px; font-weight: bold;">⚠</span>
            </div>
          </div>
        `,
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });

      const marker = L.marker(inc.coordinates, { icon: incidentIcon });
      marker.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px; color: #F8FAFC; background: #0F172A; padding: 6px 10px; border-radius: 6px; border: 1px solid #EF4444;">
          <div style="font-weight: bold; color: #F87171; text-transform: uppercase;">${inc.type.replace('_', ' ')} (${inc.id})</div>
          <div>Location: <b>${inc.location_name}</b></div>
          <div>Multi-Sensor Confidence: <b>${Math.round(inc.confidence * 100)}%</b></div>
          <div>Severity: <b style="color: #EF4444; text-transform: uppercase;">${inc.severity}</b></div>
        </div>
      `, { sticky: true, opacity: 0.95 });

      marker.addTo(layerGroup);
    });

    // 4. Draw Emergency Vehicle
    if (activeEmergency && activeEmergency.status === 'active') {
      // Find starting point (origin of corridor or first segment)
      const corridor = activeRoutes['emergency_corridor'];
      const vehiclePos = corridor && corridor.coordinates.length > 0 
        ? corridor.coordinates[0] 
        : [37.7812, -122.4210]; // West Gate default

      const ambulanceIcon = L.divIcon({
        className: 'custom-ambulance-marker',
        html: `
          <div style="position: relative; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;">
            <div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: rgba(16, 185, 129, 0.4); animation: ping 1.2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            <div style="position: relative; width: 30px; height: 30px; border-radius: 8px; background: #10B981; border: 2px solid #FFFFFF; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5);">
              <span style="color: white; font-size: 14px; font-weight: bold;">🚑</span>
            </div>
          </div>
        `,
        iconSize: [38, 38],
        iconAnchor: [19, 19]
      });

      const ambMarker = L.marker(vehiclePos as [number, number], { icon: ambulanceIcon });
      ambMarker.bindTooltip(`
        <div style="font-family: sans-serif; font-size: 11px; color: #F8FAFC; background: #0F172A; padding: 6px 10px; border-radius: 6px; border: 1px solid #10B981;">
          <div style="font-weight: bold; color: #34D399; text-transform: uppercase;">EMERGENCY UNIT: ${activeEmergency.vehicle_id}</div>
          <div>Priority: <b>${activeEmergency.priority.toUpperCase()}</b></div>
          <div>Target ETA: <b>${Math.round(activeEmergency.current_eta_seconds / 60)} mins</b></div>
        </div>
      `, { sticky: true, opacity: 0.95 });

      ambMarker.addTo(layerGroup);
    }
  }, [segments, incidents, activeRoutes, activeEmergency, selectedSegmentId]);

  return (
    <div className="relative w-full h-full bg-[#0B1120] rounded-xl overflow-hidden border border-slate-800 shadow-inner">
      <div ref={mapContainerRef} className="w-full h-full" />
      
      {/* Map Legend Overlay */}
      <div className="absolute top-4 left-4 z-[400] bg-slate-900/90 backdrop-blur-md border border-slate-800/90 rounded-lg p-3 text-xs shadow-xl">
        <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-2 font-semibold">Corridor Status</div>
        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1.5 bg-blue-500 rounded-sm"></span>
            <span className="text-slate-300">Free-Flow (Speed &gt;45 km/h)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1.5 bg-amber-500 rounded-sm"></span>
            <span className="text-slate-300">15m Risk Spike / Surge</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1.5 bg-red-500 rounded-sm"></span>
            <span className="text-slate-300">Blocked / Collision</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3.5 h-1.5 bg-emerald-500 rounded-sm shadow-sm shadow-emerald-500"></span>
            <span className="text-emerald-300 font-semibold">Priority Corridor (Pre-empted)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

