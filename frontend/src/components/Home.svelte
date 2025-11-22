<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { notifications } from '../stores/notificationStore';
  import { userStore } from '../stores/userStore';
  import UserAuth from './UserAuth.svelte';
  import HowToPlay from './HowToPlay.svelte';
  import Leaderboard from './Leaderboard.svelte';

  let playerName = '';
  let showHowToPlay = false;
  let showAuth = false;
  let showLeaderboard = false;
  export let onNameSubmit = (name) => {};

  // Check if user is logged in
  $: isLoggedIn = $userStore.isLoggedIn;
  $: if (isLoggedIn && $userStore.username) {
    playerName = $userStore.username;
  }

  function handleAuthComplete() {
    showAuth = false;
  }

  function submitName() {
    if (!playerName.trim()) {
      notifications.warning('Lütfen isminizi girin!');
      return;
    }

    onNameSubmit(playerName.trim());
  }

  function toggleHowToPlay() {
    showHowToPlay = !showHowToPlay;
  }

  function openAuth() {
    showAuth = true;
  }

  function openLeaderboard() {
    showLeaderboard = true;
  }

  function logout() {
    userStore.logout();
    playerName = '';
    notifications.info('Çıkış yapıldı');
  }
</script>

<div class="card max-w-md w-full">
  <div class="text-center mb-8">
    <!-- Logo -->
    <div class="mb-4 flex justify-center">
      <img src="/lugatoz.png" alt="LügaTöz Logo" class="w-32 h-32 object-contain" />
    </div>

    <h1 class="text-5xl font-bold text-primary mb-2">LügaTöz</h1>
    <p class="text-gray-600">Kökten Geleceğe Kelime Köprüsü. Dilimizin Zenginliği Seni Bekliyor</p>
    <p class="text-sm text-gray-500 mt-2">En fazla 4 kişiyle oyna!</p>
  </div>

  <!-- User Status -->
  {#if isLoggedIn}
    <div class="bg-green-50 border-2 border-green-300 rounded-xl p-4 mb-4">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm text-gray-600">Hoş geldin!</p>
          <p class="text-lg font-bold text-green-700">{$userStore.username}</p>
          <p class="text-xs text-gray-500">ID: {$userStore.userId}</p>
        </div>
        <button
          on:click={logout}
          class="text-red-600 hover:text-red-700 text-sm font-semibold"
        >
          Çıkış
        </button>
      </div>
    </div>
  {:else}
    <div class="bg-cyan-50 border-2 border-cyan-300 rounded-xl p-4 mb-4">
      <p class="text-sm text-gray-600 mb-2">İstatistiklerinizi kaydetmek için:</p>
      <button
        on:click={openAuth}
        class="btn btn-secondary w-full text-sm py-2"
      >
        Giriş Yap / Kayıt Ol
      </button>
    </div>
  {/if}

  <div class="mb-6">
    <label for="player-name-input" class="block text-sm font-medium text-gray-700 mb-2">
      İsminiz
    </label>
    <input
      id="player-name-input"
      type="text"
      bind:value={playerName}
      placeholder="İsminizi girin"
      class="input"
      maxlength="20"
      on:keypress={(e) => e.key === 'Enter' && submitName()}
    />
  </div>

  <button
    on:click={submitName}
    class="btn btn-primary w-full text-xl py-4"
  >
    Devam Et
  </button>

  <div class="mt-6 flex justify-center gap-6">
    <button
      on:click={toggleHowToPlay}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>📖</span>
      Nasıl Oynanır?
    </button>
    <button
      on:click={openLeaderboard}
      class="text-lime-600 hover:text-lime-700 font-semibold text-sm inline-flex items-center gap-1"
    >
      <span>🏆</span>
      Liderlik Tablosu
    </button>
  </div>
</div>

{#if showAuth}
  <UserAuth onComplete={handleAuthComplete} />
{/if}

{#if showHowToPlay}
  <HowToPlay onClose={toggleHowToPlay} />
{/if}

{#if showLeaderboard}
  <Leaderboard onClose={() => showLeaderboard = false} />
{/if}
