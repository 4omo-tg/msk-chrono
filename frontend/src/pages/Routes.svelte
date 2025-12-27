<script lang="ts">
    import { onMount } from "svelte";
    import { push } from "svelte-spa-router";
    import { User } from "lucide-svelte";

    let routes: any[] = [];
    let loading = true;
    let error = "";

    onMount(async () => {
        try {
            const response = await fetch("/api/v1/routes/");
            if (!response.ok) throw new Error("Failed to fetch routes");
            routes = await response.json();
        } catch (e) {
            error = "Could not load routes. Please try again later.";
        } finally {
            loading = false;
        }
    });
</script>

<div class="min-h-screen bg-neutral-900 text-white p-8">
    <div class="max-w-7xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1
                class="text-3xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
            >
                Walking Routes
            </h1>
            <div class="flex items-center gap-6">
                <a
                    href="#/profile"
                    class="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                >
                    <User size={18} />
                    <span>Profile</span>
                </a>
                <a
                    href="#/"
                    class="text-gray-400 hover:text-white transition-colors"
                    >Back to Home</a
                >
            </div>
        </div>

        {#if loading}
            <div class="flex justify-center p-12">
                <div
                    class="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"
                ></div>
            </div>
        {:else if error}
            <div
                class="bg-red-500/10 border border-red-500/20 p-4 rounded-lg text-red-500 text-center"
            >
                {error}
            </div>
        {:else if routes.length === 0}
            <div class="text-center text-gray-400 py-12">
                <p>No routes available yet. Check back soon!</p>
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each routes as route}
                    <div
                        class="bg-neutral-800 rounded-xl border border-white/10 overflow-hidden hover:border-amber-500/50 transition-all hover:scale-[1.02] shadow-lg"
                    >
                        <div class="p-6">
                            <div class="flex justify-between items-start mb-4">
                                <h2 class="text-xl font-bold text-white">
                                    {route.title}
                                </h2>
                                {#if route.is_premium}
                                    <span
                                        class="bg-amber-500/20 text-amber-500 text-xs px-2 py-1 rounded-full border border-amber-500/20"
                                        >Premium</span
                                    >
                                {/if}
                            </div>
                            <p class="text-gray-400 text-sm mb-4 line-clamp-3">
                                {route.description}
                            </p>

                            <div
                                class="flex items-center justify-between text-sm text-gray-500 border-t border-white/5 pt-4"
                            >
                                <span class="flex items-center">
                                    <span
                                        class="capitalize px-2 py-0.5 rounded bg-white/5 {route.difficulty ===
                                        'hard'
                                            ? 'text-red-400'
                                            : route.difficulty === 'medium'
                                              ? 'text-yellow-400'
                                              : 'text-green-400'}"
                                    >
                                        {route.difficulty}
                                    </span>
                                </span>
                                <span
                                    class="flex items-center text-amber-500 font-medium"
                                >
                                    +{route.reward_xp} XP
                                </span>
                            </div>

                            <button
                                class="w-full mt-6 bg-white/10 hover:bg-white/20 text-white font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                View Details
                            </button>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>
