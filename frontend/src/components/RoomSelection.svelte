<script>
  import { onMount } from 'svelte';
  import HowToPlay from './HowToPlay.svelte';
  import { userStore } from '../stores/userStore';
  import { socketManager } from '../utils/socket';

  export let playerName = '';
  export let onRoomSelect = () => {};

  let rooms = [];
  let loading = true;
  let showHowToPlay = false;
  let showStats = false;
  let userStats = null;
  let loadingStats = false;

  $: userId = $userStore.userId;

  onMount(async () => {
    await loadRooms();
  });

  async function loadRooms() {
    try {
      const response = await fetch('/api/rooms');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      rooms = await response.json();
      loading = false;
    } catch (error) {
      console.error('Odalar yuklenemedi:', error);
      loading = false;
    }
  }

  function selectRoom(roomCode) {
    onRoomSelect(roomCode);
  }

  function refreshRooms() {
    loading = true;
    loadRooms();
  }

  function toggleHowToPlay() {
    showHowToPlay = !showHowToPlay;
  }

  function toggleStats() {
    showStats = !showStats;
    if (showStats && !userStats && userId) {
      loadUserStats();
    }
  }

  function loadUserStats() {
    if (!userId) return;

    loadingStats = true;
    const socket = socketManager.getSocket();

    socket.once('user_stats_data', (data) => {
      userStats = data.stats;
      loadingStats = false;
    });

    socketManager.emit('get_user_stats', { user_id: userId });
  }

  function getWinRate() {
    if (!userStats || userStats.total_games_played === 0) return 0;
    return Math.round((userStats.total_games_won / userStats.total_games_played) * 100);
  }

  function getAccuracy() {
    if (!userStats || userStats.total_questions_answered === 0) return 0;
    return Math.round((userStats.total_correct_answers / userStats.total_questions_answered) * 100);
  }

  function getDeceptionRate() {
    if (!userStats || userStats.total_players_deceived === 0) return 0;
    const totalDeceptionAttempts = userStats.total_players_deceived + userStats.total_times_deceived;
    if (totalDeceptionAttempts === 0) return 0;
    return Math.round((userStats.total_players_deceived / totalDeceptionAttempts) * 100);
  }
</script>

<div class="card max-w-4xl w-full">
  <div class="text-center mb-8">
    <h1 class="text-4xl font-bold text-primary mb-2">ODA SEÇİMİ</h1>
    <p class="text-gray-600">Hoş geldin, <strong>{playerName}</strong>!</p>
    <p class="text-sm text-gray-500 mt-1">Katılmak istediğin odayı seç</p>
  </div>

  {#if loading}
    <div class="text-center py-8">
      <p class="text-gray-500">Odalar yükleniyor...</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each rooms as room}
        <button
          on:click={() => selectRoom(room.room_code)}
          disabled={!room.available}
          class="text-left p-6 rounded-lg border-2 transition-all {
            room.available
              ? 'border-cyan-200 hover:border-cyan-400 hover:shadow-lg bg-white cursor-pointer'
              : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
          }"
        >
          <div class="flex justify-between items-start mb-3">
            <div>
              <p class="text-xs text-gray-500 font-mono">{room.room_code}</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm {room.available ? 'text-cyan-600' : 'text-gray-500'} font-semibold">
                {room.players.length}/{room.max_players}
              </span>
              <span class="w-3 h-3 rounded-full {room.available ? 'bg-green-500' : 'bg-red-500'}"></span>
            </div>
          </div>

          <p class="text-xs text-gray-600 mb-3 line-clamp-2">
            {room.description}
          </p>

          <div class="flex justify-between items-center">
            <span class="text-xs px-2 py-1 rounded-full {
              room.phase === 'waiting' ? 'bg-cyan-100 text-cyan-700' : 'bg-yellow-100 text-yellow-700'
            }">
              {room.phase === 'waiting' ? 'Bekliyor' : 'Oyunda'}
            </span>

            {#if room.available}
              <span class="text-cyan-600 font-semibold text-sm">Katıl →</span>
            {:else}
              <span class="text-gray-400 text-sm">{room.phase === 'waiting' ? 'Dolu' : 'Oyun devam ediyor'}</span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}

  <div class="mt-6 flex justify-center gap-6">
    <button
      on:click={() => window.location.reload()}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm"
    >
      ← Geri Dön
    </button>
    <button
      on:click={refreshRooms}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>🔄</span>
      Yenile
    </button>
    {#if userId}
      <button
        on:click={toggleStats}
        class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm inline-flex items-center gap-1"
      >
        <span>📊</span>
        İstatistiklerim
      </button>
    {/if}
    <button
      on:click={toggleHowToPlay}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>📖</span>
      Nasıl Oynanır?
    </button>
  </div>
</div>

{#if showHowToPlay}
  <HowToPlay onClose={toggleHowToPlay} />
{/if}

{#if showStats}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" on:click={toggleStats} role="dialog" aria-modal="true">
    <div class="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden shadow-2xl" on:click|stopPropagation role="document">
      <!-- Header -->
      <div class="bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white">
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-3xl font-bold">📊 İstatistiklerim</h2>
            <p class="text-purple-50 mt-1">{playerName}</p>
            <p class="text-xs text-purple-100 mt-0.5">ID: {userId}</p>
          </div>
          <button
            on:click={toggleStats}
            class="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            aria-label="Kapat"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 140px);">
        {#if loadingStats}
          <div class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            <p class="text-gray-600 mt-4">İstatistikler yükleniyor...</p>
          </div>
        {:else if userStats}
          <div class="space-y-4">
            <!-- Genel İstatistikler -->
            <div class="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4 border-2 border-purple-200">
              <h3 class="text-lg font-bold text-gray-800 mb-3">🎮 Genel</h3>
              <div class="grid grid-cols-2 gap-3">
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Toplam Puan</p>
                  <p class="text-2xl font-bold text-purple-600">{userStats.total_score.toLocaleString()}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">En Yüksek Skor</p>
                  <p class="text-2xl font-bold text-pink-600">{userStats.highest_score.toLocaleString()}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Oynanan Oyun</p>
                  <p class="text-2xl font-bold text-gray-700">{userStats.total_games_played}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Kazanılan Oyun</p>
                  <p class="text-2xl font-bold text-green-600">{userStats.total_games_won}</p>
                </div>
              </div>
            </div>

            <!-- Başarı Oranları -->
            <div class="bg-gradient-to-r from-cyan-50 to-blue-50 rounded-xl p-4 border-2 border-cyan-200">
              <h3 class="text-lg font-bold text-gray-800 mb-3">📈 Başarı Oranları</h3>
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-white rounded-lg p-3 text-center">
                  <p class="text-xs text-gray-600 mb-1">Kazanma</p>
                  <p class="text-3xl font-bold text-green-600">{getWinRate()}%</p>
                </div>
                <div class="bg-white rounded-lg p-3 text-center">
                  <p class="text-xs text-gray-600 mb-1">Doğruluk</p>
                  <p class="text-3xl font-bold text-blue-600">{getAccuracy()}%</p>
                </div>
                <div class="bg-white rounded-lg p-3 text-center">
                  <p class="text-xs text-gray-600 mb-1">Yanıltma</p>
                  <p class="text-3xl font-bold text-orange-600">{getDeceptionRate()}%</p>
                </div>
              </div>
            </div>

            <!-- Soru İstatistikleri -->
            <div class="bg-gradient-to-r from-green-50 to-lime-50 rounded-xl p-4 border-2 border-green-200">
              <h3 class="text-lg font-bold text-gray-800 mb-3">❓ Sorular</h3>
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Toplam Soru</p>
                  <p class="text-xl font-bold text-gray-700">{userStats.total_questions_answered}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Doğru</p>
                  <p class="text-xl font-bold text-green-600">{userStats.total_correct_answers}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Yanlış</p>
                  <p class="text-xl font-bold text-red-600">{userStats.total_wrong_answers}</p>
                </div>
              </div>
            </div>

            <!-- Yanıltma İstatistikleri -->
            <div class="bg-gradient-to-r from-orange-50 to-yellow-50 rounded-xl p-4 border-2 border-orange-200">
              <h3 class="text-lg font-bold text-gray-800 mb-3">🎭 Yanıltma</h3>
              <div class="grid grid-cols-2 gap-3">
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Yanılttığım Oyuncu</p>
                  <p class="text-2xl font-bold text-orange-600">{userStats.total_players_deceived}</p>
                </div>
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Yanıldığım Sayı</p>
                  <p class="text-2xl font-bold text-yellow-600">{userStats.total_times_deceived}</p>
                </div>
              </div>
            </div>
          </div>
        {:else}
          <div class="text-center py-12">
            <p class="text-gray-600 text-lg">İstatistik verisi bulunamadı</p>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
