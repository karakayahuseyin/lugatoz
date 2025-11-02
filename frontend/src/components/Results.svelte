<script>
  import { gameState } from '../stores/gameStore';
  import Timer from './Timer.svelte';

  let timer;

  function handleTimeout() {
    // Timer finished - backend will automatically proceed to next round
    // No action needed from frontend
  }

  // Timer is only visual - backend handles auto-progression after 10 seconds
</script>

<div class="card max-w-4xl w-full">
  <div class="mb-6">
    <div class="flex justify-between items-start mb-4">
      <div class="flex-1"></div>
      <div class="flex-1 text-center">
        <h1 class="text-4xl font-bold text-primary mb-2">Tur Sonuçları</h1>
        <p class="text-gray-600">Soru {$gameState.currentRound + 1} tamamlandı!</p>
      </div>
      <div class="flex-1 flex justify-end">
        <Timer bind:this={timer} duration={10} onTimeout={handleTimeout} />
      </div>
    </div>
  </div>

  <div class="bg-gradient-to-r from-cyan-100 to-emerald-100 p-6 rounded-xl border-2 border-cyan-300 mb-6">
    <p class="text-center text-gray-700 mb-2 font-semibold">Doğru Cevap:</p>
    <p class="text-3xl font-bold text-cyan-800 text-center">
      {$gameState.results?.correct_answer}
    </p>
  </div>

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-4 text-xl">Oyuncu Sonuçları:</h3>
    <div class="space-y-3">
      {#each $gameState.results?.player_votes || [] as vote}
        <div class="bg-gray-50 p-4 rounded-lg border-2 {vote.was_correct ? 'border-cyan-300 bg-cyan-50' : 'border-gray-200'}">
          <div class="flex justify-between items-start mb-2">
            <span class="font-bold text-lg text-gray-800">{vote.player_name}</span>
            {#if vote.was_correct}
              <span class="bg-cyan-500 text-white text-xs px-3 py-1 rounded-full font-bold">
                +1000 PUAN
              </span>
            {/if}
          </div>

          <div class="text-sm space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-gray-600">Seçtiği:</span>
              <span class="font-semibold {vote.was_correct ? 'text-cyan-700' : 'text-red-600'}">
                {vote.voted_for}
              </span>
              {#if vote.was_correct}
                <span class="text-cyan-600">✓</span>
              {:else}
                <span class="text-red-600">✗</span>
              {/if}
            </div>

            {#if vote.fake_answer}
              <div class="flex items-center gap-2">
                <span class="text-gray-600">Yanlış cevabı:</span>
                <span class="font-semibold text-cyan-700">"{vote.fake_answer}"</span>
                {#if vote.votes_received > 0}
                  <span class="bg-purple-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                    {vote.votes_received} oy (+{vote.votes_received * 500} puan)
                  </span>
                {/if}
              </div>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-4 text-xl">Liderlik Tablosu:</h3>
    <div class="space-y-2">
      {#each $gameState.leaderboard as player, i}
        <div class="flex items-center gap-4 bg-gradient-to-r {
          i === 0 ? 'from-yellow-100 to-yellow-200 border-lime-400' :
          i === 1 ? 'from-gray-100 to-gray-200 border-gray-400' :
          i === 2 ? 'from-lime-100 to-lime-200 border-lime-400' :
          'from-gray-50 to-gray-100 border-gray-300'
        } border-2 p-4 rounded-lg">
          <span class="text-3xl font-bold text-gray-700 w-10">
            {#if i === 0}🥇
            {:else if i === 1}🥈
            {:else if i === 2}🥉
            {:else}{i + 1}.
            {/if}
          </span>
          <span class="flex-1 font-semibold text-lg text-gray-800">{player.name}</span>
          <span class="font-bold text-2xl text-primary">{player.score}</span>
        </div>
      {/each}
    </div>
  </div>

  <div class="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 text-center">
    <p class="text-blue-800 font-semibold">
      {$gameState.currentRound + 1 >= $gameState.maxRounds ? 'Final testine geçiliyor...' : 'Sonraki soruya geçiliyor...'}
    </p>
    <p class="text-blue-600 text-sm mt-2">
      10 saniye içinde otomatik olarak devam edilecek
    </p>
  </div>
</div>
