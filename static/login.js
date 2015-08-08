var login, updater;

login = function(form) {
  var message;
  message = form.formToDict();
  updater.socket.send(JSON.stringify(message));
  return form.find('loginform[type=text]').val('').select();
};

$(document).ready(function() {
  if (!window.console) {
    window.console = {};
  }
  if (!window.console.log) {
    window.console.log = function() {};
  }
  $('#loginform').live('submit', function() {
    login($(this));
    return false;
  });
  return updater.start();
});

jQuery.fn.formToDict = function() {
  var fields, i, json;
  fields = this.serializeArray();
  json = {};
  i = 0;
  while (i < fields.length) {
    json[fields[i].name] = fields[i].value;
    i++;
  }
  if (json.next) {
    delete json.next;
  }
  return json;
};

updater = {
  socket: null,
  start: function() {
    var url;
    url = 'ws://' + location.host + '/loginsocket';
    updater.socket = new WebSocket(url);
    return updater.socket.onmessage = function(event) {
      return updater.processMessage(JSON.parse(event.data));
    };
  },
  processMessage: function(message) {
    if (message.message === 'username_accepted') {
      return window.location.href = 'http://' + location.host + '/lobby.html?name=' + message.username;
    } else if (message.message === 'username_taken') {
      return document.getElementById('prompt_text').innerHTML = '<font color="red">Username taken, please select another:</font>';
    }
  }
};