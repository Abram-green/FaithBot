from os import stat
from mcstatus import MinecraftServer

def get_online_players(iphost):
    try:
        server = MinecraftServer.lookup(iphost)
        status = server.status()
        players = [ user['name'] for user in status.raw['players']['sample'] ]
    except Exception:
        return False
    return players

def get_online(iphost):
    try:
        server = MinecraftServer.lookup(iphost)
        status = server.status()
        max = status.raw['players']['max']
        online = status.raw['players']['online']
        result = {
            'max': max,
            'online': online
        }
    except Exception:
        return False
    return result

def get_ping(iphost):
    try:
        server = MinecraftServer.lookup(iphost)
    except Exception:
        return False
    return server.host

def get_description(iphost):
    try:
        server = MinecraftServer.lookup(iphost)
        status = server.status()
        desc = status.raw["description"]['text']
        desc = desc.replace("§0", '').replace("§1", '').replace("§2", '').replace("§3", '').replace("§4", '')
        desc = desc.replace("§5", '').replace("§6", '').replace("§7", '').replace("§8", '').replace("§9", '')
        desc = desc.replace("§a", '').replace("§b", '').replace("§c", '').replace("§d", '').replace("§e", '')
        desc = desc.replace("§f", '').replace("§l", '').replace("§n", '').replace("§m", '').replace("§k", '')
        desc = desc.replace("§r", '').replace("§0", '')
    except Exception:
        return False
    return desc