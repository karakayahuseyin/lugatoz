<script>
  import { onDestroy } from 'svelte';
  import { DEFAULT_CURRICULUM, fetchCurriculum } from '../utils/curriculum';

  const ADMIN_PASSWORD = 'lugatoz23';

  let isAuthenticated = false;
  let passwordInput = '';
  let activeTab = 'questions'; // 'questions' | 'rooms' | 'users' | 'stats'

  // Curriculum & Navigation: Bölüm (Sınıf / Dünyanın Enleri) > Tema > Sorular
  let sections = DEFAULT_CURRICULUM;
  let uncategorizedCount = 0;
  let selectedGrade = null; // '5' | '6' | '7' | '8' | 'dunyanin_enleri' | '__uncategorized__' | null
  let selectedTheme = null; // theme id | null

  // Current view questions
  let questions = [];
  let loadingQuestions = false;
  let showAddForm = false;
  let editingQuestion = null;
  let saving = false;

  // Theme management state (ekle / düzenle / sil / sırala)
  let showAddThemeForm = false;
  let newThemeName = '';
  let editingTheme = null; // { db_id, name }
  let savingTheme = false;

  // Feedback banner
  let feedback = null; // { type: 'success' | 'error', text: string }
  let feedbackTimer = null;

  // Other admin tabs
  let stats = null;
  let users = [];
  let rooms = [];
  let roomsFilter = 'all'; // 'all' | 'active'
  let roomsInterval = null;

  // 3 fields only for adding a question
  let newQuestion = {
    question_text: '',
    correct_answer: '',
    unacceptable_answers: ''
  };

  $: selectedSection = sections.find((s) => s.id === selectedGrade) || null;
  $: gradeSections = sections.filter((s) => s.has_themes);
  $: specialSection = sections.find((s) => !s.has_themes) || null;
  $: selectedThemeObj = selectedSection?.has_themes
    ? selectedSection.themes.find((t) => t.id === selectedTheme) || null
    : null;
  $: isViewingQuestions = Boolean(
    selectedGrade === '__uncategorized__' ||
    (selectedSection && (!selectedSection.has_themes || selectedThemeObj))
  );
  $: totalAllQuestions = sections.reduce((sum, s) => sum + (s.total_questions || 0), 0) + uncategorizedCount;
  $: activeRoomsCount = rooms.filter((r) => r.players.length > 0).length;

  onDestroy(() => {
    if (roomsInterval) clearInterval(roomsInterval);
    if (feedbackTimer) clearTimeout(feedbackTimer);
  });

  function showFeedback(text, type = 'success') {
    feedback = { text, type };
    if (feedbackTimer) clearTimeout(feedbackTimer);
    feedbackTimer = setTimeout(() => {
      feedback = null;
    }, 3500);
  }

  async function checkPassword() {
    if (passwordInput === ADMIN_PASSWORD) {
      isAuthenticated = true;
      await Promise.all([
        loadCurriculum(),
        loadStats(),
        loadUsers(),
        loadRooms()
      ]);
      roomsInterval = setInterval(loadRooms, 5000);
    } else {
      alert('Yanlış şifre!');
      passwordInput = '';
    }
  }

  async function loadCurriculum() {
    const data = await fetchCurriculum();
    sections = data.sections;
    uncategorizedCount = data.uncategorized_questions || 0;
  }

  async function loadTopicQuestions() {
    if (!isViewingQuestions) {
      questions = [];
      return;
    }

    loadingQuestions = true;
    try {
      const params = new URLSearchParams({ include_inactive: 'true' });
      if (selectedGrade === '__uncategorized__') {
        params.set('uncategorized', 'true');
      } else {
        params.set('grade', selectedGrade);
        if (selectedSection?.has_themes && selectedTheme) {
          params.set('theme', selectedTheme);
        }
      }

      const response = await fetch(`/api/questions?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      questions = await response.json();
    } catch (error) {
      console.error('Sorular yüklenemedi:', error);
      showFeedback('Sorular yüklenemedi! Sunucu bağlantısını kontrol edin.', 'error');
    } finally {
      loadingQuestions = false;
    }
  }

  async function selectSection(gradeId) {
    selectedGrade = gradeId;
    selectedTheme = null;
    editingQuestion = null;
    showAddForm = false;
    showAddThemeForm = false;
    editingTheme = null;
    newThemeName = '';
    feedback = null;

    const sec = sections.find((s) => s.id === gradeId);
    if (gradeId === '__uncategorized__' || (sec && !sec.has_themes)) {
      await loadTopicQuestions();
    } else {
      questions = [];
    }
  }

  async function selectTheme(themeId) {
    selectedTheme = themeId;
    editingQuestion = null;
    showAddForm = false;
    showAddThemeForm = false;
    editingTheme = null;
    feedback = null;
    await loadTopicQuestions();
  }

  function goToSections() {
    selectedGrade = null;
    selectedTheme = null;
    questions = [];
    editingQuestion = null;
    showAddForm = false;
    showAddThemeForm = false;
    editingTheme = null;
    feedback = null;
  }

  function goToThemes() {
    selectedTheme = null;
    questions = [];
    editingQuestion = null;
    showAddForm = false;
    showAddThemeForm = false;
    editingTheme = null;
    feedback = null;
  }

  async function addTheme() {
    const name = newThemeName.trim();
    if (!name) {
      showFeedback('Tema adı zorunludur!', 'error');
      return;
    }

    savingTheme = true;
    try {
      const response = await fetch('/api/themes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grade: selectedGrade,
          name
        })
      });

      if (response.ok) {
        newThemeName = '';
        showFeedback('Tema başarıyla eklendi!', 'success');
        await loadCurriculum();
      } else {
        const err = await response.json().catch(() => ({}));
        showFeedback(err.detail || 'Tema eklenemedi!', 'error');
      }
    } catch (error) {
      console.error('Tema eklenemedi:', error);
      showFeedback('Tema eklenirken bir hata oluştu!', 'error');
    } finally {
      savingTheme = false;
    }
  }

  function startEditTheme(theme) {
    editingTheme = { db_id: theme.db_id, name: theme.name };
    showAddThemeForm = false;
  }

  function cancelEditTheme() {
    editingTheme = null;
  }

  async function updateTheme() {
    if (!editingTheme) return;
    const name = editingTheme.name.trim();
    if (!name) {
      showFeedback('Tema adı zorunludur!', 'error');
      return;
    }

    savingTheme = true;
    try {
      const response = await fetch(`/api/themes/${editingTheme.db_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });

      if (response.ok) {
        editingTheme = null;
        showFeedback('Tema adı güncellendi!', 'success');
        await loadCurriculum();
      } else {
        const err = await response.json().catch(() => ({}));
        showFeedback(err.detail || 'Tema güncellenemedi!', 'error');
      }
    } catch (error) {
      console.error('Tema güncellenemedi:', error);
      showFeedback('Tema güncellenirken bir hata oluştu!', 'error');
    } finally {
      savingTheme = false;
    }
  }

  async function moveTheme(theme, direction) {
    try {
      const response = await fetch(`/api/themes/${theme.db_id}/move`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction })
      });
      if (response.ok) {
        await loadCurriculum();
      }
    } catch (error) {
      console.error('Tema sırası güncellenemedi:', error);
    }
  }

  async function deleteTheme(theme) {
    const msg = theme.total_questions > 0
      ? `"${theme.full_name}" temasında ${theme.total_questions} soru bulunuyor! Temayı silerseniz bu sorular da KALICI olarak silinecektir. Devam etmek istiyor musunuz?`
      : `"${theme.full_name}" temasını silmek istediğinizden emin misiniz?`;

    if (!confirm(msg)) return;

    try {
      const response = await fetch(`/api/themes/${theme.db_id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        if (editingTheme?.db_id === theme.db_id) {
          editingTheme = null;
        }
        showFeedback('Tema silindi!', 'success');
        await loadCurriculum();
      } else {
        const err = await response.json().catch(() => ({}));
        showFeedback(err.detail || 'Tema silinemedi!', 'error');
      }
    } catch (error) {
      console.error('Tema silinemedi:', error);
      showFeedback('Tema silinirken bir hata oluştu!', 'error');
    }
  }

  async function addQuestion() {
    const qText = newQuestion.question_text.trim();
    const cAnswer = newQuestion.correct_answer.trim();
    const uAnswers = newQuestion.unacceptable_answers.trim();

    if (!qText || !cAnswer) {
      showFeedback('Soru ve Doğru Cevap alanları zorunludur!', 'error');
      return;
    }

    saving = true;
    try {
      const response = await fetch('/api/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_text: qText,
          correct_answer: cAnswer,
          unacceptable_answers: uAnswers || null,
          grade: selectedGrade,
          theme: selectedSection?.has_themes ? selectedTheme : null
        })
      });

      if (response.ok) {
        newQuestion = {
          question_text: '',
          correct_answer: '',
          unacceptable_answers: ''
        };
        showFeedback('Soru başarıyla eklendi! Yeni soru girebilirsiniz.', 'success');
        await Promise.all([loadTopicQuestions(), loadCurriculum()]);
      } else {
        const err = await response.json().catch(() => ({}));
        showFeedback(err.detail || 'Soru eklenemedi!', 'error');
      }
    } catch (error) {
      console.error('Soru eklenemedi:', error);
      showFeedback('Soru eklenirken bir hata oluştu!', 'error');
    } finally {
      saving = false;
    }
  }

  function startEdit(question) {
    editingQuestion = {
      id: question.id,
      question_text: question.question_text,
      correct_answer: question.correct_answer,
      unacceptable_answers: question.unacceptable_answers || '',
      grade: question.grade,
      theme: question.theme
    };
    showAddForm = false;
  }

  function cancelEdit() {
    editingQuestion = null;
  }

  async function updateQuestion() {
    if (!editingQuestion) return;
    const qText = editingQuestion.question_text.trim();
    const cAnswer = editingQuestion.correct_answer.trim();
    const uAnswers = (editingQuestion.unacceptable_answers || '').trim();

    if (!qText || !cAnswer) {
      showFeedback('Soru ve Doğru Cevap alanları zorunludur!', 'error');
      return;
    }

    saving = true;
    try {
      const response = await fetch(`/api/questions/${editingQuestion.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_text: qText,
          correct_answer: cAnswer,
          unacceptable_answers: uAnswers || null,
          grade: editingQuestion.grade || selectedGrade,
          theme: selectedSection?.has_themes ? (editingQuestion.theme || selectedTheme) : null
        })
      });

      if (response.ok) {
        editingQuestion = null;
        showFeedback('Soru başarıyla güncellendi!', 'success');
        await Promise.all([loadTopicQuestions(), loadCurriculum()]);
      } else {
        const err = await response.json().catch(() => ({}));
        showFeedback(err.detail || 'Soru güncellenemedi!', 'error');
      }
    } catch (error) {
      console.error('Soru güncellenemedi:', error);
      showFeedback('Soru güncellenirken bir hata oluştu!', 'error');
    } finally {
      saving = false;
    }
  }

  async function toggleQuestion(id) {
    try {
      const response = await fetch(`/api/questions/${id}/toggle`, {
        method: 'PATCH'
      });

      if (response.ok) {
        const data = await response.json();
        questions = questions.map((q) =>
          q.id === id ? { ...q, is_active: data.is_active } : q
        );
        await loadCurriculum();
      } else {
        showFeedback('Durum değiştirilemedi!', 'error');
      }
    } catch (error) {
      console.error('Durum değiştirilemedi:', error);
      showFeedback('Durum değiştirilirken bir hata oluştu!', 'error');
    }
  }

  async function deleteQuestion(id) {
    if (!confirm('Bu soruyu KALICI olarak silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await fetch(`/api/questions/${id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        if (editingQuestion?.id === id) {
          editingQuestion = null;
        }
        showFeedback('Soru silindi!', 'success');
        await Promise.all([loadTopicQuestions(), loadCurriculum()]);
      } else {
        showFeedback('Soru silinemedi!', 'error');
      }
    } catch (error) {
      console.error('Soru silinemedi:', error);
      showFeedback('Soru silinirken bir hata oluştu!', 'error');
    }
  }

  async function loadUsers() {
    try {
      const response = await fetch('/api/users');
      if (response.ok) users = await response.json();
    } catch (error) {
      console.error('Kullanıcılar yüklenemedi:', error);
    }
  }

  async function deleteUser(user) {
    if (!confirm(`"${user.username}" (ID: ${user.user_id}) kullanıcısını ve tüm puan/istatistiklerini KALICI olarak silmek istediğinizden emin misiniz?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/users/${user.user_id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadUsers();
      } else {
        alert('Kullanıcı silinemedi!');
      }
    } catch (error) {
      console.error('Kullanıcı silinemedi:', error);
      alert('Kullanıcı silinirken bir hata oluştu!');
    }
  }

  async function deleteAllUsers() {
    if (!confirm(`Kayıtlı TÜM ${users.length} kullanıcı hesabı, puanları ve liderlik tablosu KALICI olarak silinecek (sorular korunur). Devam etmek istiyor musunuz?`)) {
      return;
    }

    try {
      const response = await fetch('/api/users', {
        method: 'DELETE'
      });

      if (response.ok) {
        await Promise.all([loadUsers(), loadStats()]);
        alert('Tüm kullanıcılar ve liderlik tablosu sıfırlandı!');
      } else {
        alert('Kullanıcılar silinemedi!');
      }
    } catch (error) {
      console.error('Kullanıcılar silinemedi:', error);
      alert('Kullanıcılar silinirken bir hata oluştu!');
    }
  }

  async function loadRooms() {
    try {
      const response = await fetch('/api/rooms');
      if (response.ok) rooms = await response.json();
    } catch (error) {
      console.error('Odalar yüklenemedi:', error);
    }
  }

  async function loadStats() {
    try {
      const response = await fetch('/api/stats');
      if (response.ok) stats = await response.json();
    } catch (error) {
      console.error('İstatistikler yüklenemedi:', error);
    }
  }

  async function resetRoom(roomCode) {
    if (!confirm('Bu odayı temizlemek istediğinizden emin misiniz? Tüm oyuncular çıkarılacak.')) {
      return;
    }

    try {
      const response = await fetch(`/api/rooms/${roomCode}/reset`, {
        method: 'POST'
      });

      if (response.ok) {
        await loadRooms();
      } else {
        alert('Oda sıfırlanamadı!');
      }
    } catch (error) {
      console.error('Oda sıfırlanamadı:', error);
      alert('Oda sıfırlanırken bir hata oluştu!');
    }
  }

  function getPhaseText(phase) {
    const phases = {
      waiting: 'Lobide',
      submitting_fake: 'Yanıltıcı Cevaplar',
      voting: 'Oylama',
      showing_results: 'Sonuçlar',
      final_test: 'Kavram Eşleştirme',
      game_over: 'Oyun Bitti'
    };
    return phases[phase] || phase;
  }
</script>

<div class="min-h-screen w-full bg-gradient-to-br from-cyan-100 to-lime-100 p-4 md:p-6">
  {#if !isAuthenticated}
    <!-- Giriş Ekranı -->
    <div class="max-w-md mx-auto mt-16">
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <div class="flex justify-center mb-3">
          <img src="/tarihtoz-logo.png" alt="TarihTöz" class="w-24 h-24 object-contain rounded-2xl" />
        </div>
        <h1 class="text-3xl font-bold text-primary text-center mb-2">TarihTöz Admin Paneli</h1>
        <p class="text-sm text-gray-500 text-center mb-6">Sınıf, Tema ve Soru Yönetimi</p>

        <div class="space-y-4">
          <div>
            <label for="admin-password-input" class="block text-sm font-medium text-gray-700 mb-2">
              Şifre
            </label>
            <input
              id="admin-password-input"
              type="password"
              bind:value={passwordInput}
              on:keypress={(e) => e.key === 'Enter' && checkPassword()}
              placeholder="Admin şifresini girin"
              class="input"
            />
          </div>

          <button
            on:click={checkPassword}
            class="btn btn-primary w-full"
          >
            Giriş Yap
          </button>
        </div>

        <div class="mt-6 text-center">
          <a href="/#" class="text-cyan-600 hover:text-cyan-700 font-semibold">
            ← Oyuna Dön
          </a>
        </div>
      </div>
    </div>
  {:else}
    <div class="max-w-6xl mx-auto space-y-6">
      <!-- Üst Başlık ve Sekmeler -->
      <div class="bg-white rounded-2xl shadow-xl p-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-5">
          <div class="flex items-center gap-3">
            <img src="/tarihtoz-logo.png" alt="TarihTöz" class="w-12 h-12 object-contain rounded-xl" />
            <div>
              <h1 class="text-3xl font-bold text-primary">TarihTöz Admin Paneli</h1>
              <p class="text-sm text-gray-500">Toplam {totalAllQuestions} soru • {users.length} kayıtlı kullanıcı</p>
            </div>
          </div>
          <a href="/#" class="btn btn-secondary text-sm py-2 px-4">
            ← Oyuna Dön
          </a>
        </div>

        <div class="flex flex-wrap gap-2 border-t border-gray-100 pt-4">
          <button
            on:click={() => activeTab = 'questions'}
            class="px-4 py-2.5 rounded-xl font-semibold text-sm transition-all {
              activeTab === 'questions'
                ? 'bg-primary text-white shadow'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }"
          >
            📚 Soru Yönetimi ({totalAllQuestions})
          </button>
          <button
            on:click={() => { activeTab = 'rooms'; loadRooms(); }}
            class="px-4 py-2.5 rounded-xl font-semibold text-sm transition-all {
              activeTab === 'rooms'
                ? 'bg-primary text-white shadow'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }"
          >
            🏠 Masalar ({activeRoomsCount} aktif)
          </button>
          <button
            on:click={() => { activeTab = 'users'; loadUsers(); }}
            class="px-4 py-2.5 rounded-xl font-semibold text-sm transition-all {
              activeTab === 'users'
                ? 'bg-primary text-white shadow'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }"
          >
            👥 Kullanıcılar ({users.length})
          </button>
          <button
            on:click={() => { activeTab = 'stats'; loadStats(); }}
            class="px-4 py-2.5 rounded-xl font-semibold text-sm transition-all {
              activeTab === 'stats'
                ? 'bg-primary text-white shadow'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }"
          >
            📊 İstatistikler
          </button>
        </div>
      </div>

      <!-- SEKME 1: SORU YÖNETİMİ (Sınıf > Tema > Sorular & Dünyanın Enleri) -->
      {#if activeTab === 'questions'}
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
          <!-- Breadcrumb -->
          <nav class="flex flex-wrap items-center gap-2 text-sm mb-6 pb-4 border-b border-gray-200">
            <button
              on:click={goToSections}
              class="font-bold transition-colors {selectedGrade ? 'text-cyan-600 hover:text-cyan-800 hover:underline' : 'text-gray-800'}"
            >
              Bölümler
            </button>

            {#if selectedSection}
              <span class="text-gray-400">›</span>
              {#if selectedThemeObj}
                <button
                  on:click={goToThemes}
                  class="font-bold text-cyan-600 hover:text-cyan-800 hover:underline"
                >
                  {selectedSection.name}
                </button>
                <span class="text-gray-400">›</span>
                <span class="font-bold text-gray-800">{selectedThemeObj.full_name}</span>
              {:else}
                <span class="font-bold text-gray-800">{selectedSection.name}</span>
              {/if}
            {:else if selectedGrade === '__uncategorized__'}
              <span class="text-gray-400">›</span>
              <span class="font-bold text-gray-800">Kategorisiz Eski Sorular</span>
            {/if}
          </nav>

          <!-- SEVİYE 1: SINIF / BÖLÜM SEÇİMİ -->
          {#if !selectedGrade}
            <div class="mb-6">
              <h2 class="text-2xl font-bold text-gray-800 mb-1">Bölüm Seçin</h2>
              <p class="text-sm text-gray-500">
                Soru eklemek, düzenlemek veya silmek için önce bir sınıf veya Dünyanın Enleri bölümünü seçin.
              </p>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
              {#each gradeSections as section}
                <button
                  on:click={() => selectSection(section.id)}
                  class="text-left p-5 rounded-2xl border-2 border-cyan-200 bg-gradient-to-br from-white to-cyan-50/60 hover:border-cyan-500 hover:shadow-lg transition-all group"
                >
                  <div class="flex items-center justify-between mb-3">
                    <span class="text-3xl">📘</span>
                    <span class="text-xs font-bold px-2.5 py-1 rounded-full bg-cyan-100 text-cyan-800">
                      {section.themes.length} Tema
                    </span>
                  </div>
                  <h3 class="text-2xl font-bold text-gray-800 group-hover:text-cyan-700">{section.name}</h3>
                  <p class="text-sm text-gray-600 mt-2">
                    <strong>{section.total_questions}</strong> soru
                    <span class="text-xs text-gray-400">({section.active_questions} aktif)</span>
                  </p>
                  <p class="text-xs font-bold text-cyan-600 mt-3 group-hover:translate-x-1 transition-transform">
                    Temaları Gör →
                  </p>
                </button>
              {/each}
            </div>

            {#if specialSection}
              <button
                on:click={() => selectSection(specialSection.id)}
                class="w-full text-left p-6 rounded-2xl border-2 border-lime-300 bg-gradient-to-r from-lime-50 to-emerald-50 hover:border-lime-500 hover:shadow-lg transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
              >
                <div class="flex items-center gap-4">
                  <span class="text-4xl">🌍</span>
                  <div>
                    <div class="flex items-center gap-2">
                      <h3 class="text-2xl font-bold text-gray-800 group-hover:text-lime-800">{specialSection.name}</h3>
                      <span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-lime-200 text-lime-900">
                        Ayrı Bölüm
                      </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-1">
                      Tema seçimi olmadan doğrudan soru eklenir ve oynanır.
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-4">
                  <div class="text-right">
                    <div class="text-xl font-bold text-lime-800">{specialSection.total_questions} soru</div>
                    <div class="text-xs text-gray-500">{specialSection.active_questions} aktif</div>
                  </div>
                  <span class="text-sm font-bold text-lime-700 group-hover:translate-x-1 transition-transform">
                    Soruları Yönet →
                  </span>
                </div>
              </button>
            {/if}

            {#if uncategorizedCount > 0}
              <div class="mt-6 pt-4 border-t border-gray-200 flex items-center justify-between">
                <span class="text-xs text-gray-500">
                  Eski sürümden kalan sınıf/teması atanmamış {uncategorizedCount} soru bulunuyor (oyunlarda gösterilmez).
                </span>
                <button
                  on:click={() => selectSection('__uncategorized__')}
                  class="text-xs font-semibold text-gray-600 hover:text-gray-800 underline"
                >
                  Eski Soruları Görüntüle
                </button>
              </div>
            {/if}

          <!-- SEVİYE 2: TEMA SEÇİMİ VE YÖNETİMİ (5, 6, 7, 8. Sınıflar için) -->
          {:else if selectedSection && selectedSection.has_themes && !selectedThemeObj}
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <h2 class="text-2xl font-bold text-gray-800">{selectedSection.name} — Temalar</h2>
                <p class="text-sm text-gray-500">
                  Tema ekleyin, düzenleyin, silin veya sorularını yönetmek için bir temayı açın ({selectedSection.themes.length} tema).
                </p>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  on:click={goToSections}
                  class="px-4 py-2.5 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold text-sm hover:bg-gray-100"
                >
                  ← Bölümlere Dön
                </button>
                <button
                  on:click={() => { showAddThemeForm = !showAddThemeForm; editingTheme = null; }}
                  class="btn btn-success text-sm py-2.5 px-5"
                >
                  {showAddThemeForm ? 'Formu Kapat' : '+ Yeni Tema Ekle'}
                </button>
              </div>
            </div>

            <!-- Bilgilendirme Banner -->
            {#if feedback}
              <div class="mb-5 px-4 py-3 rounded-xl border-2 text-sm font-semibold flex items-center justify-between {
                feedback.type === 'success'
                  ? 'bg-green-50 border-green-300 text-green-800'
                  : 'bg-red-50 border-red-300 text-red-800'
              }">
                <span>{feedback.type === 'success' ? '✓' : '⚠'} {feedback.text}</span>
                <button on:click={() => feedback = null} class="text-xs underline ml-4">Kapat</button>
              </div>
            {/if}

            <!-- YENİ TEMA EKLEME FORMU -->
            {#if showAddThemeForm}
              <div class="bg-cyan-50/70 p-5 rounded-xl border-2 border-cyan-300 mb-6">
                <h3 class="text-lg font-bold text-gray-800 mb-3">{selectedSection.name} — Yeni Tema Ekle</h3>
                <form on:submit|preventDefault={addTheme} class="flex flex-col sm:flex-row gap-3">
                  <input
                    id="new-theme-name"
                    type="text"
                    bind:value={newThemeName}
                    placeholder="Tema adını yazın (örn: Kültür ve Miras)"
                    class="input flex-1"
                    required
                  />
                  <button
                    type="submit"
                    disabled={savingTheme}
                    class="btn btn-primary whitespace-nowrap {savingTheme ? 'opacity-50 cursor-not-allowed' : ''}"
                  >
                    {savingTheme ? 'Ekleniyor...' : 'Tema Ekle'}
                  </button>
                </form>
              </div>
            {/if}

            <!-- TEMA DÜZENLEME FORMU -->
            {#if editingTheme}
              <div class="bg-yellow-50 p-5 rounded-xl border-2 border-yellow-300 mb-6">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-lg font-bold text-gray-800">Tema Adını Düzenle</h3>
                  <button
                    type="button"
                    on:click={cancelEditTheme}
                    class="text-gray-500 hover:text-gray-700 font-semibold text-sm"
                  >
                    ✕ İptal
                  </button>
                </div>
                <form on:submit|preventDefault={updateTheme} class="flex flex-col sm:flex-row gap-3">
                  <input
                    id="edit-theme-name"
                    type="text"
                    bind:value={editingTheme.name}
                    placeholder="Yeni tema adını yazın..."
                    class="input flex-1"
                    required
                  />
                  <button
                    type="submit"
                    disabled={savingTheme}
                    class="btn btn-primary whitespace-nowrap {savingTheme ? 'opacity-50 cursor-not-allowed' : ''}"
                  >
                    {savingTheme ? 'Kaydediliyor...' : 'Kaydet'}
                  </button>
                </form>
              </div>
            {/if}

            {#if selectedSection.themes.length === 0}
              <div class="bg-gray-50 p-10 rounded-xl border-2 border-dashed border-gray-300 text-center">
                <p class="text-gray-600 text-lg font-semibold">Bu sınıfta henüz tema bulunmuyor.</p>
                <p class="text-gray-400 text-sm mt-1 mb-4">İlk temayı eklemek için aşağıdaki butona tıklayın.</p>
                <button
                  on:click={() => showAddThemeForm = true}
                  class="btn btn-success text-sm"
                >
                  + İlk Temayı Ekle
                </button>
              </div>
            {:else}
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {#each selectedSection.themes as theme, tIdx (theme.db_id || theme.id)}
                  <div class="rounded-xl border-2 border-gray-200 bg-gray-50/70 hover:border-cyan-400 hover:bg-cyan-50/40 hover:shadow-md transition-all flex flex-col justify-between">
                    <button
                      type="button"
                      on:click={() => selectTheme(theme.id)}
                      class="w-full text-left p-5 pb-3 flex items-start justify-between gap-4 group"
                    >
                      <div class="flex items-start gap-3 min-w-0">
                        <span class="flex-shrink-0 w-9 h-9 rounded-xl bg-cyan-500 text-white font-bold text-base flex items-center justify-center shadow-sm">
                          {theme.order}
                        </span>
                        <div class="min-w-0">
                          <h3 class="font-bold text-gray-800 text-base group-hover:text-cyan-800 leading-snug">
                            {theme.name}
                          </h3>
                          <p class="text-xs text-gray-500 mt-1.5">
                            <strong>{theme.total_questions}</strong> soru
                            {#if theme.total_questions > 0}
                              <span class="text-gray-400">({theme.active_questions} aktif)</span>
                            {/if}
                          </p>
                        </div>
                      </div>
                      <span class="flex-shrink-0 text-xs font-bold text-cyan-600 mt-1 group-hover:translate-x-1 transition-transform">
                        Sorular →
                      </span>
                    </button>

                    <div class="px-5 py-2.5 border-t border-gray-200/80 flex items-center justify-between gap-2 bg-white/60 rounded-b-xl">
                      <div class="flex items-center gap-1">
                        <button
                          type="button"
                          on:click={() => moveTheme(theme, 'up')}
                          disabled={tIdx === 0}
                          class="px-2 py-1 rounded text-xs font-bold border border-gray-200 bg-white hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Yukarı taşı"
                        >
                          ↑
                        </button>
                        <button
                          type="button"
                          on:click={() => moveTheme(theme, 'down')}
                          disabled={tIdx === selectedSection.themes.length - 1}
                          class="px-2 py-1 rounded text-xs font-bold border border-gray-200 bg-white hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Aşağı taşı"
                        >
                          ↓
                        </button>
                      </div>

                      <div class="flex items-center gap-2">
                        <button
                          type="button"
                          on:click={() => startEditTheme(theme)}
                          class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-lime-100 text-lime-800 hover:bg-lime-200 transition-colors"
                        >
                          Düzenle
                        </button>
                        <button
                          type="button"
                          on:click={() => deleteTheme(theme)}
                          class="text-xs font-semibold px-3 py-1.5 rounded-lg bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                        >
                          Sil
                        </button>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            {/if}

          <!-- SEVİYE 3: SORULAR LİSTESİ & EKLE / DÜZENLE / SİL -->
          {:else if isViewingQuestions}
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
              <div>
                <h2 class="text-2xl font-bold text-gray-800">
                  {#if selectedThemeObj}
                    {selectedSection.name} › {selectedThemeObj.full_name}
                  {:else if selectedSection}
                    🌍 {selectedSection.name}
                  {:else}
                    Kategorisiz Eski Sorular
                  {/if}
                </h2>
                <p class="text-sm text-gray-500 mt-0.5">
                  Bu bölümde <strong>{questions.length}</strong> soru bulunuyor ({questions.filter((q) => q.is_active).length} aktif)
                </p>
              </div>

              <div class="flex flex-wrap gap-2">
                {#if selectedSection?.has_themes}
                  <button
                    on:click={goToThemes}
                    class="px-4 py-2.5 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold text-sm hover:bg-gray-100"
                  >
                    ← Temalara Dön
                  </button>
                {:else}
                  <button
                    on:click={goToSections}
                    class="px-4 py-2.5 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold text-sm hover:bg-gray-100"
                  >
                    ← Bölümlere Dön
                  </button>
                {/if}

                {#if selectedGrade !== '__uncategorized__'}
                  <button
                    on:click={() => { showAddForm = !showAddForm; editingQuestion = null; }}
                    class="btn btn-success text-sm py-2.5 px-5"
                  >
                    {showAddForm ? 'Formu Kapat' : '+ Yeni Soru Ekle'}
                  </button>
                {/if}
              </div>
            </div>

            <!-- Bilgilendirme Banner -->
            {#if feedback}
              <div class="mb-5 px-4 py-3 rounded-xl border-2 text-sm font-semibold flex items-center justify-between {
                feedback.type === 'success'
                  ? 'bg-green-50 border-green-300 text-green-800'
                  : 'bg-red-50 border-red-300 text-red-800'
              }">
                <span>{feedback.type === 'success' ? '✓' : '⚠'} {feedback.text}</span>
                <button on:click={() => feedback = null} class="text-xs underline ml-4">Kapat</button>
              </div>
            {/if}

            <!-- YENİ SORU EKLEME FORMU (Yalnızca 3 Alan!) -->
            {#if showAddForm && selectedGrade !== '__uncategorized__'}
              <div class="bg-cyan-50/60 p-6 rounded-xl border-2 border-cyan-300 mb-6">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-xl font-bold text-gray-800">Yeni Soru Ekle</h3>
                  <span class="text-xs font-bold bg-white text-cyan-800 px-3 py-1 rounded-full border border-cyan-200">
                    {selectedThemeObj ? `${selectedSection.name} • ${selectedThemeObj.full_name}` : selectedSection?.name}
                  </span>
                </div>

                <form on:submit|preventDefault={addQuestion} class="space-y-4">
                  <div>
                    <label for="new-question-text" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Soru *
                    </label>
                    <textarea
                      id="new-question-text"
                      bind:value={newQuestion.question_text}
                      placeholder="Soruyu buraya yazın..."
                      class="input min-h-[84px]"
                      required
                    ></textarea>
                  </div>

                  <div>
                    <label for="new-correct-answer" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Doğru Cevap *
                    </label>
                    <input
                      id="new-correct-answer"
                      type="text"
                      bind:value={newQuestion.correct_answer}
                      placeholder="Doğru cevabı (kavramı) girin"
                      class="input"
                      required
                    />
                  </div>

                  <div>
                    <label for="new-unacceptable-answers" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Kabul Edilmeyecek Yanıtlar
                    </label>
                    <input
                      id="new-unacceptable-answers"
                      type="text"
                      bind:value={newQuestion.unacceptable_answers}
                      placeholder="Örn: atatürk, mustafa kemal, m. kemal"
                      class="input"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                      Oyuncuların yanıltıcı cevap olarak giremeyeceği yanıtları virgülle ayırarak yazın (isteğe bağlı).
                    </p>
                  </div>

                  <div class="flex gap-3">
                    <button
                      type="submit"
                      disabled={saving}
                      class="btn btn-primary flex-1 {saving ? 'opacity-50 cursor-not-allowed' : ''}"
                    >
                      {saving ? 'Kaydediliyor...' : 'Soruyu Kaydet'}
                    </button>
                    <button
                      type="button"
                      on:click={() => showAddForm = false}
                      class="px-5 py-3 rounded-lg border-2 border-gray-300 text-gray-600 font-semibold hover:bg-gray-100"
                    >
                      Kapat
                    </button>
                  </div>
                </form>
              </div>
            {/if}

            <!-- SORU DÜZENLEME FORMU (Yalnızca 3 Alan!) -->
            {#if editingQuestion}
              <div class="bg-yellow-50 p-6 rounded-xl border-2 border-yellow-300 mb-6">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="text-xl font-bold text-gray-800">Soruyu Düzenle</h3>
                  <button
                    type="button"
                    on:click={cancelEdit}
                    class="text-gray-500 hover:text-gray-700 font-semibold text-sm"
                  >
                    ✕ İptal
                  </button>
                </div>

                <form on:submit|preventDefault={updateQuestion} class="space-y-4">
                  <div>
                    <label for="edit-question-text" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Soru *
                    </label>
                    <textarea
                      id="edit-question-text"
                      bind:value={editingQuestion.question_text}
                      placeholder="Soruyu buraya yazın..."
                      class="input min-h-[84px]"
                      required
                    ></textarea>
                  </div>

                  <div>
                    <label for="edit-correct-answer" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Doğru Cevap *
                    </label>
                    <input
                      id="edit-correct-answer"
                      type="text"
                      bind:value={editingQuestion.correct_answer}
                      placeholder="Doğru cevabı girin"
                      class="input"
                      required
                    />
                  </div>

                  <div>
                    <label for="edit-unacceptable-answers" class="block text-sm font-semibold text-gray-700 mb-1.5">
                      Kabul Edilmeyecek Yanıtlar
                    </label>
                    <input
                      id="edit-unacceptable-answers"
                      type="text"
                      bind:value={editingQuestion.unacceptable_answers}
                      placeholder="Örn: atatürk, mustafa kemal, m. kemal"
                      class="input"
                    />
                    <p class="text-xs text-gray-500 mt-1">
                      Oyuncuların yanıltıcı cevap olarak giremeyeceği yanıtları virgülle ayırarak yazın (isteğe bağlı).
                    </p>
                  </div>

                  <div class="flex gap-3">
                    <button
                      type="submit"
                      disabled={saving}
                      class="btn btn-primary flex-1 {saving ? 'opacity-50 cursor-not-allowed' : ''}"
                    >
                      {saving ? 'Güncelleniyor...' : 'Değişiklikleri Kaydet'}
                    </button>
                    <button
                      type="button"
                      on:click={cancelEdit}
                      class="px-5 py-3 rounded-lg border-2 border-gray-300 text-gray-600 font-semibold hover:bg-gray-100"
                    >
                      İptal
                    </button>
                  </div>
                </form>
              </div>
            {/if}

            <!-- SORU LİSTESİ -->
            {#if loadingQuestions}
              <div class="text-center py-10 text-gray-500">Sorular yükleniyor...</div>
            {:else if questions.length === 0}
              <div class="bg-gray-50 p-10 rounded-xl border-2 border-dashed border-gray-300 text-center">
                <p class="text-gray-600 text-lg font-semibold">Bu bölümde henüz soru bulunmuyor.</p>
                {#if selectedGrade !== '__uncategorized__'}
                  <p class="text-gray-400 text-sm mt-1 mb-4">
                    İlk soruyu eklemek için aşağıdaki butona tıklayın.
                  </p>
                  <button
                    on:click={() => showAddForm = true}
                    class="btn btn-success text-sm"
                  >
                    + İlk Soruyu Ekle
                  </button>
                {/if}
              </div>
            {:else}
              <div class="space-y-3">
                {#each questions as question, idx (question.id)}
                  <div class="p-4 rounded-xl border-2 transition-colors {
                    question.is_active
                      ? 'bg-gray-50 border-gray-200 hover:border-cyan-300'
                      : 'bg-red-50/50 border-red-200 hover:border-red-300 opacity-75'
                  }">
                    <div class="flex flex-col sm:flex-row justify-between items-start gap-3 mb-2">
                      <div class="flex-1 min-w-0">
                        <p class="font-semibold text-gray-800 mb-1.5">
                          <span class="text-cyan-600 font-bold mr-1">#{idx + 1}</span>
                          {question.question_text}
                        </p>
                        <p class="text-sm text-green-700 font-semibold">
                          ✓ Doğru Cevap: {question.correct_answer}
                        </p>
                        {#if question.unacceptable_answers}
                          <p class="text-xs text-red-600 mt-1">
                            ✗ Kabul Edilmeyecek Yanıtlar: {question.unacceptable_answers}
                          </p>
                        {/if}
                      </div>

                      <div class="flex gap-2 flex-shrink-0">
                        {#if selectedGrade !== '__uncategorized__'}
                          <button
                            on:click={() => startEdit(question)}
                            class="btn btn-secondary text-xs py-2 px-3.5"
                          >
                            Düzenle
                          </button>
                        {/if}
                        <button
                          on:click={() => deleteQuestion(question.id)}
                          class="btn btn-danger text-xs py-2 px-3.5"
                        >
                          Sil
                        </button>
                      </div>
                    </div>

                    <div class="flex gap-2 flex-wrap pt-2 border-t border-gray-200/70">
                      <button
                        on:click={() => toggleQuestion(question.id)}
                        class="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full cursor-pointer transition-colors {
                          question.is_active
                            ? 'bg-cyan-100 text-cyan-700 hover:bg-cyan-200'
                            : 'bg-red-100 text-red-700 hover:bg-red-200'
                        }"
                        title={question.is_active ? 'Pasif yapmak için tıklayın' : 'Aktif yapmak için tıklayın'}
                      >
                        <span class="relative inline-block w-7 h-3.5 rounded-full transition-colors {question.is_active ? 'bg-cyan-500' : 'bg-red-400'}">
                          <span class="absolute top-0.5 {question.is_active ? 'left-3.5' : 'left-0.5'} inline-block w-2.5 h-2.5 rounded-full bg-white transition-all shadow"></span>
                        </span>
                        {question.is_active ? 'Aktif' : 'Pasif'}
                      </button>

                      {#if question.stats}
                        <span class="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                          {question.stats.games_used} oyun
                        </span>
                        <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                          {question.stats.times_asked} eşleştirme
                        </span>
                        <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                          ✓ {question.stats.times_correct} doğru
                        </span>
                        <span class="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                          ✗ {question.stats.times_wrong} yanlış
                        </span>
                        <span class="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">
                          %{question.stats.success_rate.toFixed(1)} başarı
                        </span>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          {/if}
        </div>

      <!-- SEKME 2: MASALAR -->
      {:else if activeTab === 'rooms'}
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
          <div class="flex flex-wrap justify-between items-center gap-3 mb-4">
            <h2 class="text-2xl font-bold text-gray-800">
              Tüm Masalar ({rooms.length})
              <span class="text-sm text-gray-400 font-normal ml-2">(5 sn'de bir güncellenir)</span>
            </h2>
            <div class="flex items-center gap-2">
              <button
                on:click={() => roomsFilter = 'all'}
                class="text-xs font-bold px-3 py-1.5 rounded-full border {roomsFilter === 'all' ? 'bg-primary text-white border-primary' : 'bg-white text-gray-600 border-gray-300'}"
              >
                Tümü ({rooms.length})
              </button>
              <button
                on:click={() => roomsFilter = 'active'}
                class="text-xs font-bold px-3 py-1.5 rounded-full border {roomsFilter === 'active' ? 'bg-primary text-white border-primary' : 'bg-white text-gray-600 border-gray-300'}"
              >
                Aktif ({activeRoomsCount})
              </button>
              <button on:click={loadRooms} class="text-sm text-cyan-600 font-semibold hover:underline ml-2">
                🔄 Yenile
              </button>
            </div>
          </div>

          <div class="space-y-3">
            {#each (roomsFilter === 'active' ? rooms.filter((r) => r.players.length > 0) : rooms) as room}
              <div class="p-4 rounded-xl border-2 {
                room.players.length === 0 ? 'bg-gray-50 border-gray-200' :
                room.phase === 'waiting' ? 'bg-blue-50/70 border-blue-200' :
                'bg-orange-50/70 border-orange-200'
              }">
                <div class="flex flex-wrap justify-between items-center gap-2 mb-2">
                  <div class="flex items-center gap-2.5 flex-wrap">
                    {#if room.icon}
                      <img src={room.icon} alt={room.name} class="w-9 h-9 rounded-lg flex-shrink-0" />
                    {/if}
                    <h3 class="text-base font-bold text-gray-800">{room.name}</h3>
                    {#if room.group}
                      <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-200/80 text-gray-700">
                        {room.group}
                      </span>
                    {/if}
                    <span class="text-xs font-semibold px-2 py-0.5 rounded-full {
                      room.phase === 'waiting' ? 'bg-blue-100 text-blue-700' :
                      room.phase === 'game_over' ? 'bg-gray-200 text-gray-700' :
                      'bg-green-100 text-green-700'
                    }">
                      {getPhaseText(room.phase)}
                    </span>
                    {#if room.topic}
                      <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-100 text-cyan-800">
                        {room.topic.label}
                      </span>
                    {/if}
                    {#if room.phase !== 'waiting' && room.phase !== 'game_over' && room.current_round !== null}
                      <span class="text-xs bg-purple-100 text-purple-700 font-semibold px-2 py-0.5 rounded-full">
                        {room.current_round + 1}/{room.max_rounds}
                      </span>
                    {/if}
                  </div>

                  <div class="flex items-center gap-2">
                    <span class="text-sm font-bold {room.players.length === 0 ? 'text-gray-400' : 'text-orange-600'}">
                      {room.players.length}/{room.max_players} oyuncu
                    </span>
                    {#if room.players.length > 0}
                      <button
                        on:click={() => resetRoom(room.room_code)}
                        class="btn btn-danger text-xs py-1 px-2.5"
                      >
                        Temizle
                      </button>
                    {/if}
                  </div>
                </div>

                {#if room.players.length > 0}
                  <div class="flex flex-wrap gap-2">
                    {#each room.players as player}
                      <div class="bg-white px-2.5 py-1 rounded-lg text-xs border {player.is_host ? 'border-yellow-400' : 'border-gray-200'}">
                        {#if player.is_host}👑{/if}
                        <span class="font-semibold">{player.name}</span>
                        <span class="text-gray-500">({player.score})</span>
                        {#if !player.is_connected}
                          <span class="text-red-500">⚠</span>
                        {/if}
                      </div>
                    {/each}
                  </div>
                  {#if room.current_question}
                    <div class="mt-2 bg-white/80 px-3 py-1.5 rounded-lg text-xs">
                      <span class="text-gray-500">Soru:</span>
                      <span class="font-medium text-gray-800 ml-1">{room.current_question}</span>
                    </div>
                  {/if}
                {/if}
              </div>
            {/each}
          </div>
        </div>

      <!-- SEKME 3: KULLANICILAR -->
      {:else if activeTab === 'users'}
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
          <div class="flex flex-wrap justify-between items-center gap-3 mb-4">
            <h2 class="text-2xl font-bold text-gray-800">Kayıtlı Kullanıcılar ({users.length})</h2>
            {#if users.length > 0}
              <button
                on:click={deleteAllUsers}
                class="btn btn-danger text-xs py-2 px-4"
              >
                Tüm Kullanıcıları Sıfırla
              </button>
            {/if}
          </div>

          {#if users.length === 0}
            <div class="bg-gray-50 p-8 rounded-lg border-2 border-gray-200 text-center">
              <p class="text-gray-500 text-lg">Henüz kayıtlı kullanıcı yok.</p>
            </div>
          {:else}
            <div class="overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kullanıcı Adı</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Oyun</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Kazanma</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Toplam Puan</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">En Yüksek</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Doğruluk</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Son Giriş</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">İşlem</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  {#each users as user (user.user_id)}
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap text-sm font-bold text-primary">{user.user_id}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{user.username}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{user.stats?.total_games_played || 0}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{user.stats?.total_games_won || 0}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold text-cyan-600">{user.stats?.total_score?.toLocaleString() || 0}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm font-semibold text-lime-600">{user.stats?.highest_score?.toLocaleString() || 0}</td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {user.stats?.total_questions_answered > 0
                          ? ((user.stats.total_correct_answers / user.stats.total_questions_answered) * 100).toFixed(1)
                          : 0}%
                      </td>
                      <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                        {new Date(user.last_login).toLocaleString('tr-TR')}
                      </td>
                      <td class="px-4 py-3 whitespace-nowrap text-right">
                        <button
                          on:click={() => deleteUser(user)}
                          class="btn btn-danger text-xs py-1.5 px-3"
                        >
                          Sil
                        </button>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
        </div>

      <!-- SEKME 4: İSTATİSTİKLER -->
      {:else if activeTab === 'stats'}
        <div class="bg-white rounded-2xl shadow-xl p-6 md:p-8">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Genel Oyun İstatistikleri</h2>
          {#if stats}
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="bg-purple-50 p-4 rounded-xl border border-purple-200">
                <p class="text-gray-600 text-sm font-semibold">Toplam Oyuncu</p>
                <p class="text-3xl font-bold text-purple-700">{stats.total_players}</p>
              </div>
              <div class="bg-blue-50 p-4 rounded-xl border border-blue-200">
                <p class="text-gray-600 text-sm font-semibold">Toplam Oturum</p>
                <p class="text-3xl font-bold text-blue-700">{stats.total_sessions}</p>
              </div>
              <div class="bg-cyan-50 p-4 rounded-xl border border-cyan-200">
                <p class="text-gray-600 text-sm font-semibold">Tamamlanan Oyun</p>
                <p class="text-3xl font-bold text-cyan-700">{stats.completed_sessions}</p>
              </div>
              <div class="bg-lime-50 p-4 rounded-xl border border-lime-200">
                <p class="text-gray-600 text-sm font-semibold">Eşleştirilen Kavram</p>
                <p class="text-3xl font-bold text-lime-700">{stats.total_questions_answered}</p>
              </div>
              <div class="bg-green-50 p-4 rounded-xl border border-green-200">
                <p class="text-gray-600 text-sm font-semibold">Doğru Eşleştirme</p>
                <p class="text-3xl font-bold text-green-700">{stats.total_correct_answers}</p>
              </div>
              <div class="bg-red-50 p-4 rounded-xl border border-red-200">
                <p class="text-gray-600 text-sm font-semibold">Yanlış Eşleştirme</p>
                <p class="text-3xl font-bold text-red-700">{stats.total_wrong_answers}</p>
              </div>
              <div class="bg-yellow-50 p-4 rounded-xl border border-yellow-200">
                <p class="text-gray-600 text-sm font-semibold">Başarı Oranı</p>
                <p class="text-3xl font-bold text-yellow-700">
                  {stats.total_questions_answered > 0
                    ? ((stats.total_correct_answers / stats.total_questions_answered) * 100).toFixed(1)
                    : 0}%
                </p>
              </div>
              <div class="bg-indigo-50 p-4 rounded-xl border border-indigo-200">
                <p class="text-gray-600 text-sm font-semibold">Ort. Oyuncu/Oyun</p>
                <p class="text-3xl font-bold text-indigo-700">
                  {stats.completed_sessions > 0
                    ? (stats.total_players / stats.completed_sessions).toFixed(1)
                    : 0}
                </p>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  :global(body) {
    background: transparent;
  }
</style>
