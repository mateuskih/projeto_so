PYTHON = python
PIP = pip3
SOURCE_DIR = ./

OS := $(shell uname -s 2>/dev/null || echo Windows)

.PHONY: help
help:
	@echo "Comandos disponíveis:"
	@echo "make install     - Instala dependencias essenciais diretamente."
	@echo "make run         - Executa o projeto principal."
	@echo "make lint        - Realiza analise de estilo com flake8."
	@echo "make clean       - Remove arquivos temporários."

.PHONY: install
install:
	$(PIP) install flake8  # Exemplo de dependência essencial

.PHONY: run
run:
	$(PYTHON) main.py

.PHONY: lint
lint:
	flake8 $(SOURCE_DIR)

.PHONY: clean
clean:
	rm -fr models/__pycache__
	rm -fr services/__pycache__
	rm -fr views/__pycache__
