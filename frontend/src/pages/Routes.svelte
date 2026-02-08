<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPost, apiDelete, isAuthenticated } from "../lib/api";
    import { onMount } from "svelte";
    import { push } from "svelte-spa-router";
    import { User, Menu, X, Map, LogOut } from "lucide-svelte";
    
    let mobileMenuOpen = false;

    let routes: any[] = [];
    let loading = true;
    let error = "";

    let progressMap: Record<number, any> = {};

    onMount(async () => {
        try {
            // 1. Fetch Routes (public endpoint)
            const response = await fetch(
                `${API_BASE}/api/v1/routes/`,
            );
            if (!response.ok) throw new Error("Failed to fetch routes");
            routes = await response.json();

            // 2. Fetch Progress (if logged in)
            if (isAuthenticated()) {
                const progressRes = await apiGet("/api/v1/progress/");
                if (progressRes.ok) {
                    const progressData = await progressRes.json();
                    progressData.forEach((p: any) => {
                        progressMap[p.route_id] = p;
                    });
                    // Trigger reactivity?
                    progressMap = { ...progressMap };
                }
            }
        } catch (e) {
            error =
                "Не удалось загрузить маршруты. Пожалуйста, попробуйте позже.";
        } finally {
            loading = false;
        }
    });
    let startingRouteId: number | null = null;

    async function startRoute(routeId: number) {
        console.log("Starting route:", routeId);
        if (!isAuthenticated()) {
            console.log("No token found, redirecting to register");
            push("/register");
            return;
        }

        startingRouteId = routeId;

        try {
            const response = await apiPost(
                "/api/v1/progress/",
                {
                    route_id: routeId,
                    status: "started",
                },
            );

            console.log("Start route response:", response.status);

            if (response.ok || response.status === 400) {
                // If it's 400, it might mean progress already exists, which is fine to redirect
                push("/dashboard");
            } else {
                const errorData = await response.json();
                console.error("Start route error:", errorData);
                alert(errorData.detail || "Не удалось начать маршрут");
            }
        } catch (e) {
            console.error("Failed to start route", e);
            alert("Ошибка при запуске маршрута");
        } finally {
            startingRouteId = null;
        }
    }

    let resettingRouteId: number | null = null;

    async function resetRoute(routeId: number) {
        if (!confirm("Сбросить прогресс маршрута? Все данные будут потеряны.")) {
            return;
        }

        if (!isAuthenticated()) return;

        const progress = progressMap[routeId];
        if (!progress) return;

        resettingRouteId = routeId;

        try {
            const response = await apiDelete(
                `/api/v1/progress/${progress.id}`
            );

            if (response.ok) {
                // Remove from local state
                delete progressMap[routeId];
                progressMap = { ...progressMap };
            } else {
                alert("Не удалось сбросить маршрут");
            }
        } catch (e) {
            console.error("Failed to reset route", e);
            alert("Ошибка при сбросе маршрута");
        } finally {
            resettingRouteId = null;
        }
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Mobile Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-14 lg:h-16">
                <h1
                    class="text-xl lg:text-3xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
                >
                    Маршруты
                </h1>
                
                <!-- Desktop Nav -->
                <div class="hidden md:flex items-center gap-6">
                    <a
                        href="#/dashboard"
                        class="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                    >
                        <Map size={18} />
                        <span class="text-sm">Карта</span>
                    </a>
                    <a
                        href="#/profile"
                        class="text-gray-400 hover:text-white transition-colors flex items-center gap-2"
                    >
                        <User size={18} />
                        <span>Профиль</span>
                    </a>
                </div>
                
                <!-- Mobile Menu Button -->
                <button
                    on:click={() => mobileMenuOpen = !mobileMenuOpen}
                    class="md:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                    {#if mobileMenuOpen}
                        <X size={24} />
                    {:else}
                        <Menu size={24} />
                    {/if}
                </button>
            </div>
            
            <!-- Mobile Menu -->
            {#if mobileMenuOpen}
                <div class="md:hidden pb-4 space-y-2">
                    <a
                        href="#/dashboard"
                        class="flex items-center gap-3 p-3 hover:bg-white/5 rounded-lg transition-colors"
                        on:click={() => mobileMenuOpen = false}
                    >
                        <Map size={20} class="text-amber-500" />
                        <span>Карта</span>
                    </a>
                    <a
                        href="#/profile"
                        class="flex items-center gap-3 p-3 hover:bg-white/5 rounded-lg transition-colors"
                        on:click={() => mobileMenuOpen = false}
                    >
                        <User size={20} class="text-amber-500" />
                        <span>Профиль</span>
                    </a>
                </div>
            {/if}
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">

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
                <p>Маршруты пока недоступны. Заходите позже!</p>
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each routes as route}
                    <div
                        class="bg-neutral-800 rounded-xl border border-white/10 overflow-hidden hover:border-amber-500/50 transition-all hover:scale-[1.02] shadow-lg flex flex-col"
                    >
                        <div class="p-6 flex-1 flex flex-col">
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
                                class="flex items-center justify-between text-sm text-gray-500 border-t border-white/5 pt-4 mt-auto"
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
                                        {route.difficulty === "easy"
                                            ? "легкий"
                                            : route.difficulty === "medium"
                                              ? "средний"
                                              : "сложный"}
                                    </span>
                                </span>
                                <span
                                    class="flex items-center text-amber-500 font-medium"
                                >
                                    +{route.reward_xp} XP
                                </span>
                            </div>

                            {#if progressMap[route.id]?.status === "completed"}
                                <button
                                    disabled
                                    class="w-full mt-6 bg-green-500/20 text-green-500 border border-green-500/20 font-bold py-3 px-4 rounded-lg cursor-default"
                                >
                                    ✓ Маршрут пройден
                                </button>
                            {:else if progressMap[route.id]?.status === "started"}
                                <div class="mt-6 space-y-2">
                                    <button
                                        on:click={() => push("/dashboard")}
                                        class="w-full bg-amber-500 hover:bg-amber-600 text-black font-bold py-3 px-4 rounded-lg transition-all transform active:scale-95 shadow-lg shadow-amber-500/10"
                                    >
                                        Продолжить ({progressMap[route.id].completed_points_count}/{route.points?.length || '?'})
                                    </button>
                                    <button
                                        on:click={() => resetRoute(route.id)}
                                        disabled={resettingRouteId === route.id}
                                        class="w-full bg-red-500/10 hover:bg-red-500/20 text-red-500 font-medium py-2 px-4 rounded-lg transition-all border border-red-500/20 text-sm"
                                    >
                                        {resettingRouteId === route.id ? "Сброс..." : "Сбросить прогресс"}
                                    </button>
                                </div>
                            {:else}
                                <button
                                    on:click={() => startRoute(route.id)}
                                    disabled={startingRouteId === route.id}
                                    class="w-full mt-6 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold py-3 px-4 rounded-lg transition-all transform active:scale-95 shadow-lg shadow-amber-500/10"
                                >
                                    {startingRouteId === route.id
                                        ? "Запуск..."
                                        : "Начать экспедицию"}
                                </button>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
</div>
