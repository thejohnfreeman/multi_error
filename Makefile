test :
	pytest
	mypy --module multi_error --ignore-missing-imports
	flake8
	python example.py
