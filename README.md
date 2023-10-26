# tile-race-bot

A discord bot developed to host tile-races in Oldschool Runescape. Still in very early stages.

## Functionalities

- Automatic roll for the team after approval done by reaction to an image.
- Message sent after roll with description of the tile the team landed on.
- Reroll functionality for skipping x amount of tiles depending on game config.
- Automatic generation of board with player placements based on the rolls and rerolls.
- Possibility to define tiles that are a must hit (meaning you will hit them regardless of your roll).
- Deletion of previous boards to avoid spam.


## Previews

Example of gameboard with two player pieces at the start location.

![game_board](https://github.com/MHagenau/tile-race-bot/assets/9133193/6dd32e41-b678-4b99-adfd-8c5708d8a185)

Notification to the person(s) responsible for approving uploaded tile completions:

![billede](https://github.com/MHagenau/tile-race-bot/assets/9133193/c6eb4da1-7cf5-4a99-b20c-9fa06034db22)


Roll and more detailed tile description after approval of tile completion (done by reacting ✅ on the image).

![billede](https://github.com/MHagenau/tile-race-bot/assets/9133193/6aabd267-d74a-402b-94bc-35878bf98948)

Example of message after a drop have been declined (done by reacting with ❌ on the image).

![billede](https://github.com/MHagenau/tile-race-bot/assets/9133193/762cdcc4-da46-4245-8918-c10f19fd8169)

Example of rerolling a tile (reroll currency is only depleted if the new tile is different from the old one).

![billede](https://github.com/MHagenau/tile-race-bot/assets/9133193/5ba6da08-67ee-416f-a995-24657c0264e6)


Example of trying to reroll while not having any reroll left.

![billede](https://github.com/MHagenau/tile-race-bot/assets/9133193/ac4e7fd8-46f8-47d5-aa3b-4dd8ccb66d01)


## TODO's

- Addition of roll again and go back tiles.
- Bigger board size.
- Option to split into two paths at some points in the board.
- Always on functionality where games can be initialized through commands.
- Increase number of teams up from 4.
