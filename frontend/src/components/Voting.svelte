<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';

  let selectedAnswer = null;

  function selectAnswer(answer) {
    if ($gameState.votedAnswer) return;
    selectedAnswer = answer;
  }

  function submitVote() {
    if (!selectedAnswer) {
      alert('Lütfen bir cevap seçin!');
      return;
    }

    socketManager.emit('submit_vote', {
      answer: selectedAnswer
    });

    updateGameState({ votedAnswer: true });
  }
</script>

<div class="card max-w-3xl w-full">
  <div class="mb-6">
    <div class="flex justify-between items-center mb-4">
      <span class="bg-secondary text-white px-4 py-2 rounded-full font-semibold">
        Soru {$gameState.currentRound + 1} / {$gameState.maxRounds}
      </span>
      <span class="text-gray-600 font-semibold">
        OYLAMA
      </span>
    </div>

    <div class="bg-gradient-to-r from-cyan-100 to-lime-100 p-6 rounded-xl border-2 border-cyan-300 mb-6">
      <p class="text-2xl font-semibold text-gray-800 text-center">
        {$gameState.currentQuestion?.text}
      </p>
    </div>
  </div>

  {#if !$gameState.votedAnswer}
    <div class="space-y-4 mb-6">
      <h3 class="text-xl font-semibold text-gray-800 text-center mb-4">
        Doğru cevabı seçin!
      </h3>

      <div class="grid gap-3">
        {#each $gameState.options as option, i}
          <button
            on:click={() => selectAnswer(option)}
            class="p-4 rounded-lg border-2 transition-all text-left {
              selectedAnswer === option
                ? 'border-primary bg-primary text-white shadow-lg scale-105'
                : 'border-gray-300 bg-white hover:border-primary hover:bg-cyan-50'
            }"
          >
            <div class="flex items-center gap-3">
              <span class="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-200 flex items-center justify-center font-bold {
                selectedAnswer === option ? 'bg-white text-primary' : 'text-cyan-700'
              }">
                {String.fromCharCode(65 + i)}
              </span>
              <span class="font-semibold text-lg">
                {option}
              </span>
            </div>
          </button>
        {/each}
      </div>
    </div>

    <button
      on:click={submitVote}
      disabled={!selectedAnswer}
      class="btn btn-success w-full text-xl py-4 {!selectedAnswer ? 'opacity-50 cursor-not-allowed' : ''}"
    >
      Oyumu Gönder
    </button>
  {:else}
    <div class="bg-green-50 border-2 border-cyan-300 rounded-xl p-8 text-center">
      <div class="text-6xl mb-4">✓</div>
      <h3 class="text-2xl font-bold text-cyan-800 mb-2">Oyunuz Gönderildi!</h3>
      <p class="text-cyan-700">
        Diğer oyuncuların oylarını bekliyoruz...
      </p>
      <div class="mt-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-700"></div>
      </div>
    </div>
  {/if}

  <div class="mt-6 pt-6 border-t border-gray-200">
    <p class="text-sm text-gray-600 text-center">
      <strong>+1000 puan</strong> kazanmak için doğru cevabı bulun!
    </p>
  </div>
</div>
