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

define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", LoginHandler),
            (r"/lobby.html", LobbyHandler),
            (r"/main.html", MainHandler),
            (r"/loginsocket", LoginSocketHandler),
            (r"/lobbysocket", LobbySocketHandler),
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
        LobbySocketHandler.waiters.remove(self)
    def on_message(self,message):
        parsed = tornado.escape.json_decode(message)
        if parsed['message'] == "request_usernames":
            for waiter in self.waiters:
                waiter.write_message({"id": str(uuid.uuid4()), "message": "usernames_updated", "usernames": LoginSocketHandler.usernames})
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

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()