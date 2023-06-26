#!/bin/bash

### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ###
###  Generated with the help of ChatGPT  ###
### ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ###

# https://gist.github.com/iAnanich/2b94fdd9de8dc34f1eb6bf9def06e3d5

# Usage:
# ./do dc ps
# ./do dc down
# ./do dc up -d service
# ./do dc logs -f service
# ./do update
# ./do update service
# Add functions as you like, reuse `dc` function and other functions


### Set environment variables from .env file
### ----------------------------------------
set -o allexport
source .env
set +o allexport

### Defaults
### --------
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-$(basename "$(pwd)")}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.dev.yml}


### Get the Docker Compose binary name
### ----------------------------------
# Docker is now switching to making Compose a plugin for Docker Engine,
# there for it's call signature is no longer using dash

if docker compose version > /dev/null 2>&1; then
  # Use the plugin for the Docker CLI if available
  _DOCKER_COMPOSE_COMMAND="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
  # Use the standalone binary if available
  _DOCKER_COMPOSE_COMMAND="docker-compose"
else
  echo "Error: docker-compose or docker CLI with compose plugin is not installed"
  exit 1
fi


### Utility functions
### -----------------
yell() { echo "$0: $*" >&2; }
die() { yell "$*"; exit 111; }
try() { "$@" || die "cannot $*"; }


### ==================
###  Define functions
### ------------------

function dc {
  echo "Executing Docker Compose command: ${_DOCKER_COMPOSE_COMMAND}" "$@"
  echo "With env vars: COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME} COMPOSE_FILE=${COMPOSE_FILE}"
  ${_DOCKER_COMPOSE_COMMAND} "$@"
}

function restart {
  echo "Restart:" "$@"
  try dc restart "$@"
  dc logs -f
}

function update {
  echo "Update:" "$@"
  try dc build "$@"
  try dc up -d --force-recreate "$@"
  dc logs -f
}

function build {
  echo "Build docker image"
  IMAGE=${IMAGE_NAME:-djaram}:${IMAGE_TAG:-edge}
  docker build -t ${IMAGE} .
}

function spin {
  # quickly roll dockerized app
  try build
  try dc up -d
  dc logs -f
}

function clear-db {
  echo "Clearing DB data..."
  DB_VOLUME_NAME=${COMPOSE_PROJECT_NAME}_pgdata
  docker volume rm ${DB_VOLUME_NAME}
}

function app {
  echo "App action:" "$@"
  #cd app && sh ./do "$@" && cd -
  cd app
  ./do "$@"
  cd -
}

### -----------------------------
###  end of functions definition
### =============================


### Handle command (function) execution
### -----------------------------------

# Generate the command map dynamically based on defined functions
function generate_command_map {
  declare -a map
  for func in $(declare -F | awk '{print $3}'); do
    if [[ "$func" != "generate_command_map" ]]; then
      map+=("$func")
    fi
  done
  echo "${map[*]}"
}

# Define the command mapping
command_map=($(generate_command_map))

# Parse command line arguments and call the appropriate function
if [[ " ${command_map[*]} " == *" $1 "* ]]; then
  # Call the corresponding function
  "${1}" "${@:2}"
else
  echo "Invalid command. Usage: ./do [${command_map[*]}]. Got:" "$@"
fi
