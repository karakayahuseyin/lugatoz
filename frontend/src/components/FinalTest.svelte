<script>
  import { onMount, onDestroy } from 'svelte';
  import { gameState } from '../stores/gameStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';
  import Timer from './Timer.svelte';

  // matches: { [questionIndex: number]: { id: string, text: string } }
  let matches = {};
  let selectedConceptId = null;
  let selectedQuestionIndex = null;

  // Drag-and-drop state
  let draggedConceptId = null;
  let dragSourceQuestionIndex = null;
  let dragOverQuestionIndex = null;
  let dragOverBank = false;

  let timer;
  let isSubmitted = false;

  $: questions = $gameState.finalQuestions || [];
  $: concepts = $gameState.finalConcepts || [];
  $: duration = $gameState.finalTestDuration || 120;

  $: usedConceptIds = new Set(Object.values(matches).map((c) => c.id));
  $: availableConcepts = concepts.filter((c) => !usedConceptIds.has(c.id));
  $: matchedCount = Object.keys(matches).length;
  $: totalQuestions = questions.length;
  $: allMatched = totalQuestions > 0 && matchedCount === totalQuestions;
  $: progressPercent = totalQuestions > 0 ? Math.round((matchedCount / totalQuestions) * 100) : 0;

  onMount(() => {
    socketManager.on('final_matches_submitted', handleSubmittedAck);
  });

  onDestroy(() => {
    socketManager.off('final_matches_submitted', handleSubmittedAck);
  });

  function handleSubmittedAck(data) {
    if (data?.success) {
      isSubmitted = true;
      if (timer) timer.stop();
    }
  }

  function findConceptById(conceptId) {
    return concepts.find((c) => c.id === conceptId) || null;
  }

  function assignConceptToQuestion(conceptId, targetQuestionIndex, sourceQuestionIndex = null) {
    if (isSubmitted || !conceptId) return;
    const concept = findConceptById(conceptId);
    if (!concept) return;

    const next = { ...matches };

    // Find if this concept was already placed on another question
    let previousSlot = sourceQuestionIndex;
    if (previousSlot === null) {
      for (const [qKey, placed] of Object.entries(next)) {
        if (placed.id === conceptId) {
          previousSlot = Number(qKey);
          break;
        }
      }
    }

    const existingAtTarget = next[targetQuestionIndex] || null;

    if (previousSlot !== null) {
      delete next[previousSlot];
    }

    // If dragging/moving from one question slot onto an already filled slot, swap them!
    if (existingAtTarget && previousSlot !== null && previousSlot !== targetQuestionIndex) {
      next[previousSlot] = existingAtTarget;
    }

    next[targetQuestionIndex] = concept;
    matches = next;
    selectedConceptId = null;
    selectedQuestionIndex = null;
  }

  function removeMatch(questionIndex) {
    if (isSubmitted) return;
    if (!(questionIndex in matches)) return;
    if (selectedConceptId && matches[questionIndex]?.id === selectedConceptId) {
      selectedConceptId = null;
    }
    const next = { ...matches };
    delete next[questionIndex];
    matches = next;
    if (selectedQuestionIndex === questionIndex) {
      selectedQuestionIndex = null;
    }
  }

  function clearAllMatches() {
    if (isSubmitted) return;
    matches = {};
    selectedConceptId = null;
    selectedQuestionIndex = null;
  }

  // Click-to-match handlers (works both Concept -> Question and Question -> Concept)
  function handleBankConceptClick(concept) {
    if (isSubmitted) return;
    if (selectedQuestionIndex !== null) {
      assignConceptToQuestion(concept.id, selectedQuestionIndex, null);
      return;
    }
    selectedConceptId = selectedConceptId === concept.id ? null : concept.id;
  }

  function handleQuestionSlotClick(questionIndex) {
    if (isSubmitted) return;

    if (selectedConceptId !== null) {
      assignConceptToQuestion(selectedConceptId, questionIndex, null);
      return;
    }

    const existing = matches[questionIndex];
    if (existing) {
      // Pick up placed concept to move/swap to another question
      selectedConceptId = existing.id;
      selectedQuestionIndex = null;
      return;
    }

    // Empty slot clicked first -> let user click a concept next
    selectedQuestionIndex = selectedQuestionIndex === questionIndex ? null : questionIndex;
  }

  // Drag-and-drop handlers
  function handleDragStart(event, conceptId, sourceQuestionIndex = null) {
    if (isSubmitted) return;
    draggedConceptId = conceptId;
    dragSourceQuestionIndex = sourceQuestionIndex;
    selectedConceptId = null;
    selectedQuestionIndex = null;
    if (event.dataTransfer) {
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', conceptId);
    }
  }

  function handleDragEnd() {
    draggedConceptId = null;
    dragSourceQuestionIndex = null;
    dragOverQuestionIndex = null;
    dragOverBank = false;
  }

  function handleQuestionDragOver(event, questionIndex) {
    if (isSubmitted) return;
    event.preventDefault();
    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = 'move';
    }
    dragOverQuestionIndex = questionIndex;
  }

  function handleQuestionDragLeave(questionIndex) {
    if (dragOverQuestionIndex === questionIndex) {
      dragOverQuestionIndex = null;
    }
  }

  function handleQuestionDrop(event, questionIndex) {
    event.preventDefault();
    if (isSubmitted) return;
    const conceptId = draggedConceptId || event.dataTransfer?.getData('text/plain');
    if (conceptId) {
      assignConceptToQuestion(conceptId, questionIndex, dragSourceQuestionIndex);
    }
    handleDragEnd();
  }

  function handleBankDragOver(event) {
    if (isSubmitted || dragSourceQuestionIndex === null) return;
    event.preventDefault();
    dragOverBank = true;
  }

  function handleBankDragLeave() {
    dragOverBank = false;
  }

  function handleBankDrop(event) {
    event.preventDefault();
    if (isSubmitted) return;
    if (dragSourceQuestionIndex !== null) {
      removeMatch(dragSourceQuestionIndex);
    }
    handleDragEnd();
  }

  function buildMatchesPayload() {
    const payload = {};
    for (const q of questions) {
      payload[q.index] = matches[q.index]?.text || '';
    }
    return payload;
  }

  function submitMatches() {
    if (isSubmitted) return;
    if (!allMatched) {
      notifications.warning('Lütfen tüm soruları bir kavramla eşleştirin!');
      return;
    }

    socketManager.emit('submit_final_matches', {
      matches: buildMatchesPayload()
    });
    isSubmitted = true;
    if (timer) timer.stop();
    notifications.success('Eşleştirmeleriniz gönderildi! Diğer oyuncular bekleniyor...');
  }

  function handleTimeout() {
    if (isSubmitted) return;
    notifications.info('Süre doldu! Eşleştirmeleriniz otomatik olarak gönderildi.');
    socketManager.emit('submit_final_matches', {
      matches: buildMatchesPayload()
    });
    isSubmitted = true;
  }
</script>

<div class="card max-w-6xl w-full my-4">
  <!-- Üst Başlık & Sayaç -->
  <div class="pb-4 mb-5 border-b border-gray-200">
    <div class="flex flex-col md:flex-row justify-between items-center gap-4">
      <div class="text-center md:text-left">
        {#if $gameState.topic}
          <span class="inline-block text-xs font-bold bg-cyan-100 text-cyan-800 px-3 py-1 rounded-full mb-2">
            {$gameState.topic.grade === 'dunyanin_enleri' ? '🌍' : '📚'} {$gameState.topic.label}
          </span>
        {/if}
        <h1 class="text-3xl md:text-4xl font-bold text-primary">Kavram Eşleştirme</h1>
        <p class="text-gray-600 text-sm md:text-base mt-1">
          Oyunda öğrendiğiniz kavramları doğru sorularla eşleştirin!
        </p>
        <p class="text-xs text-cyan-700 font-semibold mt-1">
          Her doğru eşleştirme için +500 puan • Sürükle-bırak veya tıkla-eşleştir ile oynayın
        </p>
      </div>

      <div class="flex items-center gap-4">
        <div class="text-right">
          <div class="text-sm font-bold text-gray-700">
            Eşleştirilen: <span class="text-cyan-600">{matchedCount} / {totalQuestions}</span>
          </div>
          <div class="w-36 h-2.5 bg-gray-200 rounded-full overflow-hidden mt-1">
            <div
              class="h-full bg-gradient-to-r from-cyan-500 to-lime-500 transition-all duration-300"
              style="width: {progressPercent}%"
            ></div>
          </div>
        </div>
        {#if !isSubmitted}
          <Timer bind:this={timer} {duration} onTimeout={handleTimeout} />
        {/if}
      </div>
    </div>
  </div>

  {#if isSubmitted}
    <div class="bg-cyan-50 border-2 border-cyan-300 rounded-2xl p-10 text-center my-6">
      <div class="text-5xl mb-3">⏳</div>
      <h2 class="text-2xl font-bold text-cyan-800 mb-2">Eşleştirmeleriniz Gönderildi!</h2>
      <p class="text-cyan-700">
        Diğer oyuncuların etkinliği tamamlaması bekleniyor...
      </p>
      {#if $gameState.finalProgress}
        <p class="text-sm font-bold text-cyan-800 mt-3 bg-white inline-block px-4 py-1.5 rounded-full border border-cyan-200">
          Tamamlayan oyuncular: {$gameState.finalProgress.submitted} / {$gameState.finalProgress.total}
        </p>
      {/if}
    </div>
  {:else}
    <!-- Aktif Seçim İpucu Çubuğu -->
    {#if selectedConceptId}
      {@const activeConcept = findConceptById(selectedConceptId)}
      <div class="mb-4 bg-cyan-50 border-2 border-cyan-400 rounded-xl px-4 py-2.5 flex items-center justify-between gap-2 text-sm">
        <span class="text-cyan-900">
          Seçili kavram: <strong>"{activeConcept?.text}"</strong> — Şimdi eşleştirmek istediğiniz sorunun kutusuna tıklayın!
        </span>
        <button
          type="button"
          on:click={() => selectedConceptId = null}
          class="text-xs font-bold text-cyan-700 hover:text-cyan-900 underline"
        >
          İptal
        </button>
      </div>
    {:else if selectedQuestionIndex !== null}
      <div class="mb-4 bg-lime-50 border-2 border-lime-400 rounded-xl px-4 py-2.5 flex items-center justify-between gap-2 text-sm">
        <span class="text-lime-900">
          <strong>{selectedQuestionIndex + 1}. soru</strong> seçildi — Şimdi kavram havuzundan doğru kavramı tıklayın!
        </span>
        <button
          type="button"
          on:click={() => selectedQuestionIndex = null}
          class="text-xs font-bold text-lime-700 hover:text-lime-900 underline"
        >
          İptal
        </button>
      </div>
    {/if}

    <!-- Ana Eşleştirme Alanı: Sol/Üst Kavram Havuzu + Sağ/Alt Sorular -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <!-- Kavram Havuzu -->
      <div class="lg:col-span-4 lg:sticky lg:top-4">
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div
          on:dragover={handleBankDragOver}
          on:dragleave={handleBankDragLeave}
          on:drop={handleBankDrop}
          class="rounded-2xl border-2 p-4 transition-all {
            dragOverBank
              ? 'border-amber-400 bg-amber-50 shadow-inner'
              : 'border-cyan-200 bg-gradient-to-b from-cyan-50/70 to-lime-50/50'
          }"
        >
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-bold text-gray-800 text-lg">
              Kavramlar ({availableConcepts.length})
            </h2>
            {#if matchedCount > 0}
              <button
                type="button"
                on:click={clearAllMatches}
                class="text-xs font-semibold text-red-500 hover:text-red-700"
              >
                Tümünü Temizle
              </button>
            {/if}
          </div>

          <p class="text-xs text-gray-500 mb-3">
            Bir kavramı sürükleyip sorunun kutusuna bırakın ya da tıklayıp soruyu seçin.
          </p>

          {#if availableConcepts.length === 0}
            <div class="bg-green-50 border-2 border-green-300 rounded-xl p-4 text-center">
              <div class="text-2xl mb-1">✅</div>
              <p class="text-sm font-bold text-green-800">Tüm kavramlar yerleştirildi!</p>
              <p class="text-xs text-green-700 mt-1">
                Kontrol edip aşağıdan eşleştirmeyi tamamlayabilirsiniz.
              </p>
            </div>
          {:else}
            <div class="flex flex-wrap gap-2">
              {#each availableConcepts as concept (concept.id)}
                {@const isSelected = selectedConceptId === concept.id}
                <button
                  type="button"
                  draggable="true"
                  on:dragstart={(e) => handleDragStart(e, concept.id, null)}
                  on:dragend={handleDragEnd}
                  on:click={() => handleBankConceptClick(concept)}
                  class="inline-flex items-center gap-2 px-3.5 py-2.5 rounded-xl border-2 text-sm font-bold transition-all select-none cursor-grab active:cursor-grabbing {
                    isSelected
                      ? 'border-cyan-600 bg-cyan-500 text-white shadow-lg ring-4 ring-cyan-200 scale-105'
                      : selectedQuestionIndex !== null
                        ? 'border-lime-400 bg-white text-gray-800 hover:bg-lime-50 hover:border-lime-500 shadow-sm'
                        : 'border-cyan-300 bg-white text-gray-800 hover:border-cyan-500 hover:bg-cyan-50 shadow-sm'
                  }"
                >
                  <span class="opacity-50 text-xs" aria-hidden="true">⠿</span>
                  <span>{concept.text}</span>
                </button>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Sorular ve Eşleştirme Kutuları -->
      <div class="lg:col-span-8 space-y-3">
        {#each questions as question (question.index)}
          {@const matched = matches[question.index]}
          {@const isDropTarget = dragOverQuestionIndex === question.index}
          {@const isSlotSelected = selectedQuestionIndex === question.index}
          {@const isPickedUp = matched && selectedConceptId === matched.id}

          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div
            on:dragover={(e) => handleQuestionDragOver(e, question.index)}
            on:dragleave={() => handleQuestionDragLeave(question.index)}
            on:drop={(e) => handleQuestionDrop(e, question.index)}
            class="rounded-xl border-2 p-4 transition-all {
              isDropTarget
                ? 'border-cyan-500 bg-cyan-50 shadow-md scale-[1.01]'
                : isSlotSelected
                  ? 'border-lime-500 bg-lime-50/70 shadow-sm'
                  : matched
                    ? 'border-green-300 bg-green-50/40'
                    : 'border-gray-200 bg-gray-50'
            }"
          >
            <div class="flex items-start gap-3 mb-3">
              <span class="flex-shrink-0 w-7 h-7 rounded-full text-sm font-bold flex items-center justify-center {
                matched ? 'bg-green-500 text-white' : 'bg-cyan-500 text-white'
              }">
                {question.index + 1}
              </span>
              <p class="font-semibold text-gray-800 text-sm md:text-base leading-snug pt-0.5">
                {question.question_text}
              </p>
            </div>

            <!-- Eşleştirme Yuvası -->
            {#if matched}
              <div class="flex items-center justify-between gap-2 pl-10">
                <div
                  role="button"
                  tabindex="0"
                  draggable="true"
                  on:dragstart={(e) => handleDragStart(e, matched.id, question.index)}
                  on:dragend={handleDragEnd}
                  on:click={() => handleQuestionSlotClick(question.index)}
                  on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleQuestionSlotClick(question.index)}
                  class="flex-1 flex items-center justify-between gap-2 px-4 py-2.5 rounded-xl border-2 cursor-grab active:cursor-grabbing transition-all {
                    isPickedUp
                      ? 'border-cyan-600 bg-cyan-500 text-white ring-4 ring-cyan-200'
                      : 'border-green-400 bg-white text-green-900 hover:border-cyan-400 shadow-sm'
                  }"
                >
                  <div class="flex items-center gap-2 font-bold text-sm md:text-base">
                    <span class="opacity-50 text-xs" aria-hidden="true">⠿</span>
                    <span>{matched.text}</span>
                  </div>
                  <button
                    type="button"
                    on:click|stopPropagation={() => removeMatch(question.index)}
                    class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors {
                      isPickedUp
                        ? 'bg-white/25 text-white hover:bg-white/40'
                        : 'bg-red-100 text-red-600 hover:bg-red-200'
                    }"
                    title="Kavramı havuza geri gönder"
                    aria-label="Eşleştirmeyi kaldır"
                  >
                    ✕
                  </button>
                </div>
              </div>
            {:else}
              <div class="pl-10">
                <button
                  type="button"
                  on:click={() => handleQuestionSlotClick(question.index)}
                  class="w-full py-3 px-4 rounded-xl border-2 border-dashed text-sm font-medium text-center transition-all {
                    isDropTarget
                      ? 'border-cyan-500 bg-cyan-100 text-cyan-800 font-bold'
                      : selectedConceptId
                        ? 'border-cyan-400 bg-cyan-50/80 text-cyan-700 hover:bg-cyan-100 cursor-pointer'
                        : isSlotSelected
                          ? 'border-lime-500 bg-lime-100 text-lime-800 font-bold'
                          : 'border-gray-300 bg-white text-gray-400 hover:border-cyan-400 hover:text-cyan-600'
                  }"
                >
                  {#if isDropTarget}
                    Buraya bırakın
                  {:else if selectedConceptId}
                    Seçili kavramı buraya yerleştirmek için tıklayın
                  {:else if isSlotSelected}
                    Şimdi soldaki havuzdan bir kavram seçin
                  {:else}
                    Kavramı buraya sürükleyin veya tıklayarak seçin
                  {/if}
                </button>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    </div>

    <!-- Alt Gönder Butonu -->
    <div class="mt-6 pt-4 border-t border-gray-200">
      <button
        type="button"
        on:click={submitMatches}
        disabled={!allMatched}
        class="btn btn-success w-full text-xl py-4 {!allMatched ? 'opacity-50 cursor-not-allowed' : ''}"
      >
        Eşleştirmeyi Tamamla ve Sonuçları Gör
      </button>

      {#if !allMatched}
        <p class="text-center text-gray-500 text-sm mt-2">
          Devam etmek için tüm soruları eşleştirin ({matchedCount} / {totalQuestions})
        </p>
      {/if}
    </div>
  {/if}
</div>
