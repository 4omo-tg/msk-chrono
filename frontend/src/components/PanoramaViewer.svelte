<script lang="ts">
    import { onMount, onDestroy, tick } from 'svelte';
    import { X, Maximize2, Minimize2, RotateCcw } from 'lucide-svelte';
    
    export let url: string;
    export let title: string = 'Панорама';
    export let isFullscreen: boolean = false;
    export let onClose: (() => void) | null = null;
    
    let container: HTMLElement;
    let viewer: any = null;
    let loading = true;
    let error = false;
    let internalFullscreen = false;
    let ready = false;
    
    $: actualFullscreen = isFullscreen || internalFullscreen;
    
    async function initViewer() {
        if (!container || !url) return;
        
        loading = true;
        error = false;
        ready = false;
        
        try {
            // Dynamic import of Photo Sphere Viewer
            const { Viewer } = await import('@photo-sphere-viewer/core');
            
            // Destroy existing viewer if any
            if (viewer) {
                try {
                    viewer.destroy();
                } catch (e) {}
            }
            
            await tick();
            
            viewer = new Viewer({
                container: container,
                panorama: url,
                navbar: [
                    'zoom',
                    'fullscreen'
                ],
                defaultYaw: 0,
                defaultPitch: 0,
                defaultZoomLvl: 50,
                touchmoveTwoFingers: false,
                mousewheelCtrlKey: false,
                loadingTxt: '',
            });
            
            viewer.addEventListener('ready', () => {
                loading = false;
                ready = true;
            });
            
            viewer.addEventListener('panorama-loaded', () => {
                loading = false;
                ready = true;
            });
            
            viewer.addEventListener('load-progress', (e: any) => {
                // Still loading
            });
            
            viewer.addEventListener('error', (e: any) => {
                console.error('Panorama error:', e);
                loading = false;
                error = true;
            });
            
        } catch (e) {
            console.error('Failed to load panorama viewer:', e);
            loading = false;
            error = true;
        }
    }
    
    function toggleFullscreen() {
        internalFullscreen = !internalFullscreen;
    }
    
    function resetView() {
        if (viewer) {
            viewer.animate({
                yaw: 0,
                pitch: 0,
                zoom: 50,
                speed: '2rpm'
            });
        }
    }
    
    function handleClose() {
        if (onClose) {
            onClose();
        } else {
            internalFullscreen = false;
        }
    }
    
    onMount(() => {
        initViewer();
    });
    
    onDestroy(() => {
        if (viewer) {
            try {
                viewer.destroy();
            } catch (e) {}
            viewer = null;
        }
    });
    
    // Re-init when URL changes
    $: if (url && container) {
        initViewer();
    }
</script>

<svelte:head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@photo-sphere-viewer/core@5/index.min.css" />
</svelte:head>

{#if actualFullscreen}
    <div class="fixed inset-0 z-[200] bg-black flex flex-col">
        <!-- Header -->
        <div class="absolute top-0 left-0 right-0 z-10 bg-gradient-to-b from-black/80 to-transparent p-4 flex items-center justify-between">
            <h3 class="text-white font-semibold">{title}</h3>
            <div class="flex items-center gap-2">
                <button 
                    class="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
                    on:click={resetView}
                    title="Сбросить вид"
                >
                    <RotateCcw size={20} />
                </button>
                <button 
                    class="p-2 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white"
                    on:click={handleClose}
                    title="Закрыть"
                >
                    <X size={20} />
                </button>
            </div>
        </div>
        
        <!-- Panorama container -->
        <div class="flex-1 relative" bind:this={container}>
            {#if loading && !ready}
                <div class="absolute inset-0 flex items-center justify-center bg-neutral-900 z-20 pointer-events-none">
                    <div class="text-center">
                        <div class="w-10 h-10 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
                        <p class="text-gray-400 text-sm">Загрузка панорамы...</p>
                    </div>
                </div>
            {/if}
            {#if error}
                <div class="absolute inset-0 flex items-center justify-center bg-neutral-900 z-20">
                    <div class="text-center">
                        <p class="text-red-400 mb-2">Не удалось загрузить панораму</p>
                        <button 
                            class="text-amber-500 hover:text-amber-400 text-sm"
                            on:click={initViewer}
                        >
                            Попробовать снова
                        </button>
                    </div>
                </div>
            {/if}
        </div>
        
        <!-- Help text -->
        <div class="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur-sm px-4 py-2 rounded-full text-sm text-gray-300">
            Перетаскивайте для вращения • Колёсико для масштаба
        </div>
    </div>
{:else}
    <!-- Inline view -->
    <div class="relative rounded-lg overflow-hidden border border-white/10 bg-neutral-900 group">
        <!-- Panorama container -->
        <div class="h-48 relative" bind:this={container}>
            {#if loading && !ready}
                <div class="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
                    <div class="text-center">
                        <div class="w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                        <p class="text-gray-400 text-xs">Загрузка...</p>
                    </div>
                </div>
            {/if}
            {#if error}
                <div class="absolute inset-0 flex items-center justify-center z-20">
                    <p class="text-red-400 text-sm">Ошибка загрузки</p>
                </div>
            {/if}
        </div>
        
        <!-- Overlay controls -->
        <div class="absolute top-2 right-2 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
                class="p-2 bg-black/60 hover:bg-black/80 rounded-full transition-colors text-white"
                on:click={toggleFullscreen}
                title="Полный экран"
            >
                <Maximize2 size={18} />
            </button>
        </div>
        
        <!-- Title overlay -->
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-2 z-10">
            <span class="text-xs text-gray-300">{title}</span>
        </div>
    </div>
{/if}

<style>
    :global(.psv-container) {
        width: 100% !important;
        height: 100% !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
    }
    
    :global(.psv-navbar) {
        background: rgba(0, 0, 0, 0.6) !important;
    }
    
    :global(.psv-loader-container) {
        background: rgba(0, 0, 0, 0.7) !important;
    }
    
    :global(.psv-canvas-container) {
        z-index: 1 !important;
    }
</style>
