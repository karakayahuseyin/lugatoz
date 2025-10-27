<script>
  import { onMount } from 'svelte';
  import { updateGameState } from '../stores/gameStore';

  export let playerName = '';
  export let onRoomSelect = (roomCode) => {};

  let rooms = [];
  let loading = true;

  onMount(async () => {
    await loadRooms();
  });

  async function loadRooms() {
    try {
      const response = await fetch('/api/rooms');
      rooms = await response.json();
      loading = false;
    } catch (error) {
      console.error('Odalar yüklenemedi:', error);
      loading = false;
    }
  }

  function selectRoom(roomCode) {
    onRoomSelect(roomCode);
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
          on:click={() => selectRoom(room.code)}
          disabled={!room.available}
          class="text-left p-6 rounded-lg border-2 transition-all {
            room.available
              ? 'border-cyan-200 hover:border-cyan-400 hover:shadow-lg bg-white cursor-pointer'
              : 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
          }"
        >
          <div class="flex justify-between items-start mb-3">
            <h3 class="font-bold text-lg text-gray-800">{room.name}</h3>
            <div class="flex items-center gap-2">
              <span class="text-sm {room.available ? 'text-cyan-600' : 'text-gray-500'} font-semibold">
                {room.players}/{room.max_players}
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
              <span class="text-gray-400 text-sm">Dolu</span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  {/if}

  <div class="mt-6 text-center">
    <button
      on:click={() => window.location.reload()}
      class="text-cyan-600 hover:text-cyan-700 font-semibold text-sm"
    >
      ← Geri Dön
    </button>
  </div>
</div>
