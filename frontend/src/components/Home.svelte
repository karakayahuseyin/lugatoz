<script>
  import { onMount } from 'svelte';
  import { notifications } from '../stores/notificationStore';
  import { userStore } from '../stores/userStore';
  import {
    DEFAULT_CURRICULUM,
    ALL_THEMES_SLUG,
    ALL_THEMES_LABEL,
    fetchCurriculum
  } from '../utils/curriculum';
  import UserAuth from './UserAuth.svelte';
  import HowToPlay from './HowToPlay.svelte';
  import Leaderboard from './Leaderboard.svelte';

  export let initialName = '';
  export let initialGrade = null;
  export let initialTheme = null;
  export let onEntrySubmit = () => {};

  let playerName = initialName || '';
  let selectedGrade = initialGrade || null;
  let selectedTheme = initialTheme || null;
  let sections = DEFAULT_CURRICULUM;
  let loadingCurriculum = true;

  let showHowToPlay = false;
  let showAuth = false;
  let showLeaderboard = false;

  $: isLoggedIn = $userStore.isLoggedIn;
  $: if (isLoggedIn && $userStore.username && !playerName) {
    playerName = $userStore.username;
  }

  $: selectedSection = sections.find((s) => s.id === selectedGrade) || null;
  $: gradeSections = sections.filter((s) => s.has_themes);
  $: specialSection = sections.find((s) => !s.has_themes) || null;
  $: isAllThemesSelected = selectedTheme === ALL_THEMES_SLUG;
  $: selectedThemeObj = selectedSection?.has_themes && !isAllThemesSelected
    ? selectedSection.themes.find((t) => t.id === selectedTheme) || null
    : null;
  $: selectedActiveQuestions = !selectedSection
    ? 0
    : !selectedSection.has_themes || isAllThemesSelected
      ? selectedSection.active_questions
      : (selectedThemeObj?.active_questions || 0);
  $: canContinue = Boolean(
    playerName.trim() &&
    selectedSection &&
    (!selectedSection.has_themes || selectedTheme)
  );

  onMount(async () => {
    const data = await fetchCurriculum();
    sections = data.sections;
    loadingCurriculum = false;
  });

  function selectSection(gradeId) {
    if (selectedGrade !== gradeId) {
      selectedGrade = gradeId;
      selectedTheme = null;
    }
  }

  function selectTheme(themeId) {
    selectedTheme = themeId;
  }

  function handleAuthComplete() {
    showAuth = false;
    if ($userStore.isLoggedIn && $userStore.username) {
      playerName = $userStore.username;
    }
  }

  function submitEntry() {
    if (!playerName.trim()) {
      notifications.warning('Lütfen isminizi girin!');
      return;
    }
    if (!selectedSection) {
      notifications.warning('Lütfen bir sınıf veya bölüm seçin!');
      return;
    }
    if (selectedSection.has_themes && !selectedTheme) {
      notifications.warning('Lütfen bu sınıfa ait bir tema seçin!');
      return;
    }

    onEntrySubmit({
      name: playerName.trim(),
      grade: selectedSection.id,
      theme: selectedSection.has_themes ? selectedTheme : null
    });
  }

  function logout() {
    userStore.logout();
    playerName = '';
    notifications.info('Çıkış yapıldı');
  }
</script>

<div class="card max-w-2xl w-full my-4">
  <div class="text-center mb-6">
    <div class="mb-3 flex justify-center">
      <img src="/tarihtoz-logo.png" alt="TarihTöz Logo" class="w-28 h-28 object-contain rounded-2xl" />
    </div>

    <h1 class="text-4xl md:text-5xl font-bold text-primary mb-1">TarihTöz</h1>
    <p class="text-gray-600 text-sm md:text-base">Tarih ve Sosyal Bilgiler Bilgi Yarışması</p>
    <p class="text-xs text-gray-500 mt-1">Sınıfını ve temanı seç, en fazla 4 kişiyle yarış!</p>
  </div>

  <!-- Kullanıcı Durumu -->
  {#if isLoggedIn}
    <div class="bg-green-50 border-2 border-green-300 rounded-xl p-3 mb-5 flex items-center justify-between">
      <div>
        <span class="text-xs text-gray-500">Hoş geldin,</span>
        <span class="text-base font-bold text-green-700 ml-1">{$userStore.username}</span>
        <span class="text-xs text-gray-500 ml-2">(ID: {$userStore.userId})</span>
      </div>
      <button
        on:click={logout}
        class="text-red-600 hover:text-red-700 text-sm font-semibold px-2 py-1"
      >
        Çıkış
      </button>
    </div>
  {:else}
    <div class="bg-cyan-50 border-2 border-cyan-200 rounded-xl p-3 mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <p class="text-sm text-gray-600">İstatistiklerinizi kaydetmek için giriş yapabilirsiniz:</p>
      <button
        on:click={() => showAuth = true}
        class="btn btn-secondary text-sm py-2 px-4 whitespace-nowrap"
      >
        Giriş Yap / Kayıt Ol
      </button>
    </div>
  {/if}

  <!-- İsim Girişi -->
  <div class="mb-6">
    <label for="player-name-input" class="block text-sm font-semibold text-gray-700 mb-2">
      İsminiz
    </label>
    <input
      id="player-name-input"
      type="text"
      bind:value={playerName}
      placeholder="İsminizi girin"
      class="input"
      maxlength="20"
      on:keypress={(e) => e.key === 'Enter' && canContinue && submitEntry()}
    />
  </div>

  <!-- 1. Adım: Bölüm / Sınıf Seçimi -->
  <div class="mb-6">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-800 flex items-center gap-2">
        <span class="w-6 h-6 rounded-full bg-primary text-white text-xs font-bold inline-flex items-center justify-center">1</span>
        Bölüm Seçin
      </h2>
      {#if loadingCurriculum}
        <span class="text-xs text-gray-400">Yükleniyor...</span>
      {/if}
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
      {#each gradeSections as section}
        {@const isSelected = selectedGrade === section.id}
        <button
          type="button"
          on:click={() => selectSection(section.id)}
          class="p-3 rounded-xl border-2 text-center transition-all duration-150 {
            isSelected
              ? 'border-cyan-500 bg-cyan-500 text-white shadow-lg scale-[1.02]'
              : 'border-gray-200 bg-white hover:border-cyan-400 hover:bg-cyan-50 text-gray-800'
          }"
        >
          <div class="text-lg font-bold">{section.name}</div>
          <div class="text-xs mt-1 {isSelected ? 'text-cyan-50' : 'text-gray-500'}">
            {section.themes.length} Tema
          </div>
          <div class="text-[11px] mt-1 font-semibold {isSelected ? 'text-white/90' : section.active_questions > 0 ? 'text-cyan-600' : 'text-gray-400'}">
            {section.active_questions} soru
          </div>
        </button>
      {/each}
    </div>

    {#if specialSection}
      {@const isSpecialSelected = selectedGrade === specialSection.id}
      <button
        type="button"
        on:click={() => selectSection(specialSection.id)}
        class="w-full p-4 rounded-xl border-2 text-left transition-all duration-150 flex items-center justify-between gap-3 {
          isSpecialSelected
            ? 'border-lime-600 bg-gradient-to-r from-lime-500 to-emerald-500 text-white shadow-lg'
            : 'border-lime-300 bg-gradient-to-r from-lime-50 to-emerald-50 hover:border-lime-500 text-gray-800'
        }"
      >
        <div class="flex items-center gap-3">
          <span class="text-2xl">🌍</span>
          <div>
            <div class="text-lg font-bold">{specialSection.name}</div>
            <div class="text-xs {isSpecialSelected ? 'text-lime-50' : 'text-gray-600'}">
              Tema seçimi olmadan doğrudan oynanır
            </div>
          </div>
        </div>
        <span class="text-xs font-bold px-3 py-1 rounded-full {
          isSpecialSelected
            ? 'bg-white/25 text-white'
            : specialSection.active_questions > 0
              ? 'bg-lime-200 text-lime-800'
              : 'bg-gray-200 text-gray-500'
        }">
          {specialSection.active_questions} soru
        </span>
      </button>
    {/if}
  </div>

  <!-- 2. Adım: Tema Seçimi (Sadece 5, 6, 7, 8. sınıflar için) -->
  {#if selectedSection && selectedSection.has_themes}
    <div class="mb-6 bg-gray-50 border-2 border-cyan-200 rounded-xl p-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-base font-bold text-gray-800 flex items-center gap-2">
          <span class="w-6 h-6 rounded-full bg-secondary text-white text-xs font-bold inline-flex items-center justify-center">2</span>
          {selectedSection.name} Temaları
        </h2>
        <span class="text-xs text-gray-500">Yalnızca seçtiğiniz temadan sorular gelir</span>
      </div>

      {#if selectedSection.themes.length === 0}
        <p class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-center">
          Bu sınıfta henüz tema bulunmuyor. Admin panelinden tema ekleyebilirsiniz.
        </p>
      {:else}
        <!-- Tüm Temalar (Karışık) Butonu -->
        <button
          type="button"
          on:click={() => selectTheme(ALL_THEMES_SLUG)}
          class="w-full mb-3 p-3.5 rounded-xl border-2 text-left transition-all duration-150 flex items-center justify-between gap-3 {
            isAllThemesSelected
              ? 'border-lime-600 bg-gradient-to-r from-cyan-500 to-lime-500 text-white shadow-md'
              : 'border-lime-300 bg-gradient-to-r from-cyan-50 to-lime-50 hover:border-cyan-500 text-gray-800'
          }"
        >
          <div class="flex items-center gap-2.5">
            <span class="flex-shrink-0 w-7 h-7 rounded-full text-sm flex items-center justify-center {
              isAllThemesSelected ? 'bg-white/25 text-white' : 'bg-white text-cyan-600 shadow-sm'
            }">
              🎲
            </span>
            <div>
              <div class="text-sm font-bold">{ALL_THEMES_LABEL}</div>
              <div class="text-xs {isAllThemesSelected ? 'text-white/90' : 'text-gray-600'}">
                {selectedSection.name} bütün temalarından rastgele sorular
              </div>
            </div>
          </div>
          <span class="flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full {
            isAllThemesSelected
              ? 'bg-white/25 text-white'
              : selectedSection.active_questions > 0
                ? 'bg-lime-200 text-lime-800'
                : 'bg-gray-200 text-gray-500'
          }">
            {selectedSection.active_questions} soru
          </span>
        </button>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {#each selectedSection.themes as theme}
            {@const isThemeSelected = selectedTheme === theme.id}
            <button
              type="button"
              on:click={() => selectTheme(theme.id)}
              class="p-3 rounded-lg border-2 text-left transition-all duration-150 flex items-start justify-between gap-2 {
                isThemeSelected
                  ? 'border-cyan-500 bg-cyan-500 text-white shadow-md'
                  : 'border-gray-200 bg-white hover:border-cyan-400 hover:bg-cyan-50/50 text-gray-800'
              }"
            >
              <div class="flex items-start gap-2.5 min-w-0">
                <span class="flex-shrink-0 w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center mt-0.5 {
                  isThemeSelected ? 'bg-white text-cyan-600' : 'bg-cyan-100 text-cyan-700'
                }">
                  {theme.order}
                </span>
                <span class="text-sm font-semibold leading-snug">{theme.name}</span>
              </div>
              <span class="flex-shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full mt-0.5 {
                isThemeSelected
                  ? 'bg-white/25 text-white'
                  : theme.active_questions > 0
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-400'
              }">
                {theme.active_questions} soru
              </span>
            </button>
          {/each}
        </div>
      {/if}

      {#if selectedTheme && selectedActiveQuestions === 0}
        <p class="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mt-3">
          Bu bölümde henüz aktif soru bulunmuyor. Admin panelinden soru eklendikten sonra oyun başlatılabilir.
        </p>
      {/if}
    </div>
  {:else if selectedSection && !selectedSection.has_themes}
    <div class="mb-6 bg-lime-50 border-2 border-lime-300 rounded-xl p-4 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2 text-sm text-lime-900 font-medium">
        <span>✅</span>
        <span><strong>{selectedSection.name}</strong> seçildi — doğrudan oda seçimine geçebilirsiniz!</span>
      </div>
      {#if selectedSection.active_questions === 0}
        <span class="text-xs text-amber-700 font-semibold">Henüz soru yok</span>
      {/if}
    </div>
  {/if}

  <button
    on:click={submitEntry}
    disabled={!canContinue}
    class="btn btn-primary w-full text-xl py-4 {!canContinue ? 'opacity-50 cursor-not-allowed' : ''}"
  >
    Devam Et
  </button>

  <div class="mt-6 flex flex-wrap justify-center gap-6">
    <button
      on:click={() => showHowToPlay = true}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>📖</span>
      Nasıl Oynanır?
    </button>
    <button
      on:click={() => showLeaderboard = true}
      class="text-lime-600 hover:text-lime-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>🏆</span>
      Liderlik Tablosu
    </button>
    <a
      href="/#admin"
      class="text-gray-500 hover:text-gray-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>⚙️</span>
      Admin Paneli
    </a>
  </div>
</div>

{#if showAuth}
  <UserAuth onComplete={handleAuthComplete} />
{/if}

{#if showHowToPlay}
  <HowToPlay onClose={() => showHowToPlay = false} />
{/if}

{#if showLeaderboard}
  <Leaderboard onClose={() => showLeaderboard = false} />
{/if}
