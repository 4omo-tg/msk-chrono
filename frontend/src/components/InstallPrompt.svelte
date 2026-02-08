<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Download, X, Share } from 'lucide-svelte';

    let deferredPrompt: any = null;
    let showPrompt = false;
    let showIOSPrompt = false;
    let dismissed = false;

    // Check if already installed
    function isInstalled(): boolean {
        // Check display-mode
        if (window.matchMedia('(display-mode: standalone)').matches) return true;
        // Check iOS standalone
        if ((window.navigator as any).standalone === true) return true;
        return false;
    }

    // Check if iOS
    function isIOS(): boolean {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;
    }

    // Check if already dismissed
    function wasDismissed(): boolean {
        const dismissedAt = localStorage.getItem('pwa_prompt_dismissed');
        if (!dismissedAt) return false;
        // Show again after 7 days
        const dismissedDate = new Date(parseInt(dismissedAt));
        const daysSince = (Date.now() - dismissedDate.getTime()) / (1000 * 60 * 60 * 24);
        return daysSince < 7;
    }

    function handleBeforeInstallPrompt(e: Event) {
        e.preventDefault();
        deferredPrompt = e;
        
        if (!isInstalled() && !wasDismissed()) {
            // Delay showing prompt
            setTimeout(() => {
                showPrompt = true;
            }, 3000);
        }
    }

    async function installApp() {
        if (!deferredPrompt) return;
        
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        
        if (outcome === 'accepted') {
            showPrompt = false;
        }
        deferredPrompt = null;
    }

    function dismissPrompt() {
        showPrompt = false;
        showIOSPrompt = false;
        dismissed = true;
        localStorage.setItem('pwa_prompt_dismissed', Date.now().toString());
    }

    onMount(() => {
        if (isInstalled()) return;
        
        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        
        // For iOS, show custom prompt after delay
        if (isIOS() && !wasDismissed()) {
            setTimeout(() => {
                showIOSPrompt = true;
            }, 5000);
        }
    });

    onDestroy(() => {
        window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    });
</script>

<!-- Android/Desktop Install Prompt -->
{#if showPrompt && !dismissed}
    <div class="fixed bottom-20 left-4 right-4 z-[60] animate-slide-up sm:left-auto sm:right-4 sm:max-w-sm">
        <div class="bg-neutral-800 border border-amber-500/30 rounded-2xl p-4 shadow-2xl shadow-black/50">
            <button
                on:click={dismissPrompt}
                class="absolute top-3 right-3 text-gray-500 hover:text-white p-1"
                aria-label="Закрыть"
            >
                <X size={18} />
            </button>
            
            <div class="flex items-start gap-4 pr-6">
                <div class="w-12 h-12 bg-amber-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Download size={24} class="text-amber-500" />
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-white mb-1">Установите приложение</h3>
                    <p class="text-sm text-gray-400 mb-3">
                        Добавьте Moscow Chrono на главный экран для быстрого доступа
                    </p>
                    <button
                        on:click={installApp}
                        class="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-black font-bold rounded-xl transition-colors active:scale-[0.98]"
                    >
                        Установить
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- iOS Install Prompt -->
{#if showIOSPrompt && !dismissed}
    <div class="fixed bottom-20 left-4 right-4 z-[60] animate-slide-up sm:left-auto sm:right-4 sm:max-w-sm">
        <div class="bg-neutral-800 border border-amber-500/30 rounded-2xl p-4 shadow-2xl shadow-black/50">
            <button
                on:click={dismissPrompt}
                class="absolute top-3 right-3 text-gray-500 hover:text-white p-1"
                aria-label="Закрыть"
            >
                <X size={18} />
            </button>
            
            <div class="flex items-start gap-4 pr-6">
                <div class="w-12 h-12 bg-amber-500/20 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Share size={24} class="text-amber-500" />
                </div>
                <div class="flex-1">
                    <h3 class="font-bold text-white mb-1">Установите приложение</h3>
                    <p class="text-sm text-gray-400">
                        Нажмите 
                        <span class="inline-flex items-center gap-1 bg-white/10 px-1.5 py-0.5 rounded">
                            <Share size={14} />
                        </span>
                        затем <span class="text-white font-medium">"На экран Домой"</span>
                    </p>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes slide-up {
        from {
            opacity: 0;
            transform: translateY(100%);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-slide-up {
        animation: slide-up 0.3s ease-out;
    }
</style>
