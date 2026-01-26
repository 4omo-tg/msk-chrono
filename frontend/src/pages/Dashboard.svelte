<script lang="ts">
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import Map from "../components/Map.svelte";
    import QuizModal from "../components/QuizModal.svelte";
    import VerificationModal from "../components/VerificationModal.svelte";
    import OnboardingModal from "../components/OnboardingModal.svelte";
    import {
        User,
        LogOut,
        Info,
        Clock,
        Camera,
        Map as MapIcon,
        HelpCircle,
    } from "lucide-svelte";

    let selectedPOI: any = null;
    let userXP: number = 0;
    let userLevel: number = 1;
    let activeRouteProgress: any = null;
    let showReward: boolean = false;
    let lastReward: number = 0;
    let loading = true;
    let totalPoints = 0;
    let allRoutes: any[] = [];

    // Quiz state
    let showQuiz: boolean = false;
    let currentQuizzes: any[] = [];
    let currentQuizIndex: number = 0;

    // Verification state
    let showVerificationModal: boolean = false;

    // Onboarding state
    let showOnboarding: boolean = false;

    onMount(async () => {
        const token = localStorage.getItem("token");
        if (!token) {
            push("/login");
            return;
        }

        // Check if onboarding was completed
        const onboardingCompleted = localStorage.getItem("onboarding_completed");
        if (!onboardingCompleted) {
            showOnboarding = true;
        }

        try {
            // Fetch current user data
            const userRes = await fetch(
                "http://localhost:8000/api/v1/users/me/",
                {
                    headers: { Authorization: `Bearer ${token}` },
                },
            );
            if (userRes.ok) {
                const userData = await userRes.json();
                userXP = userData.xp;
            }

            // Fetch progress to find ANY active route
            const progRes = await fetch(
                "http://localhost:8000/api/v1/progress/",
                {
                    headers: { Authorization: `Bearer ${token}` },
                },
            );
            if (progRes.ok) {
                const progressArr = await progRes.json();
                // Find the first route that is 'started'
                activeRouteProgress = progressArr.find(
                    (p: any) => p.status === "started",
                );

                // Fetch all routes for reactive totalPoints calculation
                const routesRes = await fetch(
                    "http://localhost:8000/api/v1/routes/",
                );
                if (routesRes.ok) {
                    allRoutes = await routesRes.json();
                }
            }
        } catch (e) {
            console.error("Failed to fetch initial data", e);
        } finally {
            loading = false;
        }
    });

    let routeCompleted = false;

    async function checkIn() {
        if (!selectedPOI || !activeRouteProgress) return;

        const token = localStorage.getItem("token");
        try {
            const response = await fetch(
                "http://localhost:8000/api/v1/progress/check-in",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        poi_id: selectedPOI.id,
                        route_id: activeRouteProgress.route_id,
                    }),
                },
            );

            if (response.ok) {
                const result = await response.json();
                userXP = result.new_total_xp;
                userLevel = result.new_level;
                lastReward = result.xp_gained;
                showReward = true;

                // Force reload of progress to ensure consistency
                const progressResponse = await fetch(
                    "http://localhost:8000/api/v1/progress/current",
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    },
                );

                if (progressResponse.ok) {
                    const freshProgress = await progressResponse.json();
                    activeRouteProgress = freshProgress;
                } else {
                    // Fallback to response
                    activeRouteProgress = { ...result.updated_progress };
                }

                console.log("After check-in:", {
                    completed_points:
                        activeRouteProgress?.completed_points_count,
                    status: activeRouteProgress?.status,
                });

                if (activeRouteProgress.status === "completed") {
                    routeCompleted = true;
                    activeRouteProgress = null; // Clear active route immediately
                }

                // Clear selectedPOI to allow selecting next POI
                selectedPOI = null;

                setTimeout(() => (showReward = false), 3000);
            }
        } catch (e) {
            console.error("Check-in failed", e);
        }
    }

    function handleBeforeCheckIn() {
        showVerificationModal = true;
    }

    function handleVerified() {
        showVerificationModal = false;
        checkIn();
    }

    async function loadQuizzesForPOI(poiId: number) {
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(
                `http://localhost:8000/api/v1/quizzes/poi/${poiId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                },
            );

            if (response.ok) {
                currentQuizzes = await response.json();
                // Removed auto-start: if (currentQuizzes.length > 0) { ... }
            }
        } catch (error) {
            console.error("Failed to load quizzes:", error);
        }
    }

    function handleQuizComplete(event: CustomEvent) {
        userXP = event.detail.newTotalXp;
        userLevel = event.detail.newLevel;

        // Show XP reward notification
        lastReward = event.detail.xpEarned;
        showReward = true;
        setTimeout(() => {
            showReward = false;
        }, 2000);
    }

    function handleNextQuiz() {
        if (currentQuizIndex < currentQuizzes.length - 1) {
            currentQuizIndex++;
        } else {
            showQuiz = false;
            currentQuizzes = [];
            currentQuizIndex = 0;
        }
    }

    function handleCloseQuiz() {
        showQuiz = false;
        currentQuizzes = [];
        currentQuizIndex = 0;
    }

    function logout() {
        localStorage.removeItem("token");
        push("/");
    }

    function handlePOISelection(event: CustomEvent) {
        selectedPOI = event.detail;

        // Load quizzes for this POI immediately when selected
        if (selectedPOI && selectedPOI.id) {
            loadQuizzesForPOI(selectedPOI.id);
        }
    }

    // Reactive totalPoints calculation - fetch route data when activeRouteProgress changes
    $: {
        if (activeRouteProgress && activeRouteProgress.route_id) {
            // Fetch route details to get current totalPoints
            fetch(
                `http://localhost:8000/api/v1/routes/${activeRouteProgress.route_id}`,
            )
                .then((res) => res.json())
                .then((route) => {
                    if (route && route.points) {
                        totalPoints = route.points.length;
                    } else {
                        totalPoints = 0;
                    }
                })
                .catch((err) => {
                    console.error("Failed to fetch route details", err);
                    totalPoints = 0;
                });
        } else {
            totalPoints = 0;
        }
    }

    // Level Calculation Logic
    $: currentLevel = Math.max(
        1,
        Math.floor((-5 + Math.sqrt(49 + 0.16 * userXP)) / 2),
    );
    $: xpForCurrentLevel =
        25 * Math.pow(currentLevel, 2) + 125 * currentLevel - 150;
    $: xpForNextLevel =
        25 * Math.pow(currentLevel + 1, 2) + 125 * (currentLevel + 1) - 150;
    $: levelProgress = Math.min(
        100,
        Math.max(
            0,
            ((userXP - xpForCurrentLevel) /
                (xpForNextLevel - xpForCurrentLevel)) *
                100,
        ),
    );
</script>

<div class="min-h-screen bg-neutral-900 text-white flex flex-col">
    <!-- Navbar -->
    <nav
        class="h-16 bg-neutral-900/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-8 z-50"
    >
        <div class="flex items-center gap-8">
            <span
                class="text-xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
                >Moscow Chrono</span
            >

            <div
                class="bg-white/5 px-4 py-1 rounded-full border border-white/10 flex items-center gap-3"
            >
                <div class="flex items-center gap-1.5">
                    <span class="text-[10px] uppercase font-bold text-gray-500"
                        >Уровень</span
                    >
                    <span class="text-sm font-bold text-amber-500"
                        >{currentLevel}</span
                    >
                </div>
                <div
                    class="w-24 h-1.5 bg-neutral-700 rounded-full overflow-hidden"
                >
                    <div
                        class="h-full bg-amber-500 transition-all duration-500"
                        style="width: {levelProgress}%"
                    ></div>
                </div>
                <span class="text-xs font-medium text-gray-300"
                    >{Math.floor(userXP)} / {xpForNextLevel} XP</span
                >
            </div>
        </div>

        <div class="flex items-center gap-4">
            <a
                href="#/routes"
                class="hover:text-amber-400 text-sm font-medium transition-colors"
                >Маршруты</a
            >
            <button
                on:click={() => showOnboarding = true}
                class="flex items-center gap-2 hover:text-amber-400 text-sm font-medium transition-colors"
                title="Как пользоваться"
            >
                <HelpCircle size={18} />
                <span>Помощь</span>
            </button>
            <a
                href="#/profile"
                class="flex items-center gap-2 hover:text-amber-400 text-sm font-medium transition-colors"
            >
                <User size={18} />
                <span>Профиль</span>
            </a>
            <button
                on:click={logout}
                class="flex items-center gap-2 hover:text-red-400 text-sm font-medium transition-colors ml-4"
            >
                <LogOut size={18} />
                <span>Выйти</span>
            </button>
        </div>
    </nav>

    <div class="flex-1 flex overflow-hidden">
        <!-- Sidebar -->
        <div
            class="w-96 bg-neutral-800 border-r border-white/10 p-6 overflow-y-auto"
        >
            {#if selectedPOI}
                {#if activeRouteProgress}
                    <div
                        class="mb-4 flex items-center justify-between border-b border-white/10 pb-4"
                    >
                        <h2 class="text-xl font-bold text-amber-500">
                            {selectedPOI.title}
                        </h2>
                        <button
                            on:click={() => (selectedPOI = null)}
                            class="text-gray-500 hover:text-white text-sm"
                            >Закрыть</button
                        >
                    </div>

                    <div class="pb-20">
                        <div class="space-y-6">
                            <div class="sticky top-0 z-20 bg-neutral-800 pb-4">
                                <button
                                    on:click={handleBeforeCheckIn}
                                    disabled={!selectedPOI.isCurrent}
                                    class="w-full py-4 rounded-xl font-black text-lg transition-all transform flex items-center justify-center gap-3 shadow-xl group
                                    {selectedPOI.isCurrent
                                        ? 'bg-amber-500 hover:bg-amber-600 text-black active:scale-95 shadow-amber-500/30'
                                        : 'bg-neutral-700 text-gray-500 cursor-not-allowed shadow-none'}"
                                >
                                    {#if selectedPOI.isVisited}
                                        <span>✓ ТОЧКА ПРОЙДЕНА</span>
                                    {:else if selectedPOI.isCurrent}
                                        <Camera size={20} />
                                        <span>Я ЗДЕСЬ!</span>
                                        <span
                                            class="bg-black/20 px-2 py-0.5 rounded text-xs group-hover:bg-black/30 transition-colors"
                                            >+50 XP</span
                                        >
                                    {:else}
                                        <span>ЗАБЛОКИРОВАНО</span>
                                    {/if}
                                </button>
                            </div>

                            {#if selectedPOI.historic_image_url || selectedPOI.modern_image_url}
                                <div class="space-y-4">
                                    {#if selectedPOI.historic_image_url}
                                        <div class="relative group">
                                            <img
                                                src={selectedPOI.historic_image_url}
                                                alt="История"
                                                class="w-full h-48 object-cover rounded-lg border border-white/10"
                                            />
                                            <div
                                                class="absolute bottom-2 left-2 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-xs flex items-center gap-1"
                                            >
                                                <Clock size={12} /> История
                                            </div>
                                        </div>
                                    {/if}

                                    {#if selectedPOI.modern_image_url}
                                        <div class="relative group">
                                            <img
                                                src={selectedPOI.modern_image_url}
                                                alt="Современность"
                                                class="w-full h-48 object-cover rounded-lg border border-white/10"
                                            />
                                            <div
                                                class="absolute bottom-2 left-2 bg-amber-500/80 backdrop-blur-md px-2 py-1 rounded text-xs text-black font-bold flex items-center gap-1"
                                            >
                                                <Camera size={12} /> Сейчас
                                            </div>
                                        </div>
                                    {/if}
                                </div>
                            {/if}

                            <div
                                class="bg-white/5 p-4 rounded-xl border border-white/5"
                            >
                                <div
                                    class="flex items-center gap-2 mb-2 text-amber-400"
                                >
                                    <Info size={16} />
                                    <span
                                        class="text-sm font-bold uppercase tracking-wider"
                                        >Историческая справка</span
                                    >
                                </div>
                                <p
                                    class="text-sm text-gray-300 leading-relaxed italic"
                                >
                                    {selectedPOI.description}
                                </p>
                            </div>

                            {#if currentQuizzes.length > 0}
                                <button
                                    on:click={() => {
                                        currentQuizIndex = 0;
                                        showQuiz = true;
                                    }}
                                    class="w-full mt-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-black font-bold py-4 px-6 rounded-xl transition-all transform active:scale-95 shadow-lg shadow-amber-500/20 flex items-center justify-center gap-3"
                                >
                                    <span class="text-xl">🎯</span>
                                    <span>Пройти квиз</span>
                                    <span
                                        class="bg-black/20 px-2 py-0.5 rounded text-xs ml-auto"
                                        >+{currentQuizzes.reduce(
                                            (acc, q) => acc + q.reward_xp,
                                            0,
                                        )} XP</span
                                    >
                                </button>
                            {/if}
                        </div>
                    </div>
                {:else}
                    <div class="py-12 text-center">
                        <div class="mb-6 flex justify-center text-amber-500/30">
                            <MapIcon size={64} />
                        </div>
                        <h2 class="text-xl font-bold mb-2">
                            Маршрут не выбран
                        </h2>
                        <p class="text-gray-400 text-sm mb-8 leading-relaxed">
                            Чтобы отмечаться в точках, нужно сначала
                            активировать маршрут.
                        </p>
                        <a
                            href="#/routes"
                            class="inline-block py-3 px-8 bg-amber-500 hover:bg-amber-600 rounded-xl text-black font-bold transition-all transform active:scale-95"
                        >
                            К маршрутам
                        </a>
                    </div>
                {/if}
            {:else}
                <div class="mb-8">
                    <h2 class="text-lg font-bold mb-4 text-gray-300">
                        Текущая экспедиция
                    </h2>
                    {#if activeRouteProgress}
                        <div
                            class="bg-white/5 p-5 rounded-2xl border border-white/10 shadow-inner"
                        >
                            <div class="flex justify-between items-center mb-4">
                                <span
                                    class="text-xs font-bold uppercase tracking-tighter text-gray-500"
                                    >Прогресс</span
                                >
                                <span class="text-sm font-black text-amber-500">
                                    {activeRouteProgress.completed_points_count}
                                    / {totalPoints}
                                </span>
                            </div>
                            <div
                                class="w-full h-3 bg-black/40 rounded-full overflow-hidden border border-white/5 p-0.5"
                            >
                                <div
                                    class="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(245,158,11,0.3)]"
                                    style="width: {(activeRouteProgress.completed_points_count /
                                        (totalPoints || 1)) *
                                        100}%"
                                ></div>
                            </div>
                        </div>
                    {:else}
                        <div
                            class="bg-amber-500/5 border border-amber-500/10 p-6 rounded-2xl text-center"
                        >
                            <div
                                class="text-amber-500/20 mb-3 flex justify-center"
                            >
                                <MapIcon size={40} />
                            </div>
                            <p class="text-sm text-amber-200/50 italic mb-4">
                                У вас нет активных экспедиций.
                            </p>
                            <a
                                href="#/routes"
                                class="text-xs font-bold text-amber-500 hover:text-amber-400 underline underline-offset-4"
                            >
                                Выбрать маршрут →
                            </a>
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- Map Container -->
        <div class="flex-1 relative bg-neutral-900">
            <Map on:selectPOI={handlePOISelection} {activeRouteProgress} />

            {#if showReward}
                <div
                    class="absolute top-8 left-1/2 -translate-x-1/2 z-[100] animate-bounce"
                >
                    <div
                        class="bg-amber-500 text-black px-6 py-2 rounded-full font-bold shadow-2xl flex items-center gap-2"
                    >
                        <span>✨</span>
                        <span>+{lastReward} XP</span>
                        <span class="text-xs opacity-70">История оживает!</span>
                    </div>
                </div>
            {/if}
        </div>
    </div>

    {#if routeCompleted}
        <div
            class="fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-8"
        >
            <div
                class="bg-neutral-800 border border-amber-500/30 p-8 rounded-2xl max-w-md w-full text-center shadow-2xl relative overflow-hidden"
            >
                <div
                    class="absolute inset-0 bg-amber-500/5 animate-pulse"
                ></div>
                <div class="relative z-10">
                    <div
                        class="w-20 h-20 bg-amber-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg shadow-amber-500/40"
                    >
                        <span class="text-4xl">🏆</span>
                    </div>
                    <h2 class="text-3xl font-black text-white mb-2">
                        Маршрут завершен!
                    </h2>
                    <p class="text-gray-400 mb-8 leading-relaxed">
                        Поздравляем! Вы успешно прошли этот исторический маршрут
                        и открыли для себя тайны Москвы.
                    </p>
                    <button
                        on:click={() => push("/routes")}
                        class="w-full py-4 bg-amber-500 hover:bg-amber-600 rounded-xl text-black font-bold text-lg transition-transform active:scale-95 shadow-xl shadow-amber-500/20"
                    >
                        Вернуться к маршрутам
                    </button>
                </div>
            </div>
        </div>
    {/if}
</div>

<!-- Quiz Modal -->
{#if showQuiz && currentQuizzes.length > 0}
    <QuizModal
        currentQuiz={currentQuizzes[currentQuizIndex]}
        quizIndex={currentQuizIndex}
        totalQuizzes={currentQuizzes.length}
        on:quizComplete={handleQuizComplete}
        on:next={handleNextQuiz}
        on:close={handleCloseQuiz}
    />
{/if}

<!-- Verification Modal -->
{#if showVerificationModal}
    <VerificationModal
        {selectedPOI}
        on:close={() => (showVerificationModal = false)}
        on:verified={handleVerified}
    />
{/if}

<!-- Onboarding Modal -->
{#if showOnboarding}
    <OnboardingModal on:complete={() => showOnboarding = false} />
{/if}
