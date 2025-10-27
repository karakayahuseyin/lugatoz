<script>
  export let onClose = () => {};
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
  <div class="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
    <!-- Header -->
    <div class="sticky top-0 bg-gradient-to-r from-cyan-500 to-lime-500 text-white p-6 rounded-t-2xl">
      <div class="flex justify-between items-center">
        <h2 class="text-3xl font-bold">Nasıl Oynanır?</h2>
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
          <h3 class="text-xl font-bold text-gray-800 mb-2">Soru Gösterilir</h3>
          <div class="bg-gray-50 rounded-lg p-4 border-2 border-gray-200">
            <p class="text-sm text-gray-600 mb-2">Örnek:</p>
            <p class="font-semibold text-gray-800">Türkiye'nin başkenti neresidir?</p>
          </div>
          <p class="text-gray-600 mt-2 text-sm">
            Her turda bir soru sorulur. Tüm oyuncular bu soruyu görür.
          </p>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-lime-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          2
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Yanıltıcı Cevap Yazın</h3>
          <div class="bg-yellow-50 rounded-lg p-4 border-2 border-yellow-300">
            <p class="text-sm text-gray-600 mb-2">Doğru cevabı biliyorsanız:</p>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <span class="text-red-500 font-bold">✗</span>
                <span class="text-gray-700">Ankara <span class="text-xs">(Doğru cevap - yazılamaz!)</span></span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-green-500 font-bold">✓</span>
                <span class="text-gray-700">İstanbul <span class="text-xs">(İnandırıcı ama yanlış)</span></span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-green-500 font-bold">✓</span>
                <span class="text-gray-700">İzmir <span class="text-xs">(İnandırıcı ama yanlış)</span></span>
              </div>
            </div>
          </div>
          <p class="text-gray-600 mt-2 text-sm">
            <strong>Amaç:</strong> Doğru cevaptan farklı, ama diğer oyuncuları kandırabilecek bir cevap yazmak!
          </p>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-cyan-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
          3
        </div>
        <div class="flex-1">
          <h3 class="text-xl font-bold text-gray-800 mb-2">Doğru Cevabı Seçin</h3>
          <div class="bg-blue-50 rounded-lg p-4 border-2 border-blue-200 space-y-2">
            <p class="text-sm text-gray-600 mb-3">Tüm cevaplar karışık şekilde gösterilir:</p>
            <div class="space-y-2">
              <button class="w-full text-left p-3 bg-white rounded-lg border-2 border-gray-300 hover:border-cyan-400">
                A) İzmir
              </button>
              <button class="w-full text-left p-3 bg-white rounded-lg border-2 border-gray-300 hover:border-cyan-400">
                B) Ankara
              </button>
              <button class="w-full text-left p-3 bg-white rounded-lg border-2 border-gray-300 hover:border-cyan-400">
                C) İstanbul
              </button>
              <button class="w-full text-left p-3 bg-white rounded-lg border-2 border-gray-300 hover:border-cyan-400">
                D) Bursa
              </button>
            </div>
          </div>
          <p class="text-gray-600 mt-2 text-sm">
            Oyuncuların yazdığı yanlış cevaplar + doğru cevap birlikte gösterilir. Doğruyu bulmaya çalışın!
          </p>
        </div>
      </div>

      <!-- Step 4 -->
      <div class="flex gap-6 items-start">
        <div class="flex-shrink-0 w-16 h-16 bg-lime-500 text-white rounded-full flex items-center justify-center text-2xl font-bold">
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
              <span class="font-semibold text-gray-700">Birisi sizin cevabınızı seçerse</span>
              <span class="text-2xl font-bold text-cyan-600">+500</span>
            </div>
            <div class="flex items-center justify-between p-3 bg-white rounded-lg">
              <span class="font-semibold text-gray-700">Süre dolunca cevap vermezseniz</span>
              <span class="text-2xl font-bold text-red-600">-100</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Final Test Info -->
      <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl p-6">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 text-4xl">🏆</div>
          <div>
            <h3 class="text-2xl font-bold mb-2">Final Testi</h3>
            <p class="text-white text-opacity-90">
              10 soruluk tur bitiminde, oyunda çıkan sorulardan oluşan bir final testi var!
              Her doğru cevap için <strong>+500 puan</strong> kazanırsınız.
            </p>
          </div>
        </div>
      </div>

      <!-- Tips -->
      <div class="bg-yellow-50 rounded-xl p-6 border-2 border-yellow-200">
        <h3 class="text-xl font-bold text-gray-800 mb-3 flex items-center gap-2">
          💡 İpuçları
        </h3>
        <ul class="space-y-2 text-gray-700">
          <li class="flex items-start gap-2">
            <span class="text-yellow-600 font-bold">•</span>
            <span>Her turda <strong>10 soru</strong> bulunur</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-yellow-600 font-bold">•</span>
            <span>Cevaplarınızı inandırıcı yapın - böylece rakiplerinizi yanıltabilirsiniz!</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-yellow-600 font-bold">•</span>
            <span>Doğru cevabı giremezsiniz - sistem bunu kabul etmez</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-yellow-600 font-bold">•</span>
            <span>Başka bir oyuncunun girdiği cevabı giremezsiniz</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-yellow-600 font-bold">•</span>
            <span>En yüksek puanı alan kazanır!</span>
          </li>
        </ul>
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
