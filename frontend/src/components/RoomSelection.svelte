<script>
  import { onMount } from 'svelte';
  import HowToPlay from './HowToPlay.svelte';
  import { userStore } from '../stores/userStore';
  import { socketManager } from '../utils/socket';
  import { DEFAULT_CURRICULUM, fetchCurriculum, formatTopicLabel } from '../utils/curriculum';

  export let playerName = '';
  export let selectedGrade = null;
  export let selectedTheme = null;
  export let onRoomSelect = () => {};
  export let onBack = () => {};

  let sections = DEFAULT_CURRICULUM;
  let rooms = [];
  let loading = true;
  let showHowToPlay = false;
  let showStats = false;
  let userStats = null;
  let loadingStats = false;

  $: userId = $userStore.userId;
  $: selectedTopicLabel = formatTopicLabel(sections, selectedGrade, selectedTheme);

  onMount(async () => {
    const [currData] = await Promise.all([fetchCurriculum(), loadRooms()]);
    sections = currData.sections;

    return () => {
      const socket = socketManager.getSocket();
      if (socket) {
        socket.off('user_stats_data');
        socket.off('user_stats_error');
      }
    };
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

  function isRoomSameTopic(room) {
    if (!room.grade) return false;
    return room.grade === selectedGrade && (room.theme || null) === (selectedTheme || null);
  }

  function canJoinRoom(room) {
    if (!room.available) return false;
    if (room.players.length === 0) return true;
    return isRoomSameTopic(room);
  }

  function isRoomDifferentTopic(room) {
    return room.phase === 'waiting' && room.players.length > 0 && !isRoomSameTopic(room);
  }

  function selectRoom(room) {
    if (!canJoinRoom(room)) return;
    onRoomSelect(room.room_code);
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
    if (!socket) {
      loadingStats = false;
      return;
    }

    socket.off('user_stats_data');
    socket.off('user_stats_error');

    socket.on('user_stats_data', (data) => {
      userStats = data.stats;
      loadingStats = false;
    });

    socket.on('user_stats_error', (data) => {
      console.error('İstatistik hatası:', data.message);
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

<div class="card max-w-4xl w-full my-4">
  <div class="text-center mb-6">
    <h1 class="text-4xl font-bold text-primary mb-2">ODA SEÇİMİ</h1>
    <p class="text-gray-600">Hoş geldin, <strong>{playerName}</strong>!</p>

    {#if selectedTopicLabel}
      <div class="mt-3 inline-flex items-center gap-2 bg-gradient-to-r from-cyan-50 to-lime-50 border-2 border-cyan-300 text-cyan-900 px-4 py-2 rounded-full text-sm font-bold">
        <span>{selectedGrade === 'dunyanin_enleri' ? '🌍' : '📚'}</span>
        <span>{selectedTopicLabel}</span>
      </div>
    {/if}

    <p class="text-xs text-gray-500 mt-2">
      Boş bir odaya veya aynı konudaki bekleyen odaya katılabilirsiniz
    </p>
  </div>

  {#if loading}
    <div class="text-center py-8">
      <p class="text-gray-500">Odalar yükleniyor...</p>
    </div>
  {:else}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      {#each rooms as room}
        {@const joinable = canJoinRoom(room)}
        {@const sameTopic = isRoomSameTopic(room)}
        {@const diffTopic = isRoomDifferentTopic(room)}
        <button
          on:click={() => selectRoom(room)}
          disabled={!joinable}
          class="text-left p-5 rounded-xl border-2 transition-all {
            joinable
              ? sameTopic
                ? 'border-lime-400 hover:border-lime-500 hover:shadow-lg bg-lime-50/40 cursor-pointer'
                : 'border-cyan-200 hover:border-cyan-400 hover:shadow-lg bg-white cursor-pointer'
              : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-65'
          }"
        >
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3 class="font-bold text-base text-gray-800">{room.name}</h3>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm {joinable ? 'text-cyan-600' : 'text-gray-500'} font-semibold">
                {room.players.length}/{room.max_players}
              </span>
              <span class="w-3 h-3 rounded-full {joinable ? 'bg-green-500' : 'bg-red-400'}"></span>
            </div>
          </div>

          <p class="text-xs text-gray-600 mb-3 line-clamp-2">
            {room.description}
          </p>

          {#if room.topic}
            <div class="mb-3">
              <span class="inline-block text-xs font-semibold px-2.5 py-1 rounded-md {
                sameTopic
                  ? 'bg-lime-100 text-lime-800 border border-lime-300'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
              }">
                {room.grade === 'dunyanin_enleri' ? '🌍' : '📚'} {room.topic.label}
              </span>
            </div>
          {/if}

          <div class="flex justify-between items-center">
            <span class="text-xs px-2 py-1 rounded-full {
              room.phase === 'waiting' ? 'bg-cyan-100 text-cyan-700' : 'bg-yellow-100 text-yellow-700'
            }">
              {room.phase === 'waiting' ? (room.players.length === 0 ? 'Boş' : 'Bekliyor') : 'Oyunda'}
            </span>

            {#if joinable}
              <span class="{sameTopic ? 'text-lime-700' : 'text-cyan-600'} font-semibold text-sm">
                {sameTopic ? 'Aynı Konu • Katıl →' : 'Katıl →'}
              </span>
            {:else if diffTopic}
              <span class="text-amber-600 text-xs font-semibold">Farklı bölüm/tema</span>
            {:else}
              <span class="text-gray-400 text-sm">
                {room.phase === 'waiting' ? 'Dolu' : 'Oyun devam ediyor'}
              </span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}

  <div class="mt-6 flex flex-wrap justify-center gap-6">
    <button
      on:click={onBack}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm"
    >
      ← Bölüm / Tema Değiştir
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
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" on:click={toggleStats} on:keydown={(e) => e.key === 'Escape' && toggleStats()} role="dialog" aria-modal="true" tabindex="-1">
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <div class="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden shadow-2xl" on:click|stopPropagation on:keydown|stopPropagation role="document">
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

      <div class="p-6 overflow-y-auto" style="max-height: calc(90vh - 140px);">
        {#if loadingStats}
          <div class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
            <p class="text-gray-600 mt-4">İstatistikler yükleniyor...</p>
          </div>
        {:else if userStats}
          <div class="space-y-4">
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

            <div class="bg-gradient-to-r from-green-50 to-lime-50 rounded-xl p-4 border-2 border-green-200">
              <h3 class="text-lg font-bold text-gray-800 mb-3">❓ Eşleştirme</h3>
              <div class="grid grid-cols-3 gap-3">
                <div class="bg-white rounded-lg p-3">
                  <p class="text-xs text-gray-600">Toplam Kavram</p>
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
