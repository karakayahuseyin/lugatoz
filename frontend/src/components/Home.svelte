<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { notifications } from '../stores/notificationStore';
  import HowToPlay from './HowToPlay.svelte';

  let playerName = '';
  let showHowToPlay = false;
  export let onNameSubmit = (name) => {};

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
</script>

<div class="card max-w-md w-full">
  <div class="text-center mb-8">
    <!-- Logo Placeholder -->
    <div class="mb-4 flex justify-center">
      <div class="w-32 h-32 bg-gradient-to-br from-cyan-400 to-lime-400 rounded-full flex items-center justify-center shadow-lg">
        <span class="text-white text-5xl font-bold">ÖB</span>
      </div>
    </div>

    <h1 class="text-5xl font-bold text-primary mb-2">ÖzBilig</h1>
    <p class="text-gray-600">Kökten Geleceğe Kelime Köprüsü. Dilimizin Zenginliği Seni Bekliyor</p>
    <p class="text-sm text-gray-500 mt-2">En fazla 4 kişiyle oyna!</p>
  </div>

  <div class="mb-6">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      İsminiz
    </label>
    <input
      type="text"
      bind:value={playerName}
      placeholder="İsminizi girin"
      class="input"
      maxlength="20"
      on:keypress={(e) => e.key === 'Enter' && submitName()}
      autofocus
    />
  </div>

  <button
    on:click={submitName}
    class="btn btn-primary w-full text-xl py-4"
  >
    Devam Et
  </button>

  <div class="mt-6 text-center">
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
