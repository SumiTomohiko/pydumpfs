PYTHON=python

clean:
	find . -name "*.pyc" -print0 | xargs -0 rm -f
	find . -name "svn-commit*" -print0 | xargs -0 rm -f
	find . -name "*.log" -print0 | xargs -- rm -f

commit:
	svn update
	svn commit

diff:
	svn diff

status:
	svn status

test:
	PYTHONPATH=src $(PYTHON) src/pydumpfs/tests/__init__.py

update:
	svn update

sdist:
	$(PYTHON) setup.py sdist

install:
	$(PYTHON) setup.py install

.PHONY: clean commit diff status test update sdist install
