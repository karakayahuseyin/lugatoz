<script>
  import { gameState } from '../stores/gameStore';
  import Timer from './Timer.svelte';
  import { getPlayerColor } from '../utils/colors';
  import EmojiPicker from './EmojiPicker.svelte';
  import { socketManager } from '../utils/socket';
  import { onMount } from 'svelte';

  let timer;
  let showEmojiPicker = {};
  let reactions = {};

  function handleTimeout() {
    // Timer finished - backend will automatically proceed to next round
    // No action needed from frontend
  }

  function toggleEmojiPicker(playerName) {
    showEmojiPicker = {
      ...showEmojiPicker,
      [playerName]: !showEmojiPicker[playerName]
    };
  }

  function handleEmojiSelect(event) {
    const { answer, emoji } = event.detail;
    // answer here is the player name
    socketManager.emit('add_reaction', { answer, emoji });
    showEmojiPicker[answer] = false;
  }

  onMount(() => {
    // Listen for reaction updates
    const socket = socketManager.getSocket();
    socket.on('reaction_added', (data) => {
      reactions = data.all_reactions;
    });

    return () => {
      socket.off('reaction_added');
    };
  });

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
    <p class="text-center text-gray-700 mb-2 font-semibold">Dogru Cevap:</p>
    <p class="text-3xl font-bold text-cyan-800 text-center">
      {$gameState.results?.correct_answer}
    </p>
    {#if $gameState.results?.acceptable_answers}
      <p class="text-center text-gray-600 mt-3 text-sm font-semibold">Kabul Edilebilir Cevaplar:</p>
      <p class="text-lg text-cyan-700 text-center">
        {$gameState.results.acceptable_answers}
      </p>
    {/if}
  </div>

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-4 text-xl">Oyuncu Sonuçları:</h3>
    <div class="space-y-3">
      {#each $gameState.results?.player_votes || [] as vote}
        <div class="bg-gray-50 p-4 rounded-lg border-2 {vote.was_correct ? 'border-cyan-300 bg-cyan-50' : 'border-gray-200'} relative">
          <div class="flex justify-between items-start mb-2">
            <div class="flex items-center gap-2">
              <span class="font-bold text-lg text-gray-800">{vote.player_name}</span>
              <button
                on:click={() => toggleEmojiPicker(vote.player_name)}
                class="text-xl hover:scale-125 transition-transform"
                type="button"
                title="Tepki ekle"
              >
                😊
              </button>
            </div>
            {#if vote.was_correct}
              <span class="bg-cyan-500 text-white text-xs px-3 py-1 rounded-full font-bold">
                +1000 PUAN
              </span>
            {/if}
          </div>

          <!-- Show reactions for this player -->
          {#if reactions[vote.player_name?.toLowerCase()]}
            <div class="flex gap-2 flex-wrap mb-2">
              {#each Object.entries(reactions[vote.player_name.toLowerCase()]) as [_senderId, reaction]}
                <span class="text-lg bg-white/70 px-2 py-1 rounded-lg border" title={reaction.player_name || ''}>
                  {reaction.emoji || reaction} <span class="text-xs text-gray-500">{reaction.player_name || ''}</span>
                </span>
              {/each}
            </div>
          {/if}

          <!-- Emoji Picker -->
          {#if showEmojiPicker[vote.player_name]}
            <div class="absolute top-12 left-0 z-50">
              <EmojiPicker
                answer={vote.player_name}
                show={showEmojiPicker[vote.player_name]}
                on:select={handleEmojiSelect}
              />
            </div>
          {/if}

          <div class="text-sm space-y-1">
            <div class="flex items-center gap-2">
              <span class="text-gray-600">Sectigi:</span>
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
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-gray-600">Yaniltici cevabi:</span>
                <span class="font-semibold text-cyan-700">"{vote.fake_answer}"</span>
                {#if vote.votes_received > 0}
                  <span class="bg-purple-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                    {vote.votes_received} kisi kandi! (+{vote.votes_received * 500} puan)
                  </span>
                {:else}
                  <span class="bg-gray-400 text-white text-xs px-2 py-1 rounded-full">
                    Kimseyi kandiramadi
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
        {@const colors = getPlayerColor(player.color)}
        <div class="flex items-center gap-4 bg-gradient-to-r {colors.gradient} border-2 {colors.border} p-4 rounded-lg">
          <span class="text-3xl font-bold text-gray-700 w-10">
            {#if i === 0}🥇
            {:else if i === 1}🥈
            {:else if i === 2}🥉
            {:else}{i + 1}.
            {/if}
          </span>
          <span class="flex-1 font-semibold text-lg {colors.text}">{player.name}</span>
          <span class="font-bold text-2xl {colors.text}">{player.score}</span>
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
