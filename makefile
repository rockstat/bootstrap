BR := $(shell git branch | grep \* | cut -d ' ' -f2-)
bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

demo:
	docker run -it --rm -v `pwd`:/playbook:ro ubuntu:16.04 bash

up_master: 
	@echo "on branch $(BR)"
	
	@[ "$(BR)" == "dev" ] && true || (echo "only dev can be used. you on $(BR)" && exit 1)
	@[ ! -z "$(git status --porcelain)" ] && true || (echo "directory not clean. commit changes first" && exit 1)
	@git checkout master && git rebase dev && git push origin master && git checkout dev \
		&& echo "master rebased and pushed"

to_master:
	@echo $(BR)
	git checkout master && git rebase $(BR) && git checkout $(BR)

push:
	git push origin master
	git push origin dev

h_test_rebuild:
	source .env && curl -H "Content-Type: application/json" -H "Authorization: Bearer $${HETZNER_API_KEY}" \
		-d '{"image": "ubuntu-16.04"}' \
		-X POST https://api.hetzner.cloud/v1/servers/1114551/actions/rebuild | jq

h_stage_rebuild:
	source .env && curl -H "Content-Type: application/json" -H "Authorization: Bearer $${HETZNER_API_KEY}" \
		-d '{"image": "ubuntu-16.04"}' \
		-X POST https://api.hetzner.cloud/v1/servers/594645/actions/rebuild | jq
