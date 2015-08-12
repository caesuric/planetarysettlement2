$(document).ready ->
    if !window.console
        window.console = {}
    if !window.console.log
        window.console.log = ->

    window.canvas = new fabric.StaticCanvas('my_canvas')
    window.canvas.backgroundColor="black"
    window.canvas.renderAll()
    updater.start()
    window.tileTypes = initiateTileTypes()
    window.upgradeTypes = initiateUpgradeTypes()

renderTable = (upgrades_available,table_tiles,players) ->
    window.canvas.backgroundColor="black"
    for i in [0..29]
        for j in [0..29]
            if table_tiles[i][j]!=null
                x_pos = i*45
                y_pos = j*45
                window.canvas.add new fabric.Rect(left: x_pos, top: y_pos, height: 45, width: 45, stroke: 'white', fill: 'transparent', strokeWidth: 2)
                tile_data = table_tiles[i][j].split(",")
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
                rotated = getRotatedTileType(tile_type,tile_orientation)
                if tile_city_online_status==0
                    city_color = 'rgba(128,128,128,1)'
                else if tile_city_online_status==1
                    city_color = 'rgba(0,224,0,1)'
                else if tile_city_online_status==2
                    city_color = 'rgba(0,64,255,1)'
                if rotated.facilityConnection[1]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
                    if region_closed(get_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
                if rotated.cityConnection[1]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
                    if region_closed(get_city_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos+22, top: y_pos, opacity: 1.0)
                if rotated.facilityConnection[2]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
                    if region_closed(get_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
                if rotated.cityConnection[2]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
                    if region_closed(get_city_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos+45, y: y_pos+45}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos+22, opacity: 1.0)
                if rotated.facilityConnection[3]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                    if region_closed(get_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                if rotated.cityConnection[3]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                    if region_closed(get_city_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos, y: y_pos+45}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                if rotated.facilityConnection[0]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: 'rgba(255,0,0,1)', fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                    if region_closed(get_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: 'rgba(255,0,0,1)', fill: 'rgba(255,0,0,1)', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                if rotated.cityConnection[0]==true
                    window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: city_color, fill: 'transparent', strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                    if region_closed(get_city_region(i))==true
                        window.canvas.add new fabric.Polygon([{x: x_pos, y: y_pos}, {x: x_pos+22, y: y_pos+22}, {x: x_pos+45, y: y_pos}], stroke: city_color, fill: city_color, strokeWidth: 4, left: x_pos, top: y_pos, opacity: 1.0)
                if tile_electricity>0
                    window.canvas.add new fabric.Text(tile_electricity.toString(), left: x_pos+2, top: y_pos+2, fill: 'rgba(255,255,0,1)', fontSize: 15)
                if tile_water>0
                    window.canvas.add new fabric.Text(tile_water.toString(), left: x_pos+18, top: y_pos+2, fill: 'rgba(0,255,255,1)', fontSize: 15)                
                if tile_information>0
                    window.canvas.add new fabric.Text(tile_information.toString(), left: x_pos+33, top: y_pos+2, fill: 'rgba(0,224,0,1)', fontSize: 15)
                if tile_metal>0
                    window.canvas.add new fabric.Text(tile_metal.toString(), left: x_pos+2, top: y_pos+18, fill: 'rgba(128,128,128,1)', fontSize: 15)
                if tile_rare_metal>0
                    window.canvas.add new fabric.Text(tile_rare_metal.toString(), left: x_pos+18, top: y_pos+18, fill: 'rgba(255,128,0,1)', fontSize: 15)
    canvas.renderAll()

region_closed = (region) ->
    # STUB
    return true
    
get_region = (tile) ->
    # STUB
    return tile

get_city_region = (tile) ->
    # STUB
    return tile
    
getRotatedTileType = (type,orientation) ->
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
    processMessage: (message) ->
        if message.message=='push_update'
            updater.processPushUpdate(message)
    processPushUpdate: (message) ->
        upgrades_available = message.upgrades_available
        table_tiles = message.table_tiles
        players = message.players
        renderTable(upgrades_available,table_tiles,players)

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
        if game_state.upgrades_available[25]==False
            if upgrade_owner_number(25)!=player_identity
                if game_state.upgrades_available[16]==True or (game_state.upgrades_available[16]==False and upgrade_owner_number(16)!=player_identity)
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
    