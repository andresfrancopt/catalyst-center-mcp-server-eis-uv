.DEFAULT_GOAL := help

HOST ?= 0.0.0.0
PORT ?= 8000

.PHONY: help install env model smoke remote

help:
	@echo ""
	@echo "Catalyst Center MCP Server — available targets:"
	@echo ""
	@echo "  make install   Install / sync dependencies into .venv (uv sync)"
	@echo "  make env       Copy environment.example.env → environment.env (skips if exists)"
	@echo "  make model     Download the sentence-transformer embedding model (one-time)"
	@echo "  make smoke     Smoke-test: start stdio server for 10s and tail the log"
	@echo "  make remote    Start the streamable HTTP server (HOST/PORT configurable)"
	@echo ""
	@echo "  Examples:"
	@echo "    make remote HOST=127.0.0.1 PORT=9000"
	@echo ""

install:
	uv sync

env:
	@if [ -f environment.env ]; then \
		echo "environment.env already exists — skipping."; \
	else \
		cp environment.example.env environment.env; \
		echo "Created environment.env — fill in CC_URL, CC_USER, CC_PASS."; \
	fi

model:
	uv run python download_model.py --no-ssl-verify

smoke:
	@echo "Starting stdio server for 10 seconds — tailing log..."
	@mkdir -p logs
	@uv run python catalyst_center_stdio.py > /dev/null 2>&1 & PID=$$!; \
	sleep 10; \
	kill $$PID 2>/dev/null || true; \
	echo "--- logs/catalyst_center_mcp.log (last 20 lines) ---"; \
	tail -20 logs/catalyst_center_mcp.log

remote:
	uv run python catalyst_center_remote.py --host $(HOST) --port $(PORT)
