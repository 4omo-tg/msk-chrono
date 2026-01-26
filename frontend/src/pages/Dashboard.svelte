<script lang="ts">
    import { API_BASE } from "../lib/config";
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
    let showHistoricPhoto: boolean = true;
    let showPhotoModal: boolean = false;
    let photoModalSrc: string = "";
    let currentQuizzes: any[] = [];
    let currentQuizIndex: number = 0;

    // Calculate total XP for quizzes with null safety
    function getTotalQuizXP(quizzes: any[]): number {
        if (!quizzes || quizzes.length === 0) return 0;
        const total = quizzes.reduce((acc, q) => acc + (Number(q.xp_reward) || 0), 0);
        return isNaN(total) ? 0 : total;
    }

    function openPhotoModal(src: string) {
        photoModalSrc = src;
        showPhotoModal = true;
    }

    function closePhotoModal() {
        showPhotoModal = false;
        photoModalSrc = "";
    }

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
                `${API_BASE}/api/v1/users/me/`,
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
                `${API_BASE}/api/v1/progress/`,
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
                    `${API_BASE}/api/v1/routes/`,
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
                `${API_BASE}/api/v1/progress/check-in`,
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
                    `${API_BASE}/api/v1/progress/current`,
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
                `${API_BASE}/api/v1/quizzes/poi/${poiId}`,
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
                `${API_BASE}/api/v1/routes/${activeRouteProgress.route_id}`,
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
        <!-- Sidebar - только если есть активный маршрут -->
        {#if activeRouteProgress}
        <div
            class="w-96 bg-neutral-800 border-r border-white/10 p-6 overflow-y-auto"
        >
            {#if selectedPOI}
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
                                <div class="relative">
                                    <!-- Табы для переключения -->
                                    <div class="flex mb-2 bg-neutral-900 rounded-lg p-1">
                                        {#if selectedPOI.historic_image_url}
                                            <button
                                                on:click={() => showHistoricPhoto = true}
                                                class="flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5
                                                    {showHistoricPhoto ? 'bg-neutral-700 text-white' : 'text-gray-400 hover:text-white'}"
                                            >
                                                <Clock size={14} />
                                                Тогда
                                            </button>
                                        {/if}
                                        {#if selectedPOI.modern_image_url}
                                            <button
                                                on:click={() => showHistoricPhoto = false}
                                                class="flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5
                                                    {!showHistoricPhoto ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white'}"
                                            >
                                                <Camera size={14} />
                                                Сейчас
                                            </button>
                                        {/if}
                                    </div>
                                    
                                    <!-- Фото с возможностью увеличения -->
                                    <div 
                                        class="relative overflow-hidden rounded-lg border border-white/10 cursor-pointer group"
                                        on:click={() => {
                                            const src = showHistoricPhoto && selectedPOI.historic_image_url 
                                                ? selectedPOI.historic_image_url 
                                                : selectedPOI.modern_image_url;
                                            if (src) openPhotoModal(src);
                                        }}
                                        on:keydown={(e) => e.key === 'Enter' && openPhotoModal(showHistoricPhoto ? selectedPOI.historic_image_url : selectedPOI.modern_image_url)}
                                        role="button"
                                        tabindex="0"
                                    >
                                        {#if showHistoricPhoto && selectedPOI.historic_image_url}
                                            <img
                                                src={selectedPOI.historic_image_url}
                                                alt="Историческое фото"
                                                class="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-300"
                                            />
                                            <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                                                <span class="text-xs text-gray-300">Историческое фото • Нажмите для увеличения</span>
                                            </div>
                                        {:else if selectedPOI.modern_image_url}
                                            <img
                                                src={selectedPOI.modern_image_url}
                                                alt="Современное фото"
                                                class="w-full h-56 object-cover group-hover:scale-105 transition-transform duration-300"
                                            />
                                            <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                                                <span class="text-xs text-amber-400">Современный вид • Нажмите для увеличения</span>
                                            </div>
                                        {/if}
                                        <!-- Overlay icon -->
                                        <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                                            <div class="bg-white/20 backdrop-blur-sm rounded-full p-3">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white">
                                                    <circle cx="11" cy="11" r="8"></circle>
                                                    <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                                                    <line x1="11" y1="8" x2="11" y2="14"></line>
                                                    <line x1="8" y1="11" x2="14" y2="11"></line>
                                                </svg>
                                            </div>
                                        </div>
                                    </div>
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
                                    <span>Пройти квиз ({currentQuizzes.length})</span>
                                    <span
                                        class="bg-black/20 px-2 py-0.5 rounded text-xs ml-auto"
                                        >+{getTotalQuizXP(currentQuizzes)} XP</span
                                    >
                                </button>
                            {/if}
                        </div>
                    </div>
            {:else}
                <!-- Сайдбар когда не выбрана точка -->
                <div class="mb-8">
                    <h2 class="text-lg font-bold mb-4 text-gray-300">
                        Текущая экспедиция
                    </h2>
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
                    <p class="text-xs text-gray-500 mt-3">
                        Нажмите на маркер на карте, чтобы увидеть информацию о точке
                    </p>
                </div>
            {/if}
        </div>
        {/if}

        <!-- Map Container -->
        <div class="flex-1 relative bg-neutral-900">
            {#if activeRouteProgress}
                <Map on:selectPOI={handlePOISelection} {activeRouteProgress} />
            {:else}
                <!-- Пустой стейт вместо карты -->
                <div class="h-full flex items-center justify-center bg-gradient-to-br from-neutral-900 via-neutral-800 to-neutral-900">
                    <div class="text-center max-w-md px-8">
                        <div class="w-32 h-32 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto mb-8 border-2 border-amber-500/20">
                            <MapIcon size={64} class="text-amber-500/40" />
                        </div>
                        <h1 class="text-3xl font-bold text-white mb-4">
                            Исследуйте Москву
                        </h1>
                        <p class="text-gray-400 mb-8 leading-relaxed">
                            Выберите маршрут и отправляйтесь в путешествие по историческим местам столицы.
                            Посещайте точки, узнавайте историю и зарабатывайте опыт!
                        </p>
                        <a
                            href="#/routes"
                            class="inline-block py-4 px-12 bg-amber-500 hover:bg-amber-600 rounded-xl text-black font-bold text-lg transition-all transform active:scale-95 shadow-xl shadow-amber-500/30"
                        >
                            Выбрать маршрут
                        </a>
                    </div>
                </div>
            {/if}

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

<!-- Photo Gallery Modal -->
{#if showPhotoModal && photoModalSrc}
    <div 
        class="fixed inset-0 z-[200] bg-black/95 backdrop-blur-md flex items-center justify-center p-4"
        on:click={closePhotoModal}
        on:keydown={(e) => e.key === 'Escape' && closePhotoModal()}
        role="dialog"
        tabindex="-1"
    >
        <button 
            class="absolute top-4 right-4 text-white/70 hover:text-white z-10 p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
            on:click={closePhotoModal}
        >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
        </button>
        
        <!-- Navigation between photos -->
        {#if selectedPOI?.historic_image_url && selectedPOI?.modern_image_url}
            <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex gap-2 z-10">
                <button 
                    class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2
                        {photoModalSrc === selectedPOI.historic_image_url ? 'bg-white text-black' : 'bg-white/20 text-white hover:bg-white/30'}"
                    on:click|stopPropagation={() => photoModalSrc = selectedPOI.historic_image_url}
                >
                    <Clock size={16} />
                    Тогда
                </button>
                <button 
                    class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2
                        {photoModalSrc === selectedPOI.modern_image_url ? 'bg-amber-500 text-black' : 'bg-white/20 text-white hover:bg-white/30'}"
                    on:click|stopPropagation={() => photoModalSrc = selectedPOI.modern_image_url}
                >
                    <Camera size={16} />
                    Сейчас
                </button>
            </div>
        {/if}
        
        <img 
            src={photoModalSrc} 
            alt="Фото" 
            class="max-w-full max-h-[85vh] object-contain rounded-lg shadow-2xl"
            on:click|stopPropagation
        />
    </div>
{/if}
