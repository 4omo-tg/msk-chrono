<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPostFormData, apiPost, isAuthenticated } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount, onDestroy } from "svelte";
    import {
        Clock, Upload, Sparkles, ArrowLeft, Image, Loader2,
        CheckCircle, XCircle, RefreshCw, Gem, ToggleLeft, ToggleRight,
        History, ChevronDown, X, Download, Eye
    } from "lucide-svelte";

    // State
    let crystals = 0;
    let targetYear = 1950;
    let applyEraStyle = true;
    let selectedFile: File | null = null;
    let previewUrl: string | null = null;
    let generating = false;
    let currentPhoto: any = null;
    let history: any[] = [];
    let showHistory = false;
    let errorMsg = "";
    let pollTimer: ReturnType<typeof setInterval> | null = null;
    let viewPhoto: any = null;

    // Era descriptions
    const eraDescriptions: Record<string, { label: string; desc: string; color: string }> = {
        "1800": { label: "XIX век", desc: "Дагеротип, чёрно-белое фото", color: "text-stone-400" },
        "1900": { label: "Начало XX века", desc: "Сепия, зернистость, винтаж", color: "text-amber-700" },
        "1950": { label: "Середина XX века", desc: "Приглушённые цвета, плёнка", color: "text-teal-500" },
        "1970": { label: "70-е — 90-е", desc: "Тёплые тона, ретро-плёнка", color: "text-orange-400" },
        "2000": { label: "Современность", desc: "Цифровая фотография", color: "text-blue-400" },
    };

    function getEraInfo(year: number) {
        if (year < 1900) return eraDescriptions["1800"];
        if (year < 1950) return eraDescriptions["1900"];
        if (year < 1970) return eraDescriptions["1950"];
        if (year < 2000) return eraDescriptions["1970"];
        return eraDescriptions["2000"];
    }

    $: currentEra = getEraInfo(targetYear);

    // Year presets
    const yearPresets = [
        { year: 1850, label: "1850" },
        { year: 1900, label: "1900" },
        { year: 1930, label: "1930" },
        { year: 1950, label: "1950" },
        { year: 1970, label: "1970" },
        { year: 1985, label: "1985" },
        { year: 2000, label: "2000" },
        { year: 2024, label: "2024" },
    ];

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }
        await loadBalance();
        await loadHistory();
    });

    onDestroy(() => {
        if (pollTimer) clearInterval(pollTimer);
    });

    async function loadBalance() {
        try {
            const res = await apiGet("/api/v1/time-machine/balance");
            if (res.ok) {
                const data = await res.json();
                crystals = data.chrono_crystals;
            }
        } catch (e) {
            console.error("Failed to load balance", e);
        }
    }

    async function loadHistory() {
        try {
            const res = await apiGet("/api/v1/time-machine/history?per_page=50");
            if (res.ok) {
                const data = await res.json();
                history = data.items;
            }
        } catch (e) {
            console.error("Failed to load history", e);
        }
    }

    function onFileSelect(event: Event) {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            previewUrl = URL.createObjectURL(selectedFile);
        }
    }

    function clearFile() {
        selectedFile = null;
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        previewUrl = null;
    }

    async function generate() {
        if (!selectedFile || generating) return;
        if (crystals < 1) {
            errorMsg = "Недостаточно Хроно-кристаллов!";
            return;
        }
        errorMsg = "";
        generating = true;
        currentPhoto = null;

        try {
            const formData = new FormData();
            formData.append("file", selectedFile);
            formData.append("target_year", targetYear.toString());
            formData.append("apply_era_style", applyEraStyle.toString());

            const res = await apiPostFormData("/api/v1/time-machine/generate", formData);
            if (!res.ok) {
                const err = await res.json();
                errorMsg = err.detail || "Ошибка генерации";
                generating = false;
                return;
            }

            currentPhoto = await res.json();
            crystals = Math.max(0, crystals - 1);

            // Start polling if processing
            if (currentPhoto.status === "processing") {
                startPolling(currentPhoto.id);
            } else {
                generating = false;
            }
        } catch (e: any) {
            errorMsg = e.message || "Ошибка сети";
            generating = false;
        }
    }

    function startPolling(photoId: number) {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(async () => {
            try {
                const res = await apiPost(`/api/v1/time-machine/check/${photoId}`);
                if (res.ok) {
                    currentPhoto = await res.json();
                    if (currentPhoto.status === "completed" || currentPhoto.status === "failed") {
                        if (pollTimer) clearInterval(pollTimer);
                        pollTimer = null;
                        generating = false;
                        await loadHistory();
                        await loadBalance();
                    }
                }
            } catch (e) {
                console.error("Poll error", e);
            }
        }, 3000);
    }

    function getStatusIcon(status: string) {
        switch (status) {
            case "completed": return CheckCircle;
            case "failed": return XCircle;
            case "processing": return Loader2;
            default: return Clock;
        }
    }

    function getStatusColor(status: string) {
        switch (status) {
            case "completed": return "text-green-400";
            case "failed": return "text-red-400";
            case "processing": return "text-amber-400";
            default: return "text-gray-400";
        }
    }

    function getStatusText(status: string) {
        switch (status) {
            case "completed": return "Готово";
            case "failed": return "Ошибка";
            case "processing": return "Генерация...";
            default: return "Ожидание";
        }
    }

    function resolveImageUrl(url: string | null): string {
        if (!url) return "";
        if (url.startsWith("http")) return url;
        return API_BASE + url;
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-2xl mx-auto px-4 sm:px-6">
            <div class="flex justify-between items-center h-14">
                <div class="flex items-center gap-3">
                    <a href="#/dashboard" class="p-2 hover:bg-neutral-800 rounded-lg transition-colors">
                        <ArrowLeft size={20} />
                    </a>
                    <h1 class="text-xl font-bold bg-gradient-to-r from-violet-400 to-purple-600 bg-clip-text text-transparent flex items-center gap-2">
                        <Clock size={22} class="text-violet-400" />
                        Машина Времени
                    </h1>
                </div>
                <div class="flex items-center gap-3">
                    <!-- Crystal balance -->
                    <div class="flex items-center gap-1.5 px-3 py-1.5 bg-violet-500/10 border border-violet-500/30 rounded-full">
                        <Gem size={16} class="text-violet-400" />
                        <span class="text-sm font-bold text-violet-300">{crystals}</span>
                    </div>
                    <button
                        on:click={() => { showHistory = !showHistory; }}
                        class="p-2 hover:bg-neutral-800 rounded-lg transition-colors"
                        title="История"
                    >
                        <History size={20} />
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-2xl mx-auto px-4 sm:px-6 py-4 sm:py-6 space-y-4">
        <!-- Intro card -->
        <div class="bg-gradient-to-br from-violet-900/30 to-purple-900/20 rounded-xl border border-violet-500/20 p-4">
            <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center flex-shrink-0">
                    <Sparkles size={20} class="text-violet-400" />
                </div>
                <div>
                    <h2 class="font-semibold text-white">Путешествие во времени для ваших фото</h2>
                    <p class="text-sm text-gray-400 mt-1">
                        Загрузите фотографию и выберите год — ИИ перенесёт её в нужную эпоху. 
                        Фото станет чёрно-белым для 1800-х, сепия для 1900-х, или в стиле ретро-плёнки для 70-х!
                    </p>
                </div>
            </div>
        </div>

        <!-- Upload area -->
        <div class="bg-neutral-800 rounded-xl border border-white/10 p-4 space-y-4">
            <h3 class="text-sm font-medium text-gray-300 uppercase tracking-wide">1. Загрузите фото</h3>
            
            {#if previewUrl}
                <div class="relative">
                    <img src={previewUrl} alt="Preview" class="w-full max-h-64 object-contain rounded-lg bg-neutral-900" />
                    <button
                        on:click={clearFile}
                        class="absolute top-2 right-2 p-1.5 bg-black/60 hover:bg-black/80 rounded-full transition-colors"
                    >
                        <X size={16} />
                    </button>
                </div>
            {:else}
                <label class="block cursor-pointer">
                    <div class="border-2 border-dashed border-white/10 hover:border-violet-500/50 rounded-lg p-8 text-center transition-colors">
                        <Upload size={32} class="mx-auto text-gray-500 mb-3" />
                        <p class="text-gray-400 text-sm">Нажмите или перетащите фото</p>
                        <p class="text-gray-600 text-xs mt-1">JPG, PNG до 10 МБ</p>
                    </div>
                    <input type="file" accept="image/*" class="hidden" on:change={onFileSelect} />
                </label>
            {/if}
        </div>

        <!-- Year selector -->
        <div class="bg-neutral-800 rounded-xl border border-white/10 p-4 space-y-4">
            <h3 class="text-sm font-medium text-gray-300 uppercase tracking-wide">2. Выберите год</h3>
            
            <!-- Year slider -->
            <div class="space-y-2">
                <div class="flex justify-between items-center">
                    <span class="text-3xl font-bold text-white">{targetYear}</span>
                    <span class="text-sm {currentEra.color}">{currentEra.label}</span>
                </div>
                <input
                    type="range"
                    bind:value={targetYear}
                    min="1800"
                    max="2030"
                    step="1"
                    class="w-full h-2 bg-neutral-700 rounded-full appearance-none cursor-pointer
                           [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                           [&::-webkit-slider-thumb]:bg-violet-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer
                           [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-violet-500/30"
                />
                <div class="flex justify-between text-xs text-gray-600">
                    <span>1800</span>
                    <span>1900</span>
                    <span>1950</span>
                    <span>2000</span>
                    <span>2030</span>
                </div>
            </div>

            <!-- Quick presets -->
            <div class="flex flex-wrap gap-2">
                {#each yearPresets as preset}
                    <button
                        on:click={() => targetYear = preset.year}
                        class="px-3 py-1.5 text-xs rounded-full transition-all
                               {targetYear === preset.year 
                                   ? 'bg-violet-500 text-white shadow-lg shadow-violet-500/30' 
                                   : 'bg-neutral-700 text-gray-400 hover:bg-neutral-600'}"
                    >
                        {preset.label}
                    </button>
                {/each}
            </div>

            <!-- Era style preview -->
            {#if applyEraStyle}
                <div class="bg-neutral-900/50 rounded-lg p-3 border border-white/5">
                    <p class="text-xs text-gray-500">Стиль эпохи:</p>
                    <p class="text-sm {currentEra.color} font-medium">{currentEra.desc}</p>
                </div>
            {/if}
        </div>

        <!-- Era style toggle -->
        <div class="bg-neutral-800 rounded-xl border border-white/10 p-4">
            <h3 class="text-sm font-medium text-gray-300 uppercase tracking-wide mb-3">3. Стиль обработки</h3>
            
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-white font-medium">Стиль эпохи</p>
                    <p class="text-xs text-gray-500 mt-0.5">
                        {applyEraStyle 
                            ? "Фото будет стилизовано под эпоху (ч/б, сепия, ретро...)" 
                            : "Фото сохранит современное качество, изменится только сцена"}
                    </p>
                </div>
                <button
                    on:click={() => applyEraStyle = !applyEraStyle}
                    class="flex-shrink-0 p-1"
                >
                    {#if applyEraStyle}
                        <ToggleRight size={36} class="text-violet-400" />
                    {:else}
                        <ToggleLeft size={36} class="text-gray-500" />
                    {/if}
                </button>
            </div>
        </div>

        <!-- Generate button -->
        <button
            on:click={generate}
            disabled={!selectedFile || generating || crystals < 1}
            class="w-full py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-3
                   {!selectedFile || generating || crystals < 1
                       ? 'bg-neutral-700 text-gray-500 cursor-not-allowed'
                       : 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white shadow-lg shadow-violet-500/30 hover:shadow-violet-500/50'}"
        >
            {#if generating}
                <Loader2 size={22} class="animate-spin" />
                Генерация...
            {:else}
                <Sparkles size={22} />
                Перенести в {targetYear} год
                <span class="text-sm opacity-70 flex items-center gap-1">
                    (<Gem size={14} /> 1)
                </span>
            {/if}
        </button>

        {#if crystals < 1 && !generating}
            <p class="text-center text-sm text-red-400">
                Недостаточно кристаллов! Проходите маршруты и квизы, чтобы заработать.
            </p>
        {/if}

        {#if errorMsg}
            <div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">
                {errorMsg}
            </div>
        {/if}

        <!-- Current generation result -->
        {#if currentPhoto}
            <div class="bg-neutral-800 rounded-xl border border-white/10 p-4 space-y-3">
                <div class="flex items-center justify-between">
                    <h3 class="font-semibold text-white">Результат</h3>
                    <span class="flex items-center gap-1.5 text-sm {getStatusColor(currentPhoto.status)}">
                        <svelte:component this={getStatusIcon(currentPhoto.status)} size={16} class={currentPhoto.status === 'processing' ? 'animate-spin' : ''} />
                        {getStatusText(currentPhoto.status)}
                    </span>
                </div>

                {#if currentPhoto.status === "processing"}
                    <div class="text-center py-8">
                        <Loader2 size={48} class="mx-auto text-violet-400 animate-spin mb-3" />
                        <p class="text-gray-400">ИИ переносит фото в {currentPhoto.target_year} год...</p>
                        <p class="text-xs text-gray-600 mt-1">Обычно занимает 15-60 секунд</p>
                    </div>
                {:else if currentPhoto.status === "completed" && currentPhoto.result_image_url}
                    <div class="space-y-3">
                        <!-- Before / After -->
                        <div class="grid grid-cols-2 gap-2">
                            <div>
                                <p class="text-xs text-gray-500 mb-1 text-center">Оригинал</p>
                                <img src={resolveImageUrl(currentPhoto.original_image_url)} alt="Original" class="w-full rounded-lg" />
                            </div>
                            <div>
                                <p class="text-xs text-gray-500 mb-1 text-center">{currentPhoto.target_year} год</p>
                                <img src={currentPhoto.result_image_url} alt="Result" class="w-full rounded-lg" />
                            </div>
                        </div>
                        {#if currentPhoto.style_applied}
                            <p class="text-xs text-gray-500 text-center">Стиль: {currentPhoto.style_applied}</p>
                        {/if}
                    </div>
                {:else if currentPhoto.status === "failed"}
                    <div class="text-center py-4">
                        <XCircle size={32} class="mx-auto text-red-400 mb-2" />
                        <p class="text-red-400 text-sm">{currentPhoto.error_message || "Ошибка генерации"}</p>
                    </div>
                {/if}
            </div>
        {/if}

        <!-- History section -->
        {#if showHistory && history.length > 0}
            <div class="bg-neutral-800 rounded-xl border border-white/10 p-4 space-y-3">
                <h3 class="font-semibold text-white flex items-center gap-2">
                    <History size={18} />
                    История генераций
                </h3>
                <div class="space-y-2 max-h-[60vh] overflow-y-auto">
                    {#each history as photo}
                        <button
                            on:click={() => viewPhoto = photo}
                            class="w-full flex items-center gap-3 p-3 bg-neutral-900/50 rounded-lg hover:bg-neutral-700/50 transition-colors text-left"
                        >
                            <img 
                                src={resolveImageUrl(photo.original_image_url)} 
                                alt="" 
                                class="w-12 h-12 object-cover rounded-lg flex-shrink-0" 
                            />
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2">
                                    <span class="font-medium text-white">{photo.target_year}</span>
                                    <span class="text-xs {getStatusColor(photo.status)} flex items-center gap-1">
                                        <svelte:component this={getStatusIcon(photo.status)} size={12} />
                                        {getStatusText(photo.status)}
                                    </span>
                                </div>
                                <p class="text-xs text-gray-500 truncate">
                                    {photo.style_applied || (photo.apply_era_style ? "Стиль эпохи" : "Современное качество")}
                                </p>
                                <p class="text-xs text-gray-600">
                                    {new Date(photo.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>
                            {#if photo.result_image_url}
                                <img 
                                    src={photo.result_image_url} 
                                    alt="" 
                                    class="w-12 h-12 object-cover rounded-lg flex-shrink-0" 
                                />
                            {/if}
                        </button>
                    {/each}
                </div>
            </div>
        {:else if showHistory}
            <div class="bg-neutral-800 rounded-xl border border-white/10 p-8 text-center">
                <Clock size={32} class="mx-auto text-gray-600 mb-2" />
                <p class="text-gray-500">Пока нет генераций</p>
            </div>
        {/if}

        <!-- How to earn crystals -->
        <div class="bg-neutral-800/50 rounded-xl border border-white/5 p-4">
            <h3 class="text-sm font-medium text-gray-400 mb-3 flex items-center gap-2">
                <Gem size={16} class="text-violet-400" />
                Как заработать Хроно-кристаллы
            </h3>
            <ul class="space-y-2 text-sm text-gray-500">
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    Завершайте маршруты — +1 кристалл
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    Проходите квизы без ошибок — +1 кристалл
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    Ежедневная серия (streak) — +1 кристалл
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    Достижения — до +3 кристаллов
                </li>
            </ul>
        </div>
    </div>
</div>

<!-- View Photo Modal -->
{#if viewPhoto}
    <div 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        on:click={() => viewPhoto = null}
        on:keydown={(e) => e.key === 'Escape' && (viewPhoto = null)}
        role="dialog"
        tabindex="-1"
    >
        <div 
            class="bg-neutral-900 border border-white/10 rounded-2xl p-4 max-w-lg w-full shadow-2xl max-h-[90vh] overflow-y-auto"
            on:click|stopPropagation
        >
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-bold text-white">{viewPhoto.target_year} год</h3>
                <button on:click={() => viewPhoto = null} class="text-gray-500 hover:text-white">
                    <X size={20} />
                </button>
            </div>

            {#if viewPhoto.status === "completed" && viewPhoto.result_image_url}
                <div class="space-y-3">
                    <div>
                        <p class="text-xs text-gray-500 mb-1">Оригинал</p>
                        <img src={resolveImageUrl(viewPhoto.original_image_url)} alt="Original" class="w-full rounded-lg" />
                    </div>
                    <div>
                        <p class="text-xs text-gray-500 mb-1">Результат — {viewPhoto.target_year}</p>
                        <img src={viewPhoto.result_image_url} alt="Result" class="w-full rounded-lg" />
                    </div>
                </div>
            {:else}
                <img src={resolveImageUrl(viewPhoto.original_image_url)} alt="Original" class="w-full rounded-lg" />
            {/if}

            <div class="mt-3 text-xs text-gray-500 space-y-1">
                <p>Стиль: {viewPhoto.style_applied || "—"}</p>
                <p>Статус: {getStatusText(viewPhoto.status)}</p>
                <p>Стоимость: {viewPhoto.cost} <Gem size={10} class="inline text-violet-400" /></p>
            </div>
        </div>
    </div>
{/if}

<style>
    input[type="range"]::-webkit-slider-thumb {
        -webkit-appearance: none;
        appearance: none;
        width: 20px;
        height: 20px;
        background: #8b5cf6;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
    }
    input[type="range"]::-moz-range-thumb {
        width: 20px;
        height: 20px;
        background: #8b5cf6;
        border-radius: 50%;
        cursor: pointer;
        border: none;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
    }
</style>
