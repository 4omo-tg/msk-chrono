<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { apiGet, apiPostFormData, apiPost, isAuthenticated } from "../lib/api";
    import { push } from "svelte-spa-router";
    import { onMount, onDestroy } from "svelte";
    import {
        Clock, Upload, Sparkles, ArrowLeft, Image, Loader2,
        CheckCircle, XCircle, RefreshCw, Gem, ToggleLeft, ToggleRight,
        History, ChevronDown, X, Download, Eye, Settings, Shirt, Building2, Camera
    } from "lucide-svelte";

    // State
    let crystals = 0;
    let targetYear = 1950;
    let selectedMode = "full_vintage";
    let modes: {id: string, name: string, desc: string}[] = [
        {id: "clothing_only", name: "Только одежда", desc: "Изменить только одежду людей"},
        {id: "full", name: "Полная трансформация", desc: "Одежда + архитектура"},
        {id: "full_vintage", name: "Полная + винтаж", desc: "+ стиль фото эпохи"}
    ];
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
        "1800": { label: "Начало XIX века", desc: "Гравюра, акватинта, сепия", color: "text-amber-800" },
        "1850": { label: "Середина XIX века", desc: "Дагеротип, серебряное зерно", color: "text-stone-400" },
        "1900": { label: "Начало XX века", desc: "Сепия, сухие пластины", color: "text-amber-600" },
        "1950": { label: "СССР 1950-х", desc: "Ч/б, плёнка Свема", color: "text-teal-500" },
        "1985": { label: "Поздний СССР", desc: "Цветная плёнка Тасма", color: "text-orange-400" },
        "2000": { label: "2000-е", desc: "Ранняя цифра, JPEG", color: "text-blue-400" },
        "2024": { label: "Современность", desc: "Цифровая фотография", color: "text-indigo-400" },
        "2077": { label: "Будущее", desc: "Киберпанк, неон, голограммы", color: "text-cyan-400" },
    };

    function getEraInfo(year: number) {
        if (year < 1850) return eraDescriptions["1800"];
        if (year < 1900) return eraDescriptions["1850"];
        if (year < 1950) return eraDescriptions["1900"];
        if (year < 1980) return eraDescriptions["1950"];
        if (year < 2005) return eraDescriptions["1985"];
        if (year < 2025) return eraDescriptions["2000"];
        if (year > 2050) return eraDescriptions["2077"];
        return eraDescriptions["2024"];
    }

    $: currentEra = getEraInfo(targetYear);

    // Year presets
    const yearPresets = [
        { year: 1800, label: "1800" },
        { year: 1850, label: "1850" },
        { year: 1900, label: "1900" },
        { year: 1950, label: "1950" },
        { year: 1985, label: "1985" },
        { year: 2000, label: "2000" },
        { year: 2024, label: "2024" },
        { year: 2077, label: "2077" },
    ];

    // Mode icons
    function getModeIcon(modeId: string) {
        switch (modeId) {
            case "clothing_only": return Shirt;
            case "full": return Building2;
            case "full_vintage": return Camera;
            default: return Sparkles;
        }
    }

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }
        await loadBalance();
        await loadConfig();
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

    async function loadConfig() {
        try {
            const res = await apiGet("/api/v1/time-machine/config");
            if (res.ok) {
                const data = await res.json();
                if (data.modes && data.modes.length > 0) {
                    modes = data.modes;
                }
                if (data.mode) {
                    selectedMode = data.mode;
                }
            }
        } catch (e) {
            console.error("Failed to load config", e);
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
            formData.append("mode", selectedMode);
            formData.append("apply_era_style", (selectedMode === "full_vintage").toString());

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

    function getModeLabel(modeId: string): string {
        const m = modes.find(x => x.id === modeId);
        return m ? m.name : modeId;
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
                        Загрузите фотографию, выберите год и режим трансформации — ИИ перенесёт её в нужную эпоху!
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
                    max="2077"
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
                    <span>2077</span>
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
            {#if selectedMode === "full_vintage"}
                <div class="bg-neutral-900/50 rounded-lg p-3 border border-white/5">
                    <p class="text-xs text-gray-500">Стиль эпохи:</p>
                    <p class="text-sm {currentEra.color} font-medium">{currentEra.desc}</p>
                </div>
            {/if}
        </div>

        <!-- Mode selector -->
        <div class="bg-neutral-800 rounded-xl border border-white/10 p-4 space-y-4">
            <h3 class="text-sm font-medium text-gray-300 uppercase tracking-wide">3. Режим трансформации</h3>
            
            <div class="grid gap-2">
                {#each modes as mode}
                    {@const ModeIcon = getModeIcon(mode.id)}
                    <button
                        on:click={() => selectedMode = mode.id}
                        class="flex items-center gap-3 p-3 rounded-lg border transition-all text-left
                               {selectedMode === mode.id 
                                   ? 'bg-violet-500/20 border-violet-500/50 shadow-lg shadow-violet-500/10' 
                                   : 'bg-neutral-900/50 border-white/5 hover:border-white/20'}"
                    >
                        <div class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                                    {selectedMode === mode.id ? 'bg-violet-500/30' : 'bg-neutral-700'}">
                            <svelte:component this={ModeIcon} size={20} class={selectedMode === mode.id ? 'text-violet-400' : 'text-gray-400'} />
                        </div>
                        <div class="flex-1">
                            <p class="font-medium {selectedMode === mode.id ? 'text-white' : 'text-gray-300'}">
                                {mode.name}
                            </p>
                            <p class="text-xs {selectedMode === mode.id ? 'text-violet-300' : 'text-gray-500'}">
                                {mode.desc}
                            </p>
                        </div>
                        {#if selectedMode === mode.id}
                            <CheckCircle size={20} class="text-violet-400 flex-shrink-0" />
                        {/if}
                    </button>
                {/each}
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
                        <!-- Result only -->
                        <div class="relative">
                            <p class="text-xs text-gray-500 mb-2 text-center">{currentPhoto.target_year} год</p>
                            <img src={currentPhoto.result_image_url} alt="Result" class="w-full rounded-xl" />
                            <!-- Download button -->
                            <a 
                                href={currentPhoto.result_image_url} 
                                download="time-machine-{currentPhoto.target_year}.jpg"
                                target="_blank"
                                class="absolute bottom-3 right-3 p-2.5 bg-black/60 hover:bg-black/80 rounded-full transition-colors"
                                title="Скачать"
                            >
                                <Download size={18} class="text-white" />
                            </a>
                        </div>
                        {#if currentPhoto.style_applied}
                            <p class="text-xs text-gray-500 text-center">Режим: {currentPhoto.style_applied}</p>
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
                            {#if photo.result_image_url}
                                <img 
                                    src={photo.result_image_url} 
                                    alt="" 
                                    class="w-14 h-14 object-cover rounded-lg flex-shrink-0" 
                                />
                            {:else}
                                <div class="w-14 h-14 bg-neutral-700 rounded-lg flex-shrink-0 flex items-center justify-center">
                                    <svelte:component this={getStatusIcon(photo.status)} size={20} class="{getStatusColor(photo.status)} {photo.status === 'processing' ? 'animate-spin' : ''}" />
                                </div>
                            {/if}
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2">
                                    <span class="font-medium text-white">{photo.target_year} год</span>
                                    <span class="text-xs {getStatusColor(photo.status)} flex items-center gap-1">
                                        <svelte:component this={getStatusIcon(photo.status)} size={12} />
                                        {getStatusText(photo.status)}
                                    </span>
                                </div>
                                <p class="text-xs text-gray-500 truncate">
                                    {photo.style_applied || getModeLabel(photo.transformation_mode || "full_vintage")}
                                </p>
                                <p class="text-xs text-gray-600">
                                    {new Date(photo.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>
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
                    Завершите маршрут — +1 кристалл (+2 за сложный)
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    Каждые 5 правильных квизов — +1 кристалл
                </li>
                <li class="flex items-center gap-2">
                    <span class="w-1 h-1 bg-violet-400 rounded-full"></span>
                    При ошибке генерации кристалл возвращается
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
                <div class="relative">
                    <img src={viewPhoto.result_image_url} alt="Result" class="w-full rounded-xl" />
                    <a 
                        href={viewPhoto.result_image_url} 
                        download="time-machine-{viewPhoto.target_year}.jpg"
                        target="_blank"
                        class="absolute bottom-3 right-3 p-2.5 bg-black/60 hover:bg-black/80 rounded-full transition-colors"
                        title="Скачать"
                    >
                        <Download size={18} class="text-white" />
                    </a>
                </div>
                <div class="mt-3 text-xs text-gray-500 space-y-1">
                    <p>Режим: {viewPhoto.style_applied || "—"}</p>
                </div>
            {:else if viewPhoto.status === "processing"}
                <div class="text-center py-12">
                    <Loader2 size={48} class="mx-auto text-violet-400 animate-spin mb-3" />
                    <p class="text-gray-400">Генерация в процессе...</p>
                </div>
            {:else if viewPhoto.status === "failed"}
                <div class="text-center py-8">
                    <XCircle size={48} class="mx-auto text-red-400 mb-3" />
                    <p class="text-red-400">Ошибка генерации</p>
                    <p class="text-xs text-gray-500 mt-2">{viewPhoto.error_message || ''}</p>
                    <p class="text-xs text-green-400 mt-2">Кристалл возвращён</p>
                </div>
            {/if}
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
