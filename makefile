BR := $(shell git branch | grep \* | cut -d ' ' -f2-)
bump-patch:
	bumpversion patch

password:
	openssl passwd -apr1

bump-minor:
	bumpversion minor

demo:
	docker run -it --rm -v `pwd`:/playbook:ro ubuntu:16.04 bash

up_master: 
	@echo "on branch $(BR)"
	
	@[ "$(BR)" == "dev" ] && true || (echo "only dev can be used. you on $(BR)" && exit 1)
	@[ -z "$(git status --porcelain)" ] && true || (echo "directory not clean. commit changes first" && exit 1)
	@git checkout master && git merge dev && git push origin master && git checkout dev \
		&& echo "master merged and pushed"

to_master:
	@echo $(BR)
	git checkout master && git merge $(BR) && git checkout $(BR)

push:
	git push origin master
	git push origin dev


hz_images:
	@echo "quering images list"
	@source .env && curl -s \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $${HETZNER_API_KEY}" https://api.hetzner.cloud/v1/images \
		| jq '.images | .[] | {id: .id, name: .name}'

hz_servers:
	@echo "quering servers list"
	@source .env && curl -s \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $${HETZNER_API_KEY}" https://api.hetzner.cloud/v1/servers \
		| jq '.servers | .[] | {id: .id, name: .name, status: .status, image: .image.name}'

hz_test_rebuild:
	@source .env && curl -s -H "Content-Type: application/json" -H "Authorization: Bearer $${HETZNER_API_KEY}" \
		-d '{"image": "ubuntu-18.04"}' \
		-X POST "https://api.hetzner.cloud/v1/servers/$${HETZNER_TEST_SRV}/actions/rebuild" | jq

playbook_test_init:
	ansible-playbook os_init.yml --limit=test -e wait_server=1

playbook_test_full:
	ansible-playbook platform.yml --limit=test --tags=full -e branch=dev

playbook_test_platform:
	ansible-playbook platform.yml --limit=test --tags=platform -e branch=dev

test_rebuild: hz_test_rebuild playbook_test_init playbook_test_full
