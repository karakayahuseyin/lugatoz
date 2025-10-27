<script>
  import { gameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';

  function startGame() {
    socketManager.emit('start_game', {});
  }
</script>

<div class="card max-w-2xl w-full">
  <div class="text-center mb-6">
    <h1 class="text-4xl font-bold text-primary mb-2">BEKLEME ODASI</h1>
    <p class="text-gray-500">Diğer oyuncuları bekleyin...</p>
  </div>

  <div class="mb-6">
    <h3 class="font-semibold text-gray-700 mb-3">
      Oyuncular ({$gameState.players.length}/4)
    </h3>
    <div class="grid grid-cols-2 gap-3">
      {#each $gameState.players as player}
        <div class="bg-gradient-to-r from-cyan-50 to-lime-50 p-4 rounded-lg border-2 {player.is_host ? 'border-lime-400' : 'border-cyan-200'}">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-gray-800">{player.name}</span>
            {#if player.is_host}
              <span class="bg-lime-400 text-lime-900 text-xs px-2 py-1 rounded-full font-bold">
                OYUN YÖNETİCİSİ
              </span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>

  {#if $gameState.isHost}
    <button
      on:click={startGame}
      disabled={$gameState.players.length < 2}
      class="btn btn-success w-full text-xl py-4 {$gameState.players.length < 2 ? 'opacity-50 cursor-not-allowed' : ''}"
    >
      Oyunu Başlat
    </button>
    {#if $gameState.players.length < 2}
      <p class="text-center text-red-500 text-sm mt-2">
        Oyunu başlatmak için en az 2 oyuncu gerekli!
      </p>
    {/if}
  {:else}
    <div class="bg-blue-50 border-2 border-blue-200 rounded-lg p-4 text-center">
      <p class="text-blue-800 font-semibold">
        Oyun yöneticisinin oyunu başlatmasını bekleyin...
      </p>
    </div>
  {/if}

  <div class="mt-6 pt-6 border-t border-gray-200">
    <h4 class="font-semibold text-gray-700 mb-2">Oyun Kuralları:</h4>
    <ul class="text-sm text-gray-600 space-y-2">
      <li>• Her turda 10 soru bulunmaktadır</li>
      <li>• Her oyuncunun doğru cevaptan farklı bir seçenek yazması gerekir</li>
      <li>• <strong>Amaç:</strong> Doğru cevabı bulmak ve rakibi yanıltmak</li>
      <li>• Doğru cevap: <strong>+1000 puan</strong></li>
      <li>• Başkaları sizin yanlış cevabınızı seçerse: Her biri için <strong>+500 puan</strong></li>
      <li>• Süresi içerisinde seçenek eklemez veya cevap vermezseniz <strong>-100 puan</strong> kaybedersiniz</li>
      <li>• 10 soruluk tur bitiminde final testi var!</li>
    </ul>
  </div>
</div>
