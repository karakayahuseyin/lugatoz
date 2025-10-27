<script>
  import { gameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';

  let answers = {};
  let allAnswered = false;

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
    if (!allAnswered) {
      alert('Lütfen tüm soruları cevaplayın!');
      return;
    }

    // Tüm cevapları gönder
    $gameState.finalQuestions.forEach((q, i) => {
      submitAnswer(i);
    });

    // Oyunu bitir
    socketManager.emit('finish_game', {});
  }
</script>

<div class="card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
  <div class="text-center mb-6 sticky top-0 bg-white pb-4 border-b">
    <h1 class="text-4xl font-bold text-primary mb-2">Final Testi</h1>
    <p class="text-gray-600">Oyun boyunca öğrendiklerinizi test edin!</p>
    <p class="text-sm text-cyan-600 font-semibold mt-2">
      Her doğru cevap için +500 puan kazanacaksınız
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
            <p class="font-semibold text-gray-800 mb-1">{question.question_text}</p>
            {#if question.category}
              <span class="text-xs bg-lime-100 text-lime-700 px-2 py-1 rounded-full">
                {question.category}
              </span>
            {/if}
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
  </div>
</div>
