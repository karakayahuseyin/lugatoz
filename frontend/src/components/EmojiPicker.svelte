<script>
  import { createEventDispatcher } from 'svelte';

  export let answer = '';
  export let show = false;

  const dispatch = createEventDispatcher();

  // 6 most common emojis
  const emojis = ['😂', '❤️', '👍', '🔥', '😮', '🤔'];

  function selectEmoji(emoji) {
    dispatch('select', { answer, emoji });
    show = false;
  }
</script>

{#if show}
  <div class="emoji-picker">
    {#each emojis as emoji}
      <button
        class="emoji-btn"
        on:click={() => selectEmoji(emoji)}
        type="button"
      >
        {emoji}
      </button>
    {/each}
  </div>
{/if}

<style>
  .emoji-picker {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 0.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    position: absolute;
    z-index: 100;
    margin-top: 0.25rem;
  }

  .emoji-btn {
    font-size: 1.5rem;
    padding: 0.25rem 0.5rem;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: 0.25rem;
    transition: all 0.2s;
  }

  .emoji-btn:hover {
    background: #f0f0f0;
    transform: scale(1.2);
  }
</style>
