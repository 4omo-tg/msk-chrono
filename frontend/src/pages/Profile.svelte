<script lang="ts">
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import { User } from "lucide-svelte";

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

<div class="min-h-screen bg-neutral-900 text-white p-8">
    <div class="max-w-2xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1
                class="text-3xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
            >
                User Profile
            </h1>
            <a
                href="#/dashboard"
                class="text-gray-400 hover:text-white transition-colors"
                >Back to Dashboard</a
            >
        </div>

        <div
            class="bg-neutral-800 rounded-xl border border-white/10 p-8 shadow-lg"
        >
            <div class="flex items-center gap-6 mb-8">
                <div
                    class="w-20 h-20 bg-neutral-700 rounded-full flex items-center justify-center text-amber-500"
                >
                    <User size={40} />
                </div>
                <div>
                    <h2 class="text-2xl font-bold text-white">Explorer</h2>
                    <p class="text-gray-400">Level 1 • 0 XP</p>
                </div>
            </div>

            <div class="space-y-6">
                <div>
                    <h3 class="text-lg font-medium text-white mb-2">
                        Statistics
                    </h3>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-neutral-900 p-4 rounded-lg">
                            <div class="text-2xl font-bold text-amber-500">
                                0
                            </div>
                            <div class="text-sm text-gray-500">
                                Routes Completed
                            </div>
                        </div>
                        <div class="bg-neutral-900 p-4 rounded-lg">
                            <div class="text-2xl font-bold text-amber-500">
                                0 km
                            </div>
                            <div class="text-sm text-gray-500">
                                Distance Walked
                            </div>
                        </div>
                    </div>
                </div>

                <div class="pt-6 border-t border-white/10">
                    <button
                        on:click={logout}
                        class="w-full bg-red-500/10 hover:bg-red-500/20 text-red-500 font-medium py-3 rounded-lg transition-colors border border-red-500/20"
                    >
                        Sign Out
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
