from backend.core import CentralNodeServer, PeerNodeServer, _create_cell
from threading import Thread
from requests import post
from time import sleep
from itertools import cycle, product

# start server in background thread

central_app = CentralNodeServer()

lattice_grid = [2, 2]
lattice_width = int(600 / lattice_grid[1])
lattice_height = int(600 / lattice_grid[0])

# todo: remove useless cells definition for each lattice
cells_data = []

cell_id = 1
cell_types = ['A', "B"]
for start_x in range(150, 420, 30):
    for start_y in range(150, 420, 30):
        cell_type = cell_types.pop(0)
        cell_types.append(cell_type)
        cells_data.append(
            [cell_id, cell_type, list(product(range(start_x, start_x + 30), range(start_y, start_y + 30)))])
        cell_id += 1

peer_data = []
port_id = 8001
for x in range(0, 600, lattice_width):
    for y in range(0, 600, lattice_height):
        peer_data.append(
            {
                "host": "localhost",
                "port": port_id,
                "x_range": [x, x + lattice_width],
                "y_range": [y, y + lattice_height],
                "cells": cells_data
            }
        )

        port_id += 1

peers_apps = [PeerNodeServer(host=config['host'], port=config['port']) for config in peer_data]
apps = peers_apps + [central_app]


def start_server(app):
    app.run()


if __name__ == '__main__':
    for app in apps:
        Thread(target=start_server, args=[app]).start()

    sleep(5)

    central_host = "localhost"
    central_port = 8000
    for config in peer_data:
        post("http://{}:{}/peer/initialize".format(config['host'], config['port']), json={
            "x_range": config['x_range'],
            "y_range": config['y_range'],
            "cells": config['cells']
        })

        post("http://{}:{}/central/register".format(central_host, central_port), json={
            "host": config['host'],
            "port": config['port']
        })
