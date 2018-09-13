BR := $(shell git branch | grep \* | cut -d ' ' -f2-)
bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

demo:
	docker run -it --rm -v `pwd`:/playbook:ro ubuntu:16.04 bash

to_master:
	@echo $(BR)
	git checkout master && git merge $(BR) && git checkout $(BR)
