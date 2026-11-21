<script>
  import { gameState, resetGameState } from '../stores/gameStore';
  import { getPlayerColor } from '../utils/colors';
  import { socketManager } from '../utils/socket';

  function restartGame() {
    socketManager.emit('restart_game', {});
  }

  function returnToLobby() {
    socketManager.emit('return_to_lobby', {});
  }

  function leaveGame() {
    socketManager.emit('leave_room', {});
    socketManager.clearRoomInfo();
    resetGameState();
  }

  $: winner = $gameState.leaderboard?.[0];
  $: myAnswers = $gameState.playerId ? $gameState.results?.player_answers?.[$gameState.playerId] : null;
  $: myFinalScore = $gameState.playerId ? $gameState.results?.final_scores?.[$gameState.playerId] : null;
  $: isHost = $gameState.players?.find((p) => p.socket_id === $gameState.playerId)?.is_host || false;
</script>

<div class="card max-w-4xl w-full my-4">
  <div class="text-center mb-8">
    {#if $gameState.topic}
      <span class="inline-block text-xs font-bold bg-cyan-100 text-cyan-800 px-3 py-1 rounded-full mb-3">
        {$gameState.topic.grade === 'dunyanin_enleri' ? '🌍' : '📚'} {$gameState.topic.label}
      </span>
    {/if}
    <div class="text-7xl mb-3">🏆</div>
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
        {@const colors = getPlayerColor(player.color)}
        <div class="flex items-center gap-4 bg-gradient-to-r {colors.gradient} border-2 {colors.border} p-5 rounded-xl shadow-md transition-all {i === 0 ? 'scale-[1.02]' : ''}">
          <span class="text-4xl w-14 text-center">
            {#if i === 0}🥇
            {:else if i === 1}🥈
            {:else if i === 2}🥉
            {:else}<span class="font-bold text-gray-600 text-2xl">{i + 1}.</span>
            {/if}
          </span>
          <span class="flex-1 font-bold text-xl {colors.text}">{player.name}</span>
          <span class="font-bold text-3xl {colors.text}">{player.score}</span>
        </div>
      {/each}
    </div>
  </div>

  {#if myAnswers && $gameState.results?.questions_summary}
    <div class="mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <h3 class="font-semibold text-gray-700 text-xl">Kavram Eşleştirme Sonuçlarınız</h3>
        {#if myFinalScore}
          <span class="text-sm font-bold px-3 py-1 rounded-full bg-cyan-100 text-cyan-800">
            {myFinalScore.correct_count} / {$gameState.results.questions_summary.length} Doğru (+{myFinalScore.bonus_score} puan)
          </span>
        {/if}
      </div>

      <div class="space-y-3 bg-gray-50 p-4 rounded-lg border-2 border-gray-200">
        {#each $gameState.results.questions_summary as q, i}
          {@const myAnswer = myAnswers.find((a) => a.question_index === i)}
          <div class="p-4 rounded-lg border-2 {myAnswer?.is_correct ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'}">
            <p class="font-semibold text-gray-800 mb-2">
              {i + 1}. {q.question}
            </p>
            <div class="space-y-1">
              {#if myAnswer?.user_answer}
                <p class="text-sm {myAnswer.is_correct ? 'text-green-700' : 'text-red-700'} font-semibold">
                  {myAnswer.is_correct ? '✓' : '✗'} Eşleştirdiğiniz kavram: {myAnswer.user_answer}
                </p>
              {:else}
                <p class="text-sm text-gray-500 italic">
                  Eşleştirme yapmadınız
                </p>
              {/if}
              {#if !myAnswer?.is_correct}
                <p class="text-sm text-green-700 font-semibold">
                  ✓ Doğru kavram: {q.correct_answer}
                </p>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  {#if isHost}
    <div class="space-y-3">
      <button
        on:click={restartGame}
        class="btn btn-primary w-full text-xl py-4"
      >
        Yeni Oyun Başlat
      </button>
      <button
        on:click={returnToLobby}
        class="btn btn-secondary w-full text-lg py-3"
      >
        Lobiye Dön (Konu Değiştirilebilir)
      </button>
      <button
        on:click={leaveGame}
        class="btn btn-outline w-full text-gray-600"
      >
        Oyundan Çık
      </button>
    </div>
  {:else}
    <div class="space-y-3">
      <div class="bg-gray-100 p-4 rounded-lg text-center">
        <p class="text-gray-600">Oyun yöneticisinin kararı bekleniyor...</p>
      </div>
      <button
        on:click={leaveGame}
        class="btn btn-outline w-full text-gray-600"
      >
        Oyundan Çık
      </button>
    </div>
  {/if}

  <div class="mt-6 text-center text-gray-600">
    <p>Oynadığınız için teşekkürler!</p>
  </div>
</div>
