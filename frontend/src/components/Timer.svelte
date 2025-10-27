<script>
  import { onMount, onDestroy } from 'svelte';

  export let duration = 10; // Duration in seconds
  export let onTimeout = () => {}; // Callback when timer reaches 0
  export let autoStart = true;

  let timeLeft = duration;
  let interval;
  let isRunning = false;

  export function start() {
    if (isRunning) return;
    isRunning = true;
    timeLeft = duration;

    interval = setInterval(() => {
      timeLeft--;

      if (timeLeft <= 0) {
        stop();
        onTimeout();
      }
    }, 1000);
  }

  export function stop() {
    if (interval) {
      clearInterval(interval);
      interval = null;
    }
    isRunning = false;
  }

  export function reset() {
    stop();
    timeLeft = duration;
  }

  onMount(() => {
    if (autoStart) {
      start();
    }
  });

  onDestroy(() => {
    stop();
  });

  $: percentage = (timeLeft / duration) * 100;
  $: isWarning = timeLeft <= 5 && timeLeft > 0;
  $: isDanger = timeLeft <= 3 && timeLeft > 0;
</script>

<div class="timer-container">
  <div class="timer-wrapper">
    <svg class="timer-svg" viewBox="0 0 100 100">
      <!-- Background circle -->
      <circle
        class="timer-circle-bg"
        cx="50"
        cy="50"
        r="45"
      />
      <!-- Progress circle -->
      <circle
        class="timer-circle {isDanger ? 'danger' : isWarning ? 'warning' : 'normal'}"
        cx="50"
        cy="50"
        r="45"
        style="stroke-dasharray: {2 * Math.PI * 45}; stroke-dashoffset: {2 * Math.PI * 45 * (1 - percentage / 100)}"
      />
    </svg>
    <div class="timer-text {isDanger ? 'text-red-600' : isWarning ? 'text-yellow-600' : 'text-cyan-600'}">
      {timeLeft}s
    </div>
  </div>
</div>

<style>
  .timer-container {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .timer-wrapper {
    position: relative;
    width: 80px;
    height: 80px;
  }

  .timer-svg {
    width: 100%;
    height: 100%;
    transform: rotate(-90deg);
  }

  .timer-circle-bg {
    fill: none;
    stroke: #e5e7eb;
    stroke-width: 8;
  }

  .timer-circle {
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dashoffset 1s linear, stroke 0.3s ease;
  }

  .timer-circle.normal {
    stroke: #0891b2; /* cyan-600 */
  }

  .timer-circle.warning {
    stroke: #ca8a04; /* yellow-600 */
  }

  .timer-circle.danger {
    stroke: #dc2626; /* red-600 */
  }

  .timer-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1.5rem;
    font-weight: bold;
  }
</style>
