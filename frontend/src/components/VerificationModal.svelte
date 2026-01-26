<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import {
        Camera,
        MapPin,
        Loader,
        X,
        CheckCircle,
        AlertCircle,
    } from "lucide-svelte";

    export let selectedPOI: any = null;

    const dispatch = createEventDispatcher();

    let step: 0 | 1 | 2 | 3 = 0; // 0: Choose, 1: Location, 2: Photo, 3: Result
    let method: "geo" | "photo" = "geo";
    let coords: { latitude: number; longitude: number } | null = null;
    let photoFile: File | null = null;
    let photoPreview: string | null = null;

    let isVerifying: boolean = false;
    let verificationResult: { verified: boolean; message: string } | null =
        null;
    let error: string | null = null;

    function close() {
        dispatch("close");
    }

    function getLocation() {
        error = null;
        if (!navigator.geolocation) {
            error = "Геолокация не поддерживается вашим браузером.";
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                coords = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                };
                verify(); // Auto-verify for geo method
            },
            (err) => {
                console.error(err);
                if (err.code === err.PERMISSION_DENIED) {
                    error =
                        "Доступ к геопозиции запрещен. Пожалуйста, разрешите доступ в настройках браузера.";
                } else if (err.code === err.POSITION_UNAVAILABLE) {
                    error = "Не удалось определить местоположение.";
                } else {
                    error = "Ошибка при получении геопозиции.";
                }
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
        );
    }

    function handleFile(event: Event) {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files[0]) {
            photoFile = input.files[0];
            photoPreview = URL.createObjectURL(photoFile);
            error = null;
        }
    }

    async function verify() {
        if (method === "geo" && !coords) return;
        if (method === "photo" && !photoFile) return;

        isVerifying = true;
        error = null;

        const formData = new FormData();
        formData.append("poi_id", selectedPOI.id.toString());

        if (coords) {
            formData.append("latitude", coords.latitude.toString());
            formData.append("longitude", coords.longitude.toString());
        }

        if (photoFile) {
            formData.append("file", photoFile);
        }

        try {
            const token = localStorage.getItem("token");
            const res = await fetch(
                "http://localhost:8000/api/v1/verification/verify-poi",
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                    body: formData,
                },
            );

            const data = await res.json();

            if (res.ok) {
                verificationResult = data;
                if (data.verified) {
                    setTimeout(() => {
                        dispatch("verified");
                    }, 2500); // Check-in after delay
                }
            } else {
                error = data.detail || "Проверка не удалась";
                verificationResult = {
                    verified: false,
                    message: error || "Ошибка",
                };
            }
        } catch (e) {
            error = "Ошибка сети. Попробуйте еще раз.";
            verificationResult = { verified: false, message: error };
        } finally {
            isVerifying = false;
            step = 3;
        }
    }

    function retry() {
        step = 0;
        coords = null;
        photoFile = null;
        photoPreview = null;
        verificationResult = null;
        error = null;
    }
</script>

<div
    class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
>
    <div
        class="bg-neutral-900 border border-white/10 p-6 rounded-2xl w-full max-w-md shadow-2xl relative"
    >
        <button
            on:click={close}
            class="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
            <X size={24} />
        </button>

        <div class="text-center mb-6">
            <h2 class="text-2xl font-bold text-white mb-2">
                Способ верификации
            </h2>
            <p class="text-gray-400 text-sm">
                Подтвердите, что вы находитесь у "{selectedPOI?.title ||
                    "объекта"}"
            </p>
        </div>

        {#if step === 0}
            <div class="space-y-4 py-4">
                <button
                    on:click={() => {
                        method = "geo";
                        step = 1;
                    }}
                    class="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl flex items-center gap-4 transition-all group text-left"
                >
                    <div
                        class="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center text-amber-500 group-hover:bg-amber-500 group-hover:text-black transition-colors"
                    >
                        <MapPin size={24} />
                    </div>
                    <div>
                        <h3 class="font-bold text-white">Геолокация</h3>
                        <p class="text-sm text-gray-400">
                            Проверка по GPS координатам
                        </p>
                    </div>
                </button>

                <button
                    on:click={() => {
                        method = "photo";
                        step = 2;
                    }}
                    class="w-full p-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl flex items-center gap-4 transition-all group text-left"
                >
                    <div
                        class="w-12 h-12 bg-purple-500/10 rounded-full flex items-center justify-center text-purple-500 group-hover:bg-purple-500 group-hover:text-black transition-colors"
                    >
                        <Camera size={24} />
                    </div>
                    <div>
                        <h3 class="font-bold text-white">Фото-подтверждение</h3>
                        <p class="text-sm text-gray-400">
                            Анализ снимка места через ИИ
                        </p>
                    </div>
                </button>
            </div>
        {:else if step === 1}
            <div class="space-y-6 text-center py-4">
                <div
                    class="w-20 h-20 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto text-amber-500 animate-pulse"
                >
                    <MapPin size={40} />
                </div>
                <div>
                    <p class="text-white font-medium mb-2">Шаг 1: Геолокация</p>
                    <p class="text-gray-400 text-sm">
                        Нам нужно проверить ваши координаты.
                    </p>
                </div>

                {#if error}
                    <div
                        class="bg-red-500/10 text-red-500 p-3 rounded-lg text-sm flex items-center gap-2 text-left"
                    >
                        <AlertCircle size={16} />
                        {error}
                    </div>
                {/if}

                <div class="flex gap-3">
                    <button
                        on:click={() => (step = 0)}
                        class="px-4 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all"
                    >
                        Назад
                    </button>
                    <button
                        on:click={getLocation}
                        class="flex-1 py-3 bg-amber-500 hover:bg-amber-600 text-black font-bold rounded-xl transition-all"
                    >
                        Определить местоположение
                    </button>
                </div>
            </div>
        {:else if step === 2}
            <div class="space-y-6 text-center py-4">
                <div
                    class="w-20 h-20 bg-amber-500/10 rounded-full flex items-center justify-center mx-auto text-amber-500"
                >
                    <Camera size={40} />
                </div>
                <div>
                    <p class="text-white font-medium mb-2">
                        Шаг 2: Фото подтверждение
                    </p>
                    <p class="text-gray-400 text-sm">
                        Сделайте фото достопримечательности.
                    </p>
                </div>

                <div
                    class="bg-white/5 p-4 rounded-xl border border-white/10 relative overflow-hidden group"
                >
                    {#if photoPreview}
                        <img
                            src={photoPreview}
                            alt="Preview"
                            class="w-full h-48 object-cover rounded-lg"
                        />
                        <div
                            class="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <p class="text-white text-sm">
                                Нажмите чтобы изменить
                            </p>
                        </div>
                    {:else}
                        <div
                            class="h-48 flex items-center justify-center border-2 border-dashed border-white/20 rounded-lg"
                        >
                            <span class="text-gray-500 text-sm"
                                >Нажмите или перетащите фото</span
                            >
                        </div>
                    {/if}
                    <input
                        type="file"
                        accept="image/*"
                        capture="environment"
                        on:change={handleFile}
                        class="absolute inset-0 opacity-0 cursor-pointer"
                    />
                </div>

                <div class="flex gap-3">
                    <button
                        on:click={() => (step = 0)}
                        class="px-4 py-3 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all"
                    >
                        Назад
                    </button>
                    <button
                        on:click={verify}
                        disabled={!photoFile || isVerifying}
                        class="flex-1 py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold rounded-xl transition-all flex items-center justify-center gap-2"
                    >
                        {#if isVerifying}
                            <Loader size={20} class="animate-spin" />
                            Проверка...
                        {:else}
                            Подтвердить
                        {/if}
                    </button>
                </div>
            </div>
        {:else if step === 3}
            <div class="text-center py-8">
                {#if verificationResult?.verified}
                    <div
                        class="w-24 h-24 bg-green-500/10 rounded-full flex items-center justify-center mx-auto text-green-500 mb-6"
                    >
                        <CheckCircle size={48} />
                    </div>
                    <h3 class="text-2xl font-bold text-white mb-2">Успешно!</h3>
                    <p class="text-gray-300 mb-6">
                        {verificationResult.message}
                    </p>
                    <p class="text-amber-500 font-bold animate-pulse">
                        Начисление наград...
                    </p>
                {:else}
                    <div
                        class="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center mx-auto text-red-500 mb-6"
                    >
                        <X size={48} />
                    </div>
                    <h3 class="text-2xl font-bold text-white mb-2">Ошибка</h3>
                    <p class="text-gray-300 mb-6">
                        {verificationResult?.message || error}
                    </p>

                    <button
                        on:click={retry}
                        class="w-full py-3 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl transition-all"
                    >
                        Попробовать снова
                    </button>
                {/if}
            </div>
        {/if}
    </div>
</div>
