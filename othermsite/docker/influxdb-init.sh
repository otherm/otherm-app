#!/bin/bash

influx -username "$INFLUXDB_ADMIN_USER" -password "$INFLUXDB_ADMIN_PASSWORD" -execute 'create database dailysummaries' -database '_internal'