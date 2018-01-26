update-and-push:
	sh ./update-and-push.sh version

make-venv:
	pip install virtualenv
	python -m virtualenv ~/nomenclate_venv


make-venv-py3:
	python3 -m venv ~/nomenclate_venv


activate-venv:
	. ~/nomenclate_venv/bin/activate


install-deps: make-venv activate-venv
	pip install -r requirements.txt
	pip install coveralls nose


install-deps-py3: make-venv-py3 activate-venv
	pip3 install -r requirements.txt
	pip3 install coveralls nose


test-unit: activate-venv
	nosetests -c tests/nose.cfg --with-coverage --nologcapture --with-xunit --xunit-file=$TEST_PATH/noselog$PYTHON_VERSION.xml --cover-package=nomenclate


upload-coverage: activate-venv
	coveralls

load-git-tag:
	GIT_TAG=`git describe --tags`
	echo export GIT_TAG >> "$BASH_ENV"

verify-git-tag: make-venv activate-venv load-git-tag
	echo $CIRCLE_TAG
	echo $GIT_TAG
	python setup.py verify

init-pypirc:
	echo -e "[pypi]" >> ~/.pypirc
	echo -e "username = $PYPI_USERNAME" >> ~/.pypirc
	echo -e "password = $PYPI_PASSWORD" >> ~/.pypirc

upload-to-pypi: activate-venv
	twine upload dist/*