<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { Map, Camera, Award, HelpCircle, ChevronRight, ChevronLeft, X } from "lucide-svelte";

    const dispatch = createEventDispatcher();

    let currentStep = 0;

    const steps = [
        {
            icon: Map,
            title: "Добро пожаловать в Moscow Chrono!",
            description: "Исследуйте историческую Москву через интерактивные маршруты. Посещайте знаковые места, узнавайте их историю и зарабатывайте опыт.",
            highlight: "Готовы отправиться в путешествие во времени?"
        },
        {
            icon: Camera,
            title: "Как отмечаться в точках",
            description: "Когда вы дойдете до точки маршрута, нажмите кнопку \"Я ЗДЕСЬ!\". Приложение проверит вашу геолокацию или попросит сфотографировать место.",
            highlight: "За каждую точку вы получаете +50 XP!"
        },
        {
            icon: Award,
            title: "Уровни и награды",
            description: "Зарабатывайте опыт, повышайте уровень и открывайте новые маршруты. Проходите квизы по истории для дополнительного XP.",
            highlight: "Станьте экспертом по истории Москвы!"
        },
        {
            icon: HelpCircle,
            title: "Нужна помощь?",
            description: "В боковой панели вы всегда видите свой прогресс по маршруту. Выбирайте точки на карте, чтобы узнать о них больше.",
            highlight: "Точки нужно проходить по порядку — следуйте маршруту!"
        }
    ];

    function nextStep() {
        if (currentStep < steps.length - 1) {
            currentStep++;
        } else {
            complete();
        }
    }

    function prevStep() {
        if (currentStep > 0) {
            currentStep--;
        }
    }

    function complete() {
        localStorage.setItem("onboarding_completed", "true");
        dispatch("complete");
    }

    function skip() {
        localStorage.setItem("onboarding_completed", "true");
        dispatch("complete");
    }
</script>

<div class="fixed inset-0 z-[200] bg-black/90 backdrop-blur-md flex items-center justify-center p-3 sm:p-4">
    <div class="bg-neutral-800 border border-white/10 rounded-2xl max-w-lg w-full shadow-2xl overflow-hidden max-h-[95vh] overflow-y-auto">
        <!-- Header -->
        <div class="relative h-36 sm:h-48 bg-gradient-to-br from-amber-500/20 to-amber-600/10 flex items-center justify-center">
            <button
                on:click={skip}
                class="absolute top-3 right-3 flex items-center gap-1.5 bg-black/40 hover:bg-black/60 text-gray-300 hover:text-white px-3 py-1.5 rounded-full transition-colors text-sm font-medium"
                aria-label="Пропустить"
            >
                <span>Пропустить</span>
                <X size={16} />
            </button>
            
            <div class="w-16 h-16 sm:w-24 sm:h-24 bg-amber-500/20 rounded-full flex items-center justify-center border-2 border-amber-500/30">
                <svelte:component this={steps[currentStep].icon} size={36} class="text-amber-500 sm:hidden" />
                <svelte:component this={steps[currentStep].icon} size={48} class="text-amber-500 hidden sm:block" />
            </div>
        </div>

        <!-- Content -->
        <div class="p-5 sm:p-8">
            <h2 class="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">
                {steps[currentStep].title}
            </h2>
            
            <p class="text-gray-300 leading-relaxed mb-3 sm:mb-4 text-sm sm:text-base">
                {steps[currentStep].description}
            </p>
            
            <div class="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 sm:p-4 mb-5 sm:mb-6">
                <p class="text-amber-400 text-xs sm:text-sm font-medium">
                    💡 {steps[currentStep].highlight}
                </p>
            </div>

            <!-- Progress dots -->
            <div class="flex justify-center gap-2 mb-5 sm:mb-6">
                {#each steps as _, i}
                    <button
                        on:click={() => currentStep = i}
                        class="w-2 h-2 rounded-full transition-all {i === currentStep ? 'bg-amber-500 w-6' : 'bg-white/20 hover:bg-white/40'}"
                        aria-label="Шаг {i + 1}"
                    ></button>
                {/each}
            </div>

            <!-- Navigation -->
            <div class="flex gap-2 sm:gap-3">
                {#if currentStep > 0}
                    <button
                        on:click={prevStep}
                        class="flex-1 py-3 px-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        <ChevronLeft size={18} />
                        Назад
                    </button>
                {/if}
                
                <button
                    on:click={nextStep}
                    class="flex-1 py-3 px-4 bg-amber-500 hover:bg-amber-600 text-black rounded-xl font-bold transition-all transform active:scale-95 flex items-center justify-center gap-2"
                >
                    {#if currentStep === steps.length - 1}
                        Начать!
                    {:else}
                        Далее
                        <ChevronRight size={18} />
                    {/if}
                </button>
            </div>
        </div>
    </div>
</div>
