up:
	docker compose up -d --build

deploy:
	docker compose build deployer
	docker compose up deployer

logs:
	docker compose logs -f

down:
	docker compose down

clean:
	docker compose down -v --rmi local

nuke:
	docker compose down -v
	docker volume prune -f
	docker image prune -f


