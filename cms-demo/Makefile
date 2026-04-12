.PHONY: install serve help

PYTHON ?= $(shell test -x "$(CURDIR)/../taro-api/.venv/bin/python" && echo "$(CURDIR)/../taro-api/.venv/bin/python" || command -v python3 2>/dev/null || echo python)

help:
	@echo "  make install   pip install -r requirements.txt (uses taro-api/.venv if present)"
	@echo "  make serve     CMS on :8088 (set CMS_ADMIN_TOKEN in .env)"
	@echo "  PYTHONPATH=src; requires ../taro-api for policy dir"

install:
	$(PYTHON) -m pip install -r requirements.txt

serve:
	cd "$(CURDIR)" && PYTHONPATH=src $(PYTHON) -m uvicorn cms_app.main:app --host 0.0.0.0 --port 8088 --reload
