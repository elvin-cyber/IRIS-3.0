(() => {
  const orb = document.getElementById("orb");
  const coreState = document.getElementById("coreState");
  const micBtn = document.getElementById("micBtn");
  const micHint = document.getElementById("micHint");
  const transcript = document.getElementById("transcript");
  const composer = document.getElementById("composer");
  const textInput = document.getElementById("textInput");
  const waveform = document.getElementById("waveform");
  const ticksHost = document.getElementById("ticks");
  const ollamaStatus = document.getElementById("ollamaStatus");

  let assistantName = "IRIS";
  let waveformTimer = null;

  // ---------- Build the dial ticks around the ring ----------
  const TICK_COUNT = 36;
  for (let i = 0; i < TICK_COUNT; i++) {
    const tick = document.createElement("span");
    tick.style.transform = `rotate(${(360 / TICK_COUNT) * i}deg)`;
    ticksHost.appendChild(tick);
  }

  // ---------- Build the waveform bars ----------
  const BAR_COUNT = 20;
  const bars = [];
  for (let i = 0; i < BAR_COUNT; i++) {
    const bar = document.createElement("span");
    waveform.appendChild(bar);
    bars.push(bar);
  }

  function setState(state) {
    orb.dataset.state = state;
    coreState.textContent = state.toUpperCase();
  }

  function startWaveform() {
    stopWaveform();
    waveformTimer = setInterval(() => {
      bars.forEach((bar) => {
        const h = 4 + Math.random() * 24;
        bar.style.height = `${h}px`;
      });
    }, 90);
  }

  function stopWaveform() {
    if (waveformTimer) clearInterval(waveformTimer);
    waveformTimer = null;
    bars.forEach((bar) => (bar.style.height = "4px"));
  }

  function addBubble(role, text) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    const label = document.createElement("span");
    label.className = "role";
    label.textContent = role === "iris" ? assistantName : role === "user" ? "YOU" : "SYSTEM";
    const body = document.createElement("div");
    body.textContent = text;
    bubble.appendChild(label);
    bubble.appendChild(body);
    transcript.appendChild(bubble);
    transcript.scrollTop = transcript.scrollHeight;
  }

  // ---------- Backend calls ----------
  async function fetchGreeting() {
    try {
      const res = await fetch("/api/greeting");
      const data = await res.json();
      assistantName = data.assistant_name || "IRIS";
      const greetingText = `Hello ${data.user_name}! How can I help you?`;
      addBubble("iris", greetingText);
      speak(greetingText);
    } catch (err) {
      addBubble("system", "Could not reach the IRIS server.");
    }
  }

  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      const online = data.ollama === "online";
      ollamaStatus.className = `status-badge ${online ? "online" : "offline"}`;
      ollamaStatus.querySelector(".status-text").textContent = online
        ? "MODEL ONLINE"
        : "MODEL OFFLINE";
    } catch (err) {
      ollamaStatus.className = "status-badge offline";
      ollamaStatus.querySelector(".status-text").textContent = "SERVER OFFLINE";
    }
  }

  async function sendMessage(message) {
    if (!message) return;
    addBubble("user", message);
    setState("thinking");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      if (data.error) {
        addBubble("system", data.error);
        setState("error");
        return;
      }
      addBubble("iris", data.reply);
      speak(data.reply);
    } catch (err) {
      addBubble("system", "Lost connection to the IRIS server.");
      setState("error");
    }
  }

  // ---------- Text-to-speech ----------
  function speak(text) {
    if (!("speechSynthesis" in window)) {
      setState("idle");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.02;
    utterance.pitch = 0.95;
    utterance.onstart = () => {
      setState("speaking");
      startWaveform();
    };
    utterance.onend = () => {
      stopWaveform();
      setState("idle");
    };
    utterance.onerror = () => {
      stopWaveform();
      setState("idle");
    };
    window.speechSynthesis.speak(utterance);
  }

  // ---------- Speech-to-text (Web Speech API, Chrome/Edge only) ----------
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognizer = null;
  let listening = false;

  if (SpeechRecognition) {
    recognizer = new SpeechRecognition();
    recognizer.continuous = false;
    recognizer.interimResults = false;
    recognizer.lang = "en-US";

    recognizer.onstart = () => {
      listening = true;
      micBtn.classList.add("active");
      setState("listening");
      micHint.textContent = "Listening...";
    };

    recognizer.onresult = (event) => {
      const said = event.results[0][0].transcript;
      sendMessage(said);
    };

    recognizer.onerror = (event) => {
      addBubble("system", `Mic error: ${event.error}`);
      setState("idle");
    };

    recognizer.onend = () => {
      listening = false;
      micBtn.classList.remove("active");
      micHint.textContent = "Tap the mic and speak, or type below";
      if (orb.dataset.state === "listening") setState("idle");
    };
  } else {
    micBtn.disabled = true;
    micHint.textContent = "Voice input needs Chrome or Edge — type below instead";
  }

  micBtn.addEventListener("click", () => {
    if (!recognizer) return;
    if (listening) {
      recognizer.stop();
      return;
    }
    window.speechSynthesis.cancel();
    stopWaveform();
    recognizer.start();
  });

  composer.addEventListener("submit", (e) => {
    e.preventDefault();
    const value = textInput.value.trim();
    if (!value) return;
    textInput.value = "";
    sendMessage(value);
  });

  setState("idle");
  fetchGreeting();
  checkHealth();
  setInterval(checkHealth, 15000);
})();
