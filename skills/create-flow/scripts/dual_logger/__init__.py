"""
SIN-InkogniFlow Dual-Logger Architecture
=========================================

A Human-to-Agent workflow recording system that captures OS-level and
browser-level interactions in real time, merges them chronologically,
and produces a structured machine-readable JSON workflow log.

Components:
  - os_logger:    pynput + NSWorkspace OS-level event tracker (mouse, keyboard, active window)
  - browser_logger.js: Tampermonkey / JS-injection DOM selector capture (click, scroll, input)
  - agent_logger: Flask merge server on port 5000 (CORS, threading lock, chronological sort)
  - executor:     Replay engine with anti-bot countermeasures (Bezier curves, ghost-cursor,
                  CDP selectors, pyautogui for native apps, timestamp-based delays)

Usage:
  # Terminal 1: Start the merge server
  python3 -m dual_logger.agent_logger --port 5000 --output workflow.json

  # Terminal 2: Start the OS-level logger (captures mouse, keyboard, window focus)
  python3 -m dual_logger.os_logger --server http://localhost:5000

  # Browser: Install browser_logger.js as a Tampermonkey userscript
  # (or inject via nodriver/CDP). It will POST events to the merge server.

  # After recording: Replay the workflow
  python3 -m dual_logger.executor --workflow workflow.json --mode hybrid
"""
