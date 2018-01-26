update-and-push:
	sh ./update-and-push.sh version

nvenv: make-venv

nvenv3: make-venv3

make-venv:
	pip install virtualenv
	python -m virtualenv ~/nvenv

make-venv3:
	python3 -m venv ~/nvenv

install-deps: make-venv
	~/nvenv/bin/pip install -r requirements.txt
	~/nvenv/bin/pip install coveralls nose

install-deps3: make-venv3
	~/nvenv/bin/pip3 install -r requirements.txt
	~/nvenv/bin/pip3 install coveralls nose

test-unit:
	. ~/nvenv/bin/activate
	~/nvenv/bin/python -m nose -c tests/nose.cfg --with-coverage --nologcapture --with-xunit --xunit-file=$(TEST_PATH)/noselog$(PYTHON_VERSION).xml --cover-package=nomenclate

test-unit3:
	. ~/nvenv/bin/activate
	~/nvenv/bin/python3 -m nose -c tests/nose.cfg --with-coverage --nologcapture --with-xunit --xunit-file=$(TEST_PATH)/noselog$(PYTHON_VERSION).xml --cover-package=nomenclate

upload-coverage:
	. ~/nvenv/bin/activate
	~/nvenv/bin/coveralls


verify-git-tag: make-venv
	. ~/nvenv/bin/activate
	~/nvenv/bin/python setup.py verify

init-pypirc:
	echo -e "[pypi]" >> ~/.pypirc
	echo -e "username = $PYPI_USERNAME" >> ~/.pypirc
	echo -e "password = $PYPI_PASSWORD" >> ~/.pypirc

upload-to-pypi:
	. ~/nvenv/bin/activate
	~/nvenv/bin/twine upload dist/*