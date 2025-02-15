.PHONY: poetry-linux
poetry-linux:
	@# Install poetry (Linux, OSX, WSL)
	@# system Python should be installed in advance
	@# If no command "python",
	@# sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
	@# If no command pip,
	@# sudo apt install python3-pip; python -m pip install -U pip
	@curl -sSL https://install.python-poetry.org | python3 -
	@export PATH=$PATH:$HOME/.poetry/bin
	@source ~/.poetry/env
	@poetry --version
	@poetry config virtualenvs.in-project true
	@poetry config repositories.testpypi https://test.pypi.org/legacy/
	@poetry config --list

.PHONY: poetry-windows
poetry-windows:
	@# Install poetry (Windows)
	@# system Python should be installed in advance
	@(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
	@poetry --version
	@poetry config virtualenvs.in-project true
	@poetry config repositories.testpypi https://test.pypi.org/legacy/
	@poetry config --list

.PHONY: install
install:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry install --with test,docs

.PHONY: update
update:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry update

.PHONY: add
add:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry add ${target}

.PHONY: add-dev
add-dev:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry add ${target} --group dev

.PHONY: remove
remove:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry remove ${target}

.PHONY: remove-dev
remove-dev:
	@python -m pip install --upgrade pip
	@poetry self update
	@poetry remove ${target} --group dev

.PHONY: test
test:
	@# All tests: make test
	@# Selected tests: make test target=/test_scenario.py::TestScenario
	@poetry run deptry .
	@poetry run pflake8 covsirphy
	@poetry run pytest tests${target}

.PHONY: docs
docs:
	# docs/index.rst must be updated to include the notebooks
	@cp --force example/*.ipynb docs/
	@sudo apt install pandoc -y
	# Save markdown files in docs directory
	# docs/markdown/*md will be automatically included
	@cp --force .github/CODE_OF_CONDUCT.md docs/CODE_OF_CONDUCT.md
	@cp --force .github/CONTRIBUTING.md docs/CONTRIBUTING.md
	@cp --force SECURITY.md docs/SECURITY.md
	@pandoc -f commonmark -o docs/README.rst README.md --to rst
	# Create API reference
	@poetry run sphinx-apidoc -o docs covsirphy -fMT
	# Execute sphinx
	@cd docs; poetry run make html; cp -a _build/html/. ../docs

.PHONY: pypi
pypi:
	@# poetry config http-basic.pypi <username> <password>
	@rm -rf covsirphy.egg-info/*
	@rm -rf dist/*
	@poetry publish --build

.PHONY: test-pypi
test-pypi:
	@# poetry config http-basic.testpypi <username> <password>
	@rm -rf covsirphy.egg-info/*
	@rm -rf dist/*
	@poetry publish -r testpypi --build

.PHONY: clean
clean:
	@rm -rf input
	@rm -rf kaggle
	@rm -rf prof
	@rm -rf .pytest_cache
	@find -name __pycache__ | xargs --no-run-if-empty rm -r
	@rm -rf dist covsirphy.egg-info
	@rm -f .coverage*
	@poetry cache clear . --all

.PHONY: setup-anyenv
setup-anyenv:
	@ # Set-up anyenv in Bash (Linux, WSL)
	@git clone https://github.com/riywo/anyenv ~/.anyenv
	@echo 'export PATH="$HOME/.anyenv/bin:$PATH"' >> ~/.bashrc; source ~/.bashrc
	@anyenv install --init: echo 'eval "$(anyenv init -)"' >> ~/.bashrc; source ~/.bashrc
	@/bin/mkdir -p $(anyenv root)/plugins; git clone https://github.com/znz/anyenv-update.git $(anyenv root)/plugins/anyenv-update
	@ # set-up pyenv
	@anyenv install pyenv;  exec ${SHELL} -l

.PHONY: setup-latest-python
setup-latest-python:
	@# Install the latest stable version of Pythonand set default for CovsirPhy project
	@anyenv update --force
	@version=`pyenv install -l | grep -x '  [0-9]\.[0-9]\.[0-9]' | tail -n 1 | tr -d ' '`
	@echo python ${version}
	@pyenv install ${version}; pyenv local ${version}; anyenv versions
	@# Install dependencies
	@rm -rf .venv
	@rm -f poetry.lock
	@pip install --upgrade pip
	@poetry install
	@poetry env info
