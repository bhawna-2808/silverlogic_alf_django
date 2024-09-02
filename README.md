# ALF Django

This is the repository for the back end API and admin of the ALF Boss system.

## Requirements

- Python 2.7

# Devleopment

## Quick Start

1. Go to alf-ansible and follow the README to initialize it if needed
2. Go to alf-ansible/apps/api
3. Run `vagrant up db web` to start and configure the VMs
4. Use a copy of the staging database

    ```
    vagrant scp ../path-to-database-dump.sql db:/home/vagrant/
    vagrant ssh db
    sudo -u postgres psql
    drop database api; create database api;
    \q
    sudo -u postgres psql api < name-of-database-dump.sql
    ```
5. Exit the db VM
6. SSH to the web VM `vagrant ssh web`
7. Activate the dev enrionment `. dev`
8. Run any ./manage.py commands or use `py.test` to run tests.

## Residents Module Subscription

In order to use the resident module you need a subscription.  To get around having to deal
with payments / credit cards you can create a subscription for your facility in the
admin instead.
