from cassandra.cluster import Cluster
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        cluster = Cluster(["cassy"])
        session = cluster.connect()

        rows = session.execute(
            "SELECT * FROM system.schema_keyspaces WHERE keyspace_name='users'")

        if rows:
            msg = ' It looks like you already have a users keyspace.\nDo you '
            msg += 'want to delete it and recreate it? All current data will '
            msg += 'be deleted! (y/n): '
            resp = 'n' # raw_input(msg)
            if not resp or resp[0] != 'y':
                print "Ok, then we're done here."
                return
            session.execute("DROP KEYSPACE users")

        session.execute("""
            CREATE KEYSPACE users
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
            """)

        # create tables
        session.set_keyspace("users")

        session.execute("""
            CREATE TABLE users (
                username text PRIMARY KEY,
                password text
            )
            """)

        session.execute("""
            CREATE TABLE friends (
                username text,
                friend text,
                since timestamp,
                PRIMARY KEY (username, friend)
            )
            """)

        session.execute("""
            CREATE TABLE followers (
                username text,
                follower text,
                since timestamp,
                PRIMARY KEY (username, follower)
            )
            """)

        session.execute("""
            CREATE TABLE tweets (
                tweet_id uuid PRIMARY KEY,
                username text,
                body text
            )
            """)

        session.execute("""
            CREATE TABLE userline (
                username text,
                time timeuuid,
                tweet_id uuid,
                PRIMARY KEY (username, time)
            ) WITH CLUSTERING ORDER BY (time DESC)
            """)

        session.execute("""
            CREATE TABLE timeline (
                username text,
                time timeuuid,
                tweet_id uuid,
                PRIMARY KEY (username, time)
            ) WITH CLUSTERING ORDER BY (time DESC)
            """)


        rows = session.execute(
            "SELECT * FROM system.schema_keyspaces WHERE keyspace_name='bingo'")

        if rows:
            msg = ' It looks like you already have a Bingo keyspace.\nDo you '
            msg += 'want to delete it and recreate it? All current data will '
            msg += 'be deleted! (y/n): '
            resp = 'n' # raw_input(msg)
            if not resp or resp[0] != 'y':
                print "Ok, then we're done here."
                return
            session.execute("DROP KEYSPACE bingo")

        session.execute("""
            CREATE KEYSPACE bingo
            WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'}
            """)

        # create tables
        session.set_keyspace("bingo")

        session.execute("""
            CREATE TABLE bingo.tickets (
            game_id uuid,
            user text,
            a1 int,
            a2 int,
            a3 int,
            a4 int,
            a5 int,
            a6 int,
            a7 int,
            a8 int,
            a9 int,
            b1 int,
            b2 int,
            b3 int,
            b4 int,
            b5 int,
            b6 int,
            b7 int,
            b8 int,
            b9 int,
            c1 int,
            c2 int,
            c3 int,
            c4 int,
            c5 int,
            c6 int,
            c7 int,
            c8 int,
            c9 int,
            PRIMARY KEY ((game_id, user)))
            """)

        session.execute("""
            CREATE TABLE bingo.announcement (
                game_id uuid,
                announcement_time timestamp,
                number int,
                PRIMARY KEY (game_id, announcement_time)
            ) WITH CLUSTERING ORDER BY (announcement_time DESC)
            """)

        session.execute("""
            CREATE TABLE bingo.games (
            game_id uuid PRIMARY KEY,
            announcement_duration int,
            bottom_row text,
            created_by text,
            end_time timestamp,
            four_corners text,
            full_house text,
            is_active boolean,
            middle_row text,
            no_of_players int,
            start_time timestamp,
            top_row text)
            """)

        print 'All done!'
