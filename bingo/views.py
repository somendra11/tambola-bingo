import uuid
import json

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from library.decorator import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib import messages

from bingo.forms import CreateGameForm
from library.bingo_scripts import ticket_html_generator

from datetime import timedelta
from datetime import datetime

import cass

@login_required
def clicked_number(request, game_id, number):

    success = 0
    user = request.session['username']
    if game_id not in request.session:
        request.session[game_id] = { }

    game_dict = request.session[game_id]
    if user not in game_dict:
        game_dict[user] = {
            'checked': [],
            'ticket': [],
            'announcement': [],
        }

    user_dict = game_dict[user]
    to_check_set = set(user_dict['ticket']).intersection(set(user_dict['announcement']))
    number = int(number)
    if number in to_check_set:
        user_dict['checked'].append(number)
        success = 1

    game_dict[user] = user_dict
    request.session[game_id] = game_dict
    if success:
        return HttpResponse("success")
    else:
        return HttpResponse(str(game_dict))



def game_list(request):
    """Shows list of games available"""

    games = cass.get_all_games()
    context = {
        'games': games,
    }
    return render_to_response(
        'bingo/games.html', context, context_instance=RequestContext(request))

@login_required
def game(request, game_id):

    user = request.session['username']
    if game_id not in request.session:
        request.session[game_id] = { }

    game_dict = request.session[game_id]
    if user not in game_dict:
        game_dict[user] = {
            'checked': [],
            'ticket': [],
            'announcement': [],
        }

    user_dict = game_dict[user]
    try:
        game_uuid = uuid.UUID(game_id)
        game = cass.get_game_details(game_uuid)
        announcement, announcement_time = cass.get_announcement(game_uuid)
        user_dict['announcement'] = announcement

    except Exception:
        context = {
            'error': "No Game Found",
            'game_id': game_id,
        }
    else:
        data = {
            'user': user,
            'game_id': game_uuid,
        }
        if not user_dict['ticket']:
            ticket = cass.get_ticket(**data)
            user_dict['ticket'] = list(ticket)
        else:
            ticket = user_dict['ticket']
        ticket_table = ticket_html_generator(ticket, user_dict)
        announcement_list = ", ".join(str(i) for i in announcement[1:])

        refresh_time = None
        if len(announcement) < 99:
            if announcement_time:
                next_announcement = announcement_time + timedelta(seconds=game.announcement_duration)
            else:
                next_announcement = game.start_time
            cur_time = datetime.now()
            print next_announcement, cur_time
            if next_announcement > cur_time:
                refresh_time = next_announcement - cur_time
                refresh_time = refresh_time.seconds * 1000
            if not refresh_time:
                refresh_time = game.announcement_duration * 1000

        context = {
            'message': messages.get_messages(request),
            'ticket': ticket_table,
            'game': game,
            'announcement': announcement_list if announcement_list else "None",
            'last_announcement': announcement[0] if announcement else "None",
            'game_id': game_id,
            'refresh_time': refresh_time,
        }

    game_dict[user] = user_dict
    request.session[game_id] = game_dict
    return render_to_response(
        'bingo/game.html',
        context,
        context_instance=RequestContext(request))

@login_required
def claim(request, game_id, claim_type):

    claims = {
        "four_corners": None,
        "top_row": None,
        "middle_row": None,
        "bottom_row": None,
        "full_house": None
    }
    user = request.session['username']
    try:
        game_uuid = uuid.UUID(game_id)
        game = cass.get_game_details(game_uuid)
        announcement, _ = cass.get_announcement(game_uuid)
        announcement = set(announcement)
        ticket = cass.get_ticket(game_uuid, user)
        ticket = [i for i in ticket if i]


    except Exception:
        pass
    else:
        claims['four_corners'] = game.four_corners
        claims['top_row'] = game.top_row
        claims['middle_row'] = game.middle_row
        claims['bottom_row'] = game.bottom_row
        claims['full_house'] = game.full_house
        claim_types = {'four_corners', 'top_row',
                'middle_row', 'bottom_row', 'full_house'}

        if ticket and claim_type == 'four_corners' and not claims.get(claim_type):
            corners = set([ticket[0], ticket[4], ticket[10], ticket[14]])
            if not corners - announcement:
                if cass.update_claim(game_uuid, user, claim_type):
                    claims[claim_type] = user
        elif ticket and claim_type == 'top_row' and not claims.get(claim_type):
            if not set(ticket[:5]) - announcement:
                if cass.update_claim(game_uuid, user, claim_type):
                    claims[claim_type] = user
        elif ticket and claim_type == 'middle_row' and not claims.get(claim_type):
            if not set(ticket[5:10]) - announcement:
                if cass.update_claim(game_uuid, user, claim_type):
                    claims[claim_type] = user
        elif ticket and claim_type == 'bottom_row' and not claims.get(claim_type):
            if not set(ticket[10:]) - announcement:
                if cass.update_claim(game_uuid, user, claim_type):
                    claims[claim_type] = user
        elif ticket and claim_type == 'full_house' and not claims.get(claim_type):
            if not set(ticket) - announcement:
                if cass.update_claim(game_uuid, user, claim_type):
                    claims[claim_type] = user


    return HttpResponse(json.dumps(claims),
                        content_type="application/json")


@login_required
def create_game(request):

    form = CreateGameForm(request.POST or None)
    if form.is_valid():
        game_id = uuid.uuid4()
        no_of_players = 0
        data = {
            'created_by': request.session['username'],
            'game_id': game_id,
            'start_time': form.cleaned_data['start_time'],
            'announcement_duration': form.cleaned_data['announcement_duration'],
            'end_time': form.cleaned_data['finishing_time'],
            'no_of_players': no_of_players,
        }
        cass.create_game(**data)
        return HttpResponseRedirect(reverse('game_list'))
    context = {
        'form': form,
        'request': request.POST,
    }
    return render_to_response(
        'bingo/create_game.html', context, context_instance=RequestContext(request))



@login_required
def create_ticket(request, game_id):

    try:
        game_id = uuid.UUID(game_id)
    except Exception:
        return HttpResponseRedirect(reverse('game', kwargs={'game_id': game_id}))
    user = request.session['username']
    data = {
        'user': user,
        'game_id': game_id,
    }
    ticket = cass.get_ticket(**data)
    if ticket:
        messages.add_message(request, messages.INFO, "Ticket Already exists.")
    else:
        ticket = cass.create_ticket(**data)
    return HttpResponseRedirect(reverse('game', kwargs={'game_id': game_id}))
