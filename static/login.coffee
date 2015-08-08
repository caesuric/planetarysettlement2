login = (form) ->
    message = form.formToDict()
    updater.socket.send JSON.stringify(message)
    form.find('loginform[type=text]').val('').select()

$(document).ready ->
    if !window.console
        window.console = {}
    if !window.console.log
        window.console.log = ->

    $('#loginform').live 'submit', ->
        login $(this)
        false
    updater.start()

jQuery.fn.formToDict = ->
    fields = @serializeArray()
    json = {}
    i = 0
    while i < fields.length
        json[fields[i].name] = fields[i].value
        i++
    if json.next
        delete json.next
    json

updater = 
    socket: null
    start: ->
        url = 'ws://' + location.host + '/loginsocket'
        updater.socket = new WebSocket(url)
        updater.socket.onmessage = (event) ->
            updater.processMessage JSON.parse(event.data)
    processMessage: (message) ->
        if message.message == 'username_accepted'
            window.location.href= 'http://' + location.host + '/lobby.html?name=' + message.username
        else if message.message == 'username_taken'
            document.getElementById('prompt_text').innerHTML = '<font color="red">Username taken, please select another:</font>'