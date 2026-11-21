<script>
  import { onMount } from 'svelte';
  import { gameState, updateGameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';
  import { DEFAULT_CURRICULUM, fetchCurriculum } from '../utils/curriculum';
  import HowToPlay from './HowToPlay.svelte';
  import { getPlayerColor } from '../utils/colors';

  export let onLeave = () => {};

  let showHowToPlay = false;
  let showTopicEditor = false;
  let sections = DEFAULT_CURRICULUM;
  let editGrade = null;
  let editTheme = null;

  onMount(async () => {
    const data = await fetchCurriculum();
    sections = data.sections;
  });

  $: currentGrade = $gameState.topic?.grade || $gameState.selectedGrade;
  $: currentTheme = $gameState.topic?.theme || $gameState.selectedTheme;
  $: activeQuestionCount = getActiveCount(sections, currentGrade, currentTheme);

  $: editSection = sections.find((s) => s.id === editGrade) || null;
  $: canSaveTopic = Boolean(editSection && (!editSection.has_themes || editTheme));

  function getActiveCount(list, gradeId, themeId) {
    if (!gradeId) return null;
    const sec = list.find((s) => s.id === gradeId);
    if (!sec) return null;
    if (!sec.has_themes) return sec.active_questions;
    const th = sec.themes.find((t) => t.id === themeId);
    return th ? th.active_questions : 0;
  }

  function openTopicEditor() {
    editGrade = currentGrade;
    editTheme = currentTheme;
    showTopicEditor = !showTopicEditor;
  }

  function selectEditGrade(gradeId) {
    if (editGrade !== gradeId) {
      editGrade = gradeId;
      editTheme = null;
    }
  }

  function saveTopic() {
    if (!canSaveTopic) {
      notifications.warning('Lütfen geçerli bir bölüm ve tema seçin!');
      return;
    }
    socketManager.emit('set_room_topic', {
      grade: editSection.id,
      theme: editSection.has_themes ? editTheme : null
    });
    showTopicEditor = false;
  }

  function startGame() {
    socketManager.emit('start_game', {});
  }

  function leaveRoom() {
    socketManager.emit('leave_room', {});
    socketManager.clearRoomInfo();
    updateGameState({
      phase: 'home',
      roomCode: null,
      players: [],
      isHost: false
    });
    onLeave();
  }

  function toggleHowToPlay() {
    showHowToPlay = !showHowToPlay;
  }
</script>

<div class="card max-w-2xl w-full my-4">
  <div class="text-center mb-6">
    <h1 class="text-4xl font-bold text-primary mb-2">BEKLEME ODASI</h1>
    <p class="text-gray-500">Diğer oyuncuları bekleyin...</p>
  </div>

  <!-- Seçili Bölüm ve Tema Bilgisi -->
  {#if $gameState.topic}
    <div class="bg-gradient-to-r from-cyan-50 to-lime-50 border-2 border-cyan-300 rounded-xl p-4 mb-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Seçili Konu</p>
          <p class="text-lg font-bold text-cyan-900 mt-0.5">
            {$gameState.topic.grade === 'dunyanin_enleri' ? '🌍' : '📚'} {$gameState.topic.label}
          </p>
          {#if activeQuestionCount !== null}
            <p class="text-xs mt-1 {activeQuestionCount > 0 ? 'text-green-700 font-semibold' : 'text-amber-700 font-semibold'}">
              {activeQuestionCount > 0
                ? `${activeQuestionCount} aktif soru hazır (En fazla ${Math.min(10, activeQuestionCount)} soru sorulacak)`
                : 'Bu bölüm/temada henüz aktif soru bulunmuyor!'}
            </p>
          {/if}
        </div>
        {#if $gameState.isHost}
          <button
            type="button"
            on:click={openTopicEditor}
            class="text-xs font-semibold px-3 py-2 rounded-lg border-2 border-cyan-400 text-cyan-700 hover:bg-cyan-100 transition-colors whitespace-nowrap"
          >
            {showTopicEditor ? 'Vazgeç' : 'Bölüm / Tema Değiştir'}
          </button>
        {/if}
      </div>

      {#if showTopicEditor && $gameState.isHost}
        <div class="mt-4 pt-4 border-t border-cyan-200 space-y-3">
          <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {#each sections as sec}
              <button
                type="button"
                on:click={() => selectEditGrade(sec.id)}
                class="px-3 py-2 rounded-lg border-2 text-xs font-bold transition-all {
                  editGrade === sec.id
                    ? 'border-cyan-500 bg-cyan-500 text-white'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-cyan-300'
                }"
              >
                {sec.name} ({sec.active_questions})
              </button>
            {/each}
          </div>

          {#if editSection && editSection.has_themes}
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {#each editSection.themes as th}
                <button
                  type="button"
                  on:click={() => editTheme = th.id}
                  class="px-3 py-2 rounded-lg border-2 text-left text-xs font-semibold transition-all flex justify-between items-center gap-2 {
                    editTheme === th.id
                      ? 'border-lime-500 bg-lime-500 text-white'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-lime-400'
                  }"
                >
                  <span>{th.full_name}</span>
                  <span class="opacity-80">({th.active_questions})</span>
                </button>
              {/each}
            </div>
          {/if}

          <button
            type="button"
            on:click={saveTopic}
            disabled={!canSaveTopic}
            class="btn btn-primary w-full text-sm py-2 {!canSaveTopic ? 'opacity-50 cursor-not-allowed' : ''}"
          >
            Konuyu Güncelle
          </button>
        </div>
      {/if}
    </div>
  {/if}

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-3">
      Oyuncular ({$gameState.players.length}/4)
    </h3>
    <div class="grid grid-cols-2 gap-3">
      {#each $gameState.players as player}
        {@const colors = getPlayerColor(player.color)}
        <div class="bg-gradient-to-r {colors.gradient} p-4 rounded-lg border-2 {colors.border}">
          <div class="text-center">
            <div class="font-semibold {colors.text}">{player.name}</div>
            {#if player.is_host}
              <span class="{colors.badge} text-white text-xs px-2 py-1 rounded-full font-bold inline-block mt-2">
                OYUN YÖNETİCİSİ
              </span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>

  {#if $gameState.isHost}
    {@const cannotStart = $gameState.players.length < 2 || activeQuestionCount === 0}
    <button
      on:click={startGame}
      disabled={cannotStart}
      class="btn btn-success w-full text-xl py-4 {cannotStart ? 'opacity-50 cursor-not-allowed' : ''}"
    >
      Oyunu Başlat
    </button>
    {#if $gameState.players.length < 2}
      <p class="text-center text-red-500 text-sm mt-2">
        Oyunu başlatmak için en az 2 oyuncu gerekli!
      </p>
    {:else if activeQuestionCount === 0}
      <p class="text-center text-amber-700 text-sm mt-2">
        Bu temada aktif soru yok! Lütfen başka bir tema seçin veya admin panelinden soru ekleyin.
      </p>
    {/if}
  {:else}
    <div class="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 text-center">
      <p class="text-blue-800 font-semibold">
        Oyun yöneticisinin oyunu başlatmasını bekleyin...
      </p>
    </div>
  {/if}

  <div class="mt-6 pt-6 border-t border-gray-200 flex justify-center gap-6">
    <button
      on:click={leaveRoom}
      class="text-red-500 hover:text-red-600 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>←</span>
      Odadan Ayrıl
    </button>
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
