import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
import datetime
import json
from tornado.options import define, options
import random
import time

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", LoginHandler),
            (r"/lobby.html", LobbyHandler),
            (r"/main.html", MainHandler),
            (r"/loginsocket", LoginSocketHandler),
            (r"/lobbysocket", LobbySocketHandler),
            (r"/mainsocket", MainSocketHandler),
        ]
        settings = dict(
            cookie_secret="Oatmeal_Pistachio_Butterscotch_Rum_Raisin",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
class LoginHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
class LoginSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    usernames = []
    def open(self):
        LoginSocketHandler.waiters.add(self)
    def on_close(self):
        LoginSocketHandler.waiters.remove(self)
    def on_message(self,message):
        username = tornado.escape.json_decode(message)['username']
        if username in self.usernames:
            self.raise_issue()
        elif username=="message" or username=="_xsrf":
            self.raise_issue()
        else:
            self.usernames.append(username)
            self.move_to_lobby(username)
    def raise_issue(self):
        self.write_message({"id": str(uuid.uuid4()), "message": "username_taken"})
    def move_to_lobby(self,username):
        self.write_message({"id": str(uuid.uuid4()), "message": "username_accepted", "username": username})
class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_secure_cookie("username",self.get_argument("name"))
        self.render("lobby.html")
class LobbySocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    challenges = []
    challenges_accepted = []
    def open(self):
        LobbySocketHandler.waiters.add(self)
        self.username = self.get_secure_cookie("username")
    def on_close(self):
        LoginSocketHandler.usernames.remove(self.username)
        LobbySocketHandler.waiters.remove(self)
        self.update_usernames()
    def on_message(self,message):
        parsed = tornado.escape.json_decode(message)
        if parsed['message'] == "request_usernames":
            self.update_usernames()
        elif parsed['message'] == "request_own_name":
            self.write_message({"id": str(uuid.uuid4()), "message": "sending_name", "name": self.get_secure_cookie("username")})
        elif parsed['message'] == "challenge":
            users = []
            accepted = []
            users.append(self.username)
            accepted.append(True)
            for i in parsed:
                if  i!="message" and i!="_xsrf":
                    users.append(i)
                    accepted.append(False)
            for i in users:
                for j in self.waiters:
                    if i==j.username:
                        j.write_message({"id": str(uuid.uuid4()), "message": "challenge2", "usernames": users, "challenge_number": len(self.challenges)})
            self.challenges.append(users)
            self.challenges_accepted.append(accepted)
        elif parsed['message'] == "challenge3a":
            challenge_number = int(parsed['challenge_number'])
            for i in range(0,len(self.challenges[challenge_number])):
                if self.challenges[challenge_number][i]==self.username:
                    self.challenges_accepted[challenge_number][i]=True
            challenge_ready = True
            for i in self.challenges_accepted[challenge_number]:
                if i==False:
                    challenge_ready = False
            if challenge_ready == True:
                for waiter in self.waiters:
                    if waiter.username in self.challenges[challenge_number]:
                        waiter.write_message({"id": str(uuid.uuid4()), "message": "game_ready", "game_number": str(challenge_number)})
        elif parsed['message'] == "challenge3b":
            challenge_number = int(parsed['challenge_number'])
            for i in range(0,len(self.challenges[challenge_number])):
                if self.challenges[challenge_number][i]==self.username:
                    self.challenges_accepted[challenge_number][i]=False
    def update_usernames(self):
        for waiter in self.waiters:
            waiter.write_message({"id": str(uuid.uuid4()), "message": "usernames_updated", "usernames": LoginSocketHandler.usernames})
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_secure_cookie("game_id",self.get_argument("id"))
        self.render("main.html")
class MainSocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    game_numbers = []
    games = []
    def open(self):
        MainSocketHandler.waiters.add(self)
        self.username = self.get_secure_cookie("username")
        self.game_id = self.get_secure_cookie("game_id")
        if self.game_id not in self.game_numbers:
            self.game_numbers.append(self.game_id)
            self.game = Game(self.game_id)
            self.games.append(self.game)
            tornado.ioloop.IOLoop.current().add_timeout(datetime.timedelta(seconds=1),self.start_game)
        else:
            for i in self.games:
                if i.game_id==self.game_id:
                    self.game=i
        self.message_queue = []
        self.ready=True
    def on_close(self):
        MainSocketHandler.waiters.remove(self)
    def on_message(self,message):
        parsed = tornado.escape.json_decode(message)
        if parsed['message']=='tile_position_selected':
            self.game.tile_position_selected(parsed)
        elif parsed['message']=='tile_rotation_selected':
            self.game.tile_rotation_selected(parsed)
        elif parsed['message']=='return_turn_end':
            self.game.beginning_of_turn()
        elif parsed['message']=='worker_placed':
            self.game.worker_placed(parsed)
        elif parsed['message']=='update_finished':
            self.ready=True
            if len(self.message_queue)>0:
                self.ready=False
                self.write_message(self.message_queue.pop(0))
        elif parsed['message']=='request_update':
            self.game.push_update(self)
        elif parsed['message']=='next_event':
            self.game.next_event()
        elif parsed['message']=='city_delivery_position_selected':
            self.game.bring_city_online_selected(self,parsed)
        elif parsed['message']=='construct_worker_confirmed':
            self.game.construct_worker_confirmed(self)
        elif parsed['message']=='build_upgrade_confirmed':
            self.game.build_upgrade_confirmed(self)
        elif parsed['message']=='upgrade_selected':
            self.game.upgrade_selected(self,parsed)
        elif parsed['message']=='upgrade_location_selected':
            self.game.upgrade_location_selected(self,parsed)
        elif parsed['message']=='spent_freely':
            if parsed['type']=='bring_city_online':
                self.game.bring_city_online_spent(self,parsed)
            elif parsed['type']=='construct_worker':
                self.game.construct_worker_spent(self)
    def start_game(self):
        self.game.start()
    def write_message2(self,message):
        self.message_queue.append(message)
        if self.ready==True:
            self.ready=False
            self.write_message(self.message_queue.pop(0))
class Game():
    waiters = []
    def __init__(self,game_id):
        self.game_id = game_id
        self.ready = False
    def start(self):
        for i in MainSocketHandler.waiters:
            if i.game_id==self.game_id:
                self.waiters.append(i)
        random.shuffle(self.waiters)
        self.tile_types = self.initiate_tile_types()
        self.upgrade_types = self.initiate_upgrade_types()
        self.upgrades_available = [True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,
                                   True,True,True,True,True,True,True,True,True,True,True,True,True,True,True,True]
        temp_tiles = []
        for i in range(14):
            a = Tile()
            a.tile_type = 0
            temp_tiles.append(a)
        for i in range(14):
            a = Tile()
            a.tile_type = 1
            temp_tiles.append(a)
        for i in range(3):
            a = Tile()
            a.tile_type = 2
            temp_tiles.append(a)
        for i in range(3):
            a = Tile()
            a.tile_type = 3
            temp_tiles.append(a)
        for i in range(4):
            a = Tile()
            a.tile_type = 4
            temp_tiles.append(a)
        for i in range(2):
            a = Tile()
            a.tile_type = 5
            temp_tiles.append(a)
        for i in range(2):
            a = Tile()
            a.tile_type = 6
            temp_tiles.append(a)
        for i in range(4):
            a = Tile()
            a.tile_type = 7
            temp_tiles.append(a)
        for i in range(4):
            a = Tile()
            a.tile_type = 8
            temp_tiles.append(a)
        for i in range(7):
            a = Tile()
            a.tile_type = 9
            temp_tiles.append(a)
        for i in range(7):
            a = Tile()
            a.tile_type = 10
            temp_tiles.append(a)
        for i in range(11,19):
            a = Tile()
            a.tile_type = i
            temp_tiles.append(a)
        random.shuffle(temp_tiles)
        self.stack_tiles = temp_tiles

        temp_tiles = []
        for i in range(30):
            temp_row = []
            for j in range(30):
                temp_row.append(None)
            temp_tiles.append(temp_row)
        a = Tile()
        a.tile_type = 19
        temp_tiles[9][8]=a
        a = Tile()
        a.tile_type = 20
        temp_tiles[10][8]=a
        a = Tile()
        a.tile_type = 21
        temp_tiles[11][8]=a
        a = Tile()
        a.tile_type = 22
        temp_tiles[9][9]=a
        a = Tile()
        a.tile_type = 23
        temp_tiles[10][9]=a
        a = Tile()
        a.tile_type = 24
        temp_tiles[11][9]=a
        a = Tile()
        a.tile_type = 25
        temp_tiles[9][10]=a
        a = Tile()
        a.tile_type = 26
        temp_tiles[10][10]=a
        a = Tile()
        a.tile_type = 1
        a.city_online_status=2 #TEMP
        temp_tiles[11][10]=a
        a.tile_orientation = 2
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 1
        a.city_online_status=2 #TEMP
        temp_tiles[9][11]=a
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 3
        a.city_online_status=2 #TEMP
        temp_tiles[10][11]=a
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 0
        a.city_online_status=2 #TEMP
        temp_tiles[11][11]=a
        for i in range(30):
            for j in range(30):
                if temp_tiles[i][j]!=None:
                    temp_tiles[i][j].x=i
                    temp_tiles[i][j].y=j
        self.table_tiles = temp_tiles
        
        self.players = []
        for i in range(0,len(self.waiters)):
            a = Player()
            if i==0:
                a.is_first_player=True
                a.is_turn_to_place=True
            a.handler = self.waiters[i]
            self.players.append(a)
        self.ready=True
        self.event_queue = []
        self.event_queue_args = []
        self.game_over=False
        self.beginning_of_turn()
    def beginning_of_turn(self):
        self.switch_start_player()
        self.check_for_endgame()
        if not self.game_over:
            self.beginning_of_turn_phase()
            self.tile_number=1
            # self.lay_tiles()
            # TEMPORARY MEASURE TO MAKE TESTING FASTER (uncomment and comment out line above):
            self.stock_resources()
            self.lay_workers()
    def check_for_endgame(self):
        if len(self.stack_tiles)==0:
            self.endgame()
    def beginning_of_turn_phase(self):
        for i in range(0,32):
            if self.upgrades_available[i]==False:
                self.trigger_upgrade_on_turn_begins(i)
    def switch_start_player(self):
        first_player=0
        for i in range(len(self.players)):
            if self.players[i].is_first_player==True:
                first_player=i
        first_player+=1
        if first_player>=len(self.players):
            first_player=0
        for i in range(len(self.players)):
            if first_player==i:
                self.players[i].is_first_player=True
            else:
                self.players[i].is_first_player=False
    def not_ready(self):
        for waiter in self.waiters:
            if waiter.ready==False:
                return True
        return False
    def lay_tiles(self):
        self.push_updates()
        for i in self.players:
            if i.is_first_player==True:
                self.push_message(i,"Place the tile as desired.")
                tile=self.stack_tiles.pop()
                self.push_tile_lay(i,tile,True)
        for i in self.players:
            if i.is_first_player==False:
                self.push_message(i,"Other player laying tiles.")
                self.push_tile_lay(i,tile,False)
    def push_updates(self):
        if self.ready==True:
            for waiter in self.waiters:
                waiter.write_message2({"id": str(uuid.uuid4()), "message": "push_update", "upgrades_available": self.upgrades_available, "table_tiles": serialize_2d_list(self.table_tiles),
                                      "players": serialize_list(self.players),"username": waiter.username, "stack_tiles": len(self.stack_tiles)})
    def push_update(self,client):
        if self.ready==True:
            client.write_message2({"id": str(uuid.uuid4()), "message": "push_update", "upgrades_available": self.upgrades_available, "table_tiles": serialize_2d_list(self.table_tiles),
                                  "players": serialize_list(self.players),"username": client.username, "stack_tiles": len(self.stack_tiles)})
    def push_message(self,client,message):
        client.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_message", "text": message})
    def push_tile_lay(self,client,tile,active):
        client.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_tile_lay", "tile": tile.to_JSON(), "active": active})
    def tile_position_selected(self,message):
        message['message'] = 'push_tile_rotate'
        for i in self.players:
            if i.is_first_player==True:
                self.push_message(i,"Rotate the tile as desired.")
                i.handler.write_message2(message)
    def tile_rotation_selected(self,message):
        x = message['x']
        y = message['y']
        tile = Tile()
        tile.from_JSON(message['tile'])
        for i in self.players:
            if i.is_first_player==True:
                first_player = i
        if self.table_tiles[x][y]!=None:
            self.push_relay_tiles(first_player,tile)
            return
        if self.check_for_adjacent_tiles(tile,x,y)==False:
            self.push_relay_tiles(first_player,tile)
            return
        if self.check_connections(tile,x,y)==False:
            self.push_relay_tiles(first_player,tile)
            return
        if x>29 or y>29:
            self.push_relay_tiles(first_player,tile)
            return
        tile.x=x
        tile.y=y
        self.table_tiles[x][y]=tile
        region = self.get_region(x,y)
        if tile.tile_type >= 11:
            if self.count_cornerstones(region)>1:
                self.table_tiles[x][y]=None
                self.push_relay_tiles(first_player,tile)
                return
        if tile.tile_type in [0,2,4,5,6,7,9,11,12,13,14,15,16,17,18]:
            if self.region_closed(region):
                if self.count_cornerstones(region)==0:
                    self.table_tiles[x][y]=None
                    self.push_relay_tiles(first_player,tile)
                    return
        self.tile_number+=1
        if self.tile_number<=4:
            self.lay_tiles()
        else:
            self.stock_resources()
            self.lay_workers()
    def worker_placed(self,message):
        x = int(message['x'])
        y = int(message['y'])
        tile = self.table_tiles[x][y]
        for i in self.players:
            if i.is_first_player==True:
                first_player = i
        if tile==None:
            self.push_relay_worker(first_player)
            return
        type = tile.tile_type
        if type==0 or type==2 or type==3 or type==4 or type==5 or type==6 or type==7 or type==9 or type>=11:
            if self.region_closed(self.get_region(x,y))==True:
                if tile.worker_placed==-1:
                    tile.worker_placed = self.worker_turn
                    self.rotate_worker_turn()
                    if self.worker_turn!=-1:
                        self.push_updates()
                        for i in range(len(self.players)):
                            if i==self.worker_turn:
                                self.push_message(self.players[i],"Place your robot.")
                                self.players[i].workers_remaining-=1
                                self.push_worker_lay(self.players[i],True)
                            else:
                                self.push_message(self.players[i],"Other player placing robot.")
                                self.push_worker_lay(self.players[i],False)
                        return
                    else:
                        # self.push_turn_end(first_player)
                        self.worker_pickup()
                        return
        self.push_relay_worker(first_player)
    def worker_pickup(self):
        for i in self.players:
            if i.is_first_player==True:
                first_player = i
        cornerstones = self.get_cornerstones()
        regions = self.get_regions(cornerstones)
        for j in range(1,5):
            for i in regions:
                workers=self.get_workers_placed(i)
                if workers!=None:
                    self.remove_workers(i,j)
        for i in self.table_tiles:
            for j in i:
                if j != None:
                    j.worker_placed=-1
        self.next_event()
    def next_event(self):
        for i in self.players:
            if i.is_first_player==True:
                first_player = i
        if self.event_queue == []:
            self.push_updates()
            self.push_turn_end(first_player)
        else:
            self.event_queue.pop(0)(self.event_queue_args.pop(0))
    def get_workers_placed(self,region):
        workers = []
        for player in self.players:
            workers.append(0)
        for tile in region:
            if tile!=None:
                workers[tile.worker_placed]+=1
        return workers
    def remove_workers(self,region,type):
        workers = self.get_workers_placed(region)
        if sum(workers)==0:
            return
        if type==1:
            electricity,water,information,metal,rare_metal=self.get_resources(region)
            for i in region:
                i.electricity=0
                i.water=0
                i.information=0
                i.metal=0
                i.rare_metal=0
            for i in range(len(self.players)):
                self.players[i].electricity+=workers[i]*(electricity/sum(workers))
                self.players[i].water+=workers[i]*(water/sum(workers))
                self.players[i].information+=workers[i]*(information/sum(workers))
                self.players[i].metal+=workers[i]*(metal/sum(workers))
                self.players[i].rare_metal+=workers[i]*(rare_metal/sum(workers))
            region[0].electricity=electricity%(sum(workers))
            region[0].water=water%(sum(workers))
            region[0].information=information%(sum(workers))
            region[0].metal=metal%(sum(workers))
            region[0].rare_metal=rare_metal%(sum(workers))
        elif type==2:
            for j in range(len(self.players)):
                if self.players[j].is_first_player==True:
                    first_player = j
            i=-1
            while i!=first_player:
                if i==-1:
                    i=first_player
                if workers[i]>0:
                    for tile in region:
                        if tile.tile_type in [12,20]:
                            self.event_queue.append(self.bring_city_online)
                            self.event_queue_args.append(i)
                i+=1
                if i==len(self.players):
                    i=0
        elif type==3:
            for j in range(len(self.players)):
                if self.players[j].is_first_player==True:
                    first_player = j
            i=-1
            while i!=first_player:
                if i==-1:
                    i=first_player
                if workers[i]>0:
                    for tile in region:
                        if tile.tile_type in [13,21]:
                            self.event_queue.append(self.build_upgrade)
                            self.event_queue_args.append(i)
                i+=1
                if i==len(self.players):
                    i=0
        elif type==4:
            for j in range(len(self.players)):
                if self.players[j].is_first_player==True:
                    first_player = j
            i=-1
            while i!=first_player:
                if i==-1:
                    i=first_player
                if workers[i]>0:
                    for tile in region:
                        if tile.tile_type in [11,19]:
                            self.event_queue.append(self.construct_worker)
                            self.event_queue_args.append(i)
                i+=1
                if i==len(self.players):
                    i=0
    def get_workers_placed(self,region):
        workers = []
        for i in self.players:
            workers.append(0)
        for tile in region:
            if tile!=None and (tile.worker_placed)>-1:
                workers[tile.worker_placed]+=1
        return workers
    def bring_city_online(self,player_num):
        player = self.players[player_num]
        if (player.electricity+player.water+player.information+player.metal+player.rare_metal)<5:
            return
        if (self.cities_to_be_brought_online()==False):
            return
        for i in self.players:
            if i!=player:
                self.push_message(i,'Other player bringing city online.')
            else:
                self.push_dialog(i,'bring_city_online','Would you like to bring a city tile online?')
    def construct_worker(self,player_num):
        player = self.players[player_num]
        if (player.electricity+player.water+player.information+player.metal+player.rare_metal)<20:
            return
        if player.total_workers>=5:
            return
        for i in self.players:
            if i!=player:
                self.push_message(i,'Other player choosing whether or not to construct a robot.')
            else:
                self.push_dialog(i,'construct_worker','Would you like to build a robot?')
    def build_upgrade(self,player_num):
        player = self.players[player_num]
        if (player.electricity+player.water+player.information+player.metal+player.rare_metal==0):
            return
        for i in self.players:
            if i!=player:
                self.push_message(i,'Other player building an upgrade.')
            else:
                self.push_dialog(i,'build_upgrade','Would you like to build an upgrade?')
    def build_upgrade_confirmed(self,handler):
        for participant in self.players:
            if participant.handler==handler:
                player=participant
        player.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_upgrade_select"})
    def upgrade_selected(self,handler,message):
        for participant in self.players:
            if participant.handler==handler:
                player=participant
        for i in range(len(self.players)):
            if self.players[i]==player:
                player_num=i
        upgrade_id=int(message['upgrade_id'])
        if upgrade_id==13 and player.vp==0:
            self.build_upgrade(player_num)
            return
        elif self.upgrade_costs_not_met(player,upgrade_id):
            self.build_upgrade(player_num)
            return
        self.push_message(player,'Select a spot to build the upgrade.')
        player.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_upgrade_location_select", "upgrade_id": upgrade_id})
    def upgrade_location_selected(self,handler,message):
        upgrade_id=int(message['upgrade_id'])
        for participant in self.players:
            if participant.handler==handler:
                player=participant
        for i in range(len(self.players)):
            if self.players[i]==player:
                player_num=i
        if not self.pay_upgrade_cost(upgrade_id,player_num):
            self.build_upgrade(player_num)
            return
        for participant in self.players:
            if participant.handler==handler:
                player=participant
        for i in range(len(self.players)):
            if self.players[i]==player:
                player_num=i
        x = int(message['x'])
        y = int(message['y'])
        if not self.table_tiles[x] or not self.table_tiles[x][y] or self.table_tiles[x][y].tile_type not in [1,3,4,5,6,8,10] or self.table_tiles[x][y].city_online_status!=2 or self.table_tiles[x][y].upgrade_built!=-1:
            self.build_upgrade(player_num)
        else:
            self.table_tiles[x][y].upgrade_built=upgrade_id
            self.table_tiles[x][y].upgrade_owner=player_num
            self.upgrades_available[upgrade_id]=False
            self.on_buy(player_num,upgrade_id)
            self.next_event()
    def pay_upgrade_cost(self,row,player_number):
        player = self.players[player_number]
        upgrade = self.upgrade_types[row]
        cost_increase = 0
        if self.upgrades_available[25]==False:
            if self.upgrade_owner_number(25)!=player_number:
                if self.upgrades_available[16]==True or (self.upgrades_available[16]==False and upgrade_owner_number(16)!=player_number):
                    cost_increase = get_highest_costed_resource(row)
        if cost_increase==1:
            upgrade.electricity+=1
        elif cost_increase==2:
            upgrade.water+=1
        elif cost_increase==3:
            upgrade.information+=1
        elif cost_increase==4:
            upgrade.metal+=1
        elif cost_increase==5:
            upgrade.rare_metal+=1
        returnValue = True
        if player.electricity<upgrade.electricity:
            returnValue = False
        if player.water<upgrade.water:
            returnValue = False
        if player.information<upgrade.information:
            returnValue = False
        if player.metal<upgrade.metal:
            returnValue = False
        if player.rare_metal<upgrade.rare_metal:
            returnValue = False
        if returnValue == False:
            if cost_increase==1:
                upgrade.electricity-=1
            elif cost_increase==2:
                upgrade.water-=1
            elif cost_increase==3:
                upgrade.information-=1
            elif cost_increase==4:
                upgrade.metal-=1
            elif cost_increase==5:
                upgrade.rare_metal-=1
            return False
        if self.upgrades_available[10]==False:
            if self.upgrade_owner_number(10)==player_number:
                if upgrade.electricity>1 or upgrade.water>1 or upgrade.information>1 or upgrade.metal>1 or upgrade.rare_metal>1:
                    x = self.select_resource("Choose a resource to discount on upgrade purchase:",(player.electricity,player.water,player.information,player.metal,player.rare_metal))
                    while x==0 or (x==1 and upgrade.electricity<2) or (x==2 and upgrade.water<2) or (x==3 and upgrade.information<2) or (x==4 and upgrade.metal<2) or (x==5 and upgrade.rare_metal<2):
                        x = self.select_resource("Choose a resource to discount on upgrade purchase:",(player.electricity,player.water,player.information,player.metal,player.rare_metal))
                    if x==1:
                        player.electricity+=1
                    elif x==2:
                        player.water+=1
                    elif x==3:
                        player.information+=1
                    elif x==4:
                        player.metal+=1
                    elif x==5:
                        player.rare_metal+=1
        player.electricity-=upgrade.electricity
        player.water-=upgrade.water
        player.information-=upgrade.information
        player.metal-=upgrade.metal
        player.rare_metal-=upgrade.rare_metal
        if cost_increase==1:
            upgrade.electricity-=1
        elif cost_increase==2:
            upgrade.water-=1
        elif cost_increase==3:
            upgrade.information-=1
        elif cost_increase==4:
            upgrade.metal-=1
        elif cost_increase==5:
            upgrade.rare_metal-=1
        return True
    def upgrade_costs_not_met(self,player,upgrade_id):
        upgrade = self.upgrade_types[upgrade_id]
        cost_increase = 0
        if self.upgrades_available[25]==False:
            if self.upgrade_owner_number(25)!=player_number:
                if game_state.upgrades_available[16]==True or (game_state.upgrades_available[16]==False and upgrade_owner_number(16)!=player_number):
                    cost_increase = self.get_highest_costed_resource(row)
        if cost_increase==1:
            upgrade.electricity+=1
        elif cost_increase==2:
            upgrade.water+=1
        elif cost_increase==3:
            upgrade.information+=1
        elif cost_increase==4:
            upgrade.metal+=1
        elif cost_increase==5:
            upgrade.rare_metal+=1
        returnValue=False
        if player.electricity<upgrade.electricity:
            returnValue=True
        if player.water<upgrade.water:
            returnValue=True
        if player.information<upgrade.information:
            returnValue=True
        if player.metal<upgrade.metal:
            returnValue=True
        if player.rare_metal<upgrade.rare_metal:
            returnValue=True
        if cost_increase==1:
            upgrade.electricity-=1
        elif cost_increase==2:
            upgrade.water-=1
        elif cost_increase==3:
            upgrade.information-=1
        elif cost_increase==4:
            upgrade.metal-=1
        elif cost_increase==5:
            upgrade.rare_metal-=1
        return returnValue
    def upgrade_owner_number(self,upgrade):
        x,y = get_upgrade_location(upgrade)
        if self.table_tiles[x] and self.table_tiles[x][y]:
            return self.table_tiles[x][y].upgrade_owner
    def get_upgrade_location(self,upgrade):
        x=-1
        y=-1
        for row in self.table_tiles:
            for tile in row:
                if tile and tile.upgrade_built==upgrade:
                    x = tile.x
                    y = tile.y
        return (x,y)
    def get_highest_costed_resource(self,upgrade):
        if upgrade<=7:
            return 2
        elif upgrade>=8 and upgrade<=15:
            return 1
        elif upgrade>=16 and upgrade<=23:
            return 3
        elif upgrade>=24:
            return 4
    def construct_worker_confirmed(self,handler):
        for participant in self.players:
            if participant.handler==handler:
                player=participant
        self.push_spend_freely(player,'Spend 20 to build a robot.',20,'construct_worker')
    def construct_worker_spent(self,handler):
        for participant in self.players:
            if participant.handler==handler:
                player = participant
        player.total_workers+=1
        self.next_event()
    def bring_city_online_selected(self,handler,message):
        for participant in self.players:
            if participant.handler==handler:
                player = participant
        for i in range(len(self.players)):
            if self.players[i]==player:
                player_num=i
        x = int(message['x'])
        y = int(message['y'])
        if self.table_tiles[x] and self.table_tiles[x][y] and self.table_tiles[x][y].tile_type in [1,3,4,5,6,8,10] and self.region_closed(self.get_city_region(x,y)) and self.table_tiles[x][y].city_online_status==0:
            self.x_selected = x
            self.y_selected = y
            self.push_spend_freely(player,'Spend 5 to bring a city tile online.',5,'bring_city_online')
        else:
            self.bring_city_online(player_num)
    def bring_city_online_spent(self,handler,message):
        for participant in self.players:
            if participant.handler==handler:
                player = participant
        for i in range(len(self.players)):
            if self.players[i]==player:
                player_num=i
        moving_to_upgrades=False
        self.table_tiles[self.x_selected][self.y_selected].city_online_status=1
        player.vp+=1
        player.electricity = int(message['electricity'])
        player.water = int(message['water'])
        player.information = int(message['information'])
        player.metal = int(message['metal'])
        player.rare_metal = int(message['rare_metal'])
        if self.entire_city_online(self.get_city_region(self.x_selected,self.y_selected)):
            player.vp+=1
            for tile in self.get_city_region(self.x_selected,self.y_selected):
                tile.city_online_status=2
            moving_to_upgrades=True
        self.push_updates()
        if moving_to_upgrades:
            self.build_upgrade(player_num)
        elif (player.electricity+player.water+player.information+player.metal+player.rare_metal)>=5 and self.cities_to_be_brought_online():
            self.bring_city_online(player_num)
        else:
            self.next_event()
    def entire_city_online(self,region):
        value = True
        for tile in region:
            if tile and tile.city_online_status==0:
                value=False
        return value
    def push_spend_freely(self,player,text,count,type):
        player.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_spend_freely", "text": text, "count": count, "type": type})
    def cities_to_be_brought_online(self):
        city_found=False
        for row in self.table_tiles:
            for tile in row:
                if tile!=None and tile.city_online_status==0 and tile.tile_type in [1,3,4,5,6,8,10] and self.region_closed(self.get_region(tile.x,tile.y)):
                    city_found=True
                    break
        return city_found
    def push_dialog(self,player,type,text):
        player.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_dialog", "type": type, "text": text})
    def get_resources(self,region):
        electricity=0
        water=0
        information=0
        metal=0
        rare_metal=0
        for i in region:
            if i.electricity!=None:
                electricity+=i.electricity
            if i.water!=None:
                water+=i.water
            if i.information!=None:
                information+=i.information
            if i.metal!=None:
                metal+=i.metal
            if i.rare_metal!=None:
                rare_metal+=i.rare_metal
        return (electricity,water,information,metal,rare_metal)
    def get_regions(self,cornerstones):
        regions = []
        if len(cornerstones)>0:
            for i in cornerstones:
                regions.append(self.get_region(i.x,i.y))
        return regions
    def push_relay_worker(self,first_player):
        self.push_message(first_player,"Place your robot.")
        self.push_worker_lay(first_player,True)
    def rotate_worker_turn(self):
        initial_worker_turn=self.worker_turn
        self.worker_turn+=1
        if self.worker_turn>=len(self.players):
            self.worker_turn=0
        while self.players[self.worker_turn].workers_remaining<1:
            self.worker_turn+=1
            if self.worker_turn>=len(self.players):
                self.worker_turn=0
            if self.worker_turn==initial_worker_turn and self.players[self.worker_turn].workers_remaining<1:
                self.worker_turn=-1
                break
    def lay_workers(self):
        for i in self.players:
            i.workers_remaining = i.total_workers
        self.push_updates()
        for i in range(len(self.players)):
            if self.players[i].is_first_player==True:
                self.worker_turn=i
        for i in self.players:
            if i.is_first_player==True:
                self.push_message(i,"Place your robot.")
                i.workers_remaining-=1
                self.push_worker_lay(i,True)
            else:
                self.push_message(i,"Other player placing robot.")
                self.push_worker_lay(i,False)
    def push_worker_lay(self,client,active):
        client.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_worker_lay", "active": active, "worker_turn": self.worker_turn})
    def stock_resources(self):
        cornerstones = self.get_cornerstones()
        regions = []
        if len(cornerstones)>0:
            for i in cornerstones:
                regions.append(self.get_region(i.x,i.y))
            for i in regions:
                self.fill_region(i)
    def get_cornerstones(self):
        cornerstones = []
        for i in self.table_tiles:
            for j in i:
                if j!=None and j.tile_type>10:
                    cornerstones.append(j)
        return cornerstones
    def fill_region(self,region):
        if self.region_closed(region):
            for i in region:
                if region[0].tile_type==14:
                    if i.electricity==None:
                        i.electricity=1
                    else:
                        i.electricity+=1
                elif region[0].tile_type==15:
                    if i.water==None:
                        i.water=1
                    else:
                        i.water+=1
                elif region[0].tile_type==16:
                    if i.information==None:
                        i.information=1
                    else:
                        i.information+=1
                elif region[0].tile_type==17:
                    if i.metal==None:
                        i.metal=1
                    else:
                        i.metal+=1
                elif region[0].tile_type==18:
                    if i.rare_metal==None:
                        i.rare_metal=1
                    else:
                        i.rare_metal+=1
                elif region[0].tile_type==22:
                    if i.electricity==None:
                        i.electricity=2
                    else:
                        i.electricity+=2
                elif region[0].tile_type==23:
                    if i.water==None:
                        i.water=2
                    else:
                        i.water+=2
                elif region[0].tile_type==24:
                    if i.information==None:
                        i.information=2
                    else:
                        i.information+=2
                elif region[0].tile_type==25:
                    if i.metal==None:
                        i.metal=2
                    else:
                        i.metal+=2
                elif region[0].tile_type==26:
                    if i.rare_metal==None:
                        i.rare_metal=2
                    else:
                        i.rare_metal+=2
    def push_turn_end(self,first_player):
        first_player.handler.write_message2({"id": str(uuid.uuid4()), "message": "push_turn_end"})
    def push_relay_tiles(self,first_player,tile):
        self.push_message(first_player,"Place the tile as desired.")
        self.push_tile_lay(first_player,tile,True)
    def check_for_adjacent_tiles(self,tile,x,y):
        if self.table_tiles[x-1][y]!=None or self.table_tiles[x+1][y]!=None or self.table_tiles[x][y-1]!=None or self.table_tiles[x][y+1]!=None:
            return True
        else:
            return False
    def check_connections(self,tile,x,y):
        rotated = self.get_rotated_tile_type(tile)
        if rotated.facility_connection[0]==True:
            if self.check_facility_connection(x,y-1,2)==False:
                return False
        if rotated.facility_connection[1]==True:
            if self.check_facility_connection(x+1,y,3)==False:
                return False
        if rotated.facility_connection[2]==True:
            if self.check_facility_connection(x,y+1,0)==False:
                return False
        if rotated.facility_connection[3]==True:
            if self.check_facility_connection(x-1,y,1)==False:
                return False
        if rotated.city_connection[0]==True:
            if self.check_city_connection(x,y-1,2)==False:
                return False
        if rotated.city_connection[1]==True:
            if self.check_city_connection(x+1,y,3)==False:
                return False
        if rotated.city_connection[2]==True:
            if self.check_city_connection(x,y+1,0)==False:
                return False
        if rotated.city_connection[3]==True:
            if self.check_city_connection(x-1,y,1)==False:
                return False
        if rotated.facility_connection[0]==False:
            if self.check_facility_connection(x,y-1,2)==True:
                if self.table_tiles[x][y-1]!=None:
                    return False
        if rotated.facility_connection[1]==False:
            if self.check_facility_connection(x+1,y,3)==True:
                if self.table_tiles[x+1][y]!=None:
                    return False
        if rotated.facility_connection[2]==False:
            if self.check_facility_connection(x,y+1,0)==True:
                if self.table_tiles[x][y+1]!=None:
                    return False
        if rotated.facility_connection[3]==False:
            if self.check_facility_connection(x-1,y,1)==True:
                if self.table_tiles[x-1][y]!=None:
                    return False
        if rotated.city_connection[0]==False:
            if self.check_city_connection(x,y-1,2)==True:
                if self.table_tiles[x][y-1]!=None:
                    return False
        if rotated.city_connection[1]==False:
            if self.check_city_connection(x+1,y,3)==True:
                if self.table_tiles[x+1][y]!=None:
                    return False
        if rotated.city_connection[2]==False:
            if self.check_city_connection(x,y+1,0)==True:
                if self.table_tiles[x][y+1]!=None:
                    return False
        if rotated.city_connection[3]==False:
            if self.check_city_connection(x-1,y,1)==True:
                if self.table_tiles[x-1][y]!=None:
                    return False
        return True
    def get_rotated_tile_type(self,tile):
        tile_type = TileType()
        base_tile_type = self.tile_types[tile.tile_type]
        for i in range(4):
            tile_type.facility_connection[i]=base_tile_type.facility_connection[self.get_rotation(i-tile.tile_orientation)]
            tile_type.city_connection[i]=base_tile_type.city_connection[self.get_rotation(i-tile.tile_orientation)]
        return tile_type
    def get_rotation(self,rotation):
        if rotation>=0 and rotation<=3:
            return rotation
        elif rotation>3:
            while rotation>3:
                rotation-=4
            return rotation
        elif rotation<0:
            while rotation<0:
                rotation+=4
            return rotation
    def check_facility_connection(self,x,y,side):
        tile = self.table_tiles[x][y]
        if tile==None:
            return True
        rotated = self.get_rotated_tile_type(tile)
        if rotated.facility_connection[side]==False:
            return False
        elif rotated.facility_connection[side]==True:
            return True
    def check_city_connection(self,x,y,side):
        tile = self.table_tiles[x][y]
        if tile==None:
            return True
        rotated = self.get_rotated_tile_type(tile)
        if rotated.city_connection[side]==False:
            return False
        elif rotated.city_connection[side]==True:
            return True
    def region_closed(self,region):
        if self.x_in_y(None,region)==True:
            return False
        else:
            return True
    def count_cornerstones(self,region):
        count=0
        for i in region:
            if self.is_cornerstone(i)==True:
                count+=1
        return count
    def x_in_y(self,x,y):
        value = False
        for i in y:
            if i==x:
                value = True
        return value
    def is_cornerstone(self,tile):
        if tile and tile.tile_type>=11:
            return True
        else:
            return False
    def get_region(self,x,y):
        region = self.get_connected([self.table_tiles[x][y]])
        return region
    def get_connected(self,connected):
        if connected!=None:
            for i in connected:
                if i!=None:
                    for j in self.get_immediately_connected(i):
                        if self.x_in_y (j,connected)==False:
                            connected.append(j)
        return connected
    def get_immediately_connected(self,tile):
        connected = []
        x=tile.x
        y=tile.y
        theoretical_tile = self.get_rotated_tile_type(tile)
        if theoretical_tile.facility_connection[0]==True:
            connected.append(self.table_tiles[x][y-1])
        if theoretical_tile.facility_connection[1]==True:
            connected.append(self.table_tiles[x+1][y])
        if theoretical_tile.facility_connection[2]==True:
            connected.append(self.table_tiles[x][y+1])
        if theoretical_tile.facility_connection[3]==True:
            connected.append(self.table_tiles[x-1][y])
        return connected
    def get_city_region(self,x,y):
        region = self.get_city_connected([self.table_tiles[x][y]])
        return region
    def get_city_connected(self,connected):
        if connected!=None:
            for i in connected:
                if i!=None:
                    for j in self.get_immediately_city_connected(i):
                        if self.x_in_y (j,connected)==False:
                            connected.append(j)
        return connected
    def get_immediately_city_connected(self,tile):
        connected = []
        x=tile.x
        y=tile.y
        theoretical_tile = self.get_rotated_tile_type(tile)
        if theoretical_tile.city_connection[0]==True:
            connected.append(self.table_tiles[x][y-1])
        if theoretical_tile.city_connection[1]==True:
            connected.append(self.table_tiles[x+1][y])
        if theoretical_tile.city_connection[2]==True:
            connected.append(self.table_tiles[x][y+1])
        if theoretical_tile.city_connection[3]==True:
            connected.append(self.table_tiles[x-1][y])
        return connected
    def trigger_upgrade_on_turn_begins(self,upgrade):
        if upgrade==1:
            if self.no_adjacent_upgrades(upgrade)==True:
                self.upgrade_owner(upgrade).vp+=1
        elif upgrade==6:
            self.upgrade_owner(upgrade).information+=3
        elif upgrade==7:
            self.upgrade_owner(upgrade).vp+=1
        elif upgrade==8:
            if self.remove_counters_from_upgrade(upgrade,1)==True:
                if self.count_counters_on_upgrade(upgrade)==0:
                    self.gain_any_combination_of_goods(player_identity,6)
        elif upgrade==12:
            self.upgrade_owner(upgrade).metal+=2
        elif upgrade==13:
            if self.remove_counters_from_upgrade(upgrade,1)==True:
                if self.count_counters_on_upgrade(upgrade)==0:
                    self.upgrade_owner(upgrade).vp+=8
        elif upgrade==14:
           self.gain_any_one_good(self.upgrade_owner(upgrade),2)
        elif upgrade==20:
            if self.remove_counters_from_upgrade(upgrade,1)==True:
                if self.count_counters_on_upgrade(upgrade)==0:
                    self.upgrade_owner(upgrade).water+=6
        elif upgrade==22:
            if self.remove_counters_from_upgrade(upgrade,1)==True:
                if self.count_counters_on_upgrade(upgrade)==0:
                    self.gain_any_one_good(player_identity,7)
        elif upgrade==24:
            self.trade_in_resources_for_vp(player_identity,4)
        elif upgrade==28:
            upgrade_owner=self.upgrade_owner(upgrade)
            least = True
            for participant in players:
                if participant!=upgrade_owner:
                    if participant.electricity<=upgrade_owner.electricity:
                        least = False
            if least==True:
                upgrade_owner.electricity+=3
        elif upgrade==30:
            x = self.select_resource_for_opponent_to_lose("Select a resource for your opponent to lose.")
            upgrade_owner=self.upgrade_owner(upgrade)
            for participant in self.players:
                if participant!=upgrade_owner:
                    if x==1:
                        if participant.electricity>0:
                            participant.electricity-=1
                    elif x==2:
                        if participant.water>0:
                            participant.water-=1
                    elif x==3:
                        if participant.information>0:
                            participant.information-=1
                    elif x==4:
                        if participant.metal>0:
                            participant.metal-=1
                    elif x==5:
                        if participant.rare_metal>0:
                            participant.rare_metal-=1
        elif upgrade==31:
            self.add_counters_to_upgrade(upgrade,1)
            if self.count_counters_on_upgrade(upgrade)>=2:
                if self.all_upgrades_in_city_are_bureaucracy(upgrade):
                    self.use_the_hive(player_identity)
    def use_the_hive(player_num):
        #STUB
        pass
    def all_upgrades_in_city_are_bureaucracy(upgrade):
        #STUB
        return True
    def remove_counters_from_upgrade(upgrade,num):
        #STUB
        pass
    def count_counters_on_upgrade(upgrade):
        #STUB
        return 0
    def gain_any_combination_of_goods(player_num,num):
        #STUB
        pass
    def on_buy(self,player_number,upgrade):
        player = self.players[player_number]
        if upgrade==2:
            pass
            #STUB
        elif upgrade==3:
            player.vp+=1
            player.vp+=(self.count_adjacent_non_datahosting_upgrades(upgrade)*2)
        elif upgrade==4:
            pass
            #STUB
        elif upgrade==5:
            player.vp+=2
        elif upgrade==8:
            self.add_counters_to_upgrade(upgrade,2)
        elif upgrade==9:
            player.vp+=1
            self.gain_any_one_good(player_number,5)
        elif upgrade==13:
            player.vp-=1
            self.add_counters_to_upgrade(upgrade,1)
        elif upgrade==15:
            player.vp+=2
        elif upgrade==17:
            player.vp+=2
        elif upgrade==18:
            self.trade_in_resources_for_vp(player_number,3)
        elif upgrade==19:
            player.vp+=4
        elif upgrade==20:
            player.water+=6
            self.add_counters_to_upgrade(upgrade,1)
        elif upgrade==21:
            player.vp+=6
        elif upgrade==22:
            self.gain_any_one_good(player_number,7)
            self.add_counters_to_upgrade(upgrade,1)
        elif upgrade==23:
            player.vp+=8
        elif upgrade==26:
            highest=0
            target=None
            for participant in players:
                if participant.vp>highest or (participant.vp==highest and target==player):
                    target=participant
            if target.vp>=5:
                target.vp-=5
        elif upgrade==27:
            self.add_counters_to_upgrade(upgrade,1)
        else:
            return
    def count_adjacent_non_datahosting_upgrades(self,upgrade):
        x,y = self.get_upgrade_location(upgrade)
        count = 0
        if self.table_tiles[x-1] and self.table_tiles[x-1][y] and self.table_tiles[x-1][y].upgrade_built>7:
            if self.x_in_y(self.table_tiles[x-1][y],self.get_city_region[x][y]):
                count+=1
        if self.table_tiles[x+1] and self.table_tiles[x+1][y] and self.table_tiles[x+1][y].upgrade_built>7:
            if self.x_in_y(self.table_tiles[x+1][y],self.get_city_region[x][y]):
                count+=1
        if self.table_tiles[x] and self.table_tiles[x][y-1] and self.table_tiles[x][y-1].upgrade_built>7:
            if self.x_in_y(self.table_tiles[x][y-1],self.get_city_region[x][y]):
                count+=1
        if self.table_tiles[x] and self.table_tiles[x][y+1] and self.table_tiles[x][y+1].upgrade_built>7:
            if self.x_in_y(self.table_tiles[x][y+1],self.get_city_region[x][y]):
                count+=1
        return count
    def add_counters_to_upgrade(self,upgrade,counters):
        x,y = self.get_upgrade_location(upgrade)
        print x,y
        tile = self.table_tiles[x][y]
        if tile.counters==None:
            tile.counters=0
        tile.counters+=counters
    def trade_in_resources_for_vp(player_number,rate):
    #STUB
        pass
    def gain_any_one_good(player_number,amount):
    #STUB
        pass
    def no_adjacent_upgrades(self,upgrade):
        x,y = self.get_upgrade_location(upgrade)
        if self.table_tiles[x-1] and self.table_tiles[x-1][y] and self.table_tiles[x-1][y].upgrade_built>-1:
            return False
        if self.table_tiles[x+1] and self.table_tiles[x+1][y] and self.table_tiles[x+1][y].upgrade_built>-1:
            return False
        if self.table_tiles[x] and self.table_tiles[x][y-1] and self.table_tiles[x][y-1].upgrade_built>-1:
            return False
        if self.table_tiles[x] and self.table_tiles[x][y+1] and self.table_tiles[x][y+1].upgrade_built>-1:
            return False
        return True
    def upgrade_owner(self,num):
        x,y=self.get_upgrade_location(num)
        return self.players[self.table_tiles[x][y].upgrade_owner]
    def count_cities(self):
        cities = []
        kill_list = []
        for row in self.table_tiles:
            for tile in row:
                cities.append(get_city_region(tile))
        for i in cities:
            if i==None or self.x_in_y(None,i) or self.region_closed(i)!=True:
                kill_list.append(i)
        for i in range(len(cities)-1):
            if len(cities[i])==1:
                kill_list.append(cities[i])
            for j in range(i+1,len(cities)):
                difference_found=False
                for k in cities[i]:
                    if self.x_in_y(k,cities[j])!=True:
                        difference_found=True
                if difference_found==False:
                    kill_list.append(cities[j])
        for i in kill_list:
            if x_in_y(i,cities):
                cities.remove(i)
        return len(cities)
    def count_finance_upgrades_bought(self):
        count=0
        for i in range(8,16):
            if self.upgrades_available[i]==False:
                count+=1
        return count
    def total_resources(self,player):
        return player.electricity+player.water+player.information+player.metal+player.rare_metal
    def count_upgrade_categories_bought(self):
        datahosting_bought=False
        finance_bought=False
        entertainment_bought=False
        bureaucracy_bought=False
        for i in range(0,8):
            if self.upgrades_available[i]==False:
                datahosting_bought=True
        for i in range(8,16):
            if self.upgrades_available[i]==False:
                finance_bought=True
        for i in range(16,24):
            if self.upgrades_available[i]==False:
                entertainment_bought=True
        for i in range(24,32):
            if self.upgrades_available[i]==False:
                bureaucracy_bought=True
        count=0
        if datahosting_bought==True:
            count+=1
        if finance_bought==True:
            count+=1
        if entertainment_bought==True:
            count+=1
        if bureaucracy_bought==True:
            count+=1
        return count
    def count_counters_on_upgrade(self,num):
        x,y = self.get_upgrade_location(upgrade)
        tile = self.table_tiles[x][y]
        if tile.counters!=None:
            return tile.counters
        else:
            return 0
    def has_most_points(self,player):
        for participant in self.players:
            if participant.vp>player.vp:
                return False
        for participant in self.players:
            if participant!=player and participant.vp==player.vp:
                return self.tiebreaker(player)
        return True
    def tiebreaker(self,player):
        for participant in self.players:
            if self.total_resources(participant)>self.total_resources(player):
                return False
        return True
    def endgame(self):
        self.game_over=True
        if self.upgrades_available[0]==False:
            if at_least_one_other_upgrade_owned_in_city(0,player_identity):
                self.players[upgrade_owner_number(0)].vp+=1
        if self.upgrades_available[11]==False:
            self.upgrade_owner(11).vp+=(count_cities()/2)
        if self.upgrades_available[15]==False:
            self.upgrade_owner(15).vp+=(count_finance_upgrades_bought())
        if self.upgrades_available[24]==False:
            self.upgrade_owner(24).vp+=(total_resources(upgrade_owner(24))/4)
        if self.upgrades_available[29]==False:
            self.upgrade_owner(29).vp+=(2*count_upgrade_categories_bought())
        if self.upgrades_available[31]==False:
            self.upgrade_owner(31).vp+=(3*(count_counters_on_upgrade(31)/2))
        for player in self.players:
            if self.has_most_points(player):
                self.push_message(player,'YOU WIN!')
            else:
                self.push_message(player,'You have lost.')
    def initiate_tile_types (self):
        types = []
        for i in range(27):
            types.append(TileType())
        types[0].facility_connection[0]=True
        types[1].city_connection[0]=True
        types[2].facility_connection[0]=True
        types[2].facility_connection[2]=True
        types[3].city_connection[0]=True
        types[3].city_connection[2]=True
        types[4].facility_connection[0]=True
        types[4].city_connection[2]=True
        types[5].facility_connection[1]=True
        types[5].city_connection[2]=True
        types[6].facility_connection[2]=True
        types[6].city_connection[1]=True
        types[7].facility_connection=[True,True,False,True]
        types[8].city_connection=[True,True,False,True]
        types[9].facility_connection[0]=True
        types[9].facility_connection[3]=True
        types[10].city_connection[0]=True
        types[10].city_connection[3]=True
        for i in range(11,19):
            types[i].facility_connection[0] = True
        return types
    def initiate_upgrade_types(self):
        types = []
        for i in range(32):
            types.append(UpgradeType())
        for i in range(0,8):
            types[i].category="Data Hosting"
        for i in range(8,16):
            types[i].category="Finance"
        for i in range(16,24):
            types[i].category="Entertainment"
        for i in range(24,32):
            types[i].category="Bureaucracy"
        names = ["Fusion Cooling","Opt-Out Policy","Terraforming Server","Data Synergy","Geolocational Satellites","Population Metrics","Data Correlation","Server Megafarm","Investment",
                "Buy Low","Economic Efficiency","Economic Ties","Metal Markets","Rapidfire Investment","Global Market","Market Buy-In","Opiate","Holonews","Sensorial Immersion",
                "Stimvids","Hydro-Entertainment Facility","Biomechanoid Companion","Virtual Matter Playground","Total Immersion Envirosim","Trade Agreement","Customs",
                "Progressive Taxation","Public Auction","Electricity Tax","Balanced Economy","Sign in Triplicate","The Hive"]
        descriptions = ["At the end of the game, +1 VP if you have at least 1 other upgrade in this city.","+1 VP per turn so long as there are no adjacent upgrades in this city.",
                        "When bought, look at the top 20 land tiles and rearrange in any order.","+1 VP. +2 VP for every adjacent non-data hosting upgrade in this city.",
                        "When you buy this, go through the tile stack and remove four tiles of your",
                        "+2 VP. +1 VP whenever a city is brought online.","+3 information per turn.","+1 VP per turn.","Put two counters on this. Remove one each turn. When there are no more",
                        "Gain 1 VP. Gain 5 of any one good immediately.","Each upgrade you buy costs one less of any one resource (min. 1 of any",
                        "At the end of the game, +1 VP for every 2 enclosed cities.","Every turn, +2 metal.","Pay 1 VP immediately. +8 VP at the beginning of the next turn.",
                        "Each turn, +2 of any resource.","+2 VP. +1 VP per Finance upgrade bought at the end of the game.","You are not affected by cost increases.","+2 VP",
                        "When bought, trade in any number of resources. +1 VP / 3 resources.","+4 VP","+6 water immediately. +6 water on your next turn.","+6 VP",
                        "+7 of any one resource immediately. +7 of any one resource at the","+8 VP","Pay 4 resources at any time: +1 VP",
                        "All upgrades for other players cost +1 of the resource they require the most.","When bought, the player with the most VP loses 5 VP.",
                        "Once per game, you may sell another upgrade for 5 VP.","If you have the least electricity of any player, +3 electricity per turn.",
                        "+2 VP at the end of the game for each upgrade category bought.",
                        "Other players lose one resource of your choice at the beginning of each turn.",
                        "+1 counter per turn. Remove two counters: If all upgrades in this city are"]
        descriptions2 = ["","","","","choice. Play those instead of drawing on your next turn. Once per turn, you","","","",
                        "counters, gain 6 of any combination of goods.","","listed resource.)","","","","","","","","","","","","beginning of next turn.","","","","","","","",
                        "","Bureaucracy, +3 VP"]
        descriptions3 = ["","","","","may pay 1 information to gain 1 water.","","","","","","","","","","","","","","","","","","","","","","","","","","",""]
        electricity = [0,0,0,0,0,0,0,0,1,1,3,3,6,4,5,4,0,0,1,1,0,0,3,1,0,0,0,0,0,0,0,0]
        water = [1,1,3,3,6,4,5,4,0,0,1,1,0,0,3,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        information = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,3,3,6,4,5,4,0,0,1,1,0,0,3,1]
        metal = [0,0,1,1,0,0,3,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,3,3,6,4,5,4]
        rare_metal = [0,1,0,1,0,3,0,4,0,1,0,1,0,3,0,4,0,1,0,1,0,3,0,4,0,1,0,1,0,3,0,4]
        for i in range(0,32):
            types[i].name=names[i]
            types[i].description=descriptions[i]
            types[i].description2=descriptions2[i]
            types[i].description3=descriptions3[i]
            types[i].electricity=electricity[i]
            types[i].water=water[i]
            types[i].information=information[i]
            types[i].metal=metal[i]
            types[i].rare_metal=rare_metal[i]
        return types
class Tile():
    def __init__(self):
        self.tile_type = 1
        self.tile_orientation = 1
        self.upgrade_built = -1
        self.upgrade_owner = 0
        self.electricity = 0
        self.information = 0
        self.metal = 0
        self.rare_metal = 0
        self.water = 0
        self.worker_placed = -1
        self.city_online_status = 0 #0 = not online, 1 = tile brought online, 2 = entire city online
        self.counters = 0
        self.x = 0
        self.y = 0
    def to_JSON(self):
        return "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12},{13}".format(self.tile_type,self.tile_orientation,self.upgrade_built,self.upgrade_owner,self.electricity,self.information,self.metal,self.rare_metal,self.water,self.worker_placed,self.city_online_status,self.counters,self.x,self.y)
    def from_JSON(self,input):
        split = input.split(',')
        self.tile_type=int(split[0])
        self.tile_orientation=int(split[1])
        self.upgrade_built=int(split[2])
        self.upgrade_owner=int(split[3])
        self.electricity=int(split[4])
        self.information=int(split[5])
        self.metal=int(split[6])
        self.rare_metal=int(split[7])
        self.water=int(split[8])
        self.worker_placed=int(split[9])
        self.city_online_status=int(split[10])
        self.counters=int(split[11])
        self.x=int(split[12])
        self.y=int(split[13])
class Player():
    def __init__(self):
        self.vp = 10
        self.electricity=10
        self.information = 10
        self.metal = 10
        self.rare_metal = 10
        self.water = 10
        
        # self.vp=0
        # self.electricity=0
        # self.information=0
        # self.metal=0
        # self.rare_metal=0
        # self.water=0
        self.is_first_player=False
        self.is_turn_to_place=False
        self.workers_remaining=2
        self.total_workers=2
        self.handler = None
    def to_JSON(self):
        return "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}".format(self.vp,self.electricity,self.information,self.metal,self.rare_metal,self.water,self.is_first_player,self.is_turn_to_place,self.workers_remaining,self.total_workers,self.handler.username)
def serialize_list(list):
    return_list = []
    for i in list:
        if i!=None:
            return_list.append(i.to_JSON())
        else:
            return_list.append(None)
    return return_list
def serialize_2d_list(list):
    return_list = []
    for i in list:
        return_list.append(serialize_list(i))
    return return_list
class TileType ():
    def __init__(self):
        self.facility_connection = [False,False,False,False]
        self.city_connection = [False,False,False,False]
class UpgradeType():
    def __init__(self):
        self.name=""
        self.category=""
        self.description=""
        self.description2=""
        self.description3=""
        self.electricity=0
        self.water=0
        self.information=0
        self.metal=0
        self.rare_metal=0
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
