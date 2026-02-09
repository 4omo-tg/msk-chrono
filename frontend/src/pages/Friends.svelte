<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPost, apiDelete, isAuthenticated } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";
    import {
        Users, UserPlus, Search, Check, X, ArrowLeft, User,
        Clock, Send, Inbox, ChevronRight, Map
    } from "lucide-svelte";

    let friends: any[] = [];
    let incomingRequests: any[] = [];
    let outgoingRequests: any[] = [];
    let searchResults: any[] = [];
    let searchQuery = "";
    let loading = true;
    let searching = false;
    let activeTab = "friends";
    let counts = { friends: 0, incoming_requests: 0, outgoing_requests: 0 };

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
            const [friendsRes, incomingRes, outgoingRes, countsRes] = await Promise.all([
                apiGet("/api/v1/friends/"),
                apiGet("/api/v1/friends/requests/incoming"),
                apiGet("/api/v1/friends/requests/outgoing"),
                apiGet("/api/v1/friends/count"),
            ]);
            
            if (friendsRes.ok) friends = await friendsRes.json();
            if (incomingRes.ok) incomingRequests = await incomingRes.json();
            if (outgoingRes.ok) outgoingRequests = await outgoingRes.json();
            if (countsRes.ok) counts = await countsRes.json();
        } catch (e) {
            console.error(e);
        }
        loading = false;
    }

    async function searchUsers() {
        if (searchQuery.length < 2) {
            searchResults = [];
            return;
        }
        searching = true;
        try {
            const res = await apiGet(`/api/v1/profile/search?q=${encodeURIComponent(searchQuery)}`);
            if (res.ok) searchResults = await res.json();
        } catch (e) {
            console.error(e);
        }
        searching = false;
    }

    async function sendFriendRequest(userId: number) {
        try {
            const res = await apiPost(`/api/v1/friends/request/${userId}`);
            if (res.ok) {
                await loadData();
                await searchUsers();
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function acceptRequest(requestId: number) {
        try {
            const res = await apiPost(`/api/v1/friends/accept/${requestId}`);
            if (res.ok) await loadData();
        } catch (e) {
            console.error(e);
        }
    }

    async function rejectRequest(requestId: number) {
        try {
            const res = await apiPost(`/api/v1/friends/reject/${requestId}`);
            if (res.ok) await loadData();
        } catch (e) {
            console.error(e);
        }
    }

    async function cancelRequest(requestId: number) {
        try {
            const res = await apiDelete(`/api/v1/friends/cancel/${requestId}`);
            if (res.ok) await loadData();
        } catch (e) {
            console.error(e);
        }
    }

    async function removeFriend(friendId: number) {
        if (!confirm("Удалить из друзей?")) return;
        try {
            const res = await apiDelete(`/api/v1/friends/${friendId}`);
            if (res.ok) await loadData();
        } catch (e) {
            console.error(e);
        }
    }
    
    function getAvatarUrl(url: string | null): string {
        if (!url) return '';
        return url.startsWith('/') ? API_BASE + url : url;
    }

    let searchTimeout: any;
    $: {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(searchUsers, 300);
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
            <a href="#/profile" class="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700">
                <ArrowLeft size={20} />
            </a>
            <h1 class="text-xl font-bold">Друзья</h1>
            <div class="flex-1"></div>
            <a href="#/dashboard" class="p-2 rounded-lg bg-neutral-800 hover:bg-neutral-700" title="Дашборд">
                <Map size={20} />
            </a>
        </div>
    </header>

    <div class="max-w-2xl mx-auto px-4 py-4">

        <!-- Search -->
        <div class="relative mb-6">
            <Search size={18} class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
                type="text"
                bind:value={searchQuery}
                placeholder="Найти пользователей..."
                class="w-full bg-neutral-800 border border-white/10 rounded-xl pl-10 pr-4 py-3 focus:border-amber-500 focus:outline-none"
            />
            {#if searching}
                <div class="absolute right-3 top-1/2 -translate-y-1/2">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-500"></div>
                </div>
            {/if}
        </div>

        <!-- Search Results -->
        {#if searchQuery.length >= 2 && searchResults.length > 0}
            <div class="bg-neutral-800 rounded-xl border border-white/10 mb-6 overflow-hidden">
                <div class="p-3 border-b border-white/10">
                    <p class="text-sm text-gray-400">Результаты поиска</p>
                </div>
                {#each searchResults as user}
                    <div class="flex items-center justify-between p-3 hover:bg-neutral-700/50 transition-colors">
                        <a href="#/user/{user.id}" class="flex items-center gap-3 flex-1">
                            <div class="w-10 h-10 rounded-full bg-neutral-700 overflow-hidden">
                                {#if user.avatar_url}
                                    <img src="{getAvatarUrl(user.avatar_url)}" alt="" class="w-full h-full object-cover" />
                                {:else}
                                    <div class="w-full h-full flex items-center justify-center">
                                        <User size={20} class="text-gray-500" />
                                    </div>
                                {/if}
                            </div>
                            <div>
                                <div class="font-medium">{user.display_name || user.username}</div>
                                <div class="text-xs text-gray-500">@{user.username} • Ур. {user.level}</div>
                            </div>
                        </a>
                        {#if user.is_friend}
                            <span class="text-xs text-green-400 px-2 py-1 bg-green-500/10 rounded-full">Друг</span>
                        {:else}
                            <button
                                on:click={() => sendFriendRequest(user.id)}
                                class="p-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg transition-colors"
                            >
                                <UserPlus size={16} />
                            </button>
                        {/if}
                    </div>
                {/each}
            </div>
        {:else if searchQuery.length >= 2 && !searching}
            <div class="text-center text-gray-500 mb-6 py-4">Никого не найдено</div>
        {/if}

        <!-- Tabs - Scrollable on mobile -->
        <div class="flex gap-2 mb-4 overflow-x-auto pb-2 -mx-4 px-4 scrollbar-hide">
            <button
                on:click={() => activeTab = 'friends'}
                class="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap transition-colors text-sm sm:text-base {activeTab === 'friends' ? 'bg-amber-500 text-black' : 'bg-neutral-800 hover:bg-neutral-700'}"
            >
                <Users size={16} />
                <span class="hidden xs:inline">Друзья</span>
                {#if counts.friends > 0}
                    <span class="text-xs bg-black/20 px-1.5 py-0.5 rounded-full">{counts.friends}</span>
                {/if}
            </button>
            <button
                on:click={() => activeTab = 'incoming'}
                class="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap transition-colors text-sm sm:text-base {activeTab === 'incoming' ? 'bg-amber-500 text-black' : 'bg-neutral-800 hover:bg-neutral-700'}"
            >
                <Inbox size={16} />
                <span class="hidden xs:inline">Входящие</span>
                {#if counts.incoming_requests > 0}
                    <span class="text-xs bg-red-500 px-1.5 py-0.5 rounded-full text-white">{counts.incoming_requests}</span>
                {/if}
            </button>
            <button
                on:click={() => activeTab = 'outgoing'}
                class="flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg whitespace-nowrap transition-colors text-sm sm:text-base {activeTab === 'outgoing' ? 'bg-amber-500 text-black' : 'bg-neutral-800 hover:bg-neutral-700'}"
            >
                <Send size={16} />
                <span class="hidden xs:inline">Исходящие</span>
                {#if counts.outgoing_requests > 0}
                    <span class="text-xs bg-black/20 px-1.5 py-0.5 rounded-full">{counts.outgoing_requests}</span>
                {/if}
            </button>
        </div>

        {#if loading}
            <div class="flex items-center justify-center h-40">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </div>
        {:else}
            <!-- Friends List -->
            {#if activeTab === 'friends'}
                {#if friends.length === 0}
                    <div class="text-center py-12 text-gray-500">
                        <Users size={48} class="mx-auto mb-4 opacity-50" />
                        <p>У вас пока нет друзей</p>
                        <p class="text-sm mt-1">Найдите пользователей через поиск</p>
                    </div>
                {:else}
                    <div class="space-y-2">
                        {#each friends as friend}
                            <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                                <div class="flex items-center justify-between">
                                    <a href="#/user/{friend.friend_id}" class="flex items-center gap-3 flex-1">
                                        <div class="w-12 h-12 rounded-full bg-neutral-700 overflow-hidden">
                                            {#if friend.friend_avatar_url}
                                                <img src="{getAvatarUrl(friend.friend_avatar_url)}" alt="" class="w-full h-full object-cover" />
                                            {:else}
                                                <div class="w-full h-full flex items-center justify-center">
                                                    <User size={24} class="text-gray-500" />
                                                </div>
                                            {/if}
                                        </div>
                                        <div>
                                            <div class="font-medium">{friend.nickname || friend.friend_display_name || friend.friend_username}</div>
                                            <div class="text-xs text-gray-500">@{friend.friend_username} • Ур. {friend.friend_level}</div>
                                            <div class="text-xs text-amber-500">{Math.floor(friend.friend_xp)} XP</div>
                                        </div>
                                    </a>
                                    <div class="flex items-center gap-2">
                                        <button
                                            on:click={() => removeFriend(friend.friend_id)}
                                            class="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                                            title="Удалить"
                                        >
                                            <X size={16} />
                                        </button>
                                        <ChevronRight size={16} class="text-gray-500" />
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}

            <!-- Incoming Requests -->
            {:else if activeTab === 'incoming'}
                {#if incomingRequests.length === 0}
                    <div class="text-center py-12 text-gray-500">
                        <Inbox size={48} class="mx-auto mb-4 opacity-50" />
                        <p>Нет входящих заявок</p>
                    </div>
                {:else}
                    <div class="space-y-2">
                        {#each incomingRequests as request}
                            <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                                <div class="flex items-center justify-between">
                                    <a href="#/user/{request.from_user_id}" class="flex items-center gap-3 flex-1">
                                        <div class="w-12 h-12 rounded-full bg-neutral-700 overflow-hidden">
                                            {#if request.from_user_avatar_url}
                                                <img src="{getAvatarUrl(request.from_user_avatar_url)}" alt="" class="w-full h-full object-cover" />
                                            {:else}
                                                <div class="w-full h-full flex items-center justify-center">
                                                    <User size={24} class="text-gray-500" />
                                                </div>
                                            {/if}
                                        </div>
                                        <div>
                                            <div class="font-medium">{request.from_user_display_name || request.from_user_username}</div>
                                            <div class="text-xs text-gray-500">@{request.from_user_username} • Ур. {request.from_user_level}</div>
                                        </div>
                                    </a>
                                    <div class="flex gap-2">
                                        <button
                                            on:click={() => acceptRequest(request.id)}
                                            class="p-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
                                        >
                                            <Check size={16} />
                                        </button>
                                        <button
                                            on:click={() => rejectRequest(request.id)}
                                            class="p-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
                                        >
                                            <X size={16} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}

            <!-- Outgoing Requests -->
            {:else if activeTab === 'outgoing'}
                {#if outgoingRequests.length === 0}
                    <div class="text-center py-12 text-gray-500">
                        <Send size={48} class="mx-auto mb-4 opacity-50" />
                        <p>Нет исходящих заявок</p>
                    </div>
                {:else}
                    <div class="space-y-2">
                        {#each outgoingRequests as request}
                            <div class="bg-neutral-800 rounded-xl p-4 border border-white/10">
                                <div class="flex items-center justify-between">
                                    <a href="#/user/{request.to_user_id}" class="flex items-center gap-3 flex-1">
                                        <div class="w-12 h-12 rounded-full bg-neutral-700 overflow-hidden">
                                            {#if request.to_user_avatar_url}
                                                <img src="{getAvatarUrl(request.to_user_avatar_url)}" alt="" class="w-full h-full object-cover" />
                                            {:else}
                                                <div class="w-full h-full flex items-center justify-center">
                                                    <User size={24} class="text-gray-500" />
                                                </div>
                                            {/if}
                                        </div>
                                        <div>
                                            <div class="font-medium">{request.to_user_display_name || request.to_user_username}</div>
                                            <div class="text-xs text-gray-500">@{request.to_user_username} • Ур. {request.to_user_level}</div>
                                            <div class="text-xs text-amber-400 flex items-center gap-1">
                                                <Clock size={10} />
                                                Ожидает ответа
                                            </div>
                                        </div>
                                    </a>
                                    <button
                                        on:click={() => cancelRequest(request.id)}
                                        class="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                                        title="Отменить"
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            {/if}
        {/if}
    </div>
</div>
