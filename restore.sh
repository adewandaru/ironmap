#!/bin/bash
#intended to be run AFTER database schema modification. it is just a data dump!
sqlite3 data.sqlite <<!
.read file.sql 
!
