// Where the two services live. These are the local defaults (docker compose).
// On Azure the CD pipeline overwrites this file with the deployed services' URLs.
window.GYMLOG_CONFIG = {
  workoutsUrl: "http://localhost:8001",
  recordsUrl: "http://localhost:8002",
};
