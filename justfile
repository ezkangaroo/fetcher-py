test:
    poetry run pytest --cov=fetcher_py

lint: 
    ruff check .

fmt:
    ruff format .