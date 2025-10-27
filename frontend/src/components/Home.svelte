<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';

  let playerName = '';

  function joinGame() {
    if (!playerName.trim()) {
      notifications.warning('Lütfen isminizi girin!');
      return;
    }

    updateGameState({ playerName: playerName.trim() });

    socketManager.emit('join_game', {
      player_name: playerName.trim()
    });
  }
</script>

<div class="card max-w-md w-full">
  <div class="text-center mb-8">
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
      on:keypress={(e) => e.key === 'Enter' && joinGame()}
    />
  </div>

  <button
    on:click={joinGame}
    class="btn btn-primary w-full text-xl py-4"
  >
    Oyuna Katıl
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
