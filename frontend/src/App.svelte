<script>
  import { onMount, onDestroy } from 'svelte';
  import { gameState, updateGameState, setError, resetGameState } from './stores/gameStore';
  import { socketManager } from './utils/socket';

  import Home from './components/Home.svelte';
  import Lobby from './components/Lobby.svelte';
  import SubmitFake from './components/SubmitFake.svelte';
  import Voting from './components/Voting.svelte';
  import Results from './components/Results.svelte';
  import FinalTest from './components/FinalTest.svelte';
  import GameOver from './components/GameOver.svelte';
  import Admin from './components/Admin.svelte';

  let socket;
  let currentRoute = 'game'; // 'game' or 'admin'

  function checkRoute() {
    const hash = window.location.hash;
    currentRoute = hash === '#admin' ? 'admin' : 'game';
  }

  onMount(() => {
    // Route kontrolü
    checkRoute();
    window.addEventListener('hashchange', checkRoute);

    // Socket bağlantısını kur (sadece game modunda)
    if (currentRoute === 'game') {
      socket = socketManager.connect();

      // Socket event listeners
      socket.on('player_joined', (data) => {
        updateGameState({
          players: data.room_state.players,
          playerId: socket.id
        });

        // Eğer bu biziz
        if (data.player.socket_id === socket.id) {
          updateGameState({
            phase: 'lobby',
            isHost: data.player.is_host
          });
        }
      });

      socket.on('player_left', (data) => {
        updateGameState({ players: data.room_state.players });
      });

      socket.on('game_started', (data) => {
        updateGameState({
          phase: 'submitting_fake',
          currentRound: data.room_state.current_round,
          maxRounds: data.room_state.max_rounds,
          currentQuestion: data.question,
          submittedAnswer: false
        });
      });

      socket.on('submission_progress', (data) => {
        console.log(`Cevap gönderme: ${data.submitted}/${data.total}`);
      });

      socket.on('voting_phase', (data) => {
        updateGameState({
          phase: 'voting',
          options: data.options,
          votedAnswer: false
        });
      });

      socket.on('voting_progress', (data) => {
        console.log(`Oylama: ${data.voted}/${data.total}`);
      });

      socket.on('round_results', (data) => {
        updateGameState({
          phase: 'showing_results',
          results: data,
          leaderboard: data.leaderboard
        });
      });

      socket.on('new_round', (data) => {
        updateGameState({
          phase: 'submitting_fake',
          currentRound: data.room_state.current_round,
          currentQuestion: data.question,
          submittedAnswer: false,
          votedAnswer: false,
          results: null
        });
      });

      socket.on('final_test_phase', (data) => {
        updateGameState({
          phase: 'final_test',
          finalQuestions: data.questions
        });
      });

      socket.on('game_over', (data) => {
        updateGameState({
          phase: 'game_over',
          leaderboard: data.leaderboard,
          results: data
        });
      });

      socket.on('error', (data) => {
        setError(data.message);
      });
    }
  });

  onDestroy(() => {
    window.removeEventListener('hashchange', checkRoute);
    if (socket) {
      socketManager.disconnect();
    }
  });
</script>

<main>
  {#if $gameState.error}
    <div class="fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 animate-bounce">
      {$gameState.error}
    </div>
  {/if}

  {#if currentRoute === 'admin'}
    <Admin />
  {:else if $gameState.phase === 'home'}
    <Home />
  {:else if $gameState.phase === 'lobby'}
    <Lobby />
  {:else if $gameState.phase === 'submitting_fake'}
    <SubmitFake />
  {:else if $gameState.phase === 'voting'}
    <Voting />
  {:else if $gameState.phase === 'showing_results'}
    <Results />
  {:else if $gameState.phase === 'final_test'}
    <FinalTest />
  {:else if $gameState.phase === 'game_over'}
    <GameOver />
  {/if}
</main>

<style>
  main {
    width: 100%;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
</style>
