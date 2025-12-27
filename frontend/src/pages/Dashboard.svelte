<script lang="ts">
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import Map from "../components/Map.svelte";
    import { User, LogOut } from "lucide-svelte";

    onMount(() => {
        if (!localStorage.getItem("token")) {
            push("/login");
        }
    });

    function logout() {
        localStorage.removeItem("token");
        push("/");
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white flex flex-col">
    <!-- Navbar -->
    <nav
        class="h-16 bg-neutral-900/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-8 z-50"
    >
        <span
            class="text-xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
            >Moscow Chrono</span
        >

        <div class="flex items-center gap-4">
            <a
                href="#/routes"
                class="hover:text-amber-400 text-sm font-medium transition-colors"
                >Routes</a
            >
            <!-- Profile Button -->
            <a
                href="#/profile"
                class="flex items-center gap-2 hover:text-amber-400 text-sm font-medium transition-colors"
            >
                <User size={18} />
                <span>Profile</span>
            </a>
            <button
                on:click={logout}
                class="flex items-center gap-2 hover:text-red-400 text-sm font-medium transition-colors ml-4"
            >
                <LogOut size={18} />
                <span>Logout</span>
            </button>
        </div>
    </nav>

    <div class="flex-1 flex overflow-hidden">
        <!-- Sidebar -->
        <div
            class="w-80 bg-neutral-800 border-r border-white/10 p-6 overflow-y-auto"
        >
            <h2 class="text-lg font-bold mb-4">Current Expedition</h2>
            <div class="bg-white/5 rounded-lg p-4 border border-white/10 mb-6">
                <p class="text-sm text-gray-400 mb-2">No active route</p>
                <a
                    href="#/routes"
                    class="text-amber-500 text-sm hover:underline"
                    >Select a route to start</a
                >
            </div>

            <h2 class="text-lg font-bold mb-4">Nearby History</h2>
            <p class="text-sm text-gray-400">
                Explore the map to find historical spots near you.
            </p>
        </div>

        <!-- Map Container -->
        <div class="flex-1 relative bg-neutral-900">
            <Map />
        </div>
    </div>
</div>
