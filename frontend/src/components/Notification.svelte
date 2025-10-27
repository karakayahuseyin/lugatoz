<script>
  import { fade, fly } from 'svelte/transition';

  export let message = '';
  export let type = 'info'; // info, success, warning, error
  export let duration = 3000;
  export let onClose = () => {};

  let visible = true;

  setTimeout(() => {
    visible = false;
    setTimeout(onClose, 300);
  }, duration);

  function close() {
    visible = false;
    setTimeout(onClose, 300);
  }

  $: bgColor = {
    info: 'bg-cyan-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500'
  }[type];

  $: icon = {
    info: 'ℹ️',
    success: '✓',
    warning: '⚠️',
    error: '✗'
  }[type];
</script>

{#if visible}
  <div
    transition:fly={{ y: -50, duration: 300 }}
    class="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 max-w-md w-full px-4"
  >
    <div class="{bgColor} text-white rounded-xl shadow-2xl p-4 flex items-center gap-3">
      <span class="text-2xl">{icon}</span>
      <p class="flex-1 font-semibold">{message}</p>
      <button
        on:click={close}
        class="text-white hover:text-gray-200 font-bold text-xl"
      >
        ×
      </button>
    </div>
  </div>
{/if}
