# rocketleague_boost_analysis

This project performs boost usage analysis on Rocket League replay files. 

Under a provided player name, the download_replays notebook fills the `replays/replay` directory with all replays found in the [ballchasing replay repository](https://ballchasing.com/).

Once downloaded, the `main.py` script processes the replay binaries into JSONs using JJBot's [parser](https://github.com/jjbott/RocketLeagueReplayParser). The JSONs are found in `replays/json`. The script then collects player game data prior to each goal scored by the player during the match using simulations from Shafer's [replay analysis tool](https://gitlab.com/enzanki_ars/rocket-league-replay-analysis), which once completed stores a player goal JSON in `player_jsons`.

Finally the `view_results.ipynb` notebook processes the player goal JSON data and produces a plot displaying boost utilization by goal.
