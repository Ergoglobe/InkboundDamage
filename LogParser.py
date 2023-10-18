import time
import re
import os

import pandas as pd

import Display
from Domain import GameLog, Player

game_log = GameLog()

# Globals
DIVE_NUMBER = 0  # starts at 0, increments by 1 each new reset_game
COMBAT_NUMBER = 0  # starts at 0, increments by 1 each time combat start is triggered
TURN_NUMBER = 0  # starts at 0, increments by 1 each time a turn is triggered, resets to 0 on combat end


def parse():
    for line in follow():
        handle_line(line, game_log)


def follow():
    file = open(
        os.environ["USERPROFILE"] + "/AppData/LocalLow/Shiny Shoe/Inkbound/logfile.log",
        "r",
    )
    while True:
        # read last line of file
        next_line = file.readline()

        # sleep if file hasn't been updated
        if not next_line:
            Display.render(game_log)
            time.sleep(0.1)  # can probably increase this to reduce program resources
            continue

        yield next_line


def handle_line(line, game):
    if "Party run start triggered" in line:
        reset_game(game)
        global DIVE_NUMBER
        global COMBAT_NUMBER
        DIVE_NUMBER += 1
        COMBAT_NUMBER = 0

    if "EventOnCombatStarted" in line:
        COMBAT_NUMBER += 1

    # if "QuestObjective_TurnCount" in line:
    if "Advance turn" in line:
        global TURN_NUMBER
        TURN_NUMBER += 1
        print(TURN_NUMBER)

    if "TargetingSystem handling event: EventOnCombatEndSequenceStarted" in line:
        # Reset turns to 0
        TURN_NUMBER = 0

    if "is playing ability" in line:
        register_new_player(line, game)
    if "broadcasting EventOnUnitDamaged" in line:
        register_ability_damage(line, game)
    if "Setting unit class for" in line:
        register_class(line, game)
    # if "EventOnUnitStatusEffectStacks" in line:
    #     register_status_effect_stacks(line, game)

    ## TODO: find log that shows run finished
    ## TODO: 0T18:20:52 29 I [VfxSystem] InitAndTriggerEntityIntro-Loot: (EntityHandle:39) Generic_Loot_Potion(Clone)
    ## TODO: 0T18:21:28 16 I Spawning Encounter_Medium_NoGeo in socket Combat
    ## TODO: 0T18:21:28 16 I Rolled enemy group suffix: UnitData-Figment_Large_ALL_T1_Unit (Figment dTORXHoH): (StatusEffectData-ChallengeBuff_GlassCannon_Base_StatusEffect (Glass Cannon sqgof87p))
    ## TODO: 0T18:21:28 16 I WorldCommandSpawnUnit (EntityHandle:55): groupSuffixIndex 3 (ChallengeBuff_GlassCannon_Base_StatusEffect)
    ## TODO: 0T18:25:35 25 I Evaluating quest progress for (EntityHandle:15) with 62 active quests. Record variable: StatUpgrade_AllClasses_FrostbiteDamage_Applied_QuestPR
    ## TODO: 0T18:25:43 00 I Evaluating quest progress for (EntityHandle:15) with 62 active quests. Record variable: CryostasisUpgrade_Common_AddFrostbite_QuestPR


def register_class(line, game):
    entity_id = int(
        re.search(
            "(?<=animation-UnitEntityHandle:\(EntityHandle:)([\-\d]*)", line
        ).group()
    )
    class_type = re.search("(?<=classType:)([a-zA-Z0-9]*)", line).group()
    game.entity_to_class_id[entity_id] = class_type


def reset_game(game):
    game.sync_player_classes()
    game.games.append({})
    Display.reset()


def register_status_effect_stacks(line, game):
    # TODO:: clean this up
    type = re.search("(?<=EventOnUnitStatusEffectStacks)([a-zA-Z]*)", line).group()
    caster_unit_id = int(
        re.search("(?<=CasterUnitEntityHandle:\(EntityHandle:)([\-\d]*)", line).group()
    )
    target_unit_id = int(
        re.search("(?<=TargetUnitEntityHandle:\(EntityHandle:)([\-\d]*)", line).group()
    )
    effect = re.search(
        "(?<=StatusEffectData:StatusEffectData-)([a-zA-Z-_]*)", line
    ).group()

    stacks_added = re.search("(?<=StacksAdded:)(\d*)", line)
    if stacks_added is None:
        stacks_added = 0
    else:
        stacks_added = int(stacks_added.group())

    stacks_removed = re.search("(?<=StacksRemoved:)(\d*)", line)
    if stacks_removed is None:
        stacks_removed = 0
    else:
        stacks_removed = int(stacks_removed.group())

    players = game.get_players()

    if type == "Added":
        # if the target is a player record status effects received
        if target_unit_id in players.keys():
            players[target_unit_id].status_effects_received[effect] = (
                players[target_unit_id].status_effects_received.get(effect, 0)
                + stacks_added
            )

        # if the attacker is a player record status effects applied
        if caster_unit_id in players.keys():
            players[caster_unit_id].status_effects_applied[effect] = (
                players[caster_unit_id].status_effects_applied.get(effect, 0)
                + stacks_added
            )


def register_new_player(line, game):
    player_id = int(re.search("(?<=\(EntityHandle:)(\d*)", line).group())
    player_name = re.search("(?<=I )([a-zA-Z-_]*)", line).group()

    players = game.get_players()

    if player_id not in players.keys():
        players[player_id] = Player(player_id, player_name, None, {}, {}, {}, {})


# ConstrictUpgrade_Legendary_Entwine becomes Constrict -> Entwine
def clean_damage_type_jank(damage_type):
    # Maybe remove vestige and just leave the vestige name?
    if "All_Legendary_" in damage_type:
        damage_type = damage_type.replace("All_Legendary_", " -> ")

    if "Upgrade_Legendary_" in damage_type:
        damage_type = damage_type.replace("Upgrade_Legendary_", " -> ")

    if "_Legendary_" in damage_type:
        damage_type = damage_type.replace("_Legendary_", " -> ")

    return damage_type


def register_ability_damage(line, game):
    target_id = int(
        re.search("(?<=TargetUnitHandle:\(EntityHandle:)(\d*)", line).group()
    )
    attacker_id = int(
        re.search("(?<=SourceEntityHandle:\(EntityHandle:)(\d*)", line).group()
    )
    damage_amount = int(re.search("(?<=DamageAmount:)(\d*)", line).group())

    # Why is their naming scheme so jank??
    damage_type = clean_damage_type_jank(
        re.search("(?<=ActionData:)([a-zA-Z-_]*)", line)
        .group()
        .removeprefix("ActionData-")
        .removesuffix("_Action")
        .removesuffix("_ActionData")
        .removesuffix("Damage")
        .removesuffix("_")
    )

    players = game.get_players()

    # if the target is a player record damage received
    if target_id in players.keys():
        players[target_id].damage_received[damage_type] = (
            players[target_id].damage_received.get(damage_type, 0) + damage_amount
        )

    # if the attacker is a player record damage dealt
    if attacker_id in players.keys():
        players[attacker_id].damage_dealt[damage_type] = (
            players[attacker_id].damage_dealt.get(damage_type, 0) + damage_amount
        )
