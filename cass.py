from datetime import datetime
from uuid import uuid1, UUID
import random

from library.bingo_scripts import number_genrator
from library.bingo_scripts import ticket_genrator

from cassandra.cluster import Cluster

cluster = Cluster(["cassy"])
session_user = cluster.connect('users')
session_bingo = cluster.connect('bingo')

# Prepared statements, reuse as much as possible by binding new values
tweets_query = None
userline_query = None
timeline_query = None
friends_query = None
followers_query = None
remove_friends_query = None
remove_followers_query = None
add_user_query = None
get_tweets_query = None
get_usernames_query = None
get_followers_query = None
get_friends_query = None

get_games_query = None
game_query = None
get_game_detail_query = None
game_announcement_query = None
ticket_query = None
get_ticket_query = None
check_game_announcement = None
update_claim_query = None

# NOTE: Having a single userline key to store all of the public tweets is not
#       scalable.  This result in all public tweets being stored in a single
#       partition, which means they must all fit on a single node.
#
#       One fix for this is to partition the timeline by time, so we could use
#       a key like !PUBLIC!2010-04-01 to partition it per day.  We could drill
#       down even further into hourly keys, etc.  Since this is a demonstration
#       and that would add quite a bit of extra code, this excercise is left to
#       the reader.
PUBLIC_USERLINE_KEY = '!PUBLIC!'


class DatabaseError(Exception):
    """
    The base error that functions in this module will raise when things go
    wrong.
    """
    pass


class NotFound(DatabaseError):
    pass


class InvalidDictionary(DatabaseError):
    pass


def _get_line(table, username, start, limit):
    """
    Gets a timeline or a userline given a username, a start, and a limit.
    """
    global get_tweets_query
    if get_tweets_query is None:
        get_tweets_query = session_user.prepare("""
            SELECT * FROM tweets WHERE tweet_id=?
            """)

    # First we need to get the raw timeline (in the form of tweet ids)
    query = "SELECT time, tweet_id FROM {table} WHERE username=%s {time_clause} LIMIT %s"

    # See if we need to start our page at the beginning or further back
    if not start:
        time_clause = ''
        params = (username, limit)
    else:
        time_clause = 'AND time < %s'
        params = (username, UUID(start), limit)

    query = query.format(table=table, time_clause=time_clause)

    results = session_user.execute(query, params)
    if not results:
        return [], None

    # results = [row for row in results]

    # If we didn't get to the end, return a starting point for the next page
    if len(results.current_rows) == limit:
        # Find the oldest ID
        oldest_timeuuid = min(row.time for row in results)

        # Present the string version of the oldest_timeuuid for the UI
        next_timeuuid = oldest_timeuuid.urn[len('urn:uuid:'):]
    else:
        next_timeuuid = None

    # Now we fetch the tweets themselves
    futures = []
    for row in results:
        futures.append(session_user.execute_async(
            get_tweets_query, (row.tweet_id,)))

    tweets = [f.result()[0] for f in futures]
    return (tweets, next_timeuuid)


# QUERYING APIs

def get_user_by_username(username):
    """
    Given a username, this gets the user record.
    """
    global get_usernames_query
    if get_usernames_query is None:
        get_usernames_query = session_user.prepare("""
            SELECT * FROM users WHERE username=?
            """)

    rows = session_user.execute(get_usernames_query, (username,))
    if not rows:
        raise NotFound('User %s not found' % (username,))
    else:
        return rows[0]


def get_friend_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people that the user is
    following.
    """
    global get_friends_query
    if get_friends_query is None:
        get_friends_query = session_user.prepare("""
            SELECT friend FROM friends WHERE username=? LIMIT ?
            """)

    rows = session_user.execute(get_friends_query, (username, count))
    return [row.friend for row in rows]


def get_follower_usernames(username, count=5000):
    """
    Given a username, gets the usernames of the people following that user.
    """
    global get_followers_query
    if get_followers_query is None:
        get_followers_query = session_user.prepare("""
            SELECT follower FROM followers WHERE username=? LIMIT ?
            """)

    rows = session_user.execute(get_followers_query, (username, count))
    return [row.follower for row in rows]


def get_users_for_usernames(usernames):
    """
    Given a list of usernames, this gets the associated user object for each
    one.
    """
    global get_usernames_query
    if get_usernames_query is None:
        get_usernames_query = session_user.prepare("""
            SELECT * FROM users WHERE username=?
            """)

    futures = []
    for user in usernames:
        future = session_user.execute_async(get_usernames_query, (user, ))
        futures.append(future)

    users = []
    for user, future in zip(usernames, futures):
        results = future.result()
        if not results:
            raise NotFound('User %s not found' % (user,))
        users.append(results[0])

    return users


def get_followers(username, count=5000):
    """
    Given a username, gets the people following that user.
    """
    follower_usernames = get_follower_usernames(username, count=count)
    return get_users_for_usernames(follower_usernames)


def get_timeline(username, start=None, limit=40):
    """
    Given a username, get their tweet timeline (tweets from people they follow).
    """
    return _get_line("timeline", username, start, limit)


def get_userline(username, start=None, limit=40):
    """
    Given a username, get their userline (their tweets).
    """
    return _get_line("userline", username, start, limit)


def get_tweet(tweet_id):
    """
    Given a tweet id, this gets the entire tweet record.
    """
    global get_tweets_query
    if get_tweets_query is None:
        get_tweets_query = session_user.prepare("""
            SELECT * FROM tweets WHERE tweet_id=?
            """)

    results = session_user.execute(get_tweets_query, (tweet_id, ))
    if not results:
        raise NotFound('Tweet %s not found' % (tweet_id,))
    else:
        return results[0]


def get_tweets_for_tweet_ids(tweet_ids):
    """
    Given a list of tweet ids, this gets the associated tweet object for each
    one.
    """
    global get_tweets_query
    if get_tweets_query is None:
        get_tweets_query = session_user.prepare("""
            SELECT * FROM tweets WHERE tweet_id=?
            """)

    futures = []
    for tweet_id in tweet_ids:
        futures.append(session_user.execute_async(get_tweets_query, (tweet_id,)))

    tweets = []
    for tweet_id, future in zip(tweet_id, futures):
        result = future.result()
        if not result:
            raise NotFound('Tweet %s not found' % (tweet_id,))
        else:
            tweets.append(result[0])

    return tweets


# INSERTING APIs

def save_user(username, password):
    """
    Saves the user record.
    """
    global add_user_query
    if add_user_query is None:
        add_user_query = session_user.prepare("""
            INSERT INTO users (username, password)
            VALUES (?, ?)
            """)

    session_user.execute(add_user_query, (username, password))


def _timestamp_to_uuid(time_arg):
    # TODO: once this is in the python Cassandra driver, use that
    microseconds = int(time_arg * 1e6)
    timestamp = int(microseconds * 10) + 0x01b21dd213814000L

    time_low = timestamp & 0xffffffffL
    time_mid = (timestamp >> 32L) & 0xffffL
    time_hi_version = (timestamp >> 48L) & 0x0fffL

    rand_bits = random.getrandbits(8 + 8 + 48)
    clock_seq_low = rand_bits & 0xffL
    clock_seq_hi_variant = 0b10000000 | (0b00111111 & ((rand_bits & 0xff00L) >> 8))
    node = (rand_bits & 0xffffffffffff0000L) >> 16
    return UUID(
        fields=(time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node),
        version=1)


def save_tweet(tweet_id, username, tweet, timestamp=None):
    """
    Saves the tweet record.
    """

    global tweets_query
    global userline_query
    global timeline_query

    # Prepare the statements required for adding the tweet into the various timelines
    # Initialise only once, and then re-use by binding new values
    if tweets_query is None:
        tweets_query = session_user.prepare("""
            INSERT INTO tweets (tweet_id, username, body)
            VALUES (?, ?, ?)
            """)

    if userline_query is None:
        userline_query = session_user.prepare("""
            INSERT INTO userline (username, time, tweet_id)
            VALUES (?, ?, ?)
            """)

    if timeline_query is None:
        timeline_query = session_user.prepare("""
            INSERT INTO timeline (username, time, tweet_id)
            VALUES (?, ?, ?)
            """)

    if timestamp is None:
        now = uuid1()
    else:
        now = _timestamp_to_uuid(timestamp)

    # Insert the tweet
    session_user.execute(tweets_query, (tweet_id, username, tweet,))
    # Insert tweet into the user's timeline
    session_user.execute(userline_query, (username, now, tweet_id,))
    # Insert tweet into the public timeline
    session_user.execute(userline_query, (PUBLIC_USERLINE_KEY, now, tweet_id,))

    # Get the user's followers, and insert the tweet into all of their streams
    futures = []
    follower_usernames = [username] + get_follower_usernames(username)
    for follower_username in follower_usernames:
        futures.append(session_user.execute_async(
            timeline_query, (follower_username, now, tweet_id,)))

    for future in futures:
        future.result()


def add_friends(from_username, to_usernames):
    """
    Adds a friendship relationship from one user to some others.
    """
    global friends_query
    global followers_query

    if friends_query is None:
        friends_query = session_user.prepare("""
            INSERT INTO friends (username, friend, since)
            VALUES (?, ?, ?)
            """)

    if followers_query is None:
        followers_query = session_user.prepare("""
            INSERT INTO followers (username, follower, since)
            VALUES (?, ?, ?)
            """)

    now = datetime.utcnow()
    futures = []
    for to_user in to_usernames:
        # Start following user
        futures.append(session_user.execute_async(
            friends_query, (from_username, to_user, now,)))
        # Add yourself as a follower of the user
        futures.append(session_user.execute_async(
            followers_query, (to_user, from_username, now,)))

    for future in futures:
        future.result()


def remove_friends(from_username, to_usernames):
    """
    Removes a friendship relationship from one user to some others.
    """
    global remove_friends_query
    global remove_followers_query

    if remove_friends_query is None:
        remove_friends_query = session_user.prepare("""
            DELETE FROM friends WHERE username=? AND friend=?
            """)
    if remove_followers_query is None:
        remove_followers_query = session_user.prepare("""
            DELETE FROM followers WHERE username=? AND follower=?
            """)

    futures = []
    for to_user in to_usernames:
        futures.append(session_user.execute_async(
            remove_friends_query, (from_username, to_user,)))
        futures.append(session_user.execute_async(
            remove_followers_query, (to_user, from_username,)))

    for future in futures:
        future.result()



def get_all_games(count=5000):
    """
    Get all the games
    """
    global get_games_query
    if get_games_query is None:
        get_games_query = session_bingo.prepare("""
            SELECT 
                game_id, 
                start_time, 
                announcement_duration,
                is_active
            FROM games LIMIT ?
            """)

    rows = session_bingo.execute(get_games_query, (count,))
    return rows

def get_game_details(game_id):
    """
    Get all the games
    """
    global get_game_detail_query
    if get_game_detail_query is None:
        get_game_detail_query = session_bingo.prepare("""
            SELECT *
            FROM games 
            WHERE game_id = ? LIMIT 1
            """)
    results = session_bingo.execute(get_game_detail_query, (game_id,))

    if not results:
        raise NotFound('Tweet %s not found' % (game_id,))
    else:
        return results[0]

def create_game(created_by, game_id, start_time, 
    announcement_duration, end_time, no_of_players):
    """
    Create new Game
    """
    global game_query
    global game_announcement_query
    if game_query is None:

        game_query = session_bingo.prepare("""
            INSERT INTO games 
            (created_by, game_id, start_time, 
                announcement_duration, end_time, no_of_players, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """)


    if game_announcement_query is None:
        game_announcement_query = session_bingo.prepare("""
            INSERT INTO announcement 
            (game_id, announcement_time, number)
            VALUES (?, ?, ?)
            """)

    start_time = datetime.strptime(str(start_time), "%m/%d/%Y %I:%M %p")
    end_time = datetime.strptime(str(end_time), "%m/%d/%Y %I:%M:%S %p")
    announcement_duration = int(announcement_duration)
    session_bingo.execute_async(game_query, 
        (created_by, game_id, start_time, 
            announcement_duration, end_time, no_of_players, True, ))

    for row in number_genrator(game_id, 1, 100, start_time, announcement_duration):
        session_bingo.execute_async(game_announcement_query, row)


def get_announcement(game_id):
    """
    Get ticket announcement by time
    """
    current_time = datetime.now()
    global check_game_announcement
    if check_game_announcement is None:
        check_game_announcement = session_bingo.prepare("""
            SELECT number, announcement_time FROM announcement WHERE 
                game_id= ? and announcement_time <= ?
            """)

    results = session_bingo.execute(check_game_announcement, 
                                    (game_id, current_time))

    if results.current_rows:
        return [i.number for i in results.current_rows], results.current_rows[0].announcement_time
    else:
        return [], None

def create_ticket(game_id, user):
    """
    Create new ticket
    """
    global ticket_query
    global get_game_detail_query

    if get_game_detail_query is None:
        get_game_detail_query = session_bingo.prepare("""
            SELECT *
            FROM games 
            WHERE game_id = ? LIMIT 1
            """)
    results = session_bingo.execute(get_game_detail_query, (game_id,))
    no_of_players = results.current_rows[0].no_of_players +1

    
    update_no_of_players_query = session_bingo.prepare("""
        UPDATE games 
        SET no_of_players = ? 
        WHERE game_id = ?  IF EXISTS;
        """)

    results = session_bingo.execute(update_no_of_players_query, 
                                    (no_of_players, game_id))

    if ticket_query is None:

        ticket_query = session_bingo.prepare("""
            INSERT INTO tickets 
            (game_id, user, a1, a2, a3, a4, a5, a6, a7, a8, a9, 
                b1, b2, b3, b4, b5, b6, b7, b8, b9,
                c1, c2, c3, c4, c5, c6, c7, c8, c9)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)

    ticket = ticket_genrator(1, 100)
    session_bingo.execute_async(ticket_query, (game_id, user, ticket[0], 
        ticket[1], ticket[2], ticket[3], ticket[4], ticket[5], ticket[6], 
        ticket[7], ticket[8], ticket[9], ticket[10], ticket[11], ticket[12], 
        ticket[13], ticket[14], ticket[15], ticket[16], ticket[17], ticket[18], 
        ticket[19], ticket[20], ticket[21], ticket[22], ticket[23], ticket[24], 
        ticket[25], ticket[26]))


def get_ticket(game_id, user):
    """
    Get ticket of an user
    """
    global get_ticket_query
    if get_ticket_query is None:
        get_ticket_query = session_bingo.prepare("""
            SELECT a1, a2, a3, a4, a5, a6, a7, a8, a9,
                   b1, b2, b3, b4, b5, b6, b7, b8, b9,
                   c1, c2, c3, c4, c5, c6, c7, c8, c9
            FROM tickets WHERE game_id = ?
            and user = ?
            """)

    results = session_bingo.execute(get_ticket_query, 
                                    (game_id, user))

    if results.current_rows:
        return results.current_rows[0]
    else:
        return []

def update_claim(game_id, user, claim_type):
    """
    update bingo claim
    """
    
    update_claim_query = session_bingo.prepare("""
        UPDATE games 
        SET """ + claim_type + """ = ? 
        WHERE game_id = ?  IF EXISTS;
        """)

    results = session_bingo.execute(update_claim_query, 
                                    (user, game_id))

    return results