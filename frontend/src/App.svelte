<script>
  import { onMount, onDestroy } from 'svelte';
  import { gameState, updateGameState, resetGameState, setError } from './stores/gameStore';
  import { socketManager } from './utils/socket';
  import { notifications } from './stores/notificationStore';
  import { userStore } from './stores/userStore';

  import Home from './components/Home.svelte';
  import RoomSelection from './components/RoomSelection.svelte';
  import Lobby from './components/Lobby.svelte';
  import SubmitFake from './components/SubmitFake.svelte';
  import Voting from './components/Voting.svelte';
  import Results from './components/Results.svelte';
  import FinalTest from './components/FinalTest.svelte';
  import GameOver from './components/GameOver.svelte';
  import Admin from './components/Admin.svelte';
  import Notification from './components/Notification.svelte';

  let socket;
  let currentRoute = 'game'; // 'game' or 'admin'
  let playerName = '';
  let selectedGrade = null;
  let selectedTheme = null;
  let showRoomSelection = false;

  function checkRoute() {
    const hash = window.location.hash;
    currentRoute = hash === '#admin' ? 'admin' : 'game';
    if (currentRoute === 'game' && !socket) {
      setupSocket();
    }
  }

  function setupSocket() {
    if (socket) return;
    socket = socketManager.connect();

    socket.on('connect', () => {
      const storedUser = localStorage.getItem('lugatoz_user');
      if (storedUser) {
        try {
          const userData = JSON.parse(storedUser);
          if (userData && userData.userId) {
            socket.emit('login_user', { user_id: userData.userId });
          }
        } catch (e) {
          // Invalid stored data
        }
      }
    });

    socket.on('player_joined', (data) => {
      const me = data.room_state.players.find((p) => p.socket_id === socket.id);
      updateGameState({
        players: data.room_state.players,
        playerId: socket.id,
        roomCode: data.room_state.room_code,
        topic: data.room_state.topic,
        selectedGrade: data.room_state.grade,
        selectedTheme: data.room_state.theme,
        isHost: me ? me.is_host : false
      });

      if (data.player.socket_id === socket.id) {
        showRoomSelection = false;
        updateGameState({
          phase: 'lobby',
          isHost: data.player.is_host
        });
      }
    });

    socket.on('player_left', (data) => {
      const me = data.room_state.players.find((p) => p.socket_id === socket.id);
      updateGameState({
        players: data.room_state.players,
        isHost: me ? me.is_host : false
      });
    });

    socket.on('room_topic_updated', (data) => {
      selectedGrade = data.room_state.grade;
      selectedTheme = data.room_state.theme;
      updateGameState({
        topic: data.room_state.topic,
        selectedGrade: data.room_state.grade,
        selectedTheme: data.room_state.theme
      });
      if (data.room_state.topic?.label) {
        notifications.info(`Konu güncellendi: ${data.room_state.topic.label}`);
      }
    });

    socket.on('game_started', (data) => {
      updateGameState({
        phase: 'submitting_fake',
        currentRound: data.room_state.current_round,
        maxRounds: data.room_state.max_rounds,
        topic: data.room_state.topic,
        currentQuestion: data.question,
        submittedAnswer: false,
        votedAnswer: false,
        results: null,
        finalQuestions: [],
        finalConcepts: [],
        finalProgress: null
      });
    });

    socket.on('submission_progress', () => {});

    socket.on('voting_phase', (data) => {
      updateGameState({
        phase: 'voting',
        options: data.options,
        votedAnswer: false
      });
    });

    socket.on('voting_progress', () => {});

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
        maxRounds: data.room_state.max_rounds,
        topic: data.room_state.topic,
        currentQuestion: data.question,
        submittedAnswer: false,
        votedAnswer: false,
        results: null
      });
    });

    socket.on('final_test_phase', (data) => {
      updateGameState({
        phase: 'final_test',
        finalQuestions: data.questions || [],
        finalConcepts: data.concepts || [],
        finalTestDuration: data.duration || 120,
        finalProgress: null,
        topic: data.topic || $gameState.topic
      });
    });

    socket.on('final_test_progress', (data) => {
      updateGameState({ finalProgress: data });
    });

    socket.on('game_over', (data) => {
      updateGameState({
        phase: 'game_over',
        leaderboard: data.leaderboard,
        players: data.players,
        topic: data.topic || $gameState.topic,
        results: data
      });
    });

    socket.on('room_ready_for_new_game', (data) => {
      const me = data.room_state.players.find((p) => p.socket_id === socket.id);
      updateGameState({
        phase: 'lobby',
        players: data.room_state.players,
        topic: data.room_state.topic,
        selectedGrade: data.room_state.grade,
        selectedTheme: data.room_state.theme,
        isHost: me ? me.is_host : false,
        currentRound: 0,
        submittedAnswer: false,
        votedAnswer: false,
        results: null,
        finalQuestions: [],
        finalConcepts: [],
        finalProgress: null
      });
      notifications.success(data.message);
    });

    socket.on('returned_to_lobby', (data) => {
      const me = data.room_state.players.find((p) => p.socket_id === socket.id);
      updateGameState({
        phase: 'lobby',
        players: data.room_state.players,
        topic: data.room_state.topic,
        selectedGrade: data.room_state.grade,
        selectedTheme: data.room_state.theme,
        isHost: me ? me.is_host : false,
        currentRound: 0,
        submittedAnswer: false,
        votedAnswer: false,
        results: null,
        finalQuestions: [],
        finalConcepts: [],
        finalProgress: null
      });
      notifications.success(data.message);
    });

    socket.on('game_restarted', (data) => {
      updateGameState({
        phase: 'submitting_fake',
        players: data.room_state.players,
        topic: data.room_state.topic,
        currentRound: 0,
        maxRounds: data.current_question.total_rounds,
        currentQuestion: data.current_question,
        submittedAnswer: false,
        votedAnswer: false,
        results: null,
        finalQuestions: [],
        finalConcepts: [],
        finalProgress: null
      });
      notifications.success(data.message);
    });

    socket.on('room_reset', (data) => {
      socketManager.clearRoomInfo();
      showRoomSelection = false;
      resetGameState();
      notifications.warning(data.message || 'Oda sıfırlandı.');
    });

    socket.on('error', (data) => {
      setError(data.message);
    });

    socket.on('name_taken', (data) => {
      notifications.error(data.message);
    });
  }

  onMount(() => {
    userStore.loadFromStorage();
    checkRoute();
    window.addEventListener('hashchange', checkRoute);
  });

  onDestroy(() => {
    window.removeEventListener('hashchange', checkRoute);
    if (socket) {
      socket.off('connect');
      socket.off('player_joined');
      socket.off('player_left');
      socket.off('room_topic_updated');
      socket.off('game_started');
      socket.off('submission_progress');
      socket.off('voting_phase');
      socket.off('voting_progress');
      socket.off('round_results');
      socket.off('new_round');
      socket.off('final_test_phase');
      socket.off('final_test_progress');
      socket.off('game_over');
      socket.off('room_ready_for_new_game');
      socket.off('returned_to_lobby');
      socket.off('game_restarted');
      socket.off('room_reset');
      socket.off('error');
      socket.off('name_taken');
      socketManager.disconnect();
    }
  });

  function handleEntrySubmit({ name, grade, theme }) {
    playerName = name;
    selectedGrade = grade;
    selectedTheme = theme;
    updateGameState({
      playerName: name,
      selectedGrade: grade,
      selectedTheme: theme
    });
    showRoomSelection = true;
  }

  function handleBackToHome() {
    showRoomSelection = false;
  }

  function handleRoomSelect(roomCode) {
    socketManager.setRoomInfo(playerName, roomCode, selectedGrade, selectedTheme);

    socketManager.emit('join_game', {
      player_name: playerName,
      room_code: roomCode,
      grade: selectedGrade,
      theme: selectedTheme
    });
  }

  function handleLeaveLobby() {
    showRoomSelection = true;
  }
</script>

<main>
  {#if $gameState.error}
    <div class="fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 animate-bounce max-w-md">
      {$gameState.error}
    </div>
  {/if}

  {#if currentRoute === 'admin'}
    <Admin />
  {:else if showRoomSelection}
    <RoomSelection
      {playerName}
      {selectedGrade}
      {selectedTheme}
      onRoomSelect={handleRoomSelect}
      onBack={handleBackToHome}
    />
  {:else if $gameState.phase === 'home'}
    <Home
      initialName={playerName}
      initialGrade={selectedGrade}
      initialTheme={selectedTheme}
      onEntrySubmit={handleEntrySubmit}
    />
  {:else if $gameState.phase === 'lobby'}
    <Lobby onLeave={handleLeaveLobby} />
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

<!-- Notifications -->
{#each $notifications as notification (notification.id)}
  <Notification
    message={notification.message}
    type={notification.type}
    duration={notification.duration}
    onClose={() => notifications.remove(notification.id)}
  />
{/each}

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
