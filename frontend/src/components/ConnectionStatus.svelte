<script>
  import { onMount, onDestroy } from 'svelte';
  import { socketManager } from '../utils/socket';

  let isConnected = true;
  let isReconnecting = false;
  let reconnectAttempt = 0;
  let unsubscribe = null;

  onMount(() => {
    unsubscribe = socketManager.onConnectionChange((connected, reconnecting, attempt) => {
      isConnected = connected;
      isReconnecting = reconnecting;
      reconnectAttempt = attempt || 0;
    });
  });

  onDestroy(() => {
    if (unsubscribe) unsubscribe();
  });
</script>

{#if !isConnected}
  <div class="fixed top-0 left-0 right-0 z-50 bg-red-500 text-white text-center py-2 px-4 text-sm font-medium shadow-lg">
    {#if isReconnecting}
      <span class="inline-flex items-center gap-2">
        <span class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
        Bağlantı kuruluyor... {#if reconnectAttempt > 0}(Deneme {reconnectAttempt}/20){/if}
      </span>
    {:else}
      <span>Bağlantı kesildi. Lütfen internet bağlantınızı kontrol edin.</span>
    {/if}
  </div>
{/if}
