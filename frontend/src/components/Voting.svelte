<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';
  import Timer from './Timer.svelte';
  import EmojiPicker from './EmojiPicker.svelte';
  import { onMount } from 'svelte';

  let selectedAnswer = null;
  let timer;
  let timeoutReached = false;
  let showEmojiPicker = {};
  let reactions = {};

  function selectAnswer(answer) {
    if ($gameState.votedAnswer || timeoutReached) return;
    selectedAnswer = answer;
  }

  function submitVote() {
    if (!selectedAnswer) {
      notifications.warning('Lütfen bir cevap seçin!');
      return;
    }

    socketManager.emit('submit_vote', {
      answer: selectedAnswer
    });
    // Don't set votedAnswer here - wait for backend confirmation
  }

  function handleTimeout() {
    timeoutReached = true;
    // Auto-submit if user has selected something
    if (selectedAnswer) {
      submitVote();
    } else {
      notifications.error('Süre doldu! Cevap seçmediniz, -100 puan cezası aldınız.');
      // Submit empty to trigger penalty
      socketManager.emit('submit_vote', {
        answer: ''
      });
      updateGameState({ votedAnswer: true });
    }
  }

  // Listen for success from backend
  socketManager.on('vote_submitted', (data) => {
    if (data.success) {
      if (timer) timer.stop();
      updateGameState({ votedAnswer: true });
    }
  });

  // Listen for error from backend
  socketManager.on('vote_rejected', (data) => {
    if (data.reason === 'own_answer') {
      notifications.error('Kendi yanlış cevabınızı seçemezsiniz!');
      selectedAnswer = null;
    }
  });

  function toggleEmojiPicker(answer) {
    showEmojiPicker = {
      ...showEmojiPicker,
      [answer]: !showEmojiPicker[answer]
    };
  }

  function handleEmojiSelect(event) {
    const { answer, emoji } = event.detail;
    socketManager.emit('add_reaction', { answer, emoji });
    showEmojiPicker[answer] = false;
  }

  onMount(() => {
    // Listen for reaction updates
    const socket = socketManager.getSocket();
    socket.on('reaction_added', (data) => {
      reactions = data.all_reactions;
    });

    return () => {
      socket.off('reaction_added');
    };
  });
</script>

<div class="card max-w-3xl w-full">
  <div class="mb-6">
    <div class="flex justify-between items-center mb-4">
      <span class="bg-secondary text-white px-4 py-2 rounded-full font-semibold">
        Soru {$gameState.currentRound + 1} / {$gameState.maxRounds}
      </span>
      {#if !$gameState.votedAnswer}
        <Timer bind:this={timer} duration={10} onTimeout={handleTimeout} />
      {:else}
        <span class="text-gray-600 font-semibold">
          OYLAMA
        </span>
      {/if}
    </div>

    <div class="bg-gradient-to-r from-cyan-100 to-lime-100 p-6 rounded-xl border-2 border-cyan-300 mb-6">
      <p class="text-2xl font-semibold text-gray-800 text-center">
        {$gameState.currentQuestion?.text}
      </p>
    </div>
  </div>

  {#if !$gameState.votedAnswer}
    <div class="space-y-4 mb-6">
      <h3 class="text-xl font-semibold text-gray-800 text-center mb-4">
        Doğru cevabı seçin!
      </h3>

      <div class="grid gap-3">
        {#each $gameState.options as option, i}
          <div class="relative">
            <button
              on:click={() => selectAnswer(option)}
              class="p-4 rounded-lg border-2 transition-all text-left w-full {
                selectedAnswer === option
                  ? 'border-primary bg-primary text-white shadow-lg scale-105'
                  : 'border-gray-300 bg-white hover:border-primary hover:bg-cyan-50'
              }"
            >
              <div class="flex items-center gap-3">
                <span class="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-200 flex items-center justify-center font-bold {
                  selectedAnswer === option ? 'bg-white text-primary' : 'text-cyan-700'
                }">
                  {String.fromCharCode(65 + i)}
                </span>
                <span class="font-semibold text-lg flex-1">
                  {option}
                </span>
                <button
                  on:click|stopPropagation={() => toggleEmojiPicker(option)}
                  class="text-2xl hover:scale-125 transition-transform"
                  type="button"
                  title="Tepki ekle"
                >
                  😊
                </button>
              </div>

              <!-- Show reactions for this option -->
              {#if reactions[option?.toLowerCase()]}
                <div class="flex gap-1 flex-wrap mt-2 ml-11">
                  {#each Object.entries(reactions[option.toLowerCase()]) as [_playerId, emoji]}
                    <span class="text-xl">{emoji}</span>
                  {/each}
                </div>
              {/if}
            </button>

            <!-- Emoji Picker -->
            <div class="absolute top-full left-0 z-50 mt-1">
              <EmojiPicker
                answer={option}
                show={showEmojiPicker[option]}
                on:select={handleEmojiSelect}
              />
            </div>
          </div>
        {/each}
      </div>
    </div>

    <button
      on:click={submitVote}
      disabled={!selectedAnswer}
      class="btn btn-success w-full text-xl py-4 {!selectedAnswer ? 'opacity-50 cursor-not-allowed' : ''}"
    >
      Oyumu Gönder
    </button>
  {:else}
    <div class="bg-green-50 border-2 border-cyan-300 rounded-xl p-8 text-center">
      <div class="text-6xl mb-4">✓</div>
      <h3 class="text-2xl font-bold text-cyan-800 mb-2">Oyunuz Gönderildi!</h3>
      <p class="text-cyan-700">
        Diğer oyuncuların oylarını bekliyoruz...
      </p>
      <div class="mt-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-700"></div>
      </div>
    </div>
  {/if}

  <div class="mt-6 pt-6 border-t border-gray-200">
    <p class="text-sm text-gray-600 text-center">
      <strong>+1000 puan</strong> kazanmak için doğru cevabı bulun!
    </p>
  </div>
</div>
