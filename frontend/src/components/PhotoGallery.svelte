<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { Clock, Camera, Image, Maximize2, ChevronLeft, ChevronRight, X } from 'lucide-svelte';
    import PanoramaViewer from './PanoramaViewer.svelte';
    
    export let poi: any;
    
    const dispatch = createEventDispatcher();
    
    // Tab state: 'historic' | 'modern' | 'panorama'
    let activeTab: 'historic' | 'modern' | 'panorama' = 'historic';
    
    // Current image index for each gallery
    let historicIndex = 0;
    let modernIndex = 0;
    
    // Modal state
    let showModal = false;
    let modalImages: string[] = [];
    let modalIndex = 0;
    let modalTitle = '';
    
    // Get arrays of images, falling back to single image if no gallery
    $: historicImages = poi?.historic_images?.length > 0 
        ? poi.historic_images 
        : (poi?.historic_image_url ? [poi.historic_image_url] : []);
    
    $: modernImages = poi?.modern_images?.length > 0 
        ? poi.modern_images 
        : (poi?.modern_image_url ? [poi.modern_image_url] : []);
    
    $: hasHistoric = historicImages.length > 0;
    $: hasModern = modernImages.length > 0;
    $: hasHistoricPanorama = !!poi?.historic_panorama_url;
    $: hasModernPanorama = !!poi?.modern_panorama_url;
    $: hasPanorama = hasHistoricPanorama || hasModernPanorama;
    
    function openGalleryModal(images: string[], index: number, title: string) {
        modalImages = images;
        modalIndex = index;
        modalTitle = title;
        showModal = true;
    }
    
    function closeModal() {
        showModal = false;
        modalImages = [];
        modalIndex = 0;
    }
    
    function nextImage() {
        if (modalIndex < modalImages.length - 1) {
            modalIndex++;
        }
    }
    
    function prevImage() {
        if (modalIndex > 0) {
            modalIndex--;
        }
    }
    
    function handleKeydown(e: KeyboardEvent) {
        if (!showModal) return;
        if (e.key === 'Escape') closeModal();
        if (e.key === 'ArrowRight') nextImage();
        if (e.key === 'ArrowLeft') prevImage();
    }
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="space-y-3">
    <!-- Tabs -->
    <div class="flex bg-neutral-900 rounded-lg p-1 gap-1">
        {#if hasHistoric}
            <button
                on:click={() => activeTab = 'historic'}
                class="flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5
                    {activeTab === 'historic' ? 'bg-neutral-700 text-white' : 'text-gray-400 hover:text-white'}"
            >
                <Clock size={14} />
                Тогда
                {#if historicImages.length > 1}
                    <span class="bg-white/20 px-1.5 py-0.5 rounded text-[10px]">{historicImages.length}</span>
                {/if}
            </button>
        {/if}
        {#if hasModern}
            <button
                on:click={() => activeTab = 'modern'}
                class="flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5
                    {activeTab === 'modern' ? 'bg-amber-500 text-black' : 'text-gray-400 hover:text-white'}"
            >
                <Camera size={14} />
                Сейчас
                {#if modernImages.length > 1}
                    <span class="bg-black/20 px-1.5 py-0.5 rounded text-[10px]">{modernImages.length}</span>
                {/if}
            </button>
        {/if}
        {#if hasPanorama}
            <button
                on:click={() => activeTab = 'panorama'}
                class="flex-1 py-2 px-3 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5
                    {activeTab === 'panorama' ? 'bg-purple-500 text-white' : 'text-gray-400 hover:text-white'}"
            >
                <Maximize2 size={14} />
                Панорама
            </button>
        {/if}
    </div>
    
    <!-- Gallery Content -->
    {#if activeTab === 'historic' && hasHistoric}
        <div class="relative">
            <!-- Main Image -->
            <div 
                class="relative overflow-hidden rounded-lg border border-white/10 cursor-pointer group"
                on:click={() => openGalleryModal(historicImages, historicIndex, 'Исторические фото')}
                on:keydown={(e) => e.key === 'Enter' && openGalleryModal(historicImages, historicIndex, 'Исторические фото')}
                role="button"
                tabindex="0"
            >
                <img
                    src={historicImages[historicIndex]}
                    alt="Историческое фото {historicIndex + 1}"
                    class="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                    <span class="text-xs text-gray-300">Историческое фото • {historicIndex + 1}/{historicImages.length}</span>
                </div>
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <div class="bg-white/20 backdrop-blur-sm rounded-full p-3">
                        <Maximize2 size={24} class="text-white" />
                    </div>
                </div>
            </div>
            
            <!-- Navigation arrows -->
            {#if historicImages.length > 1}
                <button 
                    class="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 p-1.5 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    on:click|stopPropagation={() => historicIndex = Math.max(0, historicIndex - 1)}
                    disabled={historicIndex === 0}
                >
                    <ChevronLeft size={20} class="text-white" />
                </button>
                <button 
                    class="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 p-1.5 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    on:click|stopPropagation={() => historicIndex = Math.min(historicImages.length - 1, historicIndex + 1)}
                    disabled={historicIndex === historicImages.length - 1}
                >
                    <ChevronRight size={20} class="text-white" />
                </button>
            {/if}
        </div>
        
        <!-- Thumbnails -->
        {#if historicImages.length > 1}
            <div class="flex gap-2 overflow-x-auto pb-2">
                {#each historicImages as img, i}
                    <button
                        class="flex-shrink-0 w-16 h-12 rounded-md overflow-hidden border-2 transition-all
                            {i === historicIndex ? 'border-amber-500' : 'border-transparent hover:border-white/30'}"
                        on:click={() => historicIndex = i}
                    >
                        <img src={img} alt="Фото {i + 1}" class="w-full h-full object-cover" />
                    </button>
                {/each}
            </div>
        {/if}
    {/if}
    
    {#if activeTab === 'modern' && hasModern}
        <div class="relative">
            <!-- Main Image -->
            <div 
                class="relative overflow-hidden rounded-lg border border-white/10 cursor-pointer group"
                on:click={() => openGalleryModal(modernImages, modernIndex, 'Современные фото')}
                on:keydown={(e) => e.key === 'Enter' && openGalleryModal(modernImages, modernIndex, 'Современные фото')}
                role="button"
                tabindex="0"
            >
                <img
                    src={modernImages[modernIndex]}
                    alt="Современное фото {modernIndex + 1}"
                    class="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                    <span class="text-xs text-amber-400">Современное фото • {modernIndex + 1}/{modernImages.length}</span>
                </div>
                <div class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <div class="bg-white/20 backdrop-blur-sm rounded-full p-3">
                        <Maximize2 size={24} class="text-white" />
                    </div>
                </div>
            </div>
            
            <!-- Navigation arrows -->
            {#if modernImages.length > 1}
                <button 
                    class="absolute left-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 p-1.5 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    on:click|stopPropagation={() => modernIndex = Math.max(0, modernIndex - 1)}
                    disabled={modernIndex === 0}
                >
                    <ChevronLeft size={20} class="text-white" />
                </button>
                <button 
                    class="absolute right-2 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 p-1.5 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    on:click|stopPropagation={() => modernIndex = Math.min(modernImages.length - 1, modernIndex + 1)}
                    disabled={modernIndex === modernImages.length - 1}
                >
                    <ChevronRight size={20} class="text-white" />
                </button>
            {/if}
        </div>
        
        <!-- Thumbnails -->
        {#if modernImages.length > 1}
            <div class="flex gap-2 overflow-x-auto pb-2">
                {#each modernImages as img, i}
                    <button
                        class="flex-shrink-0 w-16 h-12 rounded-md overflow-hidden border-2 transition-all
                            {i === modernIndex ? 'border-amber-500' : 'border-transparent hover:border-white/30'}"
                        on:click={() => modernIndex = i}
                    >
                        <img src={img} alt="Фото {i + 1}" class="w-full h-full object-cover" />
                    </button>
                {/each}
            </div>
        {/if}
    {/if}
    
    {#if activeTab === 'panorama' && hasPanorama}
        <div class="space-y-3">
            {#if hasHistoricPanorama}
                <PanoramaViewer 
                    url={poi.historic_panorama_url} 
                    title="Историческая панорама (360°)" 
                />
            {/if}
            
            {#if hasModernPanorama}
                <PanoramaViewer 
                    url={poi.modern_panorama_url} 
                    title="Современная панорама (360°)" 
                />
            {/if}
        </div>
    {/if}
</div>

<!-- Full Screen Modal -->
{#if showModal}
    <div 
        class="fixed inset-0 z-[200] bg-black/95 backdrop-blur-md flex items-center justify-center"
        on:click={closeModal}
        role="dialog"
        tabindex="-1"
    >
        <!-- Close button -->
        <button 
            class="absolute top-4 right-4 text-white/70 hover:text-white z-10 p-2 bg-white/10 rounded-full hover:bg-white/20 transition-colors"
            on:click={closeModal}
        >
            <X size={24} />
        </button>
        
        <!-- Title -->
        <div class="absolute top-4 left-4 text-white z-10">
            <h3 class="text-lg font-semibold">{modalTitle}</h3>
            <p class="text-sm text-gray-400">{modalIndex + 1} / {modalImages.length}</p>
        </div>
        
        <!-- Navigation -->
        {#if modalImages.length > 1}
            <button 
                class="absolute left-4 top-1/2 -translate-y-1/2 bg-white/10 hover:bg-white/20 p-3 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed z-10"
                on:click|stopPropagation={prevImage}
                disabled={modalIndex === 0}
            >
                <ChevronLeft size={32} class="text-white" />
            </button>
            <button 
                class="absolute right-4 top-1/2 -translate-y-1/2 bg-white/10 hover:bg-white/20 p-3 rounded-full transition-colors disabled:opacity-30 disabled:cursor-not-allowed z-10"
                on:click|stopPropagation={nextImage}
                disabled={modalIndex === modalImages.length - 1}
            >
                <ChevronRight size={32} class="text-white" />
            </button>
        {/if}
        
        <!-- Image -->
        <img 
            src={modalImages[modalIndex]} 
            alt="{modalTitle} {modalIndex + 1}" 
            class="max-w-[90vw] max-h-[85vh] object-contain rounded-lg shadow-2xl"
            on:click|stopPropagation
        />
        
        <!-- Thumbnails at bottom -->
        {#if modalImages.length > 1}
            <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/50 backdrop-blur-sm p-2 rounded-lg">
                {#each modalImages as img, i}
                    <button
                        class="w-12 h-8 rounded overflow-hidden border-2 transition-all
                            {i === modalIndex ? 'border-amber-500' : 'border-transparent hover:border-white/50'}"
                        on:click|stopPropagation={() => modalIndex = i}
                    >
                        <img src={img} alt="Миниатюра {i + 1}" class="w-full h-full object-cover" />
                    </button>
                {/each}
            </div>
        {/if}
    </div>
{/if}
