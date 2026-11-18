// The Gym Log UI: static files that fetch JSON from the two services.
// The page to show comes from the URL after "#", e.g. #/workouts/3 or #/records/Squat.

const WORKOUTS = window.GYMLOG_CONFIG.workoutsUrl;
const RECORDS = window.GYMLOG_CONFIG.recordsUrl;
const page = document.getElementById("page");

// --- talking to the services ---

// Call a service and return {status, body}. If the service can't be reached at all,
// fetch throws; we turn that into status 0 and a readable error instead of crashing.
async function api(baseUrl, path, method = "GET", data = undefined) {
  const options = { method, headers: {} };
  if (data !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }
  try {
    const response = await fetch(baseUrl + path, options);
    const body = response.status === 204 ? null : await response.json();
    return { status: response.status, body };
  } catch (e) {
    return { status: 0, body: { error: `can't reach ${baseUrl}, the service may be down` } };
  }
}

// --- small helpers ---

// Escape text before putting it into HTML, so a note like "<b>" shows as text.
function esc(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

function errorBox(message) {
  return message ? `<p class="error">${esc(message)}</p>` : "";
}

function recordsLink(name) {
  return `<a href="#/records/${encodeURIComponent(name)}">${esc(name)}</a>`;
}

// "Bench Press: 8x60, 6x65" on each line -> [{name, sets: [{reps, weight_kg}]}].
// The workouts service still validates everything; this only reshapes the text.
function parseExercises(text) {
  const exercises = [];
  for (const line of text.split("\n")) {
    if (!line.trim()) continue;
    const colon = line.lastIndexOf(":");
    if (colon === -1) throw new Error(`"${line.trim()}" needs a colon, like "Squat: 5x100"`);
    const sets = line.slice(colon + 1).split(",").map((part) => {
      const [reps, weight] = part.toLowerCase().split(/x|×/).map((n) => n.trim());
      if (!reps || !weight) throw new Error(`"${part.trim()}" should look like 8x60 (reps x kg)`);
      return { reps: Number(reps), weight_kg: Number(weight) };
    });
    exercises.push({ name: line.slice(0, colon).trim(), sets });
  }
  return exercises;
}

// --- pages ---

async function showHome(section, error = "", form = {}) {
  const [workouts, exercises] = await Promise.all([
    api(WORKOUTS, "/api/workouts"),
    api(WORKOUTS, "/api/workouts/exercises"),
  ]);

  let history = errorBox(workouts.body.error);
  if (workouts.status === 200) {
    history = workouts.body.workouts.length === 0 ? "<p>No workouts yet.</p>" : `
      <table>
        <tr><th>Date</th><th>Notes</th></tr>
        ${workouts.body.workouts.map((w) => `
          <tr><td><a href="#/workouts/${w.id}">${esc(w.performed_on)}</a></td><td>${esc(w.notes)}</td></tr>
        `).join("")}
      </table>`;
  }

  let names = errorBox(exercises.body.error);
  if (exercises.status === 200) {
    names = exercises.body.exercises.length === 0 ? "<p>Log a workout to start tracking records.</p>" : `
      <p class="hint">Click an exercise to see its personal records, progress and goal.</p>
      <ul>${exercises.body.exercises.map((n) => `<li>${recordsLink(n)}</li>`).join("")}</ul>`;
  }

  page.innerHTML = `
    <h2 id="log">Log a workout</h2>
    ${errorBox(error)}
    <form id="log-form">
      <label for="date">Date</label>
      <input type="date" id="date" name="date" value="${esc(form.date || new Date().toISOString().slice(0, 10))}" required>
      <label for="exercises">Exercises</label>
      <textarea id="exercises" name="exercises" rows="5"
                placeholder="Bench Press: 8x60, 6x65&#10;Squat: 5x100">${esc(form.exercises)}</textarea>
      <p class="hint">One exercise per line. Sets are reps x kg, separated by commas.</p>
      <label for="notes">Notes</label>
      <input type="text" id="notes" name="notes" value="${esc(form.notes)}">
      <button type="submit">Save workout</button>
    </form>
    <h2 id="history">History</h2>
    ${history}
    <h2 id="records">Records by exercise</h2>
    ${names}`;

  document.getElementById("log-form").addEventListener("submit", saveWorkout);
  if (section) document.getElementById(section).scrollIntoView();
}

async function saveWorkout(event) {
  event.preventDefault();
  const form = Object.fromEntries(new FormData(event.target));
  let exercises;
  try {
    exercises = parseExercises(form.exercises);
  } catch (e) {
    return showHome("log", e.message, form);
  }
  const result = await api(WORKOUTS, "/api/workouts", "POST",
    { date: form.date, notes: form.notes, exercises });
  if (result.status !== 201) return showHome("log", result.body.error, form);
  location.hash = `#/workouts/${result.body.id}`;
}

async function showWorkout(id) {
  const result = await api(WORKOUTS, `/api/workouts/${id}`);
  if (result.status !== 200) {
    page.innerHTML = errorBox(result.body.error) + `<a class="back" href="#/">← Back to Gym Log</a>`;
    return;
  }
  const workout = result.body;
  page.innerHTML = `
    <h2>Workout on ${esc(workout.performed_on)}</h2>
    ${workout.notes ? `<p>${esc(workout.notes)}</p>` : ""}
    <p class="hint">Click an exercise to see its records and progress.</p>
    ${workout.exercises.map((exercise) => `
      <h3>${recordsLink(exercise.name)}</h3>
      <table>
        <tr><th>Set</th><th>Reps</th><th>Weight (kg)</th></tr>
        ${exercise.sets.map((s, i) => `<tr><td>${i + 1}</td><td>${s.reps}</td><td>${s.weight_kg}</td></tr>`).join("")}
      </table>
    `).join("")}
    <button id="delete">Delete workout</button>
    <br><a class="back" href="#/history">← Back to all workouts</a>`;

  document.getElementById("delete").addEventListener("click", async () => {
    if (!confirm("Delete this workout?")) return;
    await api(WORKOUTS, `/api/workouts/${id}`, "DELETE");
    location.hash = "#/history";
  });
}

// Records crosses the seam: the records service asks workouts for the sets (ADR-6).
// If workouts is down, records answers 503 with an error and the goal it owns.
async function showRecords(name, error = "") {
  const path = `/api/records/${encodeURIComponent(name)}`;
  const result = await api(RECORDS, path);
  const summary = result.body;
  const goal = summary.goal;

  let goalHtml = "";
  if (goal) {
    goalHtml = goal.percent === undefined
      ? `<p>Target <strong>${goal.target_kg} kg</strong> (set ${esc(goal.set_on)}).</p>`
      : `<p>Target <strong>${goal.target_kg} kg</strong> (set ${esc(goal.set_on)}): ${goal.percent}% there.</p>
         <div class="bar"><span style="width: ${Math.min(goal.percent, 100)}%"></span></div>`;
    goalHtml += `<button id="remove-goal">Remove goal</button>`;
  }
  const goalForm = result.status === 200 || result.status === 503 ? `
    <form id="goal-form">
      <label for="target_kg">${goal ? "Change" : "Set"} target 1RM (kg)</label>
      <input type="number" id="target_kg" name="target_kg" step="0.5" min="0.5" max="500" required>
      <button type="submit">Save goal</button>
    </form>` : "";

  let recordsHtml = "";
  let progressHtml = "";
  if (result.status === 200) {
    const prs = summary.personal_records;
    const top = Math.max(...summary.progress.map((p) => p.best_1rm));
    recordsHtml = `
      <h3>Personal records</h3>
      <table>
        <tr><th>Record</th><th>Value</th><th>Set</th><th>Date</th></tr>
        <tr><td>Heaviest weight</td><td><strong>${prs.heaviest.weight_kg} kg</strong></td>
            <td>${prs.heaviest.reps} × ${prs.heaviest.weight_kg} kg</td><td>${esc(prs.heaviest.performed_on)}</td></tr>
        <tr><td>Best estimated 1RM</td><td><strong>${prs.best_1rm.estimated_1rm} kg</strong></td>
            <td>${prs.best_1rm.reps} × ${prs.best_1rm.weight_kg} kg</td><td>${esc(prs.best_1rm.performed_on)}</td></tr>
      </table>
      <p class="hint">Estimated 1RM uses the Epley formula: weight × (1 + reps / 30).</p>`;
    progressHtml = `
      <h3>Progress</h3>
      <table>
        <tr><th>Date</th><th>Best est. 1RM</th><th></th></tr>
        ${summary.progress.map((p) => `
          <tr><td>${esc(p.date)}</td><td>${p.best_1rm} kg</td>
              <td style="width: 50%"><div class="bar"><span style="width: ${Math.round(p.best_1rm / top * 100)}%"></span></div></td></tr>
        `).join("")}
      </table>`;
  }

  page.innerHTML = `
    <h2>${esc(summary.exercise || name)}</h2>
    ${errorBox(result.status === 200 ? "" : summary.error)}
    ${recordsHtml}
    <h3>Goal</h3>
    ${errorBox(error)}
    ${goalHtml}
    ${goalForm}
    ${progressHtml}
    <a class="back" href="#/records">← Back to Gym Log</a>`;

  const form = document.getElementById("goal-form");
  if (form) form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const target = Number(new FormData(form).get("target_kg"));
    const saved = await api(RECORDS, `${path}/goal`, "PUT", { target_kg: target });
    showRecords(name, saved.status === 200 ? "" : saved.body.error);
  });
  const remove = document.getElementById("remove-goal");
  if (remove) remove.addEventListener("click", async () => {
    await api(RECORDS, `${path}/goal`, "DELETE");
    showRecords(name);
  });
}

// --- routing: pick the page from the URL after "#" ---

function route() {
  const [, kind, value] = location.hash.split("/");  // "#/records/Squat" -> ["#", "records", "Squat"]
  if (kind === "workouts" && value) return showWorkout(value);
  if (kind === "records" && value) return showRecords(decodeURIComponent(value));
  return showHome(kind);  // "", "history" or "records": the home page, scrolled to that section
}

window.addEventListener("hashchange", route);
route();
