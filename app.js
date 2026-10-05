// ============================================================
// AURA FRONTEND
// ============================================================

const state = {
  token: localStorage.getItem("aura_token"),
  user: null,
  conversationId: null,
  authMode: "login",
  currentAgent: "general",
  currentAgentName: "General Agent"
};


// ============================================================
// DOM HELPER
// ============================================================

const $ = id => document.getElementById(id);


// ============================================================
// API HELPER
// ============================================================

function api(path, options = {}) {

  options.headers = options.headers || {};

  if (state.token) {
    options.headers.Authorization = "Bearer " + state.token;
  }

  return fetch(path, options).then(async response => {

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || "Request failed"
      );
    }

    return data;
  });
}


// ============================================================
// PAGE NAVIGATION
// ============================================================

function showPage(page) {

  ["chat", "knowledge", "memory", "planner"].forEach(p => {

    const element = $(p + "Page");

    if (element) {
      element.classList.toggle(
        "hidden",
        p !== page
      );
    }
  });


  document
    .querySelectorAll(".nav[data-page]")
    .forEach(button => {

      button.classList.toggle(
        "active",
        button.dataset.page === page
      );
    });


  const titles = {
    chat: "AURA Chat",
    knowledge: "Knowledge Base",
    memory: "Long-term Memory",
    planner: "Planner"
  };


  if ($("pageTitle")) {
    $("pageTitle").textContent =
      titles[page] || "AURA";
  }


  if (page === "memory") {
    loadMemories();
  }


  if (page === "planner") {
    loadTasks();
  }
}


// ============================================================
// AUTH VISIBILITY
// ============================================================

function setAuthVisible(visible) {

  if ($("loginPage")) {
    $("loginPage").classList.toggle(
      "hidden",
      !visible
    );
  }


  ["chat", "knowledge", "memory", "planner"]
    .forEach(p => {

      const element = $(p + "Page");

      if (element) {
        element.classList.toggle(
          "hidden",
          visible
        );
      }
    });


  document
    .querySelectorAll(".nav[data-page]")
    .forEach(button => {

      button.classList.remove("active");

    });
}


// ============================================================
// BOOT
// ============================================================

async function boot() {

  if (!state.token) {
    setAuthVisible(true);
    return;
  }


  try {

    state.user = await api("/api/me");


    if ($("userBox")) {
      $("userBox").textContent =
        state.user.name;
    }


    setAuthVisible(false);

    showPage("chat");


  } catch (error) {

    localStorage.removeItem("aura_token");

    state.token = null;

    setAuthVisible(true);
  }
}


// ============================================================
// ADD CHAT MESSAGE
// ============================================================

function addMessage(role, content) {

  const div =
    document.createElement("div");

  div.className =
    "msg " + role;


  div.innerHTML =
    `<div class="role">${role}</div><div></div>`;


  div.lastChild.textContent =
    content;


  if ($("messages")) {

    $("messages").appendChild(div);

    $("messages").scrollTop =
      $("messages").scrollHeight;
  }
}


// ============================================================
// UPDATE AGENT UI
// ============================================================

function updateAgentUI(agent, agentName) {

  // Default values
  agent = agent || "general";

  agentName =
    agentName ||
    "General Agent";


  // Save in application state
  state.currentAgent = agent;

  state.currentAgentName =
    agentName;


  // ----------------------------------------------------------
  // Update dropdown
  // ----------------------------------------------------------

  const agentSelect =
    $("agent");


  if (agentSelect) {

    // Check whether this option actually exists
    const option =
      Array.from(agentSelect.options)
        .find(option =>
          option.value === agent
        );


    if (option) {

      agentSelect.value =
        agent;

    } else {

      console.warn(
        "AURA: Agent option not found:",
        agent
      );
    }
  }


  // ----------------------------------------------------------
  // Update status
  // ----------------------------------------------------------

  if ($("status")) {

    $("status").textContent =
      "Ready • " + agentName;
  }


  // ----------------------------------------------------------
  // Optional agent display element
  // ----------------------------------------------------------

  const possibleElements = [
    "agentName",
    "currentAgent",
    "selectedAgent"
  ];


  possibleElements.forEach(id => {

    const element = $(id);

    if (element) {

      element.textContent =
        agentName;
    }
  });


  // ----------------------------------------------------------
  // Console information
  // ----------------------------------------------------------

  console.log(
    "AURA selected agent:",
    agent
  );

  console.log(
    "AURA selected agent name:",
    agentName
  );
}


// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage() {

  const prompt =
    $("prompt");

  if (!prompt) return;


  const text =
    prompt.value.trim();


  if (!text) {
    return;
  }


  // ----------------------------------------------------------
  // Prepare UI
  // ----------------------------------------------------------

  prompt.value = "";

  addMessage(
    "user",
    text
  );


  if ($("status")) {

    $("status").textContent =
      "AURA is thinking...";
  }


  if ($("sendBtn")) {

    $("sendBtn").disabled =
      true;
  }


  try {

    // --------------------------------------------------------
    // Send request to backend
    // --------------------------------------------------------

    const data =
      await api("/api/chat", {

        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({

          message: text,

          conversation_id:
            state.conversationId,

          // Current UI value is sent,
          // but backend orchestrator chooses
          // the final agent.
          agent:
            $("agent")
              ? $("agent").value
              : "general"
        })
      });


    // --------------------------------------------------------
    // Save conversation
    // --------------------------------------------------------

    state.conversationId =
      data.conversation_id;


    // --------------------------------------------------------
    // IMPORTANT:
    // Read automatically selected agent
    // from backend response.
    // --------------------------------------------------------

    updateAgentUI(
      data.agent,
      data.agent_name
    );


    // --------------------------------------------------------
    // Show AI response
    // --------------------------------------------------------

    addMessage(
      "assistant",
      data.answer
    );


  } catch (error) {

    console.error(
      "AURA CHAT ERROR:",
      error
    );


    addMessage(
      "assistant",
      "Error: " + error.message
    );


    if ($("status")) {

      $("status").textContent =
        "Error";
    }


  } finally {

    if ($("sendBtn")) {

      $("sendBtn").disabled =
        false;
    }
  }
}


// ============================================================
// SEND BUTTON
// ============================================================

if ($("sendBtn")) {

  $("sendBtn").onclick =
    sendMessage;
}


// ============================================================
// ENTER KEY
// ============================================================

if ($("prompt")) {

  $("prompt")
    .addEventListener(
      "keydown",
      event => {

        if (
          event.key === "Enter" &&
          !event.shiftKey
        ) {

          event.preventDefault();

          sendMessage();
        }
      }
    );
}


// ============================================================
// NEW CHAT
// ============================================================

if ($("newChat")) {

  $("newChat").onclick = () => {

    state.conversationId =
      null;


    state.currentAgent =
      "general";


    state.currentAgentName =
      "General Agent";


    // Reset agent dropdown
    if ($("agent")) {

      $("agent").value =
        "general";
    }


    if ($("messages")) {

      $("messages").innerHTML =
        "";
    }


    addMessage(
      "assistant",
      "New conversation started. How can I help?"
    );


    if ($("status")) {

      $("status").textContent =
        "Ready";
    }
  };
}


// ============================================================
// NAVIGATION BUTTONS
// ============================================================

document
  .querySelectorAll(
    ".nav[data-page]"
  )
  .forEach(button => {

    button.onclick = () => {

      showPage(
        button.dataset.page
      );
    };
  });


// ============================================================
// LOGIN TAB
// ============================================================

if ($("loginTab")) {

  $("loginTab").onclick = () => {

    state.authMode =
      "login";


    $("loginTab")
      .classList
      .add("selected");


    $("registerTab")
      .classList
      .remove("selected");


    $("name")
      .classList
      .add("hidden");


    $("authBtn").textContent =
      "Login";
  };
}


// ============================================================
// REGISTER TAB
// ============================================================

if ($("registerTab")) {

  $("registerTab").onclick = () => {

    state.authMode =
      "register";


    $("registerTab")
      .classList
      .add("selected");


    $("loginTab")
      .classList
      .remove("selected");


    $("name")
      .classList
      .remove("hidden");


    $("authBtn").textContent =
      "Create account";
  };
}


// ============================================================
// LOGIN / REGISTER
// ============================================================

if ($("authBtn")) {

  $("authBtn").onclick =
    async () => {

      if ($("authMsg")) {

        $("authMsg").textContent =
          "";
      }


      try {

        const path =
          state.authMode === "login"
            ? "/api/auth/login"
            : "/api/auth/register";


        const body = {

          email:
            $("email")
              .value
              .trim(),

          password:
            $("password")
              .value
        };


        if (
          state.authMode ===
          "register"
        ) {

          body.name =
            $("name")
              .value
              .trim();
        }


        const data =
          await api(
            path,
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body:
                JSON.stringify(body)
            }
          );


        state.token =
          data.token;


        localStorage.setItem(
          "aura_token",
          state.token
        );


        state.user =
          data.user;


        if ($("userBox")) {

          $("userBox").textContent =
            state.user.name;
        }


        setAuthVisible(false);

        showPage("chat");


        addMessage(
          "assistant",
          "Welcome to AURA. Your AI workspace is ready."
        );


      } catch (error) {

        if ($("authMsg")) {

          $("authMsg").textContent =
            error.message;
        }
      }
    };
}


// ============================================================
// LOGOUT
// ============================================================

if ($("logoutBtn")) {

  $("logoutBtn").onclick = () => {

    localStorage.removeItem(
      "aura_token"
    );


    state.token =
      null;


    location.reload();
  };
}


// ============================================================
// PDF UPLOAD
// ============================================================

if ($("uploadBtn")) {

  $("uploadBtn").onclick =
    async () => {

      const file =
        $("pdfFile").files[0];


      if (!file) {

        $("uploadMsg").textContent =
          "Choose a PDF first.";

        return;
      }


      const form =
        new FormData();


      form.append(
        "file",
        file
      );


      $("uploadMsg").textContent =
        "Indexing...";


      try {

        const data =
          await api(
            "/api/documents/upload",
            {
              method: "POST",
              body: form
            }
          );


        $("uploadMsg").textContent =
          `Indexed ${data.chunks} chunks from ${data.filename}.`;


      } catch (error) {

        $("uploadMsg").textContent =
          error.message;
      }
    };
}


// ============================================================
// PDF / KNOWLEDGE QUERY
// ============================================================

if ($("docAskBtn")) {

  $("docAskBtn").onclick =
    async () => {

      const query =
        $("docQuery")
          .value
          .trim();


      if (!query) return;


      $("docResults").textContent =
        "Searching...";


      try {

        const rows =
          await api(
            "/api/documents/query",
            {
              method: "POST",

              headers: {
                "Content-Type":
                  "application/json"
              },

              body:
                JSON.stringify({
                  query: query,
                  top_k: 5
                })
            }
          );


        if (!rows.length) {

          $("docResults").textContent =
            "No matching knowledge found.";

          return;
        }


        $("docResults").innerHTML =
          rows
            .map(row =>

              `<div class="doc-result">
                <small>
                  ${escapeHtml(row.filename)}
                  —
                  page ${row.page}
                  —
                  score ${row.score}
                </small>

                <div>
                  ${escapeHtml(row.text)}
                </div>
              </div>`

            )
            .join("");


      } catch (error) {

        $("docResults").textContent =
          error.message;
      }
    };
}


// ============================================================
// LOAD MEMORIES
// ============================================================

async function loadMemories() {

  try {

    const rows =
      await api(
        "/api/memories"
      );


    $("memoryList").innerHTML =
      rows
        .map(row =>

          `<div class="memory">
            <span>
              ${escapeHtml(row.content)}
            </span>

            <button
              class="secondary"
              onclick="deleteMemory(${row.id})">
              Delete
            </button>
          </div>`

        )
        .join("");


  } catch (error) {

    console.error(
      "Memory loading error:",
      error
    );
  }
}


// ============================================================
// DELETE MEMORY
// ============================================================

window.deleteMemory =
  async id => {

    await api(
      "/api/memories/" + id,
      {
        method: "DELETE"
      }
    );


    loadMemories();
  };


// ============================================================
// ADD MEMORY
// ============================================================

if ($("memoryAdd")) {

  $("memoryAdd").onclick =
    async () => {

      const content =
        $("memoryInput")
          .value
          .trim();


      if (!content) return;


      await api(
        "/api/memories",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({
              content: content
            })
        }
      );


      $("memoryInput").value =
        "";


      loadMemories();
    };
}


// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {

  try {

    const rows =
      await api(
        "/api/tasks"
      );


    $("taskList").innerHTML =
      rows
        .map(row =>

          `<div class="task">

            <div class="task-main">

              <div class="task-title">
                ${escapeHtml(row.title)}
              </div>

              <div class="task-meta">
                ${escapeHtml(row.priority)}
                ·
                ${escapeHtml(row.due_date || "No due date")}
                ·
                ${escapeHtml(row.status)}
              </div>

              <div>
                ${escapeHtml(row.description)}
              </div>

            </div>

            <button
              class="secondary"
              onclick="toggleTask(${row.id}, '${row.status}')">

              ${row.status === "done"
                ? "Undo"
                : "Done"}

            </button>

            <button
              class="secondary"
              onclick="deleteTask(${row.id})">

              Delete

            </button>

          </div>`

        )
        .join("");


  } catch (error) {

    console.error(
      "Task loading error:",
      error
    );
  }
}


// ============================================================
// TOGGLE TASK
// ============================================================

window.toggleTask =
  async (id, status) => {

    await api(
      "/api/tasks/" + id,
      {
        method: "PATCH",

        headers: {
          "Content-Type":
            "application/json"
        },

        body:
          JSON.stringify({
            status:
              status === "done"
                ? "todo"
                : "done"
          })
      }
    );


    loadTasks();
  };


// ============================================================
// DELETE TASK
// ============================================================

window.deleteTask =
  async id => {

    await api(
      "/api/tasks/" + id,
      {
        method: "DELETE"
      }
    );


    loadTasks();
  };


// ============================================================
// ADD TASK
// ============================================================

if ($("taskAdd")) {

  $("taskAdd").onclick =
    async () => {

      const title =
        $("taskTitle")
          .value
          .trim();


      if (!title) return;


      await api(
        "/api/tasks",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body:
            JSON.stringify({

              title: title,

              description:
                $("taskDescription")
                  .value,

              due_date:
                $("taskDue")
                  .value,

              priority:
                $("taskPriority")
                  .value

            })
          }
        );


      $("taskTitle").value =
        "";

      $("taskDescription").value =
        "";

      $("taskDue").value =
        "";


      loadTasks();
    };
}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHtml(value) {

  return String(value)
    .replace(
      /[&<>"']/g,
      character => ({

        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"

      }[character])
    );
}


// ============================================================
// VOICE INPUT
// ============================================================

if ($("micBtn")) {

  $("micBtn").onclick = () => {

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

      alert(
        "Voice input is not supported by this browser."
      );

      return;
    }


    const recognition =
      new SpeechRecognition();


    recognition.lang =
      "en-IN";


    recognition.onresult =
      event => {

        const transcript =
          event
            .results[0][0]
            .transcript;


        $("prompt").value +=
          (
            $("prompt").value
              ? " "
              : ""
          ) + transcript;
      };


    recognition.start();
  };
}


// ============================================================
// START AURA
// ============================================================

boot();