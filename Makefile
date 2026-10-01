SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules --warn-undefined-variables

HOST_ROOT ?= $(abspath ../gams)
CARGO_TARGET_DIR ?= $(HOST_ROOT)/build.nosync/app/target
HOST_BIN ?= $(CARGO_TARGET_DIR)/release/gams
HOST_CC ?= $(shell command -v clang || command -v cc)
HOST_CXX ?= $(shell command -v clang++ || command -v c++)

.PHONY: setup-local setup-releases require-local-assets test web integration run
# Published consumption is separate from sibling development assembly.
setup-releases:
	python3 scripts/install-releases.py install --lock release-lock.json

setup-local:
	python3 scripts/setup-local.py --workspace ..

require-local-assets:
	python3 scripts/check-local.py

test:
	$(MAKE) -C game test
	$(MAKE) require-local-assets
	[[ -x "$(HOST_BIN)" ]] || { echo 'Build the external Host release binary first: make -C ../gams app-build-release' >&2; exit 1; }
	GAMS_HOST_ROOT="$(HOST_ROOT)" GAMS_HOST_BIN="$(HOST_BIN)" node content/build.mjs --check --generate-decoder

web:
	$(MAKE) -C game web

integration: require-local-assets
	[[ -x "$(HOST_BIN)" ]] || { echo 'Build the external Host release binary first: make -C ../gams app-build-release' >&2; exit 1; }
	GAMS_HOST_ROOT="$(HOST_ROOT)" GAMS_HOST_BIN="$(HOST_BIN)" HOST_CC="$(HOST_CC)" HOST_CXX="$(HOST_CXX)" node scripts/integration.mjs

run: require-local-assets
	cd "$(HOST_ROOT)/cmd/app/src-tauri"
	GAMS_APP_CWD="$(CURDIR)" CARGO_TARGET_DIR="$(CARGO_TARGET_DIR)" CC="$(HOST_CC)" CXX="$(HOST_CXX)" cargo tauri dev
