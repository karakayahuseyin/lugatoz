<script>
  import { onMount } from 'svelte';

  let questions = [];
  let showAddForm = false;
  let editingQuestion = null;
  let isAuthenticated = false;
  let passwordInput = '';
  let stats = null;

  const ADMIN_PASSWORD = 'lugatoz23';

  let newQuestion = {
    question_text: '',
    correct_answer: '',
    acceptable_answers: ''
  };

  function checkPassword() {
    if (passwordInput === ADMIN_PASSWORD) {
      isAuthenticated = true;
      loadQuestions();
      loadStats();
    } else {
      alert('Yanlış şifre!');
      passwordInput = '';
    }
  }

  onMount(async () => {
    // Don't load until authenticated
  });

  async function loadQuestions() {
    try {
      const response = await fetch('/api/questions');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      questions = await response.json();
    } catch (error) {
      console.error('Sorular yuklenemedi:', error);
      alert('Sorular yuklenemedi! Backend baglantisini kontrol edin.');
    }
  }

  async function loadStats() {
    try {
      const response = await fetch('/api/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      stats = await response.json();
    } catch (error) {
      console.error('Istatistikler yuklenemedi:', error);
    }
  }


  async function addQuestion() {
    if (!newQuestion.question_text || !newQuestion.correct_answer) {
      alert('Soru ve cevap alanları zorunludur!');
      return;
    }

    try {
      const response = await fetch('/api/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newQuestion)
      });

      if (response.ok) {
        alert('Soru başarıyla eklendi!');
        newQuestion = {
          question_text: '',
          correct_answer: '',
          acceptable_answers: ''
        };
        showAddForm = false;
        await loadQuestions();
      } else {
        alert('Soru eklenemedi!');
      }
    } catch (error) {
      console.error('Soru eklenemedi:', error);
      alert('Soru eklenirken bir hata oluştu!');
    }
  }

  function startEdit(question) {
    editingQuestion = { ...question };
    showAddForm = false;
  }

  function cancelEdit() {
    editingQuestion = null;
  }

  async function updateQuestion() {
    if (!editingQuestion.question_text || !editingQuestion.correct_answer) {
      alert('Soru ve cevap alanları zorunludur!');
      return;
    }

    try {
      const response = await fetch(`/api/questions/${editingQuestion.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question_text: editingQuestion.question_text,
          correct_answer: editingQuestion.correct_answer,
          acceptable_answers: editingQuestion.acceptable_answers
        })
      });

      if (response.ok) {
        alert('Soru başarıyla güncellendi!');
        editingQuestion = null;
        await loadQuestions();
      } else {
        alert('Soru güncellenemedi!');
      }
    } catch (error) {
      console.error('Soru güncellenemedi:', error);
      alert('Soru güncellenirken bir hata oluştu!');
    }
  }

  async function deleteQuestion(id) {
    if (!confirm('Bu soruyu silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      const response = await fetch(`/api/questions/${id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        alert('Soru silindi!');
        await loadQuestions();
      } else {
        alert('Soru silinemedi!');
      }
    } catch (error) {
      console.error('Soru silinemedi:', error);
      alert('Soru silinirken bir hata oluştu!');
    }
  }
</script>

<div class="min-h-screen bg-gradient-to-br from-cyan-100 to-lime-100 p-6">
  {#if !isAuthenticated}
    <!-- Login Screen -->
    <div class="max-w-md mx-auto mt-20">
      <div class="bg-white rounded-2xl shadow-2xl p-8">
        <h1 class="text-3xl font-bold text-primary text-center mb-6">LügaTöz Admin Paneli</h1>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Şifre
            </label>
            <input
              type="password"
              bind:value={passwordInput}
              on:keypress={(e) => e.key === 'Enter' && checkPassword()}
              placeholder="Admin şifresini girin"
              class="input"
              autofocus
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
    <!-- Admin Panel -->
    <div class="max-w-6xl mx-auto">
      <div class="bg-white rounded-2xl shadow-2xl p-8 mb-6">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-4xl font-bold text-primary">LügaTöz Admin Paneli</h1>
          <a href="/#" class="btn btn-secondary">
            Oyuna Dön
          </a>
        </div>

      <!-- İstatistikler -->
      {#if stats}
        <div class="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border-2 border-purple-200 mb-6">
          <h2 class="text-2xl font-bold text-purple-800 mb-4">Oyun İstatistikleri</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Toplam Oyuncu</p>
              <p class="text-3xl font-bold text-purple-700">{stats.total_players}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Toplam Oturum</p>
              <p class="text-3xl font-bold text-blue-700">{stats.total_sessions}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Tamamlanan Oyun</p>
              <p class="text-3xl font-bold text-cyan-700">{stats.completed_sessions}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Cevaplanan Soru</p>
              <p class="text-3xl font-bold text-lime-700">{stats.total_questions_answered}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Doğru Cevap</p>
              <p class="text-3xl font-bold text-green-700">{stats.total_correct_answers}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Yanlış Cevap</p>
              <p class="text-3xl font-bold text-red-700">{stats.total_wrong_answers}</p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Başarı Oranı</p>
              <p class="text-3xl font-bold text-yellow-700">
                {stats.total_questions_answered > 0
                  ? ((stats.total_correct_answers / stats.total_questions_answered) * 100).toFixed(1)
                  : 0}%
              </p>
            </div>
            <div class="bg-white p-4 rounded-lg shadow">
              <p class="text-gray-600 text-sm font-semibold">Ort. Oyuncu/Oyun</p>
              <p class="text-3xl font-bold text-indigo-700">
                {stats.completed_sessions > 0
                  ? (stats.total_players / stats.completed_sessions).toFixed(1)
                  : 0}
              </p>
            </div>
          </div>
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="bg-cyan-50 p-4 rounded-lg border-2 border-cyan-200">
          <p class="text-cyan-600 font-semibold">Toplam Soru</p>
          <p class="text-3xl font-bold text-cyan-700">{questions.length}</p>
        </div>
        <div class="bg-lime-50 p-4 rounded-lg border-2 border-lime-200">
          <p class="text-lime-600 font-semibold">Aktif Soru</p>
          <p class="text-3xl font-bold text-lime-700">
            {questions.filter(q => q.is_active).length}
          </p>
        </div>
      </div>

      <button
        on:click={() => showAddForm = !showAddForm}
        class="btn btn-success mb-4"
      >
        {showAddForm ? 'Formu Kapat' : 'Yeni Soru Ekle'}
      </button>

      {#if showAddForm}
        <div class="bg-gray-50 p-6 rounded-lg border-2 border-gray-200 mb-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Yeni Soru Ekle</h2>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Soru Metni
              </label>
              <textarea
                bind:value={newQuestion.question_text}
                placeholder="Sorunuzu buraya yazın..."
                class="input min-h-[80px]"
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Doğru Cevap (Görünür)
              </label>
              <input
                type="text"
                bind:value={newQuestion.correct_answer}
                placeholder="Doğru cevabı girin"
                class="input"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Kabul Edilebilir Cevaplar (Virgülle ayırın)
              </label>
              <input
                type="text"
                bind:value={newQuestion.acceptable_answers}
                placeholder="ankara,turkiyenin baskenti"
                class="input"
              />
              <p class="text-xs text-gray-500 mt-1">
                Alternatif doğru cevaplar. Virgülle ayırın, küçük harfle yazın.
              </p>
            </div>

            <button
              on:click={addQuestion}
              class="btn btn-primary w-full"
            >
              Soruyu Ekle
            </button>
          </div>
        </div>
      {/if}

      {#if editingQuestion}
        <div class="bg-yellow-50 p-6 rounded-lg border-2 border-yellow-300 mb-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold text-gray-800">Soru Düzenle</h2>
            <button
              on:click={cancelEdit}
              class="text-gray-500 hover:text-gray-700 font-semibold"
            >
              ✕ İptal
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Soru Metni
              </label>
              <textarea
                bind:value={editingQuestion.question_text}
                placeholder="Sorunuzu buraya yazın..."
                class="input min-h-[80px]"
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Doğru Cevap (Görünür)
              </label>
              <input
                type="text"
                bind:value={editingQuestion.correct_answer}
                placeholder="Doğru cevabı girin"
                class="input"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Kabul Edilebilir Cevaplar (Virgülle ayırın)
              </label>
              <input
                type="text"
                bind:value={editingQuestion.acceptable_answers}
                placeholder="ankara,turkiyenin baskenti"
                class="input"
              />
              <p class="text-xs text-gray-500 mt-1">
                Alternatif doğru cevaplar. Virgülle ayırın, küçük harfle yazın.
              </p>
            </div>

            <button
              on:click={updateQuestion}
              class="btn btn-primary w-full"
            >
              Değişiklikleri Kaydet
            </button>
          </div>
        </div>
      {/if}
    </div>

    <div class="bg-white rounded-2xl shadow-2xl p-8">
      <h2 class="text-2xl font-bold text-gray-800 mb-4">Tüm Sorular ({questions.length})</h2>

      {#if questions.length === 0}
        <div class="bg-gray-50 p-8 rounded-lg border-2 border-gray-200 text-center">
          <p class="text-gray-500 text-lg">Henüz soru eklenmemiş.</p>
          <p class="text-gray-400 text-sm mt-2">Yeni soru eklemek için yukarıdaki butonu kullanın.</p>
        </div>
      {:else}
        <div class="space-y-3">
          {#each questions as question}
            <div class="bg-gray-50 p-4 rounded-lg border-2 border-gray-200 hover:border-cyan-300 transition-colors">
              <div class="flex justify-between items-start mb-2">
                <div class="flex-1">
                  <p class="font-semibold text-gray-800 mb-1">
                    {question.question_text}
                  </p>
                  <p class="text-sm text-cyan-700 font-semibold">
                    ✓ {question.correct_answer}
                  </p>
                  {#if question.acceptable_answers}
                    <p class="text-xs text-gray-500 mt-1">
                      Kabul edilebilir: {question.acceptable_answers}
                    </p>
                  {/if}
                </div>
                <div class="flex gap-2">
                  <button
                    on:click={() => startEdit(question)}
                    class="btn btn-secondary text-sm py-2 px-4"
                  >
                    Düzenle
                  </button>
                  <button
                    on:click={() => deleteQuestion(question.id)}
                    class="btn btn-danger text-sm py-2 px-4"
                  >
                    Sil
                  </button>
                </div>
              </div>

              <div class="flex gap-2 flex-wrap">
                <span class="text-xs {question.is_active ? 'bg-cyan-100 text-cyan-700' : 'bg-red-100 text-red-700'} px-2 py-1 rounded-full">
                  {question.is_active ? 'Aktif' : 'Pasif'}
                </span>
                {#if question.stats}
                  <span class="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                    {question.stats.games_used} oyunda kullanıldı
                  </span>
                  <span class="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                    {question.stats.times_asked} kez soruldu
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
                  <span class="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded-full">
                    {question.stats.total_players_seen} oyuncu gördü
                  </span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
  {/if}
</div>

<style>
  :global(body) {
    background: transparent;
  }
</style>
