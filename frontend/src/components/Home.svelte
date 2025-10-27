<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { notifications } from '../stores/notificationStore';

  let playerName = '';
  export let onNameSubmit = (name) => {};

  function submitName() {
    if (!playerName.trim()) {
      notifications.warning('Lütfen isminizi girin!');
      return;
    }

    onNameSubmit(playerName.trim());
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

  <div class="mt-8 pt-6 border-t border-gray-200">
    <h3 class="font-semibold text-gray-800 mb-2">Nasıl Oynanır?</h3>
    <ul class="text-sm text-gray-600 space-y-1">
      <li>1. Soru gösterilir</li>
      <li>2. Herkes yanlış bir cevap ekler</li>
      <li>3. Tüm şıklar arasından doğruyu bul</li>
      <li>4. 10 soru sonunda final testi!</li>
    </ul>
  </div>
</div>
