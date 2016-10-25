from random import shuffle
from datetime import timedelta

def number_genrator(game_id, min_no, max_no, start_time, duration_gap): 
    no_list = range(min_no, max_no) 
    shuffle(no_list) 
    time_list = [start_time + timedelta(seconds=i) 
                 for i in xrange(0, duration_gap*(max_no-min_no), duration_gap)]
    game_id = [game_id for _ in xrange(min_no, max_no)]
    return zip(game_id, time_list, no_list)


def ticket_genrator(min_no, max_no):

    no_list = range(min_no, max_no)
    shuffle(no_list)
    ticket = [[None, None, None, None], 
              [None, None, None, None], 
              [None, None, None, None]] 
    for i in xrange(3): 
        for j in xrange(5): 
            ticket[i].append(no_list[i*5+j]) 
            shuffle(ticket[i]) 
    flat_ticket = sum(ticket, []) 
    return flat_ticket

def ticket_html_generator(ticket, user_dict):

    clicked_num_set = set(user_dict['checked'])
    ticket_table = ""
    if ticket:
        ticket_table = "<tr>"
        for i in ticket[:9]:
            if not i:
                ticket_table += '<td class="ticket-table missing-number">'
                ticket_table += "&nbsp;&nbsp;</td>"
            elif i in clicked_num_set:
                ticket_table += '<td class="ticket-table checked-number">'
                ticket_table += str(i)+"</td>"
            else:
                ticket_table += '<td class="ticket-table unchecked-number">'
                ticket_table += str(i)+"</td>"
        ticket_table += "</tr>"
        ticket_table += "<tr>"
        for i in ticket[9:18]:
            if not i:
                ticket_table += '<td class="ticket-table missing-number">'
                ticket_table += "&nbsp;&nbsp;</td>"
            elif i in clicked_num_set:
                ticket_table += '<td class="ticket-table checked-number">'
                ticket_table += str(i)+"</td>"
            else:
                ticket_table += '<td class="ticket-table unchecked-number">'
                ticket_table += str(i)+"</td>"
        ticket_table += "</tr>"
        ticket_table += "<tr>"
        for i in ticket[18:27]:
            if not i:
                ticket_table += '<td class="ticket-table missing-number">'
                ticket_table += "&nbsp;&nbsp;</td>"
            elif i in clicked_num_set:
                ticket_table += '<td class="ticket-table checked-number">'
                ticket_table += str(i)+"</td>"
            else:
                ticket_table += '<td class="ticket-table unchecked-number">'
                ticket_table += str(i)+"</td>"
        ticket_table += "</tr>"
    return ticket_table