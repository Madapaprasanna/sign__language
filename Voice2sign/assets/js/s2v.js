// Sign-to-Voice WebSocket Integration
let mediaStream;
let websocket;
const FPS = 15;
let frameInterval;
let currentLanguage = "en";
let lastServerFrameTime = 0;

const translations = {
  ru: {
    startWebcam: "Включить камеру",
    stopWebcam: "Выключить камеру",
    startStream: "Запустить стрим",
    stopStream: "Остановить стрим",
    webcamError: "Ошибка камеры",
    wsConnected: "Сервер подключен",
    wsClosed: "Сервер отключен",
    wsError: "Ошибка подключения",
    correctGesture: "Detected: {text}",
  },
  en: {
    startWebcam: "Enable Camera",
    stopWebcam: "Disable Camera",
    startStream: "Start Stream",
    stopStream: "Stop Stream",
    webcamError: "Camera Error",
    wsConnected: "Server Connected",
    wsClosed: "Server Closed",
    wsError: "Connection Error",
    correctGesture: "Detected: {text}",
  },
};

function speak(text) {
  if ("speechSynthesis" in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentLanguage === "ru" ? "ru-RU" : "en-US";
    window.speechSynthesis.speak(utterance);
  }
}

function showMessage(textKey, type = "success", data = {}) {
  let text = translations[currentLanguage][textKey] || textKey;
  text = text.replace("{text}", data.text || "");

  const container = document.getElementById("messageContainer");
  if (!container) return;

  const message = document.createElement("div");
  message.className = `message ${type}`;
  message.textContent = text;
  container.appendChild(message);

  setTimeout(() => message.classList.add("show"), 10);
  setTimeout(() => {
    message.classList.remove("show");
    setTimeout(() => message.remove(), 300);
  }, 3000);

  if (type === "success" && data.text) {
    document.getElementById("detectedText").textContent = data.text;
  }
}

function applyTranslations() {
  const t = translations[currentLanguage];
  document.getElementById("startWebcamButton").innerHTML =
    `<i class="fas fa-play"></i> ${t.startWebcam}`;
  document.getElementById("stopWebcamButton").innerHTML =
    `<i class="fas fa-stop"></i> ${t.stopWebcam}`;
  document.getElementById("startStreamButton").innerHTML =
    `<i class="fas fa-rocket"></i> ${t.startStream}`;
  document.getElementById("stopStreamButton").innerHTML =
    `<i class="fas fa-pause"></i> ${t.stopStream}`;
}

function changeLanguage(lang) {
  if (currentLanguage === lang) return;
  currentLanguage = lang;
  document.getElementById("langRu").classList.toggle("active", lang === "ru");
  document.getElementById("langEn").classList.toggle("active", lang === "en");
  applyTranslations();
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({ type: "LANGUAGE", lang: lang }));
  }
}

function startWebcam() {
  navigator.mediaDevices
    .getUserMedia({ video: { width: 640, height: 480 } })
    .then((stream) => {
      const video = document.getElementById("webcam");
      video.srcObject = stream;
      mediaStream = stream;
      document.getElementById("startWebcamButton").classList.add("hidden");
      document.getElementById("stopWebcamButton").classList.remove("hidden");
      document.getElementById("streamControls").classList.remove("hidden");
    })
    .catch((error) => {
      console.error(error);
      showMessage("webcamError", "error");
    });
}

function stopWebcam() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    document.getElementById("webcam").srcObject = null;
    document.getElementById("startWebcamButton").classList.remove("hidden");
    document.getElementById("stopWebcamButton").classList.add("hidden");
    document.getElementById("streamControls").classList.add("hidden");
    stopStream();
  }
}

function startStream() {
  document.getElementById("startStreamButton").classList.add("hidden");
  document.getElementById("stopStreamButton").classList.remove("hidden");
  document.getElementById("streamStatus").textContent = "Connecting...";
  document.getElementById("streamStatus").className = "status-badge connecting";

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsHost =
    window.location.hostname === "localhost"
      ? "localhost:3005"
      : "your-backend-url.railway.app";
  websocket = new WebSocket(`${protocol}//${wsHost}/`);

  websocket.onopen = () => {
    document.getElementById("streamStatus").textContent = "Live";
    document.getElementById("streamStatus").className = "status-badge live";
    showMessage("wsConnected", "success");
    websocket.send(JSON.stringify({ type: "LANGUAGE", lang: currentLanguage }));
    sendVideoStream();
  };

  websocket.onclose = () => {
    document.getElementById("streamStatus").textContent = "Offline";
    document.getElementById("streamStatus").className = "status-badge offline";
    showMessage("wsClosed", "error");
    stopStream();
  };

  websocket.onerror = () => {
    showMessage("wsError", "error");
  };

  websocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.image) {
        lastServerFrameTime = Date.now();
        const canvas = document.getElementById("feedbackCanvas");
        const ctx = canvas.getContext("2d");
        const img = new Image();
        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx.drawImage(img, 0, 0);
        };
        img.src = "data:image/jpeg;base64," + data.image;
      }
      if (data.type === "WORD") {
        document.getElementById("detectedText").textContent = data.text;
      }
    } catch (e) {
      console.error(e);
    }
  };
}

function stopStream() {
  document.getElementById("stopStreamButton").classList.add("hidden");
  document.getElementById("startStreamButton").classList.remove("hidden");
  if (frameInterval) clearInterval(frameInterval);
  if (websocket) websocket.close();
}

function sendVideoStream() {
  const video = document.getElementById("webcam");
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.width = 300;
  canvas.height = 225;

  frameInterval = setInterval(() => {
    const feedbackCanvas = document.getElementById("feedbackCanvas");
    const fCtx = feedbackCanvas.getContext("2d");

    if (
      video.readyState === video.HAVE_ENOUGH_DATA &&
      (!lastServerFrameTime || Date.now() - lastServerFrameTime > 500)
    ) {
      feedbackCanvas.width = video.videoWidth;
      feedbackCanvas.height = video.videoHeight;
      fCtx.drawImage(video, 0, 0);
    }

    if (
      websocket &&
      websocket.readyState === WebSocket.OPEN &&
      video.readyState === video.HAVE_ENOUGH_DATA
    ) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL("image/jpeg", 0.6);
      websocket.send(JSON.stringify({ type: "IMAGE", image: imageData }));
    }
  }, 1000 / FPS);
}

document.addEventListener("DOMContentLoaded", () => {
  document
    .getElementById("startWebcamButton")
    .addEventListener("click", startWebcam);
  document
    .getElementById("stopWebcamButton")
    .addEventListener("click", stopWebcam);
  document
    .getElementById("startStreamButton")
    .addEventListener("click", startStream);
  document
    .getElementById("stopStreamButton")
    .addEventListener("click", stopStream);

  const voiceBtn = document.getElementById("voiceBtn");
  if (voiceBtn) {
    voiceBtn.addEventListener("click", () => {
      const text = document.getElementById("detectedText").textContent;
      if (text && text !== "Waiting for sign...") {
        speak(text);
      }
    });
  }
  applyTranslations();
});
