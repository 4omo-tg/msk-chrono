<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import { User, Award, MapPin, Route, Star, Trophy, Target, Compass } from "lucide-svelte";

    let user: any = null;
    let completedRoutes = 0;
    let totalPointsVisited = 0;

    // Ачивки
    const achievements = [
        { id: 'first_step', icon: MapPin, title: 'Первый шаг', description: 'Посетите первую точку', condition: (pts: number) => pts >= 1 },
        { id: 'explorer', icon: Compass, title: 'Исследователь', description: 'Посетите 5 точек', condition: (pts: number) => pts >= 5 },
        { id: 'pathfinder', icon: Route, title: 'Следопыт', description: 'Завершите первый маршрут', condition: (_: number, routes: number) => routes >= 1 },
        { id: 'veteran', icon: Star, title: 'Ветеран', description: 'Посетите 10 точек', condition: (pts: number) => pts >= 10 },
        { id: 'master', icon: Trophy, title: 'Мастер', description: 'Завершите 3 маршрута', condition: (_: number, routes: number) => routes >= 3 },
        { id: 'legend', icon: Award, title: 'Легенда', description: 'Достигните 5 уровня', condition: (_: number, __: number, level: number) => level >= 5 },
    ];

    $: unlockedAchievements = achievements.filter(a => a.condition(totalPointsVisited, completedRoutes, currentLevel));

    onMount(async () => {
        const token = localStorage.getItem("token");
        if (!token) {
            push("/login");
            return;
        }

        try {
            // 1. Get User Data
            const userRes = await fetch(
                `${API_BASE}/api/v1/users/me/`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                },
            );
            if (userRes.ok) {
                user = await userRes.json();
            }

            // 2. Get Progress Stats
            const progressRes = await fetch(
                `${API_BASE}/api/v1/progress/`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                },
            );
            if (progressRes.ok) {
                const progressData = await progressRes.json();
                // Simple logic: if points count matches route length (e.g. 8) or status is 'completed'
                // For MVP just counting total points visited across all routes
                totalPointsVisited = progressData.reduce(
                    (acc: number, cur: any) => acc + cur.completed_points_count,
                    0,
                );
                // Assume status 'completed' exists or infer it?
                // Let's count routes with > 0 progress for now or just 'started' ones as 'Active'
                completedRoutes = progressData.filter(
                    (p: any) => p.status === "completed",
                ).length;
            }
        } catch (e) {
            console.error("Failed to load profile", e);
        }
    });

    function logout() {
        localStorage.removeItem("token");
        push("/");
    }
    // Reactive level details
    // Only calculate if user is loaded
    $: currentLevel = user
        ? Math.max(1, Math.floor((-5 + Math.sqrt(49 + 0.16 * user.xp)) / 2))
        : 1;
    $: xpForNextLevel =
        25 * Math.pow(currentLevel + 1, 2) + 125 * (currentLevel + 1) - 150;
</script>

<div class="min-h-screen bg-neutral-900 text-white p-8">
    <div class="max-w-2xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1
                class="text-3xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent"
            >
                Профиль пользователя
            </h1>
            <a
                href="#/dashboard"
                class="text-gray-400 hover:text-white transition-colors"
                >В дашборд</a
            >
        </div>

        {#if user}
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
                        <h2 class="text-2xl font-bold text-white">
                            {user.username}
                        </h2>
                        <p class="text-gray-400">
                            Уровень {currentLevel} • {user.xp} / {xpForNextLevel}
                            XP
                        </p>
                    </div>
                </div>

                <div class="space-y-6">
                    <div>
                        <h3 class="text-lg font-medium text-white mb-2">
                            Статистика
                        </h3>
                        <div class="grid grid-cols-3 gap-4">
                            <div class="bg-neutral-900 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-amber-500">
                                    {completedRoutes}
                                </div>
                                <div class="text-xs text-gray-500">
                                    Маршрутов
                                </div>
                            </div>
                            <div class="bg-neutral-900 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-amber-500">
                                    {totalPointsVisited}
                                </div>
                                <div class="text-xs text-gray-500">
                                    Точек
                                </div>
                            </div>
                            <div class="bg-neutral-900 p-4 rounded-lg text-center">
                                <div class="text-2xl font-bold text-amber-500">
                                    {unlockedAchievements.length}
                                </div>
                                <div class="text-xs text-gray-500">
                                    Ачивок
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Ачивки -->
                    <div class="pt-6 border-t border-white/10">
                        <h3 class="text-lg font-medium text-white mb-4">
                            Достижения
                        </h3>
                        <div class="grid grid-cols-3 gap-3">
                            {#each achievements as achievement}
                                {@const unlocked = achievement.condition(totalPointsVisited, completedRoutes, currentLevel)}
                                <div 
                                    class="p-3 rounded-lg text-center transition-all {unlocked ? 'bg-amber-500/10 border border-amber-500/30' : 'bg-neutral-900/50 border border-white/5 opacity-40'}"
                                    title={achievement.description}
                                >
                                    <div class="w-10 h-10 mx-auto mb-2 rounded-full flex items-center justify-center {unlocked ? 'bg-amber-500/20 text-amber-500' : 'bg-neutral-800 text-gray-600'}">
                                        <svelte:component this={achievement.icon} size={20} />
                                    </div>
                                    <div class="text-xs font-medium {unlocked ? 'text-white' : 'text-gray-500'}">
                                        {achievement.title}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </div>

                    <div class="pt-6 border-t border-white/10">
                        <button
                            on:click={logout}
                            class="w-full bg-red-500/10 hover:bg-red-500/20 text-red-500 font-medium py-3 rounded-lg transition-colors border border-red-500/20"
                        >
                            Выйти
                        </button>
                    </div>
                </div>
            </div>
        {/if}
    </div>
</div>
