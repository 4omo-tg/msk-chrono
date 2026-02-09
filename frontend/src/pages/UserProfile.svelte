<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPost, isAuthenticated } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import {
        User, Award, MapPin, Route, Star, Trophy, ArrowLeft,
        UserPlus, UserCheck, Clock, Calendar, Flame, Footprints, Map
    } from "lucide-svelte";

    export let params: { id: string } = { id: '' };
    
    let profile: any = null;
    let loading = true;
    let error = "";
    let actionLoading = false;

    const iconMap: Record<string, any> = {
        'Star': Star, 'Award': Award, 'Trophy': Trophy, 'Route': Route,
        'MapPin': MapPin, 'Flame': Flame
    };
    
    const colorClasses: Record<string, string> = {
        'gray': 'text-gray-400', 'green': 'text-green-400', 'blue': 'text-blue-400',
        'amber': 'text-amber-400', 'purple': 'text-purple-400', 'pink': 'text-pink-400',
        'emerald': 'text-emerald-400', 'orange': 'text-orange-400', 'red': 'text-red-400',
        'yellow': 'text-yellow-400', 'cyan': 'text-cyan-400'
    };
    
    const rarityColors: Record<string, string> = {
        'common': 'text-gray-400 bg-gray-500/10',
        'uncommon': 'text-green-400 bg-green-500/10',
        'rare': 'text-blue-400 bg-blue-500/10',
        'epic': 'text-purple-400 bg-purple-500/10',
        'legendary': 'text-amber-400 bg-amber-500/10',
    };

    onMount(async () => {
        await loadProfile();
    });

    async function loadProfile() {
        loading = true;
        error = "";
        try {
            const res = await apiGet(`/api/v1/profile/${params.id}`);
            if (res.ok) {
                profile = await res.json();
            } else if (res.status === 403) {
                error = "Профиль скрыт";
            } else if (res.status === 404) {
                error = "Пользователь не найден";
            }
        } catch (e) {
            error = "Ошибка загрузки";
        }
        loading = false;
    }

    async function sendFriendRequest() {
        actionLoading = true;
        try {
            const res = await apiPost(`/api/v1/friends/request/${profile.id}`);
            if (res.ok) {
                await loadProfile();
            }
        } catch (e) {
            console.error(e);
        }
        actionLoading = false;
    }

    async function acceptFriendRequest() {
        // Need to find the request ID - for simplicity, reload incoming requests
        actionLoading = true;
        try {
            const requestsRes = await apiGet("/api/v1/friends/requests/incoming");
            if (requestsRes.ok) {
                const requests = await requestsRes.json();
                const req = requests.find((r: any) => r.from_user_id === profile.id);
                if (req) {
                    const res = await apiPost(`/api/v1/friends/accept/${req.id}`);
                    if (res.ok) await loadProfile();
                }
            }
        } catch (e) {
            console.error(e);
        }
        actionLoading = false;
    }
    
    function getAvatarUrl(url: string | null): string {
        if (!url) return '';
        return url.startsWith('/') ? API_BASE + url : url;
    }
    
    function formatDate(dateStr: string | null): string {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        return date.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' });
    }

    $: currentLevel = profile?.level || 1;
    $: xpForNextLevel = 25 * Math.pow(currentLevel + 1, 2) + 125 * (currentLevel + 1) - 150;
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
            <button on:click={() => history.back()} class="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700">
                <ArrowLeft size={20} />
            </button>
            <h1 class="text-xl font-bold">Профиль</h1>
            <div class="flex-1"></div>
            <a href="#/dashboard" class="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700" title="Дашборд">
                <Map size={20} />
            </a>
        </div>
    </header>

    <div class="max-w-2xl mx-auto px-4 py-4">

        {#if loading}
            <div class="flex items-center justify-center h-64">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </div>
        {:else if error}
            <div class="text-center py-12">
                <User size={64} class="mx-auto mb-4 text-gray-600" />
                <p class="text-gray-400">{error}</p>
                <a href="#/friends" class="inline-block mt-4 text-amber-500 hover:underline">Назад к друзьям</a>
            </div>
        {:else if profile}
            <!-- Profile Card -->
            <div class="bg-neutral-800 rounded-xl border border-white/10 overflow-hidden">
                <!-- Background -->
                <div class="h-24 bg-gradient-to-r from-amber-600/20 to-purple-600/20"></div>
                
                <!-- Avatar & Info -->
                <div class="px-6 pb-6 -mt-12">
                    <div class="flex items-end gap-4 mb-4">
                        <div class="relative">
                            <div class="w-24 h-24 rounded-full overflow-hidden bg-neutral-700 {profile.equipped_frame?.css_class || 'ring-4 ring-neutral-800'}">
                                {#if profile.avatar_url}
                                    <img src="{getAvatarUrl(profile.avatar_url)}" alt="Avatar" class="w-full h-full object-cover" />
                                {:else}
                                    <div class="w-full h-full flex items-center justify-center">
                                        <User size={40} class="text-gray-500" />
                                    </div>
                                {/if}
                            </div>
                        </div>
                        <div class="flex-1 mb-2">
                            <div class="flex items-center gap-2">
                                <h2 class="text-xl font-bold">{profile.display_name || profile.username}</h2>
                                {#if profile.is_friend}
                                    <span class="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">Друг</span>
                                {/if}
                            </div>
                            {#if profile.equipped_title}
                                <div class="text-sm {colorClasses[profile.equipped_title.color] || 'text-gray-400'}">
                                    {profile.equipped_title.name}
                                </div>
                            {/if}
                            <div class="text-sm text-gray-500">@{profile.username}</div>
                        </div>
                    </div>
                    
                    <!-- Badges -->
                    {#if profile.equipped_badges && profile.equipped_badges.length > 0}
                        <div class="flex gap-2 mb-4">
                            {#each profile.equipped_badges as badge}
                                <div class="flex items-center gap-1 px-2 py-1 rounded-full text-xs {rarityColors[badge.rarity]}">
                                    <svelte:component this={iconMap[badge.icon] || Star} size={12} />
                                    {badge.name}
                                </div>
                            {/each}
                        </div>
                    {/if}
                    
                    <!-- Bio -->
                    {#if profile.bio}
                        <p class="text-gray-300 mb-4">{profile.bio}</p>
                    {/if}
                    
                    <!-- Stats -->
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mb-4">
                        <div class="bg-neutral-900 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-amber-500">{currentLevel}</div>
                            <div class="text-xs text-gray-500">Уровень</div>
                        </div>
                        <div class="bg-neutral-900 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-amber-500">{Math.floor(profile.xp)}</div>
                            <div class="text-xs text-gray-500">XP</div>
                        </div>
                        <div class="bg-neutral-900 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-amber-500">{profile.friends_count}</div>
                            <div class="text-xs text-gray-500">Друзей</div>
                        </div>
                        <div class="bg-neutral-900 p-3 rounded-lg text-center">
                            <div class="text-lg font-bold text-amber-500">{profile.achievements_count}</div>
                            <div class="text-xs text-gray-500">Ачивок</div>
                        </div>
                    </div>
                    
                    <!-- More Stats -->
                    <div class="flex flex-wrap gap-4 text-sm text-gray-400 mb-4">
                        {#if profile.streak_days > 0}
                            <div class="flex items-center gap-1">
                                <Flame size={14} class="text-orange-500" />
                                {profile.streak_days} дней подряд
                            </div>
                        {/if}
                        {#if profile.total_distance_km > 0}
                            <div class="flex items-center gap-1">
                                <Footprints size={14} />
                                {profile.total_distance_km.toFixed(1)} км
                            </div>
                        {/if}
                        {#if profile.created_at}
                            <div class="flex items-center gap-1">
                                <Calendar size={14} />
                                С {formatDate(profile.created_at)}
                            </div>
                        {/if}
                    </div>
                    
                    <!-- Action Button -->
                    {#if isAuthenticated()}
                        {#if profile.is_friend}
                            <a href="#/friends" class="block w-full py-3 bg-neutral-700 text-center rounded-lg">
                                <span class="flex items-center justify-center gap-2">
                                    <UserCheck size={18} class="text-green-400" />
                                    Уже в друзьях
                                </span>
                            </a>
                        {:else if profile.friend_request_sent}
                            <button disabled class="w-full py-3 bg-neutral-700 rounded-lg opacity-70">
                                <span class="flex items-center justify-center gap-2">
                                    <Clock size={18} class="text-amber-400" />
                                    Заявка отправлена
                                </span>
                            </button>
                        {:else if profile.friend_request_received}
                            <button
                                on:click={acceptFriendRequest}
                                disabled={actionLoading}
                                class="w-full py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                            >
                                <span class="flex items-center justify-center gap-2">
                                    <UserCheck size={18} />
                                    Принять заявку
                                </span>
                            </button>
                        {:else}
                            <button
                                on:click={sendFriendRequest}
                                disabled={actionLoading}
                                class="w-full py-3 bg-amber-500 hover:bg-amber-600 text-black font-medium rounded-lg transition-colors"
                            >
                                <span class="flex items-center justify-center gap-2">
                                    {#if actionLoading}
                                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-black"></div>
                                    {:else}
                                        <UserPlus size={18} />
                                    {/if}
                                    Добавить в друзья
                                </span>
                            </button>
                        {/if}
                    {:else}
                        <a href="#/login" class="block w-full py-3 bg-amber-500 text-black text-center font-medium rounded-lg">
                            Войдите, чтобы добавить в друзья
                        </a>
                    {/if}
                </div>
            </div>
        {/if}
    </div>
</div>
