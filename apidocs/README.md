# API Documentation

## Development Quick Start

There are two ways to develop the API documentation

1. Run the server locally
2. Run the server within docker (recommended)

### Option 1 - Locally

You are likely to have version conflicts/issues with Ruby and Bundler via this method.  If you do, use Docker.

1. `bundle install`
2. `middleman server`
3. Open your browser to localhost:4567

### Option 2 - Docker

1. Install Docker - https://docs.docker.com/install/
2. Run `make`
3. Open your browser to localhost:4567
