from __future__ import annotations

import math
from typing import Any

import networkx as nx
from shapely.geometry import LineString, Point, Polygon


def calculate_walkable_distances(parsed_data: dict[str, Any]) -> dict[str, Any]:
    """
    Builds a walkable path network using NetworkX and Shapely,
    calculating the shortest walkable escape route from each room centroid
    to the nearest exit, and generates SVG connection path lines.
    Coordinates are properly converted from 0..100% normalized space to true physical meters.
    """
    rooms = parsed_data.get("rooms", [])
    exits = parsed_data.get("exits", [])
    summary = parsed_data.get("summary", {})
    width_m = float(summary.get("width_m") or 42.0)
    height_m = float(summary.get("height_m") or 24.0)

    if not rooms:
        return parsed_data

    def to_meters(svg_x: float, svg_y: float) -> tuple[float, float]:
        """Converts 0..100% normalized SVG coordinates to physical meters."""
        return ((float(svg_x) / 100.0) * width_m, (float(svg_y) / 100.0) * height_m)

    exit_nodes: list[dict[str, Any]] = []
    if exits:
        for idx, e in enumerate(exits):
            pos = e["pos"]
            pos_m = to_meters(pos[0], pos[1])
            exit_nodes.append({
                "id": f"exit_{idx}",
                "name": e.get("name") or f"Exit {idx + 1}",
                "pos_m": pos_m,
                "raw_pos": pos,
            })
    else:
        exit_nodes = [
            {"id": "exit_0", "name": "EXIT STAIR S-01 (West)", "pos_m": (3.0, height_m / 2), "raw_pos": [7.14, 50.0]},
            {"id": "exit_1", "name": "EXIT STAIR S-02 (East)", "pos_m": (width_m - 3.0, height_m / 2), "raw_pos": [92.86, 50.0]},
        ]

    G = nx.Graph()

    for e in exit_nodes:
        G.add_node(e["id"], pos=e["pos_m"], kind="exit", name=e["name"])

    corridor_y = height_m / 2
    corridor_steps = 20
    corridor_nodes: list[str] = []
    for i in range(corridor_steps + 1):
        cx = 3.0 + i * ((width_m - 6.0) / corridor_steps)
        cid = f"corridor_{i}"
        G.add_node(cid, pos=(cx, corridor_y), kind="corridor")
        corridor_nodes.append(cid)
        if i > 0:
            prev_cid = f"corridor_{i - 1}"
            dist = math.dist(G.nodes[prev_cid]["pos"], G.nodes[cid]["pos"])
            G.add_edge(prev_cid, cid, weight=dist)

    for e in exit_nodes:
        closest_c = min(corridor_nodes, key=lambda cid: math.dist(G.nodes[cid]["pos"], e["pos_m"]))
        dist = math.dist(G.nodes[closest_c]["pos"], e["pos_m"])
        G.add_edge(closest_c, e["id"], weight=dist)

    calculated_rooms: list[dict[str, Any]] = []

    for r_idx, room in enumerate(rooms):
        r_id = f"room_{r_idx}"
        centroid_raw = room.get("svg_centroid") or room.get("centroid", [50, 35])
        centroid_m = to_meters(centroid_raw[0], centroid_raw[1])

        door_y = corridor_y - 2.0 if centroid_m[1] < corridor_y else corridor_y + 2.0
        door_x = max(3.0, min(width_m - 3.0, centroid_m[0]))
        door_m = (door_x, door_y)

        d_id = f"door_r_{r_idx}"
        G.add_node(r_id, pos=centroid_m, kind="room", name=room["name"])
        G.add_node(d_id, pos=door_m, kind="door")

        internal_dist = math.dist(centroid_m, door_m)
        G.add_edge(r_id, d_id, weight=internal_dist)

        closest_c = min(corridor_nodes, key=lambda cid: math.dist(G.nodes[cid]["pos"], door_m))
        corridor_conn_dist = math.dist(door_m, G.nodes[closest_c]["pos"])
        G.add_edge(d_id, closest_c, weight=corridor_conn_dist)

        best_exit = None
        min_path_len = float("inf")
        best_path_nodes: list[str] = []

        for e in exit_nodes:
            try:
                length = nx.shortest_path_length(G, source=r_id, target=e["id"], weight="weight")
                if length < min_path_len:
                    min_path_len = length
                    best_exit = e
                    best_path_nodes = nx.shortest_path(G, source=r_id, target=e["id"], weight="weight")
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if min_path_len == float("inf"):
            best_exit = exit_nodes[0]
            min_path_len = math.dist(centroid_m, best_exit["pos_m"])
            best_path_nodes = [r_id, best_exit["id"]]

        travel_dist_m = round(min_path_len, 2)

        # Build clean SVG connection line coordinates
        raw_exit_pos = best_exit.get("raw_pos", [50, 60]) if best_exit else [50, 60]
        svg_c_x = round(centroid_raw[0], 2)
        svg_c_y = round(centroid_raw[1], 2)
        svg_e_x = round(raw_exit_pos[0], 2)
        svg_e_y = round(raw_exit_pos[1], 2)

        # Midpoint for orthogonal routing along corridor spine
        mid_y = round((svg_c_y + svg_e_y) / 2.0, 2)
        connection_path = [
            [svg_c_x, svg_c_y],
            [svg_c_x, mid_y],
            [svg_e_x, mid_y],
            [svg_e_x, svg_e_y]
        ]

        room_info = {
            **room,
            "travel_distance_m": travel_dist_m,
            "nearest_exit": best_exit["name"] if best_exit else "Exit",
            "exit_pos": [svg_e_x, svg_e_y],
            "connection_path": connection_path,
            "path_nodes": [G.nodes[n]["pos"] for n in best_path_nodes],
        }
        calculated_rooms.append(room_info)

    updated_elements: list[tuple[str, str, dict[str, Any]]] = []
    room_calc_map = {r["name"]: r for r in calculated_rooms}

    for item_type, name, feature_dict in parsed_data.get("elements", []):
        props = feature_dict.get("properties", {})
        if item_type == "room" and name in room_calc_map:
            calc = room_calc_map[name]
            props["travel_distance_m"] = calc["travel_distance_m"]
            props["nearest_exit"] = calc["nearest_exit"]
            props["exit_pos"] = calc["exit_pos"]
            props["connection_path"] = calc["connection_path"]
            props["centroid_m"] = [round(to_meters(calc["centroid"][0], calc["centroid"][1])[0], 2), round(to_meters(calc["centroid"][0], calc["centroid"][1])[1], 2)]
        feature_dict["properties"] = props
        updated_elements.append((item_type, name, feature_dict))

    parsed_data["elements"] = updated_elements
    parsed_data["rooms"] = calculated_rooms
    return parsed_data
