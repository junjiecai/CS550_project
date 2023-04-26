from __future__ import annotations
from collections import defaultdict
from typing import List, Dict, NewType, Tuple
from random import choice, choices
from math import exp
from flask_cors import CORS
from flask import Flask, request
import requests
import yaml
import pathlib
from os.path import join
from loguru import logger
from time import time

# todo: fill later
adhesion_config = {}

Coordinate = NewType('Coordinate', [int, int])

T = 1


def _create_cell(x, y, w, h, cell_id, cell_type):
    coordinates = []
    for dx in range(w):
        for dy in range(h):
            coordinates.append((x + dy, y + dy))

    return Cell(cell_id, cell_type, coordinates)


class CentralNodeServer:
    def __init__(self):
        self._peer_urls = []

        app = Flask(__name__)
        app.config['CORS_HEADERS'] = 'Content-Type'
        cors = CORS(app)

        @app.route('/central/register', methods=['POST'])
        def register():
            peer_host = request.json['host']
            peer_port = request.json['port']

            self._peer_urls.append("http://{}:{}".format(peer_host, peer_port))

            return {'message': 'registered'}

        # todo: implement quartered buffer update
        @app.route('/central/step_over', methods=['GET'])
        def step_over():
            start_time = time()
            all_data = {}
            for url in self._peer_urls:
                data = requests.get("{}/peer/step_over".format(url)).json()['data']

                for key, d_ in data.items():
                    if key in all_data:
                        all_data[key].update(d_)
                    else:
                        all_data[key] = d_

            print(time() - start_time)

            return {'data': all_data}

        self._app = app

    def run(self):
        self._app.run(host="localhost", port=8000)


class PeerNodeServer:
    def __init__(self, host="localhost", port=8001):
        self._host = host
        self._port = port
        app = Flask(__name__)
        app.config['CORS_HEADERS'] = 'Content-Type'
        CORS(app)

        outer = {
            "lattice": None
        }

        @app.route('/peer/step_over', methods=['GET'])
        def step_over():
            start_time = time()
            outer['lattice'].simulate()
            print(time() - start_time)

            data = outer['lattice'].data()

            return {"data": data}

        @app.route('/peer/initialize', methods=['POST'])
        def initialize():
            x_range = request.json['x_range']
            y_range = request.json['y_range']

            cells = request.json['cells']

            outer['lattice'] = Lattice(x_range, y_range, cells)

            return {"message": "initialize"}

        self._app = app

    def run(self):
        self._app.run(host=self._host, port=self._port)


class Pixel:
    def __init__(self, _x, _y, cell: Cell):
        self.coordinate = (_x, _y)
        self.cell = cell

    @property
    def cell_id(self):
        return self.cell.cell_id

    @property
    def cell_type(self):
        return self.cell.cell_type

    def change_cell(self, new_cell):
        self.cell.remove_pixel(*self.coordinate)

    def detach_cell(self):
        self.cell.remove_pixel(self.coordinate)
        self.cell = None


class Cell:
    def __init__(self, cell_id, cell_type, pixels: List[Coordinate]):
        self.cell_id = cell_id
        self.cell_type = cell_type
        self._adhesion = None
        self._volume = None
        self._perimeter = None
        self._pixels = {}

        for (x, y) in pixels:
            self._pixels[(x, y)] = self.create_pixel(x, y)

    def create_pixel(self, x, y) -> Pixel:
        pixel = Pixel(x, y, self)
        self._pixels[(x, y)] = pixel

        return pixel

    def merge_pixel(self, pixel: Pixel):
        pixel.detach_cell()

        self._pixels[pixel.coordinate] = pixel
        pixel.cell = self

    def remove_pixel(self, coordinate) -> Pixel:
        return self._pixels.pop(coordinate)

    def in_cell(self, coordinate):
        return coordinate in self._pixels


def _get_local_neighbours(x, y, x_range=None, y_range=None):
    coordinates = []
    for dx in [-1, 0, 1]:
        if x_range:
            if not (x_range[0] <= dx + x < x_range[1]):
                continue

        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue

            if y_range:
                if not (y_range[0] <= dy + y < y_range[1]):
                    continue

            coordinates.append((x + dx, y + dy))

    return coordinates


def _get_pixel_pairs(coordinates_pixel_mapping: Dict[Coordinate, Pixel]) -> List[Tuple[int, int]]:
    return []


def init_zero():
    return 0


# todo: add some test
def _local_energy(pixels: List[Pixel]):
    # 3x3 pixels

    coordinates_pixel_mapping = {}

    pairs = _get_pixel_pairs(coordinates_pixel_mapping)

    perimeter = {}
    adhesion = {}

    for pixel_1, pixel_2 in pairs:
        if pixel_1.cell_id != pixel_2.cell_id:
            perimeter[pixel_1.cell_id] += 1
            perimeter[pixel_2.cell_id] += 1

            adhesion[pixel_1.cell_id] += adhesion_config[sorted((pixel_1.type, pixel_2.type))]
            adhesion[pixel_2.cell_id] += adhesion_config[sorted((pixel_1.type, pixel_2.type))]

    volume = defaultdict(init_zero)
    for pixel in pixels:
        volume[pixel.cell_id] += 1

    return {
        "local_adhesion": adhesion,
        "local_volume": volume,
        "local_perimeter": perimeter
    }


# energies = defaultdict(lambda: 0)
#
# for pixel in pixels:
#     energies[pixel._cell_type] += 1


# todo: implement
def cal_delta_energies(cells, current_local_energies, new_local_energies) -> int:
    return 0


def _to_probability(delta_energy, T):
    if delta_energy <= 0:
        return 1
    else:
        return exp(-delta_energy / T)


class Lattice:
    def __init__(self, x_range, y_range, cells_data: List):
        self.x_range = x_range
        self.y_range = y_range

        self.cells = [Cell(cell_id, cell_type, coordinates) for cell_id, cell_type, coordinates in cells_data]

        background_coordinates = []
        for x in range(*x_range):
            for y in range(*y_range):
                for cell in self.cells:
                    if cell.in_cell((x, y)):
                        break
                else:
                    background_coordinates.append((x, y))

        background = Cell(0, "BG", background_coordinates)
        self.cells.append(background)

        self._coordicate_pixel_mapping = {}
        for cell in self.cells:
            for coordinate, pixel in cell._pixels.items():
                x, y = coordinate
                if (x_range[0] <= x < x_range[1]) and (y_range[0] <= y < y_range[1]):
                    self._coordicate_pixel_mapping[coordinate] = pixel

    def data(self):
        new_data = {}

        for cell in self.cells:
            coordinates = cell._pixels.keys()

            for (x, y) in coordinates:
                if (self.x_range[0] <= x < self.x_range[1]) and (self.y_range[0] <= y < self.y_range[1]):
                    if not x in new_data:
                        new_data[x] = {}

                    new_data[x][y] = {
                        "id": cell.cell_id,
                        "cell_type": cell.cell_type
                    }

        return new_data

    def simulate(self):
        # todo: support buffer region
        for x in range(*self.x_range):
            for y in range(*self.y_range):
                neighbours = _get_local_neighbours(x, y, self.x_range, self.y_range)

                pixels = [self._coordicate_pixel_mapping[coordinate] for coordinate in neighbours]

                pixel = self._coordicate_pixel_mapping[(x, y)]
                pixels = [pixel_ for pixel_ in pixels if pixel_.cell_id != pixel.cell_id]

                if len(pixels) == 0:
                    continue

                pixels.append(pixel)

                current_state = _local_energy(pixels)

                target = choice(neighbours)
                new_pixels = pixels.copy()
                for new_pixel in new_pixels:
                    if pixel.coordinate == target:
                        new_pixel.cell_id = pixel.cell_id

                new_state = _local_energy(pixels)

                delta_energy = cal_delta_energies(self.cells, current_state, new_state)

                p = _to_probability(delta_energy, T)

                if pixel.cell_id == 0:
                    p = 0
                if pixel.cell_id != 0:
                    p = 1

                result = choices([True, False], [p, 1 - p], k=1)[0]

                if result:
                    cell = self._coordicate_pixel_mapping[(x, y)].cell
                    cell.merge_pixel(self._coordicate_pixel_mapping[target])

    # def _cal_delta_energy(self, pixels):
    #     pass


# for pixel in


# class Node:
#     def __init__(self):
#         cells = {
#
#         }
#
#         pixel_cells = None
#         cell_pixels = None
#
#     def simulate_all(self):
#         for quater_name, sub_lattice in self.quatered_lattice.items():
#             for (x, y), pixel in sub_lattice.items():
#                 self.act(x, y)
#
#     def act(self, x, y, pixel):
#         free_neighbours = self.get_free_neighbor(x, y)
#
#         for x, y in free_neighbours:
#             new_node = node.copy()
#             new_node.x = x
#             new_node.y = y
#             new_node.pixel = pixel


if __name__ == '__main__':
    lattice = Lattice([-1, 2], [-1, 2], [(1, 'A', [[0, 0]])])
    print(lattice.data())
    # lattice.display()

    # for _ in range(5):
    #     lattice.simulate()
    #     lattice.display()

    # node = Node([0, 0], 100, [20, 20], [])
    #
    # for i in range(100):
    #     node.simulate_all()
    # history = node.get_history()
    # video = to_video(history)

    # print(_get_local_neighbours(0, 0, x_range=[-1, 1], y_range=[-1, 1]))
