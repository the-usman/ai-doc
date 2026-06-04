# Runbook

This document tells you how to run AI-Doc locally and how to deploy it. It is written for a developer who has never seen this project before. If you can follow these steps and have a running system in under thirty minutes, the runbook is doing its job. If you get stuck, update the runbook with what you learned.

---

## Prerequisites

Before running anything, confirm you have the following installed and configured.

Docker Desktop must be running. Open a terminal and run `docker --version` — if it returns a version number, Docker is ready. If not, install it from docker.com and start Docker Desktop before continuing.

Git must be installed. Run `git --version` to confirm.

A GitHub account with access to the AI-Doc fork is required. If you are setting this up for the first time, fork the repository to your own account and clone it locally.

Your `.env` file must exist in the project root and contain all variables listed in `.env.example`. Copy `.env.example` to `.env` and fill in the values. The Dokploy access credentials and OAuth client credentials come from TSS — if you do not have them, ask before starting.

---

## Running locally

All local development runs through Docker Compose. The following commands are run from the project root directory.

To start the full stack for the first time, run `docker compose up --build` from the **repository root** (where `docker-compose.yml` lives). The `--build` flag forces Docker to rebuild the images, which is necessary the first time and after any change to a Dockerfile or dependency file. On subsequent starts where nothing has changed in the image, `docker compose up` without `--build` is faster.

You will see log output from each service as it starts. The application is ready when you see the startup message from your application server — this will look different depending on your stack, but will be something like "Application startup complete" for FastAPI or "ready - started server on 0.0.0.0:3000" for Next.js.

To stop the stack, press Control+C in the terminal where it is running, or run `docker compose down` from another terminal. The `down` command stops containers but preserves the database volume — your data persists between runs. To wipe the database and start fresh, run `docker compose down -v`. The `-v` flag removes volumes, including the database data. Use this only when you want a clean slate.

To see the logs for a specific service, run `docker compose logs -f service_name` where `service_name` is the name of the service in your compose file (for example, `app`, `db`, or `redis`).

---

## Connecting to the database locally

pgAdmin is the recommended tool for browsing the database directly. Once the stack is running, the database is accessible at `localhost` on the port defined in `docker-compose.yml` (default is 5432). Add a new server in pgAdmin with those connection details and the credentials from your `.env` file.

You can also connect directly from the terminal using `psql`:

```
psql -h localhost -p 5432 -U your_db_user -d your_db_name
```

This is useful for running the schema directly. To apply or re-apply the schema, run:

```
psql -h localhost -p 5432 -U your_db_user -d your_db_name -f schema/schema.sql
```

---

## Running the tests

Tests run inside the Docker environment to ensure they use the same database and dependencies as the application. To run the full test suite, execute the following from the project root:

For Python projects: `docker compose run --rm app pytest`

For TypeScript projects: `docker compose run --rm app npm test`

To run a specific test file: append the file path to the command — for example, `docker compose run --rm app pytest tests/test_auth.py`.

A clean test run means every test passes and there are no warnings about deprecations or missing fixtures. If the suite has failing tests before your changes, record that before you start work so you can distinguish pre-existing failures from regressions you introduced.

---

## Deploying to Dokploy

Log into your Dokploy panel using the credentials provided by TSS. The URL will be in the format `devname.tss-domain.com/dokploy`.

Navigate to your project. If this is the first deployment, create a new application and point it at the `docker-compose.prod.yml` file in the repository. Connect the GitHub repository so that Dokploy can pull on deploy.

Set all environment variables in the Dokploy secrets panel. These are the production equivalents of the values in your `.env` file. Never paste secrets directly into compose files or configuration files — always use the secrets panel.

To deploy, trigger a deployment from the Dokploy panel. Dokploy will pull the latest commit from the connected branch, build the Docker image, and start the services. Watch the deployment logs in the panel — if the deployment fails, the logs will tell you why.

Once deployed, visit the live URL and confirm the application is running. Test the sign-in flow. Confirm the database is connected by performing an action that writes to it.

---

## Common problems

**Docker Compose fails to start with a port conflict.** This means something is already using a port that the compose file is trying to bind. Find the conflicting process with `lsof -i :PORT_NUMBER` and either stop it or change the port in your `docker-compose.yml`.

**The application starts but cannot connect to the database.** Check that the `DB_HOST` environment variable points to the service name in the compose file (usually `db`), not `localhost`. Inside Docker's network, services communicate by service name, not by localhost.

**The OAuth redirect fails with a redirect_uri_mismatch error.** The callback URL configured in your OAuth provider's developer console does not match the one your application is sending. For local development, the callback URL should be `http://localhost:PORT/auth/callback`. For production, it should be your live URL. Both need to be registered in the provider's console.

**The CI pipeline fails on lint but passes locally.** Your editor may be auto-fixing issues that the CI environment does not. Run the linter from the terminal (not from your editor) before pushing to confirm what CI will see.

**A Dokploy deployment succeeds but the application returns an error.** Check the application logs in the Dokploy panel. The most common cause is a missing environment variable in the secrets panel that exists locally in `.env` but was not added to production.

---

*Update this document whenever you discover a problem that took more than ten minutes to resolve. Future you and future colleagues will thank present you.*
