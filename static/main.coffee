$(document).ready ->
    if !window.console
        window.console = {}
    if !window.console.log
        window.console.log = ->

    window.canvas = new fabric.Canvas('my_canvas')
    window.canvas.backgroundColor="black"
    window.canvas.renderAll()
    updater.start()
    window.tileTypes = initiateTileTypes()
    window.upgradeTypes = initiateUpgradeTypes()
    window.selectingUpgrade=false
costsString = (id) ->
    addCostIncreases(id)
    text = ""
    if window.upgradeTypes[id].electricity>0
        text = text + "<span style='color: #"
        if window.player_electricity<window.upgradeTypes[id].electricity
            text=text+'FF0000'
        else
            text=text+'FFFF00'
        text=text+";'>Electricity: "+window.upgradeTypes[id].electricity
        text=text+'</span>   '
    if window.upgradeTypes[id].water>0
        text = text + "<span style='color: #"
        if window.player_water<window.upgradeTypes[id].water
            text=text+'FF0000'
        else
            text=text+'00FFFF'
        text=text+";'>Water: "+window.upgradeTypes[id].water
        text=text+'</span>   '
    if window.upgradeTypes[id].information>0
        text = text + "<span style='color: #"
        if window.player_information<window.upgradeTypes[id].information
            text=text+'FF0000'
        else
            text=text+'00E000'
        text=text+";'>Information: "+window.upgradeTypes[id].information
        text=text+'</span>   '
    if window.upgradeTypes[id].metal>0
        text = text + "<span style='color: #"
        if window.player_metal<window.upgradeTypes[id].metal
            text=text+'FF0000'
        else
            text=text+'808080'
        text=text+";'>Metal: "+window.upgradeTypes[id].metal
        text=text+'</span>   '
    if window.upgradeTypes[id].rare_metal>0
        text = text + "<span style='color: #"
        if window.player_rare_metal<window.upgradeTypes[id].rare_metal
            text=text+'FF0000'
        else
            text=text+'FF8000'
        text=text+";'>Rare Metal: "+window.upgradeTypes[id].rare_metal
        text=text+'</span>'
    removeCostIncreases(id)
    return text
upgradeMouseOver = (upgrade_id) ->
    text = window.upgradeTypes[upgrade_id].name+'<br>'+costsString(upgrade_id)+'<br>'+window.upgradeTypes[upgrade_id].description+'<br>'+window.upgradeTypes[upgrade_id].description2+'<br>'+window.upgradeTypes[upgrade_id].description3
    document.getElementById('upgrade_float_text').innerHTML=text
upgradeOnClick = (upgrade_id) ->
    if window.selectingUpgrade==true
        window.selectingUpgrade=false
        updater.onUpgradeClick(upgrade_id)
upgradeMouseOff = () ->
    document.getElementById('upgrade_float_text').innerHTML=''
renderTable = (upgrades_available,table_tiles,players,username,stack_tiles) ->
    window.canvas.backgroundColor="black"
    window.canvas.clear()
    for i in [0..29]
        for j in [0..29]
            if table_tiles[i][j]!=null
                x_pos = i*45
                y_pos = j*45
                drawTableTile(x_pos,y_pos,table_tiles[i][j],true,i,j)
                tile_data = table_tiles[i][j].split(",")
                tile_worker_placed = parseInt(tile_data[9],10)
                tile_upgrade_built = parseInt(tile_data[2],10)
                switch tile_worker_placed
                    when 0 then color='rgba(64,64,255,1)'
                    when 1 then color='rgba(255,64,64,1)'
                    when 2 then color='rgba(64,255,64,1)'
                    when 3 then color='rgba(255,255,64,1)'
                    else color=-1
                if color!=-1
                    window.canvas.add new fabric.Circle(left: x_pos, top: y_pos, radius: 15, fill: color, stroke: color)
                if tile_upgrade_built>-1
                    window.canvas.add new fabric.Text('u', left: x_pos+18, top: y_pos+26, fill: 'rgba(255,255,255,1)', fontSize: 15) # 22
    playerNumber = 0
    for i in [0..players.length-1]
        player_data = players[i].split(",")
        if player_data[10]==username
            playerNumber=i
    player_data = players[playerNumber].split(",")
    player_vp = player_data[0]
    player_electricity = player_data[1]
    player_information = player_data[2]
    player_metal = player_data[3]
    player_rare_metal = player_data[4]
    player_water = player_data[5]
    player_workers_remaining = player_data[8]
    player_total_workers = player_data[9]
    window.player_electricity = player_electricity
    window.player_information = player_information
    window.player_metal = player_metal
    window.player_rare_metal = player_rare_metal
    window.player_water = player_water
    window.upgrades_available = upgrades_available
    window.player_number = playerNumber
    window.player_identity = playerNumber
    document.getElementById('player_name').innerHTML=username
    document.getElementById('vp').innerHTML=player_vp
    document.getElementById('electricity').innerHTML=player_electricity
    document.getElementById('information').innerHTML=player_information
    document.getElementById('metal').innerHTML=player_metal
    document.getElementById('rare_metal').innerHTML=player_rare_metal
    document.getElementById('water').innerHTML=player_water
    document.getElementById('total').innerHTML=parseInt(player_electricity,10)+parseInt(player_information,10)+parseInt(player_metal,10)+parseInt(player_rare_metal,10)+parseInt(player_water,10)
    document.getElementById('workers').innerHTML=player_workers_remaining
    document.getElementById('total_workers').innerHTML=player_total_workers
    document.getElementById('opponent_labels').innerHTML=''
    document.getElementById('opponent_data').innerHTML=''
    for i in [0..players.length-1]
        if i!=playerNumber
            player_data=players[i].split(",")
            player_vp = player_data[0]
            player_electricity = player_data[1]
            player_information = player_data[2]
            player_metal = player_data[3]
            player_rare_metal = player_data[4]
            player_water = player_data[5]
            player_total = parseInt(player_electricity,10)+parseInt(player_information,10)+parseInt(player_water,10)+parseInt(player_metal,10)+parseInt(player_rare_metal,10)
            player_workers_remaining = player_data[8]
            player_total_workers = player_data[9]
            player_username = player_data[10]
            document.getElementById('opponent_labels').innerHTML=document.getElementById('opponent_labels').innerHTML+'Name:<br>VP:<br>Electricity:<br>Water:<br>Information:<br>Metal:<br>Rare Metal:<br>Total:<br>Workers:<br><br>'
            document.getElementById('opponent_data').innerHTML=document.getElementById('opponent_data').innerHTML+player_username+'<br>'+player_vp+'<br><span style="color: #FFFF00;">'+player_electricity+'</span><br><span style="color: #00FFFF;">'+player_water+'</span><br><span style="color: #00E000;">'+player_information+'</span><br><span style="color: #808080;">'+player_metal+'</span><br><span style="color: #FF8000;">'+player_rare_metal+'</span><br>('+player_total+')<br>'+player_workers_remaining+'/'+player_total_workers+'<br><br>'
    document.getElementById('upgrades').innerHTML=''
    for i in [0..31]
        if upgrades_available[i]==true
            if i>=0 and i<=7
                style='<span style="color: #00FFFF;" class="upgrade"'
            else if i>=8 and i<=15
                style='<span style="color: #FFFF00;" class="upgrade"'
            else if i>=16 and i<=23
                style='<span style="color: #00E000;" class="upgrade"'
            else if i>=24 and i<=31
                style='<span style="color: #808080;" class="upgrade"'
            if upgrade_costs_met(i)==true
                document.getElementById('upgrades').innerHTML=document.getElementById('upgrades').innerHTML+style+' id="upgrade'+i+'">'+'<li>'+window.upgradeTypes[i].name+'</li>'+'</span>'
            else
                document.getElementById('upgrades').innerHTML=document.getElementById('upgrades').innerHTML+style+' id="upgrade'+i+'">'+window.upgradeTypes[i].name+'</span><br>'
    document.getElementById('upgrades').innerHTML=document.getElementById('upgrades').innerHTML+'</ul>'
    document.getElementById('upgrades').innerHTML=document.getElementById('upgrades').innerHTML+'<span style="color: #FFFFFF;"><br>Tiles Remaining: '+stack_tiles+'<br> Turn '+(18-(Math.ceil(stack_tiles/4)))+'/18</span>'
    $(".upgrade").mouseover ->
        upgradeMouseOver(parseInt(this.id.split("e")[1],10))
    $(".upgrade").mouseout ->
        upgradeMouseOff()
    $(".upgrade").click ->
        upgradeOnClick(parseInt(this.id.split("e")[1],10))
    window.table_tiles=table_tiles
    window.players = players
    window.canvas.on 'mouse:move', (options) ->
        x = Math.floor(options.e.clientX / 45)
        y = Math.floor(options.e.clientY / 45)
        if x>29
            x=29
        if y>29
            y=29
        upgrade = -1
        if window.table_tiles[x][y]!=null and window.table_tiles[x][y]!=undefined
            tile_data = window.table_tiles[x][y].split(",")
            tile_upgrade_built = parseInt(tile_data[2],10)
            if tile_upgrade_built>-1
                upgrade = tile_upgrade_built
        if upgrade==-1
            upgradeMouseOff()
        else
            upgradeMouseOver(tile_upgrade_built)
            owner = parseInt(tile_data[3],10)
            owner_data = (window.players[owner].split(","))
            owner_name = owner_data[10]
            document.getElementById('upgrade_float_text').innerHTML+='Owner: '+owner_name
drawTableTile = (x_pos,y_pos,tile,is_real_tile,i,j) ->
    group = new fabric.Group()
    group.add new fabric.Rect(left: x_pos, top: y_pos, height: 45, width: 45, stroke: 'white', fill: 'transparent', strokeWidth: 2)
    tile_data = tile.split(",")
    tile_type = parseInt(tile_data[0],10)
    tile_orientation = parseInt(tile_data[1],10)
    tile_upgrade_built = parseInt(tile_data[2],10)
    tile_upgrade_owner = parseInt(tile_data[3],10)
    tile_electricity = parseInt(tile_data[4],10)
    tile_information = parseInt(tile_data[5],10)
    tile_metal = parseInt(tile_data[6],10)
    tile_rare_metal = parseInt(tile_data[7],10)
    tile_water = parseInt(tile_data[8],10)
    tile_worker_placed = parseInt(tile_data[9],10)
    tile_city_online_status = parseInt(tile_data[10],10)
    tile_counters = parseInt(tile_data[11],10)
    rotated = getRotatedTileType(tile)
    if tile_city_online_status==0
        city_color = 'rgba(128,128,128,1)'
    else if tile_city_online_status==1
        city_color = 'rgba(0,224,0,1)'
    else if tile_city_online_status==2
        city_color = 'rgba(0,64,255,1)'
    if rotated.facilityConnection[1]==true
        group.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
    if rotated.cityConnection[1]==true
        group.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_city_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
    if rotated.facilityConnection[2]==true
        group.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
    if rotated.cityConnection[2]==true
        group.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_city_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
    if rotated.facilityConnection[3]==true
        group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
    if rotated.cityConnection[3]==true
        group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_city_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
    if rotated.facilityConnection[0]==true
        group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
    if rotated.cityConnection[0]==true
        group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
        if is_real_tile==true
            if region_closed(get_city_region(window.table_tiles[i][j]))==true
                group.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
    if tile_electricity>0
        group.add new fabric.Text(tile_electricity.toString(), left: x_pos+2, top: y_pos+2, fill: 'rgb(255,255,0)', fontSize: 15)
    if tile_water>0
        group.add new fabric.Text(tile_water.toString(), left: x_pos+18, top: y_pos+2, fill: 'rgb(0,255,255)', fontSize: 15)
    if tile_information>0
        group.add new fabric.Text(tile_information.toString(), left: x_pos+33, top: y_pos+2, fill: 'rgb(0,224,0)', fontSize: 15)
    if tile_metal>0
        group.add new fabric.Text(tile_metal.toString(), left: x_pos+2, top: y_pos+18, fill: 'rgb(128,128,128)', fontSize: 15)
    if tile_rare_metal>0
        group.add new fabric.Text(tile_rare_metal.toString(), left: x_pos+18, top: y_pos+18, fill: 'rgb(255,128,0)', fontSize: 15)
    if tile_counters>0
        group.add new fabric.Text(tile_counters.toString(), left: x_pos+33, top: y_pos+33, fill: 'rgb(255,255,255)', fontSize: 15)
    if tile_type==11 or tile_type==19
        group.add new fabric.Text('W', left: x_pos+18, top: y_pos+18, fill: 'rgba(255,255,255,1)', fontSize: 15) # 22
    if tile_type==12 or tile_type==20
        group.add new fabric.Text('D', left: x_pos+18, top: y_pos+18, fill: 'rgba(255,255,255,1)', fontSize: 15) # 22
    if tile_type==13 or tile_type==21
        group.add new fabric.Text('U', left: x_pos+18, top: y_pos+18, fill: 'rgba(255,255,255,1)', fontSize: 15) # 22
    if tile_type==14 or tile_type==22
        group.add new fabric.Circle(left: x_pos+27, top: y_pos+27, radius: 9, fill: 'rgba(255,255,0,1)', stroke: 'rgba(255,255,0,1)')
    if tile_type==15 or tile_type==23
        group.add new fabric.Circle(left: x_pos+27, top: y_pos+27, radius: 9, fill: 'rgba(0,255,255,1)', stroke: 'rgba(0,255,255,1)')
    if tile_type==16 or tile_type==24
        group.add new fabric.Circle(left: x_pos+27, top: y_pos+27, radius: 9, fill: 'rgba(0,224,0,1)', stroke: 'rgba(0,224,0,1)')
    if tile_type==17 or tile_type==25
        group.add new fabric.Circle(left: x_pos+27, top: y_pos+27, radius: 9, fill: 'rgba(128,128,128,1)', stroke: 'rgba(128,128,128,1)')
    if tile_type==18 or tile_type==26
        group.add new fabric.Circle(left: x_pos+27, top: y_pos+27, radius: 9, fill: 'rgba(255,128,0,1)', stroke: 'rgba(255,128,0,1)')
    window.canvas.add(group)
    return group
upgrade_costs_met = (id) ->
    addCostIncreases(id)
    if window.player_electricity<window.upgradeTypes[id].electricity
        return false
    if window.player_information<window.upgradeTypes[id].information
        return false
    if window.player_water<window.upgradeTypes[id].water
        return false
    if window.player_metal<window.upgradeTypes[id].metal
        return false
    if window.player_rare_metal<window.upgradeTypes[id].rare_metal
        return false
    removeCostIncreases(id)
    return true

addCostIncreases = (id) ->
    cost_increase = 0
    if window.upgrades_available[25]==false
        if upgrade_owner_number(25)!=window.player_number
            if window.upgrades_available[16]==true or (window.upgrades_available[16]==false and upgrade_owner_number(16)!=window.player_identity)
                cost_increase = get_highest_costed_resource(id)
    if cost_increase==1
        window.upgradeTypes[id].electricity=window.upgradeTypes[id].electricity+1
    else if cost_increase==2
        window.upgradeTypes[id].water=window.upgradeTypes[id].water+1
    else if cost_increase==3
        window.upgradeTypes[id].information=window.upgradeTypes[id].information+1
    else if cost_increase==4
        window.upgradeTypes[id].metal=window.upgradeTypes[id].metal+1
    else if cost_increase==5
        window.upgradeTypes[id].rare_metal=window.upgradeTypes[id].rare_metal+1
removeCostIncreases = (id) ->
    cost_increase = 0
    if window.upgrades_available[25]==false
        if upgrade_owner_number(25)!=window.player_number
            if window.upgrades_available[16]==true or (window.upgrades_available[16]==false and upgrade_owner_number(16)!=window.player_identity)
                cost_increase = get_highest_costed_resource(id)
    if cost_increase==1
        window.upgradeTypes[id].electricity=window.upgradeTypes[id].electricity-1
    else if cost_increase==2
        window.upgradeTypes[id].water=window.upgradeTypes[id].water-1
    else if cost_increase==3
        window.upgradeTypes[id].information=window.upgradeTypes[id].information-1
    else if cost_increase==4
        window.upgradeTypes[id].metal=window.upgradeTypes[id].metal-1
    else if cost_increase==5
        window.upgradeTypes[id].rare_metal=window.upgradeTypes[id].rare_metal-1

upgrade_owner_number = (id) ->
    # STUB
    return 0

get_highest_costed_resource = (id) ->
    # STUB
    return 1

region_closed = (region) ->
    if x_in_y(null,region)==true
        return false
    else
        return true

x_in_y = (x,y) ->
    if y==null
        return false
    value = false
    for i in y
        if i==x
            value = true
    return value
    
get_region = (tile) ->
    group = []
    group.push(tile)
    region = get_connected(group)
    return region

get_connected = (connected) ->
    if connected!=null
        i=0
        while i<connected.length
            if connected[i]!=null
                for j in get_immediately_connected(connected[i])
                    if x_in_y(j,connected)==false
                        connected.push(j)
            i+=1
    return connected
    
get_city_connected = (connected) ->
    if connected!=null
        i=0
        while i<connected.length
            if connected[i]!=null
                for j in get_immediately_city_connected(connected[i])
                    if x_in_y(j,connected)==false
                        connected.push(j)
            i+=1
    return connected
    
get_immediately_connected = (tile) ->
    connected = []
    split = tile.split(',')
    x = parseInt(split[12])
    y = parseInt(split[13])
    theoretical_tile = getRotatedTileType(tile)
    if theoretical_tile.facilityConnection[0]==true
        connected.push((window.table_tiles[x][y-1]))
    if theoretical_tile.facilityConnection[1]==true
        connected.push((window.table_tiles[x+1][y]))
    if theoretical_tile.facilityConnection[2]==true
        connected.push((window.table_tiles[x][y+1]))
    if theoretical_tile.facilityConnection[3]==true
        connected.push((window.table_tiles[x-1][y]))
    return connected

get_immediately_city_connected = (tile) ->
    connected = []
    split = tile.split(',')
    x = parseInt(split[12])
    y = parseInt(split[13])
    theoretical_tile = getRotatedTileType(tile)
    if theoretical_tile.cityConnection[0]==true
        connected.push((window.table_tiles[x][y-1]))
    if theoretical_tile.cityConnection[1]==true
        connected.push((window.table_tiles[x+1][y]))
    if theoretical_tile.cityConnection[2]==true
        connected.push((window.table_tiles[x][y+1]))
    if theoretical_tile.cityConnection[3]==true
        connected.push((window.table_tiles[x-1][y]))
    return connected

get_city_region = (tile) ->
    group = []
    group.push(tile)
    region = get_city_connected(group)
    return region
    
getRotatedTileType = (tile) ->
    split = tile.split(',')
    type = split[0]
    orientation = split[1]
    tileType = new TileType
    baseTileType = window.tileTypes[type]
    for i in [0..3]
        tileType.facilityConnection[i]=baseTileType.facilityConnection[getRotation(i-orientation)]
        tileType.cityConnection[i]=baseTileType.cityConnection[getRotation(i-orientation)]
    return tileType

getRotation = (rotation) ->
    if rotation>=0 and rotation<=3
        return rotation
    else if rotation>3
        while rotation>3
            rotation-=4
        return rotation
    else if rotation<0
        while rotation<0
            rotation+=4
        return rotation

updater = 
    socket: null
    start: ->
        url = 'ws://' + location.host + '/mainsocket'
        updater.socket = new WebSocket(url)
        updater.socket.onmessage = (event) ->
            updater.processMessage JSON.parse(event.data)
        updater.socket.onopen = updater.initialize
    initialize: () ->
        message = {}
        message.message = 'request_update'
        updater.socket.send(JSON.stringify(message))
    processMessage: (message) ->
        if message.message=='push_update'
            updater.processPushUpdate(message)
        else if message.message=='push_message'
            updater.processPushMessage(message)
        else if message.message=='push_tile_lay'
            updater.processTileLay(message)
        else if message.message=='push_tile_rotate'
            updater.processTileRotate(message)
        else if message.message=='push_turn_end'
            updater.processTurnEnd(message)
        else if message.message=='push_worker_lay'
            updater.processWorkerLay(message)
        else if message.message=='push_dialog'
            updater.processPushDialog(message)
        else if message.message=='push_spend_freely'
            updater.processSpendFreely(message)
        else if message.message=='push_upgrade_select'
            updater.processUpgradeSelect()
        else if message.message=='push_upgrade_location_select'
            updater.processUpgradeLocationSelect(parseInt(message.upgrade_id))
        message.message = 'update_finished'
        updater.socket.send(JSON.stringify(message))
    processTurnEnd: (message) ->
        message.message = 'return_turn_end'
        updater.socket.send(JSON.stringify(message))
    processPushUpdate: (message) ->
        upgrades_available = message.upgrades_available
        table_tiles = message.table_tiles
        window.table_tiles = table_tiles
        players = message.players
        username = message.username
        stack_tiles = message.stack_tiles
        renderTable(upgrades_available,table_tiles,players,username,stack_tiles)
        window.canvas.renderAll()
    processPushMessage: (message) ->
        document.getElementById('message').innerHTML=message.text
    processUpgradeSelect: () ->
        document.getElementById('message').innerHTML='Select an upgrade to build.'
        window.selectingUpgrade=true
    processUpgradeLocationSelect: (upgrade_id) ->
        window.canvas.on 'mouse:up', (options) ->
            message = {}
            message.x = Math.floor(options.e.clientX / 45)
            message.y = Math.floor(options.e.clientY / 45)
            message.message = 'upgrade_location_selected'
            message.upgrade_id = upgrade_id
            window.canvas.off 'mouse:up'
            updater.socket.send(JSON.stringify(message))
    onUpgradeClick: (upgrade_id) ->
        message = {}
        message.message = 'upgrade_selected'
        message.upgrade_id = upgrade_id
        updater.socket.send(JSON.stringify(message))
    processPushDialog: (message) ->
        if message.type=='bring_city_online'
            document.getElementById('message').innerHTML = 'Would you like to bring a city online? <button onclick="updater.dialogCityYes()">Yes</button><button onclick="updater.dialogNo()">No</button>'
        else if message.type=='construct_worker'
            document.getElementById('message').innerHTML = 'Would you like to build a robot? <button onclick="updater.dialogWorkerYes()">Yes</button><button onclick="updater.dialogNo()">No</button>'
        else if message.type=='build_upgrade'
            document.getElementById('message').innerHTML = 'Would you like to build an upgrade? <button onclick="updater.dialogUpgradeYes()">Yes</button><button onclick="updater.dialogNo()">No</button>'
    dialogNo: () ->
        message = {}
        message.message = 'next_event'
        updater.socket.send(JSON.stringify(message))
    dialogCityYes: () ->
        document.getElementById('message').innerHTML = 'Select a city tile to bring online.'
        window.canvas.on 'mouse:up', (options) ->
            message = {}
            message.x = Math.floor(options.e.clientX / 45)
            message.y = Math.floor(options.e.clientY / 45)
            message.message = 'city_delivery_position_selected'
            window.canvas.off 'mouse:up'
            updater.socket.send(JSON.stringify(message))
    dialogWorkerYes: () ->
        message = {}
        message.message = 'construct_worker_confirmed'
        updater.socket.send(JSON.stringify(message))
    dialogUpgradeYes: () ->
        message = {}
        message.message = 'build_upgrade_confirmed'
        updater.socket.send(JSON.stringify(message))
    processSpendFreely: (message) ->
        text = message.text+' <span style="color: #FFFF00;" onclick="updater.spendResources(0)">'+window.player_electricity+'</span>'
        text = text+' <span style="color: #00FFFF;" onclick="updater.spendResources(1)">'+window.player_water+'</span>'
        text = text+' <span style="color: #00E000;" onclick="updater.spendResources(2)">'+window.player_information+'</span>'
        text = text+' <span style="color: #808080;" onclick="updater.spendResources(3)">'+window.player_metal+'</span>'
        text = text+' <span style="color: #FF8000;" onclick="updater.spendResources(4)">'+window.player_rare_metal+'</span>'
        document.getElementById('message').innerHTML = text
        count = parseInt(message.count)
        type = message.type
        window.spendFreelySpent=0
        window.spendFreelyMax=count
        window.spendFreelyText=message.text
        window.spendFreelyType=type
    updateProcessSpendFreely: () ->
        if window.spendFreelySpent<window.spendFreelyMax
            text = window.spendFreelyText+' <span style="color: #FFFF00;" onclick="updater.spendResources(0)">'+window.player_electricity+'</span>'
            text = text+' <span style="color: #00FFFF;" onclick="updater.spendResources(1)">'+window.player_water+'</span>'
            text = text+' <span style="color: #00E000;" onclick="updater.spendResources(2)">'+window.player_information+'</span>'
            text = text+' <span style="color: #808080;" onclick="updater.spendResources(3)">'+window.player_metal+'</span>'
            text = text+' <span style="color: #FF8000;" onclick="updater.spendResources(4)">'+window.player_rare_metal+'</span>'
            document.getElementById('message').innerHTML = text
        else
            message = {}
            message.message = 'spent_freely'
            message.type = window.spendFreelyType
            message.electricity = window.player_electricity
            message.water = window.player_water
            message.information = window.player_information
            message.metal = window.player_metal
            message.rare_metal = window.player_rare_metal
            updater.socket.send(JSON.stringify(message))
    spendResources: (number) ->
        if window.spendFreelySpent<window.spendFreelyMax
            if number==0 and window.player_electricity>0
                window.player_electricity-=1
                window.spendFreelySpent+=1
            else if number==1 and window.player_water>0
                window.player_water-=1
                window.spendFreelySpent+=1
            else if number==2 and window.player_information>0
                window.player_information-=1
                window.spendFreelySpent+=1
            else if number==3 and window.player_metal>0
                window.player_metal-=1
                window.spendFreelySpent+=1
            else if number==4 and window.player_rare_metal>0
                window.player_rare_metal-=1
                window.spendFreelySpent+=1
            updater.updateProcessSpendFreely()
    processTileLay: (message) ->
        group = drawTableTile(0,0,message.tile,false,0,0)
        updater.tile = message.tile
        updater.group = group
        if message.active==true
            window.canvas.on 'mouse:move', (options) ->
                leftmost = 10000
                topmost = 10000
                x = Math.floor(options.e.clientX / 45) * 45
                y = Math.floor(options.e.clientY / 45) * 45
                group.forEachObject((o) ->
                    if o.get('left')<leftmost
                        leftmost = o.get('left'))
                group.forEachObject((o) ->
                    if o.get('top')<topmost
                        topmost = o.get('top'))
                group.forEachObject((o) ->
                    offset = o.get('left')-leftmost
                    o.set('left',x+offset))
                group.forEachObject((o) ->
                    offset = o.get('top')-topmost
                    o.set('top',y+offset))
                window.canvas.renderAll()
            window.canvas.on 'mouse:up', (options) ->
                message = {}
                x = Math.floor(options.e.clientX / 45)
                y = Math.floor(options.e.clientY / 45)
                message.message = 'tile_position_selected'
                message.tile = updater.tile
                message.x = x
                message.y = y
                window.canvas.off 'mouse:move'
                window.canvas.off 'mouse:up'
                updater.socket.send(JSON.stringify(message))
    processTileRotate: (message) ->
        window.canvas.on 'mouse:move', (options) ->
            x = options.e.clientX
            y = options.e.clientY
            tileX = message.x*45
            tileY = message.y*45
            if Math.abs(x-tileX)>Math.abs(y-tileY)
                if x>tileX
                    orientation = 1
                else
                    orientation = 3
            else
                if y>tileY
                    orientation = 2
                else
                    orientation = 0
            split_tile = message.tile.split(',')
            split_tile[1]=orientation
            updater.tile = split_tile.join(',')
            message.tile = updater.tile
            window.canvas.remove(updater.group)
            updater.group = drawTableTile(tileX,tileY,message.tile,false,message.x,message.y)
            window.canvas.renderAll()
        window.canvas.on 'mouse:up', (options) ->
            message.message = 'tile_rotation_selected'
            message.tile = updater.tile
            window.canvas.remove(updater.group)
            window.canvas.off 'mouse:move'
            window.canvas.off 'mouse:up'
            updater.socket.send(JSON.stringify(message))
    processWorkerLay: (message) ->
        switch parseInt(message.worker_turn)
                    when 0 then color='rgba(64,64,255,1)'
                    when 1 then color='rgba(255,64,64,1)'
                    when 2 then color='rgba(64,255,64,1)'
                    when 3 then color='rgba(255,255,64,1)'
                    else color=-1
        circle = new fabric.Circle(radius: 22, fill: color, stroke: color, left:0, top:0)
        window.canvas.add(circle)
        updater.circle = circle
        if message.active==true
            window.canvas.on 'mouse:move', (options) ->
                x = options.e.clientX-30
                y = options.e.clientY-50
                updater.circle.left = x
                updater.circle.top = y
                window.canvas.renderAll()
            window.canvas.on 'mouse:up', (options) ->
                x = Math.floor((options.e.clientX-8)/45)
                y = Math.floor((options.e.clientY-28)/45)
                message = {}
                message.message = 'worker_placed'
                message.x = x
                message.y = y
                window.canvas.remove(updater.circle)
                window.canvas.off 'mouse:move'
                window.canvas.off 'mouse:up'
                updater.socket.send(JSON.stringify(message))
class TileType
    constructor: () ->
        @facilityConnection = [false,false,false,false]
        @cityConnection = [false,false,false,false]

initiateTileTypes = () ->
    types = []
    for i in [1..27]
        types.push(new TileType)
    types[0].facilityConnection[0]=true
    types[1].cityConnection[0]=true
    types[2].facilityConnection[0]=true
    types[2].facilityConnection[2]=true
    types[3].cityConnection[0]=true
    types[3].cityConnection[2]=true
    types[4].facilityConnection[0]=true
    types[4].cityConnection[2]=true
    types[5].facilityConnection[1]=true
    types[5].cityConnection[2]=true
    types[6].facilityConnection[2]=true
    types[6].cityConnection[1]=true
    types[7].facilityConnection=[true,true,false,true]
    types[8].cityConnection=[true,true,false,true]
    types[9].facilityConnection[0]=true
    types[9].facilityConnection[3]=true
    types[10].cityConnection[0]=true
    types[10].cityConnection[3]=true
    for i in [11..18]
        types[i].facilityConnection[0] = true
    return types
class UpgradeType
    constructor: () ->
        @name=""
        @category=""
        @description=""
        @description2=""
        @description3=""
        @electricity=0
        @water=0
        @information=0
        @metal=0
        @rare_metal=0
    cost: (self,upgrade_number) ->
        cost_increase = 0
        player = game_state.players[player_identity]
        if game_state.upgrades_available[25]==false
            if upgrade_owner_number(25)!=player_identity
                if game_state.upgrades_available[16]==true or (game_state.upgrades_available[16]==false and upgrade_owner_number(16)!=player_identity)
                    cost_increase = get_highest_costed_resource(upgrade_number)
        if cost_increase==1
            this.electricity+=1
        else if cost_increase==2
            this.water+=1
        else if cost_increase==3
            this.information+=1
        else if cost_increase==4
            this.metal+=1
        else if cost_increase==5
            this.rare_metal+=1
        costs=[]
        colors=[]
        if this.electricity>0
            costs.push("Electricity: "+str(this.electricity))
            if player.electricity<this.electricity
                colors.push([255,0,0])
            else
                colors.push([255,255,0])
        if this.water>0
            costs.push("Water: "+str(this.water))
            if player.water<this.water
                colors.push([255,0,0])
            else
                colors.push([0,255,255])
        if this.information>0
            costs.push("Information: "+str(this.information))
            if player.information<this.information
                colors.push([255,0,0])
            else
                colors.push([0,224,0])
        if this.metal>0
            costs.push("Metal: "+str(this.metal))
            if player.metal<this.metal
                colors.push([255,0,0])
            else
                colors.push([128,128,128])
        if this.rare_metal>0
            costs.push("Rare Metal: "+str(this.rare_metal))
            if player.rare_metal<this.rare_metal
                colors.push([255,0,0])
            else
                colors.push([255,128,0])
        if cost_increase==1
            this.electricity-=1
        else if cost_increase==2
            this.water-=1
        else if cost_increase==3
            this.information-=1
        else if cost_increase==4
            this.metal-=1
        else if cost_increase==5
            this.rare_metal-=1
        returnValue = [costs,colors]
        return returnValue

initiateUpgradeTypes = () ->
    types = []
    for i in [1..32]
        types.push(new UpgradeType)
    for i in [0..7]
        types[i].category="Data Hosting"
    for i in [8..15]
        types[i].category="Finance"
    for i in [16..23]
        types[i].category="Entertainment"
    for i in [24..31]
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
    for i in [0..31]
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
    
