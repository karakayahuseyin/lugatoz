<script>
  export let onClose = () => {};
</script>

<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" on:click={onClose} on:keydown={(e) => e.key === 'Escape' && onClose()} role="dialog" aria-modal="true" tabindex="-1">
  <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
  <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" on:click|stopPropagation on:keydown|stopPropagation role="document">
    <!-- Header -->
    <div class="sticky top-0 bg-gradient-to-r from-cyan-500 to-lime-500 text-white p-6 rounded-t-2xl">
      <div class="flex justify-between items-center">
        <h2 class="text-3xl font-bold">TarihTöz Nasıl Oynanır?</h2>
        <button
          on:click={onClose}
          class="text-white hover:text-gray-200 text-3xl font-bold w-10 h-10 flex items-center justify-center"
        >
          ×
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="p-8 space-y-8">
      <!-- Step 1 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-cyan-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          1
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Sınıf ve Tema Seçin</h3>
          <p class="text-gray-600 text-sm">
            Giriş ekranında <strong>5, 6, 7, 8. Sınıf</strong> bölümlerinden birini ve o sınıfa ait bir temayı (veya <strong>Tüm Temalar (Karışık)</strong>) seçin ya da
            <strong>Dünyanın Enleri</strong> bölümüne tema seçmeden doğrudan girin. Oyunda yalnızca seçtiğiniz bölüme ait sorular gelir!
          </p>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-yellow-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          2
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Yanıltıcı Cevap Yazın</h3>
          <div class="bg-yellow-50 rounded-lg p-4 border-2 border-yellow-300">
            <p class="text-sm text-gray-600 mb-2">Örnek: <em>Mustafa Kemal'in 1881'de doğduğu şehir hangisidir?</em></p>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-red-500 font-bold">✗</span>
                <span class="text-gray-700">Selanik <span class="text-xs">(Doğru cevap - yazılamaz!)</span></span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-green-500 font-bold">✓</span>
                <span class="text-gray-700">Manastır <span class="text-xs">(İnandırıcı ama yanlış)</span></span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-green-500 font-bold">✓</span>
                <span class="text-gray-700">İstanbul <span class="text-xs">(İnandırıcı ama yanlış)</span></span>
              </div>
            </div>
          </div>
          <p class="text-gray-600 mt-2 text-sm">
            <strong>Amaç:</strong> Doğru cevaptan farklı, ama diğer oyuncuları kandırabilecek bir yanıt yazmak!
          </p>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-blue-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          3
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Doğru Cevabı Seçin</h3>
          <p class="text-gray-600 text-sm">
            Tüm oyuncuların yazdığı yanıltıcı cevaplar ve doğru cevap karışık olarak ekrana gelir.
            Kendi yazdığınız cevabı seçmeden doğru olanı bulmaya çalışın!
          </p>
        </div>
      </div>

      <!-- Step 4 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-green-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          4
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Puan Kazanın!</h3>
          <div class="bg-gradient-to-r from-cyan-50 to-lime-50 rounded-lg p-4 border-2 border-cyan-200 space-y-3">
            <div class="flex items-center justify-between p-3 bg-white rounded-lg">
              <span class="font-semibold text-gray-700">Doğru cevabı seçerseniz</span>
              <span class="text-2xl font-bold text-green-600">+1000</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-white rounded-lg">
              <span class="font-semibold text-gray-700">Birisi sizin yanıltıcı cevabınızı seçerse</span>
              <span class="text-2xl font-bold text-cyan-600">+500</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-white rounded-lg">
              <span class="font-semibold text-gray-700">Süre dolunca cevap vermezseniz</span>
              <span class="text-2xl font-bold text-red-600">-100</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Concept Matching Info -->
      <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl p-6">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 text-4xl">🧩</div>
          <div>
            <h3 class="text-2xl font-bold mb-2">Oyun Sonu: Kavram Eşleştirme</h3>
            <p class="text-white text-opacity-90">
              Turlar bittiğinde, o oyunda çıkan sorulardan kavramlar ekrana gelir!
              <strong>Sürükle-bırak</strong> veya <strong>tıkla-eşleştir</strong> yöntemiyle her kavramı doğru soruyla eşleştirin.
              Her doğru eşleştirme için <strong>+500 puan</strong> kazanırsınız!
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="sticky bottom-0 bg-gray-50 p-6 rounded-b-2xl border-t-2 border-gray-200">
      <button
        on:click={onClose}
        class="btn btn-primary w-full text-lg"
      >
        Anladım, Oyuna Başlayalım!
      </button>
    </div>
  </div>
</div>
