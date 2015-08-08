challenge = (form) ->
    message = form.formToDict()
    message.message = "challenge"
    message.challenge_number = updater.challengeNumber
    updater.socket.send JSON.stringify(message)
    form.find('lobbyform[type=text]').val('').select()

challengeRespondAccept = (form) ->
    message = form.formToDict()
    message.message = "challenge3a"
    message.challenge_number = updater.challengeNumber
    updater.socket.send JSON.stringify(message)
    form.find('challengeform[type=text]').val('').select()

challengeRespondDecline = (form) ->
    message = form.formToDict()
    message.message = "challenge3b"
    message.challenge_number = updater.challengeNumber
    updater.socket.send JSON.stringify(message)
    form.find('challengeform[type=text]').val('').select()

$(document).ready ->
    if !window.console
        window.console = {}
    if !window.console.log
        window.console.log = ->

    $('#lobbyform').live 'submit', ->
        challenge $(this)
        false
    $('#challengeformaccept').live 'submit', ->
        challengeRespondAccept $(this)
        false
    $('#challengeformdecline').live 'submit', ->
        challengeRespondDecline $(this)
        false
    updater.start()
    

updater = 
    socket: null
    start: ->
        url = 'ws://' + location.host + '/lobbysocket'
        updater.socket = new WebSocket(url)
        updater.socket.onmessage = (event) ->
            updater.processMessage JSON.parse(event.data)
        updater.socket.onopen = updater.initialize
    processMessage: (message) ->
        if message.message == 'usernames_updated'
            userList = ''
            for username in message.usernames
                userList = userList+'<input type="checkbox" value="'+username+'" name="'+username+'">'+username+'<br>'
            document.getElementById('users').innerHTML=userList
        else if message.message == 'sending_name'
            name = message.name
            document.getElementById('username').innerHTML='Hello, '+name+'!'
        else if message.message == 'challenge2'
            challengeMessage = 'You have been challenged to a game with '
            for username in message.usernames
                challengeMessage = challengeMessage+username+', '
            challengeMessage = challengeMessage + '<form action="a/message/new" method="post" id="challengeformaccept"><input type="submit" name="accept" value="Accept"></form><form action="a/message/new" method="post" id="challengeformdecline"><input type="submit" name="decline" value="Decline"></form>'
            document.getElementById('status').innerHTML=challengeMessage
            updater.challengeNumber = message.challenge_number
        else if message.message == 'game_ready'
            window.location.href = 'http://' + location.host + '/main.html?id=' + updater.challengeNumber
    requestUsernames: () ->
        message = message:'request_usernames'
        updater.socket.send JSON.stringify(message)
    requestOwnName: () ->
        message = message:'request_own_name'
        updater.socket.send JSON.stringify(message)
    initialize: () ->
        updater.requestUsernames()
        updater.requestOwnName()

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