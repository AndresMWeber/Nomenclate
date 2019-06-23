update-and-push:
	sh ./scripts/update-and-push.sh version

nvenv: make-venv

nvenv3: make-venv3

make-venv:
	pip install virtualenv
	python -m virtualenv ~/nvenv

make-venv3:
	python3 -m venv ~/nvenv

install-deps: make-venv
	~/nvenv/bin/pip install -Ur requirements.txt
	~/nvenv/bin/pip install coveralls nose2

install-deps3: make-venv3
	~/nvenv/bin/pip3 install -Ur requirements.txt
	~/nvenv/bin/pip3 install coveralls nose2

test-unit:
	. ~/nvenv/bin/activate
	~/nvenv/bin/python -m nose2 -c tests/.nose2rc --with-xunit --xunit-file=$(TEST_PATH)/nose2log$(PYTHON_VERSION).xml

test-unit3:
	. ~/nvenv/bin/activate
	~/nvenv/bin/python3 -m nose2 -c tests/.nose2rc --with-xunit --xunit-file=$(TEST_PATH)/nose2log$(PYTHON_VERSION).xml

upload-coverage:
	. ~/nvenv/bin/activate
	~/nvenv/bin/coveralls


verify-git-tag: make-venv
	. ~/nvenv/bin/activate
	~/nvenv/bin/python setup.py verify

dist:
	# create a source distribution
	~/nvenv/bin/python setup.py sdist

	# create a wheel
	~/nvenv/bin/python setup.py bdist_wheel

upload-to-pypi:
	. ~/nvenv/bin/activate
	~/nvenv/bin/twine upload dist/*