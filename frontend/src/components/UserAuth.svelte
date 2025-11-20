<script>
  import { userStore } from '../stores/userStore';
  import { socketManager } from '../utils/socket';
  import { notifications } from '../stores/notificationStore';
  import { onMount } from 'svelte';

  export let onComplete = () => {};

  let mode = 'login'; // 'login' or 'register'
  let username = '';
  let userId = '';
  let isProcessing = false;

  onMount(() => {
    // Try to auto-login from localStorage
    const userData = userStore.loadFromStorage();
    if (userData && userData.userId) {
      // Attempt to login with stored user_id
      autoLogin(userData.userId);
    }

    // Listen for auth responses
    const socket = socketManager.getSocket();

    socket.on('register_success', (data) => {
      userStore.login(data.user_id, data.username);
      notifications.success(`Hoş geldin, ${data.username}! ID: ${data.user_id}`);
      isProcessing = false;
      onComplete();
    });

    socket.on('register_error', (data) => {
      notifications.error(data.message);
      isProcessing = false;
    });

    socket.on('login_success', (data) => {
      userStore.login(data.user_id, data.username);
      notifications.success(`Tekrar hoş geldin, ${data.username}!`);
      isProcessing = false;
      onComplete();
    });

    socket.on('login_error', (data) => {
      notifications.error(data.message);
      isProcessing = false;
      // Clear invalid stored data
      userStore.logout();
    });

    return () => {
      socket.off('register_success');
      socket.off('register_error');
      socket.off('login_success');
      socket.off('login_error');
    };
  });

  function autoLogin(userId) {
    isProcessing = true;
    socketManager.emit('login_user', { user_id: userId });
  }

  function handleSubmit() {
    if (mode === 'register') {
      if (!username.trim()) {
        notifications.warning('Lütfen kullanıcı adı girin!');
        return;
      }

      if (username.trim().length < 3) {
        notifications.warning('Kullanıcı adı en az 3 karakter olmalıdır!');
        return;
      }

      isProcessing = true;
      socketManager.emit('register_user', { username: username.trim() });
    } else {
      // Login with user_id only
      if (!userId.trim()) {
        notifications.warning('Lütfen kullanıcı ID\'nizi girin!');
        return;
      }

      const id = parseInt(userId.trim());
      if (isNaN(id) || id < 10000 || id > 99999) {
        notifications.warning('Geçersiz ID! 5 basamaklı sayı olmalı.');
        return;
      }

      isProcessing = true;
      socketManager.emit('login_user', { user_id: id });
    }
  }

  function switchMode() {
    mode = mode === 'login' ? 'register' : 'login';
    username = '';
    userId = '';
  }

  function skipAuth() {
    onComplete();
  }

  function handleClose() {
    if (!isProcessing) {
      onComplete();
    }
  }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50" on:click={handleClose} role="dialog" aria-modal="true">
  <div class="card max-w-md w-full" on:click|stopPropagation role="document">
  <div class="text-center mb-6">
    <h2 class="text-3xl font-bold text-primary mb-2">
      {mode === 'register' ? 'Hesap Oluştur' : 'Giriş Yap'}
    </h2>
    <p class="text-gray-600">
      {mode === 'register'
        ? 'İstatistiklerinizi takip etmek için hesap oluşturun'
        : 'Hesabınıza giriş yapın'}
    </p>
  </div>

  <form on:submit|preventDefault={handleSubmit} class="space-y-4">
    {#if mode === 'register'}
      <div>
        <label for="username" class="block text-sm font-semibold text-gray-700 mb-2">
          Kullanıcı Adı
        </label>
        <input
          id="username"
          type="text"
          bind:value={username}
          disabled={isProcessing}
          placeholder="Kullanıcı adınızı girin"
          class="input w-full"
          maxlength="50"
          autofocus
        />
        <p class="text-xs text-gray-500 mt-1">En az 3 karakter - Kayıt olduktan sonra size bir ID verilecek</p>
      </div>
    {:else}
      <div>
        <label for="userId" class="block text-sm font-semibold text-gray-700 mb-2">
          Kullanıcı ID
        </label>
        <input
          id="userId"
          type="text"
          bind:value={userId}
          disabled={isProcessing}
          placeholder="5 basamaklı ID'nizi girin"
          class="input w-full"
          maxlength="5"
          autofocus
        />
        <p class="text-xs text-gray-500 mt-1">Hesap oluştururken aldığınız 5 basamaklı ID</p>
      </div>
    {/if}

    <button
      type="submit"
      disabled={isProcessing}
      class="btn btn-primary w-full text-lg py-3 {isProcessing ? 'opacity-50 cursor-not-allowed' : ''}"
    >
      {#if isProcessing}
        <div class="inline-block animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
        İşleniyor...
      {:else}
        {mode === 'register' ? 'Hesap Oluştur' : 'Giriş Yap'}
      {/if}
    </button>
  </form>

  <div class="mt-6 text-center">
    <button
      on:click={switchMode}
      disabled={isProcessing}
      class="text-primary hover:underline font-semibold"
    >
      {mode === 'register' ? 'Zaten hesabınız var mı? Giriş yapın' : 'Hesabınız yok mu? Kayıt olun'}
    </button>
  </div>

  <div class="mt-4 text-center">
    <button
      on:click={skipAuth}
      disabled={isProcessing}
      class="text-gray-500 hover:underline text-sm"
    >
      Misafir olarak devam et (istatistikler kaydedilmez)
    </button>
  </div>
  </div>
</div>
