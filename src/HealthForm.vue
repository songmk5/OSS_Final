<template>
  <div class="app-container">
    <!-- 사이드바 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>건강 상담</h2>
      </div>

      <div class="nav-menu">
        <div
            class="nav-item"
            :class="{ active: activeMenu === 'chat' }"
            @click="setActiveMenu('chat')"
        >
          💬 AI 상담
        </div>
        <div
            class="nav-item"
            :class="{ active: activeMenu === 'history' }"
            @click="setActiveMenu('history')"
        >
          📋 내 상담 기록
        </div>
        <div
            class="nav-item"
            :class="{ active: activeMenu === 'settings' }"
            @click="setActiveMenu('settings')"
        >
          ⚙️ 설정
        </div>
      </div>
    </div>

    <!-- 메인 컨텐츠 -->
    <div class="main-content">
      <!-- 헤더 -->
      <div class="chat-header">
        <div class="chat-title">건강기능식품 AI 상담</div>
      </div>

      <!-- 알림 영역 -->
      <div class="notification-area">
        <div class="notification-text">
          🏥 본 서비스는 건강기능식품 정보 제공 목적이며, 의학적 진단이나 치료를 대체하지 않습니다.
        </div>
      </div>

      <!-- 채팅 영역 -->
      <div v-if="activeMenu === 'chat'" class="chat-area">
        <!-- 환영 메시지 -->
        <div class="welcome-message" :style="{ fontSize: fontSize + 'px' }">안녕하세요! 👋</div>
        <div class="welcome-subtitle" :style="{ fontSize: (fontSize - 2) + 'px' }">
          건강 관련 고민이나 증상을 말씀해 주세요.<br>
          맞춤형 건강기능식품을 추천해드릴게요!
        </div>

        <!-- 실제 채팅 메시지 -->
        <div
            v-for="msg in chatMessages"
            :key="msg.id"
            :class="['message-bubble', msg.type]"
        >
          <div
              class="message-content"
              :style="{ fontSize: fontSize + 'px' }"
              v-html="msg.content.replace(/\n/g, '<br>')"
          ></div>
          <div class="message-time">{{ msg.timestamp }}</div>
        </div>
      </div>

      <!-- 상담 기록 영역 -->
      <div v-else-if="activeMenu === 'history'" class="history-area">
        <div class="history-container">
          <h3 class="history-title">내 상담 기록</h3>

          <!-- 로딩 상태 -->
          <div v-if="isLoadingHistory" class="loading-history">
            <div class="loading-icon">⏳</div>
            <div class="loading-text">상담 기록을 불러오는 중...</div>
          </div>

          <div v-else-if="consultationHistory.length === 0" class="no-history">
            <div class="no-history-icon">📝</div>
            <div class="no-history-text">아직 상담 기록이 없습니다</div>
            <div class="no-history-subtitle">AI 상담을 시작해보세요!</div>
          </div>

          <div v-else class="history-list">
            <div
                v-for="record in consultationHistory"
                :key="record.id"
                class="history-item"
            >
              <div class="history-header">
                <div class="history-date-time">
                  <span class="history-date">{{ record.date }}</span>
                  <span class="history-time">{{ record.time }}</span>
                </div>
                <div class="history-menu">
                  <button
                      class="menu-dots"
                      @click="toggleDropdown(record.id)"
                  >
                    ⋯
                  </button>
                  <div
                      v-if="showDropdown === record.id"
                      class="dropdown-menu"
                  >
                    <button
                        class="dropdown-item delete"
                        @click="deleteRecord(record.id)"
                    >
                      🗑️ 삭제
                    </button>
                  </div>
                </div>
              </div>

              <div class="history-content">
                <div class="history-summary">{{ record.summary }}</div>
                <div class="history-messages">
                  <div class="user-message">
                    <strong>질문:</strong> {{ record.userMessage }}
                  </div>
                  <div class="ai-message">
                    <strong>답변:</strong> {{ record.aiResponse }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 기타 메뉴 (설정) -->
      <div v-else-if="activeMenu === 'settings'" class="settings-area">
        <div class="settings-container">
          <h3 class="settings-title">설정</h3>

          <!-- 글꼴 크기 설정 -->
          <div class="setting-item">
            <label class="setting-label">채팅 글꼴 크기</label>
            <div class="font-size-controls">
              <input
                  type="range"
                  min="12"
                  max="24"
                  v-model="fontSize"
                  class="font-size-slider"
              >
              <span class="font-size-value">{{ fontSize }}px</span>
            </div>
            <div class="font-preview" :style="{ fontSize: fontSize + 'px' }">
              미리보기: 안녕하세요! 👋
            </div>
          </div>

        </div>
      </div>

      <!-- 기타 메뉴 -->
      <div v-else class="other-menu-area">
        <div class="coming-soon">
          <div class="coming-soon-icon">🚧</div>
          <div class="coming-soon-text">{{ getMenuTitle() }}</div>
          <div class="coming-soon-subtitle">곧 서비스될 예정입니다.</div>
        </div>
      </div>

      <!-- 입력 영역 -->
      <div class="input-area">
        <div class="input-container">
          <input
              type="text"
              class="chat-input"
              placeholder="예: 요새 좀 피곤한 것 같아요..."
              v-model="currentMessage"
              @keypress="handleKeyPress"
              :disabled="isSending"
          >
          <button class="send-btn" @click="sendMessage" :disabled="isSending">
            {{ isSending ? '⏳' : '▶' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      activeMenu: 'chat',
      currentMessage: '',
      chatMessages: [],
      fontSize: 16,
      consultationHistory: [],
      showDropdown: null,
      isLoadingHistory: false,
      isSending: false
    }
  },
  async mounted() {
    // 앱 시작 시 상담 기록 로드
    await this.loadConsultationHistory();
  },
  methods: {
    setActiveMenu(menu) {
      this.activeMenu = menu;
      // 상담 기록 메뉴로 이동할 때마다 새로고침
      if (menu === 'history') {
        this.loadConsultationHistory();
      }
    },

    // 상담 기록을 DB에서 불러오기
    async loadConsultationHistory() {
      this.isLoadingHistory = true;
      try {
        const response = await fetch("http://localhost:8000/consultations");
        if (response.ok) {
          const data = await response.json();
          this.consultationHistory = data;
        } else {
          console.error("상담 기록 로드 실패:", response.status);
        }
      } catch (error) {
        console.error("상담 기록 로드 중 오류:", error);
      } finally {
        this.isLoadingHistory = false;
      }
    },

    handleKeyPress(event) {
      if (event.key === 'Enter' && !this.isSending) {
        this.sendMessage();
      }
    },

    async sendMessage() {
      const message = this.currentMessage.trim();
      if (!message || this.isSending) return;

      this.isSending = true;

      const timestamp = new Date().toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
      });

      const msgId = Date.now();

      // 사용자 메시지를 chatMessages에 추가
      this.chatMessages.push({
        id: msgId,
        type: 'user',
        content: message,
        timestamp: timestamp
      });

      const userMessage = this.currentMessage;
      this.currentMessage = '';

      try {
        const response = await fetch("http://localhost:8000/consult", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: userMessage })
        });

        if (!response.ok) {
          throw new Error(`서버 오류: ${response.status}`);
        }

        const data = await response.json();
        let finalMessage = '';

        if (data.result) {
          finalMessage = data.result;
        } else {
          const summary = data.prescription;
          const productList = data.products.map(p => {
            const name = p.name;
            const desc = p.desc
                .replace(/ - /g, '\n  - ')
                .replace(/①/g, '\n  ①')
                .replace(/②/g, '\n  ②')
                .replace(/③/g, '\n  ③')
                .replace(/④/g, '\n  ④');

            return `● ${name}\n${desc}`;
          }).join('\n\n');
          finalMessage = summary + '\n\n' + productList;
        }

        // AI 응답을 chatMessages에 추가
        this.chatMessages.push({
          id: msgId + 1,
          type: 'ai',
          content: finalMessage,
          timestamp: new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
          })
        });

        // 상담 기록 새로고침 (DB에서 최신 데이터 가져오기)
        await this.loadConsultationHistory();

      } catch (err) {
        console.error("메시지 전송 실패:", err);
        this.chatMessages.push({
          id: msgId + 2,
          type: 'ai',
          content: '⚠️ 서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
          timestamp: new Date().toLocaleTimeString('ko-KR', {
            hour: '2-digit',
            minute: '2-digit'
          })
        });
      } finally {
        this.isSending = false;
      }
    },

    toggleDropdown(recordId) {
      this.showDropdown = this.showDropdown === recordId ? null : recordId;
    },

    // 상담 기록 삭제
    async deleteRecord(recordId) {
      try {
        const response = await fetch(`http://localhost:8000/consultations/${recordId}`, {
          method: "DELETE"
        });

        if (response.ok) {
          // 로컬 상태에서도 제거
          this.consultationHistory = this.consultationHistory.filter(
              record => record.id !== recordId
          );
          this.showDropdown = null;
        } else {
          console.error("삭제 실패:", response.status);
          alert("삭제 중 오류가 발생했습니다.");
        }
      } catch (error) {
        console.error("삭제 중 오류:", error);
        alert("삭제 중 오류가 발생했습니다.");
      }
    },

    getMenuTitle() {
      return this.activeMenu === 'history' ? '상담 기록' : '기타 메뉴';
    }
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.message-bubble {
  margin-top: 20px;
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 16px;
  word-break: break-word;
  position: relative;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.message-bubble.user {
  background-color: #e3f2fd;
  align-self: flex-end;
  color: #1565c0;
  margin-left: auto;
  border-top-right-radius: 0;
}

.message-bubble.ai {
  background-color: #f3e5f5;
  align-self: flex-start;
  color: #7b1fa2;
  margin-right: auto;
  border-top-left-radius: 0;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
  text-align: right;
}

.app-container {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  height: 100vh;
  display: flex;
  margin: 0;
  padding: 0;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* 사이드바 (고정) */
.sidebar {
  width: 280px;
  min-width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0,0,0,0.1);
  height: 100vh;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  text-align: center;
}

.nav-menu {
  flex: 1;
  padding: 20px 0;
}

.nav-item {
  padding: 15px 25px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
  color: #333;
}

.nav-item:hover {
  background: #f8f9fa;
}

.nav-item.active {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
}

/* 메인 컨텐츠 영역 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  position: relative;
  height: 100vh;
  overflow: hidden;
}

.chat-header {
  padding: 20px;
  background: #2196f3;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  flex-shrink: 0;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
}

/* 알림 영역 */
.notification-area {
  background: linear-gradient(135deg, #ffd54f 0%, #ffb300 100%);
  padding: 20px;
  margin: 20px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(255, 179, 0, 0.3);
  flex-shrink: 0;
}

.notification-text {
  color: #333;
  font-weight: 500;
  line-height: 1.4;
}

/* 채팅 영역 - 흰색 배경으로 변경 */
.chat-area {
  flex: 1;
  background: white;
  margin: 20px;
  border-radius: 24px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid #e0e0e0;
  min-height: 200px;
  overflow-y: auto;
}

.welcome-message {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 15px;
}

.welcome-subtitle {
  color: #666;
  font-size: 16px;
  text-align: center;
  line-height: 1.5;
}

/* 입력 영역 */
.input-area {
  padding: 20px;
  border-top: 1px solid #e0e0e0;
  background: white;
  flex-shrink: 0;
}

.input-container {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chat-input {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.chat-input:focus {
  border-color: #2196f3;
}

.chat-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-btn {
  width: 50px;
  height: 50px;
  background: #2196f3;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  transition: background 0.2s;
}

.send-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

/* 설정 영역 */
.settings-area {
  flex: 1;
  background: white;
  margin: 20px;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid #e0e0e0;
  min-height: 200px;
  overflow-y: auto;
}

.settings-container {
  max-width: 600px;
  margin: 0 auto;
}

.settings-title {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 30px;
  text-align: center;
}

.setting-item {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  display: block;
  color: #333;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 10px;
}

.font-size-controls {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.font-size-slider {
  flex: 1;
  height: 6px;
  background: #e0e0e0;
  border-radius: 3px;
  outline: none;
  appearance: none;
}

.font-size-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  background: #2196f3;
  border-radius: 50%;
  cursor: pointer;
}

.font-size-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: #2196f3;
  border-radius: 50%;
  cursor: pointer;
  border: none;
}

.font-size-value {
  color: #666;
  font-size: 14px;
  min-width: 40px;
  text-align: center;
}

.font-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  color: #333;
  text-align: center;
}

/* 기타 메뉴 영역 */
.other-menu-area {
  flex: 1;
  background: white;
  margin: 20px;
  border-radius: 24px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid #e0e0e0;
  min-height: 200px;
}

.coming-soon {
  text-align: center;
}

.coming-soon-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.coming-soon-text {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 10px;
}

/* 상담 기록 영역 */
.history-area {
  flex: 1;
  background: white;
  margin: 20px;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid #e0e0e0;
  min-height: 200px;
  overflow-y: auto;
}

.history-container {
  max-width: 800px;
  margin: 0 auto;
}

.history-title {
  color: #333;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 30px;
  text-align: center;
}

.loading-history {
  text-align: center;
  padding: 60px 20px;
}

.loading-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.loading-text {
  color: #666;
  font-size: 16px;
}

.no-history {
  text-align: center;
  padding: 60px 20px;
}

.no-history-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.no-history-text {
  color: #333;
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 10px;
}

.no-history-subtitle {
  color: #666;
  font-size: 14px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-item {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #2196f3;
  transition: box-shadow 0.2s;
}

.history-item:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.history-date-time {
  display: flex;
  gap: 10px;
  align-items: center;
}

.history-date {
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.history-time {
  color: #666;
  font-size: 12px;
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 10px;
}

.history-menu {
  position: relative;
}

.menu-dots {
  background: none;
  border: none;
  color: #666;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  transition: background 0.2s;
}

.menu-dots:hover {
  background: #e0e0e0;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 10;
  min-width: 120px;
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 10px 15px;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 14px;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.dropdown-item.delete {
  color: #e53e3e;
}

.dropdown-item.delete:hover {
  background: #fee;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.history-summary {
  color: #333;
  font-weight: 600;
  font-size: 16px;
}

.history-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-message, .ai-message {
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.4;
}

.user-message {
  background: #e3f2fd;
  color: #1565c0;
}

.ai-message {
  background: #f3e5f5;
  color: #7b1fa2;
}

.user-message strong, .ai-message strong {
  display: block;
  margin-bottom: 5px;
}

/* 모바일 반응형 */
@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    min-width: 100%;
    height: auto;
  }

  .main-content {
    height: calc(100vh - 150px);
  }

  .chat-area {
    margin: 10px;
    border-radius: 20px;
    min-height: 150px;
    padding: 20px;
  }

  .notification-area {
    margin: 10px;
    border-radius: 12px;
    padding: 15px;
  }

  .input-area {
    padding: 15px;
  }
}
</style>