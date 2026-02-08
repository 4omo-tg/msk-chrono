<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiFetch, apiGet, apiPost, isAuthenticated, logout as apiLogout } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import Map from "../components/Map.svelte";
    import QuizModal from "../components/QuizModal.svelte";
    import VerificationModal from "../components/VerificationModal.svelte";
    import OnboardingModal from "../components/OnboardingModal.svelte";
    import PhotoGallery from "../components/PhotoGallery.svelte";
    import {
        User,
        LogOut,
        Info,
        Clock,
        Camera,
        Map as MapIcon,
        HelpCircle,
        Menu,
        X,
        ChevronDown,
        ChevronUp,
    } from "lucide-svelte";

    let selectedPOI: any = null;
    let userXP: number = 0;
    let userLevel: number = 1;
    let activeRouteProgress: any = null;
    let showReward: boolean = false;
    let lastReward: number = 0;
    
    // Achievement notification
    let showAchievement: boolean = false;
    let newAchievements: any[] = [];
    let loading = true;
    let totalPoints = 0;
    let allRoutes: any[] = [];

    // Quiz state
    let showQuiz: boolean = false;
    let currentQuizzes: any[] = [];
    let currentQuizIndex: number = 0;

    // Calculate total XP for quizzes with null safety
    function getTotalQuizXP(quizzes: any[]): number {
        if (!quizzes || quizzes.length === 0) return 0;
        const total = quizzes.reduce((acc, q) => acc + (Number(q.xp_reward) || 0), 0);
        return isNaN(total) ? 0 : total;
    }

    // Verification state
    let showVerificationModal: boolean = false;

    // Onboarding state
    let showOnboarding: boolean = false;

    // Mobile state
    let mobileMenuOpen: boolean = false;
    let mobileSidebarOpen: boolean = false;

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }

        // Check if onboarding was completed
        const onboardingCompleted = localStorage.getItem("onboarding_completed");
        if (!onboardingCompleted) {
            showOnboarding = true;
        }

        try {
            // Fetch current user data
            const userRes = await apiGet("/api/v1/users/me/");
            if (userRes.ok) {
                const userData = await userRes.json();
                userXP = userData.xp;
            }

            // Fetch progress to find ANY active route
            const progRes = await apiGet("/api/v1/progress/");
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

        try {
            const response = await apiPost(
                "/api/v1/progress/check-in",
                {
                    poi_id: selectedPOI.id,
                    route_id: activeRouteProgress.route_id,
                },
            );

            if (response.ok) {
                const result = await response.json();
                userXP = result.new_total_xp;
                userLevel = result.new_level;
                lastReward = result.xp_gained;
                showReward = true;
                
                // Check for new achievements
                if (result.new_achievements && result.new_achievements.length > 0) {
                    newAchievements = result.new_achievements;
                    setTimeout(() => {
                        showAchievement = true;
                    }, 2000); // Show after XP notification
                }

                // Force reload of progress to ensure consistency
                const progressResponse = await apiGet(
                    "/api/v1/progress/current"
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

                setTimeout(() => {
                    showReward = false;
                    // Hide achievement after some time
                    if (showAchievement) {
                        setTimeout(() => {
                            showAchievement = false;
                            newAchievements = [];
                        }, 4000);
                    }
                }, 3000);
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
            const response = await apiGet(
                `/api/v1/quizzes/poi/${poiId}`
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
        apiLogout();
    }

    function handlePOISelection(event: CustomEvent) {
        selectedPOI = event.detail;

        // Load quizzes for this POI immediately when selected
        if (selectedPOI && selectedPOI.id) {
            loadQuizzesForPOI(selectedPOI.id);
        }
        
        // Open sidebar on mobile when POI is selected
        if (window.innerWidth < 1024) {
            mobileSidebarOpen = true;
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
    $: safeUserXP = typeof userXP === 'number' && !isNaN(userXP) ? userXP : 0;
    $: currentLevel = Math.max(
        1,
        Math.floor((-5 + Math.sqrt(49 + 0.16 * safeUserXP)) / 2),
    );
    $: xpForCurrentLevel =
        25 * Math.pow(currentLevel, 2) + 125 * currentLevel - 150;
    $: xpForNextLevel =
        25 * Math.pow(currentLevel + 1, 2) + 125 * (currentLevel + 1) - 150;
    $: levelProgress = Math.min(
        100,
        Math.max(
            0,
            ((safeUserXP - xpForCurrentLevel) /
                (xpForNextLevel - xpForCurrentLevel)) *
                100,
        ),
    );
</script>

<div class="min-h-screen bg-neutral-900 text-white flex flex-col">
    <!-- Navbar -->
    <nav
        class="h-14 lg:h-16 bg-neutral-900/80 backdrop-blur-md border-b border-white/10 flex items-center justify-between px-4 lg:px-8 z-50 fixed top-0 left-0 right-0"
    >
        <div class="flex items-center gap-4 lg:gap-8">
            <span
                class="text-lg lg:text-xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
                >Moscow Chrono</span
            >

            <!-- XP Bar - Hidden on mobile, visible on desktop -->
            <div
                class="hidden md:flex bg-white/5 px-4 py-1 rounded-full border border-white/10 items-center gap-3"
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
                    >{Math.floor(safeUserXP)} / {xpForNextLevel} XP</span
                >
            </div>
        </div>

        <!-- Mobile: Compact XP display -->
        <div class="flex md:hidden items-center gap-2">
            <div class="bg-amber-500/20 px-2 py-1 rounded-full flex items-center gap-1">
                <span class="text-xs font-bold text-amber-500">Ур.{currentLevel}</span>
                <span class="text-[10px] text-gray-400">{Math.floor(safeUserXP)} XP</span>
            </div>
        </div>

        <!-- Desktop Menu -->
        <div class="hidden lg:flex items-center gap-4">
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

        <!-- Mobile Menu Button -->
        <button
            on:click={() => mobileMenuOpen = !mobileMenuOpen}
            class="lg:hidden p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
            {#if mobileMenuOpen}
                <X size={24} />
            {:else}
                <Menu size={24} />
            {/if}
        </button>
    </nav>

    <!-- Mobile Menu Dropdown -->
    {#if mobileMenuOpen}
        <div class="fixed top-14 left-0 right-0 bg-neutral-900/95 backdrop-blur-md border-b border-white/10 z-40 lg:hidden">
            <div class="p-4 space-y-2">
                <a
                    href="#/routes"
                    class="flex items-center gap-3 p-3 hover:bg-white/5 rounded-lg transition-colors"
                    on:click={() => mobileMenuOpen = false}
                >
                    <MapIcon size={20} class="text-amber-500" />
                    <span>Маршруты</span>
                </a>
                <button
                    on:click={() => { showOnboarding = true; mobileMenuOpen = false; }}
                    class="flex items-center gap-3 p-3 hover:bg-white/5 rounded-lg transition-colors w-full text-left"
                >
                    <HelpCircle size={20} class="text-amber-500" />
                    <span>Помощь</span>
                </button>
                <a
                    href="#/profile"
                    class="flex items-center gap-3 p-3 hover:bg-white/5 rounded-lg transition-colors"
                    on:click={() => mobileMenuOpen = false}
                >
                    <User size={20} class="text-amber-500" />
                    <span>Профиль</span>
                </a>
                <button
                    on:click={() => { logout(); mobileMenuOpen = false; }}
                    class="flex items-center gap-3 p-3 hover:bg-red-500/10 rounded-lg transition-colors w-full text-left text-red-400"
                >
                    <LogOut size={20} />
                    <span>Выйти</span>
                </button>
            </div>
        </div>
    {/if}

    <div class="flex-1 flex overflow-hidden pt-14 lg:pt-16">
        <!-- Desktop Sidebar - только если есть активный маршрут -->
        {#if activeRouteProgress}
        <div
            class="hidden lg:block w-96 bg-neutral-800 border-r border-white/10 p-6 overflow-y-auto"
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

                            <!-- Photo Gallery Component -->
                            <PhotoGallery poi={selectedPOI} />

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
            
            {#if showAchievement && newAchievements.length > 0}
                <div
                    class="absolute top-24 left-1/2 -translate-x-1/2 z-[100]"
                >
                    <div
                        class="bg-gradient-to-r from-amber-600 to-amber-500 text-white px-6 py-3 rounded-xl font-bold shadow-2xl border-2 border-amber-400"
                    >
                        <div class="flex items-center gap-3">
                            <span class="text-2xl">🏆</span>
                            <div>
                                <div class="text-sm opacity-80">Новое достижение!</div>
                                {#each newAchievements as ach}
                                    <div class="text-lg">{ach.title}</div>
                                    {#if ach.xp_reward > 0}
                                        <div class="text-xs opacity-80">+{ach.xp_reward} XP</div>
                                    {/if}
                                {/each}
                            </div>
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Mobile: FAB to show progress when no POI selected -->
            {#if activeRouteProgress && !selectedPOI}
                <button
                    on:click={() => mobileSidebarOpen = true}
                    class="lg:hidden fixed bottom-6 right-6 z-30 bg-amber-500 text-black p-4 rounded-full shadow-lg shadow-amber-500/30 flex items-center gap-2"
                >
                    <Info size={24} />
                </button>
            {/if}
        </div>

        <!-- Mobile Bottom Sheet -->
        {#if activeRouteProgress}
            <div
                class="lg:hidden fixed bottom-0 left-0 right-0 z-40 transition-transform duration-300 ease-out"
                class:translate-y-full={!mobileSidebarOpen}
                class:translate-y-0={mobileSidebarOpen}
            >
                <!-- Backdrop -->
                {#if mobileSidebarOpen}
                    <button
                        class="fixed inset-0 bg-black/50 -z-10"
                        on:click={() => mobileSidebarOpen = false}
                        aria-label="Закрыть панель"
                    ></button>
                {/if}
                
                <div class="bg-neutral-800 rounded-t-3xl border-t border-white/10 max-h-[80vh] overflow-y-auto">
                    <!-- Handle -->
                    <button
                        on:click={() => mobileSidebarOpen = !mobileSidebarOpen}
                        class="w-full py-3 flex justify-center"
                        aria-label="Свернуть/развернуть панель"
                    >
                        <div class="w-12 h-1 bg-gray-600 rounded-full"></div>
                    </button>
                    
                    <div class="px-4 pb-6">
                        {#if selectedPOI}
                            <!-- POI Details -->
                            <div class="mb-4 flex items-center justify-between border-b border-white/10 pb-4">
                                <h2 class="text-lg font-bold text-amber-500 flex-1 pr-4">
                                    {selectedPOI.title}
                                </h2>
                                <button
                                    on:click={() => { selectedPOI = null; mobileSidebarOpen = false; }}
                                    class="text-gray-500 hover:text-white p-2"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <div class="space-y-4">
                                <!-- Check-in Button -->
                                <button
                                    on:click={handleBeforeCheckIn}
                                    disabled={!selectedPOI.isCurrent}
                                    class="w-full py-4 rounded-xl font-black text-lg transition-all transform flex items-center justify-center gap-3 shadow-xl
                                    {selectedPOI.isCurrent
                                        ? 'bg-amber-500 hover:bg-amber-600 text-black active:scale-95 shadow-amber-500/30'
                                        : 'bg-neutral-700 text-gray-500 cursor-not-allowed shadow-none'}"
                                >
                                    {#if selectedPOI.isVisited}
                                        <span>✓ ТОЧКА ПРОЙДЕНА</span>
                                    {:else if selectedPOI.isCurrent}
                                        <Camera size={20} />
                                        <span>Я ЗДЕСЬ!</span>
                                        <span class="bg-black/20 px-2 py-0.5 rounded text-xs">+50 XP</span>
                                    {:else}
                                        <span>ЗАБЛОКИРОВАНО</span>
                                    {/if}
                                </button>

                                <!-- Photo Gallery -->
                                <PhotoGallery poi={selectedPOI} />

                                <!-- Description -->
                                <div class="bg-white/5 p-4 rounded-xl border border-white/5">
                                    <div class="flex items-center gap-2 mb-2 text-amber-400">
                                        <Info size={16} />
                                        <span class="text-sm font-bold uppercase tracking-wider">Историческая справка</span>
                                    </div>
                                    <p class="text-sm text-gray-300 leading-relaxed italic">
                                        {selectedPOI.description}
                                    </p>
                                </div>

                                <!-- Quiz Button -->
                                {#if currentQuizzes.length > 0}
                                    <button
                                        on:click={() => { currentQuizIndex = 0; showQuiz = true; mobileSidebarOpen = false; }}
                                        class="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-black font-bold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-3"
                                    >
                                        <span class="text-xl">🎯</span>
                                        <span>Пройти квиз ({currentQuizzes.length})</span>
                                        <span class="bg-black/20 px-2 py-0.5 rounded text-xs ml-auto">+{getTotalQuizXP(currentQuizzes)} XP</span>
                                    </button>
                                {/if}
                            </div>
                        {:else}
                            <!-- Progress Info -->
                            <div class="mb-4">
                                <h2 class="text-lg font-bold mb-4 text-gray-300">
                                    Текущая экспедиция
                                </h2>
                                <div class="bg-white/5 p-5 rounded-2xl border border-white/10">
                                    <div class="flex justify-between items-center mb-4">
                                        <span class="text-xs font-bold uppercase tracking-tighter text-gray-500">Прогресс</span>
                                        <span class="text-sm font-black text-amber-500">
                                            {activeRouteProgress.completed_points_count} / {totalPoints}
                                        </span>
                                    </div>
                                    <div class="w-full h-3 bg-black/40 rounded-full overflow-hidden border border-white/5 p-0.5">
                                        <div
                                            class="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full transition-all duration-1000 shadow-[0_0_10px_rgba(245,158,11,0.3)]"
                                            style="width: {(activeRouteProgress.completed_points_count / (totalPoints || 1)) * 100}%"
                                        ></div>
                                    </div>
                                </div>
                                <p class="text-xs text-gray-500 mt-3 text-center">
                                    Нажмите на маркер на карте
                                </p>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
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


