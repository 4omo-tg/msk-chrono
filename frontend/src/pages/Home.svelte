<script lang="ts">
    import { push } from "svelte-spa-router";

    let isMenuOpen = false;

    function toggleMenu() {
        isMenuOpen = !isMenuOpen;
    }
</script>

<div
    class="min-h-screen bg-neutral-900 text-white font-sans selection:bg-amber-500 selection:text-black"
>
    <!-- Navbar -->
    <nav
        class="fixed top-0 w-full z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10"
    >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex-shrink-0">
                    <span
                        class="text-2xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
                        >Moscow Chrono</span
                    >
                </div>

                <!-- Desktop Menu -->
                <div class="hidden md:block">
                    <div class="ml-10 flex items-baseline space-x-4">
                        <a
                            href="#/routes"
                            class="hover:text-amber-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                            >Routes</a
                        >
                        <a
                            href="#/login"
                            class="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-full text-sm font-medium transition-all ml-4"
                            >Login</a
                        >
                        <a
                            href="#/register"
                            class="bg-amber-500 hover:bg-amber-600 text-black px-4 py-2 rounded-full text-sm font-medium transition-all"
                            >Sign Up</a
                        >
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <main class="pt-16">
        <div class="relative overflow-hidden">
            <!-- Background Elements -->
            <div
                class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-gradient-to-b from-amber-500/10 to-transparent pointer-events-none"
            ></div>

            <div
                class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center"
            >
                <h1
                    class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6"
                >
                    <span class="block text-white">Explore History</span>
                    <span
                        class="block bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
                        >One Step at a Time</span
                    >
                </h1>
                <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-400 mb-10">
                    Discover the hidden stories of Moscow. Compare historical
                    photos with modern views, follow curated walking routes, and
                    earn rewards as you explore.
                </p>
                <div class="flex justify-center gap-4">
                    <!-- Using hash-based routing links automatically with svelte-spa-router if using proper a hrefs with # -->
                    <a
                        href="#/register"
                        class="bg-amber-500 hover:bg-amber-600 text-black font-bold py-3 px-8 rounded-full text-lg transition-transform hover:scale-105 shadow-lg shadow-amber-500/20"
                    >
                        Start Exploring
                    </a>
                    <a
                        href="#/routes"
                        class="bg-white/10 hover:bg-white/20 text-white font-bold py-3 px-8 rounded-full text-lg transition-all backdrop-blur-sm border border-white/10 inline-block"
                    >
                        View Routes
                    </a>
                </div>
            </div>
        </div>
    </main>
</div>
