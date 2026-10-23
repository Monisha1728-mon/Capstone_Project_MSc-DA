(() => {
  const box = document.getElementById("chatMessages");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const clearButton = document.getElementById("clearChat");
  if (!box || !form || !input) return;

  const historyKey = "at-risk-chat-history-v2";
  const now = () =>
    new Intl.DateTimeFormat([], { hour: "numeric", minute: "2-digit" }).format(
      new Date(),
    );
  const answers = [
    {
      pattern: /hello|hi|hey|good morning|good evening/i,
      reply:
        "Hi! I’m glad you came by. Tell me what you need help with and we’ll take it slowly together. You can ask about the feedback form, your device, training, repair, cost or a reviewed result.",
    },
    {
      pattern: /fill|form|submit|feedback question|answer/i,
      reply:
        "Of course. Start with the first question and answer from your real experience, not what you think the system wants to hear. If a question is unclear, tell me its wording and I’ll explain it in simple language. You can also pause and return later.",
    },
    {
      pattern: /first question|device received|receive.*device/i,
      reply:
        "The first question checks whether you actually received an assistive technology device. Choose Yes only if a device was provided to you. If you never received one, choose No; that helps the administrator understand your situation correctly.",
    },
    {
      pattern: /damaged|broken|condition|repair|replace/i,
      reply:
        "For device condition, describe what is happening now: does it work, feel uncomfortable, need repair, or stop you using it? If it is damaged or broken, choose that honestly. In the details, mention what is wrong and whether you need repair, replacement or a fit check.",
    },
    {
      pattern: /training|learn|teach|orientation|maintenance|clean/i,
      reply:
        "For training and maintenance, think about whether someone showed you how to use, clean, store and look after the device. If nobody trained you or you still feel unsure, say so. That is useful information, not a wrong answer.",
    },
    {
      pattern: /cost|money|afford|insurance|fund|travel/i,
      reply:
        "Cost can include the device price, repair charges, transport, batteries or a lack of insurance support. Tell the truth about what makes access difficult. After review, you can ask about subsidies, insurance, refurbished devices or lower-cost alternatives.",
    },
    {
      pattern: /result|risk|score|reviewed|predict|percentage/i,
      reply:
        "A reviewed risk result is a support signal, not a diagnosis. Open the entry from Your History to see the risk band, the factors that influenced it and the suggested next step. If it says High or Medium, it means the support team may want to follow up earlier.",
    },
    {
      pattern: /next|what.*do|action|follow|support/i,
      reply:
        "Your next step depends on the barrier. For damage, request repair or replacement. For missing training, ask for a demonstration. For poor fit, request a fit review. For cost, ask about funding or alternatives. You can also contact support directly from your workspace.",
    },
    {
      pattern: /ask|question.*team|care team|doctor|coordinator/i,
      reply:
        "You could ask: Is this device suitable for my daily needs? Who do I contact if it breaks? Can I receive more training? Is there a repair or replacement plan? Are there subsidy, insurance or low-cost options? What should I do if the device is uncomfortable?",
    },
    {
      pattern: /privacy|safe|secure|data/i,
      reply:
        "Your feedback is stored in your AT-RISK workspace so the administrator can review it. Share only information relevant to your device and support experience. This assistant gives guidance and does not replace a clinician or support professional.",
    },
  ];

  const escapeHtml = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;",
        })[c],
    );
  const save = (text, author) => {
    const items = JSON.parse(localStorage.getItem(historyKey) || "[]");
    items.push({ text, author, time: now() });
    localStorage.setItem(historyKey, JSON.stringify(items.slice(-16)));
  };
  const addMessage = (text, author, shouldSave = true, time = now()) => {
    const row = document.createElement("div");
    row.className = `assistant-message ${author === "user" ? "assistant-user-message" : "assistant-bot-message"}`;
    row.innerHTML =
      author === "user"
        ? `<div class="assistant-message-content"><p>${escapeHtml(text)}</p><small>${time}</small></div>`
        : `<span class="message-avatar"><i class="fa-solid fa-sparkles"></i></span><div class="assistant-message-content"><p>${text}</p><small>${time}</small></div>`;
    box.appendChild(row);
    box.scrollTop = box.scrollHeight;
    if (shouldSave) save(text, author);
  };
  const replyFor = (question) => {
    const match = answers.find((item) => item.pattern.test(question));
    return match
      ? match.reply
      : "I can help with the feedback form, device condition, training, maintenance, cost, repair, privacy, reviewed risk results or questions for your support team. Tell me a little more about what you are trying to do.";
  };
  const send = (question) => {
    const text = question.trim();
    if (!text) return;
    addMessage(text, "user");
    const typing = document.createElement("div");
    typing.className = "assistant-typing";
    typing.innerHTML =
      "<span></span><span></span><span></span><em>Thinking about that...</em>";
    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;
    window.setTimeout(() => {
      typing.remove();
      addMessage(replyFor(text), "bot");
    }, 700);
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    send(input.value);
    input.value = "";
    input.style.height = "auto";
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  });
  document
    .querySelectorAll("[data-question]")
    .forEach((button) =>
      button.addEventListener("click", () => send(button.dataset.question)),
    );
  clearButton?.addEventListener("click", () => {
    localStorage.removeItem(historyKey);
    box.innerHTML = `<div class="assistant-welcome"><span class="message-avatar"><i class="fa-solid fa-sparkles"></i></span><div><strong>New conversation started.</strong><p>What would you like help with?</p><span class="welcome-time">${now()}</span></div></div>`;
  });
  try {
    JSON.parse(localStorage.getItem(historyKey) || "[]")
      .slice(-10)
      .forEach((item) =>
        addMessage(item.text, item.author, false, item.time || now()),
      );
  } catch {
    localStorage.removeItem(historyKey);
  }
})();
