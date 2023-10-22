def register_class(line, game):
    entity_id = int(
        re.search(
            "(?<=animation-UnitEntityHandle:\(EntityHandle:)([\-\d]*)", line
        ).group()
    )
    class_type = re.search("(?<=classType:)([a-zA-Z0-9]*)", line).group()
    game.entity_to_class_id[entity_id] = class_type


def register_new_player(line, game):
    player_id = int(re.search("(?<=\(EntityHandle:)(\d*)", line).group())
    player_name = re.search("(?<=I )([a-zA-Z-_]*)", line).group()

    players = game.get_players()

    if player_id not in players.keys():
        players[player_id] = Player(player_id, player_name, None, {}, {}, {}, {})


def register_ability_damage(line, game):
    target_id = int(
        re.search("(?<=TargetUnitHandle:\(EntityHandle:)(\d*)", line).group()
    )
    attacker_id = int(
        re.search("(?<=SourceEntityHandle:\(EntityHandle:)(\d*)", line).group()
    )
    damage_amount = int(re.search("(?<=DamageAmount:)(\d*)", line).group())
    # Why is their naming scheme so jank??
    damage_type = (
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
