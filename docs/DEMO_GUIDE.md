# Three-to-five minute review demonstration

1. Launch via README commands or `./start.ps1`; open http://127.0.0.1:5173. Verify health and SIMULATED DATA banner. Explain the prototype is proposal-stage.
2. Overview: choose Normal charging, speed 10×, Play. Separate human kcal, loaded electrical mJ and ideal usable reservoir J. At virtual sample 28, one synthetic receiver confirmation appears; reservoir curve is a software fixture, not a physical energy model.
3. Workout: enter activity, real or illustrative explicitly entered mass, planned duration. Start, pause/resume, finish. Show actual elapsed-time estimate and traceable completion points. Short review sessions earn completion points and few kcal, not the full planned duration.
4. Energy Lab: inspect power, TEG current/voltage, thermal ΔT, charging and excluded intervals. Explain null current produces no fabricated power.
5. Overview: switch to Failed BLE event or Insufficient voltage and Play. Show failure outcomes or threshold readiness. Sensor disconnection and stale scenarios expose quality/freshness handling.
6. Rewards: show the transaction explanations and separate simulated source. Points do not quantify electricity savings. Optional fictional leaderboard is disabled by default.
7. Experiments: select a run; inspect metadata, compare reservoir curves by sample index, export CSV, Print research report. The report retains source warning and estimate caveats.
8. Hardware mode: explicitly select it; an empty workspace reports disconnected and unavailable readings, never synthetic fallback. Create an experiment for future ingestion only if needed.

## Reset and scenarios
Reset demo clears only synthetic workouts, samples, events, experiments and reward transactions. Settings and measured/user-entered data persist. All eight scenarios: normal; low thermal gradient; slow charging; insufficient voltage; failed BLE; sensor disconnect; stale telemetry; brownout/restart. 120 synthetic samples, fixed fixture start 2026-01-01 UTC, one virtual second/sample. Wall-time playback changes speed but not timestamps or integrated totals. Synthetic freshness uses recorded reception time; measured freshness uses device time. Restart pauses an in-progress scenario. To run another scenario from the beginning, choose a different scenario or Reset demo. Same unfinished scenario resumes.

## Known limits
No physical transport has been tested. No radio command/control, event-energy integration, hardware firmware or power-budget validation. Single local workspace; manual workouts are self-reported. Dates display in browser local timezone; today/weekly activity grouping uses UTC and is labelled. Print layout supplies research summary, not an experimental feasibility result. All calculations and defaults require qualified instrumentation before scientific conclusions.
