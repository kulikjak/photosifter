
# Note, that not all of these checks are necessarily supposed to succeed
# as they are rather a quick way to check the current status of the code
# base and fix those things which do make sense to fix.

PYTHON_FILES = $(wildcard src/*.py)
PYTHON_FILES += frontend_deleter.py image_focus.py

# Disable:
#   C0111 missing docstring (dom't need a docstring for two line methods...)
PYLINT_ARGS = --disable=C0111

# Make lines longer (between 80 and 100 is ok)
PYCODESTYLE_ARGS = --max-line-length=99


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
