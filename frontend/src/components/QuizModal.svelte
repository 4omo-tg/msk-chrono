<script lang="ts">
    import { apiPost } from "../lib/api";
    import { createEventDispatcher } from "svelte";

    export let currentQuiz: any = null;
    export let quizIndex: number = 0;
    export let totalQuizzes: number = 0;

    const dispatch = createEventDispatcher();
    let selectedAnswer: string = "";
    let showResult: boolean = false;
    let isCorrect: boolean = false;
    let correctAnswer: string = "";
    let xpEarned: number = 0;

    function selectAnswer(answer: string) {
        selectedAnswer = answer;
    }

    async function submitAnswer() {
        if (!selectedAnswer) {
            alert("Пожалуйста, выберите ответ");
            return;
        }

        try {
            const response = await apiPost(
                `/api/v1/quizzes/${currentQuiz.id}/submit`,
                { answer: selectedAnswer },
            );

            if (response.ok) {
                const result = await response.json();
                isCorrect = result.is_correct;
                correctAnswer = result.correct_answer;
                xpEarned = result.xp_earned;
                showResult = true;

                // Dispatch event to update user XP
                dispatch("quizComplete", {
                    xpEarned: result.xp_earned,
                    newTotalXp: result.new_total_xp,
                    newLevel: result.new_level,
                });
            } else {
                const error = await response.json();
                alert(error.detail || "Ошибка отправки ответа");
            }
        } catch (error) {
            console.error("Quiz submit error:", error);
            alert("Ошибка отправки ответа");
        }
    }

    function nextQuiz() {
        showResult = false;
        selectedAnswer = "";
        dispatch("next");
    }

    function closeQuiz() {
        dispatch("close");
    }
</script>

<div
    class="quiz-modal-overlay"
    on:click={closeQuiz}
    role="dialog"
    aria-modal="true"
    on:keydown={(e) => e.key === "Escape" && closeQuiz()}
>
    <div
        class="quiz-modal"
        on:click|stopPropagation
        role="document"
        on:keydown={() => {}}
    >
        <div class="quiz-header">
            <h2>🎯 Квиз</h2>
            <span class="quiz-counter">{quizIndex + 1} / {totalQuizzes}</span>
            <div class="header-buttons">
                <button
                    class="skip-btn"
                    on:click={closeQuiz}
                    title="Пропустить квиз"
                >
                    Пропустить
                </button>
                <button class="close-btn" on:click={closeQuiz} title="Закрыть"
                    >✕</button
                >
            </div>
        </div>

        {#if !showResult}
            <div class="quiz-content">
                <p class="question">{currentQuiz.question}</p>

                <div class="options">
                    <button
                        class="option-btn"
                        class:selected={selectedAnswer === "A"}
                        on:click={() => selectAnswer("A")}
                    >
                        <span class="option-label">A</span>
                        {currentQuiz.option_a}
                    </button>

                    <button
                        class="option-btn"
                        class:selected={selectedAnswer === "B"}
                        on:click={() => selectAnswer("B")}
                    >
                        <span class="option-label">B</span>
                        {currentQuiz.option_b}
                    </button>

                    <button
                        class="option-btn"
                        class:selected={selectedAnswer === "C"}
                        on:click={() => selectAnswer("C")}
                    >
                        <span class="option-label">C</span>
                        {currentQuiz.option_c}
                    </button>

                    <button
                        class="option-btn"
                        class:selected={selectedAnswer === "D"}
                        on:click={() => selectAnswer("D")}
                    >
                        <span class="option-label">D</span>
                        {currentQuiz.option_d}
                    </button>
                </div>

                <button class="submit-btn" on:click={submitAnswer}>
                    Ответить
                </button>
            </div>
        {:else}
            <div class="quiz-result">
                {#if isCorrect}
                    <div class="result-icon correct">✓</div>
                    <h3 class="result-title correct">Правильно!</h3>
                    <p class="result-message">Вы заработали {xpEarned} XP</p>
                {:else}
                    <div class="result-icon incorrect">✗</div>
                    <h3 class="result-title incorrect">Неправильно</h3>
                    <p class="result-message">
                        Правильный ответ: <strong>{correctAnswer}</strong>
                    </p>
                {/if}

                {#if quizIndex < totalQuizzes - 1}
                    <button class="next-btn" on:click={nextQuiz}>
                        Следующий вопрос →
                    </button>
                {:else}
                    <button class="next-btn" on:click={closeQuiz}>
                        Завершить
                    </button>
                {/if}
            </div>
        {/if}
    </div>
</div>

<style>
    .quiz-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.85);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        padding: 12px;
    }

    .quiz-modal {
        background: rgba(23, 23, 23, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        max-width: 600px;
        width: 100%;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }

    @media (max-width: 480px) {
        .quiz-modal-overlay {
            padding: 0;
            align-items: flex-end;
        }
        
        .quiz-modal {
            border-radius: 20px 20px 0 0;
            max-height: 95vh;
        }
    }

    .quiz-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        gap: 8px;
    }

    .quiz-header h2 {
        color: #fff;
        margin: 0;
        font-size: 20px;
        font-weight: 700;
    }

    @media (min-width: 481px) {
        .quiz-header {
            padding: 24px;
        }
        .quiz-header h2 {
            font-size: 24px;
        }
    }

    .quiz-counter {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: #000;
        font-weight: bold;
        font-size: 14px;
        padding: 6px 12px;
        border-radius: 12px;
    }

    .header-buttons {
        display: flex;
        gap: 8px;
        align-items: center;
    }

    .skip-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: rgba(255, 255, 255, 0.7);
        font-size: 12px;
        padding: 6px 10px;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s;
        font-weight: 500;
    }

    @media (min-width: 481px) {
        .skip-btn {
            font-size: 14px;
            padding: 8px 16px;
            border-radius: 12px;
        }
    }

    .skip-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
        border-color: rgba(255, 255, 255, 0.2);
    }

    .close-btn {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.7);
        font-size: 24px;
        cursor: pointer;
        padding: 4px;
        width: 32px;
        height: 32px;
        line-height: 24px;
        transition: color 0.2s;
    }

    .close-btn:hover {
        color: #fff;
    }

    .quiz-content {
        padding: 20px 16px;
    }

    .question {
        color: #fff;
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 24px;
        line-height: 1.5;
    }

    @media (min-width: 481px) {
        .quiz-content {
            padding: 32px 24px;
        }
        .question {
            font-size: 20px;
            margin-bottom: 32px;
            line-height: 1.6;
        }
    }

    .options {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 32px;
    }

    .option-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #fff;
        padding: 12px 14px;
        border-radius: 12px;
        cursor: pointer;
        text-align: left;
        font-size: 14px;
        transition: all 0.3s;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    @media (min-width: 481px) {
        .option-btn {
            padding: 16px 20px;
            border-radius: 16px;
            font-size: 16px;
            gap: 12px;
        }
    }

    .option-btn:hover {
        background: rgba(255, 255, 255, 0.08);
        border-color: rgba(251, 191, 36, 0.5);
        transform: translateX(4px);
    }

    .option-btn.selected {
        background: linear-gradient(
            135deg,
            rgba(251, 191, 36, 0.2) 0%,
            rgba(245, 158, 11, 0.2) 100%
        );
        border-color: #fbbf24;
        color: #fbbf24;
    }

    .option-label {
        background: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        flex-shrink: 0;
        border: 1px solid rgba(251, 191, 36, 0.3);
        font-size: 14px;
    }

    @media (min-width: 481px) {
        .option-label {
            width: 36px;
            height: 36px;
            font-size: 16px;
        }
    }

    .option-btn.selected .option-label {
        background: #fbbf24;
        color: #000;
        border-color: #fbbf24;
    }

    .submit-btn,
    .next-btn {
        width: 100%;
        padding: 16px;
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        border: none;
        border-radius: 16px;
        color: #000;
        font-size: 18px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s;
        box-shadow: 0 4px 6px -1px rgba(251, 191, 36, 0.3);
    }

    .submit-btn:hover,
    .next-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(251, 191, 36, 0.4);
    }

    .quiz-result {
        padding: 48px 24px;
        text-align: center;
    }

    .result-icon {
        width: 96px;
        height: 96px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        margin: 0 auto 24px;
        border: 3px solid;
    }

    .result-icon.correct {
        background: linear-gradient(
            135deg,
            rgba(34, 197, 94, 0.2) 0%,
            rgba(22, 163, 74, 0.2) 100%
        );
        color: #22c55e;
        border-color: #22c55e;
    }

    .result-icon.incorrect {
        background: linear-gradient(
            135deg,
            rgba(239, 68, 68, 0.2) 0%,
            rgba(220, 38, 38, 0.2) 100%
        );
        color: #ef4444;
        border-color: #ef4444;
    }

    .result-title {
        font-size: 32px;
        margin-bottom: 12px;
        font-weight: 700;
    }

    .result-title.correct {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .result-title.incorrect {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .result-message {
        color: rgba(255, 255, 255, 0.8);
        font-size: 18px;
        margin-bottom: 32px;
        line-height: 1.5;
    }

    .result-message strong {
        color: #fbbf24;
        font-weight: 700;
    }
</style>
