<script>
  import { gameState, resetGameState } from '../stores/gameStore';

  function playAgain() {
    resetGameState();
  }

  $: winner = $gameState.leaderboard?.[0];
  $: myAnswers = $gameState.playerId ? $gameState.results?.player_answers?.[$gameState.playerId] : null;
</script>

<div class="card max-w-4xl w-full">
  <div class="text-center mb-8">
    <div class="text-8xl mb-4">🏆</div>
    <h1 class="text-5xl font-bold text-primary mb-4">Oyun Bitti!</h1>

    {#if winner}
      <div class="bg-gradient-to-r from-lime-100 to-lime-200 p-6 rounded-xl border-2 border-lime-400 mb-6">
        <p class="text-2xl font-semibold text-gray-700 mb-2">Kazanan:</p>
        <p class="text-5xl font-bold text-lime-700">{winner.name}</p>
        <p class="text-3xl font-bold text-lime-600 mt-2">{winner.score} Puan</p>
      </div>
    {/if}
  </div>

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-4 text-2xl text-center">Final Sıralaması</h3>
    <div class="space-y-3">
      {#each $gameState.leaderboard as player, i}
        <div class="flex items-center gap-4 bg-gradient-to-r {
          i === 0 ? 'from-lime-100 to-lime-200 border-lime-400 scale-105' :
          i === 1 ? 'from-gray-100 to-gray-200 border-gray-400' :
          i === 2 ? 'from-lime-100 to-lime-200 border-lime-400' :
          'from-gray-50 to-gray-100 border-gray-300'
        } border-2 p-5 rounded-xl shadow-md transition-all">
          <span class="text-4xl w-14 text-center">
            {#if i === 0}🥇
            {:else if i === 1}🥈
            {:else if i === 2}🥉
            {:else}<span class="font-bold text-gray-600 text-2xl">{i + 1}.</span>
            {/if}
          </span>
          <span class="flex-1 font-bold text-xl text-gray-800">{player.name}</span>
          <span class="font-bold text-3xl {
            i === 0 ? 'text-lime-600' :
            i === 1 ? 'text-gray-600' :
            i === 2 ? 'text-lime-600' :
            'text-primary'
          }">{player.score}</span>
        </div>
      {/each}
    </div>
  </div>

  {#if myAnswers && $gameState.results?.questions_summary}
    <div class="mb-6">
      <h3 class="font-semibold text-gray-700 mb-4 text-xl">Final Test Sonuçlarınız</h3>
      <div class="space-y-3 bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
        {#each $gameState.results.questions_summary as q, i}
          {@const myAnswer = myAnswers.find(a => a.question_index === i)}
          <div class="bg-white p-4 rounded-lg border-2 {myAnswer?.is_correct ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'}">
            <p class="font-semibold text-gray-800 mb-2">
              {i + 1}. {q.question}
            </p>
            <div class="space-y-1">
              {#if myAnswer?.user_answer}
                <p class="text-sm {myAnswer.is_correct ? 'text-green-700' : 'text-red-700'} font-semibold">
                  {myAnswer.is_correct ? '✓' : '✗'} Cevabınız: {myAnswer.user_answer}
                </p>
              {:else}
                <p class="text-sm text-gray-500 italic">
                  Cevap vermediniz
                </p>
              {/if}
              {#if !myAnswer?.is_correct}
                <p class="text-sm text-green-700 font-semibold">
                  ✓ Doğru cevap: {q.correct_answer}
                </p>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <button
    on:click={playAgain}
    class="btn btn-primary w-full text-xl py-4"
  >
    Yeni Oyun
  </button>

  <div class="mt-6 text-center text-gray-600">
    <p>Oynadığınız için teşekkürler! 🎉</p>
  </div>
</div>
