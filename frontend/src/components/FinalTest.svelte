<script>
  import { gameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';
  import Timer from './Timer.svelte';

  let answers = {};
  let allAnswered = false;
  let timer;
  let isSubmitted = false;

  $: {
    allAnswered = Object.keys(answers).length === $gameState.finalQuestions.length &&
                  Object.values(answers).every(a => a.trim().length > 0);
  }

  function submitAnswer(questionIndex) {
    const answer = answers[questionIndex];
    if (!answer || !answer.trim()) return;

    socketManager.emit('submit_final_answer', {
      question_index: questionIndex,
      answer: answer.trim()
    });
  }

  function finishGame() {
    if (isSubmitted) return;

    if (!allAnswered) {
      notifications.warning('Lütfen tüm soruları cevaplayın!');
      return;
    }

    // Tüm cevapları gönder
    $gameState.finalQuestions.forEach((q, i) => {
      submitAnswer(i);
    });

    // Oyunu bitir
    socketManager.emit('finish_game', {});
    isSubmitted = true;
    if (timer) timer.stop();
    notifications.success('Cevaplarınız gönderildi! Diğer oyuncular bekleniyor...');
  }

  function handleTimeout() {
    // Auto-submit all answers
    if (isSubmitted) return;

    notifications.info('Süre doldu! Cevaplarınız otomatik olarak gönderildi.');

    // Submit all answered questions
    $gameState.finalQuestions.forEach((q, i) => {
      if (answers[i] && answers[i].trim()) {
        submitAnswer(i);
      }
    });

    // Finish game
    socketManager.emit('finish_game', {});
    isSubmitted = true;
  }
</script>

<div class="card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
  <div class="text-center mb-6 sticky top-0 bg-white pb-4 border-b">
    <div class="flex justify-between items-start mb-2">
      <div class="flex-1"></div>
      <h1 class="text-4xl font-bold text-primary flex-1">Final Testi</h1>
      <div class="flex-1 flex justify-end">
        {#if !isSubmitted}
          <Timer bind:this={timer} duration={120} onTimeout={handleTimeout} />
        {/if}
      </div>
    </div>
    <p class="text-gray-600">Oyun boyunca öğrendiklerinizi test edin!</p>
    <p class="text-sm text-cyan-600 font-semibold mt-2">
      Her doğru cevap için +500 puan kazanacaksınız
    </p>
    <p class="text-xs text-yellow-600 font-semibold mt-1">
      120 saniyeniz var!
    </p>
  </div>

  <div class="space-y-6 mb-6">
    {#each $gameState.finalQuestions as question, i}
      <div class="bg-gray-50 p-5 rounded-xl border-2 border-cyan-200">
        <div class="flex items-start gap-3 mb-3">
          <span class="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-500 text-white flex items-center justify-center font-bold">
            {i + 1}
          </span>
          <div class="flex-1">
            <p class="font-semibold text-gray-800">{question.question_text}</p>
          </div>
        </div>

        <input
          type="text"
          bind:value={answers[i]}
          placeholder="Cevabınızı buraya yazın..."
          class="input"
        />
      </div>
    {/each}
  </div>

  <div class="sticky bottom-0 bg-white pt-4 border-t">
    {#if isSubmitted}
      <div class="bg-cyan-50 border-2 border-cyan-300 rounded-lg p-6 text-center">
        <div class="text-4xl mb-3">⏳</div>
        <p class="text-cyan-800 font-semibold text-lg mb-1">
          Cevaplarınız gönderildi!
        </p>
        <p class="text-cyan-600 text-sm">
          Diğer oyuncuların testlerini bitirmesi bekleniyor...
        </p>
      </div>
    {:else}
      <button
        on:click={finishGame}
        disabled={!allAnswered}
        class="btn btn-success w-full text-xl py-4 {!allAnswered ? 'opacity-50 cursor-not-allowed' : ''}"
      >
        Testi Bitir ve Sonuçları Gör
      </button>

      {#if !allAnswered}
        <p class="text-center text-gray-500 text-sm mt-2">
          Devam etmek için tüm soruları cevaplayın ({Object.keys(answers).length}/{$gameState.finalQuestions.length})
        </p>
      {/if}
    {/if}
  </div>
</div>
