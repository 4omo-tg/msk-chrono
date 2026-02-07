<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, isAuthenticated, logout as apiLogout } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import { 
        User, Award, MapPin, Route, Star, Trophy, Target, Compass,
        Flame, Zap, Crown, Gem, BookOpen, Camera, Clock, Mountain,
        Footprints, Flag, Medal, Sparkles, X, Lock, Check, Info
    } from "lucide-svelte";

    let user: any = null;
    let completedRoutes = 0;
    let totalPointsVisited = 0;
    let totalQuizzesPassed = 0;
    
    // Ачивки с сервера
    interface AchievementData {
        id: number;
        code: string;
        title: string;
        description: string;
        icon: string;
        xp_reward: number;
        condition_type: string;
        condition_value: number;
        unlocked: boolean;
        unlocked_at: string | null;
    }
    
    let achievements: AchievementData[] = [];
    let selectedAchievement: AchievementData | null = null;
    
    // Маппинг иконок
    const iconMap: Record<string, any> = {
        'MapPin': MapPin,
        'Compass': Compass,
        'Route': Route,
        'Star': Star,
        'Trophy': Trophy,
        'Award': Award,
        'Target': Target,
        'Flame': Flame,
        'Zap': Zap,
        'Crown': Crown,
        'Gem': Gem,
        'BookOpen': BookOpen,
        'Camera': Camera,
        'Clock': Clock,
        'Mountain': Mountain,
        'Footprints': Footprints,
        'Flag': Flag,
        'Medal': Medal,
        'Sparkles': Sparkles,
    };
    
    // Цвета для разных типов ачивок
    const colorMap: Record<string, {bg: string, text: string, border: string, glow: string}> = {
        'points': { bg: 'bg-amber-500/10', text: 'text-amber-500', border: 'border-amber-500/30', glow: 'shadow-amber-500/20' },
        'routes': { bg: 'bg-emerald-500/10', text: 'text-emerald-500', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20' },
        'level': { bg: 'bg-purple-500/10', text: 'text-purple-500', border: 'border-purple-500/30', glow: 'shadow-purple-500/20' },
        'quizzes': { bg: 'bg-blue-500/10', text: 'text-blue-500', border: 'border-blue-500/30', glow: 'shadow-blue-500/20' },
        'streak': { bg: 'bg-orange-500/10', text: 'text-orange-500', border: 'border-orange-500/30', glow: 'shadow-orange-500/20' },
        'special': { bg: 'bg-pink-500/10', text: 'text-pink-500', border: 'border-pink-500/30', glow: 'shadow-pink-500/20' },
    };
    
    function getColors(type: string) {
        return colorMap[type] || colorMap['points'];
    }
    
    function getIcon(iconName: string) {
        return iconMap[iconName] || Award;
    }
    
    function getProgress(achievement: AchievementData): number {
        const value = achievement.condition_value;
        let current = 0;
        
        switch (achievement.condition_type) {
            case 'points':
                current = totalPointsVisited;
                break;
            case 'routes':
                current = completedRoutes;
                break;
            case 'level':
                current = currentLevel;
                break;
            case 'quizzes':
                current = totalQuizzesPassed;
                break;
            default:
                current = 0;
        }
        
        return Math.min(100, (current / value) * 100);
    }
    
    function getProgressText(achievement: AchievementData): string {
        const value = achievement.condition_value;
        let current = 0;
        let unit = '';
        
        switch (achievement.condition_type) {
            case 'points':
                current = totalPointsVisited;
                unit = 'точек';
                break;
            case 'routes':
                current = completedRoutes;
                unit = 'маршрутов';
                break;
            case 'level':
                current = currentLevel;
                unit = 'уровень';
                break;
            case 'quizzes':
                current = totalQuizzesPassed;
                unit = 'квизов';
                break;
            default:
                return '';
        }
        
        return `${Math.min(current, value)} / ${value} ${unit}`;
    }
    
    function formatDate(dateStr: string | null): string {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
    }
    
    $: unlockedAchievements = achievements.filter(a => a.unlocked);

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }

        try {
            // 1. Get User Data
            const userRes = await apiGet("/api/v1/users/me");
            if (userRes.ok) {
                user = await userRes.json();
            }

            // 2. Get Progress Stats
            const progressRes = await apiGet("/api/v1/progress/");
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
            
            // 3. Get Achievements from server
            const achievementsRes = await apiGet("/api/v1/achievements/");
            if (achievementsRes.ok) {
                achievements = await achievementsRes.json();
            }
        } catch (e) {
            console.error("Failed to load profile", e);
        }
    });

    function logout() {
        apiLogout();
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
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-medium text-white">
                                Достижения
                            </h3>
                            <span class="text-sm text-gray-400">
                                {unlockedAchievements.length} / {achievements.length}
                            </span>
                        </div>
                        <div class="grid grid-cols-3 gap-3 max-h-[400px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-neutral-700 scrollbar-track-neutral-800">
                            {#each achievements as achievement}
                                {@const colors = getColors(achievement.condition_type)}
                                {@const progress = getProgress(achievement)}
                                <button 
                                    on:click={() => selectedAchievement = achievement}
                                    class="p-3 rounded-lg text-center transition-all cursor-pointer hover:scale-105 {achievement.unlocked ? `${colors.bg} border ${colors.border} shadow-lg ${colors.glow}` : 'bg-neutral-900/50 border border-white/5 opacity-50 hover:opacity-70'}"
                                >
                                    <div class="relative">
                                        <div class="w-12 h-12 mx-auto mb-2 rounded-full flex items-center justify-center {achievement.unlocked ? `${colors.bg} ${colors.text}` : 'bg-neutral-800 text-gray-600'}">
                                            <svelte:component this={getIcon(achievement.icon)} size={24} />
                                        </div>
                                        {#if achievement.unlocked}
                                            <div class="absolute -top-1 -right-1 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                                                <Check size={12} class="text-white" />
                                            </div>
                                        {:else if progress > 0}
                                            <div class="absolute -bottom-1 left-1/2 -translate-x-1/2 w-10 h-1 bg-neutral-700 rounded-full overflow-hidden">
                                                <div class="h-full {colors.bg.replace('/10', '')} transition-all" style="width: {progress}%"></div>
                                            </div>
                                        {/if}
                                    </div>
                                    <div class="text-xs font-medium {achievement.unlocked ? 'text-white' : 'text-gray-500'} truncate">
                                        {achievement.title}
                                    </div>
                                    {#if achievement.xp_reward > 0}
                                        <div class="text-[10px] mt-1 {achievement.unlocked ? colors.text : 'text-gray-600'}">
                                            +{achievement.xp_reward} XP
                                        </div>
                                    {/if}
                                </button>
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

<!-- Achievement Detail Modal -->
{#if selectedAchievement}
    {@const colors = getColors(selectedAchievement.condition_type)}
    {@const progress = getProgress(selectedAchievement)}
    <div 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        on:click={() => selectedAchievement = null}
        on:keydown={(e) => e.key === 'Escape' && (selectedAchievement = null)}
        role="dialog"
        tabindex="-1"
    >
        <div 
            class="bg-neutral-900 border border-white/10 rounded-2xl p-6 max-w-sm w-full shadow-2xl"
            on:click|stopPropagation
        >
            <!-- Header -->
            <div class="flex justify-between items-start mb-6">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 rounded-xl flex items-center justify-center {selectedAchievement.unlocked ? `${colors.bg} ${colors.text}` : 'bg-neutral-800 text-gray-500'}">
                        <svelte:component this={getIcon(selectedAchievement.icon)} size={32} />
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-white">{selectedAchievement.title}</h3>
                        <div class="flex items-center gap-2 mt-1">
                            {#if selectedAchievement.unlocked}
                                <span class="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full flex items-center gap-1">
                                    <Check size={10} /> Получено
                                </span>
                            {:else}
                                <span class="px-2 py-0.5 bg-neutral-700 text-gray-400 text-xs rounded-full flex items-center gap-1">
                                    <Lock size={10} /> Заблокировано
                                </span>
                            {/if}
                        </div>
                    </div>
                </div>
                <button 
                    on:click={() => selectedAchievement = null}
                    class="text-gray-500 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>
            </div>
            
            <!-- Description -->
            <p class="text-gray-300 mb-6">{selectedAchievement.description}</p>
            
            <!-- How to get -->
            <div class="bg-neutral-800/50 rounded-xl p-4 mb-6">
                <div class="flex items-center gap-2 text-sm text-gray-400 mb-3">
                    <Info size={14} />
                    <span>Как получить</span>
                </div>
                <p class="text-white text-sm">
                    {#if selectedAchievement.condition_type === 'points'}
                        Посетите <span class="{colors.text} font-bold">{selectedAchievement.condition_value}</span> точек на маршрутах. Нажмите "Я здесь!" у каждой достопримечательности.
                    {:else if selectedAchievement.condition_type === 'routes'}
                        Завершите <span class="{colors.text} font-bold">{selectedAchievement.condition_value}</span> маршрутов полностью. Посетите все точки маршрута по порядку.
                    {:else if selectedAchievement.condition_type === 'level'}
                        Достигните <span class="{colors.text} font-bold">{selectedAchievement.condition_value}</span> уровня. Зарабатывайте XP за посещения и квизы.
                    {:else if selectedAchievement.condition_type === 'quizzes'}
                        Правильно ответьте на <span class="{colors.text} font-bold">{selectedAchievement.condition_value}</span> квизов. Изучайте историю и проходите тесты!
                    {:else}
                        Выполните специальное условие.
                    {/if}
                </p>
            </div>
            
            <!-- Progress -->
            {#if !selectedAchievement.unlocked}
                <div class="mb-6">
                    <div class="flex justify-between text-sm mb-2">
                        <span class="text-gray-400">Прогресс</span>
                        <span class="{colors.text} font-medium">{getProgressText(selectedAchievement)}</span>
                    </div>
                    <div class="h-2 bg-neutral-800 rounded-full overflow-hidden">
                        <div 
                            class="h-full transition-all duration-500 {colors.text.replace('text-', 'bg-')}"
                            style="width: {progress}%"
                        ></div>
                    </div>
                </div>
            {:else}
                <div class="mb-6 text-center py-3 bg-green-500/10 rounded-xl border border-green-500/20">
                    <p class="text-green-400 text-sm">
                        🎉 Получено {formatDate(selectedAchievement.unlocked_at)}
                    </p>
                </div>
            {/if}
            
            <!-- Reward -->
            <div class="flex items-center justify-between p-4 bg-neutral-800 rounded-xl">
                <span class="text-gray-400">Награда</span>
                <span class="text-xl font-bold {colors.text}">+{selectedAchievement.xp_reward} XP</span>
            </div>
        </div>
    </div>
{/if}
