## Installation

1. Check out the source code
2. Install and configure apache-cassandra-2.2.6
3. Create a virtual Python environment with requirement.txt
4. Start up the webserver

### To run Cassandra use:

    bin/cassandra -f

### Create a virtual Python environment with dependencies

    pip install -U -r requirements.txt

### Create the schema

python manage.py sync_cassandra

### Start up the webserver

This is the fun part! We're done setting everything up, we just need to run it:

    python manage.py runserver