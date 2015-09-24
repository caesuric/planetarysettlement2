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
    def on_close(self):
        MainSocketHandler.waiters.remove(self)
    def on_message(self,message):
        parsed = tornado.escape.json_decode(message)
        if parsed['message']=='tile_position_selected':
            self.game.tile_position_selected(parsed)
    def start_game(self):
        self.game.start()
class Game():
    waiters = []
    def __init__(self,game_id):
        self.game_id = game_id
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
        temp_tiles[11][10]=a
        a.tile_orientation = 2
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 1
        temp_tiles[9][11]=a
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 3
        temp_tiles[10][11]=a
        a = Tile()
        a.tile_type = 1
        a.tile_orientation = 0
        temp_tiles[11][11]=a
        self.table_tiles = temp_tiles
        
        self.players = []
        for i in range(0,len(self.waiters)):
            a = Player()
            if i==0:
                a.is_first_player=True
                a.is_turn_to_place=True
            a.handler = self.waiters[i]
            self.players.append(a)
        self.beginning_of_turn()
    def beginning_of_turn(self):
        self.check_for_endgame()
        self.beginning_of_turn_phase()
        self.lay_tiles()
    def check_for_endgame(self):
        if len(self.stack_tiles)==0:
            self.endgame()
    def beginning_of_turn_phase(self):
        for i in range(0,32):
            if self.upgrades_available[i]==False:
                trigger_upgrade_on_turn_begins(i)
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
        for waiter in self.waiters:
			waiter.write_message({"id": str(uuid.uuid4()), "message": "push_update", "upgrades_available": self.upgrades_available, "table_tiles": serialize_2d_list(self.table_tiles),
								  "players": serialize_list(self.players),"username": waiter.username, "stack_tiles": len(self.stack_tiles)})
    def push_message(self,client,message):
        client.handler.write_message({"id": str(uuid.uuid4()), "message": "push_message", "text": message})
    def push_tile_lay(self,client,tile,active):
        client.handler.write_message({"id": str(uuid.uuid4()), "message": "push_tile_lay", "tile": tile.to_JSON(), "active": active})
    def tile_position_selected(self,message):
        message['message'] = 'push_tile_rotate'
        for i in self.players:
            if i.is_first_player==True:
                i.handler.write_message(message)
    def trigger_upgrade_on_turn_begins(self,number):
    #TODO: STUB
        pass
    def endgame(self):
    #TODO: STUB
        pass
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
    def to_JSON(self):
        return "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11}".format(self.tile_type,self.tile_orientation,self.upgrade_built,self.upgrade_owner,self.electricity,self.information,self.metal,self.rare_metal,self.water,self.worker_placed,self.city_online_status,self.counters)
class Player():
    def __init__(self):
        self.vp=0
        self.electricity=0
        self.information=0
        self.metal=0
        self.rare_metal=0
        self.water=0
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
    def cost(self,upgrade_number):
        cost_increase = 0
        player = game_state.players[player_identity]
        if game_state.upgrades_available[25]==False:
            if upgrade_owner_number(25)!=player_identity:
                if game_state.upgrades_available[16]==True or (game_state.upgrades_available[16]==False and upgrade_owner_number(16)!=player_identity):
                    cost_increase = get_highest_costed_resource(upgrade_number)
        if cost_increase==1:
            self.electricity+=1
        elif cost_increase==2:
            self.water+=1
        elif cost_increase==3:
            self.information+=1
        elif cost_increase==4:
            self.metal+=1
        elif cost_increase==5:
            self.rare_metal+=1
        costs=[]
        colors=[]
        if self.electricity>0:
            costs.append("Electricity: "+str(self.electricity))
            if player.electricity<self.electricity:
                colors.append((255,0,0))
            else:
                colors.append((255,255,0))
        if self.water>0:
            costs.append("Water: "+str(self.water))
            if player.water<self.water:
                colors.append((255,0,0))
            else:
                colors.append((0,255,255))
        if self.information>0:
            costs.append("Information: "+str(self.information))
            if player.information<self.information:
                colors.append((255,0,0))
            else:
                colors.append((0,224,0))
        if self.metal>0:
            costs.append("Metal: "+str(self.metal))
            if player.metal<self.metal:
                colors.append((255,0,0))
            else:
                colors.append((128,128,128))
        if self.rare_metal>0:
            costs.append("Rare Metal: "+str(self.rare_metal))
            if player.rare_metal<self.rare_metal:
                colors.append((255,0,0))
            else:
                colors.append((255,128,0))
        if cost_increase==1:
            self.electricity-=1
        elif cost_increase==2:
            self.water-=1
        elif cost_increase==3:
            self.information-=1
        elif cost_increase==4:
            self.metal-=1
        elif cost_increase==5:
            self.rare_metal-=1
        return (costs,colors)
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
