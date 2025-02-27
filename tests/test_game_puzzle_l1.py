import pytest
import os
import random
import math
from starkware.starknet.testing.starknet import Starknet
from lib import *
from visualizer import *
import asyncio

ERR_TOL = 1e-5

#
# Testing methodology:
# loop:
#   forward the scene by a random step count
#   check contract return against python simulation return.
#   stop if all objects in the scene have come to rest.
#
@pytest.mark.asyncio
async def test_game ():

    starknet = await Starknet.empty()
    contract = await starknet.deploy('examples/puzzle_v1/game.cairo')
    print()

    arr_obj_s = []
    while True:

        level = 1

        velocity_magnitude = sqrt(2*145**2)
        theta = random.uniform(0, 1) * math.pi * 2
        move_x = int(velocity_magnitude * math.cos(theta) *FP)
        move_y = int(velocity_magnitude * math.sin(theta) *FP)
        move = contract.Vec2 (move_x, move_y)

        ret = await contract.submit_move_for_level (
            level = level,
            move_x = move_x,
            move_y = move_y
        ).invoke()

        print(f'selected level: {level}')
        print(f'submitted move: {(move[0]/FP, move[1]/FP)}')
        print(f'is_solution = {ret.result.is_solution}')
        print(f'is_solution_family_new = {ret.result.is_solution_family_new}')
        print(f'solution_id = {ret.result.solution_id}')
        print(f'solution_family = {ret.result.solution_family}')
        print(f'score = {ret.result.score}')
        print(f'n_steps: {ret.call_info.execution_resources.n_steps}')

        events = ret.main_call_events
        if len(events)>0:
            for event in events:
                # for obj in event.arr_obj:
                #     print(f'{obj.vel.x}, {obj.vel.y} / ', end='')
                # print()
                arr_obj_s.append(event.arr_obj)

        occurrences = unpack_family_to_occurrences (ret.result.solution_family)
        print(f'collision occurrences: {occurrences}')
        break

    if ret.result.is_solution and ret.result.is_solution_family_new:
        msg1 = f'found a *new* solution; id={ret.result.solution_id}'
        msg2 = f'family={ret.result.solution_family}, score={ret.result.score}'
    elif ret.result.is_solution:
        msg1 = f'found an old solution.'
        msg2 = ''
    else:
        msg1 = f'scored {ret.result.score} - not a solution.'
        msg2 = ''

    visualize_game (arr_obj_s, msg1, msg2, loop=True)

def unpack_family_to_occurrences (family):
    # unpacking means deserialization, where serialization is add & shift by 28
    records = []
    rest = family
    while rest != 0:
        records.append (rest % 28)
        rest = rest // 28

    occurrences = [unpack_record_to_occurrence(record) for record in records]
    occurrences.reverse()

    return occurrences

def unpack_record_to_occurrence (record):
    if record < 16:
        return f'circle {record//4} collided with wall {record%4}'
    else:
        record_ = record - 16
        return f'circle {record_//4} collided with circle {record_%4}'


def print_scene (scene_array, names):
    for i,obj in enumerate(scene_array):
        print(f'    {names[i]}: pos=({adjust(obj.pos.x)}, {adjust(obj.pos.y)}), vel=({adjust(obj.vel.x)}, {adjust(obj.vel.y)}), acc=({adjust(obj.acc.x)}, {adjust(obj.acc.y)})')


def random_sign ():
    return 1 if random.random() < 0.5 else -1