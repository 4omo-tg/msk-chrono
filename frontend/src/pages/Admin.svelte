<script lang="ts">
    import { onMount } from "svelte";
    import { push } from "svelte-spa-router";
    import { apiGet, apiPostFormData, apiPost, apiDelete, isAuthenticated } from "../lib/api";
    import { API_BASE } from "../lib/config";
    import {
        ArrowLeft, MapPin, Plus, Upload, Trash2, Image, Calendar,
        ChevronDown, ChevronUp, X, Check, Loader2, Edit, Save, Settings
    } from "lucide-svelte";

    interface POIPhoto {
        id: number;
        poi_id: number;
        year: number;
        image_url: string;
        description: string | null;
        source: string | null;
    }

    interface POI {
        id: number;
        title: string;
        description: string | null;
        address: string | null;
        latitude: number;
        longitude: number;
        photos: POIPhoto[];
    }

    let pois: POI[] = [];
    let loading = true;
    let expandedPoi: number | null = null;
    let user: any = null;

    // Upload state
    let uploadingTo: number | null = null;
    let uploadYear = new Date().getFullYear();
    let uploadDescription = "";
    let uploadSource = "";
    let uploadFiles: FileList | null = null;
    let uploading = false;
    let uploadError = "";

    // New POI state
    let showNewPoi = false;
    let newPoi = {
        title: "",
        description: "",
        address: "",
        latitude: 55.7558,
        longitude: 37.6173
    };
    let creatingPoi = false;

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }
        
        // Check if superuser
        try {
            const res = await apiGet("/api/v1/users/me");
            if (res.ok) {
                user = await res.json();
                if (!user.is_superuser) {
                    push("/dashboard");
                    return;
                }
            } else {
                push("/register");
                return;
            }
        } catch {
            push("/register");
            return;
        }
        
        await loadPois();
    });

    async function loadPois() {
        loading = true;
        try {
            const res = await apiGet("/api/v1/pois?limit=1000");
            if (res.ok) {
                pois = await res.json();
            }
        } catch (e) {
            console.error("Failed to load POIs", e);
        } finally {
            loading = false;
        }
    }

    function toggleExpand(poiId: number) {
        expandedPoi = expandedPoi === poiId ? null : poiId;
        uploadingTo = null;
        uploadError = "";
    }

    function startUpload(poiId: number) {
        uploadingTo = poiId;
        uploadYear = new Date().getFullYear();
        uploadDescription = "";
        uploadSource = "";
        uploadFiles = null;
        uploadError = "";
    }

    function cancelUpload() {
        uploadingTo = null;
        uploadFiles = null;
        uploadError = "";
    }

    async function doUpload() {
        if (!uploadingTo || !uploadFiles || uploadFiles.length === 0) return;
        
        uploading = true;
        uploadError = "";
        
        try {
            const formData = new FormData();
            formData.append("year", uploadYear.toString());
            if (uploadDescription) formData.append("description", uploadDescription);
            if (uploadSource) formData.append("source", uploadSource);
            
            for (let i = 0; i < uploadFiles.length; i++) {
                formData.append("files", uploadFiles[i]);
            }
            
            const res = await apiPostFormData(`/api/v1/pois/${uploadingTo}/photos/upload-gallery`, formData);
            
            if (!res.ok) {
                const err = await res.json();
                uploadError = err.detail || "Ошибка загрузки";
            } else {
                // Reload POIs to see new photos
                await loadPois();
                cancelUpload();
            }
        } catch (e: any) {
            uploadError = e.message || "Ошибка сети";
        } finally {
            uploading = false;
        }
    }

    async function deletePhoto(poiId: number, photoId: number) {
        if (!confirm("Удалить фото?")) return;
        
        try {
            const res = await apiDelete(`/api/v1/pois/${poiId}/photos/${photoId}`);
            if (res.ok) {
                await loadPois();
            }
        } catch (e) {
            console.error("Failed to delete photo", e);
        }
    }

    async function createPoi() {
        if (!newPoi.title.trim()) return;
        
        creatingPoi = true;
        try {
            const res = await apiPost("/api/v1/pois", newPoi);
            if (res.ok) {
                await loadPois();
                showNewPoi = false;
                newPoi = { title: "", description: "", address: "", latitude: 55.7558, longitude: 37.6173 };
            }
        } catch (e) {
            console.error("Failed to create POI", e);
        } finally {
            creatingPoi = false;
        }
    }

    async function deletePoi(poiId: number) {
        if (!confirm("Удалить точку интереса и все её фото?")) return;
        
        try {
            const res = await apiDelete(`/api/v1/pois/${poiId}`);
            if (res.ok) {
                await loadPois();
            }
        } catch (e) {
            console.error("Failed to delete POI", e);
        }
    }

    function resolveUrl(url: string): string {
        if (!url) return "";
        if (url.startsWith("http")) return url;
        return API_BASE + url;
    }

    // Group photos by year
    function groupByYear(photos: POIPhoto[]): Map<number, POIPhoto[]> {
        const map = new Map<number, POIPhoto[]>();
        for (const p of photos) {
            if (!map.has(p.year)) map.set(p.year, []);
            map.get(p.year)!.push(p);
        }
        return new Map([...map.entries()].sort((a, b) => a[0] - b[0]));
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-4xl mx-auto px-4 sm:px-6">
            <div class="flex justify-between items-center h-14">
                <div class="flex items-center gap-3">
                    <a href="#/dashboard" class="p-2 hover:bg-neutral-800 rounded-lg transition-colors">
                        <ArrowLeft size={20} />
                    </a>
                    <h1 class="text-xl font-bold text-amber-500">Админка: Точки интереса</h1>
                </div>
                <div class="flex items-center gap-2">
                    <a
                        href="#/admin/settings"
                        class="flex items-center gap-2 px-3 py-2 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg font-medium text-sm transition-colors"
                    >
                        <Settings size={16} />
                        Настройки
                    </a>
                    <button
                        on:click={() => showNewPoi = true}
                        class="flex items-center gap-2 px-3 py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-lg font-medium text-sm transition-colors"
                    >
                        <Plus size={16} />
                        Добавить
                    </button>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-4">
        {#if loading}
            <div class="flex items-center justify-center py-20">
                <Loader2 size={32} class="animate-spin text-amber-500" />
            </div>
        {:else if pois.length === 0}
            <div class="text-center py-20">
                <MapPin size={48} class="mx-auto text-gray-600 mb-4" />
                <p class="text-gray-400">Точек интереса пока нет</p>
            </div>
        {:else}
            {#each pois as poi}
                <div class="bg-neutral-800 rounded-xl border border-white/10 overflow-hidden">
                    <!-- POI Header -->
                    <button
                        on:click={() => toggleExpand(poi.id)}
                        class="w-full flex items-center justify-between p-4 hover:bg-neutral-700/50 transition-colors text-left"
                    >
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                                <MapPin size={20} class="text-amber-500" />
                            </div>
                            <div>
                                <h3 class="font-semibold text-white">{poi.title}</h3>
                                <p class="text-xs text-gray-500">
                                    {poi.address || `${poi.latitude.toFixed(4)}, ${poi.longitude.toFixed(4)}`}
                                    • {poi.photos.length} фото
                                </p>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs text-gray-500">
                                {[...new Set(poi.photos.map(p => p.year))].length} годов
                            </span>
                            {#if expandedPoi === poi.id}
                                <ChevronUp size={20} class="text-gray-400" />
                            {:else}
                                <ChevronDown size={20} class="text-gray-400" />
                            {/if}
                        </div>
                    </button>

                    <!-- Expanded content -->
                    {#if expandedPoi === poi.id}
                        <div class="border-t border-white/10 p-4 space-y-4">
                            <!-- Actions -->
                            <div class="flex gap-2">
                                <button
                                    on:click={() => startUpload(poi.id)}
                                    class="flex items-center gap-2 px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium transition-colors"
                                >
                                    <Upload size={16} />
                                    Загрузить галерею
                                </button>
                                <button
                                    on:click={() => deletePoi(poi.id)}
                                    class="flex items-center gap-2 px-3 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg text-sm font-medium transition-colors"
                                >
                                    <Trash2 size={16} />
                                    Удалить POI
                                </button>
                            </div>

                            <!-- Upload form -->
                            {#if uploadingTo === poi.id}
                                <div class="bg-neutral-900 rounded-lg p-4 border border-green-500/30 space-y-3">
                                    <h4 class="font-medium text-green-400 flex items-center gap-2">
                                        <Upload size={16} />
                                        Загрузка фото за год
                                    </h4>
                                    
                                    <div class="grid grid-cols-2 gap-3">
                                        <div>
                                            <label class="text-xs text-gray-400 block mb-1">Год *</label>
                                            <input
                                                type="number"
                                                bind:value={uploadYear}
                                                min="1800"
                                                max="2030"
                                                class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white"
                                            />
                                        </div>
                                        <div>
                                            <label class="text-xs text-gray-400 block mb-1">Источник</label>
                                            <input
                                                type="text"
                                                bind:value={uploadSource}
                                                placeholder="Архив, автор..."
                                                class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-gray-600"
                                            />
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <label class="text-xs text-gray-400 block mb-1">Описание</label>
                                        <input
                                            type="text"
                                            bind:value={uploadDescription}
                                            placeholder="Подпись к фото..."
                                            class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-gray-600"
                                        />
                                    </div>
                                    
                                    <div>
                                        <label class="text-xs text-gray-400 block mb-1">Фотографии *</label>
                                        <input
                                            type="file"
                                            accept="image/*"
                                            multiple
                                            on:change={(e) => uploadFiles = e.currentTarget.files}
                                            class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white file:mr-3 file:bg-amber-500 file:text-black file:border-0 file:rounded file:px-2 file:py-1 file:text-sm file:font-medium"
                                        />
                                        {#if uploadFiles && uploadFiles.length > 0}
                                            <p class="text-xs text-green-400 mt-1">Выбрано: {uploadFiles.length} файлов</p>
                                        {/if}
                                    </div>
                                    
                                    {#if uploadError}
                                        <p class="text-sm text-red-400">{uploadError}</p>
                                    {/if}
                                    
                                    <div class="flex gap-2">
                                        <button
                                            on:click={doUpload}
                                            disabled={uploading || !uploadFiles || uploadFiles.length === 0}
                                            class="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
                                        >
                                            {#if uploading}
                                                <Loader2 size={16} class="animate-spin" />
                                                Загрузка...
                                            {:else}
                                                <Check size={16} />
                                                Загрузить
                                            {/if}
                                        </button>
                                        <button
                                            on:click={cancelUpload}
                                            class="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg text-sm transition-colors"
                                        >
                                            Отмена
                                        </button>
                                    </div>
                                </div>
                            {/if}

                            <!-- Photos by year -->
                            {#if poi.photos.length > 0}
                                {@const photosByYear = groupByYear(poi.photos)}
                                <div class="space-y-4">
                                    {#each [...photosByYear.entries()] as [year, photos]}
                                        <div>
                                            <div class="flex items-center gap-2 mb-2">
                                                <Calendar size={14} class="text-amber-500" />
                                                <span class="text-sm font-medium text-amber-400">{year} год</span>
                                                <span class="text-xs text-gray-500">({photos.length} фото)</span>
                                            </div>
                                            <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
                                                {#each photos as photo}
                                                    <div class="relative group">
                                                        <img
                                                            src={resolveUrl(photo.image_url)}
                                                            alt="{year}"
                                                            class="w-full aspect-square object-cover rounded-lg border border-white/10"
                                                        />
                                                        <button
                                                            on:click={() => deletePhoto(poi.id, photo.id)}
                                                            class="absolute top-1 right-1 p-1 bg-red-600 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                                        >
                                                            <X size={12} class="text-white" />
                                                        </button>
                                                        {#if photo.description}
                                                            <div class="absolute bottom-0 left-0 right-0 bg-black/70 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <p class="text-[10px] text-gray-300 truncate">{photo.description}</p>
                                                            </div>
                                                        {/if}
                                                    </div>
                                                {/each}
                                            </div>
                                        </div>
                                    {/each}
                                </div>
                            {:else}
                                <div class="text-center py-8 text-gray-500">
                                    <Image size={32} class="mx-auto mb-2 opacity-50" />
                                    <p class="text-sm">Фотографий пока нет</p>
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            {/each}
        {/if}
    </div>
</div>

<!-- New POI Modal -->
{#if showNewPoi}
    <div
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
        on:click={() => showNewPoi = false}
        on:keydown={(e) => e.key === "Escape" && (showNewPoi = false)}
        role="dialog"
        tabindex="-1"
    >
        <div
            class="bg-neutral-900 border border-white/10 rounded-2xl p-6 max-w-md w-full shadow-2xl"
            on:click|stopPropagation
        >
            <h2 class="text-xl font-bold text-white mb-4">Новая точка интереса</h2>
            
            <div class="space-y-3">
                <div>
                    <label class="text-xs text-gray-400 block mb-1">Название *</label>
                    <input
                        type="text"
                        bind:value={newPoi.title}
                        placeholder="Красная площадь"
                        class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-gray-600"
                    />
                </div>
                <div>
                    <label class="text-xs text-gray-400 block mb-1">Адрес</label>
                    <input
                        type="text"
                        bind:value={newPoi.address}
                        placeholder="Красная площадь, 1"
                        class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-gray-600"
                    />
                </div>
                <div>
                    <label class="text-xs text-gray-400 block mb-1">Описание</label>
                    <textarea
                        bind:value={newPoi.description}
                        placeholder="Краткое описание..."
                        rows="2"
                        class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white placeholder:text-gray-600 resize-none"
                    ></textarea>
                </div>
                <div class="grid grid-cols-2 gap-3">
                    <div>
                        <label class="text-xs text-gray-400 block mb-1">Широта</label>
                        <input
                            type="number"
                            step="0.0001"
                            bind:value={newPoi.latitude}
                            class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white"
                        />
                    </div>
                    <div>
                        <label class="text-xs text-gray-400 block mb-1">Долгота</label>
                        <input
                            type="number"
                            step="0.0001"
                            bind:value={newPoi.longitude}
                            class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white"
                        />
                    </div>
                </div>
            </div>
            
            <div class="flex gap-2 mt-6">
                <button
                    on:click={createPoi}
                    disabled={creatingPoi || !newPoi.title.trim()}
                    class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:bg-gray-600 disabled:cursor-not-allowed text-black rounded-lg font-medium transition-colors"
                >
                    {#if creatingPoi}
                        <Loader2 size={16} class="animate-spin" />
                    {:else}
                        <Save size={16} />
                    {/if}
                    Создать
                </button>
                <button
                    on:click={() => showNewPoi = false}
                    class="px-4 py-2 bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg transition-colors"
                >
                    Отмена
                </button>
            </div>
        </div>
    </div>
{/if}
