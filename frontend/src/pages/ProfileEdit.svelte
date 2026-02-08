<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPut, apiPostFormData, isAuthenticated } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import {
        User, Camera, Save, ArrowLeft, Sparkles, Crown, Award,
        Star, Trophy, Compass, Flame, BookOpen, Zap, Route,
        Check, Lock, X, Eye, EyeOff, Users
    } from "lucide-svelte";

    let user: any = null;
    let loading = true;
    let saving = false;
    let error = "";
    let success = "";
    
    // Edit fields
    let displayName = "";
    let bio = "";
    let profileVisibility = "public";
    let showOnLeaderboard = true;
    
    // Cosmetics
    let titles: any[] = [];
    let frames: any[] = [];
    let badges: any[] = [];
    
    let selectedTitleId: number | null = null;
    let selectedFrameId: number | null = null;
    let selectedBadgeIds: number[] = [];
    
    // Avatar upload
    let avatarFile: File | null = null;
    let avatarPreview: string | null = null;
    
    // Tab
    let activeTab = "profile";
    
    const iconMap: Record<string, any> = {
        'Star': Star, 'Award': Award, 'Trophy': Trophy, 'Crown': Crown,
        'Compass': Compass, 'Flame': Flame, 'BookOpen': BookOpen, 'Zap': Zap,
        'Route': Route, 'Camera': Camera, 'Sparkles': Sparkles
    };
    
    const rarityColors: Record<string, string> = {
        'common': 'text-gray-400 bg-gray-500/10 border-gray-500/30',
        'uncommon': 'text-green-400 bg-green-500/10 border-green-500/30',
        'rare': 'text-blue-400 bg-blue-500/10 border-blue-500/30',
        'epic': 'text-purple-400 bg-purple-500/10 border-purple-500/30',
        'legendary': 'text-amber-400 bg-amber-500/10 border-amber-500/30 animate-pulse',
    };
    
    const colorClasses: Record<string, string> = {
        'gray': 'text-gray-400', 'green': 'text-green-400', 'blue': 'text-blue-400',
        'amber': 'text-amber-400', 'purple': 'text-purple-400', 'pink': 'text-pink-400',
        'emerald': 'text-emerald-400', 'orange': 'text-orange-400', 'red': 'text-red-400',
        'yellow': 'text-yellow-400', 'cyan': 'text-cyan-400'
    };

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }
        await loadData();
    });
    
    async function loadData() {
        loading = true;
        try {
            // Load profile
            const profileRes = await apiGet("/api/v1/profile/me");
            if (profileRes.ok) {
                user = await profileRes.json();
                displayName = user.display_name || "";
                bio = user.bio || "";
                profileVisibility = user.profile_visibility || "public";
                showOnLeaderboard = user.show_on_leaderboard ?? true;
                selectedTitleId = user.equipped_title_id;
                selectedFrameId = user.equipped_frame_id;
                if (user.equipped_badge_ids) {
                    try {
                        selectedBadgeIds = JSON.parse(user.equipped_badge_ids);
                    } catch { selectedBadgeIds = []; }
                }
            }
            
            // Load cosmetics
            const [titlesRes, framesRes, badgesRes] = await Promise.all([
                apiGet("/api/v1/cosmetics/titles"),
                apiGet("/api/v1/cosmetics/frames"),
                apiGet("/api/v1/cosmetics/badges"),
            ]);
            
            if (titlesRes.ok) titles = await titlesRes.json();
            if (framesRes.ok) frames = await framesRes.json();
            if (badgesRes.ok) badges = await badgesRes.json();
            
        } catch (e) {
            error = "Ошибка загрузки данных";
        }
        loading = false;
    }
    
    function handleAvatarChange(e: Event) {
        const input = e.target as HTMLInputElement;
        if (input.files && input.files[0]) {
            avatarFile = input.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                avatarPreview = e.target?.result as string;
            };
            reader.readAsDataURL(avatarFile);
        }
    }
    
    async function uploadAvatar() {
        if (!avatarFile) return;
        const formData = new FormData();
        formData.append("file", avatarFile);
        const res = await apiPostFormData("/api/v1/profile/me/avatar", formData);
        if (res.ok) {
            const data = await res.json();
            user.avatar_url = data.avatar_url;
            avatarFile = null;
            avatarPreview = null;
        }
    }
    
    async function saveProfile() {
        saving = true;
        error = "";
        success = "";
        
        try {
            // Upload avatar if changed
            if (avatarFile) await uploadAvatar();
            
            // Update profile
            const res = await apiPut("/api/v1/profile/me", {
                display_name: displayName || null,
                bio: bio || null,
                equipped_title_id: selectedTitleId || 0,
                equipped_frame_id: selectedFrameId || 0,
                equipped_badge_ids: selectedBadgeIds,
                profile_visibility: profileVisibility,
                show_on_leaderboard: showOnLeaderboard,
            });
            
            if (res.ok) {
                success = "Профиль сохранён!";
                setTimeout(() => success = "", 3000);
            } else {
                const data = await res.json();
                error = data.detail || "Ошибка сохранения";
            }
        } catch (e) {
            error = "Ошибка сохранения";
        }
        saving = false;
    }
    
    function toggleBadge(badgeId: number) {
        if (selectedBadgeIds.includes(badgeId)) {
            selectedBadgeIds = selectedBadgeIds.filter(id => id !== badgeId);
        } else if (selectedBadgeIds.length < 3) {
            selectedBadgeIds = [...selectedBadgeIds, badgeId];
        }
    }
    
    $: currentLevel = user?.level || 1;
    $: avatarUrl = avatarPreview || user?.avatar_url || user?.telegram_photo_url;
    $: selectedTitle = titles.find(t => t.id === selectedTitleId);
    $: selectedFrame = frames.find(f => f.id === selectedFrameId);
</script>

<div class="min-h-screen bg-neutral-900 text-white pb-20">
    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
            <a href="#/profile" class="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700">
                <ArrowLeft size={20} />
            </a>
            <h1 class="text-lg sm:text-xl font-bold truncate">Настройки</h1>
        </div>
    </header>
    
    <div class="max-w-2xl mx-auto px-4 py-4">
        
        {#if loading}
            <div class="flex items-center justify-center h-64">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </div>
        {:else if user}
            <!-- Tabs - Horizontal scroll on mobile -->
            <div class="flex gap-2 mb-6 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
                {#each [{id: 'profile', label: 'Профиль', icon: User}, {id: 'titles', label: 'Титулы', icon: Crown}, {id: 'frames', label: 'Рамки', icon: Sparkles}, {id: 'badges', label: 'Бейджи', icon: Award}] as tab}
                    <button
                        on:click={() => activeTab = tab.id}
                        class="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap transition-colors text-sm sm:text-base {activeTab === tab.id ? 'bg-amber-500 text-black' : 'bg-neutral-800 hover:bg-neutral-700'}"
                    >
                        <svelte:component this={tab.icon} size={16} />
                        <span class="hidden xs:inline">{tab.label}</span>
                    </button>
                {/each}
            </div>
            
            <!-- Profile Preview -->
            <div class="bg-neutral-800 rounded-xl p-4 mb-6 border border-white/10">
                <p class="text-xs text-gray-500 mb-3">Предпросмотр</p>
                <div class="flex items-center gap-4">
                    <div class="relative">
                        <div class="w-16 h-16 rounded-full overflow-hidden {selectedFrame?.css_class || 'ring-2 ring-gray-600'}">
                            {#if avatarUrl}
                                <img src="{avatarUrl.startsWith('/') ? API_BASE + avatarUrl : avatarUrl}" alt="Avatar" class="w-full h-full object-cover" />
                            {:else}
                                <div class="w-full h-full bg-neutral-700 flex items-center justify-center">
                                    <User size={24} class="text-gray-500" />
                                </div>
                            {/if}
                        </div>
                    </div>
                    <div>
                        <div class="font-bold text-lg">{displayName || user.username}</div>
                        {#if selectedTitle}
                            <div class="text-sm {colorClasses[selectedTitle.color] || 'text-gray-400'}">
                                {selectedTitle.name}
                            </div>
                        {/if}
                        <div class="text-xs text-gray-500">@{user.username} • Ур. {currentLevel}</div>
                    </div>
                </div>
                {#if selectedBadgeIds.length > 0}
                    <div class="flex gap-2 mt-3">
                        {#each selectedBadgeIds as badgeId}
                            {@const badge = badges.find(b => b.id === badgeId)}
                            {#if badge}
                                <div class="flex items-center gap-1 px-2 py-1 rounded-full text-xs {rarityColors[badge.rarity]}">
                                    <svelte:component this={iconMap[badge.icon] || Star} size={12} />
                                    {badge.name}
                                </div>
                            {/if}
                        {/each}
                    </div>
                {/if}
            </div>
            
            <!-- Tab Content -->
            {#if activeTab === 'profile'}
                <div class="space-y-4">
                    <!-- Avatar -->
                    <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                        <label class="block text-sm font-medium mb-3">Аватар</label>
                        <div class="flex items-center gap-4">
                            <div class="w-20 h-20 rounded-full overflow-hidden bg-neutral-700">
                                {#if avatarUrl}
                                    <img src="{avatarUrl.startsWith('/') ? API_BASE + avatarUrl : avatarUrl}" alt="Avatar" class="w-full h-full object-cover" />
                                {:else}
                                    <div class="w-full h-full flex items-center justify-center">
                                        <User size={32} class="text-gray-500" />
                                    </div>
                                {/if}
                            </div>
                            <label class="cursor-pointer">
                                <input type="file" accept="image/*" class="hidden" on:change={handleAvatarChange} />
                                <span class="flex items-center gap-2 px-4 py-2 bg-neutral-700 hover:bg-neutral-600 rounded-lg transition-colors">
                                    <Camera size={16} />
                                    Загрузить
                                </span>
                            </label>
                        </div>
                    </div>
                    
                    <!-- Display Name -->
                    <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                        <label class="block text-sm font-medium mb-2">Отображаемое имя</label>
                        <input
                            type="text"
                            bind:value={displayName}
                            placeholder="{user.username}"
                            maxlength="50"
                            class="w-full bg-neutral-900 border border-white/10 rounded-lg px-4 py-2 focus:border-amber-500 focus:outline-none"
                        />
                        <p class="text-xs text-gray-500 mt-1">Будет отображаться вместо @{user.username}</p>
                    </div>
                    
                    <!-- Bio -->
                    <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                        <label class="block text-sm font-medium mb-2">О себе</label>
                        <textarea
                            bind:value={bio}
                            placeholder="Расскажите о себе..."
                            maxlength="500"
                            rows="3"
                            class="w-full bg-neutral-900 border border-white/10 rounded-lg px-4 py-2 focus:border-amber-500 focus:outline-none resize-none"
                        ></textarea>
                        <p class="text-xs text-gray-500 mt-1">{bio.length}/500</p>
                    </div>
                    
                    <!-- Privacy -->
                    <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                        <label class="block text-sm font-medium mb-3">Приватность</label>
                        <div class="space-y-3">
                            <div>
                                <p class="text-sm mb-2">Кто может видеть профиль</p>
                                <div class="flex gap-2">
                                    {#each [{id: 'public', label: 'Все', icon: Eye}, {id: 'friends', label: 'Друзья', icon: Users}, {id: 'private', label: 'Никто', icon: EyeOff}] as opt}
                                        <button
                                            on:click={() => profileVisibility = opt.id}
                                            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors {profileVisibility === opt.id ? 'bg-amber-500 text-black' : 'bg-neutral-700 hover:bg-neutral-600'}"
                                        >
                                            <svelte:component this={opt.icon} size={14} />
                                            {opt.label}
                                        </button>
                                    {/each}
                                </div>
                            </div>
                            <label class="flex items-center gap-3 cursor-pointer">
                                <input type="checkbox" bind:checked={showOnLeaderboard} class="sr-only peer" />
                                <div class="w-10 h-6 bg-neutral-700 peer-checked:bg-amber-500 rounded-full relative transition-colors">
                                    <div class="absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4"></div>
                                </div>
                                <span class="text-sm">Показывать в таблице лидеров</span>
                            </label>
                        </div>
                    </div>
                </div>
                
            {:else if activeTab === 'titles'}
                <div class="grid grid-cols-2 gap-3">
                    <!-- No title option -->
                    <button
                        on:click={() => selectedTitleId = null}
                        class="p-4 rounded-xl border transition-all {selectedTitleId === null ? 'bg-amber-500/20 border-amber-500' : 'bg-neutral-800 border-white/10 hover:border-white/30'}"
                    >
                        <div class="text-sm font-medium">Без титула</div>
                        <div class="text-xs text-gray-500">Не отображать</div>
                    </button>
                    
                    {#each titles as title}
                        <button
                            on:click={() => title.unlocked && (selectedTitleId = title.id)}
                            disabled={!title.unlocked}
                            class="p-4 rounded-xl border transition-all relative {selectedTitleId === title.id ? 'bg-amber-500/20 border-amber-500' : title.unlocked ? 'bg-neutral-800 border-white/10 hover:border-white/30' : 'bg-neutral-900/50 border-white/5 opacity-50'}"
                        >
                            {#if !title.unlocked}
                                <div class="absolute top-2 right-2">
                                    <Lock size={14} class="text-gray-500" />
                                </div>
                            {/if}
                            <div class="text-sm font-medium {colorClasses[title.color] || 'text-gray-400'}">{title.name}</div>
                            <div class="text-xs text-gray-500 mt-1">{title.description}</div>
                            <div class="text-xs mt-2 {rarityColors[title.rarity]}">{title.rarity}</div>
                        </button>
                    {/each}
                </div>
                
            {:else if activeTab === 'frames'}
                <div class="grid grid-cols-2 gap-3">
                    {#each frames as frame}
                        <button
                            on:click={() => frame.unlocked && (selectedFrameId = frame.id)}
                            disabled={!frame.unlocked}
                            class="p-4 rounded-xl border transition-all relative {selectedFrameId === frame.id ? 'bg-amber-500/20 border-amber-500' : frame.unlocked ? 'bg-neutral-800 border-white/10 hover:border-white/30' : 'bg-neutral-900/50 border-white/5 opacity-50'}"
                        >
                            {#if !frame.unlocked}
                                <div class="absolute top-2 right-2">
                                    <Lock size={14} class="text-gray-500" />
                                </div>
                            {/if}
                            <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-neutral-700 {frame.css_class}"></div>
                            <div class="text-sm font-medium text-center">{frame.name}</div>
                            <div class="text-xs text-gray-500 text-center mt-1">{frame.description}</div>
                            <div class="text-xs mt-2 text-center {rarityColors[frame.rarity]}">{frame.rarity}</div>
                        </button>
                    {/each}
                </div>
                
            {:else if activeTab === 'badges'}
                <div>
                    <p class="text-sm text-gray-400 mb-3">Выберите до 3 бейджей для отображения в профиле</p>
                    <div class="grid grid-cols-2 gap-3">
                        {#each badges as badge}
                            {@const isSelected = selectedBadgeIds.includes(badge.id)}
                            <button
                                on:click={() => badge.unlocked && toggleBadge(badge.id)}
                                disabled={!badge.unlocked || (!isSelected && selectedBadgeIds.length >= 3)}
                                class="p-4 rounded-xl border transition-all relative {isSelected ? 'bg-amber-500/20 border-amber-500' : badge.unlocked ? 'bg-neutral-800 border-white/10 hover:border-white/30' : 'bg-neutral-900/50 border-white/5 opacity-50'}"
                            >
                                {#if !badge.unlocked}
                                    <div class="absolute top-2 right-2">
                                        <Lock size={14} class="text-gray-500" />
                                    </div>
                                {:else if isSelected}
                                    <div class="absolute top-2 right-2">
                                        <Check size={14} class="text-amber-500" />
                                    </div>
                                {/if}
                                <div class="w-10 h-10 mx-auto mb-2 rounded-full flex items-center justify-center {rarityColors[badge.rarity]}">
                                    <svelte:component this={iconMap[badge.icon] || Star} size={20} />
                                </div>
                                <div class="text-sm font-medium text-center">{badge.name}</div>
                                <div class="text-xs text-gray-500 text-center mt-1">{badge.description}</div>
                            </button>
                        {/each}
                    </div>
                </div>
            {/if}
            
            <!-- Messages -->
            {#if error}
                <div class="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                    {error}
                </div>
            {/if}
            {#if success}
                <div class="mt-4 p-3 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 text-sm">
                    {success}
                </div>
            {/if}
            
            <!-- Save Button - Safe area on mobile -->
            <div class="fixed bottom-0 left-0 right-0 p-4 pb-[max(1rem,env(safe-area-inset-bottom))] bg-neutral-900/95 backdrop-blur-md border-t border-white/10">
                <div class="max-w-2xl mx-auto">
                    <button
                        on:click={saveProfile}
                        disabled={saving}
                        class="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 text-black font-bold rounded-xl transition-colors flex items-center justify-center gap-2 active:scale-[0.98]"
                    >
                        {#if saving}
                            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                        {:else}
                            <Save size={20} />
                            Сохранить
                        {/if}
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>
