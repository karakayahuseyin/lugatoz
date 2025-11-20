<script>
  import { socketManager } from '../utils/socket';
  import { onMount } from 'svelte';

  export let onClose = () => {};

  let leaderboard = [];
  let isLoading = true;

  onMount(() => {
    const socket = socketManager.getSocket();

    socket.on('leaderboard_data', (data) => {
      leaderboard = data.leaderboard;
      isLoading = false;
    });

    // Request leaderboard - top 10 only
    socketManager.emit('get_leaderboard', { limit: 10 });

    return () => {
      socket.off('leaderboard_data');
    };
  });

  function getRankEmoji(index) {
    if (index === 0) return '🥇';
    if (index === 1) return '🥈';
    if (index === 2) return '🥉';
    return `${index + 1}.`;
  }

  function getWinRate(player) {
    if (player.games_played === 0) return 0;
    return Math.round((player.games_won / player.games_played) * 100);
  }

  function getAccuracy(player) {
    if (player.total_questions === 0) return 0;
    return Math.round((player.correct_answers / player.total_questions) * 100);
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" on:click={onClose}>
  <div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl" on:click|stopPropagation>
    <!-- Header -->
    <div class="bg-gradient-to-r from-cyan-500 to-lime-500 p-6 text-white">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-3xl font-bold">🏆 Global Liderlik Tablosu</h2>
          <p class="text-cyan-50 mt-1">En başarılı 10 oyuncu</p>
        </div>
        <button
          on:click={onClose}
          class="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 120px);">
      {#if isLoading}
        <div class="text-center py-12">
          <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
          <p class="text-gray-600 mt-4">Liderlik tablosu yükleniyor...</p>
        </div>
      {:else if leaderboard.length === 0}
        <div class="text-center py-12">
          <p class="text-gray-600 text-lg">Henüz veri yok</p>
        </div>
      {:else}
        <div class="space-y-3">
          {#each leaderboard as player, index}
            <div class="bg-gradient-to-r {
              index === 0 ? 'from-yellow-100 to-yellow-50 border-yellow-300' :
              index === 1 ? 'from-gray-100 to-gray-50 border-gray-300' :
              index === 2 ? 'from-orange-100 to-orange-50 border-orange-300' :
              'from-white to-gray-50 border-gray-200'
            } border-2 rounded-xl p-4 transition-all hover:shadow-md">
              <div class="flex items-center gap-4">
                <!-- Rank -->
                <div class="text-3xl font-bold w-12 text-center">
                  {getRankEmoji(index)}
                </div>

                <!-- User Info -->
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-xl font-bold text-gray-800">{player.username}</h3>
                  </div>

                  <!-- Stats Grid -->
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
                    <div class="bg-white/70 rounded-lg p-2">
                      <p class="text-xs text-gray-600">Toplam Puan</p>
                      <p class="text-lg font-bold text-cyan-600">{player.total_score.toLocaleString()}</p>
                    </div>
                    <div class="bg-white/70 rounded-lg p-2">
                      <p class="text-xs text-gray-600">Oynanan Oyun</p>
                      <p class="text-lg font-bold text-gray-700">{player.games_played}</p>
                    </div>
                    <div class="bg-white/70 rounded-lg p-2">
                      <p class="text-xs text-gray-600">Kazanma Oranı</p>
                      <p class="text-lg font-bold text-green-600">{getWinRate(player)}%</p>
                    </div>
                    <div class="bg-white/70 rounded-lg p-2">
                      <p class="text-xs text-gray-600">Doğruluk</p>
                      <p class="text-lg font-bold text-purple-600">{getAccuracy(player)}%</p>
                    </div>
                  </div>
                </div>

                <!-- Highest Score -->
                <div class="hidden md:block text-right">
                  <p class="text-xs text-gray-600">En Yüksek Skor</p>
                  <p class="text-2xl font-bold text-lime-600">{player.highest_score.toLocaleString()}</p>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>
