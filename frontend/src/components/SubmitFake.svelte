<script>
  import { gameState, updateGameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import Timer from './Timer.svelte';

  let fakeAnswer = '';
  let timer;
  let timeoutReached = false;

  function submitFakeAnswer() {
    if (!fakeAnswer.trim()) {
      alert('Lütfen bir cevap girin!');
      return;
    }

    socketManager.emit('submit_fake_answer', {
      answer: fakeAnswer.trim()
    });

    if (timer) timer.stop();
    updateGameState({ submittedAnswer: true });
  }

  function handleTimeout() {
    timeoutReached = true;
    // Auto-submit if user has entered something
    if (fakeAnswer.trim()) {
      submitFakeAnswer();
    } else {
      alert('Süre doldu! Cevap girmediniz, -100 puan cezası aldınız.');
      // Submit empty to trigger penalty
      socketManager.emit('submit_fake_answer', {
        answer: ''
      });
      updateGameState({ submittedAnswer: true });
    }
  }

  // Listen for error from backend
  socketManager.on('answer_rejected', (data) => {
    if (data.reason === 'correct_answer') {
      alert('Doğru cevabı giremezsiniz! Yanlış ama inandırıcı bir cevap girmelisiniz.');
      fakeAnswer = '';
    }
  });
</script>

<div class="card max-w-3xl w-full">
  <div class="mb-6">
    <div class="flex justify-between items-center mb-4">
      <span class="bg-primary text-white px-4 py-2 rounded-full font-semibold">
        Soru {$gameState.currentRound + 1} / {$gameState.maxRounds}
      </span>
      {#if !$gameState.submittedAnswer}
        <Timer bind:this={timer} duration={20} onTimeout={handleTimeout} />
      {:else}
        <span class="text-gray-600">
          {$gameState.players.length} Oyuncu
        </span>
      {/if}
    </div>

    <div class="bg-gradient-to-r from-cyan-100 to-lime-100 p-6 rounded-xl border-2 border-cyan-300 mb-6">
      <p class="text-2xl font-semibold text-gray-800 text-center">
        {$gameState.currentQuestion?.text}
      </p>
    </div>
  </div>

  {#if !$gameState.submittedAnswer}
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          <span class="text-red-500 font-bold">Yanlış</span> ama <span class="text-cyan-500 font-bold">inandırıcı</span> bir cevap girin!
        </label>
        <p class="text-xs text-gray-500 mb-3">
          Diğer oyuncuları aldatmaya çalışın! Yanlış cevabınızı seçen her oyuncu için +500 puan kazanırsınız.
        </p>
        <textarea
          bind:value={fakeAnswer}
          placeholder="Yanlış cevabınızı buraya yazın..."
          class="input min-h-[100px] resize-none"
          maxlength="200"
        ></textarea>
        <p class="text-xs text-gray-400 mt-1 text-right">
          {fakeAnswer.length} / 200
        </p>
      </div>

      <button
        on:click={submitFakeAnswer}
        class="btn btn-primary w-full text-xl py-4"
      >
        Cevabı Gönder
      </button>
    </div>
  {:else}
    <div class="bg-green-50 border-2 border-cyan-300 rounded-xl p-8 text-center">
      <div class="text-6xl mb-4">✓</div>
      <h3 class="text-2xl font-bold text-cyan-800 mb-2">Cevabınız Gönderildi!</h3>
      <p class="text-cyan-700">
        Diğer oyuncuların cevaplarını bekliyoruz...
      </p>
      <div class="mt-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-700"></div>
      </div>
    </div>
  {/if}

  <div class="mt-6 pt-6 border-t border-gray-200">
    <h4 class="font-semibold text-gray-700 mb-3">İpucu:</h4>
    <p class="text-sm text-gray-600">
      En iyi yanlış cevaplar gerçek gibi görünür! Çok açık yanlış cevaplar kimseyi aldatmaz.
      Örnek: "Türkiye'nin başkenti neresidir?" sorusu için "Mars" yerine "İzmir" veya "İstanbul" gibi
      inandırıcı ama yanlış bir şehir yazabilirsiniz.
    </p>
  </div>
</div>
