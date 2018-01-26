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
	~/nvenv/bin/python -c tests/nose.cfg --with-coverage --nologcapture --with-xunit --xunit-file=$TEST_PATH/noselog$PYTHON_VERSION.xml --cover-package=nomenclate

test-unit3:
	. ~/nvenv/bin/activate
	~/nvenv/bin/python3 -c tests/nose.cfg --with-coverage --nologcapture --with-xunit --xunit-file=$TEST_PATH/noselog$PYTHON_VERSION.xml --cover-package=nomenclate

upload-coverage:
	. ~/nvenv/bin/activate
	coveralls

load-git-tag:
	GIT_TAG=`git describe --tags`
	export GIT_TAG >> "$BASH_ENV"

verify-git-tag: make-venv load-git-tag
	. ~/nvenv/bin/activate
	echo $CIRCLE_TAG
	echo $GIT_TAG
	python setup.py verify

init-pypirc:
	echo -e "[pypi]" >> ~/.pypirc
	echo -e "username = $PYPI_USERNAME" >> ~/.pypirc
	echo -e "password = $PYPI_PASSWORD" >> ~/.pypirc

upload-to-pypi:
	. ~/nvenv/bin/activate
	twine upload dist/*