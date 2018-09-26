test :
	pytest
	mypy --module multi_error
	flake8
	python example.py
