# This Makefile is used only by code checkers, not during build time.

PYTHON_FILES = $(wildcard src/*.py)
PYTHON_FILES += frontend_deleter.py photosifter.py

# Disable:
#   C0111: missing docstring (don't need a docstring for two line methods...)
#   C0103: naming style problem (to remain consistent with the Google Photos API)
#   C0330: wrong continued indentation (sometimes looks better)
#   R0902: too many instance attributes (don't care at all)
#   R0913: too many arguments (don't care as well)
PYLINT_ARGS = --disable=C0111,C0103,C0330,R0902,R0913

# Disable:
#   E128: continuation line under-indented (see above)
PYCODESTYLE_ARGS = --ignore=E128

# Make lines longer (between 80 and 100 is ok)
PYCODESTYLE_ARGS += --max-line-length=99


all: pylint pycodestyle

pylint: $(patsubst %, %.pylint, $(PYTHON_FILES))

pycodestyle: $(patsubst %, %.pycodestyle, $(PYTHON_FILES))


.PHONY: FORCE
FORCE:

%.py.pylint: FORCE
	@echo "=== pylint $(@:.pylint=) ==="
	@-pylint --extension-pkg-whitelist=cv2 $(PYLINT_ARGS) $(@:.pylint=)
	@echo

%.py.pycodestyle: FORCE
	@echo "=== pycodestyle $(@:.pycodestyle=) ==="
	@-pycodestyle $(PYCODESTYLE_ARGS) $(@:.pycodestyle=)
	@echo

%.py: %.py.pycodestyle %.py.pylint
	@echo "Done: $@"


lines:
	@wc -l $(PYTHON_FILES)
