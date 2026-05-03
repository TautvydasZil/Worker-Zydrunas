<template>
  <Teleport to="body">
    <div v-if="visible" class="overlay" @mousedown.self="handleCancel">
      <div class="dialog" role="dialog" aria-modal="true">
        <p class="message">{{ message }}</p>
        <div class="actions">
          <button class="btn-cancel" @click="handleCancel">Atšaukti</button>
          <button class="btn-confirm" @click="handleConfirm">Patvirtinti</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
const message = ref('')
let resolve = null

function show(msg) {
  message.value = msg
  visible.value = true
  return new Promise(r => { resolve = r })
}

function handleConfirm() {
  visible.value = false
  resolve?.(true)
}

function handleCancel() {
  visible.value = false
  resolve?.(false)
}

function onKeydown(e) {
  if (e.key === 'Escape' && visible.value) handleCancel()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

defineExpose({ show })
</script>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 24px;
  backdrop-filter: blur(2px);
}

.dialog {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 28px 28px 22px;
  width: 100%;
  max-width: 360px;
  box-shadow: var(--shadow-lg);
}

.message {
  font-size: 15px;
  color: var(--text-h);
  font-weight: 500;
  margin: 0 0 22px;
  line-height: 1.5;
}

.actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.btn-cancel {
  padding: 8px 18px;
  background: transparent;
  border: 1.5px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.15s, color 0.15s;
}

.btn-cancel:hover { border-color: var(--text-h); color: var(--text-h); }

.btn-confirm {
  padding: 8px 18px;
  background: var(--danger);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: opacity 0.15s;
}

.btn-confirm:hover { opacity: 0.88; }
</style>
