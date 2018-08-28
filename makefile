
patch:
	bumpversion patch

minore:
	bumpversion minore

demo:
	docker run -it --rm -v `pwd`:/playbook:ro ubuntu:16.04 bash
