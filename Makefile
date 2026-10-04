SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-builtin-rules --warn-undefined-variables

HOST_ROOT ?= $(abspath ../gams)
CARGO_TARGET_DIR ?= $(HOST_ROOT)/build.nosync/app/target
HOST_BIN ?= $(CARGO_TARGET_DIR)/release/gams
HOST_CC ?= $(shell command -v clang || command -v cc)
HOST_CXX ?= $(shell command -v clang++ || command -v c++)

.PHONY: setup-local setup-releases require-local-assets test web integration run run-dev test-release release-install release-stage release-check

# Packaging/game checks do not use a sibling Host or native game build.
test-release:
	python3 -m unittest discover -s test -p 'test_*.py'

release-install:
	python3 scripts/release.py install --lock release-lock.json

# Resolve only for release recipes; a failed read/validation also aborts make -n.
override RELEASE_TAG = $(shell python3 -c 'import json, re, sys; version = json.load(open("release.json"))["version"]; isinstance(version, str) and re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version) or sys.exit("invalid release version"); print("v" + version)')$(if $(filter 0,$(.SHELLSTATUS)),,$(error Cannot derive release tag from release.json))

release-stage:
	python3 scripts/release.py stage --tag $(RELEASE_TAG)

release-check:
	python3 scripts/release.py check --tag $(RELEASE_TAG)

run-dev: run
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
	GAMS_HOST_ROOT="$(HOST_ROOT)" GAMS_HOST_BIN="$(HOST_BIN)" node test/check-export.mjs

run: require-local-assets
	cd "$(HOST_ROOT)/cmd/app/src-tauri"
	GAMS_APP_CWD="$(CURDIR)" CARGO_TARGET_DIR="$(CARGO_TARGET_DIR)" CC="$(HOST_CC)" CXX="$(HOST_CXX)" cargo tauri dev
