# BC Registries Notify Service

This repository contains two Flask services that share a PostgreSQL database and use Google Cloud Pub/Sub for asynchronous notification delivery:

- `notify-api` accepts authenticated notification requests, persists work, selects a provider, and publishes a CloudEvent.
- `notify-delivery` receives provider-specific Pub/Sub pushes, reloads the notification, calls the provider, records delivery history, and removes successful queued work.

## Documentation

- [Architecture](ARCHITECTURE.md): canonical architecture.md-based orientation for agents and maintainers.

The package READMEs under `notify-api/` and `notify-delivery/` contain package-specific commands and image details. `ARCHITECTURE.md` is the single cross-service guide.
