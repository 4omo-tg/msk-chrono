<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import L from "leaflet";
    import "leaflet/dist/leaflet.css";

    let mapElement: HTMLElement;
    let map: L.Map;

    onMount(() => {
        // Check if mapElement exists before initializing
        if (mapElement) {
            map = L.map(mapElement).setView([55.7558, 37.6173], 13); // Moscow Center

            L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            }).addTo(map);

            // Add a test marker
            L.marker([55.7539, 37.6208])
                .addTo(map)
                .bindPopup("<b>Red Square</b><br>Historical heart of Moscow.")
                .openPopup();
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
    }
    :global(.leaflet-popup-content-wrapper) {
        background-color: #262626; /* neutral-800 */
        color: white;
    }
    :global(.leaflet-popup-tip) {
        background-color: #262626;
    }
</style>
