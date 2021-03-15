import json
import pandas as pd
from os import path, getcwd, chdir, listdir
import subprocess
from collections import defaultdict
from rocketleaguereplayanalysis.data.data_loader import parse_data

def replay_to_json(parser_path, replay_raw_path, replay_json_path):
    # move context to replay_json_path for output from parser subprocess
    if getcwd() == project_dir:
        chdir(replay_json_path)

    subprocess.run([parser_path, replay_raw_path, '--fileoutput', '--d'])

    # move context back to project_dir after parser subprocess finishes execution
    if getcwd() != project_dir:
        chdir(project_dir)


# target player name
name = 'invertedX'

parser_path = r'C:\replayparser\RocketLeagueReplayParser.Console\bin\Debug\net45\RocketLeagueReplayParser.Console.exe'
project_dir = r'C:\projects\rl_replays'
replay_json_dir = r'replays\json'
replay_raw_dir = r'replays\replay'
output_dir = r'player_jsons'

# get input/output data dirs for replays
replay_raw_path  = path.join(project_dir, replay_raw_dir)
replay_json_path = path.join(project_dir, replay_json_dir)

# process replays from .replay to .json
replay_to_json(parser_path, replay_raw_path, replay_json_path)

# get json replays
replays_json = listdir(replay_json_path)

# remove any non-replay files
replays_json = [replay for replay in replays_json if replay.split('.')[1] == 'json']

n = len(replays_json)
replay_data = {}
for i, replay_filename in enumerate(replays_json):
    replay_path = path.join(replay_json_path, replay_filename)

    with open(replay_path, 'r', errors="ignore") as f:
        data = json.load(f)

    replay_date = data['Properties']['Date']

    print(f'processing replay {i+1}/{n}:')
    print(replay_filename, replay_date)

    # handle parsing errors
    try:
        frames, _, player_info, _, _ = parse_data(data)
    except KeyError as err:
        print("bad replay KeyError")
    else:
        target_player_id = None

        for player_id, meta in player_info.items():
            if 'name' in meta and meta['name'] == name:
                target_player_id = player_id
                break

        acc = defaultdict(lambda: [])

        i = 0
        while target_player_id not in frames[i]['cars'] and i < 10:
            print(f'bad replay no player entry attempt {i+1}/10')
            i += 1
        if i < 10:
            scoreboard_prev = frames[0]['cars'][target_player_id]['scoreboard']
            events = ['goals', 'assists', 'saves', 'shots']

            if target_player_id is not None:
                for frame in frames:

                    # get server time and target boost, append to acc
                    time = frame['time']['server_time']
                    game_time = frame['time']['game_time']
                    target_boost = frame['cars'][target_player_id]['boost']
                    acc['time'].append(time)
                    acc['game_time'].append(game_time)
                    acc['target_boost'].append(target_boost)

                    # compare scoreboard dicts
                    scoreboard = frame['cars'][target_player_id]['scoreboard']
                    for event in events:
                        if event in scoreboard and scoreboard[event] != scoreboard_prev[event]:
                            acc[event].append(1)
                        else:
                            acc[event].append(0)

                    scoreboard_prev = scoreboard

            df = pd.DataFrame(acc)

            # Get goal indexes where shots were made as well
            acc = set(df.index[df['goals'] == 1])
            #acc.intersection_update(df.index[df['shots'] == 1])

            goal_data = {}
            clip_length = 5

            print(f'goals found: {len(acc)}')
            for idx in acc:
                # get game time when goal was made
                goal_game_time = df['game_time'][idx]

                # get idx where game time is clip_length game time units earlier
                clip_start = (df['game_time'] - clip_length - goal_game_time).apply(abs).idxmin()

                # find df idx where match has reset post-goal
                idx1 = df.index[df['target_boost'] == 0.3333333333333333]
                idx2 = df.index[df['game_time'] == goal_game_time]
                i = 1
                while len(idx1.intersection(idx2)) == 0 and i < 10:
                    print(f'trouble finding post-goal reset index, trying a different game time... {i}/10')

                    idx1 = df.index[df['target_boost'] == 0.3333333333333333]
                    idx2 = df.index[df['game_time'] == goal_game_time + i]
                    if len(idx1.intersection(idx2)) == 0:
                        idx1 = df.index[df['target_boost'] == 0.3333333333333333]
                        idx2 = df.index[df['game_time'] == goal_game_time - i]

                    i += 1

                if len(idx1.intersection(idx2)) == 0:
                    print('likely scored last goal in game, skipping...')
                else:
                    reset_idx = idx1.intersection(idx2)[0]

                    # find server time where goal was just scored (-9 server time)
                    target_end = df['time'][reset_idx] - 9

                    # use target_end server time to find matching idx in df
                    clip_end = df[df['time'].gt(target_end)].index[0]

                    # get relevant rows using clip_start, clip_end
                    goal_diff_df = df[clip_start:clip_end]['target_boost'].diff()

                    # get only entries where boost was lost, not gained and summate them
                    goal_boost_usage = goal_diff_df[goal_diff_df <= 0].sum()

                    goal_data[int(goal_game_time)] = round(goal_boost_usage, 5)

            goal_data['date'] = replay_date
            replay_data[replay_filename.split('.')[0]] = goal_data

to_write = json.dumps(replay_data)

# get output data dir for player goal  json
output_path = path.join(project_dir, output_dir, '.'.join([name, 'json']))

with open(output_path, 'w') as f:
    f.write(to_write)

f.close()
