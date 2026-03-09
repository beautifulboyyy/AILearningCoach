<template>
  <div class="chat-container">
    <div class="messages" ref="messageBox">
      <div v-for="(msg, index) in messages" :key="index" :class="['message', msg.role]">
        <div class="content">{{ msg.content }}</div>
        <div v-if="msg.references" class="references">
          <h4>参考来源:</h4>
          <ul>
            <li v-for="(ref, i) in msg.references" :key="i">
              {{ ref.metadata.source }} - P{{ ref.metadata.page }}
            </li>
          </ul>
        </div>
      </div>
    </div>
    <div class="input-area">
      <input v-model="userInput" @keyup.enter="send" placeholder="向教练提问..." />
      <button @click="send" :disabled="loading">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { chatStream } from '../api/ai';

const messages = ref([]);
const userInput = ref('');
const loading = ref(false);
const messageBox = ref(null);

const send = async () => {
  if (!userInput.value || loading.value) return;

  const userMsg = { role: 'user', content: userInput.value };
  messages.value.push(userMsg);
  
  const aiMsg = { role: 'assistant', content: '', references: [] };
  messages.value.push(aiMsg);
  
  const text = userInput.value;
  userInput.value = '';
  loading.value = true;

  await chatStream(
    text,
    (content) => {
      aiMsg.content += content;
      scrollToBottom();
    },
    (refs) => {
      aiMsg.references = refs;
    }
  );

  loading.value = false;
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messageBox.value) {
      messageBox.value.scrollTop = messageBox.value.scrollHeight;
    }
  });
};
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: 100%; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.message { margin-bottom: 20px; }
.message.user { text-align: right; }
.message.assistant { text-align: left; }
.content { padding: 10px; border-radius: 8px; background: #f0f0f0; display: inline-block; }
.message.user .content { background: #007bff; color: white; }
.input-area { padding: 20px; border-top: 1px solid #ddd; }
</style>
