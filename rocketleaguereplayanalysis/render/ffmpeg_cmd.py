def create_ffmpeg_cmd_files_from_path(path, filter_type, frames, player_info,
                                      video_prefix, team_info,
                                      reinit=None, modify=None):
    import functools
    import os

    from rocketleaguereplayanalysis.util.export import get_all_data

    all_data = get_all_data(frames, player_info, team_info)

    name = '-'.join(str(x) for x in path)
    if not os.path.exists(os.path.join(video_prefix)):
        os.makedirs(os.path.join(video_prefix))

    last_val = None

    if 'player_num' in path:
        for player in player_info.keys():

            new_path = list(replace_in_array(path, 'player_num', player))
            new_name = '-'.join(str(x) for x in new_path)

            if os.path.exists(os.path.join(video_prefix, new_name + '.txt')):
                os.remove(os.path.join(video_prefix, new_name + '.txt'))

            with open(os.path.join(video_prefix, new_name + '.txt'),
                      'a') as f:

                if 'frame_num' in path:
                    for i in range(0, len(frames)):
                        frame_path = list(
                                replace_in_array(new_path, 'frame_num', i))

                        curr_val = functools.reduce(lambda d, key: d[key],
                                                    frame_path, all_data)

                        if curr_val != last_val or i == 0:
                            write_to_file(f, new_name, frames, i, filter_type,
                                          reinit,
                                          curr_val, modify)
                        last_val = curr_val
                else:
                    curr_val = functools.reduce(lambda d, key: d[key],
                                                new_path, all_data)
                    write_to_file(f, new_name, frames, 0, filter_type, reinit,
                                  curr_val, modify)

    else:
        if os.path.exists(os.path.join(video_prefix, name + '.txt')):
            os.remove(os.path.join(video_prefix, name + '.txt'))

        with open(os.path.join(video_prefix,
                               name + '.txt'), 'a') as f:
            if 'frame_num' in path:
                for i in range(0, len(frames)):
                    frame_path = list(replace_in_array(path, 'frame_num', i))

                    curr_val = functools.reduce(lambda d, key: d[key],
                                                frame_path,
                                                all_data)

                    if curr_val != last_val or i == 0:
                        write_to_file(f, name, frames, i, filter_type, reinit,
                                      curr_val,
                                      modify)

                    last_val = curr_val
            else:
                curr_val = functools.reduce(lambda d, key: d[key],
                                            path,
                                            all_data)

                write_to_file(f, name, frames, 0, filter_type, reinit,
                              curr_val,
                              modify)


def write_to_file(file, name, frames, frame_num, filter_type, reinit, value,
                  modify=None):
    from rocketleaguereplayanalysis.util.sync import get_sync_time_type

    file.write(str(frames[frame_num]['time'][get_sync_time_type()]) +
               " " + filter_type + "@" + name +
               " reinit '")

    if reinit:
        for i, reinit_what in enumerate(reinit.keys(), start=1):
            mod_value = value
            if modify:
                for modify_style in modify.keys():
                    if modify_style == 'add':
                        mod_value = mod_value + modify[modify_style]
                    elif modify_style == 'subtract':
                        mod_value = mod_value - modify[modify_style]
                    elif modify_style == 'multiply':
                        mod_value = mod_value * modify[modify_style]
                    elif modify_style == 'divide':
                        mod_value = mod_value / modify[modify_style]
                    elif modify_style == 'mod':
                        mod_value = mod_value % modify[modify_style]
                    elif modify_style == 'replace':
                        for check in modify[modify_style].keys():
                            if check == str(mod_value):
                                mod_value = modify[modify_style][check]
                                break

            file.write(reinit_what + '=' +
                       reinit[reinit_what].format(mod_value))
            if i != len(reinit):
                file.write(":")
            else:
                file.write("';")

        file.write("\n")


def replace_in_array(it, find, replacement):
    array = []
    for item in it:
        if find == item:
            array.append(replacement)
        else:
            array.append(item)
    return array
