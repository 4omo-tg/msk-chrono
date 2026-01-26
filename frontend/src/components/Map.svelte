<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { onMount, onDestroy, createEventDispatcher } from "svelte";
    import L from "leaflet";
    import "leaflet/dist/leaflet.css";

    const dispatch = createEventDispatcher();
    let mapElement: HTMLElement;
    let map: L.Map;
    let pois: any[] = [];

    export let activeRouteProgress: any = null;
    let markersLayer: L.LayerGroup;
    let linesLayer: L.LayerGroup;

    async function fetchPOIs() {
        const token = localStorage.getItem("token");
        if (!token || !activeRouteProgress) return [];

        try {
            // Optimization: could just fetch specific route if endpoint exists, but strictly using available ones
            const response = await fetch(
                `${API_BASE}/api/v1/routes/`,
            );
            if (response.ok) {
                const routes = await response.json();
                const activeRoute = routes.find(
                    (r: any) => r.id === activeRouteProgress.route_id,
                );

                if (activeRoute && activeRoute.points) {
                    return activeRoute.points.map((p: any) => ({
                        ...p,
                        routeId: activeRoute.id,
                    }));
                }
            }
        } catch (e) {
            console.error("Failed to fetch POIs", e);
        }
        return [];
    }

    // Watch for changes in activeRouteProgress to re-render
    $: if (map && activeRouteProgress) {
        updateMap();
    } else if (map && !activeRouteProgress) {
        // Clear map if no active route
        if (markersLayer) markersLayer.clearLayers();
        if (linesLayer) linesLayer.clearLayers();
    }

    async function updateMap() {
        pois = await fetchPOIs();
        if (!markersLayer) markersLayer = L.layerGroup().addTo(map);
        if (!linesLayer) linesLayer = L.layerGroup().addTo(map);

        markersLayer.clearLayers();
        linesLayer.clearLayers();

        const completedCount = activeRouteProgress?.completed_points_count || 0;

        const blueIcon = new L.Icon({
            iconUrl:
                "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
            shadowUrl:
                "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
        });

        const redIcon = new L.Icon({
            iconUrl:
                "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
            shadowUrl:
                "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
        });

        const greenIcon = new L.Icon({
            iconUrl:
                "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
            shadowUrl:
                "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41],
        });

        pois.forEach((poi, index) => {
            // Show only previously completed points AND the current target point
            if (index > completedCount) return;

            let icon;
            if (index < completedCount) {
                icon = greenIcon; // Visited
            } else {
                icon = blueIcon; // Current target (start point or next point)
            }

            const marker = L.marker([poi.latitude, poi.longitude], {
                icon: icon,
            })
                .addTo(markersLayer)
                .bindPopup(`<b>${poi.title}</b>`);

            marker.on("click", () => {
                dispatch("selectPOI", {
                    ...poi,
                    index: index,
                    isVisited: index < completedCount,
                    isCurrent: index === completedCount,
                });
            });
        });

        // Draw lines
        // A segment connects point i and i+1
        // We show segment i -> i+1 IF i+1 is <= completedCount
        for (let i = 0; i < pois.length - 1; i++) {
            if (i + 1 > completedCount) break;

            const p1 = pois[i];
            const p2 = pois[i + 1];
            const latlngs = [
                [p1.latitude, p1.longitude],
                [p2.latitude, p2.longitude],
            ];

            let color = "#ef4444"; // red default (current path)

            // If the destination of this segment (i+1) is visited (index < completedCount), then the line is "passed" -> Green
            // If i+1 is the current target (index === completedCount), then the line is leading to it -> Red
            if (i + 1 < completedCount) {
                color = "#22c55e"; // green-500
            }

            L.polyline(latlngs as L.LatLngExpression[], {
                color: color,
                weight: 6,
                opacity: 0.8,
                lineJoin: "round",
            }).addTo(linesLayer);
        }
    }

    onMount(async () => {
        if (mapElement) {
            // Fix for Leaflet default icon paths in Vite
            delete (L.Icon.Default.prototype as any)._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconRetinaUrl:
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
                iconUrl:
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
                shadowUrl:
                    "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
            });

            map = L.map(mapElement).setView([55.7558, 37.6173], 15); // Slightly more zoomed in

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            }).addTo(map);

            if (activeRouteProgress) {
                updateMap();
            }
        }
    });

    onDestroy(() => {
        if (map) {
            map.remove();
        }
    });
</script>

<div
    class="w-full h-full rounded-xl overflow-hidden shadow-lg border border-white/10"
    bind:this={mapElement}
></div>

<style>
    :global(.leaflet-container) {
        background: #171717; /* neutral-900 */
        font-family: inherit;
        z-index: 10; /* Ensure map is below navbar */
    }
    :global(.leaflet-popup-content-wrapper) {
        background-color: #262626; /* neutral-800 */
        color: white;
    }
    :global(.leaflet-popup-tip) {
        background-color: #262626;
    }
</style>
